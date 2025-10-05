#!/bin/bash

# Script para executar FastAPI em produção com múltiplos workers
# Otimizado para alta performance e throughput

set -e

echo "🚀 Iniciando PDPJ API em modo produção..."

# Configurações de performance
WORKERS=${UVICORN_WORKERS:-4}
HOST=${HOST:-0.0.0.0}
PORT=${PORT:-8000}
LOG_LEVEL=${LOG_LEVEL:-info}

# Configurações de recursos
WORKER_CLASS="uvicorn.workers.UvicornWorker"
MAX_REQUESTS=1000
MAX_REQUESTS_JITTER=50
TIMEOUT=120
KEEPALIVE=5
GRACEFUL_TIMEOUT=30

echo "📊 Configurações de Performance:"
echo "   Workers: $WORKERS"
echo "   Host: $HOST"
echo "   Port: $PORT"
echo "   Log Level: $LOG_LEVEL"
echo "   Max Requests: $MAX_REQUESTS"
echo "   Timeout: ${TIMEOUT}s"

# Verificar se o banco está disponível
echo "🔍 Verificando conectividade com o banco..."
python -c "
import asyncio
import sys
from app.core.database import AsyncSessionLocal
from sqlalchemy import text

async def check_db():
    try:
        async with AsyncSessionLocal() as db:
            await db.execute(text('SELECT 1'))
        print('✅ Banco de dados conectado com sucesso')
    except Exception as e:
        print(f'❌ Erro ao conectar com o banco: {e}')
        sys.exit(1)

asyncio.run(check_db())
"

# Verificar Redis
echo "🔍 Verificando conectividade com Redis..."
python -c "
import asyncio
import sys
from app.core.cache import cache_service

async def check_redis():
    try:
        await cache_service.connect()
        await cache_service.set('health_check', 'ok', ttl=10)
        result = await cache_service.get('health_check')
        if result == 'ok':
            print('✅ Redis conectado com sucesso')
        else:
            raise Exception('Redis não retornou valor esperado')
    except Exception as e:
        print(f'❌ Erro ao conectar com Redis: {e}')
        sys.exit(1)
    finally:
        await cache_service.disconnect()

asyncio.run(check_redis())
"

echo "🎯 Iniciando servidor com Gunicorn + Uvicorn Workers..."

# Executar com Gunicorn para múltiplos workers
exec gunicorn \
    --worker-class $WORKER_CLASS \
    --workers $WORKERS \
    --bind $HOST:$PORT \
    --max-requests $MAX_REQUESTS \
    --max-requests-jitter $MAX_REQUESTS_JITTER \
    --timeout $TIMEOUT \
    --keepalive $KEEPALIVE \
    --graceful-timeout $GRACEFUL_TIMEOUT \
    --access-logfile - \
    --error-logfile - \
    --log-level $LOG_LEVEL \
    --worker-connections 1000 \
    --worker-tmp-dir /dev/shm \
    --preload \
    app.main:app
