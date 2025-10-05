"""
Configurações dinâmicas de limites e timeouts por ambiente.
"""

import os
from typing import Dict, Any, Optional
from enum import Enum
from pydantic import BaseModel, Field
from loguru import logger


class Environment(str, Enum):
    """Ambientes disponíveis."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


class DynamicLimits(BaseModel):
    """Limites dinâmicos configuráveis por ambiente."""
    
    # Timeouts
    request_timeout: float = Field(description="Timeout para requisições gerais (segundos)")
    download_timeout: float = Field(description="Timeout para downloads (segundos)")
    batch_timeout: float = Field(description="Timeout para processamento em lote (segundos)")
    
    # Limites de concorrência
    max_concurrent_requests: int = Field(description="Máximo de requisições simultâneas")
    max_concurrent_downloads: int = Field(description="Máximo de downloads simultâneos")
    max_batch_size: int = Field(description="Tamanho máximo de lote")
    
    # Limites de rate limiting
    requests_per_minute: int = Field(description="Requisições por minuto")
    requests_per_hour: int = Field(description="Requisições por hora")
    downloads_per_minute: int = Field(description="Downloads por minuto")
    
    # Limites de memória e tamanho
    max_document_size_mb: int = Field(description="Tamanho máximo de documento (MB)")
    max_batch_memory_mb: int = Field(description="Memória máxima para batch (MB)")
    max_response_size_mb: int = Field(description="Tamanho máximo de resposta (MB)")
    
    # Configurações de retry
    max_retries: int = Field(description="Número máximo de tentativas")
    retry_delay: float = Field(description="Delay inicial entre tentativas (segundos)")
    max_retry_delay: float = Field(description="Delay máximo entre tentativas (segundos)")
    
    # Configurações de cache
    cache_ttl_minutes: int = Field(description="TTL do cache (minutos)")
    batch_cache_ttl_minutes: int = Field(description="TTL do cache de batch (minutos)")


class EnvironmentLimits:
    """Gerenciador de limites por ambiente."""
    
    def __init__(self):
        self._limits: Dict[Environment, DynamicLimits] = {
            Environment.DEVELOPMENT: DynamicLimits(
                request_timeout=30.0,
                download_timeout=60.0,
                batch_timeout=300.0,
                max_concurrent_requests=10,
                max_concurrent_downloads=5,
                max_batch_size=100,
                requests_per_minute=60,
                requests_per_hour=1000,
                downloads_per_minute=30,
                max_document_size_mb=50,
                max_batch_memory_mb=200,
                max_response_size_mb=100,
                max_retries=3,
                retry_delay=1.0,
                max_retry_delay=30.0,
                cache_ttl_minutes=60,
                batch_cache_ttl_minutes=30
            ),
            Environment.STAGING: DynamicLimits(
                request_timeout=45.0,
                download_timeout=90.0,
                batch_timeout=600.0,
                max_concurrent_requests=20,
                max_concurrent_downloads=10,
                max_batch_size=500,
                requests_per_minute=120,
                requests_per_hour=5000,
                downloads_per_minute=60,
                max_document_size_mb=100,
                max_batch_memory_mb=500,
                max_response_size_mb=200,
                max_retries=5,
                retry_delay=2.0,
                max_retry_delay=60.0,
                cache_ttl_minutes=120,
                batch_cache_ttl_minutes=60
            ),
            Environment.PRODUCTION: DynamicLimits(
                request_timeout=60.0,
                download_timeout=120.0,
                batch_timeout=1800.0,
                max_concurrent_requests=50,
                max_concurrent_downloads=25,
                max_batch_size=1000,
                requests_per_minute=300,
                requests_per_hour=10000,
                downloads_per_minute=150,
                max_document_size_mb=200,
                max_batch_memory_mb=1000,
                max_response_size_mb=500,
                max_retries=7,
                retry_delay=3.0,
                max_retry_delay=120.0,
                cache_ttl_minutes=240,
                batch_cache_ttl_minutes=120
            ),
            Environment.TESTING: DynamicLimits(
                request_timeout=10.0,
                download_timeout=20.0,
                batch_timeout=60.0,
                max_concurrent_requests=5,
                max_concurrent_downloads=2,
                max_batch_size=10,
                requests_per_minute=100,
                requests_per_hour=1000,
                downloads_per_minute=50,
                max_document_size_mb=10,
                max_batch_memory_mb=50,
                max_response_size_mb=20,
                max_retries=2,
                retry_delay=0.5,
                max_retry_delay=5.0,
                cache_ttl_minutes=5,
                batch_cache_ttl_minutes=2
            )
        }
        
        self._current_environment = self._detect_environment()
        self._custom_limits: Optional[DynamicLimits] = None
    
    def _detect_environment(self) -> Environment:
        """Detectar ambiente atual."""
        env = os.getenv("ENVIRONMENT", "development").lower()
        
        if env in ["dev", "development"]:
            return Environment.DEVELOPMENT
        elif env in ["staging", "stage"]:
            return Environment.STAGING
        elif env in ["prod", "production"]:
            return Environment.PRODUCTION
        elif env in ["test", "testing"]:
            return Environment.TESTING
        else:
            logger.warning(f"⚠️ Ambiente desconhecido: {env}, usando development")
            return Environment.DEVELOPMENT
    
    def get_limits(self) -> DynamicLimits:
        """Obter limites do ambiente atual."""
        if self._custom_limits:
            return self._custom_limits
        
        limits = self._limits[self._current_environment]
        logger.debug(f"🔧 Usando limites para ambiente: {self._current_environment}")
        return limits
    
    def set_custom_limits(self, limits: DynamicLimits):
        """Definir limites customizados."""
        self._custom_limits = limits
        logger.info("🔧 Limites customizados definidos")
    
    def reset_to_environment_limits(self):
        """Resetar para limites do ambiente."""
        self._custom_limits = None
        logger.info(f"🔧 Resetado para limites do ambiente: {self._current_environment}")
    
    def get_environment(self) -> Environment:
        """Obter ambiente atual."""
        return self._current_environment
    
    def update_environment_limits(self, environment: Environment, limits: DynamicLimits):
        """Atualizar limites de um ambiente específico."""
        self._limits[environment] = limits
        logger.info(f"🔧 Limites atualizados para ambiente: {environment}")
    
    def get_limits_for_environment(self, environment: Environment) -> DynamicLimits:
        """Obter limites para um ambiente específico."""
        return self._limits[environment]
    
    def validate_limits(self, limits: DynamicLimits) -> bool:
        """Validar se os limites são válidos."""
        try:
            # Validar valores mínimos
            if limits.request_timeout < 1.0:
                logger.error("❌ request_timeout deve ser >= 1.0")
                return False
            
            if limits.max_concurrent_requests < 1:
                logger.error("❌ max_concurrent_requests deve ser >= 1")
                return False
            
            if limits.max_batch_size < 1:
                logger.error("❌ max_batch_size deve ser >= 1")
                return False
            
            if limits.max_document_size_mb < 1:
                logger.error("❌ max_document_size_mb deve ser >= 1")
                return False
            
            # Validar proporções
            if limits.download_timeout < limits.request_timeout:
                logger.warning("⚠️ download_timeout < request_timeout pode causar problemas")
            
            if limits.max_concurrent_downloads > limits.max_concurrent_requests:
                logger.warning("⚠️ max_concurrent_downloads > max_concurrent_requests pode causar problemas")
            
            logger.info("✅ Limites validados com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro na validação dos limites: {e}")
            return False
    
    def get_limits_summary(self) -> Dict[str, Any]:
        """Obter resumo dos limites atuais."""
        limits = self.get_limits()
        return {
            "environment": self._current_environment.value,
            "timeouts": {
                "request": limits.request_timeout,
                "download": limits.download_timeout,
                "batch": limits.batch_timeout
            },
            "concurrency": {
                "max_requests": limits.max_concurrent_requests,
                "max_downloads": limits.max_concurrent_downloads,
                "max_batch_size": limits.max_batch_size
            },
            "rate_limits": {
                "requests_per_minute": limits.requests_per_minute,
                "requests_per_hour": limits.requests_per_hour,
                "downloads_per_minute": limits.downloads_per_minute
            },
            "memory_limits": {
                "max_document_size_mb": limits.max_document_size_mb,
                "max_batch_memory_mb": limits.max_batch_memory_mb,
                "max_response_size_mb": limits.max_response_size_mb
            },
            "retry_config": {
                "max_retries": limits.max_retries,
                "retry_delay": limits.retry_delay,
                "max_retry_delay": limits.max_retry_delay
            },
            "cache_config": {
                "cache_ttl_minutes": limits.cache_ttl_minutes,
                "batch_cache_ttl_minutes": limits.batch_cache_ttl_minutes
            }
        }


# Instância global
environment_limits = EnvironmentLimits()


def get_current_limits() -> DynamicLimits:
    """Obter limites do ambiente atual."""
    return environment_limits.get_limits()


def get_limits_for_environment(environment: Environment) -> DynamicLimits:
    """Obter limites para um ambiente específico."""
    return environment_limits.get_limits_for_environment(environment)


def update_limits_for_environment(environment: Environment, limits: DynamicLimits):
    """Atualizar limites para um ambiente específico."""
    if environment_limits.validate_limits(limits):
        environment_limits.update_environment_limits(environment, limits)
    else:
        raise ValueError("Limites inválidos fornecidos")


def set_custom_limits(limits: DynamicLimits):
    """Definir limites customizados."""
    if environment_limits.validate_limits(limits):
        environment_limits.set_custom_limits(limits)
    else:
        raise ValueError("Limites inválidos fornecidos")
