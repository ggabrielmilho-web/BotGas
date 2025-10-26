"""
Master Agent - Main orchestrator with human intervention and audio support
"""
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from uuid import UUID
import logging

from app.agents.base import BaseAgent, AgentContext, AgentResponse
from app.services.intervention import InterventionService
from app.services.audio_processor import AudioProcessor
from app.agents.message_extractor import MessageExtractor
from app.core.config import settings

logger = logging.getLogger(__name__)


class MasterAgent(BaseAgent):
    """
    Main orchestrator agent

    Responsibilities:
    - Check for human intervention
    - Process audio messages
    - Route to appropriate sub-agents
    - Maintain conversation flow
    """

    def __init__(self):
        super().__init__(model_name="gpt-4-turbo-preview", temperature=0.7)
        self.audio_processor = AudioProcessor()
        self.message_extractor = MessageExtractor()

    async def process(self, message: Dict[str, Any], context: AgentContext, db) -> Optional[AgentResponse]:
        """
        Main processing pipeline

        Args:
            message: {
                "type": "text" | "audio",
                "content": str (for text),
                "audio_data": dict (for audio)
            }
            context: AgentContext
            db: Database session

        Returns:
            AgentResponse or None (if intervention is active)
        """
        intervention_service = InterventionService(db)

        # 1. Check human intervention status
        intervention_status = await intervention_service.check_intervention_status(
            tenant_id=context.tenant_id,
            customer_phone=context.customer_phone,
            conversation_id=context.conversation_id
        )

        if intervention_status.get("is_active"):
            # Bot is paused - log message and return None
            await intervention_service.log_message_during_intervention(
                conversation_id=context.conversation_id,
                message={
                    "content": message.get("content", ""),
                    "type": message.get("type", "text"),
                    "timestamp": datetime.utcnow().isoformat()
                }
            )

            minutes_left = intervention_status.get("minutes_remaining", 0)
            logger.info(
                f"Message received during intervention - {minutes_left}min remaining. "
                f"Conversation: {context.conversation_id}"
            )

            return None  # Don't send bot response

        # 2. Process audio if needed
        message_text = ""
        message_type = message.get("type", "text")

        if message_type == "audio":
            audio_result = await self.audio_processor.process_whatsapp_audio(
                message.get("audio_data", {})
            )

            if not audio_result.get("success"):
                # Audio processing failed - return error message
                return AgentResponse(
                    text=audio_result.get("text", "Erro ao processar áudio"),
                    intent="error",
                    should_end=False
                )

            message_text = audio_result.get("text", "")
            logger.info(f"Audio transcribed: {message_text[:100]}...")

        else:
            message_text = message.get("content", "")

        # 3. Check if customer is requesting human intervention
        should_intervene = await intervention_service.should_auto_intervene(
            message=message_text,
            context=context.session_data
        )

        if should_intervene:
            await intervention_service.start_intervention(
                conversation_id=context.conversation_id,
                tenant_id=context.tenant_id,
                reason="Customer requested human assistance"
            )

            return AgentResponse(
                text="Entendi! Vou chamar um atendente para falar com você. Só um momento! 😊",
                intent="human_requested",
                requires_human=True,
                should_end=False
            )

        # 4. A/B Test: Check if should use fine-tuned extractor
        start_time = datetime.utcnow()

        if settings.USE_FINETUNED_EXTRACTOR:
            logger.info("🚀 Using FINE-TUNED EXTRACTOR (new system)")
            logger.info(f"[A/B TEST] System: FINE-TUNED | Conversation: {context.conversation_id}")

            # Extract information with fine-tuned model
            extracted_info = await self.message_extractor.extract(message_text)
            context.session_data["extracted_info"] = extracted_info

            # Log extracted info for debug
            logger.info(
                f"Extracted info - Product: {extracted_info['product']['name']} "
                f"(conf: {extracted_info['product']['confidence']:.2f}), "
                f"Address conf: {extracted_info['address']['confidence']:.2f}, "
                f"Payment: {extracted_info['payment']['method']} "
                f"(conf: {extracted_info['payment']['confidence']:.2f})"
            )

            # Detect intent (still needed for some routing decisions)
            intent = self._detect_intent(message_text)
            context.current_intent = intent

            # Route to sub-agent with extracted_info
            response = await self._route_to_agent(message_text, extracted_info, context, db)

            # Log metrics for A/B test
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            logger.info(
                f"[A/B TEST METRICS] System: FINE-TUNED | "
                f"Processing time: {processing_time:.2f}s | "
                f"Intent: {intent} | "
                f"Agent: {response.intent} | "
                f"Completed: {response.should_end}"
            )

        else:
            logger.info("📌 Using LEGACY SYSTEM (old intent-based routing)")
            logger.info(f"[A/B TEST] System: LEGACY | Conversation: {context.conversation_id}")

            # Detect intent using old method
            intent = self._detect_intent(message_text)
            context.current_intent = intent

            # Route to sub-agent using legacy method (no extracted_info)
            response = await self._route_to_agent_legacy(message_text, intent, context, db)

            # Log metrics for A/B test
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            logger.info(
                f"[A/B TEST METRICS] System: LEGACY | "
                f"Processing time: {processing_time:.2f}s | "
                f"Intent: {intent} | "
                f"Agent: {response.intent} | "
                f"Completed: {response.should_end}"
            )

        return response

    async def _route_to_agent(
        self,
        message: str,
        extracted_info: dict,
        context: AgentContext,
        db
    ) -> AgentResponse:
        """Route message to appropriate agent based on extracted_info and intent"""

        # Import agents here to avoid circular imports
        from app.agents.attendance import AttendanceAgent
        from app.agents.validation import ValidationAgent
        from app.agents.order import OrderAgent
        from app.agents.payment import PaymentAgent

        # Determine current conversation stage
        stage = context.session_data.get("stage", "greeting")
        intent = context.current_intent

        print(f"\n{'='*80}")
        print(f"ROUTING DEBUG")
        print(f"Intent: {intent}")
        print(f"Stage: {stage}")
        print(f"Message: {message[:50]}")
        print(f"Extracted - Product: {extracted_info['product']['name']} (conf: {extracted_info['product']['confidence']:.2f})")
        print(f"Extracted - Address: conf {extracted_info['address']['confidence']:.2f}")
        print(f"Extracted - Payment: {extracted_info['payment']['method']} (conf: {extracted_info['payment']['confidence']:.2f})")
        print(f"{'='*80}\n")

        logger.info(
            f"Routing - Intent: {intent}, Stage: {stage}, "
            f"Product conf: {extracted_info['product']['confidence']:.2f}, "
            f"Address conf: {extracted_info['address']['confidence']:.2f}"
        )

        # INTELLIGENT ROUTING based on extracted_info confidence scores
        # Priority order:
        # 1. Intent-based (greeting, help, etc)
        # 2. Extracted data with high confidence
        # 3. Stage-based fallback
        # 4. Default to attendance

        # 1. Greeting / Product inquiry / Help (always handle these first)
        if intent in ["greeting", "product_inquiry", "help"]:
            print(f"-> AttendanceAgent (intent: {intent})")
            agent = AttendanceAgent()
            return await agent.process(message, context)

        # 2. Product detected with high confidence -> OrderAgent
        if extracted_info["product"]["confidence"] > 0.7:
            print(f"-> OrderAgent (product detected: {extracted_info['product']['name']})")
            agent = OrderAgent()
            return await agent.process_with_extracted_data(extracted_info, context, db)

        # 3. Address detected with high confidence -> ValidationAgent
        if extracted_info["address"]["confidence"] > 0.7 or stage == "awaiting_address":
            print("-> ValidationAgent (address detected)")
            agent = ValidationAgent()
            return await agent.process_with_extracted_data(extracted_info, context, db)

        # 4. Payment detected with high confidence -> PaymentAgent
        if extracted_info["payment"]["confidence"] > 0.7 or stage == "payment":
            print(f"-> PaymentAgent (payment: {extracted_info['payment']['method']})")
            agent = PaymentAgent()
            return await agent.process_with_extracted_data(extracted_info, context, db)

        # 5. Stage-based routing (fallback for mid-conversation)
        if stage == "building_order":
            print("-> OrderAgent (stage: building_order)")
            agent = OrderAgent()
            return await agent.process(message, context)

        if stage == "confirming_order":
            print("-> OrderAgent (stage: confirming_order)")
            agent = OrderAgent()
            return await agent.process(message, context)

        # 6. Default to attendance agent for general messages
        print(f"-> AttendanceAgent (DEFAULT)")
        agent = AttendanceAgent()
        return await agent.process(message, context)

    async def _route_to_agent_legacy(
        self,
        message: str,
        intent: str,
        context: AgentContext,
        db
    ) -> AgentResponse:
        """
        Route message to appropriate agent based on INTENT ONLY (legacy system)

        This is the old routing logic WITHOUT MessageExtractor.
        Used when USE_FINETUNED_EXTRACTOR = False (A/B test fallback)
        """

        # Import agents here to avoid circular imports
        from app.agents.attendance import AttendanceAgent
        from app.agents.validation import ValidationAgent
        from app.agents.order import OrderAgent
        from app.agents.payment import PaymentAgent

        # Determine current conversation stage
        stage = context.session_data.get("stage", "greeting")

        logger.info(
            f"[LEGACY] Routing - Intent: {intent}, Stage: {stage}"
        )

        # Intent-based routing (old system)
        if intent in ["greeting", "product_inquiry", "help"]:
            agent = AttendanceAgent()
            return await agent.process(message, context)

        if intent == "order":
            agent = OrderAgent()
            return await agent.process(message, context)

        if intent == "address" or stage == "awaiting_address":
            agent = ValidationAgent()
            return await agent.process(message, context)

        if intent == "payment" or stage == "payment":
            agent = PaymentAgent()
            return await agent.process(message, context)

        # Stage-based routing (fallback for mid-conversation)
        if stage == "building_order":
            agent = OrderAgent()
            return await agent.process(message, context)

        if stage == "confirming_order":
            agent = OrderAgent()
            return await agent.process(message, context)

        # Default to attendance agent
        agent = AttendanceAgent()
        return await agent.process(message, context)

    def _build_system_prompt(self, context: AgentContext) -> str:
        """Build system prompt for master agent"""
        return """Você é o orquestrador principal de um sistema de atendimento via WhatsApp.

Suas responsabilidades:
- Entender a intenção do cliente
- Rotear para o agente especializado correto
- Manter contexto da conversa
- Detectar quando cliente precisa de atendente humano

Seja natural, educado e eficiente."""
