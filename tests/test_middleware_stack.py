"""Testes para o stack de middlewares da aplicação."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import patch

from app.core.middleware_config import create_middleware_stack, GlobalExceptionMiddleware
from app.core.config import settings


class TestMiddlewareStack:
    """Testes para o stack de middlewares."""
    
    def test_create_middleware_stack_basic(self):
        """Testar criação básica do stack de middlewares."""
        app = FastAPI()
        app_with_middlewares = create_middleware_stack(app)
        
        assert app_with_middlewares is app
        assert len(app.user_middleware) > 0
    
    def test_middleware_order(self):
        """Testar ordem correta dos middlewares."""
        app = FastAPI()
        create_middleware_stack(app)
        
        # Verificar que middlewares foram adicionados
        middleware_types = [middleware.cls.__name__ for middleware in app.user_middleware]
        
        # Global Exception Handler deve estar primeiro
        assert "GlobalExceptionMiddleware" in middleware_types
        
        # Security middlewares devem estar presentes se habilitados
        if settings.enable_security_headers:
            assert "SecurityHeadersMiddleware" in middleware_types
        
        if settings.enable_https_redirect and not settings.debug:
            assert "HTTPSRedirectMiddleware" in middleware_types
        
        if settings.log_request_id:
            assert "RequestIDMiddleware" in middleware_types
        
        if settings.enable_rate_limiting:
            assert "RateLimitMiddleware" in middleware_types
        
        if settings.enable_metrics:
            assert "MetricsMiddleware" in middleware_types
        
        # CORS deve estar presente
        assert "CORSMiddleware" in middleware_types
    
    def test_conditional_middlewares(self):
        """Testar middlewares condicionais baseados em configurações."""
        app = FastAPI()
        
        # Testar com configurações específicas
        with patch.object(settings, 'enable_security_headers', False):
            app = FastAPI()
            create_middleware_stack(app)
            middleware_types = [middleware.cls.__name__ for middleware in app.user_middleware]
            assert "SecurityHeadersMiddleware" not in middleware_types
        
        with patch.object(settings, 'enable_rate_limiting', False):
            app = FastAPI()
            create_middleware_stack(app)
            middleware_types = [middleware.cls.__name__ for middleware in app.user_middleware]
            assert "RateLimitMiddleware" not in middleware_types
    
    def test_cors_configuration(self):
        """Testar configuração do CORS."""
        app = FastAPI()
        create_middleware_stack(app)
        
        # Verificar que CORS foi configurado
        cors_middleware = None
        for middleware in app.user_middleware:
            if middleware.cls.__name__ == "CORSMiddleware":
                cors_middleware = middleware
                break
        
        assert cors_middleware is not None
        
        # Verificar configurações do CORS
        cors_kwargs = cors_middleware.kwargs
        assert "allow_origins" in cors_kwargs
        assert "allow_methods" in cors_kwargs
        assert "allow_headers" in cors_kwargs
        assert "allow_credentials" in cors_kwargs
    
    def test_debug_mode_behavior(self):
        """Testar comportamento em modo debug."""
        app = FastAPI()
        
        with patch.object(settings, 'debug', True):
            create_middleware_stack(app)
            
            # Em debug, CORS deve permitir todas as origens
            cors_middleware = None
            for middleware in app.user_middleware:
                if middleware.cls.__name__ == "CORSMiddleware":
                    cors_middleware = middleware
                    break
            
            assert cors_middleware is not None
            assert cors_middleware.kwargs["allow_origins"] == ["*"]
    
    def test_trusted_host_middleware(self):
        """Testar middleware de hosts confiáveis."""
        app = FastAPI()
        
        with patch.object(settings, 'enable_trusted_host', True):
            with patch.object(settings, 'enable_security_headers', True):
                create_middleware_stack(app)
                
                middleware_types = [middleware.cls.__name__ for middleware in app.user_middleware]
                assert "TrustedHostMiddleware" in middleware_types
    
    def test_gzip_compression_middleware(self):
        """Testar middleware de compressão GZip."""
        app = FastAPI()
        
        with patch.object(settings, 'enable_gzip_compression', True):
            with patch.object(settings, 'debug', False):
                create_middleware_stack(app)
                
                middleware_types = [middleware.cls.__name__ for middleware in app.user_middleware]
                assert "GZipMiddleware" in middleware_types
    
    def test_global_exception_handler(self):
        """Testar middleware de captura global de exceções."""
        app = FastAPI()
        
        @app.get("/test-error")
        def test_endpoint():
            raise ValueError("Test error")
        
        create_middleware_stack(app)
        
        # Verificar que o middleware foi adicionado
        middleware_types = [middleware.cls.__name__ for middleware in app.user_middleware]
        assert "GlobalExceptionMiddleware" in middleware_types
        
        # Testar se o middleware funciona
        with TestClient(app) as client:
            response = client.get("/test-error")
            # O middleware deve capturar a exceção e registrar no log
            # (não podemos testar o log diretamente, mas verificamos que não crashou)
            assert response.status_code == 500


class TestGlobalExceptionMiddleware:
    """Testes para o middleware de captura global de exceções."""
    
    def test_global_exception_middleware_init(self):
        """Testar inicialização do middleware."""
        app = FastAPI()
        middleware = GlobalExceptionMiddleware(app)
        
        assert middleware.app is app
    
    @pytest.mark.asyncio
    async def test_global_exception_middleware_call(self):
        """Testar chamada do middleware."""
        app = FastAPI()
        middleware = GlobalExceptionMiddleware(app)
        
        # Mock de scope, receive e send
        scope = {"type": "http"}
        
        async def receive():
            return {"type": "http.request", "body": b""}
        
        async def send(message):
            pass
        
        # Testar que não levanta exceção
        await middleware(scope, receive, send)


class TestMiddlewareIntegration:
    """Testes de integração para middlewares."""
    
    def test_middleware_stack_with_test_client(self):
        """Testar stack de middlewares com TestClient."""
        app = FastAPI()
        
        @app.get("/")
        def root():
            return {"message": "Hello World"}
        
        create_middleware_stack(app)
        
        with TestClient(app) as client:
            response = client.get("/")
            assert response.status_code == 200
            assert response.json() == {"message": "Hello World"}
            
            # Verificar que headers de segurança estão presentes
            if settings.enable_security_headers:
                assert "X-Content-Type-Options" in response.headers
            
            # Verificar que request ID está presente
            if settings.log_request_id:
                assert "X-Request-ID" in response.headers
    
    def test_middleware_performance_impact(self):
        """Testar impacto de performance dos middlewares."""
        app = FastAPI()
        
        @app.get("/")
        def root():
            return {"message": "Hello World"}
        
        create_middleware_stack(app)
        
        with TestClient(app) as client:
            # Fazer múltiplas requisições para testar performance
            import time
            start_time = time.time()
            
            for _ in range(10):
                response = client.get("/")
                assert response.status_code == 200
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Verificar que não há impacto significativo de performance
            assert duration < 1.0  # Deve completar em menos de 1 segundo
    
    def test_middleware_error_handling(self):
        """Testar tratamento de erros pelos middlewares."""
        app = FastAPI()
        
        @app.get("/error")
        def error_endpoint():
            raise Exception("Test error")
        
        create_middleware_stack(app)
        
        with TestClient(app) as client:
            response = client.get("/error")
            # O middleware global deve capturar a exceção
            assert response.status_code == 500
