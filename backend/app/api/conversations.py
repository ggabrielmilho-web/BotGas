"""
Conversations API - Gerenciamento de conversas e intervenção humana
"""
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import Optional
from datetime import datetime
from uuid import UUID
import json

from app.database.base import get_db
from app.database.models import Conversation, HumanIntervention, Customer, Tenant
from app.middleware.tenant import get_current_tenant
from app.services.intervention import InterventionService
from app.services.evolution import EvolutionAPIService

router = APIRouter(prefix="/api/v1/conversations", tags=["conversations"])


@router.post("/{conversation_id}/intervene")
async def start_intervention(
    conversation_id: UUID,
    reason: Optional[str] = None,
    db: Session = Depends(get_db),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """
    Inicia intervenção humana em uma conversa
    Pausa o bot por 5 minutos
    """
    conversation = db.query(Conversation).filter(
        and_(
            Conversation.id == conversation_id,
            Conversation.tenant_id == current_tenant.id
        )
    ).first()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversa não encontrada")

    if conversation.human_intervention:
        raise HTTPException(status_code=400, detail="Intervenção já está ativa")

    # Criar registro de intervenção
    intervention = HumanIntervention(
        tenant_id=current_tenant.id,
        conversation_id=conversation_id,
        started_at=datetime.now(),
        reason=reason or "Intervenção manual"
    )
    db.add(intervention)

    # Atualizar conversa
    conversation.human_intervention = True
    conversation.intervention_started_at = datetime.now()

    db.commit()

    # Enviar mensagem para o cliente
    customer = db.query(Customer).filter(
        Customer.id == conversation.customer_id
    ).first()

    if customer:
        evolution = EvolutionAPIService()
        await evolution.send_message(
            instance_id=current_tenant.whatsapp_instance_id,
            phone=customer.whatsapp_number,
            message="Um momento, vou te conectar com um atendente... ⏳"
        )

    return {
        "message": "Intervenção iniciada",
        "intervention_id": str(intervention.id),
        "expires_in_minutes": 5
    }


@router.post("/{conversation_id}/resume")
async def resume_bot(
    conversation_id: UUID,
    operator_notes: Optional[str] = None,
    db: Session = Depends(get_db),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """
    Retoma o bot após intervenção humana
    """
    conversation = db.query(Conversation).filter(
        and_(
            Conversation.id == conversation_id,
            Conversation.tenant_id == current_tenant.id
        )
    ).first()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversa não encontrada")

    if not conversation.human_intervention:
        raise HTTPException(status_code=400, detail="Não há intervenção ativa")

    # Finalizar intervenção
    intervention = db.query(HumanIntervention).filter(
        and_(
            HumanIntervention.conversation_id == conversation_id,
            HumanIntervention.ended_at.is_(None)
        )
    ).first()

    if intervention:
        intervention.ended_at = datetime.now()
        intervention.operator_notes = operator_notes

    # Atualizar conversa
    conversation.human_intervention = False
    conversation.intervention_ended_at = datetime.now()

    db.commit()

    # Notificar cliente
    customer = db.query(Customer).filter(
        Customer.id == conversation.customer_id
    ).first()

    if customer:
        evolution = EvolutionAPIService()
        await evolution.send_message(
            instance_id=current_tenant.whatsapp_instance_id,
            phone=customer.whatsapp_number,
            message="Obrigado por aguardar! Como posso continuar te ajudando? 🤖"
        )

    return {"message": "Bot retomado com sucesso"}


@router.post("/{conversation_id}/send")
async def send_manual_message(
    conversation_id: UUID,
    message: str,
    db: Session = Depends(get_db),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """
    Envia mensagem manual durante intervenção humana
    """
    conversation = db.query(Conversation).filter(
        and_(
            Conversation.id == conversation_id,
            Conversation.tenant_id == current_tenant.id
        )
    ).first()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversa não encontrada")

    if not conversation.human_intervention:
        raise HTTPException(status_code=400, detail="Intervenção não está ativa")

    # Buscar cliente
    customer = db.query(Customer).filter(
        Customer.id == conversation.customer_id
    ).first()

    if not customer:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")

    # Enviar mensagem
    evolution = EvolutionAPIService()
    await evolution.send_message(
        instance_id=current_tenant.whatsapp_instance_id,
        phone=customer.whatsapp_number,
        message=message
    )

    # Registrar mensagem na intervenção
    intervention = db.query(HumanIntervention).filter(
        and_(
            HumanIntervention.conversation_id == conversation_id,
            HumanIntervention.ended_at.is_(None)
        )
    ).first()

    if intervention:
        messages = intervention.messages_during_intervention or []
        messages.append({
            "from": "operator",
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
        intervention.messages_during_intervention = messages
        db.commit()

    return {"message": "Mensagem enviada com sucesso"}


# WebSocket para atualizações em tempo real
class ConnectionManager:
    """Gerencia conexões WebSocket para dashboard real-time"""

    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, tenant_id: str):
        await websocket.accept()
        if tenant_id not in self.active_connections:
            self.active_connections[tenant_id] = []
        self.active_connections[tenant_id].append(websocket)

    def disconnect(self, websocket: WebSocket, tenant_id: str):
        if tenant_id in self.active_connections:
            self.active_connections[tenant_id].remove(websocket)

    async def broadcast_to_tenant(self, tenant_id: str, message: dict):
        """Envia mensagem para todos os clientes conectados de um tenant"""
        if tenant_id in self.active_connections:
            for connection in self.active_connections[tenant_id]:
                try:
                    await connection.send_json(message)
                except:
                    pass


manager = ConnectionManager()


@router.websocket("/ws/{tenant_id}")
async def websocket_endpoint(websocket: WebSocket, tenant_id: str):
    """
    WebSocket para receber atualizações em tempo real do dashboard
    """
    await manager.connect(websocket, tenant_id)

    try:
        while True:
            # Manter conexão aberta
            data = await websocket.receive_text()

            # Echo back para keep-alive
            if data == "ping":
                await websocket.send_text("pong")

    except WebSocketDisconnect:
        manager.disconnect(websocket, tenant_id)


async def notify_dashboard_update(tenant_id: str, event_type: str, data: dict):
    """
    Função auxiliar para notificar dashboard sobre atualizações
    Chamada de outros serviços quando há novos pedidos, mensagens, etc.
    """
    message = {
        "type": event_type,
        "data": data,
        "timestamp": datetime.now().isoformat()
    }
    await manager.broadcast_to_tenant(str(tenant_id), message)
