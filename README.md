# PDPJ Process API - Enterprise Edition

## Overview
Esta é uma API Python enterprise-grade e altamente escalável para consultar, armazenar e entregar dados de processos judiciais e documentos relacionados do Portal de Serviços do Processo Judicial Digital (PDPJ) brasileiro. 

**🚀 Performance Enterprise**: Capaz de processar **milhares de processos** com **monitoramento completo**, **rate limiting inteligente** e **arquitetura robusta** para produção.

## Features Principais

### 🚀 Download Assíncrono com Webhook (NOVO!)
- **Download automático** ao consultar processo
- **Processamento em background** via Celery
- **Webhook callback opcional** com retry automático (3x)
- **Monitoramento em tempo real** com progresso 0-100%
- **Retry automático** de downloads (3x com backoff exponencial)
- **Idempotência** em 3 níveis (job ativo, processo completo, cache)
- **Validação de estados** com StatusManager
- **Regeneração automática** de links S3 expirados

### 🏢 Infraestrutura Enterprise
- **FastAPI enterprise** com middleware stack completo e monitoramento avançado
- **PDPJClient otimizado** com retry inteligente, rate limiting e métricas detalhadas
- **ProcessCacheService** com Redis Pipeline para operações bulk ultra-rápidas
- **TransactionManager** com suporte a savepoints e rollback automático
- **S3Service** com pool de conexões, retry com backoff e métricas de throughput
- **Rate Limiting** por endpoint, usuário e operação com limites dinâmicos
- **Monitoramento proativo** com Prometheus, Sentry e alertas automáticos
- **Testes completos** com roadmap estruturado e validação de 100% dos componentes
- **Autenticação robusta** com API keys e validação de tokens JWT
- **Documentação completa** com guias de configuração e uso
- **Setup automatizado** com scripts otimizados para diferentes ambientes

## Requirements
- **Python 3.12+** (recomendado para melhor performance)
- **Docker and Docker Compose** (para ambiente containerizado)
- **PostgreSQL 14+** (banco de dados principal)
- **Redis 6+** (cache, rate limiting e Celery broker) - **CRÍTICO** ⚡
- **Celery Workers** (processamento assíncrono) - **NOVO** 🆕
- **AWS credentials** (para S3 storage) - **Configurado ✅**
- **PDPJ API tokens** (autenticação com o portal) - **Configurado ✅**
- **Sentry DSN** (opcional, para error tracking)

## Quick Start

### Setup Enterprise

#### Opção 1: Produção Enterprise (Recomendado)
1. Clone o repositório:
   ```bash
   git clone <repo-url>
   cd pdpj-raw
   ```
2. Execute o script de setup automatizado:
   ```bash
   ./setup.sh
   ```
3. Configure as variáveis de ambiente no arquivo `.env`:
   ```bash
   # Configurações Enterprise
   ENVIRONMENT=production
   DEBUG=false
   MAX_CONCURRENT_REQUESTS=100
   MAX_CONCURRENT_DOWNLOADS=50
   RATE_LIMIT_REQUESTS_PER_MINUTE=1000
   SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
   ```
4. Inicie os serviços com Docker Compose:
   ```bash
   docker-compose up -d
   ```
5. Execute as migrations do banco:
   ```bash
   alembic upgrade head
   ```
6. Execute o roadmap completo de testes:
   ```bash
   python test_api_initialization.py
   python test_core_infrastructure.py
   python test_external_connectivity.py
   python test_monitoring_metrics.py
   python test_performance_load.py
   python test_integration_complete.py
   ```

#### Opção 2: Desenvolvimento Local (Completo - API + Celery)

**Script Automatizado (Recomendado):**
```bash
# 1. Setup inicial (apenas primeira vez)
./setup-local.sh

# 2. Iniciar API + Celery juntos
./start-dev-complete.sh
```

Isso inicia automaticamente:
- ✅ API FastAPI (porta 8000)
- ✅ Celery Worker (4 workers)
- ✅ Verifica Redis e PostgreSQL
- ✅ Logs separados (logs/api.log, logs/celery.log)

**Setup Manual (se preferir):**

1. Clone o repositório:
   ```bash
   git clone <repo-url>
   cd pdpj-raw
   ```
2. Execute o script de setup local:
   ```bash
   ./setup-local.sh
   ```
3. Configure as variáveis de ambiente no arquivo `.env`:
   ```bash
   ENVIRONMENT=development
   DEBUG=true
   
   # AWS S3 (obrigatório para armazenamento de documentos)
   AWS_ACCESS_KEY_ID=sua_chave
   AWS_SECRET_ACCESS_KEY=sua_chave_secreta
   AWS_REGION=sa-east-1
   S3_BUCKET_NAME=pdpj-documents-br
   
   # PDPJ API
   PDPJ_API_BASE_URL=https://portaldeservicos.pdpj.jus.br
   PDPJ_API_TOKEN=seu_token_jwt
   ```
4. **Configure permissões AWS S3:**
   ```bash
   # Configurar AWS CLI
   aws configure
   
   # Aplicar permissões IAM
   ./fix_s3_permissions.sh
   ```
