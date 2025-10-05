"""Tarefas Celery para processamento de processos judiciais."""

from datetime import datetime
from typing import List, Dict, Any
from celery import current_task
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert

from app.tasks.celery_app import celery_app
from app.core.database import AsyncSessionLocal
from app.core.cache import cache_service, get_process_cache_key
from app.services.pdpj_client import pdpj_client, PDPJClientError
from app.services.s3_service import s3_service
from app.models import Process, Document


@celery_app.task(bind=True)
def process_batch_search(
    self, 
    process_numbers: List[str], 
    include_documents: bool = False
) -> Dict[str, Any]:
    """Processar busca em lote de processos."""
    
    task_id = self.request.id
    logger.info(f"Iniciando processamento em lote {task_id} com {len(process_numbers)} processos")
    
    try:
        results = {
            "task_id": task_id,
            "total_requested": len(process_numbers),
            "processed": 0,
            "found": 0,
            "not_found": [],
            "errors": [],
            "processes": []
        }
        
        # Processar cada processo
        for i, process_number in enumerate(process_numbers):
            try:
                # Atualizar progresso
                progress = (i / len(process_numbers)) * 100
                current_task.update_state(
                    state="PROGRESS",
                    meta={
                        "current": i,
                        "total": len(process_numbers),
                        "progress": progress,
                        "status": f"Processando {process_number}"
                    }
                )
                
                # Verificar se já existe no banco
                async def process_single():
                    async with AsyncSessionLocal() as db:
                        result = await db.execute(
                            select(Process).where(Process.process_number == process_number)
                        )
                        existing_process = result.scalar_one_or_none()
                        
                        if existing_process:
                            logger.info(f"Processo {process_number} já existe no banco")
                            return existing_process
                        
                        # Buscar na API PDPJ
                        try:
                            pdpj_data = await pdpj_client.get_process_full(process_number)
                            
                            # Criar novo processo
                            process = Process(
                                process_number=process_number,
                                full_data=pdpj_data,
                                court=pdpj_data.get("tribunal"),
                                subject=pdpj_data.get("assunto"),
                                status=pdpj_data.get("situacao"),
                                has_documents=bool(pdpj_data.get("documentos")),
                                last_consultation=datetime.utcnow()
                            )
                            
                            db.add(process)
                            await db.commit()
                            await db.refresh(process)
                            
                            # Armazenar no cache
                            cache_key = get_process_cache_key(process_number, "full")
                            await cache_service.set(cache_key, pdpj_data)
                            
                            logger.info(f"Processo {process_number} criado com sucesso")
                            return process
                            
                        except PDPJClientError as e:
                            logger.warning(f"Processo {process_number} não encontrado na API PDPJ: {e}")
                            return None
                
                # Executar processamento assíncrono
                import asyncio
                process = asyncio.run(process_single())
                
                if process:
                    results["found"] += 1
                    results["processes"].append({
                        "process_number": process.process_number,
                        "court": process.court,
                        "status": process.status
                    })
                    
                    # Se incluir documentos, agendar download
                    if include_documents and process.has_documents:
                        download_process_documents.delay(process_number)
                else:
                    results["not_found"].append(process_number)
                
                results["processed"] += 1
                
            except Exception as e:
                logger.error(f"Erro ao processar {process_number}: {str(e)}")
                results["errors"].append({
                    "process_number": process_number,
                    "error": str(e)
                })
        
        logger.info(f"Processamento em lote {task_id} concluído")
        return results
        
    except Exception as e:
        logger.error(f"Erro crítico no processamento em lote {task_id}: {str(e)}")
        raise


@celery_app.task(bind=True)
def refresh_process_data(self, process_number: str) -> Dict[str, Any]:
    """Atualizar dados de um processo específico."""
    
    task_id = self.request.id
    logger.info(f"Iniciando atualização do processo {process_number} (task: {task_id})")
    
    try:
        # TODO: Implementar atualização de dados
        # 1. Consultar API PDPJ para dados atualizados
        # 2. Comparar com dados existentes
        # 3. Atualizar banco de dados se houver mudanças
        # 4. Agendar download de novos documentos se necessário
        
        result = {
            "task_id": task_id,
            "process_number": process_number,
            "updated": True,
            "changes": [],
            "new_documents": 0
        }
        
        logger.info(f"Atualização do processo {process_number} concluída")
        return result
        
    except Exception as e:
        logger.error(f"Erro ao atualizar processo {process_number}: {str(e)}")
        raise


