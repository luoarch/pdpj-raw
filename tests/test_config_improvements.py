"""Testes para as melhorias nas configurações."""

import pytest
from pydantic import ValidationError, SecretStr
from app.core.config import Settings


class TestSecretFields:
    """Testes para campos secretos adicionais."""
    
    def test_new_monitoring_secrets(self):
        """Testar novos campos secretos de monitoramento."""
        settings = Settings(
            SENTRY_DSN="https://sentry.io/test",
            DATADOG_API_KEY="test_datadog_key",
            NEWRELIC_LICENSE_KEY="test_newrelic_key",
            HONEYCOMB_API_KEY="test_honeycomb_key"
        )
        
        assert isinstance(settings.sentry_dsn, SecretStr)
        assert settings.sentry_dsn.get_secret_value() == "https://sentry.io/test"
        
        assert isinstance(settings.datadog_api_key, SecretStr)
        assert settings.datadog_api_key.get_secret_value() == "test_datadog_key"
        
        assert isinstance(settings.newrelic_license_key, SecretStr)
        assert settings.newrelic_license_key.get_secret_value() == "test_newrelic_key"
        
        assert isinstance(settings.honeycomb_api_key, SecretStr)
        assert settings.honeycomb_api_key.get_secret_value() == "test_honeycomb_key"


class TestProfileConfiguration:
    """Testes para configurações baseadas em perfis."""
    
    def test_development_profile(self):
        """Testar perfil de desenvolvimento."""
        settings = Settings(PROFILE="development")
        
        assert settings.debug is True
        assert settings.enable_https_redirect is False
        assert settings.enable_security_headers is False
        assert settings.enable_rate_limiting is False
        assert settings.enable_metrics is False
        assert settings.enable_trusted_host is False
        assert settings.cors_origins == {"*"}
        assert settings.log_level == "DEBUG"
        assert settings.enable_gzip_compression is False
        assert settings.rate_limit_requests == 0
    
    def test_staging_profile(self):
        """Testar perfil de staging."""
        settings = Settings(PROFILE="staging")
        
        assert settings.debug is False
        assert settings.enable_https_redirect is True
        assert settings.enable_security_headers is True
        assert settings.enable_rate_limiting is True
        assert settings.rate_limit_requests == 500
        assert settings.enable_metrics is True
        assert settings.metrics_protected is False
        assert settings.log_level == "INFO"
        assert settings.enable_gzip_compression is True
    
    def test_production_profile(self):
        """Testar perfil de produção."""
        settings = Settings(PROFILE="production")
        
        assert settings.debug is False
        assert settings.enable_https_redirect is True
        assert settings.enable_security_headers is True
        assert settings.enable_rate_limiting is True
        assert settings.enable_metrics is True
        assert settings.metrics_protected is True
        assert settings.log_level == "WARNING"
        assert settings.enable_gzip_compression is True
    
    def test_invalid_profile(self):
        """Testar perfil inválido."""
        with pytest.raises(ValidationError, match="Perfil 'invalid' inválido"):
            Settings(PROFILE="invalid")
    
    def test_profile_environment_sync(self):
        """Testar sincronização entre profile e environment."""
        settings = Settings(PROFILE="staging", ENVIRONMENT="production")
        
        assert settings.profile == "staging"
        assert settings.environment == "staging"  # Deve sincronizar com profile


class TestEnhancedValidations:
    """Testes para validações aprimoradas."""
    
    def test_http_performance_validations(self):
        """Testar validações de performance HTTP."""
        with pytest.raises(ValidationError, match="Número máximo de conexões por host deve ser maior que 0"):
            Settings(MAX_CONNECTIONS_PER_HOST=0)
        
        with pytest.raises(ValidationError, match="Número máximo de requisições concorrentes deve ser maior que 0"):
            Settings(MAX_CONCURRENT_REQUESTS=0)
        
        with pytest.raises(ValidationError, match="Número máximo de downloads concorrentes deve ser maior que 0"):
            Settings(MAX_CONCURRENT_DOWNLOADS=0)
        
        with pytest.raises(ValidationError, match="Tamanho do pool de conexões deve ser maior que 0"):
            Settings(CONNECTION_POOL_SIZE=0)
    
    def test_workers_validations(self):
        """Testar validações de workers."""
        with pytest.raises(ValidationError, match="Número de workers Uvicorn deve ser maior que 0"):
            Settings(UVICORN_WORKERS=0)
        
        with pytest.raises(ValidationError, match="Número de workers Celery deve ser maior que 0"):
            Settings(CELERY_WORKERS=0)
    
    def test_bulk_operations_validations(self):
        """Testar validações de operações bulk."""
        with pytest.raises(ValidationError, match="Tamanho do lote para operações bulk deve ser maior que 0"):
            Settings(BULK_BATCH_SIZE=0)
        
        with pytest.raises(ValidationError, match="Tamanho do chunk para bulk insert deve ser maior que 0"):
            Settings(BULK_INSERT_CHUNK_SIZE=0)
    
    def test_redis_validations(self):
        """Testar validações do Redis."""
        with pytest.raises(ValidationError, match="Número máximo de conexões Redis deve ser maior que 0"):
            Settings(REDIS_MAX_CONNECTIONS=0)
    
    def test_timeout_validations(self):
        """Testar validações de timeouts."""
        with pytest.raises(ValidationError, match="keepalive_timeout deve ser maior que 0"):
            Settings(KEEPALIVE_TIMEOUT=0)
        
        with pytest.raises(ValidationError, match="request_timeout deve ser maior que 0"):
            Settings(REQUEST_TIMEOUT=0)
        
        with pytest.raises(ValidationError, match="download_timeout deve ser maior que 0"):
            Settings(DOWNLOAD_TIMEOUT=0)
    
    def test_gzip_validations(self):
        """Testar validações do GZip."""
        with pytest.raises(ValidationError, match="Tamanho mínimo para compressão GZip não pode ser negativo"):
            Settings(GZIP_MINIMUM_SIZE=-1)
    
    def test_security_validations(self):
        """Testar validações de segurança."""
        with pytest.raises(ValidationError, match="HSTS max age não pode ser negativo"):
            Settings(HSTS_MAX_AGE=-1)
    
    def test_logging_validations(self):
        """Testar validações de logging."""
        with pytest.raises(ValidationError, match="Dias de retenção de logs não pode ser negativo"):
            Settings(LOG_RETENTION_DAYS=-1)
    
    def test_metrics_validations(self):
        """Testar validações de métricas."""
        with pytest.raises(ValidationError, match="TTL do cache de métricas não pode ser negativo"):
            Settings(METRICS_CACHE_TTL=-1)


