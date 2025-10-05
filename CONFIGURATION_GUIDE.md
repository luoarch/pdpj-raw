# Guia de Configuração - PDPJ API Enterprise Edition v2.0

## Visão Geral

Este guia detalha todas as configurações disponíveis na aplicação PDPJ API, organizadas por categorias e incluindo validações, dependências e valores padrão específicos por ambiente.

## Perfis de Ambiente

A aplicação suporta três perfis principais que automaticamente aplicam configurações otimizadas:

### 🛠️ Development
```env
PROFILE=development
```
**Características:**
- Debug habilitado
- CORS permissivo (`*`)
- Rate limiting desabilitado
- Headers de segurança desabilitados
- HTTPS redirect desabilitado
- Logs em nível DEBUG
- GZip desabilitado para facilitar debug
- Métricas desabilitadas

### 🧪 Staging
```env
PROFILE=staging
```
**Características:**
- Configurações de produção com algumas relaxações
- Rate limit mais permissivo (500 req/min)
- Métricas não protegidas para testes
- Logs em nível INFO
- GZip habilitado
- Headers de segurança habilitados

### 🚀 Production
```env
PROFILE=production
```
**Características:**
- Configurações mais restritivas
- Métricas protegidas
- Logs em nível WARNING
- Warning para rate limits muito altos
- Todas as funcionalidades de segurança habilitadas

## Configurações por Categoria

### 🔐 Segurança

#### Credenciais Sensíveis (SecretStr)
```env
# AWS
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key

# PDPJ API
PDPJ_API_TOKEN=your_pdpj_token

# JWT
SECRET_KEY=your_jwt_secret_key

# Monitoramento
SENTRY_DSN=https://sentry.io/your-dsn
DATADOG_API_KEY=your_datadog_key
NEWRELIC_LICENSE_KEY=your_newrelic_key
HONEYCOMB_API_KEY=your_honeycomb_key
```

#### Headers de Segurança
```env
ENABLE_SECURITY_HEADERS=True
ENABLE_HTTPS_REDIRECT=True
ENABLE_TRUSTED_HOST=True
HSTS_MAX_AGE=31536000
CONTENT_SECURITY_POLICY=default-src 'self'; script-src 'self' 'unsafe-inline'
```

#### Rate Limiting
```env
ENABLE_RATE_LIMITING=True
RATE_LIMIT_REQUESTS=1000
RATE_LIMIT_WINDOW=60
```

### 🌐 Performance HTTP

#### Configurações Básicas
```env
MAX_CONCURRENT_REQUESTS=100
MAX_CONCURRENT_DOWNLOADS=50
MAX_CONNECTIONS_PER_HOST=100
CONNECTION_POOL_SIZE=200
```

#### Configurações Avançadas
```env
ENABLE_GZIP_COMPRESSION=True
GZIP_MINIMUM_SIZE=1000
HTTP2_ENABLED=True
TCP_NODELAY=True
TCP_KEEPALIVE=True
```

#### Timeouts
```env
KEEPALIVE_TIMEOUT=30
REQUEST_TIMEOUT=60
DOWNLOAD_TIMEOUT=300
```

### 📊 Observabilidade

#### Logging
```env
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
LOG_ROTATION_SIZE=100 MB
LOG_RETENTION_DAYS=30
LOG_REQUEST_ID=True
LOG_INCLUDE_USER_ID=False
LOG_INCLUDE_TRACE_ID=False
```

#### Métricas
```env
ENABLE_METRICS=True
METRICS_PATH=/metrics
METRICS_PROTECTED=True
METRICS_CACHE_TTL=30
```

#### Tracing
```env
ENABLE_TRACING=False
TRACING_PROVIDER=opentelemetry
TRACING_ENDPOINT=
TRACING_SERVICE_NAME=pdpj-api
TRACING_SERVICE_VERSION=2.0.0
TRACING_SAMPLE_RATE=0.1
```

### 🗄️ Banco de Dados e Cache

#### PostgreSQL
```env
DATABASE_URL=postgresql://user:password@localhost:5432/pdpj_db
```

#### Redis
```env
REDIS_URL=redis://localhost:6379/0
REDIS_MAX_CONNECTIONS=100
REDIS_RETRY_ON_TIMEOUT=True
REDIS_SOCKET_KEEPALIVE=True
CACHE_TTL=3600
CACHE_CRITICAL=False
```

### ⚡ Workers e Concorrência

```env
UVICORN_WORKERS=4
CELERY_WORKERS=4
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/1
```

### 📦 Operações Bulk

```env
BULK_BATCH_SIZE=1000
BULK_INSERT_CHUNK_SIZE=500
```

### 🌍 CORS

```env
CORS_ORIGINS=["https://app.example.com", "https://admin.example.com"]
CORS_ALLOW_CREDENTIALS=True
CORS_ALLOW_METHODS=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
CORS_ALLOW_HEADERS=["*"]
```

### 🔧 API

