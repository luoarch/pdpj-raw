"""Testes unitários para o middleware de rate limiting."""

import asyncio
import pytest
import time
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import FastAPI, Request, Response
from fastapi.testclient import TestClient
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.rate_limiting import (
    RateLimitMiddleware,
    RequestIDMiddleware,
    InMemoryRateLimitStorage,
    RedisRateLimitStorage,
    create_rate_limit_middleware,
    create_request_id_middleware
)


class TestInMemoryRateLimitStorage:
    """Testes para o storage em memória."""
    
    @pytest.fixture
    def storage(self):
        return InMemoryRateLimitStorage()
    
    @pytest.mark.asyncio
    async def test_get_client_requests_empty(self, storage):
        """Testar obter requisições de cliente inexistente."""
        requests = await storage.get_client_requests("192.168.1.1", time.time() - 60)
        assert requests == []
    
    @pytest.mark.asyncio
    async def test_add_and_get_client_requests(self, storage):
        """Testar adicionar e obter requisições do cliente."""
        client_ip = "192.168.1.1"
        current_time = time.time()
        
        # Adicionar algumas requisições
        await storage.add_client_request(client_ip, current_time - 30)
        await storage.add_client_request(client_ip, current_time - 10)
        await storage.add_client_request(client_ip, current_time)
        
        # Obter requisições dentro da janela de 60 segundos
        window_start = current_time - 60
        requests = await storage.get_client_requests(client_ip, window_start)
        
        assert len(requests) == 3
        assert current_time - 30 in requests
        assert current_time - 10 in requests
        assert current_time in requests
    
    @pytest.mark.asyncio
    async def test_get_client_requests_with_window(self, storage):
        """Testar obter requisições com janela de tempo específica."""
        client_ip = "192.168.1.1"
        current_time = time.time()
        
        # Adicionar requisições antigas e recentes
        await storage.add_client_request(client_ip, current_time - 120)  # Antiga
        await storage.add_client_request(client_ip, current_time - 30)   # Recente
        await storage.add_client_request(client_ip, current_time)        # Muito recente
        
        # Obter apenas requisições dos últimos 60 segundos
        window_start = current_time - 60
        requests = await storage.get_client_requests(client_ip, window_start)
        
        assert len(requests) == 2
        assert current_time - 30 in requests
        assert current_time in requests
        assert current_time - 120 not in requests
    
    @pytest.mark.asyncio
    async def test_cleanup_old_entries(self, storage):
        """Testar limpeza de entradas antigas."""
        current_time = time.time()
        
        # Adicionar cliente com última requisição antiga
        await storage.add_client_request("192.168.1.1", current_time - 200)
        await storage.add_client_request("192.168.1.2", current_time - 10)
        
        # Limpar entradas mais antigas que 100 segundos
        cutoff_time = current_time - 100
        removed_count = await storage.cleanup_old_entries(cutoff_time)
        
        assert removed_count == 1  # Apenas o primeiro cliente foi removido


class TestRedisRateLimitStorage:
    """Testes para o storage Redis."""
    
    @pytest.fixture
    def mock_redis(self):
        """Mock do cliente Redis."""
        redis_mock = AsyncMock()
        return redis_mock
    
    @pytest.fixture
    def redis_storage(self, mock_redis):
        return RedisRateLimitStorage(mock_redis)
    
    @pytest.mark.asyncio
    async def test_get_client_requests(self, redis_storage, mock_redis):
        """Testar obter requisições do Redis."""
        mock_redis.zrangebyscore.return_value = [
            ("req1", 1234567890.0),
            ("req2", 1234567891.0)
        ]
        
        requests = await redis_storage.get_client_requests("192.168.1.1", 1234567880.0)
        
        assert requests == [1234567890.0, 1234567891.0]
        mock_redis.zrangebyscore.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_add_client_request(self, redis_storage, mock_redis):
        """Testar adicionar requisição ao Redis."""
        await redis_storage.add_client_request("192.168.1.1", 1234567890.0)
        
        mock_redis.zadd.assert_called_once()
        mock_redis.expire.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cleanup_old_entries(self, redis_storage, mock_redis):
        """Testar limpeza de entradas antigas no Redis."""
        mock_redis.keys.return_value = ["rate_limit:192.168.1.1", "rate_limit:192.168.1.2"]
        mock_redis.zremrangebyscore.return_value = 5
        mock_redis.zcard.return_value = 0
        
        removed_count = await redis_storage.cleanup_old_entries(1234567880.0)
        
        assert removed_count == 10  # 5 de cada chave
        assert mock_redis.keys.called
        assert mock_redis.zremrangebyscore.call_count == 2


