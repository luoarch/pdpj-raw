"""Endpoints para consulta de processos judiciais."""

import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from sqlalchemy.orm import selectinload
from loguru import logger

from app.core.database import get_db
from app.core.security import get_current_user, require_user_or_admin
from app.core.cache import cache_service, get_process_cache_key
from app.core.endpoint_rate_limiting import (
    search_processes_rate_limit,
    download_documents_rate_limit,
    batch_search_rate_limit,
    get_process_rate_limit,
    get_files_rate_limit,
    batch_size_limit,
    download_throttle
)
from app.schemas.process import (
    ProcessSearchRequest,
    ProcessSearchResponse,
    ProcessResponse,
    ProcessFilesResponse,
)
from app.schemas.process_status import ProcessStatusResponse, DocumentStatusResponse
from app.models import Process, User, Document, DocumentStatus, ProcessJob, JobStatus
from app.services.pdpj_client import pdpj_client, PDPJClientError
from app.services.session_manager import get_active_session_cookie
from app.services.process_cache_service import process_cache_service
from app.services.webhook_service import webhook_service
from app.utils.file_utils import process_document_download
from app.utils.transaction_manager import TransactionManager, with_transaction
from app.utils.pagination_utils import (
    create_process_pagination_params,
    create_document_pagination_params,
    apply_process_filters,
    apply_document_filters,
    paginate_results,
    ProcessPaginationParams,
    DocumentPaginationParams
)
from app.services.s3_service import s3_service
from app.tasks.process_tasks import process_batch_search
from app.utils.process_utils import normalize_process_number

router = APIRouter(tags=["processes"])


async def _fallback_individual_search(process_numbers: List[str], db: AsyncSession, found_processes: List, not_found: List):
    """Fallback para busca individual quando o cache falha."""
    logger.warning("⚠️ Usando fallback para busca individual")
    
    for process_number in process_numbers:
        try:
            # Buscar no banco primeiro
            normalized_number = normalize_process_number(process_number)
            result = await db.execute(
                select(Process).where(Process.process_number == normalized_number)
            )
            process = result.scalar_one_or_none()
            
            if process:
                found_processes.append(ProcessResponse.model_validate(process))
            else:
                # Buscar na API PDPJ
                try:
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
                    found_processes.append(ProcessResponse.model_validate(process))
                    
                except PDPJClientError:
                    not_found.append(process_number)
                    
        except Exception as e:
            logger.error(f"❌ Erro no fallback para {process_number}: {e}")
            not_found.append(process_number)
    
    await db.commit()


@router.get("", response_model=List[ProcessResponse])
async def list_processes(
    pagination: ProcessPaginationParams = Depends(create_process_pagination_params),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user_or_admin())
):
    """Listar processos com paginação e filtros avançados."""
    logger.info(f"📋 Listando processos - Página {pagination.page}, Limite {pagination.limit}")
    
    try:
        # Verificar rate limit
        await get_process_rate_limit(None, current_user)
        
        # Construir query base
        query = select(Process)
        
        # Aplicar filtros e paginação
        query = apply_process_filters(query, pagination)
        
        # Executar query
        result = await db.execute(query)
        processes = result.scalars().all()
        
        # Contar total para paginação
        count_query = select(Process)
        if pagination.filter_court:
            count_query = count_query.filter(Process.court == pagination.filter_court)
        if pagination.filter_has_documents is not None:
            count_query = count_query.filter(Process.has_documents == pagination.filter_has_documents)
        
        total_result = await db.execute(select(func.count()).select_from(count_query.subquery()))
        total = total_result.scalar()
        
        logger.info(f"✅ Encontrados {len(processes)} processos de {total} total")
        
        return [ProcessResponse.model_validate(process) for process in processes]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao listar processos: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao listar processos: {str(e)}"
        )


