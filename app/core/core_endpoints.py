"""Endpoints principais da aplicação (root, health, metrics)."""

import sys
import time
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from loguru import logger

from app.core.config import settings
from app.core.app_state import get_uptime
from app.core.metrics_middleware import get_metrics_instance
from app.core.router_config import get_router_info


def register_core_endpoints(app: FastAPI):
    """Registrar endpoints principais da aplicação."""
    
    @app.get("/")
    async def root(request: Request):
        """Endpoint raiz da API."""
        try:
            start_time = getattr(app.state, 'start_time', time.time())
            uptime = time.time() - start_time if start_time else 0
            
            response_data = {
                "message": settings.api_title,
                "version": settings.api_version,
                "environment": settings.environment,
                "timestamp": datetime.utcnow().isoformat(),
                "request_id": getattr(request.state, 'request_id', None),
                "docs_url": "/docs" if settings.debug else None,
                "monitoring_url": "/monitoring/dashboard" if not settings.debug else None,
                "status": "healthy",
                "uptime_seconds": uptime,
            }
            
            if settings.debug or settings.health_check_include_version:
                response_data["python_version"] = sys.version
            
            return JSONResponse(content=response_data, status_code=200)
            
        except Exception as e:
            logger.error(f"Erro no endpoint root: {e}")
            return JSONResponse(
                content={"error": "Erro interno do servidor", "request_id": getattr(request.state, 'request_id', None)},
                status_code=500
            )
    
    @app.get("/health")
    async def health_check(request: Request):
        """Endpoint de verificação de saúde da API."""
        try:
            health_data = {
                "status": "healthy",
                "environment": settings.environment,
                "timestamp": datetime.utcnow().isoformat(),
                "request_id": getattr(request.state, 'request_id', None),
            }
            
            if settings.health_check_include_version:
                health_data["version"] = settings.api_version
            
            if settings.health_check_include_timestamp:
                health_data["uptime_seconds"] = get_uptime()
            
            return JSONResponse(content=health_data, status_code=200)
            
        except Exception as e:
            logger.error(f"Erro no endpoint health: {e}")
            return JSONResponse(
                content={"error": "Erro interno do servidor", "request_id": getattr(request.state, 'request_id', None)},
                status_code=500
            )
    
    @app.get("/metrics")
    async def get_metrics(request: Request):
        """Endpoint para métricas de performance (Prometheus-compatible)."""
        
        if settings.metrics_protected and not settings.debug:
            return JSONResponse(
                status_code=403,
                content={
                    "error": "Endpoint de métricas protegido",
                    "request_id": getattr(request.state, 'request_id', None)
                }
            )
        
        metrics_instance = get_metrics_instance()
        if not metrics_instance:
            return JSONResponse(
                status_code=503,
                content={
                    "error": "Métricas não habilitadas",
                    "request_id": getattr(request.state, 'request_id', None)
                }
            )
        
        try:
            metrics_data = metrics_instance.get_metrics()
            
            prometheus_metrics = []
            
            # Request counts
            for endpoint, count in metrics_data["request_counts"].items():
                prometheus_metrics.append(f'http_requests_total{{endpoint="{endpoint}"}} {count}')
            
            # Error counts
            for endpoint, count in metrics_data["error_counts"].items():
                prometheus_metrics.append(f'http_errors_total{{endpoint="{endpoint}"}} {count}')
            
            # Response times (avg, p95, p99)
            for endpoint, stats in metrics_data["response_times"].items():
                prometheus_metrics.append(f'http_request_duration_seconds_avg{{endpoint="{endpoint}"}} {stats["avg_ms"]/1000:.3f}')
                prometheus_metrics.append(f'http_request_duration_seconds_p95{{endpoint="{endpoint}"}} {stats["p95_ms"]/1000:.3f}')
                prometheus_metrics.append(f'http_request_duration_seconds_p99{{endpoint="{endpoint}"}} {stats["p99_ms"]/1000:.3f}')
            
            # Histogramas de latência (buckets)
            for endpoint, stats in metrics_data["response_times"].items():
                # Buckets para histograma Prometheus
                buckets = [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
                for bucket in buckets:
                    # Simular contagem de requests por bucket (simplificado)
                    count_in_bucket = max(0, stats["count"] - int(bucket * 1000 / stats["avg_ms"]) if stats["avg_ms"] > 0 else 0)
                    prometheus_metrics.append(f'http_request_duration_seconds_bucket{{endpoint="{endpoint}",le="{bucket}"}} {count_in_bucket}')
                
                # Bucket +Inf
                prometheus_metrics.append(f'http_request_duration_seconds_bucket{{endpoint="{endpoint}",le="+Inf"}} {stats["count"]}')
                
                # Soma total
                prometheus_metrics.append(f'http_request_duration_seconds_sum{{endpoint="{endpoint}"}} {stats["avg_ms"] * stats["count"] / 1000:.3f}')
                prometheus_metrics.append(f'http_request_duration_seconds_count{{endpoint="{endpoint}"}} {stats["count"]}')
            
            return PlainTextResponse(
                content="\n".join(prometheus_metrics),
                media_type="text/plain; version=0.0.4; charset=utf-8",
                headers={
                    "Cache-Control": f"public, max-age={settings.metrics_cache_ttl}",
                    "X-Request-ID": getattr(request.state, 'request_id', ''),
                    "X-Timestamp": datetime.utcnow().isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"Erro no endpoint metrics: {e}")
            return JSONResponse(
                content={
                    "error": "Erro interno do servidor", 
                    "request_id": getattr(request.state, 'request_id', None)
                },
                status_code=500
            )
    
    @app.get("/api-info")
    async def api_info(request: Request):
        """Informações sobre a API e routers registrados."""
        try:
            router_info = get_router_info()
            
            response_data = {
                "api": {
                    "title": settings.api_title,
                    "version": settings.api_version,
                    "description": settings.api_description,
                    "prefix": settings.api_prefix,
                },
                "routers": router_info,
                "environment": settings.environment,
                "debug": settings.debug,
                "timestamp": datetime.utcnow().isoformat(),
                "request_id": getattr(request.state, 'request_id', None),
            }
            
            return JSONResponse(content=response_data, status_code=200)
            
        except Exception as e:
            logger.error(f"Erro no endpoint api-info: {e}")
            return JSONResponse(
                content={
                    "error": "Erro interno do servidor",
                    "request_id": getattr(request.state, 'request_id', None)
                },
                status_code=500
            )
