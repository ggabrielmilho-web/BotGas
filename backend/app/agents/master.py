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

        # 4. Detect intent and route to appropriate agent
        intent = self._detect_intent(message_text)
        context.current_intent = intent

        # 5. Route to sub-agent
        response = await self._route_to_agent(message_text, intent, context, db)

        return response

    async def _route_to_agent(
        self,
        message: str,
        intent: str,
        context: AgentContext,
        db
    ) -> AgentResponse:
        """Route message to appropriate agent based on intent"""

        # Import agents here to avoid circular imports
        from app.agents.attendance import AttendanceAgent
        from app.agents.validation import ValidationAgent
        from app.agents.order import OrderAgent
        from app.agents.payment import PaymentAgent

        # Determine current conversation stage
        stage = context.session_data.get("stage", "greeting")

        # Greeting / Product inquiry
        if intent in ["greeting", "product_inquiry", "help", "general"]:
            agent = AttendanceAgent()
            return await agent.process(message, context)

        # Address validation
        elif intent == "provide_address" or stage == "awaiting_address":
            agent = ValidationAgent()
            return await agent.process(message, context)

        # Order management
        elif intent == "make_order" or stage == "building_order":
            agent = OrderAgent()
            return await agent.process(message, context)

        # Payment
        elif intent == "payment" or stage == "payment":
            agent = PaymentAgent()
            return await agent.process(message, context)

        # Default to attendance agent
        else:
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
