# 🗺️ Roadmap Detalhado: Implementação Completa da Nova Regra de Negócio

**Versão:** 1.0  
**Data:** 2025-10-06  
**Objetivo:** Sistema de download assíncrono com webhook opcional

---

## 📋 FASE 1: Preparação e Modelos (Estimativa: 2h)

### Passo 1.1: Criar Enum de Status de Documento
**Arquivo:** `app/models/document.py`

**Ação:** Adicionar enum antes da classe Document
```python
from enum import Enum

class DocumentStatus(str, Enum):
    """Status do processamento de documento."""
    PENDING = "pending"           # Aguardando download (com webhook)
    PROCESSING = "processing"     # Download em andamento
    AVAILABLE = "available"       # Disponível no S3
    FAILED = "failed"            # Falha no download/upload
```

**Teste:**
```bash
./venv/bin/python -c "from app.models.document import DocumentStatus; print(list(DocumentStatus))"
```

**Resultado esperado:** Lista com 4 status

---

### Passo 1.2: Adicionar Campos ao Modelo Document
**Arquivo:** `app/models/document.py`

**Ação:** Adicionar após o campo `available`:
```python
from sqlalchemy import Enum as SQLEnum

# Dentro da classe Document, adicionar:
status: Mapped[str] = mapped_column(
    SQLEnum(DocumentStatus),
    default=DocumentStatus.PENDING,
    nullable=False
)
error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
download_started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
download_completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
```

**Teste:**
```bash
./venv/bin/python -c "from app.models.document import Document; print(Document.__table__.columns.keys())"
```

**Resultado esperado:** Deve incluir 'status', 'error_message', 'download_started_at', 'download_completed_at'

---

### Passo 1.3: Criar Modelo ProcessJob
**Arquivo:** Criar `app/models/process_job.py`

**Conteúdo completo:**
```python
"""Modelo para tracking de jobs de download de processos."""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, DateTime, BigInteger, ForeignKey, Integer, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from enum import Enum

from app.core.database import Base


class JobStatus(str, Enum):
    """Status do job de processamento."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ProcessJob(Base):
    """Modelo para tracking de jobs de download de processos."""
    
    __tablename__ = "process_jobs"
    __table_args__ = {"schema": "pdpj"}
    
    # Identificação
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    job_id: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    
    # Relacionamento com processo
    process_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("pdpj.processes.id"), nullable=False)
    process: Mapped["Process"] = relationship("Process", back_populates="jobs")
    
    # Webhook
    webhook_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    webhook_sent: Mapped[bool] = mapped_column(default=False, nullable=False)
    webhook_sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    webhook_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    webhook_last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Status e progresso
    status: Mapped[str] = mapped_column(String(20), default=JobStatus.PENDING.value, nullable=False)
    total_documents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completed_documents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_documents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    progress_percentage: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Metadados
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    def update_progress(self):
        """Atualizar porcentagem de progresso."""
        if self.total_documents > 0:
            self.progress_percentage = (self.completed_documents / self.total_documents) * 100
```

**Teste:**
```bash
./venv/bin/python -c "from app.models.process_job import ProcessJob, JobStatus; print('OK')"
```

---

### Passo 1.4: Atualizar Modelo Process
**Arquivo:** `app/models/process.py`

**Ação:** Adicionar relationship:
```python
# Dentro da classe Process, adicionar:
jobs: Mapped[List["ProcessJob"]] = relationship("ProcessJob", back_populates="process")
```

---

### Passo 1.5: Atualizar __init__ dos Models
**Arquivo:** `app/models/__init__.py`

**Ação:** Adicionar import:
```python
from app.models.process_job import ProcessJob, JobStatus
from app.models.document import Document, DocumentStatus

# Atualizar __all__
__all__ = ["User", "Process", "Document", "ProcessJob", "DocumentStatus", "JobStatus"]
```

**Teste:**
```bash
./venv/bin/python -c "from app.models import ProcessJob, JobStatus, DocumentStatus; print('OK')"
```

---