```env
API_PREFIX=/api/v1
API_TITLE=PDPJ Process API - Enterprise Edition v2.0
API_DESCRIPTION=API enterprise para consulta e armazenamento de processos judiciais via PDPJ
API_VERSION=2.0.0
```

## Validações e Dependências

### Validações Automáticas

1. **Perfis**: Apenas `development`, `staging`, `production` são aceitos
2. **Tracing**: Taxa de amostragem deve estar entre 0.0 e 1.0
3. **Logging**: Níveis válidos são DEBUG, INFO, WARNING, ERROR, CRITICAL
4. **Performance**: Todos os valores numéricos devem ser > 0
5. **Timeouts**: Todos os timeouts devem ser > 0
6. **Cache**: TTL não pode ser negativo
7. **Workers**: Número de workers deve ser > 0

### Dependências Cruzadas

1. **Rate Limiting**: Se desabilitado, `rate_limit_requests` é definido como 0
2. **Tracing**: Provedores `jaeger` e `zipkin` requerem `tracing_endpoint`
3. **Perfil**: Configurações específicas são aplicadas automaticamente
4. **Environment**: Sincronizado com o perfil selecionado

### Warnings Automáticos

1. **Rate Limit Alto em Produção**: Warning se > 1000 req/min
2. **Prefixo API Não Padrão**: Warning se não seguir `/api/vX`

## Exemplos de Configuração

### Desenvolvimento Local
```env
PROFILE=development
DATABASE_URL=postgresql://postgres:password@localhost:5432/pdpj_dev
REDIS_URL=redis://localhost:6379/0
PDPJ_API_TOKEN=dev_token_here
```

### Staging
```env
PROFILE=staging
DATABASE_URL=postgresql://user:pass@staging-db:5432/pdpj_staging
REDIS_URL=redis://staging-redis:6379/0
PDPJ_API_TOKEN=staging_token_here
SENTRY_DSN=https://sentry.io/staging-dsn
```

### Produção
```env
PROFILE=production
DATABASE_URL=postgresql://user:pass@prod-db:5432/pdpj_prod
REDIS_URL=redis://prod-redis:6379/0
PDPJ_API_TOKEN=prod_token_here
SENTRY_DSN=https://sentry.io/prod-dsn
DATADOG_API_KEY=prod_datadog_key
ENABLE_TRACING=True
TRACING_PROVIDER=jaeger
TRACING_ENDPOINT=http://jaeger:14268
```

## Override de Configuração

### Arquivo de Override
```env
CONFIG_OVERRIDE_FILE=/path/to/override.env
```

### Variáveis de Ambiente
Todas as configurações podem ser sobrescritas via variáveis de ambiente:
```bash
export PROFILE=production
export ENABLE_METRICS=True
export RATE_LIMIT_REQUESTS=500
```

## Troubleshooting

### Problemas Comuns

1. **Erro de Validação de Perfil**
   ```
   ValueError: Perfil 'invalid' inválido
   ```
   **Solução**: Use `development`, `staging` ou `production`

2. **Erro de Tracing Provider**
   ```
   ValueError: Provedor de tracing 'invalid' não suportado
   ```
   **Solução**: Use `opentelemetry`, `jaeger` ou `zipkin`

3. **Erro de Taxa de Amostragem**
   ```
   ValueError: Taxa de amostragem de tracing deve estar entre 0.0 e 1.0
   ```
   **Solução**: Use valores entre 0.0 e 1.0

4. **Warning de Rate Limit Alto**
   ```
   UserWarning: Rate limit muito alto para produção: 2000
   ```
   **Solução**: Considere reduzir para ≤ 1000 em produção

### Debug de Configurações

1. **Verificar Configurações Carregadas**:
   ```python
   from app.core.config import settings
   print(settings.model_dump())
   ```

2. **Verificar Perfil Ativo**:
   ```python
   print(f"Profile: {settings.profile}")
   print(f"Environment: {settings.environment}")
   print(f"Debug: {settings.debug}")
   ```

3. **Verificar Middlewares Ativos**:
   ```python
   print(f"Security Headers: {settings.enable_security_headers}")
   print(f"Rate Limiting: {settings.enable_rate_limiting}")
   print(f"Metrics: {settings.enable_metrics}")
   ```

## Migração e Compatibilidade

### Migração de Versões Anteriores

1. **Pydantic V1 → V2**: Todas as validações foram migradas
2. **Configurações Legacy**: Mantidas compatibilidade com configurações antigas
3. **Novos Campos**: Campos opcionais com valores padrão sensatos

### Compatibilidade

- **Python**: 3.8+
- **Pydantic**: 2.0+
- **FastAPI**: 0.100+
- **Redis**: 6.0+
- **PostgreSQL**: 12+

## Referências

- [Pydantic Settings Documentation](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- [FastAPI Configuration](https://fastapi.tiangolo.com/advanced/settings/)
- [Redis Configuration](https://redis.io/docs/management/config/)
- [PostgreSQL Configuration](https://www.postgresql.org/docs/current/config-setting.html)
