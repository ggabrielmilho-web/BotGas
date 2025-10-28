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
from app.services.context_manager import ConversationContext
from app.services.intent_classifier import IntentClassifier
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
        self.intent_classifier = IntentClassifier()

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
        """
        Roteamento INTELIGENTE com contexto

        Prioridade de decisão:
        1. Contexto conversacional (bot perguntou algo? cliente respondeu?)
        2. Intent do usuário (saudação, ajuda, etc)
        3. Address com alta confidence (se já tem produto no carrinho)
        4. Product com alta confidence (validado pelo contexto)
        5. Payment com alta confidence
        6. Fallback para attendance
        """

        # Import agents
        from app.agents.attendance import AttendanceAgent
        from app.agents.validation import ValidationAgent
        from app.agents.order import OrderAgent
        from app.agents.payment import PaymentAgent

        # 1. Criar context manager para extrair informações do estado
        conv_context = ConversationContext(
            session_data=context.session_data,
            message_history=context.message_history
        )

        # Log contexto para debugging
        context_summary = conv_context.get_summary()
        logger.info(f"Context: {context_summary}")

        # 2. Classificar intent considerando contexto
        intent = await self.intent_classifier.classify(
            message=message,
            last_bot_message=conv_context.last_bot_question
        )

        logger.info(
            f"Routing - Intent: {intent}, Stage: {conv_context.current_stage}, "
            f"Has items: {conv_context.has_items_in_cart}, "
            f"Awaiting decision: {conv_context.awaiting_user_decision}"
        )

        # ========================================================================
        # PRIORIDADE 1: BOT PERGUNTOU ALGO E CLIENTE RESPONDEU
        # ========================================================================

        if conv_context.awaiting_user_decision:
            logger.info("Bot está aguardando decisão do usuário")

            if intent == "answer_yes":
                # Cliente quer continuar adicionando produtos
                logger.info("Cliente confirmou (answer_yes) → AttendanceAgent (mostrar produtos)")
                agent = AttendanceAgent()
                return await agent.process(message, context)

            elif intent == "answer_no":
                # Cliente quer finalizar/parar de adicionar
                logger.info("Cliente negou/finalizou (answer_no)")

                if conv_context.has_items_in_cart:
                    # Tem itens → pedir endereço
                    logger.info("Tem itens no carrinho → ValidationAgent (pedir endereço)")
                    agent = ValidationAgent()
                    return await agent.ask_for_address(context)
                else:
                    # Não tem itens → voltar ao início
                    logger.info("Carrinho vazio → AttendanceAgent")
                    agent = AttendanceAgent()
                    return await agent.process(message, context)

        # ========================================================================
        # PRIORIDADE 2: INTENTS ESPECÍFICOS (sempre tratados primeiro)
        # ========================================================================

        if intent == "greeting":
            logger.info("Intent: greeting → AttendanceAgent")
            agent = AttendanceAgent()
            return await agent.process(message, context)

        if intent == "product_inquiry":
            logger.info("Intent: product_inquiry → AttendanceAgent")
            agent = AttendanceAgent()
            return await agent.process(message, context)

        if intent == "help":
            logger.info("Intent: help → AttendanceAgent")
            agent = AttendanceAgent()
            return await agent.process(message, context)

        # ========================================================================
        # PRIORIDADE 3: ENDEREÇO DETECTADO (se já tem produto no carrinho)
        # ========================================================================

        if (extracted_info["address"]["confidence"] > 0.7
            and conv_context.has_items_in_cart):
            logger.info(
                f"Address detected (conf: {extracted_info['address']['confidence']:.2f}) "
                f"and has items → ValidationAgent"
            )
            agent = ValidationAgent()
            return await agent.process_with_extracted_data(extracted_info, context, db)

        # ========================================================================
        # PRIORIDADE 4: PRODUTO DETECTADO (validar contexto antes!)
        # ========================================================================

        if extracted_info["product"]["confidence"] > 0.7:
            logger.info(
                f"Product detected: {extracted_info['product']['name']} "
                f"(conf: {extracted_info['product']['confidence']:.2f})"
            )

            # VALIDAÇÃO: Se bot acabou de perguntar "deseja adicionar mais?"
            # E intent foi classificado como "answer_no"
            # NÃO adicionar produto (mesmo com confidence alta)

            if conv_context.awaiting_user_decision and intent == "answer_no":
                logger.warning(
                    "VALIDAÇÃO FALHOU: Product confidence alto MAS intent=answer_no. "
                    "Cliente não quer adicionar produto. Redirecionando..."
                )

                if conv_context.has_items_in_cart:
                    # Pedir endereço
                    agent = ValidationAgent()
                    return await agent.ask_for_address(context)
                else:
                    # Voltar ao início
                    agent = AttendanceAgent()
                    return await agent.process(message, context)

            # Contexto OK → processar produto
            logger.info("Contexto validado → OrderAgent")
            agent = OrderAgent()
            return await agent.process_with_extracted_data(extracted_info, context, db)

        # ========================================================================
        # PRIORIDADE 5: PAGAMENTO DETECTADO
        # ========================================================================

        if extracted_info["payment"]["confidence"] > 0.7:
            logger.info(
                f"Payment detected: {extracted_info['payment']['method']} "
                f"(conf: {extracted_info['payment']['confidence']:.2f}) → PaymentAgent"
            )
            agent = PaymentAgent()
            return await agent.process_with_extracted_data(extracted_info, context, db)

        # ========================================================================
        # PRIORIDADE 6: STAGE-BASED ROUTING (fallback)
        # ========================================================================

        stage = conv_context.current_stage

        if stage == "building_order":
            logger.info("Stage: building_order → OrderAgent")
            agent = OrderAgent()
            return await agent.process(message, context)

        if stage == "confirming_order":
            logger.info("Stage: confirming_order → OrderAgent")
            agent = OrderAgent()
            return await agent.process(message, context)

        if stage == "awaiting_address":
            logger.info("Stage: awaiting_address → ValidationAgent")
            agent = ValidationAgent()
            return await agent.process(message, context)

        if stage == "payment":
            logger.info("Stage: payment → PaymentAgent")
            agent = PaymentAgent()
            return await agent.process(message, context)

        # ========================================================================
        # FALLBACK: AttendanceAgent
        # ========================================================================

        logger.info("Fallback → AttendanceAgent")
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

    def _build_system_prompt_ai(self, context: AgentContext, db) -> str:
        """
        System prompt para MasterAgent decidir roteamento com IA

        NOVO: Usa LLM para decidir qual agente chamar (não IF/ELSE)
        """
        # Buscar dados do tenant
        from app.database.models import Tenant

        try:
            tenant = db.query(Tenant).filter(Tenant.id == context.tenant_id).first()
            company_name = tenant.company_name if tenant else "Distribuidora"
        except Exception as e:
            logger.error(f"Error fetching tenant: {e}")
            company_name = "Distribuidora"

        # Contexto formatado
        ctx = self._format_full_context(context)

        return f"""Você é o ORQUESTRADOR do sistema de atendimento via WhatsApp da {company_name}.

Sua ÚNICA responsabilidade é decidir QUAL agente especializado deve processar a mensagem do cliente.

{ctx}

AGENTES DISPONÍVEIS:
1. **AttendanceAgent**: Saudações, apresentar produtos, dúvidas gerais sobre a empresa
2. **OrderAgent**: Adicionar/remover itens do carrinho, gerenciar pedido
3. **ValidationAgent**: Validar endereço de entrega (após cliente fornecer)
4. **PaymentAgent**: Coletar forma de pagamento e finalizar pedido

ANÁLISE NECESSÁRIA:
1. O que o cliente está pedindo AGORA?
2. Qual o CONTEXTO da conversa (o que foi discutido antes)?
3. Se o bot fez uma pergunta, o cliente está RESPONDENDO ela?
4. Qual agente é mais ADEQUADO para esta situação?

REGRAS IMPORTANTES:
- Se stage="confirming_order" E cliente CONFIRMA (sim/ok/pode/beleza/etc) → PaymentAgent (próximo é pagamento)
- Se stage="building_order" E cliente CONFIRMA adicionar mais → AttendanceAgent (mostrar produtos)
- Se stage="awaiting_address" → ValidationAgent
- Se stage="payment" → PaymentAgent
- Se cliente menciona PRODUTO → OrderAgent
- Se cliente menciona ENDEREÇO → ValidationAgent
- Se cliente SAÚDA ou pede INFO → AttendanceAgent

ATENÇÃO: CONTEXTO > palavras isoladas
- "pode seguir" após confirmar endereço = ir para pagamento
- "pode seguir" sem contexto = pedir esclarecimento

RESPONDA **APENAS** EM JSON (não adicione texto antes ou depois):
{{
    "raciocinio": "breve explicação da sua decisão (1 frase)",
    "agente": "AttendanceAgent" | "OrderAgent" | "ValidationAgent" | "PaymentAgent",
    "contexto_adicional": {{
        "cliente_confirmando": true/false,
        "cliente_finalizando": true/false,
        "cliente_corrigindo": true/false
    }}
}}"""

    async def _execute_decision(self, decision: dict, context: AgentContext, db, message_text: str) -> AgentResponse:
        """
        Executa decisão do LLM: roteia para agente escolhido

        NOVO: Implementação do método abstrato do BaseAgent
        ATUALIZADO: Chama métodos *_with_ai() dos agentes (não process() antigo)
        """
        agente_nome = decision.get("agente", "AttendanceAgent")
        raciocinio = decision.get("raciocinio", "")

        logger.info(f"🤖 MasterAgent decidiu: {agente_nome} | Razão: {raciocinio}")

        # Importar agentes
        from app.agents.attendance import AttendanceAgent
        from app.agents.order import OrderAgent
        from app.agents.validation import ValidationAgent
        from app.agents.payment import PaymentAgent

        # Instanciar e chamar agente com IA (process_with_ai)
        try:
            if agente_nome == "AttendanceAgent":
                agent = AttendanceAgent()
                return await agent.process_with_ai(message_text, context, db)

            elif agente_nome == "OrderAgent":
                agent = OrderAgent()
                return await agent.process_with_ai(message_text, context, db)

            elif agente_nome == "ValidationAgent":
                agent = ValidationAgent()
                return await agent.process_with_ai(message_text, context, db)

            elif agente_nome == "PaymentAgent":
                agent = PaymentAgent()
                return await agent.process_with_ai(message_text, context, db)

            else:
                # Fallback
                logger.warning(f"⚠️ Agente desconhecido: {agente_nome}. Usando AttendanceAgent.")
                agent = AttendanceAgent()
                return await agent.process_with_ai(message_text, context, db)

        except AttributeError as e:
            # Se agente não tem process_with_ai, usar process() antigo
            logger.warning(f"⚠️ Agente {agente_nome} não tem process_with_ai. Usando process() legado. Erro: {e}")

            if agente_nome == "AttendanceAgent":
                agent = AttendanceAgent()
            elif agente_nome == "OrderAgent":
                agent = OrderAgent()
            elif agente_nome == "ValidationAgent":
                agent = ValidationAgent()
            elif agente_nome == "PaymentAgent":
                agent = PaymentAgent()
            else:
                agent = AttendanceAgent()

            return await agent.process(message_text, context)

    async def process_with_ai_routing(self, message: Dict[str, Any], context: AgentContext, db) -> Optional[AgentResponse]:
        """
        NOVO: Process message with AI-powered routing (substitui process antigo)

        Fluxo:
        1. Verificar intervenção humana
        2. Processar áudio se necessário
        3. LLM decide roteamento (não IF/ELSE!)
        4. Executar decisão
        """
        intervention_service = InterventionService(db)

        # 1. Check human intervention status (manter lógica existente)
        intervention_status = await intervention_service.check_intervention_status(
            tenant_id=context.tenant_id,
            customer_phone=context.customer_phone,
            conversation_id=context.conversation_id
        )

        if intervention_status.get("is_active"):
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
                f"Message during intervention - {minutes_left}min remaining. "
                f"Conversation: {context.conversation_id}"
            )
            return None

        # 2. Process audio if needed (manter lógica existente)
        message_text = ""
        message_type = message.get("type", "text")

        if message_type == "audio":
            audio_result = await self.audio_processor.process_whatsapp_audio(
                message.get("audio_data", {})
            )

            if not audio_result.get("success"):
                return AgentResponse(
                    text=audio_result.get("text", "Erro ao processar áudio"),
                    intent="error",
                    should_end=False
                )

            message_text = audio_result.get("text", "")
            logger.info(f"Audio transcribed: {message_text[:100]}...")
        else:
            message_text = message.get("content", "")

        # 3. Check if customer is requesting human intervention (manter lógica)
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

        # 4. NOVO: LLM decide roteamento (substituindo IF/ELSE)
        from langchain.schema import SystemMessage, HumanMessage

        system_prompt = self._build_system_prompt_ai(context, db)
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Mensagem do cliente: {message_text}")
        ]

        logger.info("🔄 Calling LLM for routing decision...")
        response = await self._call_llm(messages)
        decision = self._parse_llm_response(response)

        # 5. Executar decisão
        return await self._execute_decision(decision, context, db, message_text)

    def _build_system_prompt(self, context: AgentContext) -> str:
        """Build system prompt for master agent (legacy - kept for compatibility)"""
        return """Você é o orquestrador principal de um sistema de atendimento via WhatsApp.

Suas responsabilidades:
- Entender a intenção do cliente
- Rotear para o agente especializado correto
- Manter contexto da conversa
- Detectar quando cliente precisa de atendente humano

Seja natural, educado e eficiente."""