### Passo 1.6: Criar Migration
**Comando:**
```bash
alembic revision --autogenerate -m "Add document status and process job tracking"
```

**Verificar:** Revisar arquivo gerado em `alembic/versions/`

**Executar:**
```bash
alembic upgrade head
```

**Teste:**
```bash
# Verificar que tabela foi criada
./venv/bin/python -c "
import asyncio
from app.core.database import engine
from sqlalchemy import text

async def check():
    async with engine.begin() as conn:
        result = await conn.execute(text(
            \"SELECT table_name FROM information_schema.tables WHERE table_schema='pdpj' AND table_name='process_jobs'\"
        ))
        print('Tabela exists:', result.scalar() is not None)

asyncio.run(check())
"
```

**Resultado esperado:** `Tabela exists: True`

---

## 📊 FASE 2: Endpoint de Status (Estimativa: 1h)

### Passo 2.1: Criar Schema de Resposta
**Arquivo:** Criar `app/schemas/process_status.py`

**Conteúdo:**
```python
"""Schemas para status de processamento de processos."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class DocumentStatusResponse(BaseModel):
    """Status de um documento individual."""
    id: str
    uuid: str
    name: str
    status: str  # pending, processing, available, failed
    size: Optional[int] = None
    download_url: Optional[str] = None
    error_message: Optional[str] = None
    progress: Optional[float] = None


class ProcessStatusResponse(BaseModel):
    """Status completo do processamento de um processo."""
    process_number: str
    status: str  # pending, processing, completed, failed
    total_documents: int
    completed_documents: int
    failed_documents: int
    progress_percentage: float
    documents: List[DocumentStatusResponse]
    job_id: Optional[str] = None
    webhook_url: Optional[str] = None
    webhook_sent: bool = False
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
```

**Teste:**
```bash
./venv/bin/python -c "from app.schemas.process_status import ProcessStatusResponse; print('OK')"
```

---

### Passo 2.2: Criar Endpoint GET /{numero}/status
**Arquivo:** `app/api/processes.py`

**Ação:** Adicionar antes do último endpoint:
```python
@router.get("/{process_number}/status", response_model=ProcessStatusResponse)
async def get_process_status(
    process_number: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user_or_admin())
):
    """Obter status de processamento de um processo."""
    try:
        # Buscar processo
        normalized_number = normalize_process_number(process_number)
        result = await db.execute(
            select(Process)
            .where(Process.process_number == normalized_number)
            .options(selectinload(Process.documents), selectinload(Process.jobs))
        )
        process = result.scalar_one_or_none()
        
        if not process:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Processo {process_number} não encontrado"
            )
        
        # Buscar job mais recente
        latest_job = process.jobs[-1] if process.jobs else None
        
        # Contar documentos por status
        total_docs = len(process.documents)
        completed = sum(1 for d in process.documents if d.status == DocumentStatus.AVAILABLE)
        failed = sum(1 for d in process.documents if d.status == DocumentStatus.FAILED)
        processing = sum(1 for d in process.documents if d.status == DocumentStatus.PROCESSING)
        
        # Status geral
        if failed == total_docs:
            overall_status = "failed"
        elif completed == total_docs:
            overall_status = "completed"
        elif processing > 0 or (latest_job and latest_job.status == JobStatus.PROCESSING):
            overall_status = "processing"
        else:
            overall_status = "pending"
        
        # Progresso
        progress = (completed / total_docs * 100) if total_docs > 0 else 0
        
        # Montar documentos
        documents_status = []
        for doc in process.documents:
            # Extrair UUID do hrefBinario
            doc_uuid = doc.document_id
            if doc.raw_data and doc.raw_data.get("hrefBinario"):
                href = doc.raw_data.get("hrefBinario", "")
                parts = href.split("/documentos/")
                if len(parts) == 2:
                    uuid_part = parts[1].split("/")[0]
                    if "-" in uuid_part:
                        doc_uuid = uuid_part
            
            doc_status = {
                "id": doc.document_id,
                "uuid": doc_uuid,
                "name": doc.name,
                "status": doc.status if hasattr(doc, 'status') else ("available" if doc.downloaded else "pending"),
                "size": doc.size,
                "download_url": None,
                "error_message": doc.error_message if hasattr(doc, 'error_message') else None
            }
            
            # Se disponível, gerar URL presignada
            if doc.downloaded and doc.s3_key:
                try:
                    doc_status["download_url"] = await s3_service.generate_presigned_url(
                        doc.s3_key, expiration=3600
                    )
                except Exception as e:
                    doc_status["error_message"] = str(e)
            
            documents_status.append(doc_status)
        
        return ProcessStatusResponse(
            process_number=process_number,
            status=overall_status,
            total_documents=total_docs,
            completed_documents=completed,
            failed_documents=failed,
            progress_percentage=progress,
            documents=documents_status,
            job_id=latest_job.job_id if latest_job else None,
            webhook_url=latest_job.webhook_url if latest_job else None,
            webhook_sent=latest_job.webhook_sent if latest_job else False,
            created_at=latest_job.created_at if latest_job else None,
            started_at=latest_job.started_at if latest_job else None,
            completed_at=latest_job.completed_at if latest_job else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar status: {str(e)}"
        )
```

