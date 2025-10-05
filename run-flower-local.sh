#!/bin/bash

# Script para executar Flower (monitoramento Celery) localmente
set -e

echo "🚀 Iniciando Flower localmente..."

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

# Instalar Flower se não estiver instalado
if ! python -c "import flower" 2>/dev/null; then
    echo "📦 Instalando Flower..."
    pip install flower
fi

echo ""
echo "🎉 Iniciando Flower..."
echo "📊 Monitor: http://localhost:5555"
echo "🔄 Para parar: Ctrl+C"
echo ""

# Iniciar Flower
celery -A app.tasks.celery_app flower --port=5555
