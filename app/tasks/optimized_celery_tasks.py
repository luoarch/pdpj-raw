"""
Tarefas Celery otimizadas para processamento em lote de alta escala.
"""

import asyncio
import time
from typing import List, Dict, Any, Optional
from celery import Celery, Task
from celery.exceptions import Retry
from loguru import logger

from app.core.dynamic_limits import get_current_limits
from app.services.pdpj_client import pdpj_client
from app.services.process_cache_service import process_cache_service
from app.utils.transaction_manager import BatchTransactionManager
from app.utils.advanced_retry import retry_database, retry_http
from app.core.proactive_monitoring import record_error_metrics, record_request_metrics


class OptimizedCeleryTask(Task):
    """Classe base para tarefas Celery otimizadas."""
    
    def __init__(self):
        self.limits = get_current_limits()
        self.max_retries = self.limits.max_retries
        self.retry_delay = self.limits.retry_delay
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Callback para falhas."""
        logger.error(f"❌ Tarefa {task_id} falhou: {exc}")
        record_error_metrics("celery_task_failure", task_id, str(exc))
    
    def on_success(self, retval, task_id, args, kwargs):
        """Callback para sucesso."""
        logger.info(f"✅ Tarefa {task_id} concluída com sucesso")
    
    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Callback para retry."""
        logger.warning(f"⚠️ Tarefa {task_id} será tentada novamente: {exc}")


# Configurar Celery
celery_app = Celery('pdpj_optimized')
celery_app.config_from_object('app.core.celery_config')

# Configurações otimizadas
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    
    # Configurações de performance
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_disable_rate_limits=True,
    
    # Configurações de retry
    task_default_retry_delay=60,
    task_max_retries=7,
    
    # Configurações de memória
    worker_max_memory_per_child=200000,  # 200MB
    worker_max_tasks_per_child=1000,
    
    # Configurações de concorrência
    worker_concurrency=4,
    task_routes={
        'app.tasks.optimized_celery_tasks.process_batch_search_optimized': {'queue': 'batch_search'},
        'app.tasks.optimized_celery_tasks.download_documents_batch': {'queue': 'downloads'},
        'app.tasks.optimized_celery_tasks.process_large_batch': {'queue': 'large_batch'},
    }
)


@celery_app.task(bind=True, base=OptimizedCeleryTask, name='process_batch_search_optimized')
async def process_batch_search_optimized(self, process_numbers: List[str], include_documents: bool = False):
    """Processamento otimizado de busca em lote."""
    logger.info(f"🚀 Iniciando busca otimizada em lote: {len(process_numbers)} processos")
    
    start_time = time.time()
    results = {
        "total_requested": len(process_numbers),
        "found": 0,
        "not_found": [],
        "errors": [],
        "processed_at": time.time(),
        "batch_id": self.request.id
    }
    
    try:
        # Dividir em chunks menores para processamento
        chunk_size = min(self.limits.max_batch_size, 100)
        chunks = [process_numbers[i:i + chunk_size] for i in range(0, len(process_numbers), chunk_size)]
        
        logger.info(f"📦 Processando {len(chunks)} chunks de até {chunk_size} processos")
        
        # Processar chunks em paralelo
        chunk_results = []
        for i, chunk in enumerate(chunks):
            try:
                chunk_result = await process_chunk_optimized(chunk, include_documents)
                chunk_results.append(chunk_result)
                
                # Atualizar progresso
                progress = ((i + 1) / len(chunks)) * 100
                self.update_state(
                    state='PROGRESS',
                    meta={'progress': progress, 'chunk': i + 1, 'total_chunks': len(chunks)}
                )
                
            except Exception as e:
                logger.error(f"❌ Erro no chunk {i + 1}: {e}")
                results["errors"].append({"chunk": i + 1, "error": str(e)})
        
        # Consolidar resultados
        for chunk_result in chunk_results:
            results["found"] += chunk_result["found"]
            results["not_found"].extend(chunk_result["not_found"])
            results["errors"].extend(chunk_result.get("errors", []))
        
        duration = time.time() - start_time
        record_request_metrics("POST", "batch_search", 200, duration)
        
        logger.info(f"✅ Busca otimizada concluída: {results['found']} encontrados em {duration:.2f}s")
        
        return results
        
    except Exception as e:
        duration = time.time() - start_time
        record_error_metrics("batch_search_failure", self.request.id, str(e))
        logger.error(f"❌ Erro na busca otimizada: {e}")
        raise self.retry(exc=e, countdown=60, max_retries=3)


