#!/usr/bin/env python3
"""
Script de diagnóstico completo para testar conectividade com AWS S3
"""

import os
import sys
import asyncio
from pathlib import Path
from loguru import logger
from dotenv import load_dotenv

# Configurar logging
logger.remove()
logger.add(sys.stdout, format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>")
logger.add("test_s3_connectivity.log", rotation="1 MB")

async def test_env_variables():
    """Teste 1: Verificar se as variáveis de ambiente estão configuradas"""
    logger.info("=" * 80)
    logger.info("TESTE 1: Verificando variáveis de ambiente no .env")
    logger.info("=" * 80)
    
    # Carregar .env explicitamente
    env_path = Path(".env")
    if env_path.exists():
        logger.info(f"✅ Arquivo .env encontrado: {env_path.absolute()}")
        load_dotenv(override=True)
    else:
        logger.error(f"❌ Arquivo .env NÃO encontrado em: {env_path.absolute()}")
        return False
    
    # Variáveis necessárias
    required_vars = {
        "AWS_ACCESS_KEY_ID": "Chave de acesso AWS",
        "AWS_SECRET_ACCESS_KEY": "Chave secreta AWS",
        "AWS_REGION": "Região AWS",
        "S3_BUCKET_NAME": "Nome do bucket S3"
    }
    
    all_present = True
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            # Mascarar valores sensíveis
            if "SECRET" in var or "KEY" in var:
                masked = f"{value[:8]}...{value[-4:]}" if len(value) > 12 else "***"
                logger.info(f"✅ {var}: {masked} ({len(value)} caracteres)")
            else:
                logger.info(f"✅ {var}: {value}")
        else:
            logger.error(f"❌ {var} NÃO está definida! ({description})")
            all_present = False
    
    if all_present:
        logger.success("\n✅ Todas as variáveis de ambiente necessárias estão presentes!\n")
        return True
    else:
        logger.error("\n❌ Algumas variáveis de ambiente estão faltando!\n")
        return False

async def test_settings_import():
    """Teste 2: Verificar se as configurações estão sendo importadas corretamente"""
    logger.info("=" * 80)
    logger.info("TESTE 2: Verificando importação das configurações")
    logger.info("=" * 80)
    
    try:
        from app.core.config import settings
        
        logger.info("✅ Módulo settings importado com sucesso")
        
        # Verificar se as credenciais foram carregadas
        aws_access_key = settings.aws_access_key_id.get_secret_value()
        aws_secret_key = settings.aws_secret_access_key.get_secret_value()
        region = settings.aws_region
        bucket = settings.s3_bucket_name
        
        logger.info(f"✅ AWS Access Key ID: {aws_access_key[:8]}...{aws_access_key[-4:]} ({len(aws_access_key)} chars)")
        logger.info(f"✅ AWS Secret Key: {aws_secret_key[:8]}...{aws_secret_key[-4:]} ({len(aws_secret_key)} chars)")
        logger.info(f"✅ AWS Region: {region}")
        logger.info(f"✅ S3 Bucket: {bucket}")
        
        logger.success("\n✅ Configurações carregadas corretamente!\n")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro ao importar configurações: {e}")
        logger.exception("Detalhes do erro:")
        return False

async def test_s3_service_init():
    """Teste 3: Verificar se o S3Service inicializa corretamente"""
    logger.info("=" * 80)
    logger.info("TESTE 3: Verificando inicialização do S3Service")
    logger.info("=" * 80)
    
    try:
        from app.services.s3_service import s3_service
        
        logger.info("✅ S3Service importado com sucesso")
        logger.info(f"✅ Bucket configurado: {s3_service.bucket_name}")
        logger.info(f"✅ Região configurada: {s3_service.region}")
        logger.info(f"✅ Access Key ID: {str(s3_service.access_key_id)[:8]}...")
        
        logger.success("\n✅ S3Service inicializado corretamente!\n")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro ao inicializar S3Service: {e}")
        logger.exception("Detalhes do erro:")
        return False

async def test_s3_connection():
    """Teste 4: Verificar conectividade real com AWS S3"""
    logger.info("=" * 80)
    logger.info("TESTE 4: Testando conectividade com AWS S3")
    logger.info("=" * 80)
    
    try:
        import aioboto3
        from app.core.config import settings
        
        # Criar sessão
        session = aioboto3.Session(
            aws_access_key_id=settings.aws_access_key_id.get_secret_value(),
            aws_secret_access_key=settings.aws_secret_access_key.get_secret_value(),
            region_name=settings.aws_region
        )
        
        logger.info("📡 Tentando conectar ao AWS S3...")
        
        # Testar listagem de buckets
        async with session.client('s3') as s3:
            logger.info("🔍 Listando buckets disponíveis...")
            response = await s3.list_buckets()
            
            buckets = response.get('Buckets', [])
            logger.success(f"✅ Conectado com sucesso! Encontrados {len(buckets)} buckets:")
            
            for bucket in buckets:
                bucket_name = bucket['Name']
                creation_date = bucket['CreationDate'].strftime("%Y-%m-%d %H:%M:%S")
                
                if bucket_name == settings.s3_bucket_name:
                    logger.success(f"  🎯 {bucket_name} (criado em {creation_date}) ← Bucket configurado")
                else:
                    logger.info(f"  📦 {bucket_name} (criado em {creation_date})")
        
        logger.success("\n✅ Conectividade com AWS S3 verificada!\n")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro ao conectar com AWS S3: {e}")
        logger.exception("Detalhes do erro:")
        
        # Sugestões de troubleshooting
        logger.warning("\n💡 Possíveis causas:")
        logger.warning("  1. Credenciais AWS incorretas ou expiradas")
        logger.warning("  2. Região AWS incorreta")
        logger.warning("  3. Permissões IAM insuficientes")
        logger.warning("  4. Problemas de conectividade de rede")
        logger.warning("  5. Firewall bloqueando acesso à AWS")
        
        return False

async def test_bucket_exists():
    """Teste 5: Verificar se o bucket configurado existe e está acessível"""
    logger.info("=" * 80)
    logger.info("TESTE 5: Verificando bucket configurado")
    logger.info("=" * 80)
    
    try:
        from app.services.s3_service import s3_service
        
        bucket_name = s3_service.bucket_name
        logger.info(f"🔍 Verificando bucket: {bucket_name}")
        
        exists = await s3_service.bucket_exists()
        
        if exists:
            logger.success(f"✅ Bucket '{bucket_name}' existe e está acessível!")
            
            # Obter informações adicionais do bucket
            async with s3_service.session.client('s3') as s3:
                try:
                    # Obter região do bucket
                    location = await s3.get_bucket_location(Bucket=bucket_name)
                    region = location.get('LocationConstraint') or 'us-east-1'
                    logger.info(f"📍 Região do bucket: {region}")
                    
                    # Verificar ACL (permissões)
                    acl = await s3.get_bucket_acl(Bucket=bucket_name)
                    owner = acl.get('Owner', {}).get('DisplayName', 'N/A')
                    logger.info(f"👤 Proprietário: {owner}")
                    
                except Exception as e:
                    logger.warning(f"⚠️ Não foi possível obter informações adicionais: {e}")
            
            logger.success("\n✅ Bucket verificado com sucesso!\n")
            return True
        else:
            logger.error(f"❌ Bucket '{bucket_name}' NÃO existe ou não está acessível!")
            logger.warning("\n💡 Ações sugeridas:")
            logger.warning(f"  1. Criar o bucket '{bucket_name}' no console AWS")
            logger.warning(f"  2. Verificar se o nome está correto no .env")
            logger.warning(f"  3. Verificar permissões IAM para acessar o bucket")
            return False
            
    except Exception as e:
        logger.error(f"❌ Erro ao verificar bucket: {e}")
        logger.exception("Detalhes do erro:")
        return False

async def test_s3_operations():
    """Teste 6: Testar operações básicas de upload e download"""
    logger.info("=" * 80)
    logger.info("TESTE 6: Testando operações básicas (upload/download)")
    logger.info("=" * 80)
    
    try:
        from app.services.s3_service import s3_service
        import uuid
        
        # Gerar nome único para o teste
        test_id = str(uuid.uuid4())[:8]
        test_key = f"test/connectivity-test-{test_id}.txt"
        test_content = f"Teste de conectividade S3 - {test_id}".encode('utf-8')
        
        logger.info(f"📤 Tentando upload de arquivo de teste: {test_key}")
        
        # Upload de teste
        async with s3_service.session.client('s3') as s3:
            await s3.put_object(
                Bucket=s3_service.bucket_name,
                Key=test_key,
                Body=test_content,
                ContentType='text/plain'
            )
        
        logger.success(f"✅ Upload bem-sucedido!")
        
        # Download de teste
        logger.info(f"📥 Tentando download do arquivo de teste...")
        
        async with s3_service.session.client('s3') as s3:
            response = await s3.get_object(
                Bucket=s3_service.bucket_name,
                Key=test_key
            )
            downloaded_content = await response['Body'].read()
        
        if downloaded_content == test_content:
            logger.success(f"✅ Download bem-sucedido! Conteúdo corresponde.")
        else:
            logger.error(f"❌ Conteúdo baixado não corresponde ao original!")
            return False
        
        # Limpar arquivo de teste
        logger.info(f"🧹 Removendo arquivo de teste...")
        
        async with s3_service.session.client('s3') as s3:
            await s3.delete_object(
                Bucket=s3_service.bucket_name,
                Key=test_key
            )
        
        logger.success(f"✅ Arquivo de teste removido com sucesso!")
        
        logger.success("\n✅ Todas as operações S3 funcionando corretamente!\n")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro ao testar operações S3: {e}")
        logger.exception("Detalhes do erro:")
        return False

async def test_s3_health():
    """Teste 7: Executar health check completo do S3Service"""
    logger.info("=" * 80)
    logger.info("TESTE 7: Health check do S3Service")
    logger.info("=" * 80)
    
    try:
        from app.services.s3_service import s3_service
        
        logger.info("🏥 Executando health check...")
        
        health = await s3_service.health_check()
        
        if health.get('status') == 'healthy':
            logger.success("✅ S3Service está saudável!")
            
            # Mostrar detalhes
            for key, value in health.items():
                if key != 'status':
                    logger.info(f"  {key}: {value}")
        else:
            logger.error("❌ S3Service reportou problemas:")
            logger.error(f"  Status: {health.get('status')}")
            logger.error(f"  Detalhes: {health.get('details', 'N/A')}")
            return False
        
        logger.success("\n✅ Health check passou!\n")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro no health check: {e}")
        logger.exception("Detalhes do erro:")
        return False

async def main():
    """Executar todos os testes"""
    logger.info("🚀 INICIANDO DIAGNÓSTICO DE CONECTIVIDADE AWS S3")
    logger.info("=" * 80)
    logger.info("")
    
    results = []
    
    # Teste 1: Variáveis de ambiente
    result1 = await test_env_variables()
    results.append(("Variáveis de ambiente", result1))
    
    if not result1:
        logger.error("❌ Não é possível continuar sem as variáveis de ambiente corretas.")
        logger.error("💡 Verifique seu arquivo .env e tente novamente.")
        return
    
    # Teste 2: Importação de configurações
    result2 = await test_settings_import()
    results.append(("Importação de configurações", result2))
    
    if not result2:
        logger.error("❌ Não é possível continuar sem carregar as configurações.")
        return
    
    # Teste 3: Inicialização do S3Service
    result3 = await test_s3_service_init()
    results.append(("Inicialização S3Service", result3))
    
    if not result3:
        logger.error("❌ Não é possível continuar sem inicializar o S3Service.")
        return
    
    # Teste 4: Conectividade S3
    result4 = await test_s3_connection()
    results.append(("Conectividade AWS S3", result4))
    
    if not result4:
        logger.error("❌ Não é possível continuar sem conectividade com AWS S3.")
        return
    
    # Teste 5: Verificação do bucket
    result5 = await test_bucket_exists()
    results.append(("Verificação do bucket", result5))
    
    if not result5:
        logger.warning("⚠️ Bucket não encontrado, mas continuando com os testes...")
    
    # Teste 6: Operações básicas
    if result5:  # Só testar se o bucket existe
        result6 = await test_s3_operations()
        results.append(("Operações básicas", result6))
    
    # Teste 7: Health check
    result7 = await test_s3_health()
    results.append(("Health check", result7))
    
    # Resumo final
    logger.info("\n" + "=" * 80)
    logger.info("📊 RESUMO DOS TESTES")
    logger.info("=" * 80)
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        symbol = "✅" if result else "❌"
        status = "PASSOU" if result else "FALHOU"
        logger.info(f"{symbol} {test_name}: {status}")
        
        if result:
            passed += 1
        else:
            failed += 1
    
    logger.info("")
    logger.info(f"Total: {passed} passaram, {failed} falharam")
    
    if failed == 0:
        logger.success("\n🎉 TODOS OS TESTES PASSARAM! S3 está configurado e funcionando corretamente!")
    else:
        logger.error(f"\n❌ {failed} teste(s) falharam. Verifique os logs acima para detalhes.")
    
    logger.info("\n🏁 Diagnóstico concluído")

if __name__ == "__main__":
    asyncio.run(main())

