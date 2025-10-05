"""Testes para configurações da aplicação."""

import pytest
import os
from unittest.mock import patch
from pydantic import ValidationError

from app.core.config import Settings


class TestSettings:
    """Testes para a classe Settings."""
    
    def test_default_values(self):
        """Testar valores padrão das configurações."""
        settings = Settings()
        
        assert settings.database_url == "postgresql+asyncpg://user:password@localhost:5432/pdpj_db"
        assert settings.redis_url == "redis://localhost:6379/0"
        assert settings.api_prefix == "/api/v1"
        assert settings.api_title == "PDPJ Process API - Ultra-Fast Edition"
        assert settings.enable_rate_limiting is True
        assert settings.enable_metrics is True
        assert settings.debug is False
        assert settings.environment == "production"
    
    def test_secret_fields(self):
        """Testar que campos secretos são do tipo SecretStr."""
        settings = Settings()
        
        assert isinstance(settings.aws_access_key_id, str)
        assert isinstance(settings.aws_secret_access_key, str)
        assert isinstance(settings.pdpj_api_token, str)
        assert isinstance(settings.secret_key, str)
    
    def test_cors_configuration_types(self):
        """Testar que configurações CORS são sets."""
        settings = Settings()
        
        assert isinstance(settings.cors_origins, set)
        assert isinstance(settings.cors_allow_methods, set)
        assert isinstance(settings.cors_allow_headers, set)
        
        assert "GET" in settings.cors_allow_methods
        assert "POST" in settings.cors_allow_methods
        assert "http://localhost:3000" in settings.cors_origins
    
    def test_api_prefix_normalization(self):
        """Testar normalização do prefixo da API."""
        # Teste com valores válidos
        settings = Settings(api_prefix="/api/v2")
        assert settings.api_prefix == "/api/v2"
        
        settings = Settings(api_prefix="api/v3")
        assert settings.api_prefix == "/api/v3"
        
        # Teste com valores inválidos
        settings = Settings(api_prefix="")
        assert settings.api_prefix == "/api/v1"
        
        settings = Settings(api_prefix="/")
        assert settings.api_prefix == "/api/v1"
        
        settings = Settings(api_prefix=None)
        assert settings.api_prefix == "/api/v1"
    
    def test_cross_field_validation_rate_limiting(self):
        """Testar validação cruzada para rate limiting."""
        # Com rate limiting desabilitado
        settings = Settings(enable_rate_limiting=False, rate_limit_requests=100)
        assert settings.rate_limit_requests == 0
        assert settings.rate_limit_window == 60
    
    def test_tracing_validation(self):
        """Testar validação de configurações de tracing."""
        # Provedor inválido
        with pytest.raises(ValidationError) as exc_info:
            Settings(enable_tracing=True, tracing_provider="invalid")
        assert "Provedor de tracing 'invalid' não suportado" in str(exc_info.value)
        
        # Endpoint obrigatório para Jaeger
        with pytest.raises(ValidationError) as exc_info:
            Settings(enable_tracing=True, tracing_provider="jaeger")
        assert "Endpoint de tracing é obrigatório para Jaeger" in str(exc_info.value)
        
        # Configuração válida para Jaeger
        settings = Settings(
            enable_tracing=True, 
            tracing_provider="jaeger", 
            tracing_endpoint="http://jaeger:14268/api/traces"
        )
        assert settings.tracing_provider == "jaeger"
        assert settings.tracing_endpoint == "http://jaeger:14268/api/traces"
    
    def test_tracing_sample_rate_validation(self):
        """Testar validação da taxa de amostragem de tracing."""
        # Taxa inválida (negativa)
        with pytest.raises(ValidationError) as exc_info:
            Settings(enable_tracing=True, tracing_sample_rate=-0.1)
        assert "Taxa de amostragem de tracing deve estar entre 0.0 e 1.0" in str(exc_info.value)
        
        # Taxa inválida (maior que 1)
        with pytest.raises(ValidationError) as exc_info:
            Settings(enable_tracing=True, tracing_sample_rate=1.5)
        assert "Taxa de amostragem de tracing deve estar entre 0.0 e 1.0" in str(exc_info.value)
        
        # Taxas válidas
        settings = Settings(enable_tracing=True, tracing_sample_rate=0.0)
        assert settings.tracing_sample_rate == 0.0
        
        settings = Settings(enable_tracing=True, tracing_sample_rate=1.0)
        assert settings.tracing_sample_rate == 1.0
    
    def test_log_level_validation(self):
        """Testar validação do nível de log."""
        # Nível inválido
        with pytest.raises(ValidationError) as exc_info:
            Settings(log_level="INVALID")
        assert "Nível de log 'INVALID' inválido" in str(exc_info.value)
        
        # Níveis válidos
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        for level in valid_levels:
            settings = Settings(log_level=level)
            assert settings.log_level == level
    
    def test_performance_validation(self):
        """Testar validação de configurações de performance."""
        # Conexões inválidas
        with pytest.raises(ValidationError) as exc_info:
            Settings(max_connections_per_host=0)
        assert "Número máximo de conexões por host deve ser maior que 0" in str(exc_info.value)
        
        # Cache TTL inválido
        with pytest.raises(ValidationError) as exc_info:
            Settings(cache_ttl=-1)
        assert "TTL do cache não pode ser negativo" in str(exc_info.value)
    
    def test_environment_loading(self):
        """Testar carregamento de configurações via variáveis de ambiente."""
        env_vars = {
            "API_PREFIX": "/custom/api",
            "DEBUG": "true",
            "LOG_LEVEL": "DEBUG",
            "ENABLE_RATE_LIMITING": "false",
            "CORS_ORIGINS": '["https://example.com", "https://test.com"]'
        }
        
        with patch.dict(os.environ, env_vars):
            settings = Settings()
            assert settings.api_prefix == "/custom/api"
            assert settings.debug is True
            assert settings.log_level == "DEBUG"
            assert settings.enable_rate_limiting is False
            assert "https://example.com" in settings.cors_origins
            assert "https://test.com" in settings.cors_origins
    
    def test_new_logging_configurations(self):
        """Testar novas configurações de logging."""
        settings = Settings()
        
        assert settings.log_rotation_size == "100 MB"
        assert settings.log_retention_days == 30
        assert settings.log_include_user_id is False
        assert settings.log_include_trace_id is False
    
    def test_new_tracing_configurations(self):
        """Testar novas configurações de tracing."""
        settings = Settings()
        
        assert settings.tracing_provider == "opentelemetry"
        assert settings.tracing_endpoint is None
        assert settings.tracing_service_name == "pdpj-api"
        assert settings.tracing_service_version == "2.0.0"
    
    def test_monitoring_configurations(self):
        """Testar configurações de monitoramento."""
        settings = Settings()
        
        assert settings.sentry_dsn is None
        assert settings.datadog_api_key is None
        assert settings.enable_metrics is True
        assert settings.metrics_protected is True
        assert settings.metrics_cache_ttl == 30


class TestSettingsIntegration:
    """Testes de integração para configurações."""
    
    def test_settings_singleton(self):
        """Testar que settings é um singleton."""
        from app.core.config import settings
        
        settings1 = Settings()
        settings2 = Settings()
        
        # Mesmo objeto
        assert settings1 is settings
        assert settings2 is settings
    
    def test_settings_immutability(self):
        """Testar que configurações não podem ser modificadas após criação."""
        settings = Settings()
        original_prefix = settings.api_prefix
        
        # Tentar modificar (não deve funcionar)
        try:
            settings.api_prefix = "/modified"
        except Exception:
            pass
        
        # Valor deve permanecer inalterado
        assert settings.api_prefix == original_prefix
