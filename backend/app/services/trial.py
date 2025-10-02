"""
Trial Service - Gerenciamento de trial gratuito de 7 dias
"""
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.database.models import Tenant


class TrialService:
    """
    Gerencia o sistema de trial gratuito
    - 7 dias de trial ao criar conta
    - Verificação de expiração
    - Bloqueio de funcionalidades após expiração
    """

    TRIAL_DAYS = 7

    @staticmethod
    def start_trial(tenant_id: str, db: Session) -> datetime:
        """
        Inicia o trial de 7 dias para um tenant
        Chamado automaticamente ao criar conta
        """
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()

        if not tenant:
            raise ValueError("Tenant não encontrado")

        # Definir data de expiração do trial
        trial_ends_at = datetime.now() + timedelta(days=TrialService.TRIAL_DAYS)

        tenant.trial_ends_at = trial_ends_at
        tenant.subscription_status = 'trial'

        db.commit()
        db.refresh(tenant)

        return trial_ends_at

    @staticmethod
    def check_trial_status(tenant_id: str, db: Session) -> dict:
        """
        Verifica o status do trial de um tenant

        Returns:
            {
                "status": "active" | "expired" | "subscribed",
                "days_remaining": int,
                "trial_ends_at": datetime,
                "is_blocked": bool
            }
        """
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()

        if not tenant:
            raise ValueError("Tenant não encontrado")

        # Se já tem assinatura ativa
        if tenant.subscription_status == 'active':
            return {
                "status": "subscribed",
                "days_remaining": None,
                "trial_ends_at": None,
                "is_blocked": False,
                "message": "Assinatura ativa"
            }

        # Se está em trial
        if tenant.subscription_status == 'trial':
            now = datetime.now()

            if not tenant.trial_ends_at:
                # Trial não foi iniciado, iniciar agora
                trial_ends_at = TrialService.start_trial(tenant_id, db)
                return {
                    "status": "active",
                    "days_remaining": TrialService.TRIAL_DAYS,
                    "trial_ends_at": trial_ends_at,
                    "is_blocked": False,
                    "message": "Trial iniciado"
                }

            # Verificar se trial expirou
            if now > tenant.trial_ends_at:
                # Trial expirado
                tenant.subscription_status = 'expired'
                db.commit()

                return {
                    "status": "expired",
                    "days_remaining": 0,
                    "trial_ends_at": tenant.trial_ends_at,
                    "is_blocked": True,
                    "message": "Trial expirado. Por favor, assine um plano."
                }

            # Trial ainda ativo
            days_remaining = (tenant.trial_ends_at - now).days + 1

            return {
                "status": "active",
                "days_remaining": days_remaining,
                "trial_ends_at": tenant.trial_ends_at,
                "is_blocked": False,
                "message": f"Trial ativo. {days_remaining} dias restantes."
            }

        # Status expirado ou cancelado
        return {
            "status": tenant.subscription_status,
            "days_remaining": 0,
            "trial_ends_at": tenant.trial_ends_at,
            "is_blocked": True,
            "message": "Acesso bloqueado. Por favor, assine um plano."
        }

    @staticmethod
    def extend_trial(tenant_id: str, days: int, db: Session) -> datetime:
        """
        Estende o trial por X dias adicionais
        Útil para casos especiais ou promoções
        """
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()

        if not tenant:
            raise ValueError("Tenant não encontrado")

        if not tenant.trial_ends_at:
            raise ValueError("Trial não iniciado")

        # Estender trial
        new_trial_end = tenant.trial_ends_at + timedelta(days=days)
        tenant.trial_ends_at = new_trial_end
        tenant.subscription_status = 'trial'

        db.commit()
        db.refresh(tenant)

        return new_trial_end

    @staticmethod
    def activate_subscription(
        tenant_id: str,
        plan: str,
        db: Session
    ) -> dict:
        """
        Ativa assinatura paga para um tenant
        Remove limitações do trial

        Args:
            tenant_id: ID do tenant
            plan: Nome do plano (basic, premium, etc)
            db: Sessão do banco
        """
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()

        if not tenant:
            raise ValueError("Tenant não encontrado")

        # Ativar assinatura
        tenant.subscription_status = 'active'
        tenant.subscription_plan = plan

        db.commit()
        db.refresh(tenant)

        return {
            "status": "success",
            "message": f"Assinatura {plan} ativada com sucesso!",
            "plan": plan,
            "subscription_status": "active"
        }

    @staticmethod
    def cancel_subscription(tenant_id: str, db: Session) -> dict:
        """
        Cancela a assinatura de um tenant
        """
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()

        if not tenant:
            raise ValueError("Tenant não encontrado")

        tenant.subscription_status = 'cancelled'
        tenant.subscription_plan = None

        db.commit()
        db.refresh(tenant)

        return {
            "status": "success",
            "message": "Assinatura cancelada"
        }

    @staticmethod
    def get_expired_trials(db: Session) -> list:
        """
        Retorna lista de tenants com trial expirado
        Usado pela task Celery para notificações
        """
        now = datetime.now()

        expired_tenants = db.query(Tenant).filter(
            and_(
                Tenant.subscription_status == 'trial',
                Tenant.trial_ends_at < now
            )
        ).all()

        return expired_tenants

    @staticmethod
    def get_expiring_soon_trials(days: int, db: Session) -> list:
        """
        Retorna tenants cujo trial expira em X dias
        Para enviar notificações de aviso
        """
        now = datetime.now()
        future = now + timedelta(days=days)

        expiring_tenants = db.query(Tenant).filter(
            and_(
                Tenant.subscription_status == 'trial',
                Tenant.trial_ends_at > now,
                Tenant.trial_ends_at <= future
            )
        ).all()

        return expiring_tenants

    @staticmethod
    def mark_trial_as_expired(tenant_id: str, db: Session) -> None:
        """
        Marca um trial como expirado
        Chamado pela task Celery
        """
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()

        if tenant:
            tenant.subscription_status = 'expired'
            db.commit()
