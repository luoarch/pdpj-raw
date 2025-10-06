"""Tasks Celery para download assíncrono de documentos."""

import asyncio
from typing import Optional, Dict, Any
from datetime import datetime
from loguru import logger
from celery import Task

from app.tasks.celery_app import celery_app
from app.core.database import get_db
from app.models import Process, Document, ProcessJob
from app.models.document import DocumentStatus
from app.models.process_job import JobStatus
from app.services.pdpj_client import pdpj_client
from app.services.s3_service import s3_service
from app.services.webhook_service import webhook_service
from app.utils.status_manager import status_manager
from sqlalchemy import select, update


@celery_app.task(bind=True, name="download_process_documents_async")
def download_process_documents_async(
    self: Task,
    process_id: int,
    process_number: str,
    webhook_url: Optional[str] = None
) -> Dict[str, Any]:
    """
    Download assíncrono de todos os documentos de um processo.
    
    Args:
        self: Task Celery (auto-injetado com bind=True)
        process_id: ID do processo no banco
        process_number: Número do processo (formatado)
        webhook_url: URL para callback (opcional)
        
    Returns:
        Dict com resultado do processamento
    """
    
    async def download_task():
        """Tarefa assíncrona de download."""
        async for db in get_db():
            try:
                logger.info("=" * 80)
                logger.info(f"🚀 INICIANDO DOWNLOAD ASSÍNCRONO")
                logger.info(f"📁 Processo: {process_number}")
                logger.info(f"🆔 Job ID: {self.request.id}")
                logger.info(f"🔔 Webhook: {webhook_url or 'Não configurado'}")
                logger.info("=" * 80)
                
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
                    logger.error(f"❌ Processo ou job não encontrado: process_id={process_id}, job_id={self.request.id}")
                    return {"success": False, "error": "Processo ou job não encontrado"}
                
                logger.info(f"✅ Processo e job encontrados no banco")
                
                # 2. Atualizar job: PENDING → PROCESSING
                await db.execute(
                    update(ProcessJob).where(ProcessJob.id == job.id).values(
                        status=JobStatus.PROCESSING.value,
                        started_at=datetime.utcnow()
                    )
                )
                await db.commit()
                logger.info(f"📊 Job status: PENDING → PROCESSING")
                
                # 3. Buscar documentos
                docs_result = await db.execute(
                    select(Document).where(Document.process_id == process.id)
                )
                documents = docs_result.scalars().all()
                
                total = len(documents)
                completed = 0
                failed = 0
                
                logger.info(f"📄 Total de documentos a processar: {total}")
                
                # 4. Atualizar total no job
                await db.execute(
                    update(ProcessJob).where(ProcessJob.id == job.id).values(
                        total_documents=total
                    )
                )
                await db.commit()
                
                # 5. Processar documentos em lotes
                batch_size = 5
                for batch_num in range(0, len(documents), batch_size):
                    batch = documents[batch_num:batch_num + batch_size]
                    batch_index = batch_num // batch_size + 1
                    
                    logger.info(f"📦 Processando lote {batch_index}: {len(batch)} documentos")
                    
                    for doc in batch:
                        try:
                            # Validar transição de status
                            current_status = DocumentStatus(doc.status) if hasattr(doc, 'status') else DocumentStatus.PENDING
                            can_transition, error = status_manager.can_transition_document(
                                current_status,
                                DocumentStatus.PROCESSING
                            )
                            
                            if not can_transition:
                                logger.warning(f"⚠️ Pulando {doc.name}: {error}")
                                continue
                            
                            # Atualizar status: PENDING/FAILED → PROCESSING
                            await db.execute(
                                update(Document).where(Document.id == doc.id).values(
                                    status=DocumentStatus.PROCESSING.value,
                                    download_started_at=datetime.utcnow()
                                )
                            )
                            await db.commit()
                            
                            logger.info(f"⬇️ Baixando: {doc.name}")
                            
                            # Extrair hrefBinario
                            href_binario = doc.raw_data.get("hrefBinario") if doc.raw_data else None
                            if not href_binario:
                                raise Exception("hrefBinario não encontrado")
                            
                            # Download do PDPJ
                            download_result = await pdpj_client.download_document(href_binario, doc.name)
                            
                            if not download_result.get('is_valid'):
                                raise Exception("Download inválido ou corrompido")
                            
                            # Ler arquivo baixado
                            with open(download_result['saved_path'], 'rb') as f:
                                content = f.read()
                            
                            logger.info(f"📦 Arquivo baixado: {len(content)} bytes")
                            
                            # Upload para S3
                            s3_key = f"processos/{process_number}/documentos/{doc.document_id}/{doc.name}"
                            await s3_service.upload_document(
                                file_content=content,
                                process_number=process_number,
                                document_id=doc.document_id,
                                filename=doc.name,
                                content_type=doc.mime_type or "application/pdf"
                            )
                            
                            logger.info(f"☁️ Upload S3 completo: {s3_key}")
                            
                            # Gerar URL presignada
                            download_url = await s3_service.generate_presigned_url(s3_key, expiration=3600)
                            
                            # Validar transição: PROCESSING → AVAILABLE
                            can_transition, error = status_manager.can_transition_document(
                                DocumentStatus.PROCESSING,
                                DocumentStatus.AVAILABLE
                            )
                            
                            if can_transition:
                                # Atualizar documento: PROCESSING → AVAILABLE
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
                                logger.info(f"✅ {doc.name} completo ({completed}/{total})")
                            else:
                                logger.error(f"❌ Transição inválida ao marcar como AVAILABLE: {error}")
                                raise Exception(f"Erro de transição: {error}")
                            
                        except Exception as e:
                            # Marcar como falha: PROCESSING → FAILED
                            # Verificar transição (pode falhar de PENDING ou PROCESSING)
                            current_doc_status = DocumentStatus(doc.status) if hasattr(doc, 'status') else DocumentStatus.PROCESSING
                            
                            can_transition, trans_error = status_manager.can_transition_document(
                                current_doc_status,
                                DocumentStatus.FAILED
                            )
                            
                            if can_transition:
                                await db.execute(
                                    update(Document).where(Document.id == doc.id).values(
                                        status=DocumentStatus.FAILED.value,
                                        error_message=str(e)[:500],  # Limitar tamanho
                                        download_completed_at=datetime.utcnow()
                                    )
                                )
                            else:
                                # Forçar FAILED mesmo se transição inválida (safety)
                                logger.warning(f"⚠️ Forçando FAILED apesar de transição inválida")
                                await db.execute(
                                    update(Document).where(Document.id == doc.id).values(
                                        status=DocumentStatus.FAILED.value,
                                        error_message=str(e)[:500],
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
                                'progress': progress,
                                'completed': completed,
                                'failed': failed
                            }
                        )
                    
                    # Pequena pausa entre lotes
                    logger.info(f"⏸️ Pausa de 1s antes do próximo lote...")
                    await asyncio.sleep(1)
                
                # 6. Finalizar job
                final_status = JobStatus.COMPLETED.value if failed == 0 else JobStatus.FAILED.value
                await db.execute(
                    update(ProcessJob).where(ProcessJob.id == job.id).values(
                        status=final_status,
                        completed_at=datetime.utcnow()
                    )
                )
                await db.commit()
                
                logger.info("=" * 80)
                logger.info(f"📊 DOWNLOAD FINALIZADO")
                logger.info(f"✅ Completados: {completed}/{total}")
                logger.info(f"❌ Falhas: {failed}/{total}")
                logger.info(f"📊 Status Final: {final_status}")
                logger.info("=" * 80)
                
                # 7. Enviar webhook se configurado E se houver documentos completados
                if webhook_url and completed > 0:
                    logger.info(f"📤 Preparando callback para webhook: {webhook_url}")
                    
                    # Montar payload completo
                    payload = {
                        "process_number": process_number,
                        "job_id": self.request.id,
                        "status": final_status,
                        "total_documents": total,
                        "completed_documents": completed,
                        "failed_documents": failed,
                        "progress_percentage": 100.0 if completed + failed == total else 0.0,
                        "documents": [],
                        "completed_at": datetime.utcnow().isoformat()
                    }
                    
                    # Adicionar documentos com links S3
                    docs_final = await db.execute(
                        select(Document).where(Document.process_id == process.id)
                    )
                    for doc in docs_final.scalars().all():
                        # Extrair UUID do hrefBinario
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
                            "download_url": doc.download_url if doc.downloaded and doc.s3_key else None,
                            "error_message": doc.error_message if hasattr(doc, 'error_message') else None
                        }
                        payload["documents"].append(doc_data)
                    
                    logger.info(f"📦 Payload montado com {len(payload['documents'])} documentos")
                    
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
                    
                    if webhook_result.get('success'):
                        logger.info(f"✅ Webhook enviado com sucesso!")
                    else:
                        logger.error(f"❌ Webhook falhou: {webhook_result.get('error')}")
                else:
                    if not webhook_url:
                        logger.info(f"ℹ️ Webhook não configurado - usar polling manual via /status")
                    elif completed == 0:
                        logger.warning(f"⚠️ Nenhum documento baixado, webhook não será enviado")
                
                return {
                    "success": True,
                    "process_number": process_number,
                    "total": total,
                    "completed": completed,
                    "failed": failed,
                    "webhook_sent": webhook_url is not None and completed > 0 and webhook_result.get('success', False) if webhook_url and completed > 0 else False,
                    "job_id": self.request.id
                }
                
            except Exception as e:
                logger.error(f"❌ ERRO CRÍTICO na task de download: {e}")
                logger.exception(e)
                
                # Marcar job como failed
                if job:
                    try:
                        await db.execute(
                            update(ProcessJob).where(ProcessJob.id == job.id).values(
                                status=JobStatus.FAILED.value,
                                error_message=str(e)[:500],
                                completed_at=datetime.utcnow()
                            )
                        )
                        await db.commit()
                    except Exception as db_error:
                        logger.error(f"❌ Erro ao atualizar job failed: {db_error}")
                
                raise
            
            finally:
                break
    
    # Executar task assíncrona
    return asyncio.run(download_task())