@router.get("/{process_number}", response_model=ProcessResponse)
async def get_process(
    process_number: str,
    force_refresh: bool = False,
    webhook_url: Optional[str] = None,  # NOVO: URL para callback quando download completo
    auto_download: bool = True,          # NOVO: Iniciar download automático
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user_or_admin())
):
    """
    Obter dados de um processo específico.
    
    NOVA FUNCIONALIDADE:
    - Se auto_download=true (padrão), inicia download assíncrono de documentos
    - Se webhook_url fornecido, envia callback quando processamento completo
    - Consulte GET /{numero}/status para acompanhar progresso
    """
    try:
        logger.info("=" * 80)
        logger.info(f"🔍 GET /processes/{process_number}")
        logger.info(f"   auto_download: {auto_download}")
        logger.info(f"   webhook_url: {webhook_url or 'Não fornecido'}")
        logger.info(f"   force_refresh: {force_refresh}")
        logger.info("=" * 80)
        
        # Verificar cache primeiro (se não for refresh forçado)
        if not force_refresh:
            cache_key = get_process_cache_key(process_number, "full")
            cached_data = await cache_service.get(cache_key)
            
            if cached_data:
                # Buscar processo no banco para dados estruturados (usando número normalizado)
                normalized_number = normalize_process_number(process_number)
                result = await db.execute(
                    select(Process).where(Process.process_number == normalized_number)
                )
                process = result.scalar_one_or_none()
                
                if process:
                    return ProcessResponse.model_validate(process)
        
        # Buscar processo no banco (usando número normalizado)
        normalized_number = normalize_process_number(process_number)
        result = await db.execute(
            select(Process).where(Process.process_number == normalized_number)
        )
        process = result.scalar_one_or_none()
        
        if not process:
            # Se não existe, buscar na API PDPJ
            try:
                # Buscar dados completos na API PDPJ
                pdpj_data = await pdpj_client.get_process_full(process_number)
                
                # Criar novo processo (usando número normalizado)
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
                
                # Armazenar no cache
                cache_key = get_process_cache_key(process_number, "full")
                await cache_service.set(cache_key, pdpj_data)
                
            except PDPJClientError as e:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Processo {process_number} não encontrado: {str(e)}"
                )
        
        # Carregar relacion relationships antes de qualquer operação Celery
        # Isso evita lazy loading posterior
        await db.refresh(process, ["documents", "jobs"])
        
        # NOVO: Iniciar download assíncrono se auto_download=true
        logger.info(f"🔎 Verificando auto_download: {auto_download}, has_documents: {process.has_documents}")
        
        if auto_download and process.has_documents:
            logger.info(f"🚀 CONDIÇÃO ATENDIDA: Iniciando download assíncrono para processo {process_number}")
            
            # Validar webhook_url se fornecido
            if webhook_url:
                is_valid, error = webhook_service.validate_webhook_url(webhook_url)
                if not is_valid:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Webhook URL inválida: {error}"
                    )
                logger.info(f"✅ Webhook URL validada: {webhook_url}")
            
            # IDEMPOTÊNCIA AVANÇADA
            logger.info(f"🔍 Verificando idempotência...")
            
            # 1. Verificar se já existe job ativo (PENDING ou PROCESSING)
            existing_job = await db.execute(
                select(ProcessJob).where(
                    ProcessJob.process_id == process.id,
                    ProcessJob.status.in_([JobStatus.PENDING.value, JobStatus.PROCESSING.value])
                ).order_by(ProcessJob.created_at.desc())
            )
            active_job = existing_job.scalar_one_or_none()
            
            if active_job:
                logger.info(f"♻️ Job ativo encontrado: {active_job.job_id} (status: {active_job.status})")
                logger.info(f"📊 Progresso atual: {active_job.progress_percentage:.1f}%")
                # Retornar sem criar novo job
                db.expunge(process)
                return ProcessResponse.model_validate(process)
            
            # 2. Verificar se TODOS os documentos já foram baixados (job completo anterior)
            docs_count = await db.execute(
                select(func.count()).select_from(
                    select(Document).where(
                        Document.process_id == process.id,
                        Document.status == DocumentStatus.AVAILABLE.value
                    ).subquery()
                )
            )
            available_count = docs_count.scalar()
            total_docs = len(process.documents)
            
            if available_count == total_docs and total_docs > 0:
                logger.info(f"✅ Todos os documentos já estão disponíveis ({available_count}/{total_docs})")
                logger.info(f"📦 Regenerando links S3 se necessário...")
                
                # Regenerar links S3 expirados
                updated_count = 0
                for doc in process.documents:
                    if doc.downloaded and doc.s3_key and doc.status == DocumentStatus.AVAILABLE.value:
                        try:
                            # Gerar nova URL presignada
                            new_url = await s3_service.generate_presigned_url(doc.s3_key, expiration=3600)
                            await db.execute(
                                update(Document).where(Document.id == doc.id).values(
                                    download_url=new_url,
                                    updated_at=datetime.utcnow()
                                )
                            )
                            updated_count += 1
                        except Exception as e:
                            logger.warning(f"⚠️ Erro ao regenerar URL para {doc.name}: {e}")
                
                await db.commit()
                logger.info(f"🔗 {updated_count} links S3 regenerados")
                logger.info(f"ℹ️ Nenhum job criado - processo já completo")
                db.expunge(process)
                return ProcessResponse.model_validate(process)
            
            logger.info(f"📊 Documentos disponíveis: {available_count}/{total_docs} - Criando novo job")
            
            # IMPORTANTE: Registrar job no banco ANTES de chamar Celery
            # Gerar job_id único
            import uuid as uuid_module
            job_id = str(uuid_module.uuid4())
            
            # Definir status inicial dos documentos baseado em webhook
            initial_status = DocumentStatus.PENDING.value if webhook_url else DocumentStatus.PROCESSING.value
            
            # Atualizar status de documentos ainda não baixados
            await db.execute(
                update(Document).where(
                    Document.process_id == process.id,
                    Document.downloaded == False
                ).values(
                    status=initial_status
                )
            )
            
            # Criar registro do job no banco
            process_job = ProcessJob(
                job_id=job_id,
                process_id=process.id,
                webhook_url=webhook_url,
                total_documents=len(process.documents) if process.documents else 0,
                status=JobStatus.PENDING.value
            )
            db.add(process_job)
            await db.commit()
            
            logger.info(f"✅ Job registrado no banco: {job_id}")
            logger.info(f"📊 Documentos marcados com status: {initial_status}")
            
            # Agendar download assíncrono via Celery (DEPOIS de registrar no banco)
            from app.tasks.download_tasks import download_process_documents_async
            
            try:
                # Usar task_id pré-gerado
                job = download_process_documents_async.apply_async(
                    args=[process.id, process_number, webhook_url],
                    queue='documents',
                    task_id=job_id  # Usar o mesmo ID
                )
                logger.info(f"🚀 Download assíncrono agendado com sucesso: {job.id}")
            except Exception as celery_error:
                logger.error(f"❌ Erro ao agendar task Celery: {celery_error}")
                # Marcar job como failed
                await db.execute(
                    update(ProcessJob).where(ProcessJob.id == process_job.id).values(
                        status=JobStatus.FAILED.value,
                        error_message=str(celery_error)
                    )
                )
                await db.commit()
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Erro ao agendar download: {str(celery_error)}"
                )
        else:
            if not auto_download:
                logger.info(f"ℹ️ auto_download=false - Pulando download assíncrono")
            elif not process.has_documents:
                logger.info(f"ℹ️ Processo sem documentos - Pulando download assíncrono")
        
        logger.info(f"📤 Retornando ProcessResponse para: {process_number}")
        response = ProcessResponse.model_validate(process)
        logger.info(f"✅ Response montada: process_number={response.process_number}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar processo: {str(e)}"
        )