**Teste:**
```bash
curl -s "http://localhost:8000/api/v1/processes/1011745-77.2025.8.11.0041/status" \
  -H "Authorization: Bearer pdpj_admin_..." | jq '.progress_percentage'
```

**Resultado esperado:** Número entre 0-100

---

## 🔔 FASE 3: Sistema de Webhook (Estimativa: 2h)

### Passo 3.1: Criar Serviço de Webhook
**Arquivo:** Criar `app/services/webhook_service.py`

**Conteúdo completo:**
```python
"""Serviço para envio de webhooks."""

import asyncio
import httpx
from typing import Dict, Any, Optional
from loguru import logger
from datetime import datetime


class WebhookService:
    """Serviço para envio de webhooks com retry."""
    
    def __init__(self):
        self.max_retries = 3
        self.timeout = 30.0
        self.retry_delay = 2.0  # segundos
    
    async def send_webhook(
        self,
        webhook_url: str,
        payload: Dict[str, Any],
        max_retries: Optional[int] = None
    ) -> Dict[str, Any]:
        """Enviar webhook com retry automático."""
        retries = max_retries or self.max_retries
        last_error = None
        
        for attempt in range(1, retries + 1):
            try:
                logger.info(f"📤 Enviando webhook (tentativa {attempt}/{retries}): {webhook_url}")
                
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        webhook_url,
                        json=payload,
                        headers={
                            "Content-Type": "application/json",
                            "User-Agent": "PDPJ-API-Webhook/1.0",
                            "X-Webhook-Timestamp": datetime.utcnow().isoformat(),
                            "X-Webhook-Attempt": str(attempt)
                        }
                    )
                    
                    if 200 <= response.status_code < 300:
                        logger.info(f"✅ Webhook enviado com sucesso: {response.status_code}")
                        return {
                            "success": True,
                            "status_code": response.status_code,
                            "attempt": attempt,
                            "timestamp": datetime.utcnow().isoformat()
                        }
                    else:
                        last_error = f"HTTP {response.status_code}: {response.text[:200]}"
                        logger.warning(f"⚠️ Webhook retornou {response.status_code}")
                        
            except httpx.TimeoutException:
                last_error = f"Timeout após {self.timeout}s"
                logger.warning(f"⏰ Timeout no webhook (tentativa {attempt})")
                
            except Exception as e:
                last_error = str(e)
                logger.error(f"❌ Erro no webhook: {e}")
            
            # Aguardar antes de retry (exceto na última tentativa)
            if attempt < retries:
                await asyncio.sleep(self.retry_delay * attempt)  # Backoff progressivo
        
        # Todas as tentativas falharam
        logger.error(f"❌ Webhook falhou após {retries} tentativas: {last_error}")
        return {
            "success": False,
            "error": last_error,
            "attempts": retries,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def validate_webhook_url(self, url: str) -> bool:
        """Validar formato de URL do webhook."""
        if not url:
            return False
        
        # Validações básicas
        if not url.startswith(('http://', 'https://')):
            return False
        
        # Recomendação: apenas HTTPS em produção
        if url.startswith('http://') and not url.startswith('http://localhost'):
            logger.warning(f"⚠️ Webhook usando HTTP (inseguro): {url}")
        
        return True


# Instância global
webhook_service = WebhookService()
```

