"""Serviço de cache Redis."""

import json
import pickle
from typing import Any, Optional, Union
from datetime import datetime, timedelta
import redis.asyncio as redis
from loguru import logger

from app.core.config import settings


class CacheService:
    """Serviço de cache usando Redis."""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self._connection_pool: Optional[redis.ConnectionPool] = None
    
    async def connect(self):
        """Conectar ao Redis."""
        try:
            self._connection_pool = redis.ConnectionPool.from_url(
                settings.redis_url,
                decode_responses=False,  # Manter bytes para compatibilidade
                max_connections=20
            )
            self.redis_client = redis.Redis(connection_pool=self._connection_pool)
            
            # Testar conexão
            await self.redis_client.ping()
            logger.info("Conectado ao Redis com sucesso")
            
        except Exception as e:
            logger.error(f"Erro ao conectar ao Redis: {e}")
            raise
    
    async def disconnect(self):
        """Desconectar do Redis."""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Desconectado do Redis")
    
    async def get(self, key: str) -> Optional[Any]:
        """Obter valor do cache."""
        if not self.redis_client:
            return None
        
        try:
            value = await self.redis_client.get(key)
            if value is None:
                return None
            
            # Tentar deserializar como JSON primeiro, depois como pickle
            try:
                return json.loads(value.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError):
                return pickle.loads(value)
                
        except Exception as e:
            logger.error(f"Erro ao obter cache key {key}: {e}")
            return None
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None
    ) -> bool:
        """Definir valor no cache."""
        if not self.redis_client:
            return False
        
        try:
            # Usar TTL padrão se não especificado
            if ttl is None:
                ttl = settings.cache_ttl
            
            # Tentar serializar como JSON primeiro
            try:
                serialized_value = json.dumps(value, default=str)
            except (TypeError, ValueError):
                # Se JSON falhar, usar pickle
                serialized_value = pickle.dumps(value)
            
            await self.redis_client.setex(key, ttl, serialized_value)
            return True
            
        except Exception as e:
            logger.error(f"Erro ao definir cache key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Deletar chave do cache."""
        if not self.redis_client:
            return False
        
        try:
            result = await self.redis_client.delete(key)
            return bool(result)
        except Exception as e:
            logger.error(f"Erro ao deletar cache key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Verificar se chave existe no cache."""
        if not self.redis_client:
            return False
        
        try:
            result = await self.redis_client.exists(key)
            return bool(result)
        except Exception as e:
            logger.error(f"Erro ao verificar cache key {key}: {e}")
            return False
    
    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Incrementar valor numérico no cache."""
        if not self.redis_client:
            return None
        
        try:
            result = await self.redis_client.incrby(key, amount)
            return result
        except Exception as e:
            logger.error(f"Erro ao incrementar cache key {key}: {e}")
            return None
    
    async def expire(self, key: str, ttl: int) -> bool:
        """Definir TTL para uma chave existente."""
        if not self.redis_client:
            return False
        
        try:
            result = await self.redis_client.expire(key, ttl)
            return bool(result)
        except Exception as e:
            logger.error(f"Erro ao definir TTL para cache key {key}: {e}")
            return False
    
    async def get_ttl(self, key: str) -> int:
        """Obter TTL restante de uma chave."""
        if not self.redis_client:
            return -1
        
        try:
            return await self.redis_client.ttl(key)
        except Exception as e:
            logger.error(f"Erro ao obter TTL para cache key {key}: {e}")
            return -1
    
    async def flush_all(self) -> bool:
        """Limpar todo o cache (usar com cuidado!)."""
        if not self.redis_client:
            return False
        
        try:
            await self.redis_client.flushdb()
            logger.warning("Cache Redis foi limpo completamente")
            return True
        except Exception as e:
            logger.error(f"Erro ao limpar cache: {e}")
            return False


# Instância global do serviço de cache
cache_service = CacheService()


def get_cache_key(prefix: str, *args) -> str:
    """Gerar chave de cache consistente."""
    return f"pdpj:{prefix}:" + ":".join(str(arg) for arg in args)


def get_process_cache_key(process_number: str, data_type: str = "full") -> str:
    """Gerar chave de cache para processos."""
    return get_cache_key("process", process_number, data_type)


def get_user_cache_key(user_id: int, endpoint: str) -> str:
    """Gerar chave de cache para usuários."""
    return get_cache_key("user", user_id, endpoint)
