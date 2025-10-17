"""
Order Agent - Handles order creation and management
"""
from typing import Dict, Any, List, Optional
from uuid import UUID
from datetime import datetime
from decimal import Decimal
import logging
import re

from app.agents.base import BaseAgent, AgentContext, AgentResponse
from app.database.models import Product, Order, Customer, Tenant
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# Product synonyms mapping for better recognition
PRODUCT_SYNONYMS = {
    "gas": ["gas", "gás", "botijao", "botijão", "p13", "13kg", "13 kg", "botija"],
}


class OrderAgent(BaseAgent):
    """
    Handles order creation and management

    Responsibilities:
    - Build order from customer messages
    - Add/remove items
    - Calculate totals
    - Confirm order details
    - Create order in database
    """

    def __init__(self):
        super().__init__(model_name="gpt-4-turbo-preview", temperature=0.5)

    async def process(self, message: str, context: AgentContext) -> AgentResponse:
        """Process order-related messages"""

        from app.database.base import get_db

        db = next(get_db())

        try:
            # Get current order state
            current_order = context.session_data.get("current_order", {
                "items": [],
                "subtotal": 0.0,
                "delivery_fee": context.session_data.get("delivery_fee", 0.0),
                "total": 0.0
            })

            # Get tenant and products
            tenant = db.query(Tenant).filter(Tenant.id == context.tenant_id).first()
            products = db.query(Product).filter(
                Product.tenant_id == context.tenant_id,
                Product.is_available == True
            ).all()

            # Special case: If stage is "confirming_order" and we have address
            # This means ValidationAgent just validated the address
            # We should now move to payment
            stage = context.session_data.get("stage")
            if stage == "confirming_order" and context.session_data.get("delivery_address"):
                # Check if customer is confirming ("sim", "confirmar", etc)
                message_lower = message.lower()
                confirming_words = ["sim", "confirmar", "ok", "pode", "certo", "isso"]

                if any(word in message_lower for word in confirming_words):
                    # Update order with delivery fee
                    delivery_fee = context.session_data.get("delivery_fee", 0.0)
                    current_order["delivery_fee"] = delivery_fee
                    current_order["total"] = current_order.get("subtotal", 0) + delivery_fee

                    # Build final summary and ask for payment
                    summary = await self._build_order_summary(current_order, final=True)

                    payment_methods = tenant.payment_methods or ["Dinheiro"]
                    payment_options = []

                    for method in payment_methods:
                        if method.lower() == "pix" and tenant.pix_enabled:
                            payment_options.append("• 📱 PIX")
                        elif method.lower() == "dinheiro":
                            payment_options.append("• 💵 Dinheiro")
                        elif method.lower() in ["cartao", "cartão"]:
                            payment_options.append("• 💳 Cartão")

                    payment_text = "\n".join(payment_options)

                    return AgentResponse(
                        text=f"""{summary}

Perfeito! Como você quer pagar?

{payment_text}""",
                        intent="ready_for_payment",
                        next_agent="payment",
                        context_updates={
                            "current_order": current_order,
                            "stage": "payment"
                        },
                        should_end=False
                    )

            # Parse customer intent
            intent = await self._parse_order_intent(message, products, context)

            if intent["action"] == "add_item":
                # Add item to order
                result = await self._add_item_to_order(
                    current_order,
                    intent["product"],
                    intent["quantity"],
                    db
                )

                if result["success"]:
                    current_order = result["order"]

                    # Build response
                    response_text = await self._build_order_summary(
                        current_order,
                        added_item=result.get("added_item")
                    )

                    response_text += "\n\nDeseja adicionar mais alguma coisa?"

                    return AgentResponse(
                        text=response_text,
                        intent="item_added",
                        context_updates={"current_order": current_order},
                        should_end=False
                    )
                else:
                    return AgentResponse(
                        text=result.get("error", "Não consegui adicionar o item. Pode repetir?"),
                        intent="error",
                        should_end=False
                    )

            elif intent["action"] == "remove_item":
                # Remove item
                result = await self._remove_item_from_order(
                    current_order,
                    intent["item_index"]
                )

                response_text = "Item removido!\n\n"
                response_text += await self._build_order_summary(current_order)

                return AgentResponse(
                    text=response_text,
                    intent="item_removed",
                    context_updates={"current_order": current_order},
                    should_end=False
                )

            elif intent["action"] == "confirm_order":
                # Check if order has items
                if not current_order["items"]:
                    return AgentResponse(
                        text="Seu pedido está vazio! O que você gostaria de pedir?",
                        intent="empty_order",
                        should_end=False
                    )

                # Check if has address
                if not context.session_data.get("delivery_address"):
                    return AgentResponse(
                        text="""Para finalizar o pedido, preciso do seu endereço de entrega.

Por favor, me envie:
Rua, número, bairro e cidade""",
                        intent="address_needed",
                        next_agent="validation",
                        context_updates={
                            "current_order": current_order,
                            "stage": "awaiting_address"
                        },
                        should_end=False
                    )

                # Move to payment
                summary = await self._build_order_summary(current_order, final=True)

                return AgentResponse(
                    text=f"""{summary}

Perfeito! Como você quer pagar?

Aceitamos:
• PIX
• Dinheiro
• Cartão (débito/crédito)""",
                    intent="order_confirmed",
                    next_agent="payment",
                    context_updates={
                        "current_order": current_order,
                        "stage": "payment"
                    },
                    should_end=False
                )

            elif intent["action"] == "view_order":
                # Show current order
                if not current_order["items"]:
                    response_text = "Você ainda não adicionou nada ao pedido.\n\nQual produto você gostaria?"
                else:
                    response_text = await self._build_order_summary(current_order)
                    response_text += "\n\nDeseja adicionar mais algo ou finalizar o pedido?"

                return AgentResponse(
                    text=response_text,
                    intent="view_order",
                    should_end=False
                )

            else:
                # General order question - check if customer wants to finish ordering
                message_lower = message.lower()
                finish_words = ["não", "nao", "n", "so", "somente", "pronto", "terminar", "apenas isso"]

                # If order has items AND customer indicated they're done, ask for address
                if current_order.get("items") and any(word in message_lower for word in finish_words):
                    return AgentResponse(
                        text="""Para finalizar o pedido, preciso do seu endereço de entrega.

Por favor, me envie:
Rua, número, bairro""",
                        intent="address_needed",
                        next_agent="validation",
                        context_updates={
                            "current_order": current_order,
                            "stage": "awaiting_address"
                        },
                        should_end=False
                    )

                # Otherwise, use LLM for general question
                response_text = await self._handle_general_order_question(
                    message,
                    current_order,
                    products,
                    context
                )

                return AgentResponse(
                    text=response_text,
                    intent="general",
                    context_updates={"current_order": current_order},
                    should_end=False
                )

        except Exception as e:
            logger.error(f"Error in order agent: {e}")
            return AgentResponse(
                text="Desculpe, tive um problema ao processar seu pedido. Pode tentar novamente?",
                intent="error",
                should_end=False
            )

        finally:
            db.close()

    async def _parse_order_intent(
        self,
        message: str,
        products: List[Product],
        context: AgentContext
    ) -> Dict[str, Any]:
        """Parse customer intent from message"""

        message_lower = message.lower()

        # Check for confirmation
        confirm_words = ["confirmar", "finalizar", "fechar pedido", "é isso", "só isso"]
        if any(word in message_lower for word in confirm_words):
            return {"action": "confirm_order"}

        # Check for removal
        remove_words = ["remover", "tirar", "excluir", "cancelar item"]
        if any(word in message_lower for word in remove_words):
            # Try to extract item index
            numbers = re.findall(r'\d+', message)
            if numbers:
                return {"action": "remove_item", "item_index": int(numbers[0]) - 1}

        # Check for viewing order
        view_words = ["ver pedido", "meu pedido", "o que eu pedi", "resumo"]
        if any(word in message_lower for word in view_words):
            return {"action": "view_order"}

        # Try to extract product and quantity
        product_match = await self._extract_product_and_quantity(message, products)

        if product_match:
            return {
                "action": "add_item",
                "product": product_match["product"],
                "quantity": product_match["quantity"]
            }

        return {"action": "general"}

    async def _extract_product_and_quantity(
        self,
        message: str,
        products: List[Product]
    ) -> Optional[Dict[str, Any]]:
        """Extract product and quantity from message"""

        message_lower = message.lower()

        # First, try to match by index (1, 2, 3, etc)
        # If message is just a number or starts with a number, treat as index
        numbers = re.findall(r'\d+', message)
        if numbers and message.strip().isdigit():
            # Message is just a number - treat as product index
            index = int(numbers[0]) - 1  # Convert to 0-based index
            if 0 <= index < len(products):
                return {
                    "product": products[index],
                    "quantity": 1
                }

        # Try to match product name (exact or partial)
        matched_product = None
        for product in products:
            # Exact name match
            if product.name.lower() in message_lower:
                matched_product = product
                break

            # Partial word match (>3 chars)
            words = product.name.lower().split()
            if any(word in message_lower for word in words if len(word) > 3):
                matched_product = product
                break

        # Try synonyms if no direct match
        if not matched_product:
            for category, synonyms in PRODUCT_SYNONYMS.items():
                if any(syn in message_lower for syn in synonyms):
                    # Found a synonym - try to match with product by category
                    # For now, assume "gas" matches "Botijão" products
                    for product in products:
                        product_lower = product.name.lower()
                        if "botijão" in product_lower or "botijao" in product_lower or "p13" in product_lower:
                            matched_product = product
                            break
                    if matched_product:
                        break

        if not matched_product:
            return None

        # Extract quantity
        quantity = 1  # Default

        # Look for numbers
        numbers = re.findall(r'\d+', message)
        if numbers:
            quantity = int(numbers[0])

        # Look for quantity words
        quantity_words = {
            "um": 1, "uma": 1, "dois": 2, "duas": 2, "três": 3, "tres": 3,
            "quatro": 4, "cinco": 5, "seis": 6, "sete": 7, "oito": 8,
            "nove": 9, "dez": 10
        }

        for word, num in quantity_words.items():
            if word in message_lower:
                quantity = num
                break

        return {
            "product": matched_product,
            "quantity": quantity
        }

    async def _add_item_to_order(
        self,
        order: Dict[str, Any],
        product: Product,
        quantity: int,
        db: Session
    ) -> Dict[str, Any]:
        """Add item to order"""

        try:
            # Check stock if applicable
            if product.stock_quantity is not None:
                if product.stock_quantity < quantity:
                    return {
                        "success": False,
                        "error": f"Desculpe, temos apenas {product.stock_quantity} unidade(s) disponível(is)."
                    }

            # Add item
            item = {
                "product_id": str(product.id),
                "product_name": product.name,
                "quantity": quantity,
                "unit_price": float(product.price),
                "subtotal": float(product.price) * quantity
            }

            order["items"].append(item)

            # Recalculate totals
            order = self._recalculate_order(order)

            return {
                "success": True,
                "order": order,
                "added_item": item
            }

        except Exception as e:
            logger.error(f"Error adding item: {e}")
            return {
                "success": False,
                "error": "Erro ao adicionar item"
            }

    async def _remove_item_from_order(
        self,
        order: Dict[str, Any],
        item_index: int
    ) -> Dict[str, Any]:
        """Remove item from order"""

        if 0 <= item_index < len(order["items"]):
            order["items"].pop(item_index)
            order = self._recalculate_order(order)

        return order

    def _recalculate_order(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """Recalculate order totals"""

        subtotal = sum(item["subtotal"] for item in order["items"])
        delivery_fee = order.get("delivery_fee", 0.0)
        total = subtotal + delivery_fee

        order["subtotal"] = round(subtotal, 2)
        order["total"] = round(total, 2)

        return order

    async def _build_order_summary(
        self,
        order: Dict[str, Any],
        added_item: Optional[Dict[str, Any]] = None,
        final: bool = False
    ) -> str:
        """Build order summary text"""

        if added_item:
            price_str = f"R$ {added_item['subtotal']:.2f}".replace(".", ",")
            summary = f"✅ Adicionado: {added_item['quantity']}x {added_item['product_name']} - {price_str}\n\n"
        else:
            summary = ""

        if not order["items"]:
            return summary + "Seu pedido está vazio."

        summary += "📋 *Resumo do Pedido:*\n\n"

        for idx, item in enumerate(order["items"], 1):
            price_str = f"R$ {item['subtotal']:.2f}".replace(".", ",")
            summary += f"{idx}. {item['quantity']}x {item['product_name']}\n"
            summary += f"   {price_str}\n\n"

        # Totals
        subtotal_str = f"R$ {order['subtotal']:.2f}".replace(".", ",")
        delivery_str = f"R$ {order['delivery_fee']:.2f}".replace(".", ",")
        total_str = f"R$ {order['total']:.2f}".replace(".", ",")

        summary += f"Subtotal: {subtotal_str}\n"
        summary += f"Taxa de entrega: {delivery_str}\n"
        summary += f"*Total: {total_str}*"

        return summary

    async def _handle_general_order_question(
        self,
        message: str,
        current_order: Dict[str, Any],
        products: List[Product],
        context: AgentContext
    ) -> str:
        """Handle general questions using LLM"""

        product_list = "\n".join([f"- {p.name} (R$ {p.price})" for p in products])

        system_prompt = f"""Você é um assistente de pedidos.

Produtos disponíveis:
{product_list}

Pedido atual do cliente:
{len(current_order['items'])} item(s)

Ajude o cliente a adicionar produtos ao pedido.
Seja claro e objetivo."""

        messages = self._build_messages(message, context, system_prompt)
        response = await self._call_llm(messages)

        return response

    async def create_order_in_db(
        self,
        order: Dict[str, Any],
        context: AgentContext,
        payment_method: str,
        db: Session
    ) -> Order:
        """Create order in database"""

        # Get or create customer
        customer = db.query(Customer).filter(
            Customer.tenant_id == context.tenant_id,
            Customer.whatsapp_number == context.customer_phone
        ).first()

        if not customer:
            customer = Customer(
                tenant_id=context.tenant_id,
                whatsapp_number=context.customer_phone,
                name=context.session_data.get("customer_name", "Cliente")
            )
            db.add(customer)
            db.flush()

        # Generate order number (get max order_number for tenant and increment)
        max_order = db.query(Order).filter(
            Order.tenant_id == context.tenant_id
        ).order_by(Order.order_number.desc()).first()

        next_order_number = (max_order.order_number + 1) if max_order and max_order.order_number else 1

        # Create order
        order_obj = Order(
            tenant_id=context.tenant_id,
            customer_id=customer.id,
            order_number=next_order_number,
            status="new",
            items=order["items"],
            subtotal=order["subtotal"],
            delivery_fee=order["delivery_fee"],
            total=order["total"],
            delivery_address=context.session_data.get("delivery_address"),
            payment_method=payment_method,
            created_at=datetime.utcnow()
        )

        db.add(order_obj)
        db.commit()
        db.refresh(order_obj)

        # Update customer stats
        customer.order_count += 1
        customer.total_spent += Decimal(str(order["total"]))
        customer.last_order_at = datetime.utcnow()
        db.commit()

        logger.info(f"Order created: {order_obj.id} - Total: R$ {order['total']:.2f}")

        return order_obj
