"""
Base classes for LangChain agents
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
from uuid import UUID
import logging

from langchain.schema import SystemMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class AgentContext(BaseModel):
    """Context shared between agents"""
    tenant_id: UUID
    customer_phone: str
    conversation_id: UUID
    session_data: Dict[str, Any] = {}
    message_history: List[Dict[str, Any]] = []
    current_intent: Optional[str] = None
    current_step: Optional[str] = None

    class Config:
        arbitrary_types_allowed = True


class AgentResponse(BaseModel):
    """Standard agent response"""
    text: str
    intent: Optional[str] = None
    next_agent: Optional[str] = None
    context_updates: Dict[str, Any] = {}
    should_end: bool = False
    requires_human: bool = False
    metadata: Dict[str, Any] = {}


class BaseAgent(ABC):
    """Base class for all agents"""

    def __init__(self, model_name: str = "gpt-4-turbo-preview", temperature: float = 0.7):
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=temperature
        )
        self.agent_name = self.__class__.__name__

    @abstractmethod
    async def process(self, message: str, context: AgentContext) -> AgentResponse:
        """
        Process a message and return a response

        NOTE: Most agents should override this method to use the new AI-based flow:
        1. Build system prompt with _build_system_prompt()
        2. Call LLM with _call_llm()
        3. Parse JSON response with _parse_llm_response()
        4. Execute decision with _execute_decision()
        """
        pass

    @abstractmethod
    async def _execute_decision(self, decision: dict, context: AgentContext) -> AgentResponse:
        """
        Execute decision made by LLM

        Each agent must implement how to execute the decision returned by the LLM.
        The decision is a parsed JSON dict from _parse_llm_response().

        Args:
            decision: Dict with LLM's decision (parsed JSON)
            context: AgentContext

        Returns:
            AgentResponse
        """
        pass

    async def process_with_extracted_data(
        self,
        extracted_info: dict,
        context: AgentContext,
        db
    ) -> AgentResponse:
        """
        Process message with pre-extracted data (optional)

        This method allows agents to receive pre-extracted information
        from MessageExtractor instead of parsing the raw message.

        Override this method in agents that support extracted_info.
        Default implementation falls back to regular process method.

        Args:
            extracted_info: Dict with product, address, payment, metadata
            context: AgentContext
            db: Database session

        Returns:
            AgentResponse
        """
        # Default: call regular process with empty message
        return await self.process("", context)

    def _build_system_prompt(self, context: AgentContext) -> str:
        """Build system prompt for this agent"""
        return f"""Você é um assistente virtual para distribuidora de gás e água.
Seja educado, objetivo e eficiente.
Sempre confirme informações importantes antes de prosseguir."""

    def _build_messages(self, message: str, context: AgentContext, system_prompt: Optional[str] = None) -> List:
        """Build message list for LLM"""
        messages = []

        # System message
        if system_prompt is None:
            system_prompt = self._build_system_prompt(context)
        messages.append(SystemMessage(content=system_prompt))

        # Message history (last 10 messages)
        history = context.message_history[-10:] if context.message_history else []
        for msg in history:
            if msg.get("role") == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg.get("role") == "assistant":
                messages.append(AIMessage(content=msg["content"]))

        # Current message
        messages.append(HumanMessage(content=message))

        return messages

    async def _call_llm(self, messages: List) -> str:
        """Call LLM and get response"""
        try:
            response = await self.llm.ainvoke(messages)
            return response.content
        except Exception as e:
            logger.error(f"Error calling LLM in {self.agent_name}: {e}")
            return "Desculpe, tive um problema ao processar sua mensagem. Pode repetir?"

    # REMOVED: _detect_intent() method
    # This was pure IF/ELSE with keyword lists
    # Now replaced by LLM-based decision making in each agent

    def _parse_llm_response(self, response_text: str) -> dict:
        """
        Parse resposta JSON do LLM

        LLM deve retornar JSON estruturado.
        Este método extrai e valida o JSON.
        """
        import json
        import re

        try:
            # Tentar parse direto
            return json.loads(response_text)
        except json.JSONDecodeError:
            # Se falhar, buscar JSON entre ```json e ```
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(1))
                except json.JSONDecodeError:
                    pass

            # Se ainda falhar, buscar qualquer { ... }
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(0))
                except json.JSONDecodeError:
                    pass

            # Falha total
            logger.error(f"Não foi possível parsear JSON: {response_text}")
            return {"erro": "resposta_invalida", "texto": response_text}

    def _format_full_context(self, context: AgentContext) -> str:
        """
        Formata contexto completo para o prompt

        Inclui:
        - Dados da sessão
        - Estado do carrinho
        - Histórico de mensagens
        - Informações do cliente
        """
        # Carrinho
        current_order = context.session_data.get("current_order", {})
        items = current_order.get("items", [])
        cart_summary = f"{len(items)} item(s) - R$ {current_order.get('total', 0):.2f}" if items else "vazio"

        # Stage
        stage = context.session_data.get("stage", "início")

        # Endereço
        has_address = bool(context.session_data.get("delivery_address"))

        # Histórico
        history_text = self._format_history_text(context.message_history[-5:])

        return f"""
CONTEXTO ATUAL:
- Stage: {stage}
- Carrinho: {cart_summary}
- Endereço validado: {has_address}
- Cliente: {context.customer_phone}

HISTÓRICO RECENTE (últimas 5 mensagens):
{history_text}
"""

    def _format_history_text(self, messages: list) -> str:
        """Formata histórico para texto legível"""
        if not messages:
            return "(nenhuma mensagem anterior)"

        text = ""
        for msg in messages:
            role = "Cliente" if msg.get("role") == "user" else "Bot"
            content = msg.get("content", "")[:100]
            text += f"- {role}: {content}...\n"

        return text

    def _update_context(self, context: AgentContext, updates: Dict[str, Any]) -> AgentContext:
        """Update context with new data"""
        context.session_data.update(updates)
        return context

    def _log_interaction(self, message: str, response: str, context: AgentContext):
        """Log agent interaction"""
        logger.info(f"""
        Agent: {self.agent_name}
        Tenant: {context.tenant_id}
        Customer: {context.customer_phone}
        Message: {message[:100]}...
        Response: {response[:100]}...
        """)
