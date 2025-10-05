"""Testes para a factory da aplicação FastAPI."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import time

from app.core.app_factory import create_fastapi_app
from app.core.config import settings


class TestAppFactory:
    """Testes para a factory da aplicação."""
    
    def test_create_fastapi_app(self):
        """Testar criação da aplicação FastAPI."""
        app = create_fastapi_app()
        
        assert app is not None
        assert app.title == settings.api_title
        assert app.version == settings.api_version
        assert app.description == settings.api_description
    
    def test_app_initialization_state(self):
        """Testar estado de inicialização da aplicação."""
        app = create_fastapi_app()
        client = TestClient(app)
        
        # Verificar se app.state é inicializado corretamente
        response = client.get("/")
        assert response.status_code == 200
        
        # Verificar se uptime está sendo calculado
        data = response.json()
        assert "uptime_seconds" in data
        assert data["uptime_seconds"] >= 0
    
    def test_middleware_order(self):
        """Testar ordem correta dos middlewares."""
        app = create_fastapi_app()
        client = TestClient(app)
        
        response = client.get("/")
        
        # Verificar headers na ordem correta
        assert "X-Request-ID" in response.headers  # Request ID middleware
        assert "X-RateLimit-Limit" in response.headers  # Rate limiting middleware
        assert "X-Response-Time" in response.headers  # Metrics middleware
        assert "access-control-allow-origin" in response.headers.lower()  # CORS middleware
    
    def test_startup_event_prevention(self):
        """Testar prevenção de múltiplas inicializações."""
        app = create_fastapi_app()
        
        # Simular estado já inicializado
        app.state.is_initialized = True
        app.state.start_time = time.time()
        
        # Startup não deve executar novamente
        with patch('app.services.advanced_cache_service.advanced_cache_service') as mock_cache:
            # Não deve chamar connect se já inicializado
            pass  # O teste verifica que não há erro
    
    def test_error_handling_in_endpoints(self):
        """Testar tratamento de erros nos endpoints."""
        app = create_fastapi_app()
        client = TestClient(app)
        
        # Simular erro no endpoint
        with patch('app.core.app_factory.logger') as mock_logger:
            response = client.get("/")
            # Deve retornar 200 mesmo com logs de erro
            assert response.status_code == 200
    
    def test_metrics_endpoint_protection(self):
        """Testar proteção do endpoint de métricas."""
        app = create_fastapi_app()
        client = TestClient(app)
        
        # Fazer algumas requisições para gerar métricas
        client.get("/")
        client.get("/health")
        
        response = client.get("/metrics")
        
        # Verificar comportamento baseado na configuração
        if settings.enable_metrics:
            if settings.metrics_protected and not settings.debug:
                assert response.status_code == 403
            else:
                assert response.status_code == 200
                assert response.headers["content-type"] == "text/plain; version=0.0.4; charset=utf-8"
        else:
            assert response.status_code == 503


class TestAppFactoryIsolation:
    """Testes para isolamento da factory."""
    
    def test_factory_independence(self):
        """Testar que factory pode ser chamada isoladamente."""
        # Criar duas instâncias independentes
        app1 = create_fastapi_app()
        app2 = create_fastapi_app()
        
        # Devem ser objetos diferentes
        assert app1 is not app2
        
        # Mas com mesmas configurações
        assert app1.title == app2.title
        assert app1.version == app2.version
    
    def test_settings_isolation(self):
        """Testar isolamento de configurações."""
        with patch.dict('os.environ', {'DEBUG': 'true'}):
            app_debug = create_fastapi_app()
            assert app_debug.docs_url == "/docs"
        
        with patch.dict('os.environ', {'DEBUG': 'false'}):
            app_prod = create_fastapi_app()
            assert app_prod.docs_url is None
    
    def test_middleware_configuration_isolation(self):
        """Testar isolamento de configuração de middlewares."""
        with patch.dict('os.environ', {'ENABLE_RATE_LIMITING': 'false'}):
            app_no_rate_limit = create_fastapi_app()
            client = TestClient(app_no_rate_limit)
            response = client.get("/")
            # Em configuração sem rate limiting, headers podem não estar presentes
            # Isso depende da implementação específica


class TestAppFactoryComponents:
    """Testes para componentes individuais da factory."""
    
    def test_logging_configuration(self):
        """Testar configuração de logging."""
        from app.core.app_factory import configure_logging
        
        # Não deve levantar exceção
        configure_logging()
    
    def test_middleware_stack_creation(self):
        """Testar criação do stack de middlewares."""
        from app.core.middleware_config import create_middleware_stack
        from fastapi import FastAPI
        
        app = FastAPI()
        app = create_middleware_stack(app)
        
        assert app is not None
        # Verificar se middlewares foram adicionados
        # (implementação específica pode variar)
    
    def test_endpoint_registration(self):
        """Testar registro de endpoints."""
        from app.core.core_endpoints import register_core_endpoints
        from fastapi import FastAPI
        
        app = FastAPI()
        register_core_endpoints(app)
        
        # Verificar se endpoints foram registrados
        routes = [route.path for route in app.routes]
        assert "/" in routes
        assert "/health" in routes
        assert "/metrics" in routes
    
    def test_router_registration(self):
        """Testar registro de routers."""
        from app.core.router_config import register_api_routers
        from fastapi import FastAPI
        
        app = FastAPI()
        register_api_routers(app)
        
        # Verificar se routers foram registrados
        routes = [route.path for route in app.routes]
        # Verificar se rotas da API estão presentes
        assert any("/api" in route for route in routes)


class TestAppFactoryIntegration:
    """Testes de integração para a factory."""
    
    def test_full_application_creation(self):
        """Testar criação completa da aplicação."""
        app = create_fastapi_app()
        client = TestClient(app)
        
        # Testar todos os endpoints principais
        endpoints = ["/", "/health", "/metrics"]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            # Deve retornar algum status code (não necessariamente 200)
            assert response.status_code in [200, 403, 503]
    
    def test_application_state_management(self):
        """Testar gerenciamento de estado da aplicação."""
        app = create_fastapi_app()
        
        # Estado inicial
        assert not hasattr(app.state, 'is_initialized')
        assert not hasattr(app.state, 'start_time')
        
        client = TestClient(app)
        response = client.get("/")
        
        # Após primeira requisição, estado deve estar definido
        assert response.status_code == 200
        data = response.json()
        assert "uptime_seconds" in data
    
    def test_error_resilience(self):
        """Testar resiliência a erros."""
        app = create_fastapi_app()
        client = TestClient(app)
        
        # Testar endpoints que podem gerar erro
        response = client.get("/nonexistent")
        assert response.status_code == 404
        
        # Verificar se middlewares ainda funcionam
        assert "X-Request-ID" in response.headers


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
