#!/usr/bin/env python3
"""
Exemplo de uso da criptografia de campos sensíveis na configuração.

Este script demonstra como usar o sistema de criptografia integrado
para proteger credenciais e dados sensíveis.
"""

import os
import sys
from pathlib import Path

# Adicionar o diretório raiz ao path para importar a configuração
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import Settings


def exemplo_criptografia_basica():
    """Exemplo básico de criptografia de valores sensíveis."""
    print("=== Exemplo de Criptografia Básica ===")
    
    # Criar configuração com criptografia habilitada
    settings = Settings.create_with_overrides(
        enable_field_encryption=True,
        encryption_key="minha_chave_super_secreta_123",
        encryption_salt="salt_personalizado_pdpj",
        database_url="postgresql://user:senha123@localhost:5432/pdpj_db",
        aws_access_key_id="AKIAIOSFODNN7EXAMPLE",
        aws_secret_access_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
    )
    
    # Criptografar valores
    db_url_encrypted = settings.encrypt_sensitive_value(settings.database_url)
    aws_key_encrypted = settings.encrypt_sensitive_value("AKIAIOSFODNN7EXAMPLE")
    
    print(f"URL do banco (original): {settings.database_url}")
    print(f"URL do banco (criptografada): {db_url_encrypted}")
    print(f"AWS Key (original): AKIAIOSFODNN7EXAMPLE")
    print(f"AWS Key (criptografada): {aws_key_encrypted}")
    
    # Descriptografar valores
    db_url_decrypted = settings.decrypt_sensitive_value(db_url_encrypted)
    aws_key_decrypted = settings.decrypt_sensitive_value(aws_key_encrypted)
    
    print(f"URL do banco (descriptografada): {db_url_decrypted}")
    print(f"AWS Key (descriptografada): {aws_key_decrypted}")
    
    # Verificar se os valores são iguais
    print(f"URLs são iguais: {settings.database_url == db_url_decrypted}")
    print(f"AWS Keys são iguais: {'AKIAIOSFODNN7EXAMPLE' == aws_key_decrypted}")


def exemplo_metodos_seguros():
    """Exemplo de uso dos métodos seguros da configuração."""
    print("\n=== Exemplo de Métodos Seguros ===")
    
    settings = Settings.create_with_overrides(
        enable_field_encryption=True,
        encryption_key="outra_chave_secreta_456",
        database_url="postgresql://admin:senha_admin@prod-db:5432/pdpj_prod",
        redis_url="redis://redis-user:redis_pass@redis-prod:6379/0",
        pdpj_api_token="token_pdpj_super_secreto_12345"
    )
    
    # Usar métodos seguros
    safe_db_url = settings.get_safe_database_url()
    safe_redis_url = settings.get_safe_redis_url()
    safe_aws_creds = settings.get_safe_aws_credentials()
    safe_pdpj_token = settings.get_safe_pdpj_token()
    
    print(f"Database URL segura: {safe_db_url}")
    print(f"Redis URL segura: {safe_redis_url}")
    print(f"AWS credentials seguras: {safe_aws_creds}")
    print(f"PDPJ token seguro: {safe_pdpj_token}")
    
    # Descriptografar para verificar
    db_url_original = settings.decrypt_sensitive_value(safe_db_url)
    redis_url_original = settings.decrypt_sensitive_value(safe_redis_url)
    pdpj_token_original = settings.decrypt_sensitive_value(safe_pdpj_token)
    
    print(f"\nValores descriptografados:")
    print(f"Database URL: {db_url_original}")
    print(f"Redis URL: {redis_url_original}")
    print(f"PDPJ Token: {pdpj_token_original}")


def exemplo_arquivo_config_criptografado():
    """Exemplo de arquivo de configuração com valores criptografados."""
    print("\n=== Exemplo de Arquivo de Configuração Criptografado ===")
    
    # Configuração com criptografia
    settings = Settings.create_with_overrides(
        enable_field_encryption=True,
        encryption_key="chave_producao_super_secreta",
        encryption_salt="salt_producao_pdpj"
    )
    
    # Valores sensíveis para criptografar
    valores_sensiveis = {
        "database_url": "postgresql://prod_user:prod_password@prod-db.pdpj.gov.br:5432/pdpj_production",
        "redis_url": "redis://prod_redis:redis_password@prod-redis.pdpj.gov.br:6379/0",
        "aws_access_key_id": "AKIAIOSFODNN7PRODEXAMPLE",
        "aws_secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYPRODEXAMPLE",
        "pdpj_api_token": "token_pdpj_producao_super_secreto_789"
    }
    
    print("Valores criptografados para arquivo de configuração:")
    print("=" * 60)
    
    for chave, valor in valores_sensiveis.items():
        valor_criptografado = settings.encrypt_sensitive_value(valor)
        print(f"{chave.upper()}={valor_criptografado}")
    
    print("\nExemplo de arquivo .env.production.encrypted:")
    print("=" * 60)
    print("PROFILE=production")
    print("ENABLE_FIELD_ENCRYPTION=true")
    print("ENCRYPTION_KEY=sua_chave_super_secreta_aqui")
    print("ENCRYPTION_SALT=salt_producao_personalizado")
    print()
    
    for chave, valor in valores_sensiveis.items():
        valor_criptografado = settings.encrypt_sensitive_value(valor)
        print(f"{chave.upper()}={valor_criptografado}")


def exemplo_validacao_erro():
    """Exemplo de tratamento de erros na criptografia."""
    print("\n=== Exemplo de Tratamento de Erros ===")
    
    # Configuração sem criptografia
    settings_sem_criptografia = Settings.create_with_overrides(
        enable_field_encryption=False
    )
    
    # Tentar criptografar sem chave
    try:
        settings_sem_criptografia.encrypt_sensitive_value("teste")
        print("Criptografia funcionou (inesperado)")
    except ValueError as e:
        print(f"Erro esperado: {e}")
    
    # Configuração com criptografia
    settings_com_criptografia = Settings.create_with_overrides(
        enable_field_encryption=True,
        encryption_key="chave_teste"
    )
    
    # Tentar descriptografar valor inválido
    try:
        settings_com_criptografia.decrypt_sensitive_value("valor_invalido")
        print("Descriptografia funcionou (inesperado)")
    except ValueError as e:
        print(f"Erro esperado: {e}")


if __name__ == "__main__":
    print("Exemplos de Criptografia de Configurações PDPJ")
    print("=" * 50)
    
    try:
        exemplo_criptografia_basica()
        exemplo_metodos_seguros()
        exemplo_arquivo_config_criptografado()
        exemplo_validacao_erro()
        
        print("\n" + "=" * 50)
        print("Todos os exemplos executados com sucesso!")
        
    except Exception as e:
        print(f"\nErro durante execução: {e}")
        import traceback
        traceback.print_exc()
