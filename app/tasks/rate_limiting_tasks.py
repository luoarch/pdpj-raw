"""Tasks periódicas para limpeza e manutenção do rate limiting."""

import time
from typing import Optional
from celery import Celery
from loguru import logger

from app.core.config import settings


def create_rate_limiting_celery_app() -> Optional[Celery]:
    """Criar app Celery para tasks de rate limiting se configurado."""
    if not settings.enable_celery:
        return None
    
    celery_app = Celery(
        'rate_limiting_tasks',
        broker=settings.celery_broker_url,
        backend=settings.celery_result_backend
    )
    
    # Configurações do Celery
    celery_app.conf.update(
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='UTC',
        enable_utc=True,
        task_track_started=True,
        task_time_limit=300,  # 5 minutos
        task_soft_time_limit=240,  # 4 minutos
    )
    
    return celery_app


# Criar instância do Celery
celery_app = create_rate_limiting_celery_app()


@celery_app.task(bind=True, name='cleanup_redis_rate_limiting')
def cleanup_redis_rate_limiting_task(self, redis_url: str, key_prefix: str = "rate_limit"):
    """Task periódica para limpeza de dados antigos no Redis.
    
    Args:
        redis_url: URL de conexão Redis
        key_prefix: Prefixo das chaves para limpeza
    
    Returns:
        Dict com estatísticas da limpeza
    """
    try:
        import redis
        
        # Conectar ao Redis
        redis_client = redis.Redis.from_url(redis_url, decode_responses=False)
        
        # Calcular cutoff time (2 horas atrás)
        current_time = time.time()
        cutoff_time = current_time - (2 * 3600)  # 2 horas
        
        # Obter todas as chaves do rate limiting
        pattern = f"{key_prefix}:*"
        keys = redis_client.keys(pattern)
        
        total_removed = 0
        keys_processed = 0
        
        for key in keys:
            try:
                # Remover entradas antigas de cada chave
                removed = redis_client.zremrangebyscore(key, 0, cutoff_time)
                total_removed += removed
                keys_processed += 1
                
                # Se a chave ficou vazia, removê-la
                if redis_client.zcard(key) == 0:
                    redis_client.delete(key)
                
            except Exception as e:
                logger.error(f"Erro ao limpar chave {key}: {str(e)}")
                continue
        
        # Estatísticas
        stats = {
            "keys_processed": keys_processed,
            "entries_removed": total_removed,
            "cutoff_time": cutoff_time,
            "execution_time": time.time() - current_time
        }
        
        logger.info(f"Limpeza Redis concluída: {stats}")
        return stats
        
    except Exception as e:
        logger.error(f"Erro na task de limpeza Redis: {str(e)}")
        raise self.retry(exc=e, countdown=60, max_retries=3)


@celery_app.task(bind=True, name='get_rate_limiting_stats')
def get_rate_limiting_stats_task(self, redis_url: str, key_prefix: str = "rate_limit"):
    """Task para obter estatísticas do rate limiting Redis.
    
    Args:
        redis_url: URL de conexão Redis
        key_prefix: Prefixo das chaves
    
    Returns:
        Dict com estatísticas
    """
    try:
        import redis
        
        # Conectar ao Redis
        redis_client = redis.Redis.from_url(redis_url, decode_responses=False)
        
        # Obter todas as chaves
        pattern = f"{key_prefix}:*"
        keys = redis_client.keys(pattern)
        
        total_clients = len(keys)
        total_requests = 0
        active_clients = 0
        
        current_time = time.time()
        window_start = current_time - 3600  # Última hora
        
        for key in keys:
            try:
                # Contar total de requisições
                total_requests += redis_client.zcard(key)
                
                # Verificar se tem requisições na última hora
                recent_requests = redis_client.zcount(key, window_start, "+inf")
                if recent_requests > 0:
                    active_clients += 1
                    
            except Exception as e:
                logger.error(f"Erro ao processar chave {key}: {str(e)}")
                continue
        
        stats = {
            "total_clients": total_clients,
            "active_clients": active_clients,
            "total_requests": total_requests,
            "timestamp": current_time
        }
        
        logger.info(f"Estatísticas Redis: {stats}")
        return stats
        
    except Exception as e:
        logger.error(f"Erro na task de estatísticas Redis: {str(e)}")
        raise self.retry(exc=e, countdown=60, max_retries=3)