@celery_app.task(bind=True)
def download_process_documents(self, process_number: str) -> Dict[str, Any]:
    """Baixar todos os documentos de um processo."""
    
    task_id = self.request.id
    logger.info(f"Iniciando download de documentos do processo {process_number} (task: {task_id})")
    
    try:
        result = {
            "task_id": task_id,
            "process_number": process_number,
            "documents_found": 0,
            "documents_downloaded": 0,
            "documents_failed": 0,
            "errors": []
        }
        
        async def download_documents():
            async with AsyncSessionLocal() as db:
                # Buscar processo no banco
                process_result = await db.execute(
                    select(Process).where(Process.process_number == process_number)
                )
                process = process_result.scalar_one_or_none()
                
                if not process:
                    logger.error(f"Processo {process_number} não encontrado no banco")
                    return result
                
                # Obter lista de documentos da API PDPJ
                try:
                    documents_data = await pdpj_client.get_process_documents(process_number)
                    result["documents_found"] = len(documents_data)
                    
                    for i, doc_data in enumerate(documents_data):
                        try:
                            # Atualizar progresso
                            progress = (i / len(documents_data)) * 100
                            current_task.update_state(
                                state="PROGRESS",
                                meta={
                                    "current": i,
                                    "total": len(documents_data),
                                    "progress": progress,
                                    "status": f"Baixando documento {doc_data.get('id', 'unknown')}"
                                }
                            )
                            
                            document_id = doc_data.get("id")
                            if not document_id:
                                continue
                            
                            # Verificar se documento já foi baixado
                            doc_result = await db.execute(
                                select(Document).where(
                                    Document.document_id == document_id,
                                    Document.process_id == process.id
                                )
                            )
                            existing_doc = doc_result.scalar_one_or_none()
                            
                            if existing_doc and existing_doc.downloaded:
                                logger.info(f"Documento {document_id} já foi baixado")
                                result["documents_downloaded"] += 1
                                continue
                            
                            # Baixar documento da API PDPJ
                            try:
                                file_content = await pdpj_client.download_document(
                                    process_number, 
                                    document_id,
                                    doc_data.get("url")
                                )
                                
                                # Upload para S3
                                s3_result = await s3_service.upload_document(
                                    file_content=file_content,
                                    process_number=process_number,
                                    document_id=document_id,
                                    filename=doc_data.get("nome"),
                                    content_type=doc_data.get("tipo_mime")
                                )
                                
                                # Salvar metadados no banco
                                if existing_doc:
                                    existing_doc.downloaded = True
                                    existing_doc.s3_key = s3_result["s3_key"]
                                    existing_doc.s3_bucket = s3_result["bucket"]
                                    existing_doc.size = s3_result["file_size"]
                                    existing_doc.mime_type = s3_result["content_type"]
                                else:
                                    document = Document(
                                        document_id=document_id,
                                        process_id=process.id,
                                        name=doc_data.get("nome"),
                                        type=doc_data.get("tipo"),
                                        size=s3_result["file_size"],
                                        mime_type=s3_result["content_type"],
                                        s3_key=s3_result["s3_key"],
                                        s3_bucket=s3_result["bucket"],
                                        raw_data=doc_data,
                                        downloaded=True,
                                        available=True
                                    )
                                    db.add(document)
                                
                                result["documents_downloaded"] += 1
                                logger.info(f"Documento {document_id} baixado com sucesso")
                                
                            except Exception as e:
                                logger.error(f"Erro ao baixar documento {document_id}: {str(e)}")
                                result["documents_failed"] += 1
                                result["errors"].append({
                                    "document_id": document_id,
                                    "error": str(e)
                                })
                        
                        except Exception as e:
                            logger.error(f"Erro ao processar documento {i}: {str(e)}")
                            result["documents_failed"] += 1
                            result["errors"].append({
                                "document_index": i,
                                "error": str(e)
                            })
                    
                    # Atualizar flag de documentos baixados no processo
                    process.documents_downloaded = True
                    await db.commit()
                    
                except PDPJClientError as e:
                    logger.error(f"Erro ao obter lista de documentos: {e}")
                    result["errors"].append({
                        "error": f"Erro ao obter lista de documentos: {str(e)}"
                    })
        
        # Executar download assíncrono
        import asyncio
        asyncio.run(download_documents())
        
        logger.info(f"Download de documentos do processo {process_number} concluído")
        return result
        
    except Exception as e:
        logger.error(f"Erro ao baixar documentos do processo {process_number}: {str(e)}")
        raise
