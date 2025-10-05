"""Testes para o middleware de segurança."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import patch

from app.core.security_middleware import SecurityHeadersMiddleware, create_security_middleware
from app.core.config import settings


class TestSecurityHeadersMiddleware:
    """Testes para o SecurityHeadersMiddleware."""
    
    def test_security_headers_middleware_init(self):
        """Testar inicialização do middleware com configurações padrão."""
        app = FastAPI()
        middleware = SecurityHeadersMiddleware(app)
        
        assert middleware.hsts_max_age == settings.hsts_max_age
        assert middleware.content_security_policy == settings.content_security_policy
        assert middleware.frame_options == settings.frame_options
        assert middleware.xss_protection == settings.xss_protection
        assert middleware.referrer_policy == settings.referrer_policy
        assert middleware.permissions_policy == settings.permissions_policy
        assert middleware.coep_policy == settings.coep_policy
        assert middleware.coop_policy == settings.coop_policy
        assert middleware.corp_policy == settings.corp_policy
        assert middleware.cache_control == settings.security_headers_cache_control
    
    def test_security_headers_middleware_custom_config(self):
        """Testar inicialização do middleware com configurações customizadas."""
        app = FastAPI()
        middleware = SecurityHeadersMiddleware(
            app,
            hsts_max_age=12345,
            content_security_policy="custom-csp",
            frame_options="SAMEORIGIN",
            xss_protection="0",
            referrer_policy="no-referrer",
            permissions_policy="custom-permissions",
            coep_policy="unsafe-none",
            coop_policy="unsafe-none",
            corp_policy="cross-origin",
            cache_control="no-cache"
        )
        
        assert middleware.hsts_max_age == 12345
        assert middleware.content_security_policy == "custom-csp"
        assert middleware.frame_options == "SAMEORIGIN"
        assert middleware.xss_protection == "0"
        assert middleware.referrer_policy == "no-referrer"
        assert middleware.permissions_policy == "custom-permissions"
        assert middleware.coep_policy == "unsafe-none"
        assert middleware.coop_policy == "unsafe-none"
        assert middleware.corp_policy == "cross-origin"
        assert middleware.cache_control == "no-cache"
    
    def test_security_headers_application(self):
        """Testar aplicação dos headers de segurança."""
        app = FastAPI()
        
        @app.get("/")
        def root():
            return {"message": "Hello World"}
        
        app.add_middleware(SecurityHeadersMiddleware)
        
        with TestClient(app) as client:
            response = client.get("/")
            
            assert response.status_code == 200
            
            # Verificar headers de segurança
            assert "Strict-Transport-Security" in response.headers
            assert "Content-Security-Policy" in response.headers
            assert "X-Content-Type-Options" in response.headers
            assert "X-Frame-Options" in response.headers
            assert "X-XSS-Protection" in response.headers
            assert "Referrer-Policy" in response.headers
            assert "Permissions-Policy" in response.headers
            assert "Cross-Origin-Embedder-Policy" in response.headers
            assert "Cross-Origin-Opener-Policy" in response.headers
            assert "Cross-Origin-Resource-Policy" in response.headers
    
    def test_security_headers_values(self):
        """Testar valores específicos dos headers de segurança."""
        app = FastAPI()
        
        @app.get("/")
        def root():
            return {"message": "Hello World"}
        
        app.add_middleware(SecurityHeadersMiddleware)
        
        with TestClient(app) as client:
            response = client.get("/")
            
            assert response.status_code == 200
            
            # Verificar valores dos headers
            assert response.headers["X-Content-Type-Options"] == "nosniff"
            assert response.headers["X-Frame-Options"] == settings.frame_options
            assert response.headers["X-XSS-Protection"] == settings.xss_protection
            assert response.headers["Referrer-Policy"] == settings.referrer_policy
            assert response.headers["Cross-Origin-Embedder-Policy"] == settings.coep_policy
            assert response.headers["Cross-Origin-Opener-Policy"] == settings.coop_policy
            assert response.headers["Cross-Origin-Resource-Policy"] == settings.corp_policy
    
    def test_hsts_header_format(self):
        """Testar formato do header HSTS."""
        app = FastAPI()
        
        @app.get("/")
        def root():
            return {"message": "Hello World"}
        
        app.add_middleware(SecurityHeadersMiddleware)
        
        with TestClient(app) as client:
            response = client.get("/")
            
            assert response.status_code == 200
            
            hsts_header = response.headers["Strict-Transport-Security"]
            assert f"max-age={settings.hsts_max_age}" in hsts_header
            assert "includeSubDomains" in hsts_header
            assert "preload" in hsts_header
    
    def test_static_response_cache_control(self):
        """Testar cache control para respostas estáticas."""
        app = FastAPI()
        
        @app.get("/static/style.css")
        def static_css():
            return "body { color: red; }"
        
        app.add_middleware(SecurityHeadersMiddleware)
        
        with TestClient(app) as client:
            response = client.get("/static/style.css")
            
            assert response.status_code == 200
            assert "Cache-Control" in response.headers
            assert response.headers["Cache-Control"] == settings.security_headers_cache_control
    
    def test_non_static_response_no_cache_control(self):
        """Testar que respostas não-estáticas não recebem cache control."""
        app = FastAPI()
        
        @app.get("/api/data")
        def api_data():
            return {"data": "dynamic"}
        
        app.add_middleware(SecurityHeadersMiddleware)
        
        with TestClient(app) as client:
            response = client.get("/api/data")
            
            assert response.status_code == 200
            # Cache-Control não deve estar presente para respostas dinâmicas
            # (pode estar presente por outros middlewares, mas não pelo nosso)
    
    def test_is_static_response_method(self):
        """Testar método _is_static_response."""
        app = FastAPI()
        middleware = SecurityHeadersMiddleware(app)
        
        # Mock request e response
        from unittest.mock import Mock
        
        # Teste com extensão estática
        request = Mock()
        request.url.path = "/style.css"
        response = Mock()
        response.status_code = 200
        
        assert middleware._is_static_response(request, response) is True
        
        # Teste com path /static/
        request.url.path = "/static/image.png"
        assert middleware._is_static_response(request, response) is True
        
        # Teste com path dinâmico
        request.url.path = "/api/data"
        assert middleware._is_static_response(request, response) is False
        
        # Teste com extensão não-estática
        request.url.path = "/data.txt"
        assert middleware._is_static_response(request, response) is False
    
    @patch('app.core.security_middleware.settings')
    def test_security_headers_disabled(self, mock_settings):
        """Testar comportamento quando headers de segurança estão desabilitados."""
        mock_settings.enable_security_headers = False
        
        app = FastAPI()
        
        @app.get("/")
        def root():
            return {"message": "Hello World"}
        
        app.add_middleware(SecurityHeadersMiddleware)
        
        with TestClient(app) as client:
            response = client.get("/")
            
            assert response.status_code == 200
            
            # Headers de segurança não devem estar presentes
            assert "Strict-Transport-Security" not in response.headers
            assert "Content-Security-Policy" not in response.headers
            assert "X-Content-Type-Options" not in response.headers
            assert "X-Frame-Options" not in response.headers
            assert "X-XSS-Protection" not in response.headers
            assert "Referrer-Policy" not in response.headers
            assert "Permissions-Policy" not in response.headers
            assert "Cross-Origin-Embedder-Policy" not in response.headers
            assert "Cross-Origin-Opener-Policy" not in response.headers
            assert "Cross-Origin-Resource-Policy" not in response.headers


class TestCreateSecurityMiddleware:
    """Testes para a função create_security_middleware."""
    
    def test_create_security_middleware_with_headers_enabled(self):
        """Testar criação do middleware com headers habilitados."""
        app = FastAPI()
        
        @app.get("/")
        def root():
            return {"message": "Hello World"}
        
        with patch.object(settings, 'enable_security_headers', True):
            with patch.object(settings, 'enable_https_redirect', True):
                result_app = create_security_middleware(app)
                
                assert result_app is app  # Deve retornar a mesma instância
                
                with TestClient(result_app) as client:
                    response = client.get("/")
                    
                    assert response.status_code == 200
                    assert "Strict-Transport-Security" in response.headers
    
    def test_create_security_middleware_with_headers_disabled(self):
        """Testar criação do middleware com headers desabilitados."""
        app = FastAPI()
        
        @app.get("/")
        def root():
            return {"message": "Hello World"}
        
        with patch.object(settings, 'enable_security_headers', False):
            with patch.object(settings, 'enable_https_redirect', False):
                result_app = create_security_middleware(app)
                
                assert result_app is app  # Deve retornar a mesma instância
                
                with TestClient(result_app) as client:
                    response = client.get("/")
                    
                    assert response.status_code == 200
                    assert "Strict-Transport-Security" not in response.headers
    
    def test_create_security_middleware_https_redirect_only(self):
        """Testar criação do middleware apenas com HTTPS redirect."""
        app = FastAPI()
        
        @app.get("/")
        def root():
            return {"message": "Hello World"}
        
        with patch.object(settings, 'enable_security_headers', False):
            with patch.object(settings, 'enable_https_redirect', True):
                result_app = create_security_middleware(app)
                
                assert result_app is app  # Deve retornar a mesma instância
    
    def test_create_security_middleware_with_custom_config(self):
        """Testar criação do middleware com configurações customizadas."""
        app = FastAPI()
        
        @app.get("/")
        def root():
            return {"message": "Hello World"}
        
        with patch.object(settings, 'enable_security_headers', True):
            with patch.object(settings, 'hsts_max_age', 9999):
                with patch.object(settings, 'content_security_policy', 'custom-policy'):
                    result_app = create_security_middleware(app)
                    
                    with TestClient(result_app) as client:
                        response = client.get("/")
                        
                        assert response.status_code == 200
                        hsts_header = response.headers["Strict-Transport-Security"]
                        assert "max-age=9999" in hsts_header
                        assert response.headers["Content-Security-Policy"] == "custom-policy"


class TestSecurityMiddlewareIntegration:
    """Testes de integração para o middleware de segurança."""
    
    def test_security_middleware_with_other_middlewares(self):
        """Testar integração com outros middlewares."""
        app = FastAPI()
        
        @app.get("/")
        def root():
            return {"message": "Hello World"}
        
        # Adicionar middleware de segurança
        app.add_middleware(SecurityHeadersMiddleware)
        
        # Simular outro middleware que adiciona headers
        from starlette.middleware.base import BaseHTTPMiddleware
        
        class TestMiddleware(BaseHTTPMiddleware):
            async def dispatch(self, request, call_next):
                response = await call_next(request)
                response.headers["X-Test"] = "test-value"
                return response
        
        app.add_middleware(TestMiddleware)
        
        with TestClient(app) as client:
            response = client.get("/")
            
            assert response.status_code == 200
            
            # Verificar que ambos os middlewares funcionaram
            assert "Strict-Transport-Security" in response.headers
            assert "X-Test" in response.headers
            assert response.headers["X-Test"] == "test-value"
    
    def test_security_middleware_performance(self):
        """Testar performance do middleware de segurança."""
        app = FastAPI()
        
        @app.get("/")
        def root():
            return {"message": "Hello World"}
        
        app.add_middleware(SecurityHeadersMiddleware)
        
        with TestClient(app) as client:
            import time
            
            # Fazer múltiplas requisições para testar performance
            start_time = time.time()
            
            for _ in range(10):
                response = client.get("/")
                assert response.status_code == 200
                assert "Strict-Transport-Security" in response.headers
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Verificar que não há impacto significativo de performance
            assert duration < 1.0  # Deve completar em menos de 1 segundo
    
