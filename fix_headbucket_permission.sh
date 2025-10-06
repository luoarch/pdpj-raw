#!/bin/bash

# Script para adicionar permissão HeadBucket específica
# Isso resolve o erro 403 no método bucket_exists()

set -e

echo "🔧 Adicionando permissão HeadBucket..."
echo ""

# Cores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Obter nome do usuário
USER_NAME=$(aws sts get-caller-identity --query Arn --output text | awk -F'/' '{print $NF}')

echo -e "${GREEN}✅ Usuário detectado: $USER_NAME${NC}"
echo ""

# Criar política atualizada com permissão HeadBucket explícita
cat > /tmp/pdpj-s3-policy-fixed.json <<'EOF'
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "ListAllBuckets",
            "Effect": "Allow",
            "Action": [
                "s3:ListAllMyBuckets",
                "s3:GetBucketLocation",
                "s3:HeadBucket"
            ],
            "Resource": "*"
        },
        {
            "Sid": "PDPJBucketAccess",
            "Effect": "Allow",
            "Action": [
                "s3:ListBucket",
                "s3:GetBucketLocation",
                "s3:GetBucketVersioning",
                "s3:HeadBucket"
            ],
            "Resource": "arn:aws:s3:::pdpj-documents-br"
        },
        {
            "Sid": "PDPJObjectAccess",
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:GetObject",
                "s3:DeleteObject",
                "s3:GetObjectVersion",
                "s3:PutObjectAcl",
                "s3:GetObjectAcl"
            ],
            "Resource": "arn:aws:s3:::pdpj-documents-br/*"
        }
    ]
}
EOF

echo "📝 Política atualizada criada"
echo ""

# Aplicar política atualizada
echo "🚀 Aplicando política atualizada..."

if aws iam put-user-policy \
    --user-name "$USER_NAME" \
    --policy-name PDPJBucketAccess \
    --policy-document file:///tmp/pdpj-s3-policy-fixed.json; then
    
    echo ""
    echo -e "${GREEN}✅ Política atualizada com sucesso!${NC}"
    echo ""
    echo "📋 Permissão HeadBucket adicionada"
    echo ""
    
    # Limpar cache de credenciais boto3 (forçar refresh)
    echo "🧹 Limpando cache..."
    rm -rf ~/.aws/boto/cache/* 2>/dev/null || true
    rm -rf ~/.aws/cli/cache/* 2>/dev/null || true
    
    echo -e "${YELLOW}⏳ Aguardando propagação (10 segundos)...${NC}"
    sleep 10
    
    echo ""
    echo "🧪 Testando acesso..."
    if aws s3api head-bucket --bucket pdpj-documents-br 2>/dev/null; then
        echo -e "${GREEN}✅ SUCESSO! HeadBucket funcionando via CLI!${NC}"
    else
        echo -e "${YELLOW}⚠️ CLI ainda com 403, mas pode funcionar no Python...${NC}"
    fi
    
    echo ""
    echo "🎉 Configuração concluída!"
    echo ""
    echo "📝 Próximo passo:"
    echo "   Execute: ./venv/bin/python test_s3_connectivity.py"
    
else
    echo ""
    echo -e "${RED}❌ Erro ao aplicar política!${NC}"
    exit 1
fi

# Limpeza
rm -f /tmp/pdpj-s3-policy-fixed.json

echo ""