@celery_app.task(bind=True, name='health_check_redis')
def health_check_redis_task(self, redis_url: str):
    """Task para verificar saúde da conexão Redis.
    
    Args:
        redis_url: URL de conexão Redis
    
    Returns:
        Dict com status da saúde
    """
    try:
        import redis
        
        # Conectar ao Redis
        redis_client = redis.Redis.from_url(redis_url)
        
        # Teste básico de conectividade
        start_time = time.time()
        redis_client.ping()
        response_time = time.time() - start_time
        
        # Obter informações do Redis
        info = redis_client.info()
        
        health_status = {
            "status": "healthy",
            "response_time_ms": round(response_time * 1000, 2),
            "redis_version": info.get("redis_version"),
            "used_memory_human": info.get("used_memory_human"),
            "connected_clients": info.get("connected_clients"),
            "timestamp": time.time()
        }
        
        logger.info(f"Health check Redis: {health_status}")
        return health_status
        
    except Exception as e:
        error_status = {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": time.time()
        }
        logger.error(f"Health check Redis falhou: {error_status}")
        return error_status


def schedule_periodic_tasks():
    """Agendar tasks periódicas se Celery estiver habilitado."""
    if not celery_app:
        logger.warning("Celery não configurado - tasks periódicas não serão agendadas")
        return
    
    try:
        # Limpeza a cada 30 minutos
        celery_app.conf.beat_schedule.update({
            'cleanup-redis-rate-limiting': {
                'task': 'cleanup_redis_rate_limiting',
                'schedule': 30 * 60,  # 30 minutos
                'args': (settings.redis_url, "rate_limit")
            },
        })
        
        # Estatísticas a cada 5 minutos
        celery_app.conf.beat_schedule.update({
            'get-rate-limiting-stats': {
                'task': 'get_rate_limiting_stats',
                'schedule': 5 * 60,  # 5 minutos
                'args': (settings.redis_url, "rate_limit")
            },
        })
        
        # Health check a cada 2 minutos
        celery_app.conf.beat_schedule.update({
            'health-check-redis': {
                'task': 'health_check_redis',
                'schedule': 2 * 60,  # 2 minutos
                'args': (settings.redis_url,)
            },
        })
        
        logger.info("Tasks periódicas de rate limiting agendadas com sucesso")
        
    except Exception as e:
        logger.error(f"Erro ao agendar tasks periódicas: {str(e)}")


def start_periodic_tasks():
    """Iniciar tasks periódicas."""
    if celery_app:
        schedule_periodic_tasks()
        logger.info("Tasks periódicas de rate limiting iniciadas")
    else:
        logger.warning("Celery não disponível - usando limpeza manual")


# Função para executar limpeza manual (fallback)
def manual_cleanup_redis(redis_client, key_prefix: str = "rate_limit") -> dict:
    """Executar limpeza manual do Redis (fallback quando Celery não está disponível)."""
    try:
        current_time = time.time()
        cutoff_time = current_time - (2 * 3600)  # 2 horas
        
        pattern = f"{key_prefix}:*"
        keys = redis_client.keys(pattern)
        
        total_removed = 0
        keys_processed = 0
        
        for key in keys:
            try:
                removed = redis_client.zremrangebyscore(key, 0, cutoff_time)
                total_removed += removed
                keys_processed += 1
                
                if redis_client.zcard(key) == 0:
                    redis_client.delete(key)
                    
            except Exception as e:
                logger.error(f"Erro ao limpar chave {key}: {str(e)}")
                continue
        
        stats = {
            "keys_processed": keys_processed,
            "entries_removed": total_removed,
            "cutoff_time": cutoff_time,
            "execution_time": time.time() - current_time,
            "mode": "manual"
        }
        
        logger.info(f"Limpeza manual Redis concluída: {stats}")
        return stats
        
    except Exception as e:
        logger.error(f"Erro na limpeza manual Redis: {str(e)}")
        return {"error": str(e), "mode": "manual"}
