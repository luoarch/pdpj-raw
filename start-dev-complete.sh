#!/bin/bash

# Script para iniciar COMPLETO: API + Celery Worker
set -e

echo "🚀 Iniciando PDPJ API + Celery Worker (Desenvolvimento Completo)"
echo "================================================================"

# Verificar se venv existe
if [ ! -d "venv" ]; then
    echo "❌ Ambiente virtual não encontrado. Execute ./setup-local.sh primeiro"
    exit 1
fi

# Ativar venv
source venv/bin/activate

# Verificar serviços
echo "🔍 Verificando serviços..."

# Redis
if ! redis-cli ping > /dev/null 2>&1; then
    echo "❌ Redis não está rodando. Iniciando..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew services start redis
    fi
    sleep 2
fi
echo "✅ Redis OK"

# PostgreSQL
if ! pg_isready > /dev/null 2>&1; then
    echo "❌ PostgreSQL não está rodando. Iniciando..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew services start postgresql
    fi
    sleep 2
fi
echo "✅ PostgreSQL OK"

# Parar processos existentes
echo "🔄 Parando processos anteriores..."
pkill -f "uvicorn app.main:app" 2>/dev/null || true
pkill -f "celery.*worker" 2>/dev/null || true
sleep 2

# Criar diretórios
mkdir -p logs

echo ""
echo "🎯 Iniciando serviços..."
echo ""

# 1. Iniciar API em background
echo "📡 Iniciando API FastAPI..."
uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --reload \
    --log-level info \
    > logs/api.log 2>&1 &

API_PID=$!
echo "   → PID: $API_PID"
echo "   → Logs: logs/api.log"
sleep 3

# 2. Iniciar Celery Worker em background
echo "⚙️  Iniciando Celery Worker..."
celery -A app.tasks.celery_app worker \
    --loglevel=info \
    --concurrency=4 \
    --max-tasks-per-child=100 \
    --time-limit=3600 \
    --soft-time-limit=3300 \
    > logs/celery.log 2>&1 &

CELERY_PID=$!
echo "   → PID: $CELERY_PID"
echo "   → Logs: logs/celery.log"
sleep 3

# Verificar se está tudo rodando
echo ""
echo "🧪 Verificando saúde dos serviços..."
sleep 2

# Testar API
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ API FastAPI está rodando"
else
    echo "❌ API FastAPI falhou ao iniciar - verifique logs/api.log"
    exit 1
fi

# Testar Celery (via Redis)
if celery -A app.tasks.celery_app inspect ping > /dev/null 2>&1; then
    echo "✅ Celery Worker está rodando"
else
    echo "⚠️ Celery Worker pode não estar pronto ainda (aguarde alguns segundos)"
fi

echo ""
echo "================================================================"
echo "✅ PDPJ API + Celery Worker INICIADOS COM SUCESSO!"
echo "================================================================"
echo ""
echo "📊 Status dos Serviços:"
echo "   🌐 API FastAPI:    http://localhost:8000"
echo "   📖 Documentação:   http://localhost:8000/docs"
echo "   ❤️  Health Check:  http://localhost:8000/health"
echo "   ⚙️  Celery Worker: Rodando (PID: $CELERY_PID)"
echo ""
echo "📁 Logs:"
echo "   API:    tail -f logs/api.log"
echo "   Celery: tail -f logs/celery.log"
echo ""
echo "🛑 Para parar tudo:"
echo "   pkill -f uvicorn && pkill -f celery"
echo ""
echo "💡 Dica: Para ver tasks Celery em tempo real:"
echo "   ./run-flower-local.sh  (Monitor em http://localhost:5555)"
echo ""

