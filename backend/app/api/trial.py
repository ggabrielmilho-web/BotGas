"""
Trial API endpoints
Gerenciamento de trial gratuito e assinaturas
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.database.base import get_db
from app.database.models import Tenant
from app.middleware.tenant import get_current_tenant
from app.services.trial import TrialService

router = APIRouter(prefix="/api/v1/trial", tags=["trial"])


class ExtendTrialRequest(BaseModel):
    days: int


class ActivateSubscriptionRequest(BaseModel):
    plan: str  # basic, premium, etc


@router.get("/status")
async def get_trial_status(
    db: Session = Depends(get_db),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """
    Retorna o status do trial do tenant atual
    """
    try:
        status = TrialService.check_trial_status(str(current_tenant.id), db)
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/start")
async def start_trial(
    db: Session = Depends(get_db),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """
    Inicia o trial de 7 dias
    Normalmente chamado automaticamente no registro
    """
    try:
        trial_ends_at = TrialService.start_trial(str(current_tenant.id), db)

        return {
            "status": "success",
            "message": "Trial iniciado com sucesso",
            "trial_ends_at": trial_ends_at,
            "trial_days": TrialService.TRIAL_DAYS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/extend")
async def extend_trial(
    request: ExtendTrialRequest,
    db: Session = Depends(get_db),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """
    Estende o trial por X dias adicionais
    Apenas admin ou suporte pode chamar
    """
    try:
        new_end_date = TrialService.extend_trial(
            str(current_tenant.id),
            request.days,
            db
        )

        return {
            "status": "success",
            "message": f"Trial estendido por {request.days} dias",
            "new_trial_end": new_end_date
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/activate")
async def activate_subscription(
    request: ActivateSubscriptionRequest,
    db: Session = Depends(get_db),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """
    Ativa uma assinatura paga
    Remove limitações do trial
    """
    try:
        result = TrialService.activate_subscription(
            str(current_tenant.id),
            request.plan,
            db
        )

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cancel")
async def cancel_subscription(
    db: Session = Depends(get_db),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """
    Cancela a assinatura atual
    """
    try:
        result = TrialService.cancel_subscription(str(current_tenant.id), db)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/plans")
async def get_available_plans():
    """
    Retorna os planos disponíveis
    """
    return {
        "plans": [
            {
                "id": "basic",
                "name": "Plano Básico",
                "price": 200.00,
                "features": [
                    "WhatsApp ilimitado",
                    "Até 500 pedidos/mês",
                    "1 usuário",
                    "Suporte por email"
                ]
            },
            {
                "id": "premium",
                "name": "Plano Premium",
                "price": 300.00,
                "features": [
                    "Tudo do Básico",
                    "Pedidos ilimitados",
                    "Até 3 usuários",
                    "Suporte prioritário",
                    "Relatórios avançados"
                ],
                "popular": True
            }
        ]
    }