**Teste:**
```bash
./venv/bin/python -c "from app.services.webhook_service import webhook_service; print(webhook_service.validate_webhook_url('https://example.com/webhook'))"
```

**Resultado esperado:** `True`

---

### Passo 3.2: Criar Endpoint de Teste de Webhook
**Arquivo:** Criar `app/api/webhooks.py`

**Conteúdo:**
```python
"""Endpoints para testes de webhook."""

from fastapi import APIRouter, Request
from loguru import logger

router = APIRouter(tags=["webhooks"])


@router.post("/webhook-test")
async def webhook_test_endpoint(request: Request):
    """Endpoint de teste para receber webhooks."""
    try:
        payload = await request.json()
        logger.info(f"📥 Webhook recebido: {payload.keys()}")
        
        return {
            "received": True,
            "process_number": payload.get("process_number"),
            "total_documents": payload.get("total_documents"),
            "message": "Webhook recebido com sucesso"
        }
    except Exception as e:
        logger.error(f"❌ Erro ao processar webhook: {e}")
        return {"error": str(e)}, 400
```

**Registrar router em `app/main.py`:**
```python
from app.api import webhooks

app.include_router(webhooks.router, prefix="/api/v1/webhooks")
```

**Teste:**
```bash
curl -X POST "http://localhost:8000/api/v1/webhooks/webhook-test" \
  -H "Content-Type: application/json" \
  -d '{"process_number": "test", "total_documents": 10}' | jq '.'
```

**Resultado esperado:** `"received": true`

---

## ⚡ FASE 4: Download Assíncrono na Consulta (Estimativa: 4h)

### Passo 4.1: Modificar GET /{numero}
**Arquivo:** `app/api/processes.py`

**Ação:** Substituir o endpoint existente:
```python
@router.get("/{process_number}", response_model=ProcessResponse)
async def get_process(
    process_number: str,
    webhook_url: Optional[str] = None,  # NOVO: Webhook opcional
    auto_download: bool = True,          # NOVO: Controle de download automático
    force_refresh: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user_or_admin())
):
    """Obter dados de um processo e iniciar download assíncrono de documentos."""
    try:
        # 1. Buscar/criar processo (lógica existente mantida)
        normalized_number = normalize_process_number(process_number)
        result = await db.execute(
            select(Process).where(Process.process_number == normalized_number)
        )
        process = result.scalar_one_or_none()
        
        if not process:
            # Buscar na API PDPJ
            pdpj_data = await pdpj_client.get_process_full(process_number)
            process = Process(
                process_number=normalized_number,
                full_data=pdpj_data,
                court=pdpj_data.get("siglaTribunal"),
                subject=pdpj_data.get("tramitacoes", [{}])[0].get("assunto", [{}])[0].get("descricao") if pdpj_data.get("tramitacoes") else None,
                status=pdpj_data.get("tramitacaoAtual", {}).get("descricao"),
                has_documents=bool(pdpj_data.get("documentos"))
            )
            db.add(process)
            await db.commit()
            await db.refresh(process)
        
        # 2. NOVO: Se auto_download=true, iniciar download assíncrono
        if auto_download and process.has_documents:
            from app.tasks.download_tasks import download_process_documents_async
            
            # Validar webhook_url se fornecido
            if webhook_url:
                from app.services.webhook_service import webhook_service
                if not webhook_service.validate_webhook_url(webhook_url):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Webhook URL inválida: {webhook_url}"
                    )
            
            # Agendar download assíncrono
            job = download_process_documents_async.delay(
                process.id,
                process_number,
                webhook_url
            )
            
            logger.info(f"🚀 Download assíncrono agendado: Job {job.id}")
            
            # Registrar job no banco
            process_job = ProcessJob(
                job_id=job.id,
                process_id=process.id,
                webhook_url=webhook_url,
                total_documents=len(process.documents) if process.documents else 0,
                status=JobStatus.PENDING.value
            )
            db.add(process_job)
            await db.commit()
        
        return ProcessResponse.model_validate(process)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar processo: {str(e)}"
        )
```

