#!/bin/bash

# Script de setup para o projeto PDPJ API
set -e

echo "🚀 Configurando projeto PDPJ API..."

# Verificar se Python 3.12+ está instalado
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 não encontrado. Por favor, instale Python 3.12+"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "✅ Python $PYTHON_VERSION encontrado"

# Criar ambiente virtual se não existir
if [ ! -d "venv" ]; then
    echo "📦 Criando ambiente virtual..."
    python3 -m venv venv
fi

# Ativar ambiente virtual
echo "🔧 Ativando ambiente virtual..."
source venv/bin/activate

# Atualizar pip
echo "⬆️  Atualizando pip..."
pip install --upgrade pip

# Instalar dependências
echo "📚 Instalando dependências..."
pip install -r requirements.txt

# Criar diretórios necessários
echo "📁 Criando diretórios..."
mkdir -p logs
mkdir -p docker/postgres

# Copiar arquivo de configuração se não existir
if [ ! -f ".env" ]; then
    echo "⚙️  Criando arquivo .env..."
    cp env.example .env
    echo "⚠️  IMPORTANTE: Configure as variáveis no arquivo .env antes de continuar!"
fi

# Inicializar Alembic se não existir
if [ ! -f "alembic/versions" ] || [ -z "$(ls -A alembic/versions)" ]; then
    echo "🗄️  Inicializando Alembic..."
    alembic revision --autogenerate -m "Initial migration"
fi

echo ""
echo "✅ Setup concluído!"
echo ""
echo "📋 Próximos passos:"
echo "1. Configure as variáveis no arquivo .env"
echo "2. Execute: docker-compose up -d (para PostgreSQL e Redis)"
echo "3. Execute: alembic upgrade head (para criar tabelas)"
echo "4. Execute: python scripts/create_admin_user.py (para criar usuários iniciais)"
echo "5. Execute: uvicorn app.main:app --reload (para iniciar a API)"
echo ""
echo "🌐 A API estará disponível em: http://localhost:8000"
echo "📖 Documentação em: http://localhost:8000/docs"
echo "👤 Usuários criados automaticamente (admin e test_user)"