class TestTracingImprovements:
    """Testes para melhorias no tracing."""
    
    def test_zipkin_provider(self):
        """Testar provedor Zipkin."""
        settings = Settings(
            ENABLE_TRACING=True,
            TRACING_PROVIDER="zipkin",
            TRACING_ENDPOINT="http://zipkin:9411"
        )
        
        assert settings.tracing_provider == "zipkin"
        assert settings.tracing_endpoint == "http://zipkin:9411"
    
    def test_zipkin_without_endpoint(self):
        """Testar Zipkin sem endpoint."""
        with pytest.raises(ValidationError, match="Endpoint de tracing é obrigatório para zipkin"):
            Settings(
                ENABLE_TRACING=True,
                TRACING_PROVIDER="zipkin",
                TRACING_ENDPOINT=None
            )
    
    def test_invalid_tracing_provider(self):
        """Testar provedor de tracing inválido."""
        with pytest.raises(ValidationError, match="Provedor de tracing 'invalid' não suportado"):
            Settings(
                ENABLE_TRACING=True,
                TRACING_PROVIDER="invalid"
            )


class TestHTTPAdvancedFeatures:
    """Testes para funcionalidades HTTP avançadas."""
    
    def test_http2_configuration(self):
        """Testar configuração do HTTP/2."""
        settings = Settings(HTTP2_ENABLED=False)
        assert settings.http2_enabled is False
        
        settings = Settings(HTTP2_ENABLED=True)
        assert settings.http2_enabled is True
    
    def test_tcp_configurations(self):
        """Testar configurações TCP."""
        settings = Settings(
            TCP_NODELAY=False,
            TCP_KEEPALIVE=False
        )
        
        assert settings.tcp_nodelay is False
        assert settings.tcp_keepalive is False


class TestProfileWarnings:
    """Testes para warnings em perfis."""
    
    def test_production_rate_limit_warning(self):
        """Testar warning para rate limit alto em produção."""
        with pytest.warns(UserWarning, match="Rate limit muito alto para produção"):
            Settings(
                PROFILE="production",
                RATE_LIMIT_REQUESTS=2000
            )
    
    def test_no_warning_for_reasonable_rate_limit(self):
        """Testar que não há warning para rate limit razoável."""
        with pytest.warns(None):
            Settings(
                PROFILE="production",
                RATE_LIMIT_REQUESTS=500
            )


class TestConfigurationOverride:
    """Testes para override de configuração."""
    
    def test_config_override_file_field(self):
        """Testar campo de arquivo de override."""
        settings = Settings(CONFIG_OVERRIDE_FILE="/path/to/override.env")
        assert settings.config_override_file == "/path/to/override.env"
    
    def test_config_override_file_none(self):
        """Testar campo de override como None."""
        settings = Settings(CONFIG_OVERRIDE_FILE=None)
        assert settings.config_override_file is None


class TestEnvironmentSpecificDefaults:
    """Testes para valores padrão específicos do ambiente."""
    
    def test_development_defaults_override(self):
        """Testar que valores padrão de desenvolvimento sobrescrevem configurações."""
        settings = Settings(
            PROFILE="development",
            DEBUG=False,  # Deve ser sobrescrito para True
            ENABLE_HTTPS_REDIRECT=True,  # Deve ser sobrescrito para False
            LOG_LEVEL="ERROR"  # Deve ser sobrescrito para DEBUG
        )
        
        assert settings.debug is True
        assert settings.enable_https_redirect is False
        assert settings.log_level == "DEBUG"
    
    def test_staging_defaults_override(self):
        """Testar que valores padrão de staging sobrescrevem configurações."""
        settings = Settings(
            PROFILE="staging",
            DEBUG=True,  # Deve ser sobrescrito para False
            METRICS_PROTECTED=True,  # Deve ser sobrescrito para False
            LOG_LEVEL="ERROR"  # Deve ser sobrescrito para INFO
        )
        
        assert settings.debug is False
        assert settings.metrics_protected is False
        assert settings.log_level == "INFO"
    
    def test_production_defaults_override(self):
        """Testar que valores padrão de produção sobrescrevem configurações."""
        settings = Settings(
            PROFILE="production",
            DEBUG=True,  # Deve ser sobrescrito para False
            METRICS_PROTECTED=False,  # Deve ser sobrescrito para True
            LOG_LEVEL="DEBUG"  # Deve ser sobrescrito para WARNING
        )
        
        assert settings.debug is False
        assert settings.metrics_protected is True
        assert settings.log_level == "WARNING"
