"""
Sistema avançado de retry com backoff exponencial e jitter.
"""

import asyncio
import random
import time
from typing import Callable, Any, Optional, Dict, List, Type, Union
from functools import wraps
from enum import Enum
from dataclasses import dataclass
from loguru import logger

from app.core.dynamic_limits import get_current_limits


class RetryStrategy(str, Enum):
    """Estratégias de retry."""
    EXPONENTIAL = "exponential"
    LINEAR = "linear"
    FIXED = "fixed"
    CUSTOM = "custom"


class RetryCondition(str, Enum):
    """Condições para retry."""
    ALL_EXCEPTIONS = "all_exceptions"
    SPECIFIC_EXCEPTIONS = "specific_exceptions"
    HTTP_ERRORS = "http_errors"
    TIMEOUT_ERRORS = "timeout_errors"
    RATE_LIMIT_ERRORS = "rate_limit_errors"


@dataclass
class RetryConfig:
    """Configuração de retry."""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    jitter: bool = True
    jitter_range: float = 0.1
    backoff_multiplier: float = 2.0
    condition: RetryCondition = RetryCondition.ALL_EXCEPTIONS
    specific_exceptions: List[Type[Exception]] = None
    http_status_codes: List[int] = None
    timeout_seconds: Optional[float] = None


class AdvancedRetry:
    """Sistema avançado de retry com backoff exponencial."""
    
    def __init__(self, config: RetryConfig = None):
        self.config = config or RetryConfig()
        self.limits = get_current_limits()
        
        # Aplicar limites do ambiente
        self.config.max_attempts = min(self.config.max_attempts, self.limits.max_retries)
        self.config.max_delay = min(self.config.max_delay, self.limits.max_retry_delay)
        self.config.base_delay = min(self.config.base_delay, self.limits.retry_delay)
    
    def calculate_delay(self, attempt: int) -> float:
        """Calcular delay para a tentativa atual."""
        if attempt <= 0:
            return 0.0
        
        # Calcular delay base
        if self.config.strategy == RetryStrategy.EXPONENTIAL:
            delay = self.config.base_delay * (self.config.backoff_multiplier ** (attempt - 1))
        elif self.config.strategy == RetryStrategy.LINEAR:
            delay = self.config.base_delay * attempt
        elif self.config.strategy == RetryStrategy.FIXED:
            delay = self.config.base_delay
        else:
            delay = self.config.base_delay
        
        # Aplicar delay máximo
        delay = min(delay, self.config.max_delay)
        
        # Aplicar jitter se habilitado
        if self.config.jitter:
            jitter_amount = delay * self.config.jitter_range
            jitter = random.uniform(-jitter_amount, jitter_amount)
            delay += jitter
        
        # Garantir delay mínimo
        delay = max(delay, 0.1)
        
        return delay
    
    def should_retry(self, exception: Exception, attempt: int) -> bool:
        """Determinar se deve tentar novamente."""
        if attempt >= self.config.max_attempts:
            return False
        
        # Verificar condição de retry
        if self.config.condition == RetryCondition.ALL_EXCEPTIONS:
            return True
        elif self.config.condition == RetryCondition.SPECIFIC_EXCEPTIONS:
            return isinstance(exception, tuple(self.config.specific_exceptions or []))
        elif self.config.condition == RetryCondition.HTTP_ERRORS:
            return hasattr(exception, 'status_code') and exception.status_code in (self.config.http_status_codes or [])
        elif self.config.condition == RetryCondition.TIMEOUT_ERRORS:
            return isinstance(exception, (asyncio.TimeoutError, TimeoutError))
        elif self.config.condition == RetryCondition.RATE_LIMIT_ERRORS:
            return hasattr(exception, 'status_code') and exception.status_code == 429
        
        return False
    
    async def execute_with_retry(self, func: Callable, *args, **kwargs) -> Any:
        """Executar função com retry."""
        last_exception = None
        
        for attempt in range(1, self.config.max_attempts + 1):
            try:
                # Aplicar timeout se configurado
                if self.config.timeout_seconds:
                    return await asyncio.wait_for(
                        func(*args, **kwargs),
                        timeout=self.config.timeout_seconds
                    )
                else:
                    return await func(*args, **kwargs)
                    
            except Exception as e:
                last_exception = e
                
                # Verificar se deve tentar novamente
                if not self.should_retry(e, attempt):
                    logger.error(f"❌ Não será tentado novamente: {e}")
                    break
                
                # Calcular delay
                delay = self.calculate_delay(attempt)
                
                logger.warning(f"⚠️ Tentativa {attempt} falhou: {e}")
                logger.info(f"⏳ Aguardando {delay:.2f}s antes da próxima tentativa")
                
                # Aguardar antes da próxima tentativa
                await asyncio.sleep(delay)
        
        # Se chegou aqui, todas as tentativas falharam
        logger.error(f"❌ Todas as {self.config.max_attempts} tentativas falharam")
        raise last_exception
    
    def retry_decorator(self, config: RetryConfig = None):
        """Decorator para retry automático."""
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                retry_instance = AdvancedRetry(config or self.config)
                return await retry_instance.execute_with_retry(func, *args, **kwargs)
            return wrapper
        return decorator


