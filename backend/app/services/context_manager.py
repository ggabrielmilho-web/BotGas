"""
Context Manager - Gerencia contexto de conversas
"""
from typing import Dict, Any, List, Optional


class ConversationContext:
    """
    Gerencia contexto entre chamadas de agentes

    Responsável por extrair informações do estado da conversa
    que ajudam na tomada de decisão do roteamento.
    """

    def __init__(self, session_data: Dict[str, Any], message_history: List[Dict[str, Any]]):
        """
        Inicializa o context manager

        Args:
            session_data: Dados da sessão (current_order, stage, etc)
            message_history: Histórico de mensagens da conversa
        """
        self.session_data = session_data
        self.message_history = message_history

    @property
    def last_bot_message(self) -> Dict[str, Any]:
        """
        Retorna a última mensagem enviada pelo bot

        Returns:
            Dict com role, content, intent, timestamp
        """
        for msg in reversed(self.message_history):
            if msg.get("role") == "assistant":
                return msg
        return {}

    @property
    def last_bot_question(self) -> str:
        """
        Retorna o texto da última pergunta do bot

        Returns:
            String com a pergunta ou vazio
        """
        last_msg = self.last_bot_message
        return last_msg.get("content", "")

    @property
    def last_bot_intent(self) -> str:
        """
        Retorna o intent da última mensagem do bot

        Returns:
            String com o intent ou vazio
        """
        last_msg = self.last_bot_message
        return last_msg.get("intent", "")

    @property
    def has_items_in_cart(self) -> bool:
        """
        Verifica se há itens no carrinho de compras

        Returns:
            True se há itens, False caso contrário
        """
        current_order = self.session_data.get("current_order", {})
        items = current_order.get("items", [])
        return bool(items)

    @property
    def cart_items_count(self) -> int:
        """
        Retorna quantidade de itens no carrinho

        Returns:
            Número de itens
        """
        current_order = self.session_data.get("current_order", {})
        items = current_order.get("items", [])
        return len(items)

    @property
    def awaiting_user_decision(self) -> bool:
        """
        Verifica se bot está esperando uma decisão do usuário (sim/não)

        Analisa a última pergunta do bot para detectar se é uma pergunta
        que espera confirmação ou negação.

        Returns:
            True se está esperando decisão, False caso contrário
        """
        last_question = self.last_bot_question.lower()

        # Keywords que indicam que bot está esperando decisão
        decision_keywords = [
            "deseja adicionar mais",
            "quer adicionar",
            "mais alguma coisa",
            "ou finalizar",
            "podemos continuar",
            "está correto",
            "confirma",
            "tudo certo"
        ]

        return any(keyword in last_question for keyword in decision_keywords)

    @property
    def current_stage(self) -> str:
        """
        Retorna o stage atual da conversa

        Returns:
            String com o stage (greeting, building_order, etc)
        """
        return self.session_data.get("stage", "greeting")

    @property
    def has_delivery_address(self) -> bool:
        """
        Verifica se endereço de entrega já foi definido

        Returns:
            True se tem endereço, False caso contrário
        """
        return bool(self.session_data.get("delivery_address"))

    def get_summary(self) -> Dict[str, Any]:
        """
        Retorna resumo do contexto para debugging

        Returns:
            Dict com informações principais do contexto
        """
        return {
            "stage": self.current_stage,
            "has_items": self.has_items_in_cart,
            "items_count": self.cart_items_count,
            "has_address": self.has_delivery_address,
            "awaiting_decision": self.awaiting_user_decision,
            "last_bot_intent": self.last_bot_intent,
            "last_question_preview": self.last_bot_question[:50] + "..." if len(self.last_bot_question) > 50 else self.last_bot_question
        }
