"""Exemplos de uso do middleware de rate limiting."""

import asyncio
import redis.asyncio as redis
from fastapi import FastAPI

from app.core.rate_limiting import (
    RateLimitMiddleware,
    InMemoryRateLimitStorage,
    RedisRateLimitStorage,
    create_rate_limit_middleware,
    create_request_id_middleware
)


# Exemplo 1: Configuração básica para desenvolvimento
def setup_development_app():
    """Configurar aplicação para desenvolvimento com storage em memória."""
    app = FastAPI()
    
    # Adicionar middlewares
    app.add_middleware(
        RateLimitMiddleware,
        storage=InMemoryRateLimitStorage()
    )
    app.add_middleware(RequestIDMiddleware)
    
    @app.get("/api/data")
    async def get_data():
        return {"data": "example"}
    
    return app


# Exemplo 2: Configuração para produção com Redis
async def setup_production_app():
    """Configurar aplicação para produção com Redis."""
    app = FastAPI()
    
    # Configurar Redis
    redis_client = redis.Redis(
        host="localhost",
        port=6379,
        db=0,
        decode_responses=False  # Manter bytes para sorted sets
    )
    
    # Criar storage Redis
    redis_storage = RedisRateLimitStorage(
        redis_client=redis_client,
        key_prefix="api_rate_limit"
    )
    
    # Adicionar middlewares
    app.add_middleware(
        RateLimitMiddleware,
        storage=redis_storage
    )
    app.add_middleware(RequestIDMiddleware)
    
    @app.get("/api/data")
    async def get_data():
        return {"data": "example"}
    
    @app.get("/api/stats")
    async def get_stats():
        """Endpoint para obter estatísticas do rate limiting."""
        stats = await redis_storage.get_stats()
        return {
            "rate_limiting_stats": stats,
            "total_clients": stats.get("total_clients", 0),
            "total_requests": stats.get("total_requests", 0)
        }
    
    return app


# Exemplo 3: Usando factory functions
def setup_with_factory_functions():
    """Configurar aplicação usando as funções factory."""
    app = FastAPI()
    
    # Para desenvolvimento - usa InMemoryRateLimitStorage automaticamente
    app = create_rate_limit_middleware(app)
    app = create_request_id_middleware(app)
    
    @app.get("/api/data")
    async def get_data():
        return {"data": "example"}
    
    return app


# Exemplo 4: Configuração customizada para produção
async def setup_custom_production():
    """Configuração customizada para produção."""
    app = FastAPI()
    
    # Redis com configurações customizadas
    redis_client = redis.Redis(
        host="redis-cluster.example.com",
        port=6379,
        db=1,
        password="secure_password",
        ssl=True,
        decode_responses=False
    )
    
    # Storage Redis customizado
    redis_storage = RedisRateLimitStorage(
        redis_client=redis_client,
        key_prefix="prod_api_rate_limit"
    )
    
    # Middleware customizado
    middleware = RateLimitMiddleware(app, storage=redis_storage)
    middleware.rate_limit_requests = 1000  # 1000 req/hora
    middleware.rate_limit_window = 3600    # 1 hora
    
    app.add_middleware(lambda app: middleware)
    app.add_middleware(RequestIDMiddleware)
    
    @app.get("/api/data")
    async def get_data():
        return {"data": "example"}
    
    @app.get("/api/admin/stats")
    async def admin_stats():
        """Endpoint administrativo para estatísticas."""
        stats = await redis_storage.get_stats()
        return {
            "rate_limiting": {
                "total_clients": stats.get("total_clients", 0),
                "total_requests": stats.get("total_requests", 0),
                "rate_limit_per_hour": 1000,
                "current_window_seconds": 3600
            }
        }
    
    return app


# Exemplo 5: Configuração para diferentes ambientes
def create_app_for_environment(environment: str):
    """Criar aplicação baseada no ambiente."""
    app = FastAPI()
    
    if environment == "development":
        # Desenvolvimento: storage em memória
        storage = InMemoryRateLimitStorage()
        app.add_middleware(RateLimitMiddleware, storage=storage)
        
    elif environment == "staging":
        # Staging: Redis local
        async def setup_staging_storage():
            redis_client = redis.Redis(host="localhost", port=6379, db=0)
            return RedisRateLimitStorage(redis_client, "staging_rate_limit")
        
        # Para staging, você precisaria configurar Redis primeiro
        # storage = await setup_staging_storage()
        storage = InMemoryRateLimitStorage()  # Fallback
        
    elif environment == "production":
        # Produção: Redis cluster
        async def setup_production_storage():
            redis_client = redis.Redis(
                host="redis-cluster.prod.com",
                port=6379,
                password="prod_password",
                ssl=True
            )
            return RedisRateLimitStorage(redis_client, "prod_rate_limit")
        
        # Para produção, você precisaria configurar Redis primeiro
        # storage = await setup_production_storage()
        storage = InMemoryRateLimitStorage()  # Fallback
    
    else:
        raise ValueError(f"Ambiente não suportado: {environment}")
    
    app.add_middleware(RateLimitMiddleware, storage=storage)
    app.add_middleware(RequestIDMiddleware)
    
    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "environment": environment}
    
    return app


# Exemplo 6: Middleware com configurações diferentes por endpoint
def setup_endpoint_specific_limits():
    """Configurar rate limiting específico por endpoint."""
    app = FastAPI()
    
    # Storage compartilhado
    storage = InMemoryRateLimitStorage()
    
    # Middleware padrão para todos os endpoints
    app.add_middleware(RateLimitMiddleware, storage=storage)
    app.add_middleware(RequestIDMiddleware)
    
    @app.get("/api/public")
    async def public_endpoint():
        """Endpoint público com rate limiting padrão."""
        return {"message": "public data"}
    
    @app.get("/api/premium")
    async def premium_endpoint():
        """Endpoint premium - você pode implementar lógica customizada aqui."""
        return {"message": "premium data"}
    
    @app.get("/api/admin")
    async def admin_endpoint():
        """Endpoint administrativo - sem rate limiting ou limite alto."""
        return {"message": "admin data"}
    
    return app


# Exemplo de uso
if __name__ == "__main__":
    # Para desenvolvimento
    dev_app = setup_development_app()
    print("App de desenvolvimento configurado")
    
    # Para produção (requer Redis)
    # prod_app = asyncio.run(setup_production_app())
    # print("App de produção configurado")
    
    # Usando factory functions
    factory_app = setup_with_factory_functions()
    print("App com factory functions configurado")
    
    # Para ambiente específico
    staging_app = create_app_for_environment("staging")
    print("App de staging configurado")
