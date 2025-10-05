"""
Endpoints de monitoramento e métricas para o PDPJ Client.
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import PlainTextResponse
from typing import Dict, Any
from loguru import logger

from app.services.pdpj_client import pdpj_client
from app.utils.monitoring_integration import get_health_status, get_prometheus_metrics

router = APIRouter(prefix="/monitoring", tags=["monitoring"])

@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Endpoint de health check para monitoramento."""
    try:
        # Obter status de saúde do sistema de monitoramento
        health_status = get_health_status()
        
        # Adicionar métricas do cliente PDPJ
        client_metrics = pdpj_client.get_metrics()
        
        return {
            **health_status,
            "pdpj_client": {
                "status": client_metrics.get("health_status", "unknown"),
                "requests_made": client_metrics.get("requests_made", 0),
                "success_rate": client_metrics.get("success_rate", 0.0),
                "error_rate": client_metrics.get("error_rate", 0.0),
                "concurrent_requests": client_metrics.get("concurrent_requests", 0),
                "alerts": client_metrics.get("alerts", [])
            }
        }
    except Exception as e:
        logger.error(f"Erro no health check: {e}")
        raise HTTPException(status_code=500, detail=f"Erro no health check: {e}")

@router.get("/metrics")
async def prometheus_metrics() -> PlainTextResponse:
    """Endpoint de métricas Prometheus."""
    try:
        metrics_text = get_prometheus_metrics()
        return PlainTextResponse(content=metrics_text, media_type="text/plain")
    except Exception as e:
        logger.error(f"Erro ao obter métricas Prometheus: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao obter métricas: {e}")

@router.get("/pdpj/metrics")
async def pdpj_client_metrics() -> Dict[str, Any]:
    """Obter métricas detalhadas do cliente PDPJ."""
    try:
        metrics = pdpj_client.get_metrics()
        return {
            "status": "success",
            "timestamp": metrics.get("timestamp", "unknown"),
            "metrics": metrics
        }
    except Exception as e:
        logger.error(f"Erro ao obter métricas do cliente PDPJ: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao obter métricas: {e}")

@router.get("/pdpj/status")
async def pdpj_client_status() -> Dict[str, Any]:
    """Obter status simplificado do cliente PDPJ."""
    try:
        metrics = pdpj_client.get_metrics()
        
        return {
            "status": "success",
            "health": metrics.get("health_status", "unknown"),
            "summary": {
                "requests_made": metrics.get("requests_made", 0),
                "downloads_successful": metrics.get("downloads_successful", 0),
                "downloads_failed": metrics.get("downloads_failed", 0),
                "success_rate": f"{metrics.get('success_rate', 0.0)*100:.1f}%",
                "error_rate": f"{metrics.get('error_rate', 0.0)*100:.1f}%",
                "avg_request_time": f"{metrics.get('avg_request_time', 0.0):.3f}s",
                "avg_download_time": f"{metrics.get('avg_download_time', 0.0):.3f}s"
            },
            "alerts": metrics.get("alerts", [])
        }
    except Exception as e:
        logger.error(f"Erro ao obter status do cliente PDPJ: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao obter status: {e}")

@router.get("/pdpj/errors")
async def pdpj_error_summary() -> Dict[str, Any]:
    """Obter resumo de erros do cliente PDPJ."""
    try:
        metrics = pdpj_client.get_metrics()
        http_errors = metrics.get("http_errors", {})
        
        total_errors = sum(http_errors.values())
        
        return {
            "status": "success",
            "total_errors": total_errors,
            "error_breakdown": http_errors,
            "error_rate": f"{metrics.get('error_rate', 0.0)*100:.1f}%",
            "last_error": metrics.get("last_error"),
            "last_error_time": metrics.get("last_error_time")
        }
    except Exception as e:
        logger.error(f"Erro ao obter resumo de erros: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao obter resumo de erros: {e}")

@router.get("/pdpj/performance")
async def pdpj_performance_summary() -> Dict[str, Any]:
    """Obter resumo de performance do cliente PDPJ."""
    try:
        metrics = pdpj_client.get_metrics()
        
        return {
            "status": "success",
            "performance": {
                "avg_request_time": f"{metrics.get('avg_request_time', 0.0):.3f}s",
                "avg_download_time": f"{metrics.get('avg_download_time', 0.0):.3f}s",
                "total_request_time": f"{metrics.get('total_request_time', 0.0):.3f}s",
                "total_download_time": f"{metrics.get('total_download_time', 0.0):.3f}s",
                "concurrent_utilization": f"{metrics.get('concurrent_utilization', 0.0)*100:.1f}%",
                "session_cache_hit_rate": f"{metrics.get('session_cache_hit_rate', 0.0)*100:.1f}%"
            },
            "throughput": {
                "requests_made": metrics.get("requests_made", 0),
                "downloads_successful": metrics.get("downloads_successful", 0),
                "success_rate": f"{metrics.get('success_rate', 0.0)*100:.1f}%"
            }
        }
    except Exception as e:
        logger.error(f"Erro ao obter resumo de performance: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao obter resumo de performance: {e}")