@router.post("/search", response_model=ProcessSearchResponse)
async def search_processes(
    search_request: ProcessSearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user_or_admin())
):
    """Buscar múltiplos processos em lote com cache otimizado."""
    
    logger.info(f"🚀 Iniciando busca de processos: {len(search_request.process_numbers)} processos")
    
    try:
        # Verificar rate limit
        await search_processes_rate_limit(None, current_user)
        
        # Verificar limite de tamanho do lote
        await batch_size_limit(None, search_request)
        
        # Se muitos processos, usar processamento assíncrono
        if len(search_request.process_numbers) > 100:
            logger.info(f"📦 Processamento assíncrono para {len(search_request.process_numbers)} processos")
            batch_id = str(uuid.uuid4())
            
            # Agendar tarefa assíncrona
            task = process_batch_search.delay(
                search_request.process_numbers,
                search_request.include_documents
            )
            
            return ProcessSearchResponse(
                total_requested=len(search_request.process_numbers),
                found=0,
                not_found=search_request.process_numbers,
                processes=[],
                batch_id=batch_id
            )
        
        # Processamento síncrono para poucos processos
        logger.info(f"🔄 Processamento síncrono para {len(search_request.process_numbers)} processos")
        found_processes = []
        not_found = []
        
        # Usar cache otimizado para busca em lote
        try:
            cached_data = await process_cache_service.batch_get_processes(search_request.process_numbers)
            logger.info(f"📦 Cache processado: {len(cached_data)} processos encontrados")
            
            # Processar resultados do cache
            async with TransactionManager(db).transaction():
                for process_number in search_request.process_numbers:
                    try:
                        # Verificar se existe no banco
                        normalized_number = normalize_process_number(process_number)
                        result = await db.execute(
                            select(Process).where(Process.process_number == normalized_number)
                        )
                        process = result.scalar_one_or_none()
                        
                        if process:
                            logger.debug(f"✅ Processo encontrado no banco: {process_number}")
                            found_processes.append(ProcessResponse.model_validate(process))
                        elif process_number in cached_data:
                            # Criar novo processo com dados do cache
                            pdpj_data = cached_data[process_number]
                            process = Process(
                                process_number=normalized_number,
                                full_data=pdpj_data,
                                court=pdpj_data.get("siglaTribunal"),
                                subject=pdpj_data.get("tramitacoes", [{}])[0].get("assunto", [{}])[0].get("descricao") if pdpj_data.get("tramitacoes") else None,
                                status=pdpj_data.get("tramitacaoAtual", {}).get("descricao"),
                                has_documents=bool(pdpj_data.get("documentos"))
                            )
                            
                            db.add(process)
                            found_processes.append(ProcessResponse.model_validate(process))
                            logger.debug(f"✅ Processo criado com dados do cache: {process_number}")
                        else:
                            not_found.append(process_number)
                            logger.debug(f"❌ Processo não encontrado: {process_number}")
                            
                    except Exception as e:
                        logger.error(f"❌ Erro ao processar {process_number}: {e}")
                        not_found.append(process_number)
                
                # Commit da transação
                await db.commit()
                logger.info(f"💾 Transação commitada com sucesso")
                
        except Exception as e:
            logger.error(f"❌ Erro no processamento em lote: {e}")
            # Fallback para processamento individual
            await _fallback_individual_search(search_request.process_numbers, db, found_processes, not_found)
        
        logger.info(f"📊 Resultado da busca: {len(found_processes)} encontrados, {len(not_found)} não encontrados")
        if not_found:
            logger.warning(f"❌ Processos não encontrados: {not_found}")
        
        return ProcessSearchResponse(
            total_requested=len(search_request.process_numbers),
            found=len(found_processes),
            not_found=not_found,
            processes=found_processes
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro na busca em lote: {str(e)}"
        )


