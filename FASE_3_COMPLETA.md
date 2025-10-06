# ✅ FASE 3: COMPLETA - Sistema de Webhook

**Data:** 2025-10-06  
**Status:** ✅ SUCESSO  
**Duração:** ~1 hora

---

## 📊 Resultados

### ✅ WebhookService Implementado

**Arquivo:** `app/services/webhook_service.py`

**Features:**
- ✅ Envio de webhooks com retry automático (3 tentativas)
- ✅ Backoff exponencial (2s, 4s, 8s)
- ✅ Timeout configurável (30s padrão)
- ✅ Validação de URLs (protocolo, domínio, porta)
- ✅ Headers customizados (timestamp, attempt, job_id)
- ✅ Teste de conectividade
- ✅ Logging detalhado

**Configuração:**
```python
max_retries = 3       # Tentativas
timeout = 30.0        # Timeout em segundos
retry_delay = 2.0     # Delay base (com backoff exponencial)
```

---

### ✅ Endpoints de Webhook

**Arquivo:** `app/api/webhooks.py`

#### 1. **POST /webhook-validate**
Validar formato de URL
```json
Request: {"webhook_url": "https://example.com/webhook"}
Response: {"valid": true, "message": "URL válida para webhook"}
```

#### 2. **POST /webhook-test-connectivity**
Testar conectividade real
```json
Request: {"webhook_url": "https://example.com/webhook"}
Response: {
  "reachable": true,
  "status_code": 200,
  "response_time_ms": 123.5
}
```

#### 3. **POST /webhook-send-test**
Enviar webhook de teste com retry
```json
Request: {"webhook_url": "http://localhost:8000/api/v1/webhooks/webhook-test-receiver"}
Response: {
  "success": true,
  "status_code": 200,
  "attempts": 1,
  "message": "Webhook enviado com sucesso!"
}
```

#### 4. **POST /webhook-test-receiver**
Endpoint receptor para testes
```json
Response: {
  "received": true,
  "timestamp": "2025-10-06T12:00:00",
  "payload_keys": ["test", "message", "timestamp"],
  "message": "Webhook recebido com sucesso!"
}
```

---

## 🧪 Testes Realizados

### Teste 1: Validação de URL Válida ✅
```bash
curl -X POST /webhooks/webhook-validate \
  -d '{"webhook_url": "https://example.com/webhook"}'
```

**Resultado:**
```json
{
  "valid": true,
  "url": "https://example.com/webhook",
  "message": "URL válida para webhook"
}
```
✅ **PASSOU**

---

### Teste 2: Validação de URL Inválida ✅
```bash
curl -X POST /webhooks/webhook-validate \
  -d '{"webhook_url": "ftp://invalid-url"}'
```

**Resultado:**
```json
{
  "valid": false,
  "url": "ftp://invalid-url",
  "error": "URL deve usar protocolo HTTP ou HTTPS",
  "message": "URL inválida para webhook"
}
```
✅ **PASSOU**

---

### Teste 3: Envio de Webhook Completo ✅
```bash
curl -X POST /webhooks/webhook-send-test \
  -d '{"webhook_url": "http://localhost:8000/api/v1/webhooks/webhook-test-receiver"}'
```

**Resultado:**
```json
{
  "success": true,
  "url": "http://localhost:8000/api/v1/webhooks/webhook-test-receiver",
  "status_code": 200,
  "attempts": 1,
  "message": "Webhook enviado com sucesso!"
}
```
✅ **PASSOU**

---

## 📝 Arquivos Criados/Modificados

1. ✅ `app/services/webhook_service.py` (NOVO)
   - Classe `WebhookService`
   - Método `send_webhook` com retry
   - Método `validate_webhook_url`
   - Método `test_webhook_connectivity`
   - Instância global `webhook_service`

2. ✅ `app/api/webhooks.py` (NOVO)
   - 4 endpoints de webhook
   - Schemas de request (Pydantic)
   - Logging detalhado

3. ✅ `app/core/router_config.py`
   - Registro do router `webhooks`
   - Import atualizado

---

## 🔧 Funcionalidades Técnicas