---

### Passo 4.2: Criar Celery Task de Download Assíncrono
**Arquivo:** Criar `app/tasks/download_tasks.py`

**Conteúdo completo:**
```python
"""Tasks Celery para download assíncrono de documentos."""

import asyncio
from typing import Optional
from datetime import datetime
from loguru import logger
from celery import Task

from app.core.celery_app import celery_app
from app.core.database import get_db
from app.models import Process, Document, ProcessJob
from app.models.document import DocumentStatus
from app.models.process_job import JobStatus
from app.services.pdpj_client import pdpj_client
from app.services.s3_service import s3_service
from app.services.webhook_service import webhook_service
from sqlalchemy import select, update


@celery_app.task(bind=True, name="download_process_documents_async")
def download_process_documents_async(
    self: Task,
    process_id: int,
    process_number: str,
    webhook_url: Optional[str] = None
) -> Dict[str, Any]:
    """Download assíncrono de todos os documentos de um processo."""
    
    async def download_task():
        async for db in get_db():
            try:
                logger.info(f"🚀 Iniciando download assíncrono para processo {process_number}")
                
                # 1. Buscar job e processo
                job_result = await db.execute(
                    select(ProcessJob).where(ProcessJob.job_id == self.request.id)
                )
                job = job_result.scalar_one_or_none()
                
                process_result = await db.execute(
                    select(Process).where(Process.id == process_id)
                )
                process = process_result.scalar_one_or_none()
                
                if not process or not job:
                    return {"success": False, "error": "Processo ou job não encontrado"}
                
                # 2. Atualizar job status
                await db.execute(
                    update(ProcessJob).where(ProcessJob.id == job.id).values(
                        status=JobStatus.PROCESSING.value,
                        started_at=datetime.utcnow()
                    )
                )
                await db.commit()
                
                # 3. Buscar documentos
                docs_result = await db.execute(
                    select(Document).where(Document.process_id == process.id)
                )
                documents = docs_result.scalars().all()
                
                total = len(documents)
                completed = 0
                failed = 0
                
                # 4. Atualizar total no job
                await db.execute(
                    update(ProcessJob).where(ProcessJob.id == job.id).values(
                        total_documents=total
                    )
                )
                await db.commit()
                
                # 5. Processar documentos em lotes
                batch_size = 5
                for i in range(0, len(documents), batch_size):
                    batch = documents[i:i + batch_size]
                    
                    for doc in batch:
                        try:
                            # Atualizar status do documento
                            await db.execute(
                                update(Document).where(Document.id == doc.id).values(
                                    status=DocumentStatus.PROCESSING.value,
                                    download_started_at=datetime.utcnow()
                                )
                            )
                            await db.commit()
                            
                            # Extrair hrefBinario
                            href_binario = doc.raw_data.get("hrefBinario") if doc.raw_data else None
                            if not href_binario:
                                raise Exception("hrefBinario não encontrado")
                            
                            # Download do PDPJ
                            download_result = await pdpj_client.download_document(href_binario, doc.name)
                            
                            if not download_result.get('is_valid'):
                                raise Exception("Download inválido")
                            
                            # Ler arquivo
                            with open(download_result['saved_path'], 'rb') as f:
                                content = f.read()
                            
                            # Upload para S3
                            s3_key = f"processos/{process_number}/documentos/{doc.document_id}/{doc.name}"
                            await s3_service.upload_document(
                                file_content=content,
                                process_number=process_number,
                                document_id=doc.document_id,
                                filename=doc.name,
                                content_type=doc.mime_type or "application/pdf"
                            )
                            
                            # Gerar URL presignada
                            download_url = await s3_service.generate_presigned_url(s3_key, expiration=3600)
                            
                            # Atualizar documento como disponível
                            await db.execute(
                                update(Document).where(Document.id == doc.id).values(
                                    status=DocumentStatus.AVAILABLE.value,
                                    downloaded=True,
                                    s3_key=s3_key,
                                    s3_bucket=s3_service.bucket_name,
                                    download_url=download_url,
                                    size=len(content),
                                    download_completed_at=datetime.utcnow(),
                                    error_message=None
                                )
                            )
                            
                            completed += 1
                            logger.info(f"✅ {doc.name} baixado ({completed}/{total})")
                            
                        except Exception as e:
                            # Marcar como falha
                            await db.execute(
                                update(Document).where(Document.id == doc.id).values(
                                    status=DocumentStatus.FAILED.value,
                                    error_message=str(e),
                                    download_completed_at=datetime.utcnow()
                                )
                            )
                            failed += 1
                            logger.error(f"❌ Falha em {doc.name}: {e}")
                        
                        # Atualizar progresso do job
                        progress = ((completed + failed) / total) * 100
                        await db.execute(
                            update(ProcessJob).where(ProcessJob.id == job.id).values(
                                completed_documents=completed,
                                failed_documents=failed,
                                progress_percentage=progress
                            )
                        )
                        await db.commit()
                        
                        # Atualizar estado da task no Celery
                        self.update_state(
                            state='PROGRESS',
                            meta={
                                'current': completed + failed,
                                'total': total,
                                'progress': progress
                            }
                        )
                    
                    # Pequena pausa entre lotes
                    await asyncio.sleep(1)
                
                # 6. Marcar job como completo
                final_status = JobStatus.COMPLETED.value if failed == 0 else JobStatus.FAILED.value
                await db.execute(
                    update(ProcessJob).where(ProcessJob.id == job.id).values(
                        status=final_status,
                        completed_at=datetime.utcnow()
                    )
                )
                await db.commit()
                
                # 7. Enviar webhook se fornecido
                if webhook_url and completed > 0:
                    logger.info(f"📤 Enviando callback para webhook: {webhook_url}")
                    
                    # Montar payload completo
                    payload = {
                        "process_number": process_number,
                        "job_id": self.request.id,
                        "status": final_status,
                        "total_documents": total,
                        "completed_documents": completed,
                        "failed_documents": failed,
                        "documents": [],
                        "completed_at": datetime.utcnow().isoformat()
                    }
                    
                    # Adicionar documentos com links
                    docs_final = await db.execute(
                        select(Document).where(Document.process_id == process.id)
                    )
                    for doc in docs_final.scalars().all():
                        # Extrair UUID
                        doc_uuid = doc.document_id
                        if doc.raw_data and doc.raw_data.get("hrefBinario"):
                            href = doc.raw_data.get("hrefBinario", "")
                            parts = href.split("/documentos/")
                            if len(parts) == 2:
                                uuid_part = parts[1].split("/")[0]
                                if "-" in uuid_part:
                                    doc_uuid = uuid_part
                        
                        doc_data = {
                            "id": doc.document_id,
                            "uuid": doc_uuid,
                            "name": doc.name,
                            "type": doc.type,
                            "size": doc.size,
                            "status": doc.status,
                            "download_url": doc.download_url if doc.downloaded else None,
                            "error_message": doc.error_message
                        }
                        payload["documents"].append(doc_data)
                    
                    # Enviar webhook
                    webhook_result = await webhook_service.send_webhook(webhook_url, payload)
                    
                    # Atualizar job com resultado do webhook
                    await db.execute(
                        update(ProcessJob).where(ProcessJob.id == job.id).values(
                            webhook_sent=webhook_result.get('success', False),
                            webhook_sent_at=datetime.utcnow() if webhook_result.get('success') else None,
                            webhook_attempts=webhook_result.get('attempts', 0),
                            webhook_last_error=webhook_result.get('error')
                        )
                    )
                    await db.commit()
                
                return {
                    "success": True,
                    "process_number": process_number,
                    "total": total,
                    "completed": completed,
                    "failed": failed,
                    "webhook_sent": webhook_url is not None and webhook_result.get('success', False)
                }
                
            except Exception as e:
                logger.error(f"❌ Erro na task de download: {e}")
                
                # Marcar job como failed
                if job:
                    await db.execute(
                        update(ProcessJob).where(ProcessJob.id == job.id).values(
                            status=JobStatus.FAILED.value,
                            error_message=str(e),
                            completed_at=datetime.utcnow()
                        )
                    )
                    await db.commit()
                
                raise
            
            finally:
                break
    
    return asyncio.run(download_task())
```

