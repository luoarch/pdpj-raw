"""Configurações e factory para middlewares da aplicação FastAPI."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from loguru import logger

from app.core.config import settings
from app.core.rate_limiting import RequestIDMiddleware, RateLimitMiddleware
from app.core.metrics_middleware import MetricsMiddleware
from app.core.security_middleware import SecurityHeadersMiddleware, HTTPSRedirectMiddleware
from app.core.versioning_middleware import create_versioning_middleware


class GlobalExceptionMiddleware:
    """Middleware para captura global de exceções."""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            try:
                await self.app(scope, receive, send)
            except Exception as e:
                logger.error(f"Erro global capturado: {e}")
                # Em produção, você pode integrar com Sentry/Datadog aqui
                raise
        else:
            await self.app(scope, receive, send)


def create_middleware_stack(app: FastAPI) -> FastAPI:
    """
    Configurar stack de middlewares na ordem correta.
    
    Ordem dos middlewares (do último para o primeiro):
    1. Global Exception Handler (primeiro a capturar exceções)
    2. Trusted Host (validação de host confiável)
    3. GZip Compression (compressão de resposta)
    4. Security Headers (headers de segurança)
    5. HTTPS Redirect (redirecionamento HTTPS)
    6. Request ID (rastreabilidade)
    7. Rate Limiting (proteção contra abuso)
    8. Metrics (observabilidade)
    9. CORS (controle de acesso cross-origin)
    """
    
    # Global Exception Handler
    if settings.enable_global_exception_handler:
        logger.info("Global exception handler middleware enabled")
        app.add_middleware(GlobalExceptionMiddleware)
    
    # Trusted Host Middleware (proteção contra Host Header attacks) - DESABILITADO PARA DESENVOLVIMENTO
    # if settings.enable_trusted_host and settings.enable_security_headers:
    #     trusted_hosts = ["*"] if settings.debug else list(settings.cors_origins)
    #     logger.info(f"Trusted host middleware enabled with hosts: {trusted_hosts}")
    #     app.add_middleware(
    #         TrustedHostMiddleware,
    #         allowed_hosts=trusted_hosts
    #     )
    
    # GZip Compression (melhoria de performance)
    if settings.enable_gzip_compression and not settings.debug:
        logger.info(f"GZip compression middleware enabled (min size: {settings.gzip_minimum_size} bytes)")
        app.add_middleware(GZipMiddleware, minimum_size=settings.gzip_minimum_size)
    
    # Security Headers (aplicados primeiro para máxima proteção)
    if settings.enable_security_headers:
        logger.info("Security headers middleware enabled")
        app.add_middleware(SecurityHeadersMiddleware)
    
    # HTTPS Redirect (redirecionamento para HTTPS) - DESABILITADO PARA DESENVOLVIMENTO
    # if settings.enable_https_redirect and not settings.debug and settings.environment != 'development':
    #     logger.info("HTTPS redirect middleware enabled")
    #     app.add_middleware(HTTPSRedirectMiddleware)
    
    # Request ID (rastreabilidade para todas as requisições)
    if settings.log_request_id:
        logger.info("Request ID middleware enabled")
        app.add_middleware(RequestIDMiddleware)
    
    # Versioning (versionamento dinâmico da API)
    if getattr(settings, 'enable_api_versioning', False):
        logger.info("API versioning middleware enabled")
        app.add_middleware(create_versioning_middleware)
    
    # Rate Limiting (proteção contra abuso)
    if settings.enable_rate_limiting:
        logger.info(f"Rate limiting middleware enabled: {settings.rate_limit_requests} req/{settings.rate_limit_window}s")
        app.add_middleware(RateLimitMiddleware)
    
    # Metrics (observabilidade e monitoramento)
    if settings.enable_metrics:
        logger.info(f"Metrics middleware enabled at {settings.metrics_path}")
        app.add_middleware(MetricsMiddleware)
    
    # CORS (controle de acesso cross-origin)
    cors_origins = list(settings.cors_origins) if settings.cors_origins else []
    if settings.debug:
        cors_origins = ["*"]  # Permitir todas as origens em desenvolvimento
    
    if cors_origins:
        logger.info(f"CORS middleware enabled with origins: {cors_origins}")
        app.add_middleware(
            CORSMiddleware,
            allow_origins=cors_origins,
            allow_credentials=settings.cors_allow_credentials,
            allow_methods=list(settings.cors_allow_methods),
            allow_headers=list(settings.cors_allow_headers),
        )
    else:
        logger.warning("CORS middleware disabled - no origins configured")
    
    return app
