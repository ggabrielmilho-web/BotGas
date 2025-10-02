"""
Celery Tasks para gerenciamento de Trial
"""
from datetime import datetime
from app.tasks.celery_app import celery_app
from app.database.base import SessionLocal
from app.services.trial import TrialService
from app.services.evolution import EvolutionService
import logging

logger = logging.getLogger(__name__)


@celery_app.task(name='app.tasks.trial.check_expired_trials')
def check_expired_trials():
    """
    Task periódica (a cada 1 hora) para verificar trials expirados
    Marca como expired no banco de dados
    """
    db = SessionLocal()

    try:
        # Buscar trials expirados
        expired_tenants = TrialService.get_expired_trials(db)

        logger.info(f"Verificando trials expirados: {len(expired_tenants)} encontrados")

        for tenant in expired_tenants:
            try:
                # Marcar como expirado
                TrialService.mark_trial_as_expired(str(tenant.id), db)

                logger.info(f"Trial expirado marcado: {tenant.company_name} (ID: {tenant.id})")

                # TODO: Enviar email de notificação
                # send_trial_expired_email(tenant.email, tenant.company_name)

            except Exception as e:
                logger.error(f"Erro ao processar tenant {tenant.id}: {str(e)}")

        return {
            "status": "success",
            "expired_count": len(expired_tenants),
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Erro na task check_expired_trials: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }
    finally:
        db.close()


@celery_app.task(name='app.tasks.trial.notify_expiring_trials')
def notify_expiring_trials():
    """
    Task periódica (a cada 24 horas) para notificar trials que expiram em breve
    Envia notificação 3 dias antes da expiração
    """
    db = SessionLocal()

    try:
        # Buscar trials que expiram em 3 dias
        expiring_tenants = TrialService.get_expiring_soon_trials(days=3, db=db)

        logger.info(f"Verificando trials expirando: {len(expiring_tenants)} encontrados")

        for tenant in expiring_tenants:
            try:
                # Calcular dias restantes
                days_remaining = (tenant.trial_ends_at - datetime.now()).days + 1

                logger.info(
                    f"Trial expirando em {days_remaining} dias: "
                    f"{tenant.company_name} (ID: {tenant.id})"
                )

                # TODO: Enviar email de aviso
                # send_trial_expiring_email(
                #     tenant.email,
                #     tenant.company_name,
                #     days_remaining
                # )

                # TODO: Enviar mensagem no WhatsApp
                # if tenant.whatsapp_connected:
                #     evolution = EvolutionService()
                #     await evolution.send_message(
                #         instance_id=tenant.whatsapp_instance_id,
                #         phone=tenant.phone,
                #         message=f"Seu trial expira em {days_remaining} dias..."
                #     )

            except Exception as e:
                logger.error(f"Erro ao notificar tenant {tenant.id}: {str(e)}")

        return {
            "status": "success",
            "notified_count": len(expiring_tenants),
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Erro na task notify_expiring_trials: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }
    finally:
        db.close()


@celery_app.task(name='app.tasks.trial.extend_trial_task')
def extend_trial_task(tenant_id: str, days: int):
    """
    Task assíncrona para estender trial de um tenant
    """
    db = SessionLocal()

    try:
        new_end_date = TrialService.extend_trial(tenant_id, days, db)

        logger.info(f"Trial estendido: {tenant_id} por {days} dias até {new_end_date}")

        return {
            "status": "success",
            "tenant_id": tenant_id,
            "days_extended": days,
            "new_end_date": new_end_date.isoformat()
        }

    except Exception as e:
        logger.error(f"Erro ao estender trial {tenant_id}: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }
    finally:
        db.close()
