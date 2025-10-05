#!/bin/bash

# Script para executar Celery workers em produção com alta performance
# Otimizado para 4 réplicas de workers com diferentes especializações

set -e

echo "🚀 Iniciando Celery workers em modo produção..."

# Configurações de workers
WORKERS=${CELERY_WORKERS:-4}
CONCURRENCY=${CELERY_CONCURRENCY:-4}
LOG_LEVEL=${CELERY_LOG_LEVEL:-info}

echo "📊 Configurações de Workers:"
echo "   Workers: $WORKERS"
echo "   Concorrência por worker: $CONCURRENCY"
echo "   Log Level: $LOG_LEVEL"

# Verificar se o Redis está disponível
echo "🔍 Verificando conectividade com Redis..."
python -c "
import asyncio
import sys
from app.services.advanced_cache_service import advanced_cache_service

async def check_redis():
    try:
        await advanced_cache_service.connect()
        await advanced_cache_service.set('health_check', 'ok', ttl=10)
        result = await advanced_cache_service.get('health_check')
        if result == 'ok':
            print('✅ Redis conectado com sucesso')
        else:
            raise Exception('Redis não retornou valor esperado')
    except Exception as e:
        print(f'❌ Erro ao conectar com Redis: {e}')
        sys.exit(1)
    finally:
        await advanced_cache_service.disconnect()

asyncio.run(check_redis())
"

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

echo "🎯 Iniciando Celery workers..."

# Worker 1: Processos (alta prioridade)
echo "🔄 Iniciando Worker 1: Processos..."
celery -A app.tasks.celery_app worker \
    --loglevel=$LOG_LEVEL \
    --concurrency=$CONCURRENCY \
    --queues=processes,default \
    --hostname=worker-processes@%h \
    --prefetch-multiplier=1 \
    --max-tasks-per-child=500 \
    --max-memory-per-child=200000 \
    --without-gossip \
    --without-mingle \
    --without-heartbeat &

# Worker 2: Documentos
echo "🔄 Iniciando Worker 2: Documentos..."
celery -A app.tasks.celery_app worker \
    --loglevel=$LOG_LEVEL \
    --concurrency=$CONCURRENCY \
    --queues=documents,default \
    --hostname=worker-documents@%h \
    --prefetch-multiplier=1 \
    --max-tasks-per-child=500 \
    --max-memory-per-child=200000 \
    --without-gossip \
    --without-mingle \
    --without-heartbeat &

# Worker 3: Ultra Fast (tasks de alta performance)
echo "🔄 Iniciando Worker 3: Ultra Fast..."
celery -A app.tasks.celery_app worker \
    --loglevel=$LOG_LEVEL \
    --concurrency=$CONCURRENCY \
    --queues=ultra_fast,default \
    --hostname=worker-ultra-fast@%h \
    --prefetch-multiplier=1 \
    --max-tasks-per-child=500 \
    --max-memory-per-child=200000 \
    --without-gossip \
    --without-mingle \
    --without-heartbeat &

# Worker 4: Geral (backup e tasks gerais)
echo "🔄 Iniciando Worker 4: Geral..."
celery -A app.tasks.celery_app worker \
    --loglevel=$LOG_LEVEL \
    --concurrency=$CONCURRENCY \
    --queues=default,processes,documents \
    --hostname=worker-general@%h \
    --prefetch-multiplier=1 \
    --max-tasks-per-child=500 \
    --max-memory-per-child=200000 \
    --without-gossip \
    --without-mingle \
    --without-heartbeat &

# Aguardar todos os workers
wait
