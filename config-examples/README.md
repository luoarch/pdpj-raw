# Configurações da Aplicação PDPJ Process API

Este diretório contém exemplos de arquivos de configuração para diferentes ambientes e cenários de uso.

## Arquivos Disponíveis

### Arquivos de Ambiente (.env)

- **`.env.development`** - Configurações para desenvolvimento local
- **`.env.staging`** - Configurações para ambiente de staging/homologação  
- **`.env.production`** - Configurações para ambiente de produção

### Arquivos de Override

- **`override.json`** - Exemplo de override em formato JSON
- **`override.yaml`** - Exemplo de override em formato YAML

## Como Usar

### 1. Configuração por Ambiente

Para usar um arquivo de ambiente específico:

```bash
# Desenvolvimento
cp config-examples/.env.development .env

# Staging
cp config-examples/.env.staging .env

# Produção
cp config-examples/.env.production .env
```

### 2. Sistema de Override

O sistema de configuração suporta arquivos de override que podem sobrescrever configurações específicas:

```bash
# Usar override JSON
export CONFIG_OVERRIDE_FILE=config-examples/override.json

# Usar override YAML
export CONFIG_OVERRIDE_FILE=config-examples/override.yaml
```

### 3. Perfis de Ambiente

A aplicação suporta três perfis que ajustam automaticamente as configurações:

#### Development
- Debug habilitado
- Rate limiting desabilitado
- CORS permissivo
- Logging detalhado
- Métricas desabilitadas
- Compressão desabilitada (para facilitar debug)

#### Staging
- Debug desabilitado
- Rate limiting com limites intermediários
- CORS restritivo
- Logging informativo
- Métricas habilitadas
- Compressão habilitada
- Tracing habilitado com amostragem moderada

#### Production
- Debug desabilitado
- Rate limiting com limites restritivos
- CORS muito restritivo
- Logging de warnings/errors
- Métricas habilitadas e protegidas
- Compressão habilitada
- Tracing habilitado com amostragem baixa
- Todas as configurações de segurança ativadas

## Variáveis de Ambiente Importantes

### Obrigatórias para Produção
```bash
# Banco de dados
DB_USER=seu_usuario_db
DB_PASSWORD=sua_senha_db
DB_HOST=seu_host_db
DB_PORT=5432
DB_NAME=pdpj_prod

# Redis
REDIS_HOST=seu_host_redis
REDIS_PORT=6379
REDIS_DB=0

# Segurança
SECRET_KEY=sua_chave_secreta_super_segura

# APIs Externas
PDPJ_API_TOKEN=seu_token_pdpj
AWS_ACCESS_KEY_ID=sua_chave_aws
AWS_SECRET_ACCESS_KEY=sua_chave_secreta_aws

# Monitoramento
SENTRY_DSN=sua_dsn_sentry
DATADOG_API_KEY=sua_chave_datadog
```

### Opcionais
```bash
# Override de configurações
CONFIG_OVERRIDE_FILE=path/to/override.json

# Perfil de ambiente (desenvolvimento/staging/produção)
PROFILE=production

# Configurações específicas
LOG_LEVEL=INFO
CACHE_TTL=3600
RATE_LIMIT_REQUESTS=1000
```

## Estrutura de Configuração

A classe `Settings` no arquivo `app/core/config.py` centraliza todas as configurações e oferece:

- **Validação automática** de campos e dependências
- **Tipagem forte** com Pydantic
- **Proteção de credenciais** com SecretStr
- **Suporte a múltiplos formatos** de override (JSON, YAML, .env)
- **Configurações baseadas em perfil** de ambiente
- **Documentação integrada** para cada campo

## Exemplos de Uso no Código

```python
from app.core.config import settings

# Acessar configurações
print(f"Ambiente: {settings.environment}")
print(f"Debug: {settings.debug}")
print(f"Rate limit: {settings.rate_limit_requests}")

# Usar credenciais seguras
aws_key = settings.aws_access_key_id.get_secret_value()
pdpj_token = settings.pdpj_api_token.get_secret_value()

# Criar instância com overrides específicos
from app.core.config import Settings
custom_settings = Settings.create_with_overrides(
    log_level="DEBUG",
    cache_ttl=600
)
```

## Segurança

### Credenciais Sensíveis
- Todas as credenciais são protegidas com `SecretStr`
- Use variáveis de ambiente para valores sensíveis
- Nunca commite arquivos `.env` com credenciais reais

### Configurações de Produção
- Sempre use HTTPS em produção
- Configure headers de segurança apropriados
- Limite origens CORS apenas ao necessário
- Configure rate limiting adequado
- Habilite monitoramento e alertas