class TestRateLimitMiddleware:
    """Testes para o middleware de rate limiting."""
    
    @pytest.fixture
    def app(self):
        """Aplicação FastAPI de teste."""
        app = FastAPI()
        
        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}
        
        return app
    
    @pytest.fixture
    def mock_storage(self):
        """Mock do storage para testes."""
        storage = AsyncMock(spec=InMemoryRateLimitStorage)
        storage.get_client_requests.return_value = []
        storage.add_client_request.return_value = None
        storage.cleanup_old_entries.return_value = 0
        return storage
    
    @pytest.fixture
    def middleware(self, app, mock_storage):
        """Middleware com storage mockado."""
        middleware = RateLimitMiddleware(app, storage=mock_storage)
        middleware.rate_limit_requests = 2
        middleware.rate_limit_window = 60
        return middleware
    
    @pytest.mark.asyncio
    async def test_rate_limit_allowed(self, middleware, mock_storage):
        """Testar requisição permitida dentro do rate limit."""
        mock_storage.get_client_requests.return_value = []  # Nenhuma requisição anterior
        
        # Mock do request
        request = MagicMock(spec=Request)
        request.headers = {"X-Forwarded-For": "192.168.1.1"}
        request.method = "GET"
        request.url.path = "/test"
        request.state.request_id = "test-request-id"
        
        # Mock do call_next
        response = Response(content='{"message": "test"}', status_code=200)
        call_next = AsyncMock(return_value=response)
        
        # Executar middleware
        result = await middleware.dispatch(request, call_next)
        
        # Verificações
        assert result.status_code == 200
        mock_storage.get_client_requests.assert_called_once()
        mock_storage.add_client_request.assert_called_once()
        call_next.assert_called_once_with(request)
    
    @pytest.mark.asyncio
    async def test_rate_limit_exceeded(self, middleware, mock_storage):
        """Testar requisição bloqueada por rate limit."""
        # Simular que já atingiu o limite
        mock_storage.get_client_requests.return_value = [
            time.time() - 30,
            time.time() - 10
        ]
        
        # Mock do request
        request = MagicMock(spec=Request)
        request.headers = {"X-Forwarded-For": "192.168.1.1"}
        request.method = "GET"
        request.url.path = "/test"
        request.state.request_id = "test-request-id"
        
        call_next = AsyncMock()
        
        # Executar middleware
        result = await middleware.dispatch(request, call_next)
        
        # Verificações
        assert result.status_code == 429  # Too Many Requests
        assert "Rate limit exceeded" in result.body.decode()
        mock_storage.get_client_requests.assert_called_once()
        mock_storage.add_client_request.assert_not_called()
        call_next.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_get_client_ip_with_forwarded_for(self, middleware):
        """Testar detecção de IP com X-Forwarded-For."""
        request = MagicMock(spec=Request)
        request.headers = {"X-Forwarded-For": "203.0.113.1, 192.168.1.1"}
        
        client_ip = middleware._get_client_ip(request)
        assert client_ip == "203.0.113.1"
    
    @pytest.mark.asyncio
    async def test_get_client_ip_with_real_ip(self, middleware):
        """Testar detecção de IP com X-Real-IP."""
        request = MagicMock(spec=Request)
        request.headers = {"X-Real-IP": "203.0.113.1"}
        
        client_ip = middleware._get_client_ip(request)
        assert client_ip == "203.0.113.1"
    
    @pytest.mark.asyncio
    async def test_get_client_ip_fallback(self, middleware):
        """Testar fallback para IP direto."""
        request = MagicMock(spec=Request)
        request.headers = {}
        request.client = MagicMock()
        request.client.host = "192.168.1.100"
        
        client_ip = middleware._get_client_ip(request)
        assert client_ip == "192.168.1.100"
    
    def test_validate_ip_format(self, middleware):
        """Testar validação de formato de IP."""
        assert middleware._validate_ip_format("192.168.1.1") == True
        assert middleware._validate_ip_format("127.0.0.1") == True
        assert middleware._validate_ip_format("10.0.0.1") == True
        assert middleware._validate_ip_format("203.0.113.1") == True
        assert middleware._validate_ip_format("invalid") == False
        assert middleware._validate_ip_format("192.168.1") == False
        assert middleware._validate_ip_format("192.168.1.256") == False
    
    def test_ip_validation_cache(self, middleware):
        """Testar cache de validação de IP."""
        # Primeira validação - deve ir para cache
        result1 = middleware._is_valid_ip("192.168.1.1")
        assert result1 == True
        assert "192.168.1.1" in middleware._ip_validation_cache
        
        # Segunda validação - deve usar cache
        result2 = middleware._is_valid_ip("192.168.1.1")
        assert result2 == True
        assert result1 == result2


