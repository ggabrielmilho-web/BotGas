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
        """Process a message and return a response"""
        pass

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

    def _detect_intent(self, message: str) -> str:
        """Detect user intent from message"""
        message_lower = message.lower()

        # Greetings
        greetings = ["oi", "olá", "bom dia", "boa tarde", "boa noite", "alo", "alô"]
        if any(word in message_lower for word in greetings):
            return "greeting"

        # Product inquiry
        product_words = ["produto", "preço", "quanto custa", "valor", "cardápio", "menu"]
        if any(word in message_lower for word in product_words):
            return "product_inquiry"

        # Order
        order_words = ["quero", "pedido", "comprar", "pedir"]
        if any(word in message_lower for word in order_words):
            return "make_order"

        # Address
        address_words = ["endereço", "entregar", "entrega", "rua", "avenida"]
        if any(word in message_lower for word in address_words):
            return "provide_address"

        # Payment
        payment_words = ["pagamento", "pagar", "pix", "dinheiro", "cartão"]
        if any(word in message_lower for word in payment_words):
            return "payment"

        # Help
        help_words = ["ajuda", "help", "como funciona", "não entendi"]
        if any(word in message_lower for word in help_words):
            return "help"

        return "general"

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
