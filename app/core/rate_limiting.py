"""Middleware de rate limiting otimizado para FastAPI."""

import time
import uuid
from abc import ABC, abstractmethod
from typing import Dict, Optional, List
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from loguru import logger

from app.core.config import settings


class RateLimitStorage(ABC):
    """Interface abstrata para storage de rate limiting."""
    
    @abstractmethod
    async def get_client_requests(self, client_ip: str, window_start: float) -> List[float]:
        """Obter requisições do cliente dentro da janela de tempo."""
        pass
    
    @abstractmethod
    async def add_client_request(self, client_ip: str, request_time: float) -> None:
        """Adicionar nova requisição do cliente."""
        pass
    
    @abstractmethod
    async def cleanup_old_entries(self, cutoff_time: float) -> int:
        """Limpar entradas antigas e retornar quantidade removida."""
        pass


class InMemoryRateLimitStorage(RateLimitStorage):
    """Implementação em memória do storage de rate limiting."""
    
    def __init__(self):
        self.clients: Dict[str, Dict] = {}
    
    async def get_client_requests(self, client_ip: str, window_start: float) -> List[float]:
        """Obter requisições do cliente dentro da janela de tempo."""
        if client_ip not in self.clients:
            return []
        
        client_data = self.clients[client_ip]
        return [req_time for req_time in client_data["requests"] if req_time > window_start]
    
    async def add_client_request(self, client_ip: str, request_time: float) -> None:
        """Adicionar nova requisição do cliente."""
        if client_ip not in self.clients:
            self.clients[client_ip] = {
                "requests": [],
                "last_request": request_time
            }
        
        client_data = self.clients[client_ip]
        client_data["requests"].append(request_time)
        client_data["last_request"] = request_time
    
    async def cleanup_old_entries(self, cutoff_time: float) -> int:
        """Limpar entradas antigas e retornar quantidade removida."""
        clients_to_remove = []
        
        for client_ip, client_data in self.clients.items():
            if client_data["last_request"] < cutoff_time:
                clients_to_remove.append(client_ip)
        
        for client_ip in clients_to_remove:
            if client_ip in self.clients:
                del self.clients[client_ip]
        
        return len(clients_to_remove)


