#!/bin/bash

# Script para executar testes automatizados da API PDPJ
# Requer: newman (npm install -g newman)

echo "🚀 Iniciando testes automatizados da API PDPJ"
echo "=============================================="

# Verificar se newman está instalado
if ! command -v newman &> /dev/null; then
    echo "❌ Newman não encontrado. Instale com: npm install -g newman"
    exit 1
fi

# Verificar se arquivos existem
if [ ! -f "PDPJ_API_Collection_v2.json" ]; then
    echo "❌ Collection não encontrada: PDPJ_API_Collection_v2.json"
    exit 1
fi

if [ ! -f "PDPJ_API_Environment.json" ]; then
    echo "❌ Environment não encontrado: PDPJ_API_Environment.json"
    exit 1
fi

# Criar diretório para relatórios
mkdir -p reports

echo "📋 Executando Health Check..."
newman run PDPJ_API_Collection_v2.json \
    -e PDPJ_API_Environment.json \
    --folder "🏥 Health Check" \
    --reporters cli,json \
    --reporter-json-export reports/health-check.json

echo ""
echo "👤 Testando Funcionalidades de Usuário..."
newman run PDPJ_API_Collection_v2.json \
    -e PDPJ_API_Environment.json \
    --folder "👤 Usuários" \
    --reporters cli,json \
    --reporter-json-export reports/users.json

echo ""
echo "📋 Testando Funcionalidades de Processos..."
newman run PDPJ_API_Collection_v2.json \
    -e PDPJ_API_Environment.json \
    --folder "📋 Processos" \
    --reporters cli,json \
    --reporter-json-export reports/processes.json

echo ""
echo "📄 Testando Funcionalidades de Documentos..."
newman run PDPJ_API_Collection_v2.json \
    -e PDPJ_API_Environment.json \
    --folder "📄 Documentos" \
    --reporters cli,json \
    --reporter-json-export reports/documents.json

echo ""
echo "🧪 Executando Testes de Stress..."
newman run PDPJ_API_Collection_v2.json \
    -e PDPJ_API_Environment.json \
    --folder "🧪 Testes de Stress" \
    --reporters cli,json \
    --reporter-json-export reports/stress.json

echo ""
echo "📊 Executando Monitoramento..."
newman run PDPJ_API_Collection_v2.json \
    -e PDPJ_API_Environment.json \
    --folder "📊 Monitoramento" \
    --reporters cli,json \
    --reporter-json-export reports/monitoring.json

echo ""
echo "🔧 Testando Configurações..."
newman run PDPJ_API_Collection_v2.json \
    -e PDPJ_API_Environment.json \
    --folder "🔧 Configurações" \
    --reporters cli,json \
    --reporter-json-export reports/config.json

echo ""
echo "📈 Gerando Relatório Completo..."
newman run PDPJ_API_Collection_v2.json \
    -e PDPJ_API_Environment.json \
    --reporters cli,html \
    --reporter-html-export reports/complete-report.html

echo ""
echo "✅ Testes concluídos!"
echo "📊 Relatórios salvos em: ./reports/"
echo "🌐 Abra reports/complete-report.html para ver o relatório completo"

# Verificar se houve falhas
if [ -f "reports/health-check.json" ]; then
    echo ""
    echo "🔍 Resumo dos Resultados:"
    echo "========================"
    
    # Contar falhas em cada categoria
    for report in reports/*.json; do
        if [ -f "$report" ]; then
            category=$(basename "$report" .json)
            failures=$(jq -r '.run.failures | length' "$report" 2>/dev/null || echo "0")
            if [ "$failures" != "0" ]; then
                echo "❌ $category: $failures falhas"
            else
                echo "✅ $category: OK"
            fi
        fi
    done
fi

echo ""
echo "🎯 Para executar testes específicos:"
echo "newman run PDPJ_API_Collection_v2.json -e PDPJ_API_Environment.json --folder \"Nome da Pasta\""
