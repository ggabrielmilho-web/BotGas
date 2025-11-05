"""
Dashboard API endpoints
Fornece dados em tempo real para o dashboard administrativo
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc, cast, Text
from typing import List, Optional
from datetime import datetime, timedelta
from uuid import UUID
from pydantic import BaseModel

from app.database.base import get_db
from app.database.models import (
    Order, Customer, Conversation, Product,
    HumanIntervention, Tenant
)
from app.database.schemas import (
    OrderResponse, ConversationResponse,
    DashboardSummary, CustomerResponse
)
from app.middleware.tenant import get_current_tenant, get_current_user

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary)
async def get_dashboard_summary(
    db: Session = Depends(get_db),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """
    Retorna resumo do dashboard com métricas principais
    """
    # Pedidos hoje
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    orders_today = db.query(func.count(Order.id)).filter(
        and_(
            Order.tenant_id == current_tenant.id,
            Order.created_at >= today_start
        )
    ).scalar()

    # Receita hoje
    revenue_today = db.query(func.sum(Order.total)).filter(
        and_(
            Order.tenant_id == current_tenant.id,
            Order.created_at >= today_start,
            Order.status.in_(['completed', 'delivered'])
        )
    ).scalar() or 0

    # Pedidos pendentes
    pending_orders = db.query(func.count(Order.id)).filter(
        and_(
            Order.tenant_id == current_tenant.id,
            Order.status == 'new'
        )
    ).scalar()

    # Conversas ativas
    active_conversations = db.query(func.count(Conversation.id)).filter(
        and_(
            Conversation.tenant_id == current_tenant.id,
            Conversation.status == 'active'
        )
    ).scalar()

    # Intervenções ativas
    active_interventions = db.query(func.count(HumanIntervention.id)).filter(
        and_(
            HumanIntervention.tenant_id == current_tenant.id,
            HumanIntervention.ended_at.is_(None)
        )
    ).scalar()

    # Total de clientes
    total_customers = db.query(func.count(Customer.id)).filter(
        Customer.tenant_id == current_tenant.id
    ).scalar()

    return DashboardSummary(
        orders_today=orders_today,
        revenue_today=float(revenue_today),
        pending_orders=pending_orders,
        active_conversations=active_conversations,
        active_interventions=active_interventions,
        total_customers=total_customers
    )


@router.get("/orders", response_model=List[OrderResponse])
async def get_recent_orders(
    status: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None, description="Data inicial (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Data final (YYYY-MM-DD)"),
    limit: int = Query(50, le=100),
    offset: int = Query(0),
    db: Session = Depends(get_db),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """
    Lista pedidos recentes com filtros de status e data
    """
    query = db.query(Order).filter(Order.tenant_id == current_tenant.id)

    if status:
        query = query.filter(Order.status == status)

    # Filtro de data inicial
    if date_from:
        try:
            date_from_dt = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(Order.created_at >= date_from_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Formato de data_from inválido. Use YYYY-MM-DD")

    # Filtro de data final (inclui o dia inteiro)
    if date_to:
        try:
            date_to_dt = datetime.strptime(date_to, '%Y-%m-%d').replace(
                hour=23, minute=59, second=59, microsecond=999999
            )
            query = query.filter(Order.created_at <= date_to_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Formato de date_to inválido. Use YYYY-MM-DD")

    orders = query.order_by(desc(Order.created_at)).offset(offset).limit(limit).all()

    return orders


@router.put("/orders/{order_id}/status")
async def update_order_status(
    order_id: UUID,
    status: str,
    db: Session = Depends(get_db),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """
    Atualiza status de um pedido
    """
    order = db.query(Order).filter(
        and_(
            Order.id == order_id,
            Order.tenant_id == current_tenant.id
        )
    ).first()

    if not order:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")

    order.status = status

    if status == 'delivered':
        order.delivered_at = datetime.now()

        # End conversation when order is delivered
        # Find the active conversation associated with this order
        # Using JSONB contains operator (@>) to search for order_id
        from sqlalchemy import cast, Text
        conversation = db.query(Conversation).filter(
            and_(
                Conversation.tenant_id == current_tenant.id,
                Conversation.status == 'active',
                cast(Conversation.context, Text).like(f'%"order_id": "{str(order.id)}"%')
            )
        ).first()

        if conversation:
            conversation.status = 'ended'
            conversation.ended_at = datetime.now()

    db.commit()
    db.refresh(order)

    return {"message": "Status atualizado", "order": order}


@router.get("/conversations", response_model=List[ConversationResponse])
async def get_conversations(
    status: Optional[str] = Query(None),
    intervention_only: bool = Query(False),
    date_from: Optional[str] = Query(None, description="Data inicial (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Data final (YYYY-MM-DD)"),
    limit: int = Query(50, le=100),
    db: Session = Depends(get_db),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """
    Lista conversas com filtros de status, intervenção e data
    """
    query = db.query(Conversation).filter(
        Conversation.tenant_id == current_tenant.id
    )

    if status:
        query = query.filter(Conversation.status == status)

    if intervention_only:
        query = query.filter(Conversation.human_intervention == True)

    # Filtro de data inicial
    if date_from:
        try:
            date_from_dt = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(Conversation.started_at >= date_from_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Formato de data_from inválido. Use YYYY-MM-DD")

    # Filtro de data final (inclui o dia inteiro)
    if date_to:
        try:
            date_to_dt = datetime.strptime(date_to, '%Y-%m-%d').replace(
                hour=23, minute=59, second=59, microsecond=999999
            )
            query = query.filter(Conversation.started_at <= date_to_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Formato de date_to inválido. Use YYYY-MM-DD")

    conversations = query.order_by(desc(Conversation.started_at)).limit(limit).all()

    return conversations


@router.get("/conversations/{conversation_id}/messages")
async def get_conversation_messages(
    conversation_id: UUID,
    db: Session = Depends(get_db),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """
    Retorna todas as mensagens de uma conversa
    Inclui transcrições de áudio
    """
    conversation = db.query(Conversation).filter(
        and_(
            Conversation.id == conversation_id,
            Conversation.tenant_id == current_tenant.id
        )
    ).first()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversa não encontrada")

    return {
        "conversation_id": conversation.id,
        "customer_id": conversation.customer_id,
        "messages": conversation.messages,
        "context": conversation.context,
        "human_intervention": conversation.human_intervention,
        "started_at": conversation.started_at
    }


@router.get("/interventions")
async def get_active_interventions(
    date_from: Optional[str] = Query(None, description="Data inicial (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Data final (YYYY-MM-DD)"),
    active_only: bool = Query(True, description="Mostrar apenas intervenções ativas"),
    db: Session = Depends(get_db),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """
    Lista intervenções humanas com filtros de data
    """
    query = db.query(HumanIntervention).filter(
        HumanIntervention.tenant_id == current_tenant.id
    )

    # Filtro de intervenções ativas (padrão)
    if active_only:
        query = query.filter(HumanIntervention.ended_at.is_(None))

    # Filtro de data inicial
    if date_from:
        try:
            date_from_dt = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(HumanIntervention.started_at >= date_from_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Formato de data_from inválido. Use YYYY-MM-DD")

    # Filtro de data final (inclui o dia inteiro)
    if date_to:
        try:
            date_to_dt = datetime.strptime(date_to, '%Y-%m-%d').replace(
                hour=23, minute=59, second=59, microsecond=999999
            )
            query = query.filter(HumanIntervention.started_at <= date_to_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Formato de date_to inválido. Use YYYY-MM-DD")

    interventions = query.all()

    result = []
    for intervention in interventions:
        conversation = db.query(Conversation).filter(
            Conversation.id == intervention.conversation_id
        ).first()

        customer = db.query(Customer).filter(
            Customer.id == conversation.customer_id
        ).first() if conversation else None

        result.append({
            "intervention_id": intervention.id,
            "conversation_id": intervention.conversation_id,
            "customer_name": customer.name if customer else "Desconhecido",
            "customer_phone": customer.whatsapp_number if customer else None,
            "started_at": intervention.started_at,
            "reason": intervention.reason,
            "messages_count": len(intervention.messages_during_intervention)
        })

    return result


@router.get("/customers", response_model=List[CustomerResponse])
async def get_customers(
    search: Optional[str] = Query(None),
    limit: int = Query(50, le=100),
    db: Session = Depends(get_db),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """
    Lista clientes com busca opcional
    """
    query = db.query(Customer).filter(Customer.tenant_id == current_tenant.id)

    if search:
        query = query.filter(
            (Customer.name.ilike(f"%{search}%")) |
            (Customer.whatsapp_number.ilike(f"%{search}%"))
        )

    customers = query.order_by(desc(Customer.last_order_at)).limit(limit).all()

    return customers


@router.get("/realtime-stats")
async def get_realtime_stats(
    db: Session = Depends(get_db),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """
    Estatísticas em tempo real para atualização via WebSocket
    """
    # Últimos 5 minutos
    recent_time = datetime.now() - timedelta(minutes=5)

    recent_orders = db.query(Order).filter(
        and_(
            Order.tenant_id == current_tenant.id,
            Order.created_at >= recent_time
        )
    ).all()

    recent_conversations = db.query(Conversation).filter(
        and_(
            Conversation.tenant_id == current_tenant.id,
            Conversation.started_at >= recent_time
        )
    ).count()

    return {
        "recent_orders_count": len(recent_orders),
        "recent_orders": [
            {
                "id": str(order.id),
                "order_number": order.order_number,
                "total": float(order.total),
                "status": order.status,
                "created_at": order.created_at.isoformat()
            }
            for order in recent_orders
        ],
        "recent_conversations": recent_conversations,
        "timestamp": datetime.now().isoformat()
    }


# ============================================================================
# DELIVERY DRIVER ENDPOINTS
# ============================================================================

class SendToDriverRequest(BaseModel):
    driver_id: UUID

@router.post("/orders/{order_id}/send-to-driver")
async def send_order_to_driver(
    order_id: UUID,
    request: SendToDriverRequest,
    db: Session = Depends(get_db),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """Envia ticket do pedido ao motoboy via WhatsApp"""

    # Buscar pedido
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.tenant_id == current_tenant.id,
        Order.status == 'new'
    ).first()

    if not order:
        raise HTTPException(404, "Pedido não encontrado ou já processado")

    # Buscar motoboy
    from app.database.models import DeliveryDriver

    driver = db.query(DeliveryDriver).filter(
        DeliveryDriver.id == request.driver_id,
        DeliveryDriver.tenant_id == current_tenant.id,
        DeliveryDriver.is_active == True
    ).first()

    if not driver:
        raise HTTPException(404, "Motoboy não encontrado ou inativo")

    # Buscar cliente
    customer = db.query(Customer).filter(
        Customer.id == order.customer_id
    ).first()

    # Formatar itens do pedido
    items_text = "\n".join([
        f"- {item.get('quantity')}x {item.get('product_name')} (R$ {float(item.get('subtotal', 0)):.2f})"
        for item in order.items
    ])

    # Formatar endereço
    address = order.delivery_address or {}
    address_text = address.get('normalized_address') or address.get('address', 'Endereço não informado')
    neighborhood = address.get('neighborhood', '')

    # Montar ticket
    ticket = f"""🚚 *Nova Entrega - Pedido #{order.order_number}*