@router.get("/{process_number}/files", response_model=ProcessFilesResponse)
async def get_process_files(
    process_number: str,
    pagination: DocumentPaginationParams = Depends(create_document_pagination_params),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user_or_admin())
):
    """Obter arquivos/documentos de um processo com paginação e filtros."""
    logger.info(f"📁 Iniciando busca de documentos para processo: {process_number}")
    
    try:
        # Buscar processo no banco (usando número normalizado)
        normalized_number = normalize_process_number(process_number)
        logger.info(f"🔍 Número normalizado: {normalized_number}")
        
        result = await db.execute(
            select(Process)
            .where(Process.process_number == normalized_number)
            .options(selectinload(Process.documents))
        )
        process = result.scalar_one_or_none()
        
        if process:
            logger.info(f"✅ Processo encontrado com {len(process.documents)} documentos")
        else:
            logger.warning(f"❌ Processo não encontrado: {process_number}")
        
        if not process:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Processo {process_number} não encontrado"
            )
        
        # Verificar rate limit
        await get_files_rate_limit(None, current_user)
        
        # Buscar documentos no banco com paginação e filtros
        logger.info(f"🔍 Buscando documentos no banco para processo ID: {process.id}")
        
        # Construir query base
        query = select(Document).where(Document.process_id == process.id)
        
        # Aplicar filtros e paginação
        query = apply_document_filters(query, pagination)
        
        # Executar query
        result = await db.execute(query)
        documents = result.scalars().all()
        
        # Contar total para paginação
        count_query = select(Document).where(Document.process_id == process.id)
        if pagination.filter_type:
            count_query = count_query.filter(Document.type == pagination.filter_type)
        if pagination.filter_downloaded is not None:
            count_query = count_query.filter(Document.downloaded == pagination.filter_downloaded)
        
        total_result = await db.execute(select(func.count()).select_from(count_query.subquery()))
        total = total_result.scalar()
        
        logger.info(f"📄 Encontrados {len(documents)} documentos de {total} total")
        
        # Gerar URLs presignadas para documentos disponíveis
        documents_with_urls = []
        downloaded_count = 0
        available_count = 0
        
        logger.info(f"🔗 Gerando URLs presignadas para {len(documents)} documentos")
        
        for i, doc in enumerate(documents):
            if i % 50 == 0:  # Log a cada 50 documentos
                logger.info(f"📊 Processando documento {i+1}/{len(documents)}")
            
            # Extrair UUID do hrefBinario se disponível
            document_uuid = doc.document_id  # Padrão: usar idOrigem
            if doc.raw_data and doc.raw_data.get("hrefBinario"):
                href = doc.raw_data.get("hrefBinario", "")
                # hrefBinario formato: /processos/.../documentos/{UUID}/binario
                parts = href.split("/documentos/")
                if len(parts) == 2:
                    uuid_part = parts[1].split("/")[0]
                    if "-" in uuid_part:  # Validação básica de UUID
                        document_uuid = uuid_part
            
            doc_data = {
                "id": doc.document_id,  # ID original (numérico)
                "uuid": document_uuid,  # UUID para download
                "name": doc.name,
                "type": doc.type,
                "size": doc.size,
                "mime_type": doc.mime_type,
                "downloaded": doc.downloaded,
                "available": doc.available,
                "created_at": doc.created_at.isoformat() if doc.created_at else None
            }
            
            # Se o documento foi baixado, gerar URL presignada
            if doc.downloaded and doc.s3_key:
                try:
                    # Gerar nova URL presignada (válida por 1 hora)
                    doc_data["download_url"] = await s3_service.generate_presigned_url(
                        doc.s3_key,
                        expiration=3600  # 1 hora
                    )
                    doc_data["s3_key"] = doc.s3_key
                    doc_data["expires_in"] = 3600
                except Exception as e:
                    doc_data["download_url"] = None
                    doc_data["error"] = str(e)
            elif doc.downloaded:
                # Documento marcado como baixado mas sem s3_key
                doc_data["download_url"] = None
                doc_data["error"] = "Documento baixado mas não encontrado no S3"
            
            documents_with_urls.append(doc_data)
            
            # Contar estatísticas
            if doc.downloaded:
                downloaded_count += 1
            if doc.available:
                available_count += 1
        
        logger.info(f"✅ Processamento concluído: {len(documents_with_urls)} documentos processados")
        logger.info(f"📊 Estatísticas: {downloaded_count} baixados, {available_count} disponíveis")
        
        return ProcessFilesResponse(
            process_number=process_number,
            documents=documents_with_urls,
            total_documents=len(documents),
            downloaded_documents=downloaded_count
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar arquivos: {str(e)}"
        )


