# Guia de Configuração do Rate Limiting

## Configurações Disponíveis

### Configurações Básicas

```python
# app/core/config.py
class Settings:
    # Rate Limiting
    enable_rate_limiting: bool = True
    rate_limit_requests: int = 1000  # Requisições por janela
    rate_limit_window: int = 3600    # Janela em segundos (1 hora)
    
    # Request ID
    log_request_id: bool = True
    
    # Redis (para produção)
    redis_url: str = "redis://localhost:6379/0"
    
    # Celery (para tasks periódicas)
    enable_celery: bool = False
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"
```

### Configurações por Ambiente

#### Desenvolvimento
```python
# Desenvolvimento - storage em memória
enable_rate_limiting = True
rate_limit_requests = 100      # 100 req/hora
rate_limit_window = 3600       # 1 hora
log_request_id = True
enable_celery = False          # Não usar Celery em dev
```

#### Staging
```python
# Staging - Redis local
enable_rate_limiting = True
rate_limit_requests = 500      # 500 req/hora
rate_limit_window = 3600       # 1 hora
log_request_id = True
redis_url = "redis://localhost:6379/0"
enable_celery = True           # Usar Celery para limpeza
```

#### Produção
```python
# Produção - Redis cluster
enable_rate_limiting = True
rate_limit_requests = 1000     # 1000 req/hora
rate_limit_window = 3600       # 1 hora
log_request_id = True
redis_url = "redis://redis-cluster.prod.com:6379/0"
enable_celery = True           # Tasks periódicas obrigatórias
```

## Switching de Backends

### 1. Desenvolvimento → Staging

```python
# Antes (Desenvolvimento)
from app.core.rate_limiting import create_rate_limit_middleware

app = create_rate_limit_middleware(app)  # Usa InMemory automaticamente

# Depois (Staging)
import redis.asyncio as redis
from app.core.rate_limiting import create_rate_limit_middleware, RedisRateLimitStorage

# Configurar Redis
redis_client = redis.Redis(host="localhost", port=6379, db=0)
redis_storage = RedisRateLimitStorage(redis_client, "staging_rate_limit")

# Usar Redis storage
app = create_rate_limit_middleware(app, storage=redis_storage)
```

### 2. Staging → Produção

```python
# Antes (Staging)
redis_client = redis.Redis(host="localhost", port=6379, db=0)

# Depois (Produção)
redis_client = redis.Redis(
    host="redis-cluster.prod.com",
    port=6379,
    db=0,
    password="secure_password",
    ssl=True,
    max_connections=20,
    socket_keepalive=True,
    socket_keepalive_options={},
    health_check_interval=30
)

redis_storage = RedisRateLimitStorage(redis_client, "prod_rate_limit")
app = create_rate_limit_middleware(app, storage=redis_storage)
```

### 3. Configuração Dinâmica por Ambiente

```python
import os
from app.core.rate_limiting import (
    InMemoryRateLimitStorage, 
    RedisRateLimitStorage,
    create_rate_limit_middleware
)

def setup_rate_limiting_for_environment(app, environment: str):
    """Configurar rate limiting baseado no ambiente."""
    
    if environment == "development":
        # Desenvolvimento: storage em memória
        storage = InMemoryRateLimitStorage()
        
    elif environment == "staging":
        # Staging: Redis local
        redis_client = redis.Redis(host="localhost", port=6379, db=0)
        storage = RedisRateLimitStorage(redis_client, "staging_rate_limit")
        
    elif environment == "production":
        # Produção: Redis cluster
        redis_client = redis.Redis(
            host=os.getenv("REDIS_HOST", "redis-cluster.prod.com"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            password=os.getenv("REDIS_PASSWORD"),
            ssl=os.getenv("REDIS_SSL", "true").lower() == "true"
        )
        storage = RedisRateLimitStorage(redis_client, "prod_rate_limit")
        
    else:
        raise ValueError(f"Ambiente não suportado: {environment}")
    
    return create_rate_limit_middleware(app, storage=storage)

# Uso
app = setup_rate_limiting_for_environment(app, os.getenv("ENVIRONMENT", "development"))
```

## Configurações Avançadas

### Rate Limiting por Endpoint

```python
from app.core.rate_limiting import RateLimitMiddleware, InMemoryRateLimitStorage

# Middleware padrão
default_storage = InMemoryRateLimitStorage()
default_middleware = RateLimitMiddleware(app, storage=default_storage)

# Middleware para endpoints específicos (exemplo conceitual)
class EndpointSpecificRateLimit:
    def __init__(self, app):
        self.app = app
        self.storage = InMemoryRateLimitStorage()
        
    async def __call__(self, request, call_next):
        # Lógica customizada baseada no endpoint
        if request.url.path.startswith("/api/premium/"):
            # Rate limit mais alto para endpoints premium
            middleware = RateLimitMiddleware(self.app, storage=self.storage)
            middleware.rate_limit_requests = 2000
            middleware.rate_limit_window = 3600
        elif request.url.path.startswith("/api/admin/"):
            # Sem rate limit para admin
            return await call_next(request)
        else:
            # Rate limit padrão
            middleware = RateLimitMiddleware(self.app, storage=self.storage)
            
        return await middleware.dispatch(request, call_next)
```

