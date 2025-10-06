"""Configuração de routers da API."""

from fastapi import FastAPI
from loguru import logger

from app.core.config import settings


def register_api_routers(app: FastAPI):
    """
    Registrar routers da API com versionamento e compatibilidade legacy.
    
    Esta função registra os routers da API de forma organizada:
    - Routers versionados com prefixo /api/v1
    - Routers legacy com prefixo /legacy para evitar conflitos
    - Tratamento de erros de importação
    - Logging detalhado para debugging
    """
    try:
        # Importação local para evitar dependências circulares
        from app.api import processes, users, monitoring, webhooks
        
        logger.info("Iniciando registro de routers da API")
        
        # Routers versionados (produção)
        _register_versioned_routers(app)
        
        # Routers legacy (compatibilidade)
        _register_legacy_routers(app)
        
        logger.info("Routers da API registrados com sucesso")
        
    except ImportError as e:
        logger.error(f"Erro ao importar routers: {e}")
        raise RuntimeError(f"Falha na importação de routers: {e}")
    except Exception as e:
        logger.error(f"Erro inesperado ao registrar routers: {e}")
        raise


def _register_versioned_routers(app: FastAPI):
    """Registrar routers versionados com prefixo /api/v1."""
    from app.api import processes, users, monitoring, webhooks
    
    # Configuração de routers versionados
    routers_config = [
        (processes.router, "processes", "Processos judiciais"),
        (users.router, "users", "Gerenciamento de usuários"),
        (monitoring.router, "monitoring", "Monitoramento e métricas"),
        (webhooks.router, "webhooks", "Webhooks e callbacks"),
    ]
    
    for router, tag, description in routers_config:
        try:
            app.include_router(
                router,
                prefix=f"{settings.api_prefix}/{tag}",
                tags=[tag],
                responses={
                    404: {"description": "Recurso não encontrado"},
                    500: {"description": "Erro interno do servidor"},
                }
            )
            logger.debug(f"Router '{tag}' registrado com prefixo {settings.api_prefix}/{tag}")
        except Exception as e:
            logger.error(f"Erro ao registrar router '{tag}': {e}")
            raise


def _register_legacy_routers(app: FastAPI):
    """Registrar routers legacy com prefixo /legacy para evitar conflitos."""
    from app.api import processes, users, monitoring
    
    # Configuração de routers legacy
    legacy_routers_config = [
        (processes.router, "processes-legacy", "Processos judiciais (legacy)"),
        (users.router, "users-legacy", "Usuários (legacy)"),
        (monitoring.router, "monitoring-legacy", "Monitoramento (legacy)"),
    ]
    
    # Só registrar legacy em desenvolvimento ou se explicitamente habilitado
    if settings.debug or getattr(settings, 'enable_legacy_routes', False):
        for router, tag, description in legacy_routers_config:
            try:
                app.include_router(
                    router,
                    prefix="/legacy",
                    tags=[tag],
                    include_in_schema=settings.debug,  # Só aparece na doc em debug
                    responses={
                        404: {"description": "Recurso não encontrado (legacy)"},
                        500: {"description": "Erro interno do servidor (legacy)"},
                    }
                )
                logger.debug(f"Router legacy '{tag}' registrado com prefixo /legacy")
            except Exception as e:
                logger.error(f"Erro ao registrar router legacy '{tag}': {e}")
                raise
    else:
        logger.info("Routers legacy desabilitados em produção")


def get_router_info() -> dict:
    """
    Obter informações sobre os routers registrados.
    
    Returns:
        dict: Informações sobre routers versionados e legacy
    """
    return {
        "versioned": {
            "prefix": settings.api_prefix,
            "routers": ["processes", "users", "ultra-fast", "monitoring"],
            "enabled": True
        },
        "legacy": {
            "prefix": "/legacy",
            "routers": ["processes-legacy", "users-legacy", "ultra-fast-legacy", "monitoring-legacy"],
            "enabled": settings.debug or getattr(settings, 'enable_legacy_routes', False),
            "in_schema": settings.debug
        }
    }