@router.get("/{process_number}/status", response_model=ProcessStatusResponse)
async def get_process_status(
    process_number: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user_or_admin())
):
    """Obter status de processamento de um processo com progresso em tempo real."""
    try:
        logger.info(f"📊 Buscando status do processo: {process_number}")
        
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
        completed = sum(1 for d in process.documents if hasattr(d, 'status') and d.status == DocumentStatus.AVAILABLE.value)
        failed = sum(1 for d in process.documents if hasattr(d, 'status') and d.status == DocumentStatus.FAILED.value)
        processing = sum(1 for d in process.documents if hasattr(d, 'status') and d.status == DocumentStatus.PROCESSING.value)
        pending = sum(1 for d in process.documents if hasattr(d, 'status') and d.status == DocumentStatus.PENDING.value)
        
        # Se não tem campo status (documentos antigos), usar flag downloaded
        if not any(hasattr(d, 'status') for d in process.documents):
            completed = sum(1 for d in process.documents if d.downloaded)
            pending = total_docs - completed
            processing = 0
            failed = 0
        
        # Status geral do processo
        if failed == total_docs and total_docs > 0:
            overall_status = "failed"
        elif completed == total_docs and total_docs > 0:
            overall_status = "completed"
        elif processing > 0 or (latest_job and latest_job.status == JobStatus.PROCESSING.value):
            overall_status = "processing"
        else:
            overall_status = "pending"
        
        # Progresso
        progress = (completed / total_docs * 100) if total_docs > 0 else 0
        
        logger.info(f"📊 Status: {overall_status}, Progresso: {progress:.1f}% ({completed}/{total_docs})")
        
        # Montar documentos com status
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
            
            # Status do documento
            doc_status = doc.status if hasattr(doc, 'status') else ("available" if doc.downloaded else "pending")
            
            doc_data = DocumentStatusResponse(
                id=doc.document_id,
                uuid=doc_uuid,
                name=doc.name or "Documento sem nome",
                status=doc_status,
                size=doc.size,
                mime_type=doc.mime_type,
                download_url=None,
                error_message=doc.error_message if hasattr(doc, 'error_message') else None,
                download_started_at=doc.download_started_at if hasattr(doc, 'download_started_at') else None,
                download_completed_at=doc.download_completed_at if hasattr(doc, 'download_completed_at') else None
            )
            
            # Se disponível, gerar URL presignada
            if doc.downloaded and doc.s3_key:
                try:
                    doc_data.download_url = await s3_service.generate_presigned_url(
                        doc.s3_key, expiration=3600
                    )
                except Exception as e:
                    logger.warning(f"⚠️ Erro ao gerar URL presignada: {e}")
                    doc_data.error_message = f"Erro ao gerar URL: {str(e)}"
            
            documents_status.append(doc_data)
        
        return ProcessStatusResponse(
            process_number=process_number,
            status=overall_status,
            total_documents=total_docs,
            completed_documents=completed,
            failed_documents=failed,
            pending_documents=pending,
            processing_documents=processing,
            progress_percentage=progress,
            documents=documents_status,
            job_id=latest_job.job_id if latest_job else None,
            webhook_url=latest_job.webhook_url if latest_job else None,
            webhook_sent=latest_job.webhook_sent if latest_job else False,
            webhook_sent_at=latest_job.webhook_sent_at if latest_job else None,
            created_at=latest_job.created_at if latest_job else None,
            started_at=latest_job.started_at if latest_job else None,
            completed_at=latest_job.completed_at if latest_job else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao buscar status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar status: {str(e)}"
        )