### Configurações de Cache

```python
# Configurar cache de validação de IP
middleware = RateLimitMiddleware(app, storage=storage)

# Ajustar configurações de cache
middleware._cache_max_size = 20000      # Máximo de IPs em cache
middleware._cache_ttl = 7200           # TTL do cache (2 horas)
```

### Configurações de Limpeza

```python
# Configurar limpeza otimizada
middleware = RateLimitMiddleware(app, storage=storage)

# Ajustar intervalos de limpeza
middleware.cleanup_interval = 600       # Limpeza a cada 10 minutos
middleware.max_clients_before_cleanup = 5000  # Limiar para limpeza forçada
```

## Tasks Periódicas (Celery)

### Configuração do Celery

```python
# app/core/config.py
class Settings:
    enable_celery: bool = True
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"
```

### Inicialização das Tasks

```python
# app/main.py
from app.tasks.rate_limiting_tasks import start_periodic_tasks

# Iniciar tasks periódicas
start_periodic_tasks()
```

### Tasks Disponíveis

1. **Limpeza Automática**: A cada 30 minutos
2. **Estatísticas**: A cada 5 minutos  
3. **Health Check**: A cada 2 minutos

### Executar Tasks Manualmente

```python
from app.tasks.rate_limiting_tasks import (
    cleanup_redis_rate_limiting_task,
    get_rate_limiting_stats_task,
    health_check_redis_task
)

# Limpeza manual
result = cleanup_redis_rate_limiting_task.delay(
    redis_url="redis://localhost:6379/0",
    key_prefix="rate_limit"
)

# Estatísticas
stats = get_rate_limiting_stats_task.delay(
    redis_url="redis://localhost:6379/0",
    key_prefix="rate_limit"
)

# Health check
health = health_check_redis_task.delay(
    redis_url="redis://localhost:6379/0"
)
```

## Monitoramento e Métricas

### Endpoint de Estatísticas

```python
@app.get("/api/admin/rate-limit-stats")
async def get_rate_limit_stats():
    """Obter estatísticas do rate limiting."""
    if isinstance(middleware.storage, RedisRateLimitStorage):
        stats = await middleware.storage.get_stats()
        return {
            "storage_type": "Redis",
            "total_clients": stats.get("total_clients", 0),
            "total_requests": stats.get("total_requests", 0),
            "rate_limit_config": {
                "requests_per_window": settings.rate_limit_requests,
                "window_seconds": settings.rate_limit_window
            }
        }
    else:
        return {
            "storage_type": "InMemory",
            "message": "Estatísticas não disponíveis para storage em memória"
        }
```

### Logs Estruturados

```python
# Configurar logs estruturados
import structlog

logger = structlog.get_logger()

# Logs incluem automaticamente:
# - request_id
# - client_ip
# - rate_limit_status
# - response_time
# - error_details
```

## Troubleshooting

### Problemas Comuns

1. **Redis Connection Error**
   ```bash
   # Verificar conexão Redis
   redis-cli ping
   
   # Verificar logs
   tail -f logs/app.log | grep "Redis"
   ```

2. **Rate Limit Muito Restritivo**
   ```python
   # Ajustar configurações
   settings.rate_limit_requests = 2000  # Aumentar limite
   settings.rate_limit_window = 3600    # Manter janela
   ```

3. **Celery Tasks Não Executando**
   ```bash
   # Verificar Celery worker
   celery -A app.tasks.rate_limiting_tasks worker --loglevel=info
   
   # Verificar Celery beat
   celery -A app.tasks.rate_limiting_tasks beat --loglevel=info
   ```

### Comandos Úteis

```bash
# Verificar estatísticas Redis
redis-cli --eval scripts/rate_limit_stats.lua

# Limpeza manual Redis
redis-cli --eval scripts/cleanup_rate_limit.lua

# Monitorar logs em tempo real
tail -f logs/app.log | grep -E "(rate_limit|Rate limit)"

# Teste de carga
python scripts/load_test_rate_limiting.py
```

## Migração Gradual

### Estratégia de Migração

1. **Fase 1**: Implementar com InMemory em produção
2. **Fase 2**: Migrar para Redis com fallback
3. **Fase 3**: Ativar tasks periódicas
4. **Fase 4**: Otimizar configurações baseado em métricas

### Fallback Strategy

```python
def create_robust_rate_limiting(app):
    """Criar rate limiting com fallback automático."""
    try:
        # Tentar Redis primeiro
        redis_client = redis.Redis(host="redis-cluster.prod.com")
        storage = RedisRateLimitStorage(redis_client, "prod_rate_limit")
        logger.info("Usando Redis storage para rate limiting")
    except Exception as e:
        # Fallback para InMemory
        storage = InMemoryRateLimitStorage()
        logger.warning(f"Redis indisponível, usando InMemory storage: {str(e)}")
    
    return create_rate_limit_middleware(app, storage=storage)
```

Esta configuração garante que o rate limiting sempre funcione, mesmo em caso de falhas no Redis.
