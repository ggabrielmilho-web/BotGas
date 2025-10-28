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

        from app.database.base import get_db

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

    async def process_with_extracted_data(
        self,
        extracted_info: dict,
        context: AgentContext,
        db: Session
    ) -> AgentResponse:
        """
        Process payment with pre-extracted data from MessageExtractor

        Args:
            extracted_info: Information extracted by fine-tuned model
            context: AgentContext
            db: Database session

        Returns:
            AgentResponse
        """
        try:
            # Get tenant
            tenant = db.query(Tenant).filter(Tenant.id == context.tenant_id).first()

            if not tenant:
                return AgentResponse(
                    text="Erro ao processar pagamento. Tente novamente.",
                    intent="error",
                    should_end=True
                )

            # Get payment information from extracted_info
            payment_info = extracted_info.get("payment", {})
            payment_method = payment_info.get("method", "unknown")
            change_for = payment_info.get("change_for")
            confidence = payment_info.get("confidence", 0.0)

            # If confidence is low or method unknown, ask customer
            if confidence < 0.7 or payment_method == "unknown":
                current_order = context.session_data.get("current_order")
                return AgentResponse(
                    text=await self._build_payment_options(tenant, current_order),
                    intent="payment_method_needed",
                    should_end=False
                )

            # Get current order
            current_order = context.session_data.get("current_order")

            if not current_order or not current_order.get("items"):
                return AgentResponse(
                    text="Não encontrei um pedido ativo. Vamos começar de novo?",
                    intent="error",
                    should_end=False
                )

            # Add change information to context if present
            if change_for:
                context.session_data["change_for"] = change_for

            # Process based on payment method
            if payment_method == "pix":
                response_text = await self._handle_pix_payment(tenant, current_order)
            elif payment_method == "dinheiro":
                response_text = await self._handle_cash_payment(tenant, current_order, change_for)
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
            logger.error(f"Error in process_with_extracted_data: {e}")
            return AgentResponse(
                text="Desculpe, tive um problema ao processar o pagamento. Um atendente vai entrar em contato.",
                intent="error",
                requires_human=True,
                should_end=False
            )

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

    async def _handle_cash_payment(self, tenant: Tenant, order: Dict[str, Any], change_for: Optional[float] = None) -> str:
        """Handle cash payment"""

        total_str = f"R$ {order['total']:.2f}".replace(".", ",")

        message = f"""✅ Pagamento em Dinheiro

💵 *Valor:* {total_str}

Você vai pagar em dinheiro na entrega."""

        if change_for:
            change_str = f"R$ {change_for:.2f}".replace(".", ",")
            change_amount = change_for - order['total']
            change_amount_str = f"R$ {change_amount:.2f}".replace(".", ",")
            message += f"""

💵 *Troco para:* {change_str}
💰 *Troco:* {change_amount_str}"""
        else:
            message += """

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

    # ================================================================
    # NOVOS MÉTODOS COM IA REAL (não IF/ELSE)
    # ================================================================

    def _build_system_prompt_ai(self, context: AgentContext, db) -> str:
        """
        System prompt para PaymentAgent detectar forma de pagamento com IA

        NOVO: Usa LLM para detectar pagamento (não listas de palavras)
        """
        from app.database.models import Tenant

        try:
            tenant = db.query(Tenant).filter(Tenant.id == context.tenant_id).first()
            payment_methods = tenant.payment_methods or ["Dinheiro"]
            pix_enabled = tenant.pix_enabled

            # Pedido atual
            current_order = context.session_data.get("current_order", {})
            total = current_order.get("total", 0)
        except Exception as e:
            logger.error(f"Error building system prompt: {e}")
            payment_methods = ["Dinheiro"]
            pix_enabled = False
            total = 0

        ctx = self._format_full_context(context)

        methods_text = "\n".join([f"- {m}" for m in payment_methods])

        return f"""Você é responsável por coletar a FORMA DE PAGAMENTO do cliente.

{ctx}

VALOR TOTAL DO PEDIDO: R$ {total:.2f}

FORMAS DE PAGAMENTO ACEITAS:
{methods_text}
{"- PIX (disponível)" if pix_enabled else ""}

RESPONSABILIDADES:
1. Detectar qual forma de pagamento o cliente escolheu
2. Se for DINHEIRO, perguntar se precisa de troco
3. Confirmar forma de pagamento

REGRAS DE DETECÇÃO:
1. Variações comuns:
   - "pix" / "no pix" / "vou pagar no pix" = PIX
   - "dinheiro" / "espécie" / "na entrega" / "cash" = Dinheiro
   - "cartão" / "cartao" / "débito" / "credito" / "na maquininha" = Cartão
   - "100 reais" (se total < 100) = Dinheiro com troco para R$ 100