**Teste:**
```bash
# Aguardar execução da task
celery -A app.core.celery_app flower
# Verificar em http://localhost:5555
```

---

### Passo 4.3: Registrar Import da Task
**Arquivo:** `app/tasks/__init__.py`

**Adicionar:**
```python
from app.tasks.download_tasks import download_process_documents_async

__all__ = [..., "download_process_documents_async"]
```

---

## 📈 FASE 5: Gerenciamento de Status (Estimativa: 2h)

### Passo 5.1: Helper de Transição de Status
**Arquivo:** Criar `app/utils/status_manager.py`

**Conteúdo:**
```python
"""Gerenciador de transições de status de documentos."""

from app.models.document import DocumentStatus
from app.models.process_job import JobStatus


class StatusManager:
    """Gerenciar transições de status."""
    
    @staticmethod
    def get_initial_document_status(has_webhook: bool) -> DocumentStatus:
        """Status inicial do documento baseado em webhook."""
        return DocumentStatus.PENDING if has_webhook else DocumentStatus.PROCESSING
    
    @staticmethod
    def can_transition_to(current: DocumentStatus, target: DocumentStatus) -> bool:
        """Verificar se transição de status é válida."""
        valid_transitions = {
            DocumentStatus.PENDING: [DocumentStatus.PROCESSING, DocumentStatus.FAILED],
            DocumentStatus.PROCESSING: [DocumentStatus.AVAILABLE, DocumentStatus.FAILED],
            DocumentStatus.AVAILABLE: [],  # Estado final
            DocumentStatus.FAILED: [DocumentStatus.PROCESSING]  # Pode retry
        }
        
        return target in valid_transitions.get(current, [])


status_manager = StatusManager()
```

