"""Configuração do Celery para tarefas assíncronas."""

from celery import Celery
from app.core.config import settings

# Criar instância do Celery
celery_app = Celery(
    "pdpj_tasks",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.tasks.process_tasks", "app.tasks.document_tasks", "app.tasks.download_tasks"]
)

# Configurações do Celery otimizadas para alta performance
celery_app.conf.update(
    # Serialização
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    
    # Configurações de timezone
    timezone="America/Sao_Paulo",
    enable_utc=True,
    
    # Configurações de task
    task_track_started=True,
    task_time_limit=60 * 60,  # 60 minutos para tasks pesadas
    task_soft_time_limit=55 * 60,  # 55 minutos
    task_acks_late=True,  # Confirmar task apenas após conclusão
    task_reject_on_worker_lost=True,  # Rejeitar tasks se worker for perdido
    
    # Configurações de worker
    worker_prefetch_multiplier=1,  # Processar uma task por vez para evitar memory leaks
    worker_max_tasks_per_child=500,  # Reiniciar worker após 500 tasks
    worker_max_memory_per_child=200000,  # 200MB por worker
    
    # Configurações de resultado
    result_expires=3600,  # 1 hora
    
    # Configurações de performance
    worker_direct=True,  # Conexão direta com broker
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
    broker_connection_max_retries=10,
    
    # Configurações de concorrência
    worker_concurrency=4,  # 4 threads por worker
    
    # Configurações de routing
    task_routes={
        'app.tasks.process_tasks.*': {'queue': 'processes'},
        'app.tasks.document_tasks.*': {'queue': 'documents'},
        'app.tasks.ultra_fast_tasks.*': {'queue': 'ultra_fast'},
    },
    
    # Configurações de fila
    task_default_queue='default',
    task_queues={
        'default': {
            'exchange': 'default',
            'routing_key': 'default',
        },
        'processes': {
            'exchange': 'processes',
            'routing_key': 'processes',
        },
        'documents': {
            'exchange': 'documents',
            'routing_key': 'documents',
        },
        'ultra_fast': {
            'exchange': 'ultra_fast',
            'routing_key': 'ultra_fast',
        },
    },
)
