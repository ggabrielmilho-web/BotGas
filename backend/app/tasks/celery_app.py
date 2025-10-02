"""
Celery Application Configuration
"""
from celery import Celery
from app.core.config import settings

# Criar instância do Celery
celery_app = Celery(
    "gasbot",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=['app.tasks.trial']
)

# Configurações do Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='America/Sao_Paulo',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutos
    result_expires=3600,  # 1 hora
)

# Configurar schedule para tasks periódicas
celery_app.conf.beat_schedule = {
    'check-expired-trials': {
        'task': 'app.tasks.trial.check_expired_trials',
        'schedule': 3600.0,  # A cada 1 hora
    },
    'notify-expiring-trials': {
        'task': 'app.tasks.trial.notify_expiring_trials',
        'schedule': 86400.0,  # A cada 24 horas
    },
}
