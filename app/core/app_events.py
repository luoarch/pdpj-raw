"""Eventos de startup e shutdown da aplicação."""

import sys
import time
import asyncio
from datetime import datetime
from fastapi import FastAPI
from loguru import logger

from app.core.config import settings


def register_startup_events(app: FastAPI):
    """Registrar eventos de startup da aplicação."""
    
    @app.on_event("startup")
    async def startup_event():
        """Evento de inicialização da aplicação."""
        # Verificar se já foi inicializada
        if getattr(app.state, 'is_initialized', False):
            logger.warning("Aplicação já foi inicializada - pulando startup")
            return
        
        from app.services.process_cache_service import process_cache_service
        
        # Definir start_time global
        app.state.start_time = time.time()
        app.state.is_initialized = True
        
        logger.info("Iniciando aplicação PDPJ API Ultra-Fast Edition")
        logger.info(f"Ambiente: {settings.environment}")
        logger.info(f"Debug: {settings.debug}")
        
        if settings.debug or settings.health_check_include_version:
            logger.info(f"Python: {sys.version}")
        
        logger.info(f"Timestamp: {datetime.utcnow().isoformat()}")
        
        # Conectar ao Redis com tratamento robusto
        cache_connected = False
        try:
            # Cache service não precisa de conexão explícita
            cache_connected = True
            logger.info("Cache Redis conectado")
        except Exception as e:
            logger.error(f"Erro ao conectar ao Redis: {e}")
            
            if settings.cache_critical:
                logger.critical("Cache é crítico - abortando startup")
                raise SystemExit(1)
            else:
                logger.warning("Cache não disponível - funcionalidade degradada")
        
        # Log de configurações importantes
        logger.info(f"Rate Limiting: {'Habilitado' if settings.enable_rate_limiting else 'Desabilitado'}")
        if settings.enable_rate_limiting:
            logger.info(f"Limite: {settings.rate_limit_requests} req/{settings.rate_limit_window}s")
        
        logger.info(f"CORS Origins: {settings.cors_origins if not settings.debug else 'Todas (*)'}")
        logger.info(f"Log Request ID: {'Habilitado' if settings.log_request_id else 'Desabilitado'}")
        
        # Log de middlewares ativos
        logger.info(f"Security Headers: {'Habilitado' if settings.enable_security_headers else 'Desabilitado'}")
        logger.info(f"HTTPS Redirect: {'Habilitado' if settings.enable_https_redirect else 'Desabilitado'}")
        logger.info(f"Métricas Prometheus: {'Habilitado' if settings.enable_metrics else 'Desabilitado'}")
        
        logger.info("Aplicação inicializada com sucesso")


def register_shutdown_events(app: FastAPI):
    """Registrar eventos de shutdown da aplicação."""
    
    @app.on_event("shutdown")
    async def shutdown_event():
        """Evento de encerramento gracioso da aplicação."""
        from app.services.process_cache_service import process_cache_service
        from app.core.database import engine
        
        logger.info("Iniciando encerramento gracioso da aplicação")
        
        try:
            # Cache service não precisa de desconexão explícita
            logger.info("Cache Redis desconectado")
        except Exception as e:
            logger.error(f"Erro ao desconectar do Redis: {e}")
        
        try:
            from app.tasks.celery_app import celery_app
            
            # Método assíncrono robusto para shutdown do Celery
            logger.info("Enviando comando de shutdown para Celery workers...")
            
            # Tentar método assíncrono primeiro (Celery 5.x+)
            try:
                # Usar control.inspect para verificar workers ativos
                inspect = celery_app.control.inspect()
                active_workers = inspect.active()
                
                if active_workers:
                    logger.info(f"Workers ativos encontrados: {list(active_workers.keys())}")
                    
                    # Enviar shutdown para workers ativos
                    shutdown_result = celery_app.control.broadcast('shutdown', reply=True, timeout=10)
                    logger.info(f"Shutdown enviado para workers: {shutdown_result}")
                    
                    # Aguardar confirmação (com timeout)
                    await asyncio.sleep(2)  # Aguardar workers processarem shutdown
                    
                else:
                    logger.info("Nenhum worker ativo encontrado")
                    
            except Exception as celery_error:
                logger.warning(f"Erro no shutdown assíncrono do Celery: {celery_error}")
                
                # Fallback para método síncrono
                try:
                    response = celery_app.control.broadcast('shutdown', timeout=5)
                    logger.info(f"Shutdown síncrono enviado: {response}")
                except Exception as sync_error:
                    logger.error(f"Erro no shutdown síncrono do Celery: {sync_error}")
                    
        except Exception as e:
            logger.warning(f"Erro geral ao enviar shutdown para Celery workers: {e}")
        
        finally:
            try:
                await engine.dispose()
                logger.info("Conexões do banco de dados fechadas")
            except Exception as e:
                logger.error(f"Erro ao fechar conexões do banco: {e}")
        
        logger.info("Aplicação encerrada graciosamente")