@router.post("/{process_number}/refresh")
async def refresh_process(
    process_number: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user_or_admin())
):
    """Forçar atualização dos dados de um processo."""
    try:
        # Buscar dados atualizados na API PDPJ
        try:
            pdpj_data = await pdpj_client.get_process_full(process_number)
        except PDPJClientError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Processo {process_number} não encontrado: {str(e)}"
            )
        
        # Buscar processo no banco (usando número normalizado)
        normalized_number = normalize_process_number(process_number)
        result = await db.execute(
            select(Process).where(Process.process_number == normalized_number)
        )
        process = result.scalar_one_or_none()
        
        if process:
            # Atualizar processo existente
            await db.execute(
                update(Process)
                .where(Process.id == process.id)
                .values(
                    full_data=pdpj_data,
                    court=pdpj_data.get("siglaTribunal"),
                    subject=pdpj_data.get("tramitacoes", [{}])[0].get("assunto", [{}])[0].get("descricao") if pdpj_data.get("tramitacoes") else None,
                    status=pdpj_data.get("tramitacaoAtual", {}).get("descricao"),
                    has_documents=bool(pdpj_data.get("documentos")),
                    last_consultation=datetime.utcnow()
                )
            )
        else:
            # Criar novo processo (usando número normalizado)
            process = Process(
                process_number=normalized_number,
                full_data=pdpj_data,
                court=pdpj_data.get("siglaTribunal"),
                subject=pdpj_data.get("tramitacoes", [{}])[0].get("assunto", [{}])[0].get("descricao") if pdpj_data.get("tramitacoes") else None,
                status=pdpj_data.get("tramitacaoAtual", {}).get("descricao"),
                has_documents=bool(pdpj_data.get("documentos")),
                last_consultation=datetime.utcnow()
            )
            db.add(process)
        
        await db.commit()
        
        # Atualizar cache
        cache_key = get_process_cache_key(process_number, "full")
        await cache_service.set(cache_key, pdpj_data)
        
        return {
            "message": f"Processo {process_number} atualizado com sucesso",
            "updated_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao atualizar processo: {str(e)}"
        )


@router.post("/{process_number}/download-documents")
async def download_process_documents(
    process_number: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user_or_admin())
):
    """Baixar todos os documentos de um processo e salvar no banco."""
    logger.info(f"⬇️ Iniciando download de documentos para processo: {process_number}")
    
    # Verificar rate limit
    await download_documents_rate_limit(None, current_user)
    
    # Verificar throttling de downloads
    user_id = str(current_user.id)
    if not await download_throttle.acquire(user_id):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Muitos downloads simultâneos. Tente novamente em alguns minutos."
        )

    # Debug: verificar token carregado
    from app.core.config import settings
    token = settings.pdpj_api_token.get_secret_value()
    logger.info(f"🔑 Token PDPJ carregado - Tamanho: {len(token)}, Início: {token[:50]}...")
    
    try:
        # Buscar processo no banco (usando número normalizado)
        normalized_number = normalize_process_number(process_number)
        logger.info(f"🔍 Número normalizado: {normalized_number}")
        
        result = await db.execute(
            select(Process).where(Process.process_number == normalized_number)
        )
        process = result.scalar_one_or_none()
        
        if process:
            logger.info(f"✅ Processo encontrado para download: {process_number}")
        else:
            logger.warning(f"❌ Processo não encontrado para download: {process_number}")
        
        if not process:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Processo {process_number} não encontrado"
            )
        
        # Buscar documentos na API PDPJ
        logger.info(f"🌐 Buscando documentos na API PDPJ para: {process_number}")
        
        # DEBUG: Verificar configurações do cliente PDPJ
        logger.info(f"🔍 DEBUG - Cliente PDPJ: {type(pdpj_client).__name__}")
        logger.info(f"🔍 DEBUG - Token do cliente: {pdpj_client.token[:50] if hasattr(pdpj_client, 'token') and pdpj_client.token else 'N/A'}...")
        logger.info(f"🔍 DEBUG - Base URL do cliente: {pdpj_client.base_url if hasattr(pdpj_client, 'base_url') else 'N/A'}")
        
        try:
            documents_data = await pdpj_client.get_process_documents(process_number)
            logger.info(f"✅ Documentos recebidos da API PDPJ: {len(documents_data) if documents_data else 0}")
        except PDPJClientError as e:
            logger.error(f"❌ Erro na API PDPJ: {e}")
            logger.error(f"🔍 DEBUG - Tipo de erro: {type(e).__name__}")
            logger.error(f"🔍 DEBUG - Mensagem completa: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Erro ao buscar documentos: {str(e)}"
            )
        
        if not documents_data:
            return {
                "process_number": process_number,
                "message": "Nenhum documento encontrado",
                "documents_processed": 0
            }
        
        documents_processed = 0
        documents_errors = []
        
        for doc_data in documents_data:
            try:
                # Verificar se documento já existe
                existing_doc = await db.execute(
                    select(Document).where(
                        Document.process_id == process.id,
                        Document.document_id == doc_data.get("idOrigem")
                    )
                )
                
                if existing_doc.scalar_one_or_none():
                    continue  # Documento já existe, pular
                
                # Extrair hrefBinario para download
                href_binario = doc_data.get("hrefBinario")
                if not href_binario:
                    logger.warning(f"⚠️ Documento {doc_data.get('idOrigem')} não possui hrefBinario")
                    documents_errors.append({
                        "document_id": doc_data.get("idOrigem"),
                        "error": "hrefBinario não encontrado"
                    })
                    continue
                
                # Criar registro do documento
                document = Document(
                    process_id=process.id,
                    document_id=doc_data.get("idOrigem"),
                    name=doc_data.get("nome"),
                    type=doc_data.get("tipo", {}).get("nome"),
                    size=doc_data.get("arquivo", {}).get("tamanho"),
                    mime_type=doc_data.get("arquivo", {}).get("tipo"),
                    raw_data=doc_data,
                    downloaded=False,
                    available=True
                )
                
                db.add(document)
                documents_processed += 1
                
                logger.info(f"✅ Documento {doc_data.get('idOrigem')} registrado com hrefBinario: {href_binario}")
                
            except Exception as e:
                documents_errors.append({
                    "document_id": doc_data.get("idOrigem"),
                    "error": str(e)
                })
        
        # Atualizar processo
        await db.execute(
            update(Process)
            .where(Process.id == process.id)
            .values(
                has_documents=True,
                updated_at=datetime.utcnow()
            )
        )
        
        await db.commit()
        
        return {
            "process_number": process_number,
            "message": f"Documentos processados com sucesso",
            "documents_processed": documents_processed,
            "total_documents": len(documents_data),
            "errors": documents_errors if documents_errors else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao processar documentos: {str(e)}"
        )
    finally:
        # Liberar throttle de download
        await download_throttle.release(user_id)