# Configurações pré-definidas
class RetryConfigs:
    """Configurações pré-definidas de retry."""
    
    @staticmethod
    def http_requests() -> RetryConfig:
        """Configuração para requisições HTTP."""
        return RetryConfig(
            max_attempts=5,
            base_delay=1.0,
            max_delay=30.0,
            strategy=RetryStrategy.EXPONENTIAL,
            jitter=True,
            jitter_range=0.1,
            backoff_multiplier=2.0,
            condition=RetryCondition.HTTP_ERRORS,
            http_status_codes=[500, 502, 503, 504, 429],
            timeout_seconds=30.0
        )
    
    @staticmethod
    def rate_limit() -> RetryConfig:
        """Configuração para rate limiting."""
        return RetryConfig(
            max_attempts=7,
            base_delay=2.0,
            max_delay=120.0,
            strategy=RetryStrategy.EXPONENTIAL,
            jitter=True,
            jitter_range=0.2,
            backoff_multiplier=2.5,
            condition=RetryCondition.RATE_LIMIT_ERRORS,
            timeout_seconds=60.0
        )
    
    @staticmethod
    def timeouts() -> RetryConfig:
        """Configuração para timeouts."""
        return RetryConfig(
            max_attempts=3,
            base_delay=0.5,
            max_delay=10.0,
            strategy=RetryStrategy.LINEAR,
            jitter=True,
            jitter_range=0.1,
            backoff_multiplier=1.5,
            condition=RetryCondition.TIMEOUT_ERRORS,
            timeout_seconds=15.0
        )
    
    @staticmethod
    def database_operations() -> RetryConfig:
        """Configuração para operações de banco."""
        return RetryConfig(
            max_attempts=4,
            base_delay=1.0,
            max_delay=20.0,
            strategy=RetryStrategy.EXPONENTIAL,
            jitter=True,
            jitter_range=0.1,
            backoff_multiplier=2.0,
            condition=RetryCondition.SPECIFIC_EXCEPTIONS,
            specific_exceptions=[ConnectionError, TimeoutError],
            timeout_seconds=20.0
        )
    
    @staticmethod
    def file_operations() -> RetryConfig:
        """Configuração para operações de arquivo."""
        return RetryConfig(
            max_attempts=3,
            base_delay=0.5,
            max_delay=5.0,
            strategy=RetryStrategy.FIXED,
            jitter=True,
            jitter_range=0.1,
            backoff_multiplier=1.0,
            condition=RetryCondition.ALL_EXCEPTIONS,
            timeout_seconds=10.0
        )


# Instância global
advanced_retry = AdvancedRetry()


# Funções de conveniência
async def retry_http_request(func: Callable, *args, **kwargs) -> Any:
    """Executar requisição HTTP com retry."""
    config = RetryConfigs.http_requests()
    retry_instance = AdvancedRetry(config)
    return await retry_instance.execute_with_retry(func, *args, **kwargs)


async def retry_rate_limit(func: Callable, *args, **kwargs) -> Any:
    """Executar operação com retry para rate limiting."""
    config = RetryConfigs.rate_limit()
    retry_instance = AdvancedRetry(config)
    return await retry_instance.execute_with_retry(func, *args, **kwargs)


async def retry_timeout(func: Callable, *args, **kwargs) -> Any:
    """Executar operação com retry para timeouts."""
    config = RetryConfigs.timeouts()
    retry_instance = AdvancedRetry(config)
    return await retry_instance.execute_with_retry(func, *args, **kwargs)


async def retry_database(func: Callable, *args, **kwargs) -> Any:
    """Executar operação de banco com retry."""
    config = RetryConfigs.database_operations()
    retry_instance = AdvancedRetry(config)
    return await retry_instance.execute_with_retry(func, *args, **kwargs)


async def retry_file_operation(func: Callable, *args, **kwargs) -> Any:
    """Executar operação de arquivo com retry."""
    config = RetryConfigs.file_operations()
    retry_instance = AdvancedRetry(config)
    return await retry_instance.execute_with_retry(func, *args, **kwargs)


# Decorators de conveniência
def retry_http(config: RetryConfig = None):
    """Decorator para requisições HTTP com retry."""
    return advanced_retry.retry_decorator(config or RetryConfigs.http_requests())


def retry_rate_limit(config: RetryConfig = None):
    """Decorator para rate limiting com retry."""
    return advanced_retry.retry_decorator(config or RetryConfigs.rate_limit())


def retry_timeout(config: RetryConfig = None):
    """Decorator para timeouts com retry."""
    return advanced_retry.retry_decorator(config or RetryConfigs.timeouts())


def retry_database(config: RetryConfig = None):
    """Decorator para operações de banco com retry."""
    return advanced_retry.retry_decorator(config or RetryConfigs.database_operations())


def retry_file_operation(config: RetryConfig = None):
    """Decorator para operações de arquivo com retry."""
    return advanced_retry.retry_decorator(config or RetryConfigs.file_operations())