📦 *Itens:*
{items_text}

💰 *Valor Total:* R$ {float(order.total):.2f}
💳 *Pagamento:* {order.payment_method}

📍 *Endereço:*
{address_text}
{f'Bairro: {neighborhood}' if neighborhood else ''}

👤 *Cliente:* {customer.name if customer else 'N/A'}
📞 *Contato:* {customer.whatsapp_number if customer else 'N/A'}

---
Boa entrega! 🏍️"""

    # Enviar via Evolution API
    from app.services.evolution import evolution_service
    import re

    try:
        instance_name = f"tenant_{str(current_tenant.id)}"

        # Normalizar telefone: adicionar +55 se não tiver
        phone = re.sub(r'[^0-9]', '', driver.phone)  # Remove caracteres especiais
        if not phone.startswith('55'):
            phone = '55' + phone

        await evolution_service.send_text_message(
            instance_name=instance_name,
            number=phone,
            message=ticket
        )

        # Atualizar pedido
        order.driver_name = driver.name
        order.status = 'confirmed'

        db.commit()

        return {
            "success": True,
            "message": f"Ticket enviado para {driver.name}",
            "driver_name": driver.name,
            "order_status": "confirmed"
        }

    except Exception as e:
        raise HTTPException(500, f"Erro ao enviar ticket: {str(e)}")
