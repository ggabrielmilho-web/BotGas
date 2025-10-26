"""
Intent Classifier - Classifica intenção do usuário considerando contexto
"""
import logging
from typing import Optional
from openai import AsyncOpenAI
from app.core.config import settings

logger = logging.getLogger(__name__)


class IntentClassifier:
    """
    Classifica a intenção do usuário baseado na mensagem E no contexto

    Usa GPT-4-mini com prompt curto e focado para economizar tokens.
    Diferente do MessageExtractor que extrai dados, este classifica
    a AÇÃO/INTENÇÃO do usuário.
    """

    def __init__(self):
        """Inicializa o classificador"""
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "gpt-4o-mini"

    async def classify(
        self,
        message: str,
        last_bot_message: Optional[str] = None
    ) -> str:
        """
        Classifica a intenção do usuário

        Args:
            message: Mensagem do usuário
            last_bot_message: Última mensagem do bot (contexto)

        Returns:
            Intent classificado:
            - "answer_yes": Usuário concordou/confirmou
            - "answer_no": Usuário negou/recusou/finalizou
            - "greeting": Saudação
            - "product_inquiry": Pergunta sobre produtos
            - "help": Pedido de ajuda humana
            - "general": Outros casos
        """

        # Construir prompt curto e focado
        if last_bot_message:
            prompt = f"""Classifique a intenção do cliente.

CONTEXTO:
Última mensagem do bot: "{last_bot_message}"

MENSAGEM DO CLIENTE:
"{message}"

CLASSIFICAÇÕES POSSÍVEIS:
- answer_yes: Cliente concordou/confirmou (sim, ok, pode, beleza, isso mesmo, confirmo)
- answer_no: Cliente negou/recusou/finalizou (não, nao, finalizar, pronto, só isso, fechar)
- greeting: Saudação (oi, olá, bom dia, etc)
- product_inquiry: Pergunta sobre produtos (produtos, o que tem, cardápio, catálogo)
- help: Pedido de ajuda humana (falar com atendente, preciso de ajuda)
- general: Outros casos

IMPORTANTE: Se o bot perguntou "deseja adicionar mais?" e cliente disse "finalizar/não/pronto",
a classificação é "answer_no", NÃO "general".

Responda APENAS com a classificação (uma palavra)."""
        else:
            prompt = f"""Classifique a intenção do cliente.

MENSAGEM: "{message}"

CLASSIFICAÇÕES:
- answer_yes: sim, ok, pode, confirmo
- answer_no: não, finalizar, pronto
- greeting: oi, olá, bom dia
- product_inquiry: produtos, cardápio
- help: falar com atendente
- general: outros

Responda APENAS a classificação."""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=10,  # Resposta curta (economia!)
                temperature=0.1  # Determinístico
            )

            intent = response.choices[0].message.content.strip().lower()

            # Validar resposta
            valid_intents = [
                "answer_yes", "answer_no", "greeting",
                "product_inquiry", "help", "general"
            ]

            if intent not in valid_intents:
                logger.warning(f"Intent inválido retornado: {intent}. Usando 'general'.")
                intent = "general"

            logger.info(f"IntentClassifier: '{message[:30]}...' → {intent}")

            return intent

        except Exception as e:
            logger.error(f"Erro no IntentClassifier: {e}")
            # Fallback seguro
            return "general"

    async def is_affirmative(self, message: str) -> bool:
        """
        Verifica se mensagem é afirmativa (sim/ok/pode)

        Helper method para casos simples

        Args:
            message: Mensagem do usuário

        Returns:
            True se é afirmativa, False caso contrário
        """
        message_lower = message.lower().strip()

        affirmative_words = [
            "sim", "s", "yes", "ok", "pode", "beleza",
            "certo", "isso", "confirmo", "perfeito", "exato"
        ]

        return any(word == message_lower for word in affirmative_words)

    async def is_negative(self, message: str) -> bool:
        """
        Verifica se mensagem é negativa (não/finalizar)

        Helper method para casos simples

        Args:
            message: Mensagem do usuário

        Returns:
            True se é negativa, False caso contrário
        """
        message_lower = message.lower().strip()

        negative_words = [
            "não", "nao", "n", "no", "finalizar", "pronto",
            "só isso", "somente", "apenas isso", "fechar", "terminar"
        ]

        return any(word in message_lower for word in negative_words)
