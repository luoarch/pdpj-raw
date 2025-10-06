#!/bin/bash

# Script para corrigir permissões S3 via AWS CLI
# Região: sa-east-1 (São Paulo)
# Bucket: pdpj-documents-br

set -e

echo "🔧 Corrigindo permissões S3 para PDPJ..."
echo ""

# Cores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Verificar se AWS CLI está instalado
if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI não está instalado!${NC}"
    echo "Instale com: brew install awscli (macOS) ou pip install awscli"
    exit 1
fi

echo -e "${GREEN}✅ AWS CLI encontrado${NC}"

# Verificar credenciais
echo ""
echo "📋 Verificando credenciais AWS..."
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}❌ Credenciais AWS não configuradas!${NC}"
    echo "Configure com: aws configure"
    exit 1
fi

# Obter informações da conta
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
USER_ARN=$(aws sts get-caller-identity --query Arn --output text)
USER_NAME=$(echo $USER_ARN | awk -F'/' '{print $NF}')

echo -e "${GREEN}✅ Credenciais válidas${NC}"
echo "   Account ID: $ACCOUNT_ID"
echo "   Usuário: $USER_NAME"
echo ""

# Criar arquivo de política
echo "📝 Criando política IAM..."

cat > /tmp/pdpj-s3-policy.json <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "ListAllBuckets",
            "Effect": "Allow",
            "Action": [
                "s3:ListAllMyBuckets",
                "s3:GetBucketLocation"
            ],
            "Resource": "*"
        },
        {
            "Sid": "PDPJBucketAccess",
            "Effect": "Allow",
            "Action": [
                "s3:ListBucket",
                "s3:GetBucketLocation",
                "s3:GetBucketVersioning"
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

echo -e "${GREEN}✅ Política criada em: /tmp/pdpj-s3-policy.json${NC}"
echo ""

# Aplicar política inline no usuário
echo "🚀 Aplicando política ao usuário IAM..."
echo ""

if aws iam put-user-policy \
    --user-name "$USER_NAME" \
    --policy-name PDPJBucketAccess \
    --policy-document file:///tmp/pdpj-s3-policy.json; then
    
    echo ""
    echo -e "${GREEN}✅ Política aplicada com sucesso!${NC}"
    echo ""
    echo "📋 Detalhes:"
    echo "   Usuário: $USER_NAME"
    echo "   Política: PDPJBucketAccess"
    echo "   Bucket: pdpj-documents-br"
    echo ""
    
    # Verificar política aplicada
    echo "🔍 Verificando política aplicada..."
    if aws iam get-user-policy \
        --user-name "$USER_NAME" \
        --policy-name PDPJBucketAccess &> /dev/null; then
        echo -e "${GREEN}✅ Política confirmada!${NC}"
    fi
    
    echo ""
    echo -e "${YELLOW}⏳ Aguardando propagação (30 segundos)...${NC}"
    sleep 30
    
    echo ""
    echo "🧪 Testando acesso ao bucket..."
    if aws s3 ls s3://pdpj-documents-br/ &> /dev/null; then
        echo -e "${GREEN}✅ SUCESSO! Acesso ao bucket funcionando!${NC}"
    else
        echo -e "${YELLOW}⚠️ Ainda sem acesso. Aguarde mais alguns minutos para propagação completa.${NC}"
    fi
    
    echo ""
    echo "🎉 Configuração concluída!"
    echo ""
    echo "📝 Próximos passos:"
    echo "   1. Aguarde 1-2 minutos para propagação completa"
    echo "   2. Execute: ./venv/bin/python test_s3_connectivity.py"
    echo "   3. Todos os testes devem passar ✅"
    
else
    echo ""
    echo -e "${RED}❌ Erro ao aplicar política!${NC}"
    echo ""
    echo "💡 Possíveis causas:"
    echo "   1. Usuário não tem permissão para modificar políticas IAM"
    echo "   2. Nome do usuário incorreto"
    echo "   3. Política já existe com nome diferente"
    echo ""
    echo "🔧 Soluções alternativas:"
    echo "   1. Use o Console AWS (mais fácil)"
    echo "   2. Peça ao administrador AWS para aplicar a política"
    echo "   3. Use uma política gerenciada existente"
    exit 1
fi

# Limpeza
rm -f /tmp/pdpj-s3-policy.json

echo ""

