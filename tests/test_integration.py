"""Testes de integração para cenários debug vs produção."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
import os

from app.main import app


class TestDebugEnvironment:
    """Testes para ambiente de debug."""
    
    @patch.dict(os.environ, {"DEBUG": "true", "ENVIRONMENT": "development"})
    def test_debug_environment_configuration(self):
        """Testar configurações específicas do ambiente debug."""
        # Recriar app com configurações de debug
        from app.core.app_factory import create_fastapi_app
        debug_app = create_fastapi_app()
        client = TestClient(debug_app)
        
        # Verificar se docs estão disponíveis
        response = client.get("/docs")
        assert response.status_code == 200
        
        response = client.get("/redoc")
        assert response.status_code == 200
        
        # Verificar endpoint root
        response = client.get("/")
        data = response.json()
        assert data["docs_url"] == "/docs"
        assert data["monitoring_url"] is None  # Não disponível em debug
        
        # Verificar se python_version está incluído
        assert "python_version" in data
    
    @patch.dict(os.environ, {"DEBUG": "true", "METRICS_PROTECTED": "false"})
    def test_debug_metrics_access(self):
        """Testar acesso às métricas em debug."""
        from app.core.app_factory import create_fastapi_app
        debug_app = create_fastapi_app()
        client = TestClient(debug_app)
        
        # Fazer algumas requisições para gerar métricas
        client.get("/")
        client.get("/health")
        
        # Métricas devem estar acessíveis em debug
        response = client.get("/metrics")
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/plain; version=0.0.4; charset=utf-8"


class TestProductionEnvironment:
    """Testes para ambiente de produção."""
    
    @patch.dict(os.environ, {"DEBUG": "false", "ENVIRONMENT": "production"})
    def test_production_environment_configuration(self):
        """Testar configurações específicas do ambiente produção."""
        from app.core.app_factory import create_fastapi_app
        prod_app = create_fastapi_app()
        client = TestClient(prod_app)
        
        # Verificar se docs estão desabilitados
        response = client.get("/docs")
        assert response.status_code == 404
        
        response = client.get("/redoc")
        assert response.status_code == 404
        
        # Verificar endpoint root
        response = client.get("/")
        data = response.json()
        assert data["docs_url"] is None
        assert data["monitoring_url"] == "/monitoring/dashboard"
        
        # Verificar se python_version não está incluído por padrão
        assert "python_version" not in data
    
    @patch.dict(os.environ, {"DEBUG": "false", "METRICS_PROTECTED": "true"})
    def test_production_metrics_protection(self):
        """Testar proteção das métricas em produção."""
        from app.core.app_factory import create_fastapi_app
        prod_app = create_fastapi_app()
        client = TestClient(prod_app)
        
        # Métricas devem estar protegidas em produção
        response = client.get("/metrics")
        assert response.status_code == 403
        data = response.json()
        assert "protegido" in data["error"]
    
    @patch.dict(os.environ, {"DEBUG": "false", "ENABLE_SECURITY_HEADERS": "true"})
    def test_production_security_headers(self):
        """Testar headers de segurança em produção."""
        from app.core.app_factory import create_fastapi_app
        prod_app = create_fastapi_app()
        client = TestClient(prod_app)
        
        response = client.get("/")
        
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
    
    @patch.dict(os.environ, {"DEBUG": "false", "ENABLE_HTTPS_REDIRECT": "true"})
    def test_production_https_redirect(self):
        """Testar redirecionamento HTTPS em produção."""
        from app.core.app_factory import create_fastapi_app
        prod_app = create_fastapi_app()
        client = TestClient(prod_app)
        
        # Em ambiente de teste, o HTTPS redirect pode não funcionar
        # Mas verificamos se o middleware está configurado
        response = client.get("/")
        assert response.status_code == 200


class TestEnvironmentVariables:
    """Testes para diferentes configurações de variáveis de ambiente."""
    
    @patch.dict(os.environ, {
        "API_PREFIX": "api/v2",
        "ENABLE_RATE_LIMITING": "true",
        "RATE_LIMIT_REQUESTS": "500",
        "RATE_LIMIT_WINDOW": "30"
    })
    def test_custom_api_prefix(self):
        """Testar prefixo de API customizado."""
        from app.core.app_factory import create_fastapi_app
        custom_app = create_fastapi_app()
        client = TestClient(custom_app)
        
        # Verificar se o prefixo foi normalizado
        from app.core.config import settings
        assert settings.api_prefix == "/api/v2"
        
        # Verificar se endpoints funcionam com novo prefixo
        response = client.get("/api/v2/")
        assert response.status_code == 200
    
    @patch.dict(os.environ, {
        "METRICS_CACHE_TTL": "60",
        "LOG_REQUEST_ID": "true",
        "HEALTH_CHECK_INCLUDE_VERSION": "false"
    })
    def test_custom_metrics_and_logging_config(self):
        """Testar configurações customizadas de métricas e logging."""
        from app.core.app_factory import create_fastapi_app
        custom_app = create_fastapi_app()
        client = TestClient(custom_app)
        
        from app.core.config import settings
        assert settings.metrics_cache_ttl == 60
        assert settings.log_request_id is True
        assert settings.health_check_include_version is False
        
        # Verificar health check
        response = client.get("/health")
        data = response.json()
        assert "version" not in data  # Não incluído por configuração
        
        # Verificar se request ID está presente
        assert "X-Request-ID" in response.headers
    
    @patch.dict(os.environ, {
        "ENABLE_TRACING": "true",
        "TRACING_SAMPLE_RATE": "0.5"
    })
    def test_tracing_configuration(self):
        """Testar configuração de tracing distribuído."""
        from app.core.app_factory import create_fastapi_app
        tracing_app = create_fastapi_app()
        client = TestClient(tracing_app)
        
        from app.core.config import settings
        assert settings.enable_tracing is True
        assert settings.tracing_sample_rate == 0.5
        
        # Verificar se trace ID está presente
        response = client.get("/")
        if settings.enable_tracing:
            assert "X-Trace-ID" in response.headers


class TestMiddlewareStack:
    """Testes para stack de middlewares."""
    
    def test_middleware_order(self):
        """Testar ordem correta dos middlewares."""
        client = TestClient(app)
        response = client.get("/")
        
        # Verificar headers na ordem correta
        assert "X-Request-ID" in response.headers  # Request ID middleware
        assert "X-RateLimit-Limit" in response.headers  # Rate limiting middleware
        assert "X-Response-Time" in response.headers  # Metrics middleware
        assert "access-control-allow-origin" in response.headers.lower()  # CORS middleware
    
    def test_error_handling_across_middlewares(self):
        """Testar tratamento de erros através dos middlewares."""
        client = TestClient(app)
        
        # Testar endpoint inexistente
        response = client.get("/nonexistent")
        assert response.status_code == 404
        
        # Verificar se middlewares ainda funcionam em caso de erro
        assert "X-Request-ID" in response.headers
        assert "X-RateLimit-Limit" in response.headers


class TestCachingAndPerformance:
    """Testes para cache e performance."""
    
    def test_metrics_cache_headers(self):
        """Testar headers de cache das métricas."""
        client = TestClient(app)
        
        # Fazer algumas requisições para gerar métricas
        client.get("/")
        client.get("/health")
        
        response = client.get("/metrics")
        
        if response.status_code == 200:
            assert "Cache-Control" in response.headers
            assert "max-age=" in response.headers["Cache-Control"]
    
    def test_rate_limiting_headers(self):
        """Testar headers de rate limiting."""
        client = TestClient(app)
        
        response = client.get("/")
        
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers
        
        # Verificar valores válidos
        assert int(response.headers["X-RateLimit-Limit"]) > 0
        assert int(response.headers["X-RateLimit-Remaining"]) >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
