#!/bin/bash

# Script para executar Celery localmente (sem Docker)
set -e

echo "🚀 Iniciando Celery Worker localmente..."

# Verificar se estamos no ambiente virtual
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  Ativando ambiente virtual..."
    source venv/bin/activate
fi

# Verificar se Redis está rodando
if ! redis-cli ping >/dev/null 2>&1; then
    echo "❌ Redis não está rodando. Iniciando..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew services start redis
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        sudo systemctl start redis-server
    fi
    sleep 2
fi

echo "✅ Redis verificado"

# Verificar se PostgreSQL está rodando
if ! pg_isready -h localhost -p 5432 >/dev/null 2>&1; then
    echo "❌ PostgreSQL não está rodando. Iniciando..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew services start postgresql
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        sudo systemctl start postgresql
    fi
    sleep 2
fi

echo "✅ PostgreSQL verificado"

echo ""
echo "🎉 Iniciando Celery Worker..."
echo "📊 Monitor: http://localhost:5555 (se Flower estiver rodando)"
echo "🔄 Para parar: Ctrl+C"
echo ""

# Iniciar Celery Worker
celery -A app.tasks.celery_app worker --loglevel=info --concurrency=4