**Teste:**
```bash
./venv/bin/python -c "
from app.utils.status_manager import status_manager
from app.models.document import DocumentStatus
print(status_manager.can_transition_to(DocumentStatus.PENDING, DocumentStatus.PROCESSING))
"
```

**Resultado esperado:** `True`

---

## 🔄 FASE 6: Idempotência (Estimativa: 2h)

### Passo 6.1: Verificar Job Existente
**Arquivo:** `app/api/processes.py`

**Ação:** Adicionar no `get_process` antes de criar novo job:
```python
# Verificar se já existe job em andamento
existing_job = await db.execute(
    select(ProcessJob).where(
        ProcessJob.process_id == process.id,
        ProcessJob.status.in_([JobStatus.PENDING.value, JobStatus.PROCESSING.value])
    ).order_by(ProcessJob.created_at.desc())
)
active_job = existing_job.scalar_one_or_none()

if active_job:
    logger.info(f"♻️ Job já existe: {active_job.job_id} (status: {active_job.status})")
    # Retornar sem criar novo job
    return ProcessResponse.model_validate(process)
```

---

## 🛡️ FASE 7: Tratamento de Erros (Estimativa: 2-3h)

### Passo 7.1: Retry de Downloads com Backoff
**Arquivo:** `app/tasks/download_tasks.py`

