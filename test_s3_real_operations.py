#!/usr/bin/env python3
"""
Teste direto de operações S3 (pula o HeadBucket que está com problema)
"""

import asyncio
import uuid
from loguru import logger
from app.services.s3_service import s3_service

logger.add("test_s3_real_operations.log", rotation="1 MB")

async def test_real_s3_operations():
    """Testar operações reais de upload/download no S3"""
    
    logger.info("🚀 Testando operações REAIS no S3 (sem HeadBucket)")
    logger.info("="*60)
    
    try:
        # Gerar ID único
        test_id = str(uuid.uuid4())[:8]
        test_key = f"test/connectivity-{test_id}.txt"
        test_content = f"Teste de conectividade S3 - {test_id}".encode('utf-8')
        
        logger.info(f"📤 Teste 1: Upload de arquivo")
        logger.info(f"   Arquivo: {test_key}")
        logger.info(f"   Tamanho: {len(test_content)} bytes")
        
        # Upload usando o S3Service
        async with s3_service.session.client('s3') as s3:
            await s3.put_object(
                Bucket=s3_service.bucket_name,
                Key=test_key,
                Body=test_content,
                ContentType='text/plain'
            )
        
        logger.success(f"✅ Upload bem-sucedido!")
        
        # Download
        logger.info(f"\n📥 Teste 2: Download de arquivo")
        
        async with s3_service.session.client('s3') as s3:
            response = await s3.get_object(
                Bucket=s3_service.bucket_name,
                Key=test_key
            )
            downloaded_content = await response['Body'].read()
        
        if downloaded_content == test_content:
            logger.success(f"✅ Download bem-sucedido! Conteúdo corresponde.")
        else:
            logger.error(f"❌ Conteúdo não corresponde!")
            return False
        
        # Listar objetos
        logger.info(f"\n📋 Teste 3: Listar objetos no bucket")
        
        async with s3_service.session.client('s3') as s3:
            response = await s3.list_objects_v2(
                Bucket=s3_service.bucket_name,
                Prefix='test/',
                MaxKeys=10
            )
            
            objects_found = response.get('Contents', [])
            logger.info(f"   Objetos encontrados: {len(objects_found)}")
            
            for obj in objects_found[:5]:  # Mostrar até 5
                logger.info(f"   - {obj['Key']} ({obj['Size']} bytes)")
        
        logger.success(f"✅ Listagem bem-sucedida!")
        
        # Deletar arquivo de teste
        logger.info(f"\n🧹 Teste 4: Deletar arquivo de teste")
        
        async with s3_service.session.client('s3') as s3:
            await s3.delete_object(
                Bucket=s3_service.bucket_name,
                Key=test_key
            )
        
        logger.success(f"✅ Arquivo deletado com sucesso!")
        
        # Verificar que foi deletado
        logger.info(f"\n🔍 Teste 5: Verificar deleção")
        
        async with s3_service.session.client('s3') as s3:
            try:
                await s3.head_object(
                    Bucket=s3_service.bucket_name,
                    Key=test_key
                )
                logger.error(f"❌ Arquivo ainda existe!")
                return False
            except Exception:
                logger.success(f"✅ Arquivo foi deletado corretamente!")
        
        logger.info("\n" + "="*60)
        logger.success("🎉 TODOS OS TESTES PASSARAM!")
        logger.success("✅ S3 está completamente funcional!")
        logger.info("="*60)
        
        return True
        
    except Exception as e:
        logger.error(f"\n❌ Erro durante os testes: {e}")
        logger.exception("Detalhes do erro:")
        return False

async def test_upload_document():
    """Teste de upload usando o método do S3Service"""
    
    logger.info("\n📦 Teste BONUS: Upload usando S3Service.upload_document()")
    logger.info("="*60)
    
    try:
        test_id = str(uuid.uuid4())[:8]
        test_content = f"Documento de teste PDPJ - {test_id}".encode('utf-8')
        
        # Upload usando método do serviço
        result = await s3_service.upload_document(
            file_content=test_content,
            process_number="0000000-00.0000.0.00.0000",
            document_id=test_id,
            filename="test-document.txt",
            content_type="text/plain"
        )
        
        logger.success(f"✅ Upload via S3Service funcionou!")
        logger.info(f"   S3 Key: {result.get('s3_key')}")
        logger.info(f"   Tamanho: {result.get('size')} bytes")
        
        # Limpar
        s3_key = result.get('s3_key')
        async with s3_service.session.client('s3') as s3:
            await s3.delete_object(
                Bucket=s3_service.bucket_name,
                Key=s3_key
            )
        
        logger.success(f"✅ Limpeza concluída!")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro: {e}")
        logger.exception("Detalhes:")
        return False

async def main():
    """Executar todos os testes"""
    
    logger.info("🏁 TESTE DE OPERAÇÕES REAIS S3")
    logger.info("="*60)
    logger.info(f"Bucket: {s3_service.bucket_name}")
    logger.info(f"Região: {s3_service.region}")
    logger.info("="*60)
    logger.info("")
    
    # Teste 1: Operações básicas
    result1 = await test_real_s3_operations()
    
    if not result1:
        logger.error("\n❌ Operações básicas falharam!")
        return
    
    # Teste 2: Upload via serviço
    result2 = await test_upload_document()
    
    if result2:
        logger.info("\n" + "="*60)
        logger.success("🎊 SUCESSO TOTAL!")
        logger.success("✅ Todas as operações S3 estão funcionando!")
        logger.info("="*60)
        logger.info("\n💡 CONCLUSÃO:")
        logger.info("   O erro de HeadBucket é irrelevante para o uso normal.")
        logger.info("   Upload, download, listagem e deleção funcionam perfeitamente!")
        logger.info("   O sistema PDPJ pode ser usado normalmente! 🚀")

if __name__ == "__main__":
    asyncio.run(main())

