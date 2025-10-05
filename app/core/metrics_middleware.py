"""Middleware de métricas para observabilidade."""

import time
import uuid
from typing import Dict, Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from loguru import logger

from app.core.config import settings


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware para coletar métricas de performance e uso."""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.request_counts: Dict[str, int] = {}
        self.response_times: Dict[str, list] = {}
        self.error_counts: Dict[str, int] = {}
        
    async def dispatch(self, request: Request, call_next):
        """Coletar métricas da requisição."""
        
        # Gerar trace ID se habilitado
        if settings.enable_tracing:
            trace_id = getattr(request.state, 'trace_id', str(uuid.uuid4()))
            request.state.trace_id = trace_id
        
        # Iniciar timer
        start_time = time.time()
        
        # Contar requisição
        endpoint = f"{request.method} {request.url.path}"
        self.request_counts[endpoint] = self.request_counts.get(endpoint, 0) + 1
        
        try:
            # Processar requisição
            response = await call_next(request)
            
            # Calcular tempo de resposta
            process_time = time.time() - start_time
            
            # Armazenar tempo de resposta
            if endpoint not in self.response_times:
                self.response_times[endpoint] = []
            self.response_times[endpoint].append(process_time)
            
            # Manter apenas os últimos 1000 tempos para evitar vazamento de memória
            if len(self.response_times[endpoint]) > 1000:
                self.response_times[endpoint] = self.response_times[endpoint][-1000:]
            
            # Adicionar headers de métricas
            response.headers["X-Response-Time"] = f"{process_time:.3f}"
            if settings.enable_tracing and hasattr(request.state, 'trace_id'):
                response.headers["X-Trace-ID"] = request.state.trace_id
            
            # Log de métricas com trace ID se disponível
            trace_info = f" - Trace: {request.state.trace_id}" if settings.enable_tracing and hasattr(request.state, 'trace_id') else ""
            logger.debug(
                f"Metrics: {endpoint} - "
                f"Status: {response.status_code} - "
                f"Time: {process_time:.3f}s - "
                f"Count: {self.request_counts[endpoint]}{trace_info}"
            )
            
            return response
            
        except Exception as e:
            # Calcular tempo de erro
            process_time = time.time() - start_time
            
            # Contar erro
            error_key = f"{endpoint} ERROR"
            self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
            
            # Log de erro com métricas
            logger.error(
                f"Metrics ERROR: {endpoint} - "
                f"Error: {str(e)} - "
                f"Time: {process_time:.3f}s - "
                f"Error Count: {self.error_counts[error_key]}"
            )
            
            raise
    
    def get_metrics(self) -> Dict[str, any]:
        """Obter métricas coletadas."""
        metrics = {
            "request_counts": self.request_counts.copy(),
            "error_counts": self.error_counts.copy(),
            "response_times": {}
        }
        
        # Calcular estatísticas de tempo de resposta
        for endpoint, times in self.response_times.items():
            if times:
                metrics["response_times"][endpoint] = {
                    "count": len(times),
                    "avg_ms": round(sum(times) / len(times) * 1000, 2),
                    "min_ms": round(min(times) * 1000, 2),
                    "max_ms": round(max(times) * 1000, 2),
                    "p95_ms": round(self._calculate_percentile(times, 95) * 1000, 2),
                    "p99_ms": round(self._calculate_percentile(times, 99) * 1000, 2),
                }
        
        return metrics
    
    def _calculate_percentile(self, data: list, percentile: int) -> float:
        """Calcular percentil de uma lista de dados."""
        if not data:
            return 0.0
        
        sorted_data = sorted(data)
        k = (len(sorted_data) - 1) * percentile / 100
        f = int(k)
        c = k - f
        
        if f + 1 < len(sorted_data):
            return sorted_data[f] + (sorted_data[f + 1] - sorted_data[f]) * c
        return sorted_data[f]


def create_metrics_middleware(app):
    """Criar middleware de métricas se habilitado."""
    if settings.enable_metrics:
        logger.info(f"Métricas habilitadas em {settings.metrics_path}")
        return MetricsMiddleware(app)
    else:
        logger.info("Métricas desabilitadas")
        return app


# Instância global para acesso às métricas
metrics_middleware_instance: Optional[MetricsMiddleware] = None


def get_metrics_instance() -> Optional[MetricsMiddleware]:
    """Obter instância do middleware de métricas."""
    return metrics_middleware_instance


def set_metrics_instance(instance: MetricsMiddleware):
    """Definir instância do middleware de métricas."""
    global metrics_middleware_instance
    metrics_middleware_instance = instance
