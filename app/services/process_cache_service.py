"""
Serviço de cache otimizado para processos judiciais.
"""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from loguru import logger

from app.core.cache import cache_service
from app.services.pdpj_client import pdpj_client, PDPJClientError
from app.utils.process_utils import normalize_process_number


class ProcessCacheService:
    """Serviço de cache inteligente para processos judiciais."""
    
    def __init__(self):
        self._cache_ttl = timedelta(hours=1)  # TTL padrão de 1 hora
        self._batch_cache_ttl = timedelta(minutes=30)  # TTL menor para batch
        self._pending_requests: Dict[str, asyncio.Future] = {}
        self._lock = asyncio.Lock()
    
    def _get_cache_key(self, process_number: str, cache_type: str = "full") -> str:
        """Gerar chave de cache normalizada."""
        normalized = normalize_process_number(process_number)
        return f"process:{normalized}:{cache_type}"
    
    async def get_process_full(self, process_number: str, force_refresh: bool = False) -> Optional[Dict[str, Any]]:
        """Obter dados completos do processo com cache inteligente."""
        cache_key = self._get_cache_key(process_number, "full")
        
        # Se não for refresh forçado, verificar cache primeiro
        if not force_refresh:
            cached_data = await cache_service.get(cache_key)
            if cached_data:
                logger.debug(f"📦 Cache hit para processo {process_number}")
                return cached_data
        
        # Verificar se já existe uma requisição pendente para este processo
        async with self._lock:
            if process_number in self._pending_requests:
                logger.debug(f"⏳ Aguardando requisição pendente para {process_number}")
                return await self._pending_requests[process_number]
            
            # Criar nova requisição
            future = asyncio.Future()
            self._pending_requests[process_number] = future
        
        try:
            # Buscar dados na API PDPJ
            logger.info(f"🌐 Buscando dados completos na API PDPJ: {process_number}")
            pdpj_data = await pdpj_client.get_process_full(process_number)
            
            # Armazenar no cache
            await cache_service.set(cache_key, pdpj_data, ttl=self._cache_ttl.total_seconds())
            
            # Resolver future
            future.set_result(pdpj_data)
            return pdpj_data
            
        except PDPJClientError as e:
            logger.error(f"❌ Erro na API PDPJ para {process_number}: {e}")
            future.set_exception(e)
            raise
        except Exception as e:
            logger.error(f"❌ Erro inesperado para {process_number}: {e}")
            future.set_exception(e)
            raise
        finally:
            # Limpar requisição pendente
            async with self._lock:
                self._pending_requests.pop(process_number, None)
    
    async def get_process_documents(self, process_number: str, force_refresh: bool = False) -> Optional[List[Dict[str, Any]]]:
        """Obter documentos do processo com cache."""
        cache_key = self._get_cache_key(process_number, "documents")
        
        if not force_refresh:
            cached_data = await cache_service.get(cache_key)
            if cached_data:
                logger.debug(f"📦 Cache hit para documentos de {process_number}")
                return cached_data
        
        try:
            logger.info(f"📄 Buscando documentos na API PDPJ: {process_number}")
            documents = await pdpj_client.get_process_documents(process_number)
            
            # Armazenar no cache
            await cache_service.set(cache_key, documents, ttl=self._cache_ttl.total_seconds())
            
            return documents
            
        except PDPJClientError as e:
            logger.error(f"❌ Erro ao buscar documentos para {process_number}: {e}")
            raise
    
    async def batch_get_processes(self, process_numbers: List[str]) -> Dict[str, Any]:
        """Buscar múltiplos processos em lote com cache otimizado."""
        logger.info(f"🚀 Iniciando busca em lote de {len(process_numbers)} processos")
        
        # Separar processos em cache e não cache
        cached_processes = {}
        uncached_processes = []
        
        # Verificar cache para todos os processos
        for process_number in process_numbers:
            cache_key = self._get_cache_key(process_number, "full")
            cached_data = await cache_service.get(cache_key)
            if cached_data:
                cached_processes[process_number] = cached_data
            else:
                uncached_processes.append(process_number)
        
        logger.info(f"📦 Cache hit: {len(cached_processes)}, Cache miss: {len(uncached_processes)}")
        
        # Buscar processos não em cache em paralelo
        if uncached_processes:
            logger.info(f"🌐 Buscando {len(uncached_processes)} processos na API PDPJ")
            
            # Usar batch download do cliente PDPJ se disponível
            if hasattr(pdpj_client, 'batch_get_processes'):
                try:
                    batch_results = await pdpj_client.batch_get_processes(uncached_processes)
                    for process_number, data in batch_results.items():
                        if data:
                            cache_key = self._get_cache_key(process_number, "full")
                            await cache_service.set(cache_key, data, ttl=self._batch_cache_ttl.total_seconds())
                            cached_processes[process_number] = data
                except Exception as e:
                    logger.warning(f"⚠️ Batch processing falhou, usando requisições individuais: {e}")
                    # Fallback para requisições individuais
                    await self._fallback_individual_requests(uncached_processes, cached_processes)
            else:
                # Fallback para requisições individuais
                await self._fallback_individual_requests(uncached_processes, cached_processes)
        
        return cached_processes
    
    async def _fallback_individual_requests(self, process_numbers: List[str], cached_processes: Dict[str, Any]):
        """Fallback para requisições individuais quando batch não está disponível."""
        # Processar em lotes menores para evitar sobrecarga
        batch_size = 10
        for i in range(0, len(process_numbers), batch_size):
            batch = process_numbers[i:i + batch_size]
            
            # Criar tasks para processamento paralelo
            tasks = []
            for process_number in batch:
                task = self._fetch_single_process(process_number)
                tasks.append(task)
            
            # Executar em paralelo
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Processar resultados
            for process_number, result in zip(batch, results):
                if isinstance(result, Exception):
                    logger.error(f"❌ Erro ao buscar {process_number}: {result}")
                elif result:
                    cached_processes[process_number] = result
    
    async def _fetch_single_process(self, process_number: str) -> Optional[Dict[str, Any]]:
        """Buscar um único processo e armazenar no cache."""
        try:
            data = await pdpj_client.get_process_full(process_number)
            if data:
                cache_key = self._get_cache_key(process_number, "full")
                await cache_service.set(cache_key, data, ttl=self._batch_cache_ttl.total_seconds())
            return data
        except Exception as e:
            logger.error(f"❌ Erro ao buscar {process_number}: {e}")
            return None
    
    async def invalidate_cache(self, process_number: str):
        """Invalidar cache de um processo específico."""
        cache_keys = [
            self._get_cache_key(process_number, "full"),
            self._get_cache_key(process_number, "documents")
        ]
        
        for cache_key in cache_keys:
            await cache_service.delete(cache_key)
        
        logger.info(f"🗑️ Cache invalidado para processo {process_number}")
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Obter estatísticas do cache."""
        return {
            "pending_requests": len(self._pending_requests),
            "cache_ttl_hours": self._cache_ttl.total_seconds() / 3600,
            "batch_cache_ttl_minutes": self._batch_cache_ttl.total_seconds() / 60
        }


# Instância global do serviço de cache
process_cache_service = ProcessCacheService()
