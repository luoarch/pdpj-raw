# 🔧 Melhorias Aplicadas aos Modelos

## ✅ Document Model

### 1. **Índices Otimizados**
```python
process_id: index=True  # Consultas frequentes por processo
status: index=True      # Filtros por status
download_started_at: index=True  # Ordenação temporal
```

### 2. **Foreign Key com CASCADE**
```python
ForeignKey("pdpj.processes.id", ondelete="CASCADE")
```
- Garante integridade referencial
- Remove documentos órfãos automaticamente

### 3. **Propriedade Computada `is_available`**
```python
@property
def is_available(self) -> bool:
    return self.status == DocumentStatus.AVAILABLE.value
```
- Evita inconsistência entre `available` e `status`
- Fonte única de verdade: `status`
- Substituir `if document.available` por `if document.is_available`

### 4. **Flag `available` → Deprecada**
- Manter por compatibilidade temporária
- Migrar para usar `status` e `is_available`
- Remover em versão futura

---

## ✅ ProcessJob Model

### 1. **Índices Otimizados**
```python
process_id: index=True  # Buscar jobs por processo
job_id: unique=True, index=True  # Lookup por job_id
status: index=True  # Filtrar jobs ativos/completos
```

### 2. **Foreign Key com CASCADE**
```python
ForeignKey("pdpj.processes.id", ondelete="CASCADE")
```

### 3. **Propriedades Computadas**

#### `is_active`
```python
@property
def is_active(self) -> bool:
    return self.status in [JobStatus.PENDING.value, JobStatus.PROCESSING.value]
```
Uso: Verificar se job precisa de atenção

#### `duration_seconds`
```python
@property
def duration_seconds(self) -> Optional[float]:
    if self.started_at and self.completed_at:
        return (self.completed_at - self.started_at).total_seconds()
    elif self.started_at:
        return (datetime.utcnow() - self.started_at).total_seconds()
    return None
```
Uso: Métricas de performance

---

## 📊 Métricas e Monitoramento

### Queries Otimizadas

#### 1. Buscar documentos pendentes de um processo
```python
# Antes (sem índice)
documents = await db.execute(
    select(Document).where(
        Document.process_id == process_id,
        Document.downloaded == False
    )
)

# Depois (com índices)
documents = await db.execute(
    select(Document).where(
        Document.process_id == process_id,  # índice
        Document.status.in_([DocumentStatus.PENDING, DocumentStatus.PROCESSING])  # índice
    )
)
```

#### 2. Buscar jobs ativos
```python
active_jobs = await db.execute(
    select(ProcessJob).where(
        ProcessJob.status.in_([JobStatus.PENDING.value, JobStatus.PROCESSING.value])
    )
)
```

#### 3. Calcular tempo médio de download
```python
completed_jobs = await db.execute(
    select(ProcessJob).where(ProcessJob.status == JobStatus.COMPLETED.value)
)
avg_duration = sum(job.duration_seconds for job in completed_jobs.scalars()) / len(completed_jobs.scalars().all())
```

---

## 🔒 Validações a Implementar

### 1. Webhook URL Validation
**Local:** `app/services/webhook_service.py` (já criado na FASE 3)

```python
def validate_webhook_url(self, url: str) -> bool:
    if not url:
        return False
    
    # Validar formato
    if not url.startswith(('http://', 'https://')):
        return False
    
    # Produção: apenas HTTPS
    if settings.environment == "production" and not url.startswith('https://'):
        raise ValueError("Webhook deve usar HTTPS em produção")
    
    # Opcional: Whitelist de domínios
    if settings.webhook_allowed_domains != {"*"}:
        from urllib.parse import urlparse
        domain = urlparse(url).netloc
        if domain not in settings.webhook_allowed_domains:
            raise ValueError(f"Domínio {domain} não permitido")
    
    return True
```

### 2. Status Transitions Validation
**Local:** `app/utils/status_manager.py` (será criado na FASE 5)

```python
VALID_TRANSITIONS = {
    DocumentStatus.PENDING: [DocumentStatus.PROCESSING, DocumentStatus.FAILED],
    DocumentStatus.PROCESSING: [DocumentStatus.AVAILABLE, DocumentStatus.FAILED],
    DocumentStatus.AVAILABLE: [],  # Final
    DocumentStatus.FAILED: [DocumentStatus.PROCESSING]  # Permite retry
}

def validate_status_transition(current: DocumentStatus, target: DocumentStatus) -> bool:
    if target not in VALID_TRANSITIONS.get(current, []):
        raise ValueError(f"Transição inválida: {current} → {target}")
    return True
```

---

## 📈 Métricas Sugeridas

### Prometheus Metrics
```python
# app/utils/metrics.py
from prometheus_client import Counter, Histogram, Gauge

# Documentos
documents_downloaded = Counter('pdpj_documents_downloaded_total', 'Total de documentos baixados')
documents_failed = Counter('pdpj_documents_failed_total', 'Total de documentos com falha')
download_duration = Histogram('pdpj_download_duration_seconds', 'Tempo de download')

# Jobs
jobs_started = Counter('pdpj_jobs_started_total', 'Total de jobs iniciados')
jobs_completed = Counter('pdpj_jobs_completed_total', 'Total de jobs completados')
jobs_active = Gauge('pdpj_jobs_active', 'Jobs ativos no momento')
job_duration = Histogram('pdpj_job_duration_seconds', 'Tempo total do job')

# Webhooks
webhooks_sent = Counter('pdpj_webhooks_sent_total', 'Webhooks enviados')
webhooks_failed = Counter('pdpj_webhooks_failed_total', 'Webhooks com falha')
```

---

## 🔄 Migration Path

### Sincronizar `available` com `status` (dados existentes)

```python
# Será incluído na migration
# Após adicionar coluna status, sincronizar:
UPDATE pdpj.documents
SET status = CASE
    WHEN downloaded = true THEN 'available'
    ELSE 'pending'
END;
```

---

## ✅ Checklist de Melhorias Aplicadas

- [x] Índices em `process_id`, `status`, `download_started_at` (Document)
- [x] Índices em `process_id`, `job_id`, `status` (ProcessJob)
- [x] Foreign keys com `ondelete="CASCADE"`
- [x] Propriedade `is_available` no Document
- [x] Propriedade `is_active` no ProcessJob
- [x] Propriedade `duration_seconds` no ProcessJob
- [x] Documentação de queries otimizadas
- [x] Documentação de validações a implementar
- [x] Métricas sugeridas

---

## 🚀 Próximos Passos

1. ✅ **Criar migration** com melhorias aplicadas
2. ✅ **Executar migration** no banco
3. ✅ **Testar** que tabelas foram criadas
4. ➡️ **Continuar** FASE 2 (Endpoint de Status)

