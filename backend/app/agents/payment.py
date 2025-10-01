"""
Payment Agent - Handles payment method selection (simplified, no validation)
"""
from typing import Dict, Any, Optional
from uuid import UUID
from datetime import datetime
import logging

from app.agents.base import BaseAgent, AgentContext, AgentResponse
from app.database.models import Tenant
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class PaymentAgent(BaseAgent):
    """
    Handles payment method selection

    Responsibilities:
    - Ask for payment method
    - Show PIX details if selected
    - Confirm payment method
    - Finalize order

    NOTE: This is simplified - no actual payment validation
    """

    def __init__(self):
        super().__init__(model_name="gpt-4-turbo-preview", temperature=0.5)

    async def process(self, message: str, context: AgentContext) -> AgentResponse:
        """Process payment selection"""

        from app.database.session import get_db

        db = next(get_db())

        try:
            # Get tenant
            tenant = db.query(Tenant).filter(Tenant.id == context.tenant_id).first()

            if not tenant:
                return AgentResponse(
                    text="Erro ao processar pagamento. Tente novamente.",
                    intent="error",
                    should_end=True
                )

            # Get current order
            current_order = context.session_data.get("current_order")

            if not current_order or not current_order.get("items"):
                return AgentResponse(
                    text="Não encontrei um pedido ativo. Vamos começar de novo?",
                    intent="error",
                    should_end=False
                )

            # Detect payment method
            payment_method = await self._detect_payment_method(message, tenant)

            if not payment_method:
                # Couldn't detect, ask again
                return AgentResponse(
                    text=await self._build_payment_options(tenant, current_order),
                    intent="payment_method_needed",
                    should_end=False
                )

            # Process based on payment method
            if payment_method == "pix":
                response_text = await self._handle_pix_payment(tenant, current_order)
            elif payment_method == "dinheiro":
                response_text = await self._handle_cash_payment(tenant, current_order)
            elif payment_method == "cartao":
                response_text = await self._handle_card_payment(tenant, current_order)
            else:
                response_text = await self._build_payment_options(tenant, current_order)

            # Create order in database
            from app.agents.order import OrderAgent

            order_agent = OrderAgent()
            order_obj = await order_agent.create_order_in_db(
                order=current_order,
                context=context,
                payment_method=payment_method,
                db=db
            )

            # Add order confirmation
            response_text += f"""

✅ *Pedido Confirmado!*

📱 *Número do pedido:* #{order_obj.order_number}

Seu pedido foi registrado e já estamos preparando!

Obrigado pela preferência! 😊"""

            return AgentResponse(
                text=response_text,
                intent="payment_completed",
                context_updates={
                    "stage": "completed",
                    "order_id": str(order_obj.id),
                    "order_number": order_obj.order_number
                },
                should_end=True,
                metadata={
                    "order_id": str(order_obj.id),
                    "order_number": order_obj.order_number,
                    "total": current_order["total"]
                }
            )

        except Exception as e:
            logger.error(f"Error in payment agent: {e}")
            return AgentResponse(
                text="Desculpe, tive um problema ao processar o pagamento. Um atendente vai entrar em contato.",
                intent="error",
                requires_human=True,
                should_end=False
            )

        finally:
            db.close()

    async def _detect_payment_method(self, message: str, tenant: Tenant) -> Optional[str]:
        """Detect payment method from message"""

        message_lower = message.lower()

        # PIX
        if "pix" in message_lower:
            return "pix" if tenant.pix_enabled else None

        # Cash
        cash_words = ["dinheiro", "espécie", "cash"]
        if any(word in message_lower for word in cash_words):
            return "dinheiro"

        # Card
        card_words = ["cartão", "cartao", "débito", "debito", "crédito", "credito", "card"]
        if any(word in message_lower for word in card_words):
            return "cartao"

        return None

    async def _build_payment_options(self, tenant: Tenant, order: Dict[str, Any]) -> str:
        """Build payment options message"""

        total_str = f"R$ {order['total']:.2f}".replace(".", ",")

        message = f"""💰 *Total do pedido: {total_str}*

Como você quer pagar?

"""

        # Available payment methods
        methods = tenant.payment_methods or ["Dinheiro"]

        for method in methods:
            if method.lower() == "pix" and tenant.pix_enabled:
                message += "• 📱 PIX\n"
            elif method.lower() == "dinheiro":
                message += "• 💵 Dinheiro\n"
            elif method.lower() in ["cartao", "cartão"]:
                message += "• 💳 Cartão (débito/crédito)\n"

        message += "\nEscolha uma opção acima."

        return message

    async def _handle_pix_payment(self, tenant: Tenant, order: Dict[str, Any]) -> str:
        """Handle PIX payment"""

        if not tenant.pix_enabled or not tenant.pix_key:
            return "Desculpe, PIX não está disponível no momento. Escolha outra forma de pagamento."

        total_str = f"R$ {order['total']:.2f}".replace(".", ",")

        message = f"""✅ Pagamento via PIX

💰 *Valor:* {total_str}

📱 *Chave PIX:*
`{tenant.pix_key}`

👤 *Nome:* {tenant.pix_name or tenant.company_name}

"""

        if tenant.payment_instructions:
            message += f"\n📝 {tenant.payment_instructions}\n"

        message += """
Após realizar o pagamento, pode enviar o comprovante ou apenas confirmar.

Seu pedido já foi registrado e será preparado!"""

        return message

    async def _handle_cash_payment(self, tenant: Tenant, order: Dict[str, Any]) -> str:
        """Handle cash payment"""

        total_str = f"R$ {order['total']:.2f}".replace(".", ",")

        message = f"""✅ Pagamento em Dinheiro

💵 *Valor:* {total_str}

Você vai pagar em dinheiro na entrega.

💡 *Dica:* Prepare o valor exato ou nos avise se precisa de troco!"""

        return message

    async def _handle_card_payment(self, tenant: Tenant, order: Dict[str, Any]) -> str:
        """Handle card payment"""

        total_str = f"R$ {order['total']:.2f}".replace(".", ",")

        message = f"""✅ Pagamento no Cartão

💳 *Valor:* {total_str}

Você vai pagar com cartão na entrega.

Aceitamos débito e crédito!"""

        return message

    def _build_system_prompt(self, context: AgentContext) -> str:
        """Build system prompt for payment agent"""

        return """Você é um assistente de pagamento.

Suas funções:
- Identificar forma de pagamento escolhida
- Fornecer instruções de pagamento
- Confirmar pedido

Seja claro e educado. Não valide pagamentos, apenas registre a forma escolhida."""
