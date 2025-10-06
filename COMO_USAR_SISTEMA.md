# 📚 Como Usar o Sistema de Download Assíncrono

**Versão:** 1.0  
**Última Atualização:** 2025-10-06

---

## 🚀 Quick Start

### 1. Iniciar Ambiente Completo
```bash
./start-dev-complete.sh
```

Isso inicia:
- ✅ API FastAPI (porta 8000)
- ✅ Celery Worker (4 workers)
- ✅ Verifica Redis e PostgreSQL

---

## 🎯 Casos de Uso

### Caso 1: Download com Webhook (Callback Automático)

```bash
# 1. Consultar processo (inicia download assíncrono)
curl -X GET "http://localhost:8000/api/v1/processes/NUMERO?webhook_url=https://myapp.com/callback" \
  -H "Authorization: Bearer pdpj_admin_..."

# Resposta imediata:
{
  "process_number": "...",
  "has_documents": true,
  "court": "TJMT"
}

# 2. Sistema processa em background...

# 3. Quando completo, recebe callback automático:
POST https://myapp.com/callback
{
  "process_number": "...",
  "status": "completed",
  "job_id": "uuid-...",
  "total_documents": 31,
  "completed_documents": 31,
  "failed_documents": 0,
  "documents": [
    {
      "id": "123",
      "uuid": "abc-def-...",
      "name": "Petição.pdf",
      "status": "available",
      "download_url": "https://s3.amazonaws.com/...",
      "size": 123456
    },
    ...
  ],
  "completed_at": "2025-10-06T14:00:00"
}
```

---

### Caso 2: Download sem Webhook (Polling Manual)

```bash
# 1. Consultar processo (inicia download)
curl -X GET "http://localhost:8000/api/v1/processes/NUMERO" \
  -H "Authorization: Bearer pdpj_admin_..."

# Resposta imediata

# 2. Consultar status periodicamente
curl -X GET "http://localhost:8000/api/v1/processes/NUMERO/status" \
  -H "Authorization: Bearer pdpj_admin_..."

# Durante processamento:
{
  "status": "processing",
  "progress_percentage": 45.5,
  "completed_documents": 15,
  "total_documents": 33,
  "job_id": "uuid-..."
}

# Quando completo:
{
  "status": "completed",
  "progress_percentage": 100.0,
  "completed_documents": 33,
  "total_documents": 33,
  "documents": [...]  # Com URLs S3
}
```

---

### Caso 3: Desabilitar Download Automático

```bash
# Apenas consultar metadados sem iniciar download
curl -X GET "http://localhost:8000/api/v1/processes/NUMERO?auto_download=false" \
  -H "Authorization: Bearer pdpj_admin_..."
```

---

## 🔍 Monitoramento

### Verificar Progresso
```bash
# Status resumido
curl "http://localhost:8000/api/v1/processes/NUMERO/status" | jq '{
  status,
  progress_percentage,
  completed_documents,
  total_documents,
  job_id
}'
```

### Ver Documentos com Falha
```bash
# Filtrar documentos FAILED
curl "http://localhost:8000/api/v1/processes/NUMERO/status" | \
  jq '.documents[] | select(.status == "failed")'
```

### Verificar Webhook
```bash
# Info do webhook
curl "http://localhost:8000/api/v1/processes/NUMERO/status" | jq '{
  webhook_url,
  webhook_sent,
  webhook_sent_at
}'
```

---

## 🧪 Testes de Webhook

### 1. Validar URL
```bash
curl -X POST "http://localhost:8000/api/v1/webhooks/webhook-validate" \
  -H "Content-Type: application/json" \
  -d '{"webhook_url": "https://myapp.com/callback"}'

# Resposta:
{
  "valid": true,
  "message": "URL válida para webhook"
}
```

### 2. Testar Conectividade
```bash
curl -X POST "http://localhost:8000/api/v1/webhooks/webhook-test-connectivity" \
  -H "Content-Type: application/json" \
  -d '{"webhook_url": "https://myapp.com/callback"}'

# Resposta:
{
  "reachable": true,
  "status_code": 200,
  "response_time_ms": 123.5
}
```

### 3. Enviar Payload de Teste
```bash
curl -X POST "http://localhost:8000/api/v1/webhooks/webhook-send-test" \
  -H "Content-Type: application/json" \
  -d '{
    "webhook_url": "https://myapp.com/callback",
    "test_payload": {
      "test": true,
      "message": "Teste do sistema PDPJ"
    }
  }'
```

---

## 📊 Comportamento do Sistema

### Status de Documentos

```
PENDING ────→ PROCESSING ────→ AVAILABLE ✅
    │              │
    │              └────→ FAILED ❌
    │                       ↓
    └────→ FAILED ←────────┘ (retry permitido)
```

### Retry Automático

```
Tentativa 1 (0s) ──→ Falha
Aguarda 2s
Tentativa 2 (2s) ──→ Falha  
Aguarda 4s
Tentativa 3 (6s) ──→ Falha
Marca como FAILED
```

### Idempotência

```
Chamada 1: Cria job → Processa
Chamada 2: Detecta job ativo → Retorna (sem criar novo)
Chamada 3: Processo completo → Regenera links S3 → Retorna
```

---

## 🛠️ Troubleshooting

### Problema: Webhook não está sendo enviado
**Solução:**
1. Verificar logs: `tail -f logs/celery.log | grep webhook`
2. Validar URL: `POST /webhooks/webhook-validate`
3. Testar conectividade: `POST /webhooks/webhook-test-connectivity`

### Problema: Documentos ficam em PROCESSING
**Solução:**
1. Verificar Celery worker: `ps aux | grep celery`
2. Ver logs: `tail -f logs/celery.log`
3. Reiniciar: `./start-dev-complete.sh`

### Problema: Links S3 expirados
**Solução:**
- Chamar GET novamente → Regenera automaticamente
- Ou consultar `/status` → Gera novos links

---

## 📞 Endpoints Principais

```
GET  /processes/{numero}                        # Consultar (inicia download)
GET  /processes/{numero}/status                 # Ver progresso
POST /processes/{numero}/download-documents     # Registrar metadados
POST /processes/{numero}/download-document/{id} # Baixar individual

POST /webhooks/webhook-validate                 # Validar webhook URL
POST /webhooks/webhook-send-test                # Testar webhook
POST /webhooks/webhook-test-receiver            # Receptor de teste
```

---

## 📋 Logs

### Ver Logs da API
```bash
tail -f logs/api.log
```

### Ver Logs do Celery
```bash
tail -f logs/celery.log
```

### Filtrar por Processo
```bash
tail -f logs/celery.log | grep "NUMERO-DO-PROCESSO"
```

---

## 🎉 Sistema Completo e Funcional!

✅ Download automático  
✅ Webhook callback  
✅ Retry automático (3x)  
✅ Idempotência  
✅ Monitoramento  
✅ S3 storage  
✅ Logs detalhados  

**Pronto para uso em produção!** 🚀