5. Execute a aplicação:
   ```bash
   ./run-local.sh
   ```
5. Em outro terminal, execute o Celery worker:
   ```bash
   ./run-celery-local.sh
   ```
6. (Opcional) Execute o Flower para monitoramento:
   ```bash
   ./run-flower-local.sh
   ```

#### Opção 3: Setup Manual
1. Clone o repositório:
   ```bash
   git clone <repo-url>
   cd pdpj-raw
   ```
2. Crie e ative o ambiente virtual:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Linux/Mac
   # ou
   venv\Scripts\activate     # Windows
   ```
3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
4. Instale e configure PostgreSQL e Redis localmente
5. Copie `env.example` para `.env` e configure as variáveis
6. Execute as migrations:
   ```bash
   alembic upgrade head
   ```

### Usage Enterprise

#### Endpoints Principais

##### 📋 Processos
- **Documentação interativa**: `http://localhost:8000/docs`
- **Busca de processos**: `POST /api/v1/processes/search` - Busca com paginação e filtros
- **Processo único**: `GET /api/v1/processes/{numero}?auto_download=true&webhook_url={url}` - **NOVO!** ⚡
- **Status e progresso**: `GET /api/v1/processes/{numero}/status` - **NOVO!** 📊
- **Documentos**: `GET /api/v1/processes/{numero}/files` - Lista de documentos
- **Download metadados**: `POST /api/v1/processes/{numero}/download-documents` - Registrar metadados
- **Download individual**: `POST /api/v1/processes/{numero}/download-document/{id}` - Baixar 1 documento
- **Download em massa**: `POST /api/v1/processes/{numero}/download-all-documents` - Baixar todos

##### 🔔 Webhooks (NOVO!)
- **Validar URL**: `POST /api/v1/webhooks/webhook-validate` - Validar webhook URL
- **Testar conectividade**: `POST /api/v1/webhooks/webhook-test-connectivity` - Testar acesso
- **Enviar teste**: `POST /api/v1/webhooks/webhook-send-test` - Enviar payload de teste
- **Receptor de teste**: `POST /api/v1/webhooks/webhook-test-receiver` - Endpoint para testes

##### 📊 Monitoramento
- **Status do sistema**: `GET /api/v1/monitoring/status` - Status geral
- **Métricas**: `GET /api/v1/monitoring/metrics` - Métricas detalhadas

#### Exemplo de Uso
```bash
# Busca de processos com autenticação
curl -X POST "http://localhost:8000/api/v1/processes/search" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer pdpj_test_b3Xd4tVTqsXrKzJ_sIinewIxmsinYTaIf6KFK9XINvM" \
  -d '{
    "process_numbers": ["1000145-91.2023.8.26.0597"],
    "include_documents": true,
    "page": 1,
    "limit": 10
  }'

# Download de documentos
curl -X POST "http://localhost:8000/api/v1/processes/1000145-91.2023.8.26.0597/download-documents" \
  -H "Authorization: Bearer pdpj_test_b3Xd4tVTqsXrKzJ_sIinewIxmsinYTaIf6KFK9XINvM"

# Monitorar sistema
curl "http://localhost:8000/api/v1/monitoring/status" \
  -H "Authorization: Bearer pdpj_admin_xYl0kmPaK9o00xe_BdhoGBZvALr7YuHKI0gTgePAbZU"
```

#### Performance Esperada
- **Processo único**: < 2 segundos
- **Busca com filtros**: < 5 segundos
- **Download de documentos**: < 10 segundos
- **Throughput**: > 50 req/s
- **Disponibilidade**: > 99.9%

## Project Structure Enterprise
```
app/
  api/                    # REST API endpoints
    ├── processes.py      # Endpoints de processos judiciais
    ├── users.py          # Gerenciamento de usuários
    └── monitoring.py     # Monitoramento e métricas
  core/                   # Configuração e infraestrutura
    ├── config.py         # Configurações centralizadas
    ├── app_factory.py    # Factory da aplicação FastAPI
    ├── middleware_config.py # Stack de middleware
    ├── rate_limiting.py  # Rate limiting inteligente
    ├── security.py       # Autenticação e autorização
    └── proactive_monitoring.py # Monitoramento proativo
  models/                 # Modelos do banco de dados
    ├── process.py        # Modelo de processos
    ├── document.py       # Modelo de documentos
    └── user.py           # Modelo de usuários
  services/               # Serviços de negócio
    ├── pdpj_client.py    # Cliente PDPJ otimizado
    ├── s3_service.py     # Integração com AWS S3
    └── process_cache_service.py # Cache de processos
  utils/                  # Utilitários e helpers
    ├── token_validator.py # Validação de tokens JWT
    ├── monitoring_integration.py # Integração com monitoramento
    └── transaction_manager.py # Gerenciamento de transações
  tasks/                  # Tarefas assíncronas Celery
    ├── celery_app.py     # Configuração do Celery
    ├── process_tasks.py  # Tarefas de processos
    └── document_tasks.py # Tarefas de documentos
tests/                    # Testes automatizados
  ├── test_api_initialization.py # Testes de inicialização
  ├── test_core_infrastructure.py # Testes de infraestrutura
  ├── test_external_connectivity.py # Testes de conectividade
  ├── test_monitoring_metrics.py # Testes de monitoramento
  ├── test_performance_load.py # Testes de performance
  └── test_integration_complete.py # Testes de integração
docs/                     # Documentação
  └── PDPJ_CLIENT_GUIDE.md # Guia completo do cliente
```