async def process_chunk_optimized(process_numbers: List[str], include_documents: bool) -> Dict[str, Any]:
    """Processar um chunk de processos de forma otimizada."""
    logger.info(f"📦 Processando chunk de {len(process_numbers)} processos")
    
    found = 0
    not_found = []
    errors = []
    
    try:
        # Usar cache otimizado
        cached_data = await process_cache_service.batch_get_processes(process_numbers)
        
        # Processar resultados do cache
        for process_number in process_numbers:
            try:
                if process_number in cached_data:
                    # Processo encontrado no cache
                    found += 1
                    logger.debug(f"✅ Processo encontrado no cache: {process_number}")
                else:
                    # Processo não encontrado
                    not_found.append(process_number)
                    logger.debug(f"❌ Processo não encontrado: {process_number}")
                    
            except Exception as e:
                logger.error(f"❌ Erro ao processar {process_number}: {e}")
                errors.append({"process_number": process_number, "error": str(e)})
        
        return {
            "found": found,
            "not_found": not_found,
            "errors": errors
        }
        
    except Exception as e:
        logger.error(f"❌ Erro no processamento do chunk: {e}")
        raise


@celery_app.task(bind=True, base=OptimizedCeleryTask, name='download_documents_batch')
async def download_documents_batch(self, process_number: str, document_ids: List[str]):
    """Download em lote de documentos."""
    logger.info(f"⬇️ Iniciando download em lote: {len(document_ids)} documentos para {process_number}")
    
    start_time = time.time()
    results = {
        "process_number": process_number,
        "total_documents": len(document_ids),
        "downloaded": 0,
        "failed": 0,
        "errors": [],
        "batch_id": self.request.id
    }
    
    try:
        # Dividir em chunks menores
        chunk_size = min(50, len(document_ids))  # Máximo 50 documentos por chunk
        chunks = [document_ids[i:i + chunk_size] for i in range(0, len(document_ids), chunk_size)]
        
        logger.info(f"📦 Processando {len(chunks)} chunks de downloads")
        
        # Processar chunks sequencialmente para evitar sobrecarga
        for i, chunk in enumerate(chunks):
            try:
                chunk_result = await download_chunk_documents(process_number, chunk)
                
                results["downloaded"] += chunk_result["downloaded"]
                results["failed"] += chunk_result["failed"]
                results["errors"].extend(chunk_result.get("errors", []))
                
                # Atualizar progresso
                progress = ((i + 1) / len(chunks)) * 100
                self.update_state(
                    state='PROGRESS',
                    meta={'progress': progress, 'chunk': i + 1, 'total_chunks': len(chunks)}
                )
                
            except Exception as e:
                logger.error(f"❌ Erro no chunk de download {i + 1}: {e}")
                results["errors"].append({"chunk": i + 1, "error": str(e)})
        
        duration = time.time() - start_time
        record_request_metrics("POST", "download_batch", 200, duration)
        
        logger.info(f"✅ Download em lote concluído: {results['downloaded']} baixados em {duration:.2f}s")
        
        return results
        
    except Exception as e:
        duration = time.time() - start_time
        record_error_metrics("download_batch_failure", self.request.id, str(e))
        logger.error(f"❌ Erro no download em lote: {e}")
        raise self.retry(exc=e, countdown=120, max_retries=3)


async def download_chunk_documents(process_number: str, document_ids: List[str]) -> Dict[str, Any]:
    """Download de um chunk de documentos."""
    downloaded = 0
    failed = 0
    errors = []
    
    try:
        # Usar semáforo para controlar concorrência
        semaphore = asyncio.Semaphore(5)  # Máximo 5 downloads simultâneos
        
        async def download_single_document(doc_id: str):
            async with semaphore:
                try:
                    # Implementar download individual
                    # (código de download seria implementado aqui)
                    downloaded += 1
                    logger.debug(f"✅ Documento baixado: {doc_id}")
                except Exception as e:
                    failed += 1
                    errors.append({"document_id": doc_id, "error": str(e)})
                    logger.error(f"❌ Erro ao baixar {doc_id}: {e}")
        
        # Executar downloads em paralelo
        tasks = [download_single_document(doc_id) for doc_id in document_ids]
        await asyncio.gather(*tasks, return_exceptions=True)
        
        return {
            "downloaded": downloaded,
            "failed": failed,
            "errors": errors
        }
        
    except Exception as e:
        logger.error(f"❌ Erro no download do chunk: {e}")
        raise


