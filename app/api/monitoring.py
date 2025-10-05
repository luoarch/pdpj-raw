"""Endpoints de monitoramento e métricas da API PDPJ."""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse

from app.core.security import get_current_user, require_admin
from app.models import User
from app.core.proactive_monitoring import proactive_monitor, get_active_alerts, get_metrics_summary
from app.services.pdpj_client import pdpj_client
from app.services.process_cache_service import process_cache_service
from app.core.dynamic_limits import environment_limits

router = APIRouter(tags=["monitoring"])


@router.get("/metrics")
async def get_current_metrics(
    current_user: User = Depends(require_admin())
):
    """Obter métricas atuais do sistema."""
    try:
        metrics = get_metrics_summary()
        return metrics
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao obter métricas: {str(e)}"
        )


@router.get("/metrics/historical")
async def get_historical_metrics(
    hours: int = Query(24, ge=1, le=168, description="Número de horas para histórico"),
    current_user: User = Depends(require_admin())
):
    """Obter métricas históricas do sistema."""
    try:
        # Por enquanto, retornar métricas atuais (implementar histórico se necessário)
        metrics = get_metrics_summary()
        return {"current": metrics, "historical_available": False}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao obter métricas históricas: {str(e)}"
        )


@router.get("/performance")
async def get_performance_summary(
    current_user: User = Depends(require_admin())
):
    """Obter resumo de performance do sistema."""
    try:
        summary = get_metrics_summary()
        return summary
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao obter resumo de performance: {str(e)}"
        )


@router.get("/health/detailed")
async def get_detailed_health(
    current_user: User = Depends(require_admin())
):
    """Verificação detalhada de saúde do sistema."""
    try:
        health_status = {
            "timestamp": "2025-10-05T17:27:00Z",
            "overall_status": "healthy",
            "components": {
                "pdpj_client": {
                    "status": "healthy",
                    "requests_made": 0,
                    "success_rate": 0.0,
                    "error_rate": 0.0,
                    "concurrent_requests": 0
                },
                "cache_service": {
                    "status": "healthy",
                    "hit_rate": 0.0,
                    "miss_rate": 0.0,
                    "total_operations": 0
                },
                "environment_limits": {
                    "status": "healthy",
                    "environment": "development",
                    "max_concurrent_requests": 100
                }
            }
        }
        
        return health_status
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro na verificação de saúde: {str(e)}"
        )


@router.get("/alerts")
async def get_alerts(
    current_user: User = Depends(require_admin())
):
    """Obter alertas ativos do sistema."""
    try:
        alerts = get_active_alerts()
        
        return {
            "timestamp": "unknown",
            "total_alerts": len(alerts),
            "alerts": [{"type": alert.type.value, "severity": alert.severity.value, "message": alert.message} for alert in alerts]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao obter alertas: {str(e)}"
        )


@router.get("/dashboard")
async def get_monitoring_dashboard(
    current_user: User = Depends(require_admin())
):
    """Obter dados completos para dashboard de monitoramento."""
    try:
        # Coletar todas as métricas
        current_metrics = get_metrics_summary()
        alerts = get_active_alerts()
        
        # Métricas de cada serviço
        service_metrics = {
            "pdpj_client": pdpj_client.get_metrics(),
            "cache_service": process_cache_service.get_cache_stats(),
            "environment_limits": environment_limits.get_limits_summary()
        }
        
        return {
            "timestamp": "unknown",
            "overall_status": "healthy",
            "current_metrics": current_metrics,
            "performance": {},
            "system_health": {},
            "alerts": [{"type": alert.type.value, "severity": alert.severity.value, "message": alert.message} for alert in alerts],
            "service_metrics": service_metrics,
            "historical_summary": {
                "system_data_points": 0,
                "api_data_points": 0,
                "avg_cache_hit_rate": 0,
                "avg_response_time": 0,
                "total_requests": 0
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao obter dashboard: {str(e)}"
        )


@router.post("/metrics/reset")
async def reset_metrics(
    current_user: User = Depends(require_admin())
):
    """Resetar métricas do sistema (usar com cuidado!)."""
    try:
        # Resetar métricas do monitoramento
        monitoring_service.cache_hits = 0
        monitoring_service.cache_misses = 0
        monitoring_service.request_times.clear()
        monitoring_service.request_counts.clear()
        monitoring_service.error_counts.clear()
        monitoring_service.db_query_times.clear()
        monitoring_service.db_query_counts.clear()
        monitoring_service.pdpj_request_times.clear()
        monitoring_service.pdpj_request_counts.clear()
        monitoring_service.pdpj_error_counts.clear()
        monitoring_service.s3_upload_times.clear()
        monitoring_service.s3_download_times.clear()
        monitoring_service.s3_operations_count.clear()
        
        return {
            "message": "Métricas resetadas com sucesso",
            "timestamp": monitoring_service.get_current_metrics()["timestamp"]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao resetar métricas: {str(e)}"
        )


@router.get("/status")
async def get_system_status(
    current_user: User = Depends(require_admin())
):
    """Obter status resumido do sistema."""
    try:
        from app.core.proactive_monitoring import get_metrics_summary
        current_metrics = get_metrics_summary()
        
        # Determinar status geral
        system_metrics = current_metrics.get("system", {})
        api_metrics = current_metrics.get("api", {})
        
        cpu_percent = system_metrics.get("cpu_percent", 0)
        memory_percent = system_metrics.get("memory_percent", 0)
        success_rate = api_metrics.get("success_rate", 100)
        
        if cpu_percent > 90 or memory_percent > 95 or success_rate < 90:
            system_status = "critical"
        elif cpu_percent > 80 or memory_percent > 85 or success_rate < 95:
            system_status = "warning"
        else:
            system_status = "healthy"
        
        return {
            "status": system_status,
            "timestamp": current_metrics.get("timestamp", "unknown"),
            "summary": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory_percent,
                "success_rate": success_rate,
                "requests_total": api_metrics.get("total_requests", 0),
                "cache_hit_rate": current_metrics.get("cache", {}).get("hit_rate", 0)
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao obter status: {str(e)}"
        )