class TestRequestIDMiddleware:
    """Testes para o middleware de Request ID."""
    
    @pytest.fixture
    def app(self):
        app = FastAPI()
        
        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}
        
        return app
    
    @pytest.fixture
    def middleware(self, app):
        return RequestIDMiddleware(app)
    
    @pytest.mark.asyncio
    async def test_generate_request_id(self, middleware):
        """Testar geração de request ID quando não fornecido."""
        request = MagicMock(spec=Request)
        request.headers = {}
        request.state = MagicMock()
        
        response = Response(content='{"message": "test"}', status_code=200)
        call_next = AsyncMock(return_value=response)
        
        await middleware.dispatch(request, call_next)
        
        # Verificar se request_id foi gerado e adicionado ao state
        assert hasattr(request.state, 'request_id')
        assert request.state.request_id is not None
        assert len(request.state.request_id) > 0
    
    @pytest.mark.asyncio
    async def test_use_existing_request_id(self, middleware):
        """Testar uso de request ID existente."""
        existing_id = "existing-request-id"
        
        request = MagicMock(spec=Request)
        request.headers = {"X-Request-ID": existing_id}
        request.state = MagicMock()
        
        response = Response(content='{"message": "test"}', status_code=200)
        call_next = AsyncMock(return_value=response)
        
        await middleware.dispatch(request, call_next)
        
        assert request.state.request_id == existing_id


class TestFactoryFunctions:
    """Testes para as funções factory."""
    
    @pytest.fixture
    def app(self):
        return FastAPI()
    
    @patch('app.core.rate_limiting.settings')
    def test_create_rate_limit_middleware_enabled(self, mock_settings, app):
        """Testar criação de middleware com rate limiting habilitado."""
        mock_settings.enable_rate_limiting = True
        mock_settings.rate_limit_requests = 100
        mock_settings.rate_limit_window = 60
        
        middleware = create_rate_limit_middleware(app)
        
        assert isinstance(middleware, RateLimitMiddleware)
        assert middleware.rate_limit_requests == 100
        assert middleware.rate_limit_window == 60
    
    @patch('app.core.rate_limiting.settings')
    def test_create_rate_limit_middleware_disabled(self, mock_settings, app):
        """Testar criação de middleware com rate limiting desabilitado."""
        mock_settings.enable_rate_limiting = False
        
        result = create_rate_limit_middleware(app)
        
        assert result == app  # Deve retornar a app original
    
    @patch('app.core.rate_limiting.settings')
    def test_create_rate_limit_middleware_with_storage(self, mock_settings, app):
        """Testar criação de middleware com storage customizado."""
        mock_settings.enable_rate_limiting = True
        mock_settings.rate_limit_requests = 100
        mock_settings.rate_limit_window = 60
        
        custom_storage = AsyncMock()
        middleware = create_rate_limit_middleware(app, storage=custom_storage)
        
        assert isinstance(middleware, RateLimitMiddleware)
        assert middleware.storage == custom_storage
    
    @patch('app.core.rate_limiting.settings')
    def test_create_request_id_middleware_enabled(self, mock_settings, app):
        """Testar criação de middleware de request ID habilitado."""
        mock_settings.log_request_id = True
        
        middleware = create_request_id_middleware(app)
        
        assert isinstance(middleware, RequestIDMiddleware)
    
    @patch('app.core.rate_limiting.settings')
    def test_create_request_id_middleware_disabled(self, mock_settings, app):
        """Testar criação de middleware de request ID desabilitado."""
        mock_settings.log_request_id = False
        
        result = create_request_id_middleware(app)
        
        assert result == app  # Deve retornar a app original


class TestIntegration:
    """Testes de integração."""
    
    @pytest.fixture
    def app_with_middleware(self):
        """Aplicação com middleware configurado."""
        app = FastAPI()
        
        # Adicionar middleware
        app.add_middleware(RateLimitMiddleware, storage=InMemoryRateLimitStorage())
        app.add_middleware(RequestIDMiddleware)
        
        @app.get("/test")
        async def test_endpoint():
            return {"message": "success"}
        
        @app.get("/slow")
        async def slow_endpoint():
            await asyncio.sleep(0.1)
            return {"message": "slow"}
        
        return app
    
    def test_rate_limiting_integration(self, app_with_middleware):
        """Teste de integração do rate limiting."""
        client = TestClient(app_with_middleware)
        
        # Configurar rate limit baixo para teste
        middleware = app_with_middleware.user_middleware[0].cls
        middleware.rate_limit_requests = 2
        middleware.rate_limit_window = 60
        
        # Fazer requisições dentro do limite
        response1 = client.get("/test")
        assert response1.status_code == 200
        assert "X-RateLimit-Remaining" in response1.headers
        assert "X-Request-ID" in response1.headers
        
        response2 = client.get("/test")
        assert response2.status_code == 200
        
        # Terceira requisição deve ser bloqueada
        response3 = client.get("/test")
        assert response3.status_code == 429
        assert "Rate limit exceeded" in response3.json()["error"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