class RedisRateLimitStorage(RateLimitStorage):
    """Implementação Redis do storage de rate limiting para produção."""
    
    def __init__(self, redis_client, key_prefix: str = "rate_limit"):
        """Inicializar storage Redis.
        
        Args:
            redis_client: Cliente Redis assíncrono
            key_prefix: Prefixo para as chaves Redis
        """
        self.redis = redis_client
        self.key_prefix = key_prefix
    
    def _get_client_key(self, client_ip: str) -> str:
        """Obter chave Redis para o cliente."""
        return f"{self.key_prefix}:{client_ip}"
    
    async def get_client_requests(self, client_ip: str, window_start: float) -> List[float]:
        """Obter requisições do cliente dentro da janela de tempo usando Redis sorted sets."""
        try:
            client_key = self._get_client_key(client_ip)
            
            # Usar ZRANGEBYSCORE para obter requisições dentro da janela
            # Redis sorted sets usam timestamp como score
            request_timestamps = await self.redis.zrangebyscore(
                client_key, 
                min=window_start, 
                max="+inf", 
                withscores=True
            )
            
            # Extrair apenas os timestamps (scores)
            return [float(timestamp) for _, timestamp in request_timestamps]
            
        except Exception as e:
            logger.error(f"Erro ao obter requisições do Redis para {client_ip}: {str(e)}")
            return []
    
    async def add_client_request(self, client_ip: str, request_time: float) -> None:
        """Adicionar nova requisição do cliente usando Redis sorted sets."""
        try:
            client_key = self._get_client_key(client_ip)
            
            # Usar ZADD para adicionar requisição com timestamp como score
            # Usar request_time como member e score para ordenação temporal
            await self.redis.zadd(client_key, {str(request_time): request_time})
            
            # Definir TTL para a chave (2x a janela de rate limiting)
            # Isso garante que dados antigos sejam removidos automaticamente
            await self.redis.expire(client_key, int(3600 * 2))  # 2 horas TTL
            
        except Exception as e:
            logger.error(f"Erro ao adicionar requisição no Redis para {client_ip}: {str(e)}")
            raise
    
    async def cleanup_old_entries(self, cutoff_time: float) -> int:
        """Limpar entradas antigas do Redis."""
        try:
            # Obter todas as chaves do rate limiting
            pattern = f"{self.key_prefix}:*"
            keys = await self.redis.keys(pattern)
            
            removed_count = 0
            
            for key in keys:
                # Remover entradas antigas de cada chave
                removed = await self.redis.zremrangebyscore(key, 0, cutoff_time)
                removed_count += removed
                
                # Se a chave ficou vazia, removê-la
                if await self.redis.zcard(key) == 0:
                    await self.redis.delete(key)
            
            return removed_count
            
        except Exception as e:
            logger.error(f"Erro durante limpeza Redis: {str(e)}")
            return 0
    
    async def get_stats(self) -> Dict[str, int]:
        """Obter estatísticas do storage Redis."""
        try:
            pattern = f"{self.key_prefix}:*"
            keys = await self.redis.keys(pattern)
            
            total_clients = len(keys)
            total_requests = 0
            
            for key in keys:
                total_requests += await self.redis.zcard(key)
            
            return {
                "total_clients": total_clients,
                "total_requests": total_requests
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas Redis: {str(e)}")
            return {"total_clients": 0, "total_requests": 0}


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware de rate limiting com storage configurável."""
    
    def __init__(self, app: ASGIApp, storage: Optional[RateLimitStorage] = None):
        super().__init__(app)
        self.rate_limit_requests = settings.rate_limit_requests
        self.rate_limit_window = settings.rate_limit_window
        
        # Usar storage fornecido ou padrão em memória
        self.storage = storage or InMemoryRateLimitStorage()
        
        # Configuração de limpeza otimizada
        self.last_cleanup = time.time()
        self.cleanup_interval = 300  # 5 minutos
        self.max_clients_before_cleanup = 1000  # Limiar para forçar limpeza
        
        # Cache de validação de IP para otimização
        self._ip_validation_cache: Dict[str, bool] = {}
        self._cache_max_size = 10000  # Máximo de IPs em cache
        self._cache_ttl = 3600  # TTL do cache em segundos
        self._cache_timestamps: Dict[str, float] = {}
    
    async def dispatch(self, request: Request, call_next):
        """Processar requisição com rate limiting."""
        
        try:
            # Gerar request ID se não existir
            request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
            request.state.request_id = request_id
            
            # Adicionar request ID ao contexto de log
            bound_logger = logger.bind(request_id=request_id)
            
            # Verificar rate limiting
            client_ip = self._get_client_ip(request)
            
            # Validar configurações
            if self.rate_limit_requests <= 0 or self.rate_limit_window <= 0:
                bound_logger.error("Configuração de rate limiting inválida")
                # Continuar sem rate limiting se configuração inválida
                response = await call_next(request)
                response.headers["X-Request-ID"] = request_id
                return response
            
            if not await self._check_rate_limit(client_ip):
                bound_logger.warning(f"Rate limit excedido para IP {client_ip}")
                
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "error": "Rate limit exceeded",
                        "message": f"Máximo de {self.rate_limit_requests} requisições por {self.rate_limit_window} segundos",
                        "request_id": request_id
                    },
                    headers={
                        "X-RateLimit-Limit": str(self.rate_limit_requests),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(int(time.time()) + self.rate_limit_window),
                        "X-Request-ID": request_id
                    }
                )
        
        except Exception as e:
            bound_logger.error(f"Erro no rate limiting: {str(e)}")
            # Em caso de erro, continuar sem rate limiting
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response
        
        # Processar requisição
        start_time = time.time()
        
        try:
            response = await call_next(request)
            
            # Adicionar headers de rate limiting
            remaining = await self._get_remaining_requests(client_ip)
            reset_time = int(time.time()) + self.rate_limit_window
            
            response.headers["X-RateLimit-Limit"] = str(self.rate_limit_requests)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Reset"] = str(reset_time)
            response.headers["X-Request-ID"] = request_id
            
            # Log da requisição
            process_time = time.time() - start_time
            bound_logger.info(
                f"Request {request.method} {request.url.path} - "
                f"Status: {response.status_code} - "
                f"Time: {process_time:.3f}s - "
                f"IP: {client_ip} - "
                f"Rate Limit: {remaining}/{self.rate_limit_requests}"
            )
            
            return response
            
        except Exception as e:
            # Log de erro
            process_time = time.time() - start_time
            bound_logger.error(
                f"Request {request.method} {request.url.path} - "
                f"Error: {str(e)} - "
                f"Time: {process_time:.3f}s - "
                f"IP: {client_ip} - "
                f"Request ID: {request_id}"
            )
            raise
    
    def _get_client_ip(self, request: Request) -> str:
        """Obter IP real do cliente com suporte a múltiplos proxies."""
        # Lista de headers para verificar (em ordem de prioridade)
        proxy_headers = [
            "X-Forwarded-For",
            "X-Real-IP", 
            "CF-Connecting-IP",  # Cloudflare
            "True-Client-IP",    # Akamai
            "X-Client-IP",
            "X-Cluster-Client-IP"
        ]
        
        # Verificar cada header de proxy
        for header in proxy_headers:
            header_value = request.headers.get(header)
            if header_value:
                # Para X-Forwarded-For, pegar o primeiro IP (cliente original)
                if header == "X-Forwarded-For":
                    # Separar por vírgula e pegar o primeiro IP válido
                    ips = [ip.strip() for ip in header_value.split(",")]
                    for ip in ips:
                        if self._is_valid_ip(ip):
                            return ip
                else:
                    # Para outros headers, usar o valor diretamente se válido
                    if self._is_valid_ip(header_value.strip()):
                        return header_value.strip()
        
        # Fallback para IP direto da conexão
        if hasattr(request.client, 'host') and request.client.host:
            return request.client.host
        
        # Fallback final
        return "unknown"
    
    def _is_valid_ip(self, ip: str) -> bool:
        """Validar se um IP é válido com cache para otimização."""
        if not ip or ip == "unknown":
            return False
        
        # Verificar cache primeiro
        current_time = time.time()
        if ip in self._ip_validation_cache:
            # Verificar se o cache ainda é válido
            if current_time - self._cache_timestamps.get(ip, 0) < self._cache_ttl:
                return self._ip_validation_cache[ip]
            else:
                # Cache expirado, remover
                self._ip_validation_cache.pop(ip, None)
                self._cache_timestamps.pop(ip, None)
        
        # Validar IP
        is_valid = self._validate_ip_format(ip)
        
        # Adicionar ao cache se não estiver cheio
        if len(self._ip_validation_cache) < self._cache_max_size:
            self._ip_validation_cache[ip] = is_valid
            self._cache_timestamps[ip] = current_time
        
        return is_valid
    
    def _validate_ip_format(self, ip: str) -> bool:
        """Validar formato de IP sem cache (IPv4 e IPv6)."""
        if not ip or ip == "unknown":
            return False
        
        # Verificar se é IP privado/localhost (opcional)
        # Para rate limiting, você pode querer incluir IPs privados
        private_prefixes = ["127.", "192.168.", "10.", "172."]
        if any(ip.startswith(prefix) for prefix in private_prefixes):
            return True  # Aceitar IPs privados para rate limiting
        
        # IPv6 localhost
        if ip == "::1":
            return True
        
        # Validação IPv4
        if "." in ip:
            return self._validate_ipv4(ip)
        
        # Validação IPv6
        if ":" in ip:
            return self._validate_ipv6(ip)
        
        return False
    
    def _validate_ipv4(self, ip: str) -> bool:
        """Validar formato IPv4."""
        parts = ip.split(".")
        if len(parts) != 4:
            return False
        
        try:
            for part in parts:
                num = int(part)
                if not 0 <= num <= 255:
                    return False
            return True
        except ValueError:
            return False
    
    def _validate_ipv6(self, ip: str) -> bool:
        """Validar formato IPv6 básico."""
        # Remover colchetes se presentes
        if ip.startswith("[") and ip.endswith("]"):
            ip = ip[1:-1]
        
        # Verificar se contém apenas caracteres válidos
        valid_chars = set("0123456789abcdefABCDEF:")
        if not all(c in valid_chars for c in ip):
            return False
        
        # Verificar se tem no máximo 8 grupos
        groups = ip.split(":")
        if len(groups) > 8:
            return False
        
        # Verificar se cada grupo tem no máximo 4 caracteres
        for group in groups:
            if len(group) > 4:
                return False
            
            # Se não está vazio, deve ser um hex válido
            if group and not all(c in "0123456789abcdefABCDEF" for c in group):
                return False
        
        # Verificar se não tem mais de uma sequência de zeros consecutivos
        if ip.count("::") > 1:
            return False
        
        return True
    
    async def _check_rate_limit(self, client_ip: str) -> bool:
        """Verificar se o cliente está dentro do rate limit."""
        try:
            current_time = time.time()
            
            # Limpar dados antigos periodicamente
            if current_time - self.last_cleanup > self.cleanup_interval:
                await self._cleanup_old_entries(current_time)
                self.last_cleanup = current_time
            
            # Obter requisições recentes do cliente
            window_start = current_time - self.rate_limit_window
            recent_requests = await self.storage.get_client_requests(client_ip, window_start)
            
            # Verificar se excedeu o limite
            if len(recent_requests) >= self.rate_limit_requests:
                return False
            
            # Adicionar nova requisição
            await self.storage.add_client_request(client_ip, current_time)
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao verificar rate limit para {client_ip}: {str(e)}")
            # Em caso de erro, permitir a requisição (fail-open)
            return True

    async def _get_remaining_requests(self, client_ip: str) -> int:
        """Obter número de requisições restantes."""
        try:
            current_time = time.time()
            window_start = current_time - self.rate_limit_window
            
            recent_requests = await self.storage.get_client_requests(client_ip, window_start)
            return max(0, self.rate_limit_requests - len(recent_requests))
            
        except Exception as e:
            logger.error(f"Erro ao obter requisições restantes para {client_ip}: {str(e)}")
            # Em caso de erro, retornar limite completo
            return self.rate_limit_requests
    
    async def _cleanup_old_entries(self, current_time: float):
        """Limpar entradas antigas para economizar memória de forma otimizada."""
        try:
            cutoff_time = current_time - (self.rate_limit_window * 2)  # Manter 2x a janela
            
            removed_count = await self.storage.cleanup_old_entries(cutoff_time)
            
            if removed_count > 0:
                logger.debug(f"Limpeza de rate limiting: removidos {removed_count} clientes inativos")
                
        except Exception as e:
            logger.error(f"Erro durante limpeza de rate limiting: {str(e)}")


def create_rate_limit_middleware(app, storage: Optional[RateLimitStorage] = None):
    """Criar middleware de rate limiting se habilitado.
    
    Args:
        app: Aplicação FastAPI
        storage: Instância de storage para rate limiting (opcional, usa InMemory por padrão)
    
    Returns:
        Middleware de rate limiting ou aplicação original
    """
    if settings.enable_rate_limiting:
        storage_type = storage.__class__.__name__ if storage else "InMemoryRateLimitStorage"
        logger.info(
            f"Rate limiting habilitado: {settings.rate_limit_requests} req/{settings.rate_limit_window}s "
            f"com storage: {storage_type}"
        )
        return RateLimitMiddleware(app, storage=storage)
    else:
        logger.info("Rate limiting desabilitado")
        return app


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware para gerar e propagar request ID."""
    
    async def dispatch(self, request: Request, call_next):
        """Adicionar request ID a todas as requisições."""
        
        # Gerar request ID se não existir
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id
        
        # Contextualizar logs com request_id
        bound_logger = None
        if settings.log_request_id:
            from loguru import logger
            bound_logger = logger.bind(request_id=request_id)
            bound_logger.debug(f"Request iniciada: {request.method} {request.url.path}")
        
        try:
            # Processar requisição
            response = await call_next(request)
            
            # Adicionar request ID à resposta
            response.headers["X-Request-ID"] = request_id
            
            if bound_logger:
                bound_logger.debug(f"Request finalizada: {request.method} {request.url.path} - Status: {response.status_code}")
            
            return response
            
        except Exception as e:
            if bound_logger:
                bound_logger.error(f"Erro na request {request.method} {request.url.path}: {str(e)}")
            raise


def create_request_id_middleware(app):
    """Criar middleware de request ID se habilitado."""
    if settings.log_request_id:
        logger.info("Request ID middleware habilitado")
        return RequestIDMiddleware(app)
    else:
        return app