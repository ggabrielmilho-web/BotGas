"""
Attendance Agent - Handles greetings, product inquiries, and general questions
"""
from typing import Dict, Any, List
from uuid import UUID
import json
import logging

from app.agents.base import BaseAgent, AgentContext, AgentResponse
from app.database.models import Product, Tenant
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class AttendanceAgent(BaseAgent):
    """
    Handles initial contact and general inquiries

    Responsibilities:
    - Greetings and welcome messages
    - List available products
    - Provide company information
    - Answer general questions
    - Guide customer to next steps
    """

    def __init__(self):
        super().__init__(model_name="gpt-4-turbo-preview", temperature=0.8)
        self.cache_ttl = 300  # 5 minutes

    async def process(self, message: str, context: AgentContext) -> AgentResponse:
        """Process attendance-related messages"""

        from app.database.base import get_db

        db = next(get_db())

        try:
            # Get tenant info
            tenant = db.query(Tenant).filter(Tenant.id == context.tenant_id).first()

            if not tenant:
                return AgentResponse(
                    text="Desculpe, ocorreu um erro. Por favor, tente novamente.",
                    intent="error",
                    should_end=True
                )

            # Detect specific intent
            intent = self._detect_intent(message)

            # Handle based on intent
            if intent == "greeting":
                response_text = await self._handle_greeting(tenant, context)

            elif intent == "product_inquiry":
                response_text = await self._handle_product_inquiry(tenant, db, context)

            elif intent == "help":
                response_text = await self._handle_help(tenant)

            else:
                # Use LLM for general conversation
                response_text = await self._handle_general(message, tenant, context)

            # Update context
            if intent == "product_inquiry":
                # Customer is interested in products, next step is order
                return AgentResponse(
                    text=response_text,
                    intent=intent,
                    next_agent="order",
                    context_updates={"stage": "building_order"},
                    should_end=False
                )

            return AgentResponse(
                text=response_text,
                intent=intent,
                should_end=False
            )

        finally:
            db.close()

    async def _handle_greeting(self, tenant: Tenant, context: AgentContext) -> str:
        """Handle greeting messages"""

        # Check if returning customer
        is_returning = len(context.message_history) > 0

        if is_returning:
            return f"""Olá novamente! 😊

Como posso ajudar hoje?

Você pode:
• Ver nossos produtos e fazer um pedido
• Consultar um pedido anterior
• Falar com um atendente

O que você precisa?"""

        else:
            return f"""Olá! Bem-vindo à {tenant.company_name}! 😊

Sou seu assistente virtual e estou aqui para ajudar.

Você pode:
• Ver nossos produtos e preços
• Fazer um pedido
• Consultar áreas de entrega
• Falar com um atendente

Como posso ajudar você hoje?"""

    async def _handle_product_inquiry(self, tenant: Tenant, db: Session, context: AgentContext) -> str:
        """Handle product listing and pricing"""

        # Get products (with cache)
        products = await self._get_products(tenant.id, db)

        if not products:
            return """No momento não temos produtos cadastrados.

Gostaria de falar com um atendente?"""

        # Build product list
        product_list = "📋 *Nossos Produtos:*\n\n"

        for idx, product in enumerate(products, 1):
            price_str = f"R$ {product.price:.2f}".replace(".", ",")
            product_list += f"{idx}. *{product.name}*\n"

            if product.description:
                product_list += f"   {product.description}\n"

            product_list += f"   💰 {price_str}\n\n"

        product_list += "Para fazer um pedido, me diga o que você quer! 😊"

        return product_list

    async def _handle_help(self, tenant: Tenant) -> str:
        """Handle help requests"""

        return f"""🤖 Como posso ajudar você:

*Para fazer um pedido:*
Diga o produto que você quer e a quantidade
Exemplo: "Quero 2 botijões de 13kg"

*Para consultar produtos:*
Pergunte "Quais produtos vocês têm?"

*Para falar com atendente:*
Diga "Quero falar com atendente"

*Horário de funcionamento:*
{tenant.settings.get('business_hours', 'Seg-Sex: 8h-18h, Sáb: 8h-12h')}

Posso ajudar em algo mais?"""

    async def _handle_general(self, message: str, tenant: Tenant, context: AgentContext) -> str:
        """Handle general questions using LLM"""

        # Build address info safely
        address_info = ""
        if tenant.address and isinstance(tenant.address, dict):
            street = tenant.address.get('street', '')
            city = tenant.address.get('city', '')
            if street or city:
                address_info = f"- Endereço: {street} - {city}"

        system_prompt = f"""Você é assistente virtual da {tenant.company_name}, uma distribuidora de gás e água.

Informações da empresa:
- Nome: {tenant.company_name}
- Telefone: {tenant.phone}
{address_info}

Seja educado, prestativo e objetivo.
Se não souber algo, sugira falar com atendente humano.
Incentive o cliente a fazer um pedido.
"""

        messages = self._build_messages(message, context, system_prompt)
        response = await self._call_llm(messages)

        return response

    async def _get_products(self, tenant_id: UUID, db: Session) -> List[Product]:
        """Get products with caching"""

        # Try cache first (if Redis is available)
        try:
            from app.core.cache import redis_client

            cache_key = f"products:{tenant_id}"
            cached = await redis_client.get(cache_key)

            if cached:
                logger.info(f"Products loaded from cache for tenant {tenant_id}")
                return json.loads(cached)

        except Exception as e:
            logger.warning(f"Cache not available: {e}")

        # Get from database
        products = db.query(Product).filter(
            Product.tenant_id == tenant_id,
            Product.is_available == True
        ).order_by(Product.name).all()

        # Save to cache
        try:
            from app.core.cache import redis_client

            cache_key = f"products:{tenant_id}"
            await redis_client.setex(
                cache_key,
                self.cache_ttl,
                json.dumps([{
                    "id": str(p.id),
                    "name": p.name,
                    "description": p.description,
                    "price": float(p.price),
                    "category": p.category
                } for p in products])
            )

        except Exception as e:
            logger.warning(f"Failed to cache products: {e}")

        return products

    def _build_system_prompt(self, context: AgentContext) -> str:
        """Build system prompt for attendance agent"""

        return """Você é um assistente de atendimento amigável e prestativo.

Suas funções:
- Cumprimentar clientes
- Apresentar produtos
- Responder dúvidas gerais
- Guiar o cliente para fazer pedido

Seja natural, use emojis moderadamente, e seja sempre educado."""

    # ================================================================
    # NOVOS MÉTODOS COM IA REAL (LLM responde diretamente)
    # ================================================================

    def _build_system_prompt_ai(self, context: AgentContext, db) -> str:
        """
        System prompt para AttendanceAgent responder com IA

        NOVO: LLM responde TUDO (não usa templates hardcoded)
        """
        from app.database.models import Tenant, Product

        try:
            tenant = db.query(Tenant).filter(Tenant.id == context.tenant_id).first()
            products = db.query(Product).filter(
                Product.tenant_id == context.tenant_id,
                Product.is_available == True
            ).order_by(Product.name).all()

            # Formatar produtos
            products_text = ""
            for i, p in enumerate(products, 1):
                products_text += f"{i}. {p.name} - R$ {p.price:.2f}"
                if p.description:
                    products_text += f" ({p.description})"
                products_text += "\n"

            # Informações da empresa
            company_name = tenant.company_name if tenant else "Distribuidora"
            phone = tenant.phone if tenant else ""

            address_info = ""
            if tenant and tenant.address and isinstance(tenant.address, dict):
                street = tenant.address.get('street', '')
                city = tenant.address.get('city', '')
                if street or city:
                    address_info = f"\n- Endereço: {street} - {city}"

        except Exception as e:
            logger.error(f"Error building system prompt: {e}")
            company_name = "Distribuidora"
            phone = ""
            address_info = ""
            products_text = "(erro ao carregar produtos)"

        ctx = self._format_full_context(context)

        # Detectar se é primeira interação
        is_first_message = len(context.message_history) == 0

        return f"""Você é o assistente virtual da {company_name}, uma distribuidora de gás e água via WhatsApp.

{ctx}

INFORMAÇÕES DA EMPRESA:
- Nome: {company_name}
- Telefone: {phone}{address_info}

PRODUTOS DISPONÍVEIS:
{products_text}

RESPONSABILIDADES:
1. Cumprimentar clientes (especialmente se for primeira mensagem)
2. Apresentar produtos quando solicitado
3. Responder dúvidas gerais sobre a empresa
4. Guiar cliente para fazer pedido
5. Ser amigável e prestativo

REGRAS DE RESPOSTA:
1. Se cliente SAÚDA (oi/olá/bom dia):
   → Cumprimente de volta
   → Apresente-se brevemente
   → {"Pergunte como pode ajudar" if is_first_message else "Pergunte o que precisa"}

2. Se cliente pergunta sobre PRODUTOS:
   → Liste os produtos com preços
   → Incentive a fazer pedido
   → Exemplo: "Para fazer um pedido, me diga o que você quer!"

3. Se cliente pede AJUDA ou tem DÚVIDA:
   → Responda educadamente
   → Se não souber, sugira falar com atendente

4. Se cliente menciona PEDIDO/PRODUTO específico:
   → Confirme interesse
   → Sugira próximo passo (fazer pedido)

IMPORTANTE:
- Seja natural e amigável
- Use emojis moderadamente (1-2 por mensagem)
- Respostas curtas e objetivas
- NUNCA invente informações (preços, horários, etc)
- Se não souber algo, seja honesto

RESPONDA DIRETAMENTE (não precisa JSON, apenas texto natural)"""

    async def process_with_ai(self, message: str, context: AgentContext, db) -> AgentResponse:
        """
        NOVO: Process with AI-powered responses (LLM responde tudo)

        Fluxo:
        1. LLM recebe contexto completo + produtos
        2. LLM responde diretamente (natural)
        3. Sistema detecta próximo passo baseado na resposta
        """
        from langchain.schema import SystemMessage, HumanMessage

        try:
            system_prompt = self._build_system_prompt_ai(context, db)
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"Cliente: {message}")
            ]

            logger.info("🔄 AttendanceAgent calling LLM...")
            response = await self._call_llm(messages)

            # Detectar próximo passo baseado no contexto
            message_lower = message.lower()
            next_agent = None
            stage = None

            # Se cliente está interessado em produtos/pedido
            product_keywords = ["quero", "pedido", "produto", "botijão", "p13", "preço", "quanto"]
            if any(word in message_lower for word in product_keywords):
                next_agent = "order"
                stage = "building_order"

            return AgentResponse(
                text=response,
                intent="attendance",
                next_agent=next_agent,
                context_updates={"stage": stage} if stage else {},
                should_end=False
            )

        except Exception as e:
            logger.error(f"Error in process_with_ai: {e}")
            return AgentResponse(
                text="Desculpe, tive um problema. Como posso ajudar?",
                intent="error",
                should_end=False
            )