@router.post("/{process_number}/download-all-documents")
async def download_all_documents_physical(
    process_number: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user_or_admin())
):
    """Baixar TODOS os documentos de um processo fisicamente e fazer upload para S3."""
    logger.info(f"🚀 Iniciando download em massa de documentos para: {process_number}")
    
    try:
        # Buscar processo
        normalized_number = normalize_process_number(process_number)
        process_result = await db.execute(
            select(Process).where(Process.process_number == normalized_number)
        )
        process = process_result.scalar_one_or_none()
        
        if not process:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Processo {process_number} não encontrado"
            )
        
        # Buscar TODOS os documentos (sempre baixa, mesmo se já foi baixado)
        result = await db.execute(
            select(Document).where(Document.process_id == process.id)
        )
        documents = result.scalars().all()
        
        if not documents:
            return {
                "process_number": process_number,
                "message": "Nenhum documento encontrado para este processo",
                "total": 0,
                "downloaded": 0,
                "failed": 0
            }
        
        logger.info(f"📊 Total de documentos para baixar: {len(documents)}")
        
        downloaded_count = 0
        failed_count = 0
        results = []
        
        # Baixar em lotes de 5
        batch_size = 5
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            logger.info(f"📦 Processando lote {i//batch_size + 1}: {len(batch)} documentos")
            
            for doc in batch:
                try:
                    # Extrair hrefBinario
                    href_binario = doc.raw_data.get("hrefBinario") if doc.raw_data else None
                    if not href_binario:
                        failed_count += 1
                        results.append({"document_id": doc.document_id, "status": "failed", "error": "hrefBinario não encontrado"})
                        continue
                    
                    # Baixar documento
                    download_result = await pdpj_client.download_document(href_binario, doc.name)
                    
                    if download_result.get('is_valid') and download_result.get('saved_path'):
                        with open(download_result['saved_path'], 'rb') as f:
                            document_content = f.read()
                        
                        # Upload para S3
                        s3_key = f"processos/{process_number}/documentos/{doc.document_id}/{doc.name}"
                        await s3_service.upload_document(
                            file_content=document_content,
                            process_number=process_number,
                            document_id=doc.document_id,
                            filename=doc.name,
                            content_type=doc.mime_type or "application/pdf"
                        )
                        
                        # Gerar URL presignada
                        download_url = await s3_service.generate_presigned_url(s3_key, expiration=3600)
                        
                        # Atualizar no banco
                        await db.execute(
                            update(Document).where(Document.id == doc.id).values(
                                s3_key=s3_key,
                                s3_bucket=s3_service.bucket_name,
                                download_url=download_url,
                                size=len(document_content),
                                downloaded=True,
                                updated_at=datetime.utcnow()
                            )
                        )
                        
                        downloaded_count += 1
                        results.append({"document_id": doc.document_id, "name": doc.name, "status": "success", "size": len(document_content)})
                        logger.info(f"✅ {doc.name} baixado com sucesso")
                    else:
                        failed_count += 1
                        results.append({"document_id": doc.document_id, "status": "failed", "error": "Download inválido"})
                    
                except Exception as e:
                    failed_count += 1
                    results.append({"document_id": doc.document_id, "status": "error", "error": str(e)})
                    logger.error(f"❌ Erro ao baixar {doc.name}: {e}")
            
            await db.commit()
            await asyncio.sleep(1)  # Pequena pausa entre lotes
        
        return {
            "process_number": process_number,
            "message": f"Download em massa concluído",
            "total": len(documents),
            "downloaded": downloaded_count,
            "failed": failed_count,
            "results": results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro no download em massa: {str(e)}"
        )


