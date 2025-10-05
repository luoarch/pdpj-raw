"""
Integração com sistemas de monitoramento externo (Prometheus, Sentry, Datadog).
"""

import time
from typing import Dict, Any, Optional, List
from datetime import datetime
from loguru import logger

try:
    from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, generate_latest
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    logger.warning("⚠️ Prometheus client não disponível. Instale com: pip install prometheus-client")

try:
    import sentry_sdk
    SENTRY_AVAILABLE = True
except ImportError:
    SENTRY_AVAILABLE = False
    logger.warning("⚠️ Sentry SDK não disponível. Instale com: pip install sentry-sdk")

class MonitoringIntegration:
    """Integração com sistemas de monitoramento externo."""
    
    def __init__(self, enable_prometheus: bool = True, enable_sentry: bool = True):
        self.enable_prometheus = enable_prometheus and PROMETHEUS_AVAILABLE
        self.enable_sentry = enable_sentry and SENTRY_AVAILABLE
        
        # Métricas Prometheus
        if self.enable_prometheus:
            self._setup_prometheus_metrics()
        
        # Configurar Sentry
        if self.enable_sentry:
            self._setup_sentry()
    
    def _setup_prometheus_metrics(self):
        """Configurar métricas Prometheus."""
        self.registry = CollectorRegistry()
        
        # Contadores
        self.pdpj_requests_total = Counter(
            'pdpj_requests_total',
            'Total de requisições PDPJ',
            ['method', 'endpoint', 'status'],
            registry=self.registry
        )
        
        self.pdpj_downloads_total = Counter(
            'pdpj_downloads_total',
            'Total de downloads PDPJ',
            ['status', 'file_type'],
            registry=self.registry
        )
        
        self.pdpj_errors_total = Counter(
            'pdpj_errors_total',
            'Total de erros PDPJ',
            ['error_type', 'endpoint'],
            registry=self.registry
        )
        
        # Histogramas
        self.pdpj_request_duration = Histogram(
            'pdpj_request_duration_seconds',
            'Duração das requisições PDPJ',
            ['method', 'endpoint'],
            registry=self.registry
        )
        
        self.pdpj_download_duration = Histogram(
            'pdpj_download_duration_seconds',
            'Duração dos downloads PDPJ',
            ['file_type'],
            registry=self.registry
        )
        
        # Gauges
        self.pdpj_concurrent_requests = Gauge(
            'pdpj_concurrent_requests',
            'Requisições simultâneas ativas',
            registry=self.registry
        )
        
        self.pdpj_concurrent_downloads = Gauge(
            'pdpj_concurrent_downloads',
            'Downloads simultâneos ativos',
            registry=self.registry
        )
        
        self.pdpj_cache_hit_rate = Gauge(
            'pdpj_cache_hit_rate',
            'Taxa de hit do cache de sessão',
            registry=self.registry
        )
        
        self.pdpj_success_rate = Gauge(
            'pdpj_success_rate',
            'Taxa de sucesso das operações',
            registry=self.registry
        )
        
        logger.info("📊 Métricas Prometheus configuradas")
    
    def _setup_sentry(self):
        """Configurar Sentry para rastreamento de erros."""
        import os
        from app.core.config import settings
        
        # Usar DSN do settings ou variável de ambiente
        sentry_dsn = settings.sentry_dsn.get_secret_value() if settings.sentry_dsn else os.getenv("SENTRY_DSN")
        
        if sentry_dsn:
            # Configuração básica do Sentry
            sentry_sdk.init(
                dsn=sentry_dsn,
                traces_sample_rate=0.1,  # 10% das transações
                profiles_sample_rate=0.1,  # 10% dos perfis
                environment=settings.environment,  # Usar ambiente do settings
                send_default_pii=True,  # Incluir dados pessoais se necessário
            )
        else:
            logger.warning("⚠️ SENTRY_DSN não configurado")
            self.enable_sentry = False
        
        # Adicionar tags padrão
        sentry_sdk.set_tag("service", "pdpj-client")
        sentry_sdk.set_tag("version", "2.0.0")
        
        logger.info("🚨 Sentry configurado para rastreamento de erros")
    
    def record_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """Registrar métricas de requisição."""
        if self.enable_prometheus:
            # Incrementar contador
            self.pdpj_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status=str(status_code)
            ).inc()
            
            # Registrar duração
            self.pdpj_request_duration.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)
        
        # Enviar para Sentry se erro
        if self.enable_sentry and status_code >= 400:
            with sentry_sdk.push_scope() as scope:
                scope.set_tag("endpoint", endpoint)
                scope.set_tag("method", method)
                scope.set_tag("status_code", status_code)
                scope.set_context("request", {
                    "method": method,
                    "endpoint": endpoint,
                    "duration": duration
                })
                sentry_sdk.capture_message(f"Erro HTTP {status_code} em {method} {endpoint}")
    
    def record_download(self, status: str, file_type: str, duration: float, size: int = 0):
        """Registrar métricas de download."""
        if self.enable_prometheus:
            # Incrementar contador
            self.pdpj_downloads_total.labels(
                status=status,
                file_type=file_type
            ).inc()
            
            # Registrar duração
            self.pdpj_download_duration.labels(
                file_type=file_type
            ).observe(duration)
        
        # Enviar para Sentry se falha
        if self.enable_sentry and status == "failed":
            with sentry_sdk.push_scope() as scope:
                scope.set_tag("file_type", file_type)
                scope.set_context("download", {
                    "file_type": file_type,
                    "duration": duration,
                    "size": size
                })
                sentry_sdk.capture_message(f"Falha no download de arquivo {file_type}")
    
    def record_error(self, error_type: str, endpoint: str, error_message: str):
        """Registrar erro."""
        if self.enable_prometheus:
            self.pdpj_errors_total.labels(
                error_type=error_type,
                endpoint=endpoint
            ).inc()
        
        if self.enable_sentry:
            with sentry_sdk.push_scope() as scope:
                scope.set_tag("error_type", error_type)
                scope.set_tag("endpoint", endpoint)
                scope.set_context("error", {
                    "type": error_type,
                    "endpoint": endpoint,
                    "message": error_message
                })
                sentry_sdk.capture_exception()
    
    def update_gauge_metrics(self, metrics: Dict[str, Any]):
        """Atualizar métricas de gauge com dados do cliente PDPJ."""
        if not self.enable_prometheus:
            return
        
        # Atualizar gauges
        self.pdpj_concurrent_requests.set(metrics.get('concurrent_requests', 0))
        self.pdpj_concurrent_downloads.set(metrics.get('concurrent_downloads', 0))
        self.pdpj_cache_hit_rate.set(metrics.get('session_cache_hit_rate', 0.0))
        self.pdpj_success_rate.set(metrics.get('success_rate', 0.0))
    
    def get_prometheus_metrics(self) -> str:
        """Obter métricas Prometheus em formato texto."""
        if not self.enable_prometheus:
            return "# Prometheus não disponível\n"
        
        return generate_latest(self.registry).decode('utf-8')
    
    def create_health_check_endpoint(self) -> Dict[str, Any]:
        """Criar endpoint de health check para monitoramento."""
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "2.0.0",
            "monitoring": {
                "prometheus_enabled": self.enable_prometheus,
                "sentry_enabled": self.enable_sentry
            }
        }
        
        # Adicionar métricas básicas se Prometheus estiver disponível
        if self.enable_prometheus:
            try:
                # Obter algumas métricas básicas
                health_status["metrics"] = {
                    "requests_total": "available",
                    "downloads_total": "available",
                    "errors_total": "available"
                }
            except Exception as e:
                health_status["status"] = "degraded"
                health_status["error"] = str(e)
        
        return health_status

# Instância global para uso em toda a aplicação
monitoring = MonitoringIntegration()

# Funções de conveniência
def record_request_metrics(method: str, endpoint: str, status_code: int, duration: float):
    """Registrar métricas de requisição."""
    monitoring.record_request(method, endpoint, status_code, duration)

def record_download_metrics(status: str, file_type: str, duration: float, size: int = 0):
    """Registrar métricas de download."""
    monitoring.record_download(status, file_type, duration, size)

def record_error_metrics(error_type: str, endpoint: str, error_message: str):
    """Registrar métricas de erro."""
    monitoring.record_error(error_type, endpoint, error_message)

def update_client_metrics(metrics: Dict[str, Any]):
    """Atualizar métricas do cliente."""
    monitoring.update_gauge_metrics(metrics)

def get_health_status() -> Dict[str, Any]:
    """Obter status de saúde."""
    return monitoring.create_health_check_endpoint()

def get_prometheus_metrics() -> str:
    """Obter métricas Prometheus."""
    return monitoring.get_prometheus_metrics()