### Retry Automático com Backoff Exponencial
```python
for attempt in range(1, retries + 1):
    try:
        # Enviar webhook
        response = await client.post(webhook_url, json=payload)
        if 200 <= response.status_code < 300:
            return {"success": True}
    except Exception as e:
        last_error = str(e)
    
    # Aguardar com backoff: 2s, 4s, 8s
    if attempt < retries:
        wait_time = self.retry_delay * (2 ** (attempt - 1))
        await asyncio.sleep(wait_time)
```

### Validações de Segurança
```python
def validate_webhook_url(self, url: str) -> tuple[bool, Optional[str]]:
    # 1. Protocolo HTTP/HTTPS
    if not url.startswith(('http://', 'https://')):
        return False, "URL deve usar protocolo HTTP ou HTTPS"
    
    # 2. Domínio válido
    if not parsed.netloc:
        return False, "URL inválida: domínio não encontrado"
    
    # 3. Portas bloqueadas
    if parsed.port and parsed.port in [22, 23, 3389]:
        return False, f"Porta {parsed.port} não permitida"
    
    return True, None
```

### Headers Customizados
```python
headers = {
    "Content-Type": "application/json",
    "User-Agent": "PDPJ-API-Webhook/1.0",
    "X-Webhook-Timestamp": datetime.utcnow().isoformat(),
    "X-Webhook-Attempt": str(attempt),
    "X-Webhook-ID": payload.get("job_id", "unknown")
}
```

---

## 📊 Casos de Uso

### 1. Validar Webhook Antes de Usar
```bash
# Validar URL
POST /webhooks/webhook-validate
{"webhook_url": "https://myapp.com/callback"}

# Testar conectividade
POST /webhooks/webhook-test-connectivity
{"webhook_url": "https://myapp.com/callback"}
```

### 2. Testar Webhook Localmente
```bash
# Terminal 1: Receber webhook
curl /webhooks/webhook-test-receiver

# Terminal 2: Enviar teste
POST /webhooks/webhook-send-test
{"webhook_url": "http://localhost:8000/api/v1/webhooks/webhook-test-receiver"}
```

### 3. Debug de Webhook em Produção
```bash
# Enviar payload customizado
POST /webhooks/webhook-send-test
{
  "webhook_url": "https://myapp.com/callback",
  "test_payload": {
    "process_number": "1234567-89.2025.8.11.0041",
    "status": "completed",
    "documents": [...]
  }
}
```

---

## 🎯 Integração Futura (FASE 4)

O `WebhookService` será usado na **FASE 4 (Download Assíncrono)**:

```python
# Na Celery Task, ao finalizar download:
if webhook_url:
    payload = {
        "process_number": process_number,
        "status": "completed",
        "total_documents": total,
        "completed_documents": completed,
        "documents": [...],  # Com URLs S3
        "completed_at": datetime.utcnow().isoformat()
    }
    
    result = await webhook_service.send_webhook(webhook_url, payload)
    
    # Atualizar ProcessJob com resultado
    job.webhook_sent = result.get("success")
    job.webhook_attempts = result.get("attempts")
```

---

## ✅ Checklist FASE 3

- [x] 3.1 Criar `WebhookService`
- [x] 3.2 Implementar `send_webhook` com retry
- [x] 3.3 Implementar `validate_webhook_url`
- [x] 3.4 Implementar `test_webhook_connectivity`
- [x] 3.5 Criar endpoint `/webhook-validate`
- [x] 3.6 Criar endpoint `/webhook-test-connectivity`
- [x] 3.7 Criar endpoint `/webhook-send-test`
- [x] 3.8 Criar endpoint `/webhook-test-receiver`
- [x] 3.9 Registrar router no `app_factory`
- [x] 3.10 Testar validação de URL válida
- [x] 3.11 Testar validação de URL inválida
- [x] 3.12 Testar envio completo de webhook
- [x] ✅ TESTE FASE 3: TODOS PASSARAM

---

## 🎯 Próxima Fase

**FASE 4: Download Assíncrono** (A MAIS COMPLEXA - 4h)
- Modificar `GET /{numero}` para aceitar `webhook_url` e `auto_download`
- Criar Celery task `download_process_documents_async`
- Integrar com `WebhookService` para callback
- Atualizar `ProcessJob` durante execução
- Testar fluxo completo

**Estimativa:** 4 horas

---

**Status Final:** ✅ 100% COMPLETO

**Progresso Geral:** 3/10 fases (30% do roadmap)

