"""
Sistema de monitoramento pró-ativo para alertas e métricas.
"""

import os
import time
import asyncio
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from loguru import logger

from prometheus_client import Counter, Histogram, Gauge, generate_latest
import sentry_sdk


class AlertSeverity(str, Enum):
    """Severidade dos alertas."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertType(str, Enum):
    """Tipos de alertas."""
    PERFORMANCE = "performance"
    ERROR_RATE = "error_rate"
    MEMORY_USAGE = "memory_usage"
    RATE_LIMIT = "rate_limit"
    TIMEOUT = "timeout"
    CACHE_MISS = "cache_miss"
    BATCH_FAILURE = "batch_failure"


@dataclass
class Alert:
    """Estrutura de um alerta."""
    type: AlertType
    severity: AlertSeverity
    message: str
    timestamp: datetime
    metadata: Dict[str, Any]
    resolved: bool = False
    resolved_at: Optional[datetime] = None


class ProactiveMonitor:
    """Monitor pró-ativo com alertas automáticos."""
    
    def __init__(self):
        self._alerts: List[Alert] = []
        self._thresholds: Dict[str, Dict[str, float]] = {
            "error_rate": {"low": 0.05, "medium": 0.10, "high": 0.20, "critical": 0.30},
            "response_time": {"low": 2.0, "medium": 5.0, "high": 10.0, "critical": 20.0},
            "memory_usage": {"low": 0.70, "medium": 0.80, "high": 0.90, "critical": 0.95},
            "cache_miss_rate": {"low": 0.20, "medium": 0.30, "high": 0.40, "critical": 0.50},
            "rate_limit_hits": {"low": 10, "medium": 25, "high": 50, "critical": 100},
            "timeout_rate": {"low": 0.01, "medium": 0.05, "high": 0.10, "critical": 0.20}
        }
        
        self._metrics_history: Dict[str, List[float]] = {}
        self._alert_callbacks: List[Callable[[Alert], None]] = []
        
        # Métricas Prometheus
        self._setup_prometheus_metrics()
        
        # Configurar Sentry
        self._setup_sentry()
    
    def _setup_prometheus_metrics(self):
        """Configurar métricas Prometheus."""
        self.request_count = Counter(
            'pdpj_requests_total',
            'Total number of requests',
            ['method', 'endpoint', 'status_code']
        )
        
        self.request_duration = Histogram(
            'pdpj_request_duration_seconds',
            'Request duration in seconds',
            ['method', 'endpoint']
        )
        
        self.error_count = Counter(
            'pdpj_errors_total',
            'Total number of errors',
            ['error_type', 'endpoint']
        )
        
        self.active_alerts = Gauge(
            'pdpj_active_alerts',
            'Number of active alerts',
            ['severity', 'type']
        )
        
        self.cache_hit_rate = Gauge(
            'pdpj_cache_hit_rate',
            'Cache hit rate percentage'
        )
        
        self.memory_usage = Gauge(
            'pdpj_memory_usage_bytes',
            'Memory usage in bytes'
        )
        
        self.rate_limit_hits = Counter(
            'pdpj_rate_limit_hits_total',
            'Total rate limit hits',
            ['endpoint', 'user_id']
        )
        
        logger.info("📊 Métricas Prometheus configuradas")
    
    def _setup_sentry(self):
        """Configurar Sentry para alertas críticos."""
        sentry_dsn = os.getenv("SENTRY_DSN")
        if sentry_dsn:
            sentry_sdk.init(
                dsn=sentry_dsn,
                traces_sample_rate=1.0,
                profiles_sample_rate=1.0,
            )
            logger.info("🚨 Sentry configurado para alertas críticos")
        else:
            logger.warning("⚠️ SENTRY_DSN não configurado")
    
    def add_alert_callback(self, callback: Callable[[Alert], None]):
        """Adicionar callback para alertas."""
        self._alert_callbacks.append(callback)
    
    def record_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """Registrar requisição."""
        self.request_count.labels(method=method, endpoint=endpoint, status_code=status_code).inc()
        self.request_duration.labels(method=method, endpoint=endpoint).observe(duration)
        
        # Verificar thresholds
        self._check_response_time_threshold(endpoint, duration)
    
    def record_error(self, error_type: str, endpoint: str, message: str):
        """Registrar erro."""
        self.error_count.labels(error_type=error_type, endpoint=endpoint).inc()
        
        # Verificar thresholds
        self._check_error_rate_threshold(endpoint)
        
        # Enviar para Sentry se crítico
        if error_type in ["critical", "timeout", "memory_error"]:
            sentry_sdk.capture_exception(Exception(f"{error_type}: {message}"))
    
    def record_rate_limit_hit(self, endpoint: str, user_id: str):
        """Registrar hit de rate limit."""
        self.rate_limit_hits.labels(endpoint=endpoint, user_id=user_id).inc()
        
        # Verificar thresholds
        self._check_rate_limit_threshold(endpoint)
    
    def record_cache_metrics(self, hits: int, misses: int):
        """Registrar métricas de cache."""
        total = hits + misses
        if total > 0:
            hit_rate = hits / total
            self.cache_hit_rate.set(hit_rate * 100)
            
            # Verificar thresholds
            self._check_cache_miss_threshold(hit_rate)
    
    def record_memory_usage(self, usage_bytes: int, total_bytes: int):
        """Registrar uso de memória."""
        usage_percentage = usage_bytes / total_bytes
        self.memory_usage.set(usage_bytes)
        
        # Verificar thresholds
        self._check_memory_threshold(usage_percentage)
    
    def _check_response_time_threshold(self, endpoint: str, duration: float):
        """Verificar threshold de tempo de resposta."""
        thresholds = self._thresholds["response_time"]
        
        severity = None
        if duration >= thresholds["critical"]:
            severity = AlertSeverity.CRITICAL
        elif duration >= thresholds["high"]:
            severity = AlertSeverity.HIGH
        elif duration >= thresholds["medium"]:
            severity = AlertSeverity.MEDIUM
        elif duration >= thresholds["low"]:
            severity = AlertSeverity.LOW
        
        if severity:
            self._create_alert(
                AlertType.PERFORMANCE,
                severity,
                f"Tempo de resposta alto: {duration:.2f}s para {endpoint}",
                {"endpoint": endpoint, "duration": duration}
            )
    
    def _check_error_rate_threshold(self, endpoint: str):
        """Verificar threshold de taxa de erro."""
        # Calcular taxa de erro dos últimos 5 minutos
        error_rate = self._calculate_error_rate(endpoint, minutes=5)
        
        thresholds = self._thresholds["error_rate"]
        severity = None
        
        if error_rate >= thresholds["critical"]:
            severity = AlertSeverity.CRITICAL
        elif error_rate >= thresholds["high"]:
            severity = AlertSeverity.HIGH
        elif error_rate >= thresholds["medium"]:
            severity = AlertSeverity.MEDIUM
        elif error_rate >= thresholds["low"]:
            severity = AlertSeverity.LOW
        
        if severity:
            self._create_alert(
                AlertType.ERROR_RATE,
                severity,
                f"Taxa de erro alta: {error_rate:.2%} para {endpoint}",
                {"endpoint": endpoint, "error_rate": error_rate}
            )
    
    def _check_memory_threshold(self, usage_percentage: float):
        """Verificar threshold de uso de memória."""
        thresholds = self._thresholds["memory_usage"]
        severity = None
        
        if usage_percentage >= thresholds["critical"]:
            severity = AlertSeverity.CRITICAL
        elif usage_percentage >= thresholds["high"]:
            severity = AlertSeverity.HIGH
        elif usage_percentage >= thresholds["medium"]:
            severity = AlertSeverity.MEDIUM
        elif usage_percentage >= thresholds["low"]:
            severity = AlertSeverity.LOW
        
        if severity:
            self._create_alert(
                AlertType.MEMORY_USAGE,
                severity,
                f"Uso de memória alto: {usage_percentage:.1%}",
                {"usage_percentage": usage_percentage}
            )
    
    def _check_cache_miss_threshold(self, hit_rate: float):
        """Verificar threshold de cache miss."""
        miss_rate = 1 - hit_rate
        thresholds = self._thresholds["cache_miss_rate"]
        severity = None
        
        if miss_rate >= thresholds["critical"]:
            severity = AlertSeverity.CRITICAL
        elif miss_rate >= thresholds["high"]:
            severity = AlertSeverity.HIGH
        elif miss_rate >= thresholds["medium"]:
            severity = AlertSeverity.MEDIUM
        elif miss_rate >= thresholds["low"]:
            severity = AlertSeverity.LOW
        
        if severity:
            self._create_alert(
                AlertType.CACHE_MISS,
                severity,
                f"Taxa de cache miss alta: {miss_rate:.1%}",
                {"miss_rate": miss_rate, "hit_rate": hit_rate}
            )
    
    def _check_rate_limit_threshold(self, endpoint: str):
        """Verificar threshold de rate limit."""
        # Contar hits dos últimos 5 minutos
        hits = self._count_rate_limit_hits(endpoint, minutes=5)
        
        thresholds = self._thresholds["rate_limit_hits"]
        severity = None
        
        if hits >= thresholds["critical"]:
            severity = AlertSeverity.CRITICAL
        elif hits >= thresholds["high"]:
            severity = AlertSeverity.HIGH
        elif hits >= thresholds["medium"]:
            severity = AlertSeverity.MEDIUM
        elif hits >= thresholds["low"]:
            severity = AlertSeverity.LOW
        
        if severity:
            self._create_alert(
                AlertType.RATE_LIMIT,
                severity,
                f"Muitos hits de rate limit: {hits} para {endpoint}",
                {"endpoint": endpoint, "hits": hits}
            )
    
    def _create_alert(self, alert_type: AlertType, severity: AlertSeverity, message: str, metadata: Dict[str, Any]):
        """Criar novo alerta."""
        alert = Alert(
            type=alert_type,
            severity=severity,
            message=message,
            timestamp=datetime.utcnow(),
            metadata=metadata
        )
        
        self._alerts.append(alert)
        self.active_alerts.labels(severity=severity.value, type=alert_type.value).inc()
        
        logger.warning(f"🚨 ALERTA {severity.value.upper()}: {message}")
        
        # Notificar callbacks
        for callback in self._alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"❌ Erro no callback de alerta: {e}")
    
    def _calculate_error_rate(self, endpoint: str, minutes: int = 5) -> float:
        """Calcular taxa de erro dos últimos N minutos."""
        # Implementação simplificada - em produção, usar métricas reais
        return 0.0
    
    def _count_rate_limit_hits(self, endpoint: str, minutes: int = 5) -> int:
        """Contar hits de rate limit dos últimos N minutos."""
        # Implementação simplificada - em produção, usar métricas reais
        return 0
    
    def get_active_alerts(self) -> List[Alert]:
        """Obter alertas ativos."""
        return [alert for alert in self._alerts if not alert.resolved]
    
    def resolve_alert(self, alert_id: int):
        """Resolver alerta."""
        if 0 <= alert_id < len(self._alerts):
            alert = self._alerts[alert_id]
            alert.resolved = True
            alert.resolved_at = datetime.utcnow()
            
            self.active_alerts.labels(severity=alert.severity.value, type=alert.type.value).dec()
            logger.info(f"✅ Alerta resolvido: {alert.message}")
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Obter resumo das métricas."""
        active_alerts = self.get_active_alerts()
        
        return {
            "active_alerts": len(active_alerts),
            "alerts_by_severity": {
                severity.value: len([a for a in active_alerts if a.severity == severity])
                for severity in AlertSeverity
            },
            "alerts_by_type": {
                alert_type.value: len([a for a in active_alerts if a.alert_type == alert_type])
                for alert_type in AlertType
            },
            "thresholds": self._thresholds,
            "prometheus_metrics": generate_latest().decode('utf-8')
        }
    
    def update_thresholds(self, new_thresholds: Dict[str, Dict[str, float]]):
        """Atualizar thresholds."""
        self._thresholds.update(new_thresholds)
        logger.info("🔧 Thresholds atualizados")
    
    def cleanup_old_alerts(self, days: int = 7):
        """Limpar alertas antigos."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        old_count = len(self._alerts)
        
        self._alerts = [
            alert for alert in self._alerts
            if alert.timestamp > cutoff_date
        ]
        
        removed_count = old_count - len(self._alerts)
        if removed_count > 0:
            logger.info(f"🧹 Removidos {removed_count} alertas antigos")


# Instância global
proactive_monitor = ProactiveMonitor()


# Funções de conveniência
def record_request_metrics(method: str, endpoint: str, status_code: int, duration: float):
    """Registrar métricas de requisição."""
    proactive_monitor.record_request(method, endpoint, status_code, duration)


def record_error_metrics(error_type: str, endpoint: str, message: str):
    """Registrar métricas de erro."""
    proactive_monitor.record_error(error_type, endpoint, message)


def record_rate_limit_metrics(endpoint: str, user_id: str):
    """Registrar métricas de rate limit."""
    proactive_monitor.record_rate_limit_hit(endpoint, user_id)


def record_cache_metrics(hits: int, misses: int):
    """Registrar métricas de cache."""
    proactive_monitor.record_cache_metrics(hits, misses)


def record_memory_metrics(usage_bytes: int, total_bytes: int):
    """Registrar métricas de memória."""
    proactive_monitor.record_memory_usage(usage_bytes, total_bytes)


def get_active_alerts() -> List[Alert]:
    """Obter alertas ativos."""
    return proactive_monitor.get_active_alerts()


def get_metrics_summary() -> Dict[str, Any]:
    """Obter resumo das métricas."""
    return proactive_monitor.get_metrics_summary()
