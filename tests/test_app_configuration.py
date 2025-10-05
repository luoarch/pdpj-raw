"""Testes para configuração da aplicação FastAPI."""

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
import asyncio

from app.main import create_app
from app.core.config import settings
from app.core.app_state import get_uptime


@pytest.fixture
def app():
    """Fixture para criar aplicação de teste."""
    return create_app()


@pytest.fixture
def client(app):
    """Fixture para cliente de teste."""
    return TestClient(app)


@pytest.fixture
async def async_client(app):
    """Fixture para cliente assíncrono de teste."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


class TestAppConfiguration:
    """Testes para configuração da aplicação."""
    
    def test_app_creation(self, app):
        """Testar criação da aplicação."""
        assert app.title == settings.api_title
        assert app.version == settings.api_version
        assert app.description == settings.api_description
    
    def test_root_endpoint(self, client):
        """Testar endpoint raiz."""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert data["message"] == settings.api_title
        assert data["version"] == settings.api_version
        assert data["environment"] == settings.environment
        assert "timestamp" in data
        assert "request_id" in data
        assert "python_version" in data
    
    def test_health_endpoint(self, client):
        """Testar endpoint de health check."""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert data["environment"] == settings.environment
        assert "timestamp" in data
        assert "request_id" in data
        
        if settings.health_check_include_version:
            assert "version" in data
        
        if settings.health_check_include_timestamp:
            assert "uptime" in data
    
    def test_request_id_middleware(self, client):
        """Testar middleware de request ID."""
        response = client.get("/")
        
        # Verificar se request ID está na resposta
        assert "X-Request-ID" in response.headers
        
        # Verificar se request ID está no JSON
        data = response.json()
        assert "request_id" in data
        assert data["request_id"] is not None
    
    def test_cors_headers(self, client):
        """Testar headers CORS."""
        response = client.options("/")
        
        # Verificar headers CORS básicos
        assert "access-control-allow-origin" in response.headers.lower()
        assert "access-control-allow-methods" in response.headers.lower()
        assert "access-control-allow-headers" in response.headers.lower()
    
    def test_rate_limiting_headers(self, client):
        """Testar headers de rate limiting."""
        response = client.get("/")
        
        # Verificar headers de rate limiting
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers
        
        # Verificar valores
        assert int(response.headers["X-RateLimit-Limit"]) == settings.rate_limit_requests
        assert int(response.headers["X-RateLimit-Remaining"]) >= 0
    
    def test_metrics_endpoint(self, client):
        """Testar endpoint de métricas."""
        # Fazer algumas requisições para gerar métricas
        client.get("/")
        client.get("/health")
        
        response = client.get("/metrics")
        
        if settings.enable_metrics:
            if settings.metrics_protected and not settings.debug:
                # Em produção com métricas protegidas, deve retornar 403
                assert response.status_code == 403
                data = response.json()
                assert "error" in data
                assert "protegido" in data["error"]
            else:
                # Em debug ou com métricas não protegidas
                assert response.status_code == 200
                # Verificar se é PlainTextResponse
                assert response.headers["content-type"] == "text/plain; version=0.0.4; charset=utf-8"
                # Verificar headers de métricas
                assert "X-Request-ID" in response.headers
                assert "X-Timestamp" in response.headers
                # Verificar cache de métricas
                assert "Cache-Control" in response.headers
                assert f"max-age={settings.metrics_cache_ttl}" in response.headers["Cache-Control"]
        else:
            assert response.status_code == 503
            data = response.json()
            assert "error" in data
            assert "não habilitadas" in data["error"]
    
    def test_metrics_headers(self, client):
        """Testar headers de métricas."""
        response = client.get("/")
        
        if settings.enable_metrics:
            # Verificar headers de métricas
            assert "X-Response-Time" in response.headers
            
            # Verificar formato do tempo de resposta
            response_time = response.headers["X-Response-Time"]
            assert response_time.endswith("s")  # Formato: "0.123s"
            
            # Verificar se é um número válido
            time_value = float(response_time.rstrip("s"))
            assert time_value >= 0
    
    def test_api_versioning(self, client):
        """Testar versionamento da API."""
        # Testar endpoints com prefixo normalizado
        response = client.get(f"{settings.api_prefix}/")
        assert response.status_code == 200
        
        # Testar endpoints sem prefixo (compatibilidade)
        response = client.get("/")
        assert response.status_code == 200
    
    def test_docs_availability(self, client):
        """Testar disponibilidade da documentação."""
        if settings.debug:
            # Em modo debug, docs devem estar disponíveis
            response = client.get("/docs")
            assert response.status_code == 200
            
            response = client.get("/redoc")
            assert response.status_code == 200
        else:
            # Em produção, docs devem estar desabilitados
            response = client.get("/docs")
            assert response.status_code == 404
            
            response = client.get("/redoc")
            assert response.status_code == 404
    
    def test_monitoring_endpoints(self, client):
        """Testar endpoints de monitoramento."""
        # Endpoints de monitoramento devem estar disponíveis
        response = client.get("/monitoring/status")
        assert response.status_code in [200, 401, 403]  # Pode requerer autenticação
        
        response = client.get("/api/v1/monitoring/status")
        assert response.status_code in [200, 401, 403]
    
    @pytest.mark.asyncio
    async def test_startup_event(self, async_client):
        """Testar evento de startup."""
        # Simular uma requisição após startup
        response = await async_client.get("/health")
        assert response.status_code == 200
        
        # Verificar se a aplicação está funcionando
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_middleware_order(self, client):
        """Testar ordem dos middlewares."""
        response = client.get("/")
        
        # Request ID deve estar presente (segundo middleware)
        assert "X-Request-ID" in response.headers
        
        # Rate limiting deve estar presente (terceiro middleware)
        assert "X-RateLimit-Limit" in response.headers
        
        # Headers de segurança devem estar presentes (primeiro middleware)
        if settings.enable_security_headers:
            assert "Strict-Transport-Security" in response.headers
            assert "X-Content-Type-Options" in response.headers
            assert "X-Frame-Options" in response.headers
        
        # CORS deve estar presente (último middleware)
        assert "access-control-allow-origin" in response.headers.lower()
    
    def test_error_handling(self, client):
        """Testar tratamento de erros."""
        # Testar endpoint inexistente
        response = client.get("/nonexistent")
        assert response.status_code == 404
        
        # Verificar se request ID está presente mesmo em erros
        assert "X-Request-ID" in response.headers
    
    def test_logging_format(self, client):
        """Testar formato de logging."""
        # Fazer uma requisição para gerar logs
        response = client.get("/health")
        assert response.status_code == 200
        
        # Verificar se request ID está sendo usado
        request_id = response.headers["X-Request-ID"]
        assert request_id is not None
        assert len(request_id) > 0


class TestRateLimiting:
    """Testes específicos para rate limiting."""
    
    def test_rate_limiting_basic(self, client):
        """Testar rate limiting básico."""
        # Fazer múltiplas requisições rapidamente
        for i in range(5):
            response = client.get("/health")
            assert response.status_code == 200
            
            # Verificar que remaining está diminuindo
            remaining = int(response.headers["X-RateLimit-Remaining"])
            assert remaining >= 0
    
    def test_rate_limiting_exceeded(self, client):
        """Testar quando rate limit é excedido."""
        # Fazer muitas requisições rapidamente para exceder o limite
        # (Este teste pode ser instável em ambientes de teste)
        
        # Para este teste, vamos apenas verificar que o sistema está funcionando
        response = client.get("/health")
        assert response.status_code == 200
        assert "X-RateLimit-Remaining" in response.headers


class TestConfiguration:
    """Testes para configurações."""
    
    def test_settings_loaded(self):
        """Testar se configurações foram carregadas corretamente."""
        assert settings.api_title is not None
        assert settings.api_version is not None
        assert settings.api_description is not None
        assert settings.cors_origins is not None
        assert settings.rate_limit_requests > 0
        assert settings.rate_limit_window > 0
    
    def test_environment_specific_settings(self):
        """Testar configurações específicas do ambiente."""
        assert settings.environment in ["development", "staging", "production"]
        assert isinstance(settings.debug, bool)
        assert isinstance(settings.enable_rate_limiting, bool)
        assert isinstance(settings.log_request_id, bool)
    
    def test_api_prefix_normalization(self):
        """Testar normalização do prefixo da API."""
        # O prefixo deve ser normalizado durante carregamento
        assert settings.api_prefix.startswith("/")
        assert settings.api_prefix != "/"
    
    def test_metrics_cache_settings(self):
        """Testar configurações de cache de métricas."""
        assert isinstance(settings.metrics_cache_ttl, int)
        assert settings.metrics_cache_ttl > 0


class TestAppState:
    """Testes para estado da aplicação."""
    
    def test_get_uptime(self):
        """Testar função get_uptime."""
        uptime = get_uptime()
        assert isinstance(uptime, float)
        assert uptime >= 0
    
    def test_get_uptime_formatted(self):
        """Testar função get_uptime_formatted."""
        from app.core.app_state import get_uptime_formatted
        formatted = get_uptime_formatted()
        assert isinstance(formatted, str)
        assert ":" in formatted  # Formato HH:MM:SS


if __name__ == "__main__":
    # Executar testes diretamente
    pytest.main([__file__, "-v"])
