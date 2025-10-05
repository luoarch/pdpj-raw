#!/bin/bash

# Script para executar PDPJ API localmente (sem Docker)
set -e

echo "🚀 Iniciando PDPJ API localmente..."

# Verificar se estamos no ambiente virtual
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  Ativando ambiente virtual..."
    source venv/bin/activate
fi

# Verificar se os serviços estão rodando
echo "🔍 Verificando serviços..."

# Verificar PostgreSQL
if ! pg_isready -h localhost -p 5432 >/dev/null 2>&1; then
    echo "❌ PostgreSQL não está rodando. Iniciando..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew services start postgresql
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        sudo systemctl start postgresql
    fi
    sleep 2
fi

# Verificar Redis
if ! redis-cli ping >/dev/null 2>&1; then
    echo "❌ Redis não está rodando. Iniciando..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew services start redis
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        sudo systemctl start redis-server
    fi
    sleep 2
fi

echo "✅ Serviços verificados"

# Executar migrations se necessário
echo "🗄️  Verificando migrations..."
if [ -f "alembic/versions" ] && [ "$(ls -A alembic/versions)" ]; then
    echo "Executando migrations..."
    alembic upgrade head
else
    echo "⚠️  Nenhuma migration encontrada. Execute: alembic revision --autogenerate -m 'Initial migration'"
fi

# Verificar se usuários existem
echo "👤 Verificando usuários..."
if python -c "from app.core.database import AsyncSessionLocal; from app.models import User; from sqlalchemy import select; import asyncio; asyncio.run(AsyncSessionLocal().execute(select(User))).scalar_one_or_none()" 2>/dev/null; then
    echo "✅ Usuários encontrados"
else
    echo "⚠️  Nenhum usuário encontrado. Criando usuários iniciais..."
    python scripts/create_admin_user.py
fi

echo ""
echo "🎉 Iniciando API..."
echo "🌐 API: http://localhost:8000"
echo "📖 Docs: http://localhost:8000/docs"
echo "🔄 Para parar: Ctrl+C"
echo ""

# Iniciar a API
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
