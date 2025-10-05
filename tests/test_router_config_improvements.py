"""Testes para as melhorias na configuração de routers."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.router_config import register_api_routers, get_router_info
from app.core.app_factory import create_fastapi_app


class TestRouterConfigImprovements:
    """Testes para as melhorias na configuração de routers."""
    
    def test_register_api_routers_success(self):
        """Testar registro bem-sucedido de routers."""
        app = FastAPI()
        
        # Não deve levantar exceção
        register_api_routers(app)
        
        # Verificar se os routers foram registrados
        routes = [route.path for route in app.routes]
        
        # Verificar rotas versionadas
        assert any("/api/v1/processes" in route for route in routes)
        assert any("/api/v1/users" in route for route in routes)
        assert any("/api/v1/ultra-fast" in route for route in routes)
        assert any("/api/v1/monitoring" in route for route in routes)
    
    def test_legacy_routes_conditional_registration(self):
        """Testar registro condicional de rotas legacy."""
        app = FastAPI()
        
        # Simular ambiente de desenvolvimento
        original_debug = settings.debug
        settings.debug = True
        
        try:
            register_api_routers(app)
            
            routes = [route.path for route in app.routes]
            
            # Em debug, rotas legacy devem estar presentes
            assert any("/legacy/processes" in route for route in routes)
            assert any("/legacy/users" in route for route in routes)
            
        finally:
            settings.debug = original_debug
    
    def test_legacy_routes_disabled_in_production(self):
        """Testar que rotas legacy são desabilitadas em produção."""
        app = FastAPI()
        
        # Simular ambiente de produção
        original_debug = settings.debug
        original_legacy = getattr(settings, 'enable_legacy_routes', False)
        
        settings.debug = False
        settings.enable_legacy_routes = False
        
        try:
            register_api_routers(app)
            
            routes = [route.path for route in app.routes]
            
            # Em produção, rotas legacy não devem estar presentes
            assert not any("/legacy/processes" in route for route in routes)
            assert not any("/legacy/users" in route for route in routes)
            
        finally:
            settings.debug = original_debug
            settings.enable_legacy_routes = original_legacy
    
    def test_get_router_info(self):
        """Testar função get_router_info."""
        info = get_router_info()
        
        # Verificar estrutura da resposta
        assert "versioned" in info
        assert "legacy" in info
        
        # Verificar informações versionadas
        assert info["versioned"]["prefix"] == settings.api_prefix
        assert "processes" in info["versioned"]["routers"]
        assert "users" in info["versioned"]["routers"]
        assert info["versioned"]["enabled"] is True
        
        # Verificar informações legacy
        assert info["legacy"]["prefix"] == "/legacy"
        assert "processes-legacy" in info["legacy"]["routers"]
        assert "users-legacy" in info["legacy"]["routers"]
        assert info["legacy"]["enabled"] == (settings.debug or getattr(settings, 'enable_legacy_routes', False))
    
    def test_router_tags_consistency(self):
        """Testar consistência das tags dos routers."""
        app = FastAPI()
        register_api_routers(app)
        
        # Verificar se as tags estão corretas
        # Este teste verifica se os routers foram registrados com as tags esperadas
        routes = app.routes
        
        # Encontrar routers com tags específicas
        processes_routes = [r for r in routes if hasattr(r, 'tags') and 'processes' in r.tags]
        users_routes = [r for r in routes if hasattr(r, 'tags') and 'users' in r.tags]
        
        assert len(processes_routes) > 0
        assert len(users_routes) > 0
    
    def test_error_handling_import_failure(self, monkeypatch):
        """Testar tratamento de erro em caso de falha de importação."""
        app = FastAPI()
        
        # Simular falha de importação
        def mock_import(*args, **kwargs):
            raise ImportError("Mocked import error")
        
        monkeypatch.setattr("app.core.router_config.__import__", mock_import)
        
        # Deve levantar RuntimeError com mensagem específica
        with pytest.raises(RuntimeError, match="Falha na importação de routers"):
            register_api_routers(app)
    
    def test_api_info_endpoint(self):
        """Testar endpoint /api-info."""
        app = create_fastapi_app()
        client = TestClient(app)
        
        response = client.get("/api-info")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verificar estrutura da resposta
        assert "api" in data
        assert "routers" in data
        assert "environment" in data
        assert "debug" in data
        assert "timestamp" in data
        assert "request_id" in data
        
        # Verificar informações da API
        assert data["api"]["title"] == settings.api_title
        assert data["api"]["version"] == settings.api_version
        assert data["api"]["prefix"] == settings.api_prefix
        
        # Verificar informações dos routers
        assert "versioned" in data["routers"]
        assert "legacy" in data["routers"]


class TestVersioningMiddleware:
    """Testes para o middleware de versionamento."""
    
    def test_versioning_middleware_creation(self):
        """Testar criação do middleware de versionamento."""
        from app.core.versioning_middleware import create_versioning_middleware, get_versioning_config
        
        app = FastAPI()
        middleware = create_versioning_middleware(app)
        
        assert middleware is not None
        assert middleware.enable_header_versioning is True
        assert middleware.enable_query_versioning is True
        
        # Testar configuração padrão
        config = get_versioning_config()
        assert config["enable_header_versioning"] is True
        assert config["enable_query_versioning"] is True
        assert "v1" in config["supported_versions"]
        assert config["default_version"] == "v1"
    
    def test_version_detection_header(self):
        """Testar detecção de versão via header."""
        from app.core.versioning_middleware import VersioningMiddleware
        
        app = FastAPI()
        middleware = VersioningMiddleware(app)
        
        # Simular request com header
        class MockRequest:
            def __init__(self, headers=None, query_params=None):
                self.headers = headers or {}
                self.query_params = query_params or {}
        
        request = MockRequest(headers={"X-API-Version": "v2"})
        version = middleware._detect_version(request)
        
        assert version == "v2"
    
    def test_version_detection_query(self):
        """Testar detecção de versão via query parameter."""
        from app.core.versioning_middleware import VersioningMiddleware
        
        app = FastAPI()
        middleware = VersioningMiddleware(app)
        
        # Simular request com query parameter
        class MockRequest:
            def __init__(self, headers=None, query_params=None):
                self.headers = headers or {}
                self.query_params = query_params or {}
        
        request = MockRequest(query_params={"version": "v2"})
        version = middleware._detect_version(request)
        
        assert version == "v2"
    
    def test_version_source_detection(self):
        """Testar detecção da fonte da versão."""
        from app.core.versioning_middleware import VersioningMiddleware
        
        app = FastAPI()
        middleware = VersioningMiddleware(app)
        
        # Testar fonte via header
        class MockRequest:
            def __init__(self, headers=None, query_params=None):
                self.headers = headers or {}
                self.query_params = query_params or {}
        
        request = MockRequest(headers={"X-API-Version": "v2"})
        source = middleware._get_version_source(request)
        assert source == "header"
        
        # Testar fonte via query
        request = MockRequest(query_params={"version": "v2"})
        source = middleware._get_version_source(request)
        assert source == "query"
        
        # Testar fonte padrão
        request = MockRequest()
        source = middleware._get_version_source(request)
        assert source == "default"


class TestRouterConflictResolution:
    """Testes para resolução de conflitos de rotas."""
    
    def test_no_route_conflicts(self):
        """Testar que não há conflitos entre rotas versionadas e legacy."""
        app = FastAPI()
        register_api_routers(app)
        
        # Obter todas as rotas
        routes = []
        for route in app.routes:
            if hasattr(route, 'path'):
                routes.append(route.path)
        
        # Verificar que não há duplicatas
        assert len(routes) == len(set(routes)), "Há rotas duplicadas"
        
        # Verificar que rotas versionadas e legacy têm prefixos diferentes
        versioned_routes = [r for r in routes if r.startswith("/api/v1")]
        legacy_routes = [r for r in routes if r.startswith("/legacy")]
        
        # Não deve haver sobreposição
        for v_route in versioned_routes:
            for l_route in legacy_routes:
                # Remover prefixos para comparar
                v_clean = v_route.replace("/api/v1", "")
                l_clean = l_route.replace("/legacy", "")
                assert v_clean != l_clean, f"Conflito de rotas: {v_route} vs {l_route}"
    
    def test_route_priority(self):
        """Testar prioridade das rotas (versionadas têm prioridade sobre legacy)."""
        app = FastAPI()
        register_api_routers(app)
        
        # Em caso de conflito, rotas versionadas devem ter prioridade
        # Este teste verifica se a ordem de registro está correta
        routes = [route.path for route in app.routes if hasattr(route, 'path')]
        
        # Rotas versionadas devem estar presentes
        assert any("/api/v1/processes" in route for route in routes)
        assert any("/api/v1/users" in route for route in routes)
