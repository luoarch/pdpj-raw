"""
Configurações da aplicação usando Pydantic Settings.

Este módulo define todas as configurações da aplicação PDPJ Process API usando Pydantic Settings,
fornecendo validação robusta, tipagem forte e suporte a múltiplos ambientes.

Principais recursos:
- Validação automática de campos e dependências cross-field
- Suporte a múltiplos perfis de ambiente (development, staging, production)
- Proteção de credenciais sensíveis com SecretStr
- Configurações otimizadas para performance e segurança
- Sistema de override de configurações via arquivos externos
- Logging avançado e observabilidade (métricas, tracing)

Exemplo de uso:
    from app.core.config import settings
    
    # Configurações são carregadas automaticamente do .env
    # e podem ser sobrescritas via variáveis de ambiente
    print(f"Ambiente: {settings.environment}")
    print(f"Debug: {settings.debug}")
    
Perfis de ambiente:
- development: Configurações permissivas para desenvolvimento local
- staging: Configurações intermediárias para testes e homologação  
- production: Configurações restritivas e otimizadas para produção

Variáveis de ambiente importantes:
- PROFILE: Define o perfil (development/staging/production)
- CONFIG_OVERRIDE_FILE: Arquivo adicional de configurações
- DATABASE_URL: URL de conexão com PostgreSQL
- REDIS_URL: URL de conexão com Redis
- AWS_ACCESS_KEY_ID: Credenciais AWS para S3
- PDPJ_API_TOKEN: Token da API PDPJ
"""

