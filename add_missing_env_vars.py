#!/usr/bin/env python3
"""
Script para adicionar variáveis de ambiente faltantes ao arquivo .env
"""

import os
from pathlib import Path

def add_missing_env_vars():
    """Adiciona variáveis de ambiente faltantes ao .env"""
    
    env_file = Path(".env")
    
    # Variáveis importantes que estão faltando
    missing_vars = {
        # Configurações de Performance
        "MAX_CONCURRENT_REQUESTS": "100",
        "MAX_CONCURRENT_DOWNLOADS": "50", 
        "CONNECTION_POOL_SIZE": "200",
        "MAX_CONNECTIONS_PER_HOST": "100",
        "REQUEST_TIMEOUT": "60",
        "DOWNLOAD_TIMEOUT": "300",
        
        # Configurações de Segurança
        "ENABLE_SECURITY_HEADERS": "True",
        "ENABLE_RATE_LIMITING": "True",
        "HSTS_MAX_AGE": "31536000",
        "FRAME_OPTIONS": "DENY",
        "XSS_PROTECTION": "1; mode=block",
        "REFERRER_POLICY": "strict-origin-when-cross-origin",
        "PERMISSIONS_POLICY": "geolocation=(), microphone=(), camera=(), payment=(), usb=(), magnetometer=(), gyroscope=(), speaker=()",
        "COEP_POLICY": "require-corp",
        "COOP_POLICY": "same-origin",
        "CORP_POLICY": "same-origin",
        
        # Configurações de API
        "API_PREFIX": "/api/v1",
        "API_TITLE": "PDPJ Process API - Ultra-Fast Edition",
        "API_DESCRIPTION": "API ultra-rápida para consulta e armazenamento de processos judiciais via PDPJ",
        "API_VERSION": "2.0.0",
        
        # Configurações de Logging
        "LOG_FORMAT": "{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
        "LOG_ROTATION_SIZE": "100 MB",
        "LOG_RETENTION_DAYS": "30",
        "LOG_REQUEST_ID": "True",
        
        # Configurações de Observabilidade
        "ENABLE_METRICS": "True",
        "METRICS_PATH": "/metrics",
        "METRICS_PROTECTED": "True",
        "METRICS_CACHE_TTL": "30",
        "ENABLE_TRACING": "False",
        "TRACING_SAMPLE_RATE": "0.1",
        "TRACING_PROVIDER": "opentelemetry",
        "TRACING_SERVICE_NAME": "pdpj-api",
        "TRACING_SERVICE_VERSION": "2.0.0",
        
        # Configurações de Performance HTTP
        "ENABLE_GZIP_COMPRESSION": "True",
        "GZIP_MINIMUM_SIZE": "1000",
        "HTTP2_ENABLED": "True",
        "TCP_NODELAY": "True",
        "TCP_KEEPALIVE": "True",
        "KEEPALIVE_TIMEOUT": "30",
        
        # Configurações de Workers
        "UVICORN_WORKERS": "4",
        "CELERY_WORKERS": "4",
        
        # Configurações de Redis
        "REDIS_MAX_CONNECTIONS": "100",
        "REDIS_RETRY_ON_TIMEOUT": "True",
        "REDIS_SOCKET_KEEPALIVE": "True",
        "REDIS_SOCKET_KEEPALIVE_OPTIONS": '{"1": 1, "2": 3, "3": 5}',
        
        # Configurações de Bulk Operations
        "BULK_BATCH_SIZE": "1000",
        "BULK_INSERT_CHUNK_SIZE": "500",
        
        # Configurações de CORS
        "CORS_ORIGINS": '["http://localhost:3000", "http://localhost:8080"]',
        "CORS_ALLOW_CREDENTIALS": "True",
        "CORS_ALLOW_METHODS": '["GET", "POST", "PUT", "DELETE", "OPTIONS"]',
        "CORS_ALLOW_HEADERS": '["*"]',
        
        # Configurações de Health Check
        "HEALTH_CHECK_INCLUDE_VERSION": "True",
        "HEALTH_CHECK_INCLUDE_TIMESTAMP": "True",
        
        # Configurações de Cache
        "CACHE_CRITICAL": "False",
        
        # Configurações de Segurança Avançada
        "ENABLE_TRUSTED_HOST": "True",
        "ENABLE_GLOBAL_EXCEPTION_HANDLER": "True",
        "SECURITY_HEADERS_CACHE_CONTROL": "public, max-age=31536000, immutable",
        "CONTENT_SECURITY_POLICY": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
        
        # Configurações de PDPJ
        "PDPJ_REQUEST_TIMEOUT": "30.0",
        "PDPJ_DOWNLOAD_TIMEOUT": "60.0",
        "PDPJ_MAX_RETRIES": "3",
        "PDPJ_RETRY_DELAY": "1.0",
        "PDPJ_MAX_CONNECTIONS": "10",
        "PDPJ_MAX_KEEPALIVE": "5",
        
        # Configurações de Ambiente
        "PROFILE": "development",
    }
    
    if not env_file.exists():
        print("❌ Arquivo .env não encontrado!")
        return False
    
    # Ler arquivo atual
    with open(env_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Verificar quais variáveis já existem
    existing_vars = set()
    for line in content.split('\n'):
        if '=' in line and not line.strip().startswith('#'):
            var_name = line.split('=')[0].strip()
            existing_vars.add(var_name)
    
    # Filtrar variáveis que não existem
    vars_to_add = {k: v for k, v in missing_vars.items() if k not in existing_vars}
    
    if not vars_to_add:
        print("✅ Todas as variáveis importantes já estão no .env!")
        return True
    
    # Adicionar variáveis faltantes
    print(f"📝 Adicionando {len(vars_to_add)} variáveis ao .env...")
    
    # Construir novo conteúdo
    new_content = content.rstrip() + "\n\n"
    
    # Adicionar por categoria
    categories = [
        ("Performance", ["MAX_CONCURRENT_REQUESTS", "MAX_CONCURRENT_DOWNLOADS", "CONNECTION_POOL_SIZE", "MAX_CONNECTIONS_PER_HOST", "REQUEST_TIMEOUT", "DOWNLOAD_TIMEOUT"]),
        ("Segurança", ["ENABLE_SECURITY_HEADERS", "ENABLE_RATE_LIMITING", "HSTS_MAX_AGE", "FRAME_OPTIONS", "XSS_PROTECTION", "REFERRER_POLICY", "PERMISSIONS_POLICY", "COEP_POLICY", "COOP_POLICY", "CORP_POLICY"]),
        ("API", ["API_PREFIX", "API_TITLE", "API_DESCRIPTION", "API_VERSION"]),
        ("Logging", ["LOG_FORMAT", "LOG_ROTATION_SIZE", "LOG_RETENTION_DAYS", "LOG_REQUEST_ID"]),
        ("Observabilidade", ["ENABLE_METRICS", "METRICS_PATH", "METRICS_PROTECTED", "METRICS_CACHE_TTL", "ENABLE_TRACING", "TRACING_SAMPLE_RATE", "TRACING_PROVIDER", "TRACING_SERVICE_NAME", "TRACING_SERVICE_VERSION"]),
        ("Performance HTTP", ["ENABLE_GZIP_COMPRESSION", "GZIP_MINIMUM_SIZE", "HTTP2_ENABLED", "TCP_NODELAY", "TCP_KEEPALIVE", "KEEPALIVE_TIMEOUT"]),
        ("Workers", ["UVICORN_WORKERS", "CELERY_WORKERS"]),
        ("Redis", ["REDIS_MAX_CONNECTIONS", "REDIS_RETRY_ON_TIMEOUT", "REDIS_SOCKET_KEEPALIVE", "REDIS_SOCKET_KEEPALIVE_OPTIONS"]),
        ("Bulk Operations", ["BULK_BATCH_SIZE", "BULK_INSERT_CHUNK_SIZE"]),
        ("CORS", ["CORS_ORIGINS", "CORS_ALLOW_CREDENTIALS", "CORS_ALLOW_METHODS", "CORS_ALLOW_HEADERS"]),
        ("Health Check", ["HEALTH_CHECK_INCLUDE_VERSION", "HEALTH_CHECK_INCLUDE_TIMESTAMP"]),
        ("Cache", ["CACHE_CRITICAL"]),
        ("Segurança Avançada", ["ENABLE_TRUSTED_HOST", "ENABLE_GLOBAL_EXCEPTION_HANDLER", "SECURITY_HEADERS_CACHE_CONTROL", "CONTENT_SECURITY_POLICY"]),
        ("PDPJ", ["PDPJ_REQUEST_TIMEOUT", "PDPJ_DOWNLOAD_TIMEOUT", "PDPJ_MAX_RETRIES", "PDPJ_RETRY_DELAY", "PDPJ_MAX_CONNECTIONS", "PDPJ_MAX_KEEPALIVE"]),
        ("Ambiente", ["PROFILE"])
    ]
    
    for category, var_names in categories:
        category_vars = {k: v for k, v in vars_to_add.items() if k in var_names}
        if category_vars:
            new_content += f"\n# Configurações de {category}\n"
            for var_name, var_value in category_vars.items():
                new_content += f"{var_name}={var_value}\n"
    
    # Escrever arquivo atualizado
    with open(env_file, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"✅ Adicionadas {len(vars_to_add)} variáveis ao .env:")
    for var_name in sorted(vars_to_add.keys()):
        print(f"   • {var_name}")
    
    return True

if __name__ == "__main__":
    print("🔧 ADICIONANDO VARIÁVEIS DE AMBIENTE FALTANTES")
    print("=" * 50)
    
    success = add_missing_env_vars()
    
    if success:
        print("\n🎉 SUCESSO! Variáveis adicionadas ao .env")
        print("💡 Execute 'python validate_environment_variables.py' para verificar")
    else:
        print("\n❌ ERRO! Não foi possível adicionar as variáveis")
        exit(1)