## Troubleshooting

### Problemas Comuns

1. **Erro ao carregar override**: Verifique se o arquivo existe e tem formato válido
2. **Configurações não aplicadas**: Verifique se a variável `PROFILE` está definida corretamente
3. **Credenciais expostas**: Use `SecretStr` e variáveis de ambiente
4. **Rate limiting muito restritivo**: Ajuste `RATE_LIMIT_REQUESTS` para o ambiente

### Debug de Configurações

```python
from app.core.config import settings

# Verificar configurações carregadas
print("Configurações atuais:")
for field_name, field_value in settings.model_dump().items():
    if "secret" in field_name.lower() or "key" in field_name.lower() or "token" in field_name.lower():
        print(f"{field_name}: [PROTEGIDO]")
    else:
        print(f"{field_name}: {field_value}")
```

## Criptografia de Campos Sensíveis

O sistema de configuração suporta criptografia automática de campos sensíveis para máxima segurança em produção.

### Habilitando Criptografia

```bash
# Habilitar criptografia
ENABLE_FIELD_ENCRYPTION=true
ENCRYPTION_KEY=sua_chave_super_secreta_aqui
ENCRYPTION_SALT=salt_personalizado_opcional
```

### Usando Valores Criptografados

1. **Gerar valores criptografados**:
```python
from app.core.config import Settings

settings = Settings.create_with_overrides(
    enable_field_encryption=True,
    encryption_key="sua_chave_secreta",
    encryption_salt="salt_personalizado"
)

# Criptografar valor sensível
encrypted_db_url = settings.encrypt_sensitive_value(
    "postgresql://user:password@localhost:5432/db"
)
print(encrypted_db_url)
```

2. **Usar no arquivo .env**:
```bash
# Arquivo .env com valores criptografados
ENABLE_FIELD_ENCRYPTION=true
ENCRYPTION_KEY=sua_chave_secreta
DATABASE_URL=gAAAAABh...  # Valor criptografado
```

3. **Acessar valores descriptografados**:
```python
from app.core.config import settings

# Valores são automaticamente descriptografados
db_url = settings.get_safe_database_url()
aws_creds = settings.get_safe_aws_credentials()
pdpj_token = settings.get_safe_pdpj_token()
```

### Métodos Seguros Disponíveis

- `get_safe_database_url()` - URL do banco com credenciais protegidas
- `get_safe_redis_url()` - URL do Redis com credenciais protegidas  
- `get_safe_aws_credentials()` - Credenciais AWS protegidas
- `get_safe_pdpj_token()` - Token PDPJ protegido
- `encrypt_sensitive_value(value)` - Criptografar qualquer valor
- `decrypt_sensitive_value(encrypted_value)` - Descriptografar valor

### Exemplo Completo

Veja o arquivo `encryption-example.py` para um exemplo completo de uso da criptografia.

### Segurança da Criptografia

- **Algoritmo**: AES-256 em modo Fernet (cryptographic authentication)
- **Derivação de chave**: PBKDF2-HMAC-SHA256 com 100.000 iterações
- **Salt**: Personalizável para cada ambiente
- **Encoding**: Base64 para armazenamento seguro

### Arquivo de Exemplo Criptografado

O arquivo `.env.encrypted` contém um exemplo de configuração com valores criptografados. Substitua os valores `gAAAAABh...` pelos valores reais criptografados usando o script de exemplo.

## Troubleshooting - Criptografia

### Problemas Comuns

1. **Erro "Chave de criptografia é obrigatória"**:
   - Verifique se `ENCRYPTION_KEY` está definida
   - Certifique-se que `ENABLE_FIELD_ENCRYPTION=true`

2. **Erro ao descriptografar**:
   - Verifique se a chave de criptografia está correta
   - Certifique-se que o salt é o mesmo usado para criptografar
   - Verifique se o valor não foi corrompido

3. **Valores não descriptografam**:
   - Use os métodos seguros (`get_safe_*`) em vez de acessar diretamente
   - Verifique se a configuração de criptografia está ativa

### Debug de Criptografia

```python
from app.core.config import Settings

# Testar configuração de criptografia
settings = Settings.create_with_overrides(
    enable_field_encryption=True,
    encryption_key="teste",
    encryption_salt="teste_salt"
)

# Testar criptografia/descriptografia
test_value = "valor_teste"
encrypted = settings.encrypt_sensitive_value(test_value)
decrypted = settings.decrypt_sensitive_value(encrypted)
print(f"Original: {test_value}")
print(f"Criptografado: {encrypted}")
print(f"Descriptografado: {decrypted}")
print(f"Valores iguais: {test_value == decrypted}")
```
