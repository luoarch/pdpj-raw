"""
Testes oficiais para o serviço AWS S3.

Este módulo contém testes críticos para garantir que:
1. Credenciais AWS estão carregadas corretamente
2. Conectividade com S3 está funcionando
3. Operações de upload/download funcionam
4. URLs presignadas são geradas corretamente
"""

import pytest
import uuid
from pathlib import Path

from app.core.config import settings
from app.services.s3_service import s3_service, S3ServiceError


@pytest.mark.integration
@pytest.mark.s3
@pytest.mark.critical
class TestS3Configuration:
    """Testes de configuração do S3."""
    
    def test_aws_credentials_loaded(self):
        """Verificar se as credenciais AWS foram carregadas do .env"""
        # Verificar que as credenciais existem
        assert settings.aws_access_key_id is not None
        assert settings.aws_secret_access_key is not None
        assert settings.aws_region is not None
        assert settings.s3_bucket_name is not None
        
        # Verificar que podemos extrair os valores
        access_key = settings.aws_access_key_id.get_secret_value()
        secret_key = settings.aws_secret_access_key.get_secret_value()
        
        # Verificar formato básico
        assert len(access_key) == 20, "AWS Access Key deve ter 20 caracteres"
        assert len(secret_key) == 40, "AWS Secret Key deve ter 40 caracteres"
        assert access_key.startswith("AKIA"), "AWS Access Key deve começar com AKIA"
    
    def test_s3_service_initialization(self):
        """Verificar se o S3Service inicializa corretamente"""
        assert s3_service is not None
        assert s3_service.bucket_name == settings.s3_bucket_name
        assert s3_service.region == settings.aws_region
        
        # Verificar que as credenciais foram extraídas corretamente
        assert s3_service.access_key_id is not None
        assert s3_service.secret_access_key is not None
        assert len(s3_service.access_key_id) == 20
        assert len(s3_service.secret_access_key) == 40
        
        # Verificar que não são strings mascaradas
        assert s3_service.access_key_id != "**********"
        assert s3_service.secret_access_key != "**********"


@pytest.mark.integration
@pytest.mark.s3
@pytest.mark.slow
@pytest.mark.critical
class TestS3Connectivity:
    """Testes de conectividade com AWS S3."""
    
    async def test_s3_connection(self):
        """Verificar conectividade básica com AWS S3"""
        # Tentar listar buckets
        async with s3_service.session.client('s3') as s3:
            response = await s3.list_buckets()
            buckets = response.get('Buckets', [])
            
            # Deve retornar lista de buckets
            assert len(buckets) > 0, "Deve haver pelo menos 1 bucket"
            
            # Verificar se o bucket configurado existe
            bucket_names = [b['Name'] for b in buckets]
            assert s3_service.bucket_name in bucket_names, f"Bucket {s3_service.bucket_name} não encontrado"
    
    async def test_bucket_region(self):
        """Verificar região do bucket"""
        async with s3_service.session.client('s3') as s3:
            location = await s3.get_bucket_location(Bucket=s3_service.bucket_name)
            region = location.get('LocationConstraint') or 'us-east-1'
            
            assert region == s3_service.region, f"Região do bucket ({region}) não corresponde à configurada ({s3_service.region})"