2. Se cliente menciona valor maior que o total:
   - Assumir dinheiro com troco
   - Exemplo: total R$ 65, cliente diz "100" = troco para R$ 100

3. Se não conseguir detectar:
   - Pedir esclarecimento educadamente

RESPONDA **APENAS** EM JSON:
{{
    "metodo": "pix" | "dinheiro" | "cartao" | "desconhecido",
    "troco_para": valor numérico ou null,
    "confirmado": true/false,
    "mensagem_cliente": "texto amigável da resposta",
    "proximo_passo": "confirmar_pedido" | "pedir_troco" | "esclarecer"
}}

IMPORTANTE: Seja amigável e confirme antes de finalizar."""

    async def _execute_decision_ai(self, decision: dict, context: AgentContext, db) -> AgentResponse:
        """
        Executa decisão do LLM para processar pagamento

        NOVO: Implementação com IA (não IF/ELSE)
        """
        try:
            metodo = decision.get("metodo", "desconhecido")
            mensagem = decision.get("mensagem_cliente", "")
            troco_para = decision.get("troco_para")
            confirmado = decision.get("confirmado", False)

            logger.info(f"💳 PaymentAgent: Método={metodo}, Troco={troco_para}, Confirmado={confirmado}")

            # Se não detectou ou não confirmou
            if metodo == "desconhecido" or not confirmado:
                tenant = db.query(Tenant).filter(Tenant.id == context.tenant_id).first()
                current_order = context.session_data.get("current_order", {})

                return AgentResponse(
                    text=await self._build_payment_options(tenant, current_order),
                    intent="payment_method_needed",
                    context_updates={"stage": "payment"},
                    should_end=False
                )

            # Método detectado e confirmado
            tenant = db.query(Tenant).filter(Tenant.id == context.tenant_id).first()
            current_order = context.session_data.get("current_order")

            if not current_order or not current_order.get("items"):
                return AgentResponse(
                    text="Não encontrei um pedido ativo. Vamos começar de novo?",
                    intent="error",
                    should_end=False
                )

            # Adicionar troco ao contexto
            if troco_para:
                context.session_data["change_for"] = troco_para

            # Processar baseado no método
            if metodo == "pix":
                response_text = await self._handle_pix_payment(tenant, current_order)
            elif metodo == "dinheiro":
                response_text = await self._handle_cash_payment(tenant, current_order, troco_para)
            elif metodo == "cartao":
                response_text = await self._handle_card_payment(tenant, current_order)
            else:
                return AgentResponse(
                    text=await self._build_payment_options(tenant, current_order),
                    intent="payment_method_needed",
                    should_end=False
                )

            # Criar pedido no banco
            from app.agents.order import OrderAgent
            order_agent = OrderAgent()
            order_obj = await order_agent.create_order_in_db(
                order=current_order,
                context=context,
                payment_method=metodo,
                db=db
            )

            # Confirmação
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
            logger.error(f"Error in _execute_decision_ai: {e}")
            return AgentResponse(
                text="Desculpe, tive um problema ao processar o pagamento.",
                intent="error",
                should_end=False
            )

    async def process_with_ai(self, message: str, context: AgentContext, db) -> AgentResponse:
        """
        NOVO: Process with AI-powered payment detection (não IF/ELSE)

        Fluxo:
        1. LLM detecta forma de pagamento
        2. Se dinheiro, detecta necessidade de troco
        3. Confirma e cria pedido
        """
        from langchain.schema import SystemMessage, HumanMessage

        try:
            system_prompt = self._build_system_prompt_ai(context, db)
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"Cliente: {message}")
            ]

            logger.info("🔄 PaymentAgent calling LLM...")
            response = await self._call_llm(messages)
            decision = self._parse_llm_response(response)

            return await self._execute_decision_ai(decision, context, db)

        except Exception as e:
            logger.error(f"Error in process_with_ai: {e}")
            return AgentResponse(
                text="Desculpe, tive um problema. Como você quer pagar?",
                intent="error",
                should_end=False
            )

    async def _execute_decision(self, decision: dict, context: AgentContext) -> AgentResponse:
        """
        Wrapper para satisfazer BaseAgent abstrato

        Chama _execute_decision_ai() com db do contexto
        """
        from app.database.base import get_db
        db = next(get_db())
        try:
            return await self._execute_decision_ai(decision, context, db)
        finally:
            db.close()
