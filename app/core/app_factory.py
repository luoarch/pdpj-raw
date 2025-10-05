"""Factory para criação da aplicação FastAPI com lógica comum centralizada."""

from fastapi import FastAPI
from loguru import logger

from app.core.config import settings
from app.core.middleware_config import create_middleware_stack
from app.core.app_events import register_startup_events, register_shutdown_events
from app.core.core_endpoints import register_core_endpoints
from app.core.router_config import register_api_routers


def configure_logging():
    """Configurar sistema de logging."""
    logger.remove()
    logger.add(
        "logs/app.log" if settings.log_file else "sys.stderr",
        level=settings.log_level,
        rotation="1 day",
        retention="30 days",
        format=settings.log_format,
        filter=lambda record: True,
    )


def create_fastapi_app() -> FastAPI:
    """Criar aplicação FastAPI com todas as configurações."""
    
    app = FastAPI(
        title=settings.api_title,
        description=settings.api_description,
        version=settings.api_version,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
    )
    
    # Configurar componentes em ordem
    configure_logging()
    app = create_middleware_stack(app)
    register_startup_events(app)
    register_shutdown_events(app)
    register_core_endpoints(app)
    register_api_routers(app)
    
    return app