**Modificar:** Adicionar retry no loop de documentos:
```python
max_retries = 3
for retry in range(max_retries):
    try:
        download_result = await pdpj_client.download_document(href_binario, doc.name)
        break  # Sucesso, sair do loop
    except Exception as e:
        if retry < max_retries - 1:
            await asyncio.sleep(2 ** retry)  # Backoff exponencial
            continue
        else:
            raise  # Última tentativa falhou
```

---

## 🔒 FASE 8: Segurança (Estimativa: 1-2h)

### Passo 8.1: Whitelist de Webhooks (Opcional)
**Arquivo:** `app/core/config.py`

**Adicionar:**
```python
webhook_allowed_domains: Set[str] = Field(
    default_factory=lambda: {"*"},  # Todos permitidos por padrão
    description="Domínios permitidos para webhooks"
)
```

---

## 📚 FASE 9: Documentação (Estimativa: 1h)

### Passo 9.1: Atualizar README.md
**Adicionar seção:**
```markdown
### Download Assíncrono com Webhook

```bash
# Com webhook (recebe callback quando completo)
curl "http://localhost:8000/api/v1/processes/1011745-77.2025.8.11.0041?webhook_url=https://seu-servidor.com/callback"

# Sem webhook (consultar status manualmente)
curl "http://localhost:8000/api/v1/processes/1011745-77.2025.8.11.0041"

# Verificar status
curl "http://localhost:8000/api/v1/processes/1011745-77.2025.8.11.0041/status"
```
```

---

## 🧪 FASE 10: Testes E2E (Estimativa: 2-3h)

### Passo 10.1: Teste Completo com Webhook
**Arquivo:** Criar `tests/test_async_download_webhook.py`

**Conteúdo:**
```python
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.integration
@pytest.mark.asyncio
async def test_download_with_webhook():
    """Testar download assíncrono com webhook."""
    # 1. Criar servidor webhook de teste
    # 2. Consultar processo com webhook_url
    # 3. Aguardar job completar
    # 4. Verificar que webhook foi chamado
    # 5. Validar payload recebido
    pass
```

---

## 📊 Checklist de Implementação

### FASE 1: Modelos
- [ ] 1.1 Enum DocumentStatus
- [ ] 1.2 Campos em Document
- [ ] 1.3 Modelo ProcessJob
- [ ] 1.4 Relationship em Process
- [ ] 1.5 Atualizar __init__
- [ ] 1.6 Migration
- [ ] ✅ TESTE FASE 1

### FASE 2: Endpoint Status
- [ ] 2.1 Schema ProcessStatusResponse
- [ ] 2.2 Endpoint GET /status
- [ ] ✅ TESTE FASE 2

### FASE 3: Webhook
- [ ] 3.1 WebhookService
- [ ] 3.2 Endpoint de teste
- [ ] ✅ TESTE FASE 3

### FASE 4: Download Assíncrono
- [ ] 4.1 Modificar GET /{numero}
- [ ] 4.2 Celery Task
- [ ] 4.3 Registrar imports
- [ ] ✅ TESTE FASE 4

### FASE 5: Status Management
- [ ] 5.1 StatusManager
- [ ] ✅ TESTE FASE 5

### FASE 6: Idempotência
- [ ] 6.1 Verificar job existente
- [ ] 6.2 Cache de resultados
- [ ] ✅ TESTE FASE 6

### FASE 7: Erros
- [ ] 7.1 Retry downloads
- [ ] 7.2 Retry webhooks
- [ ] ✅ TESTE FASE 7

### FASE 8: Segurança
- [ ] 8.1 Whitelist webhooks
- [ ] 8.2 Rate limiting
- [ ] ✅ TESTE FASE 8

### FASE 9: Docs
- [ ] 9.1 README
- [ ] 9.2 Postman
- [ ] ✅ TESTE FASE 9

### FASE 10: E2E
- [ ] 10.1 Testes E2E
- [ ] 10.2 Load tests
- [ ] 10.3 Deploy
- [ ] ✅ TESTE FINAL

---

## 🎯 Começar Agora?

**Próximo passo:** FASE 1.1 - Criar Enum DocumentStatus

Confirme para começar a implementação! 🚀