import os
import json
import yaml
import base64
import hashlib
from pathlib import Path
from typing import Optional, List, Set, Dict, Any, Union
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from pydantic import Field, field_validator, model_validator, SecretStr, ConfigDict
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Configurações da aplicação PDPJ Process API.
    
    Esta classe centraliza todas as configurações da aplicação, incluindo:
    - Configurações de banco de dados e cache
    - Credenciais e integrações externas (AWS, PDPJ, monitoramento)
    - Configurações de segurança e performance
    - Configurações de logging e observabilidade
    - Configurações específicas por ambiente
    
    A classe automaticamente:
    - Carrega configurações do arquivo .env
    - Aplica overrides de arquivos de configuração externos
    - Valida dependências entre campos
    - Ajusta configurações baseadas no perfil de ambiente
    """
    
    # Configurações do Banco de Dados
    database_url: str = Field(
        default="postgresql+asyncpg://user:password@localhost:5432/pdpj_db",
        description="URL de conexão com o PostgreSQL (ex: postgresql+asyncpg://user:pass@host:5432/db)"
    )
    
    # Configurações do Redis
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="URL de conexão com o Redis"
    )
    
    # Configurações da AWS S3
    aws_access_key_id: SecretStr = Field(default=SecretStr(""), description="AWS Access Key ID")
    aws_secret_access_key: SecretStr = Field(default=SecretStr(""), description="AWS Secret Access Key")
    aws_region: str = Field(default="us-east-1", description="Região da AWS")
    s3_bucket_name: str = Field(default="pdpj-documents-dev", description="Nome do bucket S3")
    
    # Configurações da API PDPJ
    pdpj_api_base_url: str = Field(
        default="https://api.pdpj.gov.br",
        description="URL base da API PDPJ"
    )
    pdpj_api_token: SecretStr = Field(default=SecretStr(""), description="Token da API PDPJ")
    
    # Configurações de timeout e retry para PDPJ
    pdpj_request_timeout: float = Field(default=30.0, description="Timeout para requisições PDPJ (segundos)")
    pdpj_download_timeout: float = Field(default=60.0, description="Timeout para downloads PDPJ (segundos)")
    pdpj_max_retries: int = Field(default=3, description="Número máximo de tentativas para requisições PDPJ")
    pdpj_retry_delay: float = Field(default=1.0, description="Delay entre tentativas PDPJ (segundos)")
    
    # Configurações de conexão HTTP para PDPJ
    pdpj_max_connections: int = Field(default=10, description="Número máximo de conexões HTTP simultâneas")
    pdpj_max_keepalive: int = Field(default=5, description="Número máximo de conexões keep-alive")
    
    # Configurações de Segurança
    secret_key: SecretStr = Field(default=SecretStr("dev-secret-key-change-in-production"), description="Chave secreta para JWT")
    api_key_header: str = Field(default="X-API-Key", description="Header da API Key")
    
    # Configurações de Rate Limiting
    rate_limit_requests: int = Field(default=100, description="Número de requisições por janela")
    rate_limit_window: int = Field(default=60, description="Janela de tempo em segundos")
    
    # Configurações de Cache
    cache_ttl: int = Field(default=3600, description="TTL do cache em segundos")
    
    # Configurações de Log
    log_level: str = Field(default="INFO", description="Nível de log")
    log_file: Optional[str] = Field(default=None, description="Arquivo de log")
    
    # Configurações do Celery
    celery_broker_url: str = Field(
        default="redis://localhost:6379/1",
        description="URL do broker Celery"
    )
    celery_result_backend: str = Field(
        default="redis://localhost:6379/1",
        description="Backend de resultados do Celery"
    )
    
    # Configurações de Performance HTTP
    max_concurrent_requests: int = Field(default=100, description="Máximo de requisições concorrentes")
    max_concurrent_downloads: int = Field(default=50, description="Máximo de downloads concorrentes")
    max_connections_per_host: int = Field(default=100, description="Máximo de conexões por host")
    connection_pool_size: int = Field(default=200, description="Tamanho do pool de conexões")
    keepalive_timeout: int = Field(default=30, description="Timeout de keepalive em segundos")
    request_timeout: int = Field(default=60, description="Timeout de requisição em segundos")
    download_timeout: int = Field(default=300, description="Timeout de download em segundos")
    
    # Configurações de Performance HTTP Avançadas
    enable_gzip_compression: bool = Field(default=True, description="Habilitar compressão GZip")
    gzip_minimum_size: int = Field(default=1000, description="Tamanho mínimo para compressão GZip em bytes")
    http2_enabled: bool = Field(default=True, description="Habilitar HTTP/2")
    tcp_nodelay: bool = Field(default=True, description="Habilitar TCP_NODELAY")
    tcp_keepalive: bool = Field(default=True, description="Habilitar TCP Keep-Alive")
    
    # Configurações de Workers
    uvicorn_workers: int = Field(default=4, description="Número de workers Uvicorn")
    celery_workers: int = Field(default=4, description="Número de workers Celery")
    
    # Configurações de Redis Otimizadas
    redis_max_connections: int = Field(default=100, description="Máximo de conexões Redis")
    redis_retry_on_timeout: bool = Field(default=True, description="Retry automático no Redis timeout")
    redis_socket_keepalive: bool = Field(default=True, description="Keepalive socket Redis")
    redis_socket_keepalive_options: dict = Field(
        default_factory=lambda: {1: 1, 2: 3, 3: 5}, 
        description="Opções de keepalive Redis"
    )
    
    # Configurações de Bulk Operations
    bulk_batch_size: int = Field(default=1000, description="Tamanho do lote para operações bulk")
    bulk_insert_chunk_size: int = Field(default=500, description="Tamanho do chunk para bulk insert")
    
    # Configurações de CORS
    cors_origins: Set[str] = Field(
        default_factory=lambda: {"http://localhost:3000", "http://localhost:8080"},
        description="Origens permitidas para CORS"
    )
    cors_allow_credentials: bool = Field(default=True, description="Permitir credenciais CORS")
    cors_allow_methods: Set[str] = Field(
        default_factory=lambda: {"GET", "POST", "PUT", "DELETE", "OPTIONS"},
        description="Métodos HTTP permitidos"
    )
    cors_allow_headers: Set[str] = Field(
        default_factory=lambda: {"*"},
        description="Headers permitidos"
    )
    
    # Configurações de API
    api_prefix: str = Field(default="/api/v1", description="Prefixo da API")
    api_title: str = Field(default="PDPJ Process API - Ultra-Fast Edition", description="Título da API")
    api_description: str = Field(
        default="API ultra-rápida para consulta e armazenamento de processos judiciais via PDPJ",
        description="Descrição da API"
    )
    api_version: str = Field(default="2.0.0", description="Versão da API")
    enable_legacy_routes: bool = Field(default=False, description="Habilitar rotas legacy com prefixo /legacy")
    enable_api_versioning: bool = Field(default=False, description="Habilitar middleware de versionamento dinâmico da API")
    
    @field_validator('api_prefix', mode='before')
    @classmethod
    def normalize_api_prefix(cls, v):
        """Normalizar prefixo da API durante carregamento."""
        if v is None or v == "/" or v == "":
            return "/api/v1"
        if not v.startswith("/"):
            return "/" + v.lstrip("/")
        if not v.startswith("/api/"):
            import warnings
            warnings.warn(f"Prefixo da API '{v}' não segue convenção padrão /api/vX")
        return v
    
    @model_validator(mode='after')
    def validate_cross_field_dependencies(self):
        """Validar dependências entre campos e aplicar configurações baseadas no ambiente."""
        
        # Validar perfil de ambiente
        valid_profiles = ['development', 'staging', 'production']
        if self.profile.lower() not in valid_profiles:
            raise ValueError(f"Perfil '{self.profile}' inválido. Use: {', '.join(valid_profiles)}")
        
        # Aplicar configurações baseadas no perfil
        profile = self.profile.lower()
        
        if profile == 'development':
            object.__setattr__(self, 'debug', True)
            object.__setattr__(self, 'enable_https_redirect', False)
            object.__setattr__(self, 'enable_security_headers', False)
            object.__setattr__(self, 'enable_rate_limiting', False)
            object.__setattr__(self, 'enable_metrics', False)
            object.__setattr__(self, 'enable_trusted_host', False)
            object.__setattr__(self, 'cors_origins', {"*"})
            object.__setattr__(self, 'log_level', "DEBUG")
            object.__setattr__(self, 'enable_gzip_compression', False)  # Desabilitar para facilitar debug
            object.__setattr__(self, 'rate_limit_requests', 0)
        elif profile == 'staging':
            object.__setattr__(self, 'debug', False)
            object.__setattr__(self, 'enable_https_redirect', True)
            object.__setattr__(self, 'enable_security_headers', True)
            object.__setattr__(self, 'enable_rate_limiting', True)
            object.__setattr__(self, 'rate_limit_requests', 500)  # Mais permissivo que produção
            object.__setattr__(self, 'enable_metrics', True)
            object.__setattr__(self, 'metrics_protected', False)  # Mais acessível para testes
            object.__setattr__(self, 'log_level', "INFO")
            object.__setattr__(self, 'enable_gzip_compression', True)
        elif profile == 'production':
            object.__setattr__(self, 'debug', False)
            object.__setattr__(self, 'enable_https_redirect', True)
            object.__setattr__(self, 'enable_security_headers', True)
            object.__setattr__(self, 'enable_rate_limiting', True)
            object.__setattr__(self, 'enable_metrics', True)
            object.__setattr__(self, 'metrics_protected', True)
            object.__setattr__(self, 'log_level', "WARNING")
            object.__setattr__(self, 'enable_gzip_compression', True)
            # Configurações mais restritivas para produção
            if self.rate_limit_requests > 1000:
                import warnings
                warnings.warn(f"Rate limit muito alto para produção: {self.rate_limit_requests}")
        
        # Sincronizar environment com profile se necessário
        if self.environment.lower() != profile:
            object.__setattr__(self, 'environment', profile)
        
        # Se rate limiting está desabilitado, ignorar configurações específicas
        if not self.enable_rate_limiting:
            object.__setattr__(self, 'rate_limit_requests', 0)
            object.__setattr__(self, 'rate_limit_window', 60)
        
        # Se tracing está habilitado, validar configurações
        if self.enable_tracing:
            if self.tracing_provider not in ['opentelemetry', 'jaeger', 'zipkin']:
                raise ValueError(f"Provedor de tracing '{self.tracing_provider}' não suportado")
            
            # Se endpoint é obrigatório para Jaeger e Zipkin
            if self.tracing_provider in ['jaeger', 'zipkin'] and not self.tracing_endpoint:
                raise ValueError(f"Endpoint de tracing é obrigatório para {self.tracing_provider}")
        
        # Validar taxa de amostragem de tracing
        if not 0.0 <= self.tracing_sample_rate <= 1.0:
            raise ValueError("Taxa de amostragem de tracing deve estar entre 0.0 e 1.0")
        
        # Validar configurações de log
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if self.log_level.upper() not in valid_levels:
            raise ValueError(f"Nível de log '{self.log_level}' inválido. Use: {', '.join(valid_levels)}")
        
        # Validar configurações de performance HTTP
        if self.max_connections_per_host <= 0:
            raise ValueError("Número máximo de conexões por host deve ser maior que 0")
        
        if self.max_concurrent_requests <= 0:
            raise ValueError("Número máximo de requisições concorrentes deve ser maior que 0")
        
        if self.max_concurrent_downloads <= 0:
            raise ValueError("Número máximo de downloads concorrentes deve ser maior que 0")
        
        if self.connection_pool_size <= 0:
            raise ValueError("Tamanho do pool de conexões deve ser maior que 0")
        
        # Validar configurações de cache
        if self.cache_ttl < 0:
            raise ValueError("TTL do cache não pode ser negativo")
        
        # Validar configurações de workers
        if self.uvicorn_workers <= 0:
            raise ValueError("Número de workers Uvicorn deve ser maior que 0")
        
        if self.celery_workers <= 0:
            raise ValueError("Número de workers Celery deve ser maior que 0")
        
        # Validar configurações de GZip
        if self.gzip_minimum_size < 0:
            raise ValueError("Tamanho mínimo para compressão GZip não pode ser negativo")
        
        # Validar configurações de bulk operations
        if self.bulk_batch_size <= 0:
            raise ValueError("Tamanho do lote para operações bulk deve ser maior que 0")
        
        if self.bulk_insert_chunk_size <= 0:
            raise ValueError("Tamanho do chunk para bulk insert deve ser maior que 0")
        
        # Validar configurações de Redis
        if self.redis_max_connections <= 0:
            raise ValueError("Número máximo de conexões Redis deve ser maior que 0")
        
        # Validar configurações de timeouts
        timeouts = [
            ('keepalive_timeout', self.keepalive_timeout),
            ('request_timeout', self.request_timeout),
            ('download_timeout', self.download_timeout),
        ]
        
        for timeout_name, timeout_value in timeouts:
            if timeout_value <= 0:
                raise ValueError(f"{timeout_name} deve ser maior que 0")
        
        # Validar configurações de segurança
        if self.hsts_max_age < 0:
            raise ValueError("HSTS max age não pode ser negativo")
        
        # Validar configurações de retenção de logs
        if self.log_retention_days < 0:
            raise ValueError("Dias de retenção de logs não pode ser negativo")
        
        # Validar configurações de métricas
        if self.metrics_cache_ttl < 0:
            raise ValueError("TTL do cache de métricas não pode ser negativo")
        
        return self
    
    # Configurações de Segurança
    enable_https_redirect: bool = Field(default=True, description="Habilitar redirecionamento HTTPS")
    enable_security_headers: bool = Field(default=True, description="Habilitar headers de segurança")
    enable_trusted_host: bool = Field(default=True, description="Habilitar validação de hosts confiáveis")
    enable_global_exception_handler: bool = Field(default=True, description="Habilitar captura global de exceções")
    hsts_max_age: int = Field(default=31536000, description="HSTS max age em segundos")
    content_security_policy: str = Field(
        default="default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
        description="Content Security Policy"
    )
    
    # Configurações Avançadas de Headers de Segurança
    security_headers_cache_control: str = Field(
        default="public, max-age=31536000, immutable",
        description="Cache-Control para headers de segurança"
    )
    frame_options: str = Field(default="DENY", description="X-Frame-Options policy")
    xss_protection: str = Field(default="1; mode=block", description="X-XSS-Protection policy")
    referrer_policy: str = Field(
        default="strict-origin-when-cross-origin",
        description="Referrer-Policy"
    )
    permissions_policy: str = Field(
        default="geolocation=(), microphone=(), camera=(), payment=(), usb=(), magnetometer=(), gyroscope=(), speaker=()",
        description="Permissions-Policy"
    )
    coep_policy: str = Field(default="require-corp", description="Cross-Origin-Embedder-Policy")
    coop_policy: str = Field(default="same-origin", description="Cross-Origin-Opener-Policy")
    corp_policy: str = Field(default="same-origin", description="Cross-Origin-Resource-Policy")
    
    # Configurações de Rate Limiting
    enable_rate_limiting: bool = Field(default=True, description="Habilitar rate limiting")
    rate_limit_requests: int = Field(default=1000, description="Limite de requisições por minuto")
    rate_limit_window: int = Field(default=60, description="Janela de tempo em segundos")
    
    # Configurações de Logging
    log_request_id: bool = Field(default=True, description="Incluir request ID nos logs")
    log_level: str = Field(default="INFO", description="Nível de log")
    log_format: str = Field(
        default="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
        description="Formato dos logs"
    )
    log_rotation_size: str = Field(default="100 MB", description="Tamanho máximo do arquivo de log antes da rotação")
    log_retention_days: int = Field(default=30, description="Dias para retenção de logs")
    
    # Configurações de Health Check
    health_check_include_version: bool = Field(default=True, description="Incluir versão no health check")
    health_check_include_timestamp: bool = Field(default=True, description="Incluir timestamp no health check")
    
    # Configurações de Cache Crítico
    cache_critical: bool = Field(default=False, description="Cache é crítico (abortar startup se falhar)")
    
    # Configurações de Observabilidade
    enable_metrics: bool = Field(default=True, description="Habilitar métricas Prometheus")
    metrics_path: str = Field(default="/metrics", description="Path para métricas Prometheus")
    metrics_protected: bool = Field(default=True, description="Proteger endpoint de métricas")
    metrics_cache_ttl: int = Field(default=30, description="TTL do cache de métricas em segundos")
    enable_tracing: bool = Field(default=False, description="Habilitar tracing distribuído")
    tracing_sample_rate: float = Field(default=0.1, description="Taxa de amostragem para tracing")
    tracing_provider: str = Field(default="opentelemetry", description="Provedor de tracing (opentelemetry, jaeger)")
    tracing_endpoint: Optional[str] = Field(default=None, description="Endpoint do serviço de tracing")
    tracing_service_name: str = Field(default="pdpj-api", description="Nome do serviço para tracing")
    tracing_service_version: str = Field(default="2.0.0", description="Versão do serviço para tracing")
    
    # Configurações de Monitoramento Externo
    sentry_dsn: Optional[SecretStr] = Field(default=None, description="DSN do Sentry para error tracking")
    datadog_api_key: Optional[SecretStr] = Field(default=None, description="API Key do Datadog")
    newrelic_license_key: Optional[SecretStr] = Field(default=None, description="License Key do New Relic")
    honeycomb_api_key: Optional[SecretStr] = Field(default=None, description="API Key do Honeycomb")
    
    # Configurações de Logging Avançado
    log_include_user_id: bool = Field(default=False, description="Incluir user_id nos logs")
    log_include_trace_id: bool = Field(default=False, description="Incluir trace_id nos logs")
    
    # Configurações de Criptografia
    enable_field_encryption: bool = Field(default=False, description="Habilitar criptografia de campos sensíveis")
    encryption_key: Optional[SecretStr] = Field(default=None, description="Chave de criptografia para campos sensíveis")
    encryption_salt: Optional[str] = Field(default=None, description="Salt para derivação de chave de criptografia")
    
    # Configurações de Ambiente
    debug: bool = Field(default=False, description="Modo debug")
    environment: str = Field(default="production", description="Ambiente de execução")
    profile: str = Field(default="production", description="Perfil de configuração (development, staging, production)")
    config_override_file: Optional[str] = Field(default=None, description="Arquivo de override de configuração")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow",  # Permitir campos extras para testes
        case_sensitive=False,
        validate_assignment=True,  # Validar atribuições
        use_enum_values=True,  # Usar valores de enum
        str_strip_whitespace=True,  # Remover espaços em branco
    )
    
    @classmethod
    def load_override_file(cls, file_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Carrega configurações de um arquivo de override.
        
        Args:
            file_path: Caminho para o arquivo de override. Se None, usa CONFIG_OVERRIDE_FILE.
            
        Returns:
            Dicionário com as configurações carregadas.
            
        Raises:
            ValueError: Se o formato do arquivo não for suportado.
            FileNotFoundError: Se o arquivo não existir.
        """
        if not file_path:
            file_path = os.getenv("CONFIG_OVERRIDE_FILE")
            
        if not file_path:
            return {}
            
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Arquivo de configuração não encontrado: {file_path}")
        
        suffix = path.suffix.lower()
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                if suffix == '.json':
                    return json.load(f)
                elif suffix in ['.yml', '.yaml']:
                    return yaml.safe_load(f)
                elif suffix == '.env':
                    # Para arquivos .env, retornar dicionário vazio
                    # O Pydantic Settings já cuida disso
                    return {}
                else:
                    raise ValueError(f"Formato de arquivo não suportado: {suffix}")
        except Exception as e:
            raise ValueError(f"Erro ao carregar arquivo de configuração {file_path}: {e}")
    
    @classmethod
    def create_with_overrides(cls, **kwargs) -> "Settings":
        """
        Cria uma instância de Settings com overrides específicos.
        
        Args:
            **kwargs: Configurações para sobrescrever.
            
        Returns:
            Nova instância de Settings com as configurações aplicadas.
        """
        # Carregar override file se especificado
        override_config = cls.load_override_file()
        
        # Mesclar configurações: override_file < kwargs < env vars
        final_config = {**override_config, **kwargs}
        
        return cls(**final_config)
    
    def _derive_encryption_key(self, password: str, salt: bytes) -> bytes:
        """
        Deriva uma chave de criptografia usando PBKDF2.
        
        Args:
            password: Senha para derivação
            salt: Salt para derivação
            
        Returns:
            Chave derivada de 32 bytes
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))
    
    def _get_fernet_instance(self) -> Optional[Fernet]:
        """
        Cria uma instância Fernet para criptografia.
        
        Returns:
            Instância Fernet ou None se criptografia não estiver habilitada
        """
        if not self.enable_field_encryption:
            return None
            
        if not self.encryption_key:
            raise ValueError("Chave de criptografia é obrigatória quando enable_field_encryption=True")
        
        # Usar salt padrão se não fornecido
        salt = self.encryption_salt or "pdpj_default_salt"
        
        # Derivar chave
        key = self._derive_encryption_key(
            self.encryption_key.get_secret_value(),
            salt.encode()
        )
        
        return Fernet(key)
    
    def encrypt_sensitive_value(self, value: str) -> str:
        """
        Criptografa um valor sensível.
        
        Args:
            value: Valor a ser criptografado
            
        Returns:
            Valor criptografado em base64
            
        Raises:
            ValueError: Se criptografia não estiver configurada
        """
        if not value:
            return value
            
        fernet = self._get_fernet_instance()
        if not fernet:
            return value
            
        encrypted = fernet.encrypt(value.encode())
        return base64.b64encode(encrypted).decode()
    
    def decrypt_sensitive_value(self, encrypted_value: str) -> str:
        """
        Descriptografa um valor sensível.
        
        Args:
            encrypted_value: Valor criptografado em base64
            
        Returns:
            Valor descriptografado
            
        Raises:
            ValueError: Se criptografia não estiver configurada ou valor inválido
        """
        if not encrypted_value:
            return encrypted_value
            
        fernet = self._get_fernet_instance()
        if not fernet:
            return encrypted_value
            
        try:
            encrypted_bytes = base64.b64decode(encrypted_value.encode())
            decrypted = fernet.decrypt(encrypted_bytes)
            return decrypted.decode()
        except Exception as e:
            raise ValueError(f"Erro ao descriptografar valor: {e}")
    
    def get_safe_database_url(self) -> str:
        """
        Retorna a URL do banco de dados com credenciais protegidas se necessário.
        
        Returns:
            URL do banco de dados (criptografada se habilitado)
        """
        if self.enable_field_encryption and self.encryption_key:
            return self.encrypt_sensitive_value(self.database_url)
        return self.database_url
    
    def get_safe_redis_url(self) -> str:
        """
        Retorna a URL do Redis com credenciais protegidas se necessário.
        
        Returns:
            URL do Redis (criptografada se habilitado)
        """
        if self.enable_field_encryption and self.encryption_key:
            return self.encrypt_sensitive_value(self.redis_url)
        return self.redis_url
    
    def get_safe_aws_credentials(self) -> Dict[str, str]:
        """
        Retorna credenciais AWS com valores protegidos se necessário.
        
        Returns:
            Dicionário com credenciais AWS (criptografadas se habilitado)
        """
        credentials = {
            "access_key_id": self.aws_access_key_id.get_secret_value(),
            "secret_access_key": self.aws_secret_access_key.get_secret_value(),
            "region": self.aws_region
        }
        
        if self.enable_field_encryption and self.encryption_key:
            credentials["access_key_id"] = self.encrypt_sensitive_value(credentials["access_key_id"])
            credentials["secret_access_key"] = self.encrypt_sensitive_value(credentials["secret_access_key"])
        
        return credentials
    
    def get_safe_pdpj_token(self) -> str:
        """
        Retorna o token PDPJ com valor protegido se necessário.
        
        Returns:
            Token PDPJ (criptografado se habilitado)
        """
        token = self.pdpj_api_token.get_secret_value()
        if self.enable_field_encryption and self.encryption_key:
            return self.encrypt_sensitive_value(token)
        return token


# Instância global das configurações
# Carrega automaticamente overrides se CONFIG_OVERRIDE_FILE estiver definido
try:
    settings = Settings.create_with_overrides()
except Exception as e:
    # Se houver erro ao carregar overrides, usar configuração padrão
    import warnings
    warnings.warn(f"Erro ao carregar configurações de override: {e}. Usando configuração padrão.")
    settings = Settings()
