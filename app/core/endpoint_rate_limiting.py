"""
Rate limiting específico para endpoints de processos.
"""

import asyncio
import time
from typing import Dict, Optional, Any
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from loguru import logger

from app.core.rate_limiting import InMemoryRateLimitStorage, create_rate_limit_middleware


class EndpointRateLimiter:
    """Rate limiter específico para endpoints de processos."""
    
    def __init__(self):
        self._user_limits: Dict[str, Dict[str, Any]] = {}
        self._endpoint_limits = {
            "search_processes": {"requests_per_minute": 10, "requests_per_hour": 100},
            "download_documents": {"requests_per_minute": 5, "requests_per_hour": 50},
            "batch_search": {"requests_per_minute": 2, "requests_per_hour": 20},
            "get_process": {"requests_per_minute": 30, "requests_per_hour": 500},
            "get_files": {"requests_per_minute": 20, "requests_per_hour": 200}
        }
    
    def get_user_limits(self, user_id: str) -> Dict[str, Any]:
        """Obter limites específicos do usuário."""
        if user_id not in self._user_limits:
            # Limites padrão para novos usuários
            self._user_limits[user_id] = {
                "search_processes": {"requests_per_minute": 10, "requests_per_hour": 100},
                "download_documents": {"requests_per_minute": 5, "requests_per_hour": 50},
                "batch_search": {"requests_per_minute": 2, "requests_per_hour": 20},
                "get_process": {"requests_per_minute": 30, "requests_per_hour": 500},
                "get_files": {"requests_per_minute": 20, "requests_per_hour": 200}
            }
        return self._user_limits[user_id]
    
    def set_user_limits(self, user_id: str, limits: Dict[str, Any]):
        """Definir limites específicos para um usuário."""
        self._user_limits[user_id] = limits
        logger.info(f"🔧 Limites atualizados para usuário {user_id}")
    
    def get_endpoint_limits(self, endpoint: str) -> Dict[str, int]:
        """Obter limites para um endpoint específico."""
        return self._endpoint_limits.get(endpoint, {"requests_per_minute": 10, "requests_per_hour": 100})
    
    async def check_rate_limit(self, request: Request, user_id: str, endpoint: str, 
                              requests_per_minute: int, requests_per_hour: int):
        """Verificar rate limit para um usuário e endpoint específico."""
        current_time = time.time()
        
        # Verificar limite por minuto
        minute_key = f"{user_id}:{endpoint}:minute:{int(current_time // 60)}"
        minute_requests = self._get_requests_count(minute_key)
        
        if minute_requests >= requests_per_minute:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Limite de {requests_per_minute} requisições por minuto excedido para {endpoint}"
            )
        
        # Verificar limite por hora
        hour_key = f"{user_id}:{endpoint}:hour:{int(current_time // 3600)}"
        hour_requests = self._get_requests_count(hour_key)
        
        if hour_requests >= requests_per_hour:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Limite de {requests_per_hour} requisições por hora excedido para {endpoint}"
            )
        
        # Registrar requisição
        self._record_request(minute_key)
        self._record_request(hour_key)
    
    def _get_requests_count(self, key: str) -> int:
        """Obter contagem de requisições para uma chave."""
        # Implementação simples em memória
        if not hasattr(self, '_request_counts'):
            self._request_counts = {}
        
        return self._request_counts.get(key, 0)
    
    def _record_request(self, key: str):
        """Registrar uma requisição."""
        if not hasattr(self, '_request_counts'):
            self._request_counts = {}
        
        self._request_counts[key] = self._request_counts.get(key, 0) + 1


# Instância global
endpoint_rate_limiter = EndpointRateLimiter()


def create_endpoint_rate_limit(endpoint_name: str):
    """Criar decorator de rate limiting para endpoint específico."""
    
    async def rate_limit_check(request: Request, current_user=None):
        """Verificar rate limit para endpoint específico."""
        user_id = str(current_user.id) if current_user else "anonymous"
        
        # Obter limites do usuário
        user_limits = endpoint_rate_limiter.get_user_limits(user_id)
        endpoint_limits = user_limits.get(endpoint_name, endpoint_rate_limiter.get_endpoint_limits(endpoint_name))
        
        # Verificar rate limit usando o endpoint rate limiter
        try:
            # Usar o endpoint rate limiter com limites específicos
            await endpoint_rate_limiter.check_rate_limit(
                request,
                user_id=user_id,
                endpoint=endpoint_name,
                requests_per_minute=endpoint_limits["requests_per_minute"],
                requests_per_hour=endpoint_limits["requests_per_hour"]
            )
        except HTTPException as e:
            logger.warning(f"⚠️ Rate limit excedido para {user_id} em {endpoint_name}")
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit excedido",
                    "endpoint": endpoint_name,
                    "limits": endpoint_limits,
                    "retry_after": 60  # segundos
                }
            )
        
        return None
    
    return rate_limit_check


def create_batch_size_limit(max_processes: int = 1000):
    """Criar limitador de tamanho de lote."""
    
    async def batch_size_check(request: Request, search_request=None):
        """Verificar tamanho do lote."""
        if search_request and len(search_request.process_numbers) > max_processes:
            logger.warning(f"⚠️ Lote muito grande: {len(search_request.process_numbers)} > {max_processes}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Máximo de {max_processes} processos por requisição"
            )
        return None
    
    return batch_size_check


def create_download_throttle(max_concurrent_downloads: int = 5):
    """Criar throttling para downloads."""
    
    class DownloadThrottle:
        def __init__(self):
            self._active_downloads: Dict[str, int] = {}
            self._lock = asyncio.Lock()
        
        async def acquire(self, user_id: str) -> bool:
            """Adquirir slot de download."""
            async with self._lock:
                current_downloads = self._active_downloads.get(user_id, 0)
                if current_downloads >= max_concurrent_downloads:
                    return False
                
                self._active_downloads[user_id] = current_downloads + 1
                return True
        
        async def release(self, user_id: str):
            """Liberar slot de download."""
            async with self._lock:
                current_downloads = self._active_downloads.get(user_id, 0)
                if current_downloads > 0:
                    self._active_downloads[user_id] = current_downloads - 1
    
    return DownloadThrottle()


# Instâncias globais
download_throttle = create_download_throttle()

# Decorators pré-configurados
search_processes_rate_limit = create_endpoint_rate_limit("search_processes")
download_documents_rate_limit = create_endpoint_rate_limit("download_documents")
batch_search_rate_limit = create_endpoint_rate_limit("batch_search")
get_process_rate_limit = create_endpoint_rate_limit("get_process")
get_files_rate_limit = create_endpoint_rate_limit("get_files")

batch_size_limit = create_batch_size_limit(1000)
