"""Middleware de segurança para FastAPI."""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.types import ASGIApp
from loguru import logger

from app.core.config import settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware para adicionar headers de segurança."""
    
    def __init__(
        self,
        app: ASGIApp,
        hsts_max_age: int = None,
        content_security_policy: str = None,
        frame_options: str = None,
        xss_protection: str = None,
        referrer_policy: str = None,
        permissions_policy: str = None,
        coep_policy: str = None,
        coop_policy: str = None,
        corp_policy: str = None,
        cache_control: str = None
    ):
        super().__init__(app)
        
        # Usar configurações do settings como padrão se não fornecidas
        self.hsts_max_age = hsts_max_age or settings.hsts_max_age
        self.content_security_policy = content_security_policy or settings.content_security_policy
        self.frame_options = frame_options or settings.frame_options
        self.xss_protection = xss_protection or settings.xss_protection
        self.referrer_policy = referrer_policy or settings.referrer_policy
        self.permissions_policy = permissions_policy or settings.permissions_policy
        self.coep_policy = coep_policy or settings.coep_policy
        self.coop_policy = coop_policy or settings.coop_policy
        self.corp_policy = corp_policy or settings.corp_policy
        self.cache_control = cache_control or settings.security_headers_cache_control
    
    async def dispatch(self, request: Request, call_next):
        """Adicionar headers de segurança à resposta."""
        response = await call_next(request)
        
        # Headers de segurança para todas as respostas
        if settings.enable_security_headers:
            self._apply_security_headers(request, response)
        
        return response
    
    def _apply_security_headers(self, request: Request, response):
        """Aplicar headers de segurança à resposta."""
        # Cache Control para headers de segurança (apenas para respostas estáticas)
        if self._is_static_response(request, response):
            response.headers["Cache-Control"] = self.cache_control
        
        # HSTS (HTTP Strict Transport Security)
        response.headers["Strict-Transport-Security"] = f"max-age={self.hsts_max_age}; includeSubDomains; preload"
        
        # Content Security Policy
        response.headers["Content-Security-Policy"] = self.content_security_policy
        
        # X-Content-Type-Options
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # X-Frame-Options
        response.headers["X-Frame-Options"] = self.frame_options
        
        # X-XSS-Protection
        response.headers["X-XSS-Protection"] = self.xss_protection
        
        # Referrer Policy
        response.headers["Referrer-Policy"] = self.referrer_policy
        
        # Permissions Policy
        response.headers["Permissions-Policy"] = self.permissions_policy
        
        # Cross-Origin-Embedder-Policy
        response.headers["Cross-Origin-Embedder-Policy"] = self.coep_policy
        
        # Cross-Origin-Opener-Policy
        response.headers["Cross-Origin-Opener-Policy"] = self.coop_policy
        
        # Cross-Origin-Resource-Policy
        response.headers["Cross-Origin-Resource-Policy"] = self.corp_policy
        
        # Log com request_id se disponível
        request_id = getattr(request.state, 'request_id', None)
        if request_id:
            logger.debug(f"Security headers aplicados - Request ID: {request_id}")
    
    def _is_static_response(self, request: Request, response) -> bool:
        """Verificar se a resposta é para um recurso estático que pode ser cached."""
        static_extensions = {'.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.ico', '.svg', '.woff', '.woff2'}
        path = request.url.path.lower()
        
        # Verificar se é um arquivo estático
        if any(path.endswith(ext) for ext in static_extensions):
            return True
        
        # Verificar se é uma resposta de sucesso para recursos estáticos
        if response.status_code == 200 and path.startswith('/static/'):
            return True
        
        return False


def create_security_middleware(app):
    """
    Criar middleware de segurança usando o padrão add_middleware.
    
    Args:
        app: Instância da aplicação FastAPI
        
    Returns:
        FastAPI: Aplicação com middlewares de segurança adicionados
    """
    # Security Headers Middleware
    if settings.enable_security_headers:
        logger.info("Headers de segurança habilitados")
        app.add_middleware(
            SecurityHeadersMiddleware,
            hsts_max_age=settings.hsts_max_age,
            content_security_policy=settings.content_security_policy,
            frame_options=settings.frame_options,
            xss_protection=settings.xss_protection,
            referrer_policy=settings.referrer_policy,
            permissions_policy=settings.permissions_policy,
            coep_policy=settings.coep_policy,
            coop_policy=settings.coop_policy,
            corp_policy=settings.corp_policy,
            cache_control=settings.security_headers_cache_control
        )
    else:
        logger.info("Headers de segurança desabilitados")
    
    # HTTPS Redirect Middleware
    if settings.enable_https_redirect:
        logger.info("Redirecionamento HTTPS habilitado")
        app.add_middleware(HTTPSRedirectMiddleware)
    else:
        logger.info("Redirecionamento HTTPS desabilitado")
    
    return app