@router.post("/{process_number}/download-document/{document_id}")
async def download_document_physical(
    process_number: str,
    document_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user_or_admin())
):
    """Baixar um documento específico fisicamente e fazer upload para S3.
    
    Args:
        document_id: Pode ser o ID numérico (idOrigem) ou UUID do hrefBinario
    """
    try:
        # Buscar documento no banco (usando número normalizado)
        normalized_number = normalize_process_number(process_number)
        
        # Primeiro buscar o processo
        process_result = await db.execute(
            select(Process).where(Process.process_number == normalized_number)
        )
        process = process_result.scalar_one_or_none()
        
        if not process:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Processo {process_number} não encontrado"
            )
        
        # Tentar buscar documento por ID numérico primeiro
        result = await db.execute(
            select(Document).where(
                Document.process_id == process.id,
                Document.document_id == document_id
            )
        )
        document = result.scalar_one_or_none()
        
        # Se não encontrou e document_id parece ser UUID, buscar no hrefBinario
        if not document and "-" in document_id:
            logger.info(f"🔍 Buscando documento por UUID no hrefBinario: {document_id}")
            result = await db.execute(
                select(Document).where(Document.process_id == process.id)
            )
            all_docs = result.scalars().all()
            
            # Procurar UUID no hrefBinario
            for doc in all_docs:
                if doc.raw_data and doc.raw_data.get("hrefBinario"):
                    href = doc.raw_data.get("hrefBinario", "")
                    if document_id in href:
                        document = doc
                        logger.info(f"✅ Documento encontrado por UUID: {doc.document_id}")
                        break
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Documento {document_id} não encontrado no processo {process_number}"
            )
        
        if document.downloaded:
            return {
                "message": f"Documento {document_id} já foi baixado",
                "s3_key": document.s3_key,
                "download_url": document.download_url,
                "size": document.size
            }
        
        # Extrair hrefBinario dos dados do documento
        href_binario = document.raw_data.get("hrefBinario")
        if not href_binario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"hrefBinario não encontrado para o documento {document_id}"
            )
        
        # Baixar documento da API PDPJ usando hrefBinario
        try:
            download_result = await pdpj_client.download_document(href_binario)
            
            # O pdpj_client retorna metadados, precisamos ler o arquivo salvo
            if download_result.get('is_valid') and download_result.get('saved_path'):
                with open(download_result['saved_path'], 'rb') as f:
                    document_content = f.read()
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Erro ao baixar documento: arquivo inválido"
                )
        except PDPJClientError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Erro ao baixar documento: {str(e)}"
            )
        
        # Gerar chave S3
        s3_key = f"processos/{process_number}/documentos/{document_id}/{document.name}"
        
        # Upload para S3
        try:
            await s3_service.upload_document(
                file_content=document_content,
                process_number=process_number,
                document_id=document_id,
                filename=document.name,
                content_type=document.mime_type or "application/pdf"
            )
            
            # Gerar URL presignada
            download_url = await s3_service.generate_presigned_url(s3_key, expiration=3600)
            
            # Atualizar documento no banco
            await db.execute(
                update(Document)
                .where(Document.id == document.id)
                .values(
                    s3_key=s3_key,
                    s3_bucket=s3_service.bucket_name,
                    download_url=download_url,
                    size=len(document_content),
                    downloaded=True,
                    updated_at=datetime.utcnow()
                )
            )
            
            await db.commit()
            
            return {
                "message": f"Documento {document_id} baixado e armazenado com sucesso",
                "document_id": document_id,
                "name": document.name,
                "size": len(document_content),
                "s3_key": s3_key,
                "download_url": download_url,
                "expires_in": 3600
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erro ao fazer upload para S3: {str(e)}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao processar documentos: {str(e)}"
        )