@pytest.mark.integration
@pytest.mark.s3
@pytest.mark.slow
@pytest.mark.critical
class TestS3Operations:
    """Testes de operações S3 (upload, download, delete)."""
    
    async def test_upload_download_cycle(self):
        """Testar ciclo completo: upload → download → verificação → delete"""
        # Gerar dados de teste únicos
        test_id = str(uuid.uuid4())[:8]
        test_key = f"tests/integration/test-{test_id}.txt"
        test_content = f"Teste de integração S3 - {test_id}".encode('utf-8')
        
        try:
            # 1. Upload
            async with s3_service.session.client('s3') as s3:
                await s3.put_object(
                    Bucket=s3_service.bucket_name,
                    Key=test_key,
                    Body=test_content,
                    ContentType='text/plain'
                )
            
            # 2. Download
            async with s3_service.session.client('s3') as s3:
                response = await s3.get_object(
                    Bucket=s3_service.bucket_name,
                    Key=test_key
                )
                downloaded_content = await response['Body'].read()
            
            # 3. Verificar conteúdo
            assert downloaded_content == test_content, "Conteúdo baixado não corresponde ao enviado"
            
            # 4. Verificar metadados
            async with s3_service.session.client('s3') as s3:
                response = await s3.head_object(
                    Bucket=s3_service.bucket_name,
                    Key=test_key
                )
                assert response['ContentType'] == 'text/plain'
                assert response['ContentLength'] == len(test_content)
            
        finally:
            # 5. Limpar (sempre executar)
            try:
                async with s3_service.session.client('s3') as s3:
                    await s3.delete_object(
                        Bucket=s3_service.bucket_name,
                        Key=test_key
                    )
            except Exception:
                pass  # Ignorar erros na limpeza
    
    async def test_upload_document_method(self):
        """Testar método upload_document() do S3Service"""
        test_id = str(uuid.uuid4())[:8]
        test_content = f"Documento de teste PDPJ - {test_id}".encode('utf-8')
        
        process_number = "0000000-00.0000.0.00.0000"
        document_id = test_id
        filename = "test-document.txt"
        
        try:
            # Upload usando método do serviço
            result = await s3_service.upload_document(
                file_content=test_content,
                process_number=process_number,
                document_id=document_id,
                filename=filename,
                content_type="text/plain"
            )
            
            # Verificar resultado
            assert result is not None
            assert 's3_key' in result
            assert 'size' in result or 'file_size' in result
            
            s3_key = result['s3_key']
            
            # Verificar que o arquivo foi enviado
            async with s3_service.session.client('s3') as s3:
                response = await s3.head_object(
                    Bucket=s3_service.bucket_name,
                    Key=s3_key
                )
                assert response['ContentLength'] == len(test_content)
            
        finally:
            # Limpar
            try:
                s3_key = f"processes/{process_number}/documents/{document_id}/{filename}"
                async with s3_service.session.client('s3') as s3:
                    await s3.delete_object(
                        Bucket=s3_service.bucket_name,
                        Key=s3_key
                    )
            except Exception:
                pass
    
    async def test_list_objects(self):
        """Testar listagem de objetos no bucket"""
        # Criar arquivo de teste
        test_id = str(uuid.uuid4())[:8]
        test_key = f"tests/list-test-{test_id}.txt"
        test_content = b"test"
        
        try:
            # Upload
            async with s3_service.session.client('s3') as s3:
                await s3.put_object(
                    Bucket=s3_service.bucket_name,
                    Key=test_key,
                    Body=test_content
                )
            
            # Listar objetos com prefixo
            async with s3_service.session.client('s3') as s3:
                response = await s3.list_objects_v2(
                    Bucket=s3_service.bucket_name,
                    Prefix='tests/',
                    MaxKeys=100
                )
            
            # Verificar que encontrou objetos
            objects = response.get('Contents', [])
            assert len(objects) > 0, "Deve encontrar pelo menos 1 objeto"
            
            # Verificar que nosso arquivo está na lista
            keys = [obj['Key'] for obj in objects]
            assert test_key in keys, f"Arquivo {test_key} não encontrado na listagem"
            
        finally:
            # Limpar
            try:
                async with s3_service.session.client('s3') as s3:
                    await s3.delete_object(
                        Bucket=s3_service.bucket_name,
                        Key=test_key
                    )
            except Exception:
                pass
    
    async def test_generate_presigned_url(self):
        """Testar geração de URLs presignadas"""
        # Criar arquivo de teste
        test_id = str(uuid.uuid4())[:8]
        test_key = f"tests/presigned-test-{test_id}.txt"
        test_content = b"presigned test"
        
        try:
            # Upload
            async with s3_service.session.client('s3') as s3:
                await s3.put_object(
                    Bucket=s3_service.bucket_name,
                    Key=test_key,
                    Body=test_content
                )
            
            # Gerar URL presignada
            presigned_url = await s3_service.generate_presigned_url(
                s3_key=test_key,
                expiration=3600
            )
            
            # Verificar formato da URL
            assert presigned_url is not None
            assert presigned_url.startswith('https://')
            assert s3_service.bucket_name in presigned_url
            assert test_key in presigned_url
            # Verificar que tem parâmetros de assinatura (pode ser X-Amz-Algorithm ou AWSAccessKeyId)
            assert 'X-Amz-Algorithm' in presigned_url or 'AWSAccessKeyId' in presigned_url
            assert 'Signature' in presigned_url or 'X-Amz-Credential' in presigned_url
            
        finally:
            # Limpar
            try:
                async with s3_service.session.client('s3') as s3:
                    await s3.delete_object(
                        Bucket=s3_service.bucket_name,
                        Key=test_key
                    )
            except Exception:
                pass
    
    async def test_delete_nonexistent_object(self):
        """Testar deleção de objeto que não existe (deve ser bem-sucedida)"""
        # S3 não retorna erro ao deletar objeto inexistente
        test_key = f"tests/nonexistent-{uuid.uuid4()}.txt"
        
        # Não deve lançar exceção
        async with s3_service.session.client('s3') as s3:
            await s3.delete_object(
                Bucket=s3_service.bucket_name,
                Key=test_key
            )


@pytest.mark.integration
@pytest.mark.s3
@pytest.mark.critical
class TestS3Health:
    """Testes de health check do S3."""
    
    async def test_health_check(self):
        """Verificar que health check retorna status correto"""
        health = await s3_service.health_check()
        
        assert health is not None
        assert 'status' in health
        assert health['status'] == 'healthy', f"S3 não está saudável: {health}"
        assert 'bucket' in health
        assert 'region' in health
        assert health['bucket'] == s3_service.bucket_name
        assert health['region'] == s3_service.region


@pytest.mark.integration
@pytest.mark.s3
class TestS3ErrorHandling:
    """Testes de tratamento de erros."""
    
    async def test_download_nonexistent_object(self):
        """Testar download de objeto inexistente"""
        test_key = f"tests/nonexistent-{uuid.uuid4()}.txt"
        
        with pytest.raises(Exception):  # Deve lançar exceção
            async with s3_service.session.client('s3') as s3:
                response = await s3.get_object(
                    Bucket=s3_service.bucket_name,
                    Key=test_key
                )
                await response['Body'].read()
    
    async def test_upload_to_invalid_bucket(self):
        """Testar upload para bucket inexistente"""
        test_content = b"test"
        invalid_bucket = f"bucket-that-does-not-exist-{uuid.uuid4()}"
        
        with pytest.raises(Exception):  # Deve lançar exceção
            async with s3_service.session.client('s3') as s3:
                await s3.put_object(
                    Bucket=invalid_bucket,
                    Key="test.txt",
                    Body=test_content
                )


# Testes marcados como asyncio por padrão
pytestmark = pytest.mark.asyncio

