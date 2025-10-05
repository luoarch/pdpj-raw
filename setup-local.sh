#!/bin/bash

# Script de setup para desenvolvimento local (sem Docker)
set -e

echo "🚀 Configurando PDPJ API para desenvolvimento local..."

# Verificar se Python 3.12+ está instalado
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 não encontrado. Por favor, instale Python 3.12+"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "✅ Python $PYTHON_VERSION encontrado"

# Verificar se PostgreSQL está instalado
if ! command -v psql &> /dev/null; then
    echo "❌ PostgreSQL não encontrado. Instalando..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew install postgresql
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        sudo apt-get update
        sudo apt-get install -y postgresql postgresql-contrib
    else
        echo "❌ Sistema operacional não suportado. Instale PostgreSQL manualmente."
        exit 1
    fi
fi

# Verificar se Redis está instalado
if ! command -v redis-server &> /dev/null; then
    echo "❌ Redis não encontrado. Instalando..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew install redis
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        sudo apt-get install -y redis-server
    else
        echo "❌ Sistema operacional não suportado. Instale Redis manualmente."
        exit 1
    fi
fi

# Iniciar serviços
echo "🔧 Iniciando serviços..."

# PostgreSQL
if [[ "$OSTYPE" == "darwin"* ]]; then
    brew services start postgresql
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    sudo systemctl start postgresql
    sudo systemctl enable postgresql
fi

# Redis
if [[ "$OSTYPE" == "darwin"* ]]; then
    brew services start redis
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    sudo systemctl start redis-server
    sudo systemctl enable redis-server
fi

# Aguardar serviços iniciarem
echo "⏳ Aguardando serviços iniciarem..."
sleep 3

# Criar banco de dados
echo "🗄️  Configurando banco de dados..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    createdb pdpj_db 2>/dev/null || echo "Banco pdpj_db já existe"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    sudo -u postgres createdb pdpj_db 2>/dev/null || echo "Banco pdpj_db já existe"
fi

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
    echo "   - Configure DATABASE_URL para seu PostgreSQL local"
    echo "   - Configure REDIS_URL para seu Redis local"
    echo "   - Configure credenciais AWS e token PDPJ"
fi

# Inicializar Alembic se não existir
if [ ! -f "alembic/versions" ] || [ -z "$(ls -A alembic/versions)" ]; then
    echo "🗄️  Inicializando Alembic..."
    alembic revision --autogenerate -m "Initial migration"
fi

echo ""
echo "✅ Setup local concluído!"
echo ""
echo "📋 Próximos passos:"
echo "1. Configure as variáveis no arquivo .env"
echo "2. Execute: alembic upgrade head (para criar tabelas)"
echo "3. Execute: python scripts/create_admin_user.py (para criar usuários iniciais)"
echo "4. Execute: uvicorn app.main:app --reload (para iniciar a API)"
echo ""
echo "🌐 A API estará disponível em: http://localhost:8000"
echo "📖 Documentação em: http://localhost:8000/docs"
echo ""
echo "💡 Para processamento assíncrono, execute em outro terminal:"
echo "   celery -A app.tasks.celery_app worker --loglevel=info"