## Monitoramento e Métricas

### Dashboard de Performance
Acesse `http://localhost:8000/api/v1/monitoring/status` para visualizar:
- **Status do sistema**: Saúde geral dos componentes
- **Métricas de performance**: Tempos de resposta e throughput
- **Status dos serviços**: PDPJ, S3, Redis, PostgreSQL
- **Alertas automáticos**: CPU alto, memória baixa, erros

### Endpoints de Monitoramento
- `GET /api/v1/monitoring/status` - Status resumido do sistema
- `GET /api/v1/monitoring/metrics` - Métricas detalhadas
- `GET /api/v1/monitoring/performance` - Resumo de performance
- `GET /api/v1/monitoring/health/detailed` - Saúde detalhada dos componentes

### Testes Automatizados
Execute o roadmap completo de testes:
- ✅ **FASE 1**: Inicialização e Configuração Base
- ✅ **FASE 2**: Testes de Infraestrutura Core
- ✅ **FASE 3**: Testes de Conectividade Externa
- ✅ **FASE 4**: Testes de Monitoramento e Métricas
- ✅ **FASE 5**: Testes de Performance e Carga
- ✅ **FASE 6**: Testes de Integração Completa

## Arquitetura Enterprise

### Fluxo de Processamento
```mermaid
graph TD
    A[Cliente] --> B[FastAPI + Middleware Stack]
    B --> C[Rate Limiting]
    B --> D[Authentication]
    B --> E[PDPJClient]
    B --> F[ProcessCacheService]
    B --> G[TransactionManager]
    E --> H[API PDPJ]
    F --> I[Redis Cache]
    G --> J[PostgreSQL]
    B --> K[Celery Workers]
    K --> L[S3Service]
    L --> M[AWS S3]
    B --> N[Monitoring]
    N --> O[Prometheus + Sentry]
```

### Componentes Enterprise
1. **FastAPI**: Middleware stack completo com rate limiting
2. **PDPJClient**: Retry inteligente, métricas e rate limiting
3. **ProcessCacheService**: Cache Redis com TTL configurável
4. **TransactionManager**: Transações com savepoints e rollback
5. **S3Service**: Pool de conexões e retry com backoff
6. **Monitoring**: Prometheus, Sentry e alertas automáticos
7. **Security**: Autenticação JWT e autorização por roles

## Documentação Adicional

### Guias Específicos
- **[PDPJ Client Guide](docs/PDPJ_CLIENT_GUIDE.md)** - Guia completo do cliente PDPJ
- **[Configuration Guide](CONFIGURATION_GUIDE.md)** - Configuração detalhada
- **[Testing Roadmap](TESTING_ROADMAP.md)** - Roadmap completo de testes
- **[Postman Collection V2](POSTMAN_COLLECTION_V2_GUIDE.md)** - Guia da collection robusta
- **[Rate Limiting Guide](RATE_LIMITING_CONFIGURATION_GUIDE.md)** - Configuração de rate limiting

### Scripts de Setup
- **`./setup.sh`** - Setup completo para produção
- **`./setup-local.sh`** - Setup para desenvolvimento local
- **`./run-local.sh`** - Executar API localmente
- **`./run-production.sh`** - Executar em produção

### Testes
- **`test_api_initialization.py`** - Testes de inicialização ✅
- **`test_core_infrastructure.py`** - Testes de infraestrutura ✅
- **`test_external_connectivity.py`** - Testes de conectividade ✅
- **`test_monitoring_metrics.py`** - Testes de monitoramento ✅
- **`test_performance_load.py`** - Testes de performance ✅
- **`test_integration_complete.py`** - Testes de integração ✅

### Testes Oficiais (Pytest)
```bash
# Testes S3 e PDPJ (críticos)
./venv/bin/pytest -v -m critical

# Todos os testes S3
./venv/bin/pytest tests/test_s3_service.py tests/test_pdpj_s3_integration.py -v

# Ver guia completo
cat tests/README_S3_TESTS.md
```

### Scripts de Diagnóstico
- **`test_s3_connectivity.py`** - Diagnóstico completo S3 ✅
- **`test_s3_real_operations.py`** - Operações reais S3 ✅
- **`test_api_v2_download.py`** - Download PDPJ com /api/v2/ ✅

## Contributing
Contribuições, issues e feature requests são bem-vindos!  
Por favor leia o CONTRIBUTING.md para diretrizes.

## License
Este projeto está licenciado sob a Licença MIT.

---

Para roadmap completo de testes e status atual, veja [TESTING_ROADMAP.md](TESTING_ROADMAP.md).