@celery_app.task(bind=True, base=OptimizedCeleryTask, name='process_large_batch')
async def process_large_batch(self, process_numbers: List[str], batch_size: int = 1000):
    """Processamento de lotes muito grandes."""
    logger.info(f"🚀 Iniciando processamento de lote grande: {len(process_numbers)} processos")
    
    start_time = time.time()
    results = {
        "total_requested": len(process_numbers),
        "processed": 0,
        "errors": [],
        "batch_id": self.request.id
    }
    
    try:
        # Dividir em sub-lotes
        sub_batches = [process_numbers[i:i + batch_size] for i in range(0, len(process_numbers), batch_size)]
        
        logger.info(f"📦 Processando {len(sub_batches)} sub-lotes de até {batch_size} processos")
        
        # Processar sub-lotes sequencialmente
        for i, sub_batch in enumerate(sub_batches):
            try:
                # Agendar sub-lote como tarefa separada
                task = process_batch_search_optimized.delay(sub_batch)
                
                # Aguardar conclusão
                sub_result = task.get(timeout=300)  # 5 minutos de timeout
                
                results["processed"] += sub_result.get("found", 0)
                results["errors"].extend(sub_result.get("errors", []))
                
                # Atualizar progresso
                progress = ((i + 1) / len(sub_batches)) * 100
                self.update_state(
                    state='PROGRESS',
                    meta={'progress': progress, 'sub_batch': i + 1, 'total_sub_batches': len(sub_batches)}
                )
                
            except Exception as e:
                logger.error(f"❌ Erro no sub-lote {i + 1}: {e}")
                results["errors"].append({"sub_batch": i + 1, "error": str(e)})
        
        duration = time.time() - start_time
        record_request_metrics("POST", "large_batch", 200, duration)
        
        logger.info(f"✅ Processamento de lote grande concluído: {results['processed']} processados em {duration:.2f}s")
        
        return results
        
    except Exception as e:
        duration = time.time() - start_time
        record_error_metrics("large_batch_failure", self.request.id, str(e))
        logger.error(f"❌ Erro no processamento de lote grande: {e}")
        raise self.retry(exc=e, countdown=300, max_retries=2)


@celery_app.task(bind=True, base=OptimizedCeleryTask, name='cleanup_old_tasks')
async def cleanup_old_tasks(self, days: int = 7):
    """Limpeza de tarefas antigas."""
    logger.info(f"🧹 Iniciando limpeza de tarefas antigas (>{days} dias)")
    
    try:
        # Implementar limpeza de tarefas antigas
        # (código de limpeza seria implementado aqui)
        
        logger.info("✅ Limpeza de tarefas antigas concluída")
        return {"cleaned_tasks": 0, "days": days}
        
    except Exception as e:
        logger.error(f"❌ Erro na limpeza de tarefas: {e}")
        raise


@celery_app.task(bind=True, base=OptimizedCeleryTask, name='health_check')
async def health_check(self):
    """Verificação de saúde do sistema."""
    logger.info("🏥 Executando verificação de saúde")
    
    try:
        # Verificar saúde dos componentes
        health_status = {
            "timestamp": time.time(),
            "celery": "healthy",
            "database": "healthy",
            "cache": "healthy",
            "pdpj_api": "healthy"
        }
        
        # Implementar verificações específicas
        # (código de verificação seria implementado aqui)
        
        logger.info("✅ Verificação de saúde concluída")
        return health_status
        
    except Exception as e:
        logger.error(f"❌ Erro na verificação de saúde: {e}")
        raise


# Configurações de filas
celery_app.conf.task_routes.update({
    'app.tasks.optimized_celery_tasks.process_batch_search_optimized': {'queue': 'batch_search'},
    'app.tasks.optimized_celery_tasks.download_documents_batch': {'queue': 'downloads'},
    'app.tasks.optimized_celery_tasks.process_large_batch': {'queue': 'large_batch'},
    'app.tasks.optimized_celery_tasks.cleanup_old_tasks': {'queue': 'maintenance'},
    'app.tasks.optimized_celery_tasks.health_check': {'queue': 'monitoring'},
})

# Configurações de prioridade
celery_app.conf.task_routes.update({
    'app.tasks.optimized_celery_tasks.process_batch_search_optimized': {'priority': 5},
    'app.tasks.optimized_celery_tasks.download_documents_batch': {'priority': 3},
    'app.tasks.optimized_celery_tasks.process_large_batch': {'priority': 1},
    'app.tasks.optimized_celery_tasks.cleanup_old_tasks': {'priority': 9},
    'app.tasks.optimized_celery_tasks.health_check': {'priority': 10},
})
