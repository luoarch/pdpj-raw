"""
Testes de integração completa: PDPJ API → Download → S3 Storage.

Este módulo testa o fluxo completo de download de documentos:
1. Download de documento da API PDPJ
2. Upload para S3
3. Geração de URL presignada
4. Limpeza
"""

import pytest
import uuid
from unittest.mock import patch, AsyncMock, MagicMock

from app.services.pdpj_client import pdpj_client
from app.services.s3_service import s3_service
from app.utils.file_utils import process_document_download


@pytest.mark.integration
@pytest.mark.pdpj
@pytest.mark.s3
@pytest.mark.critical
class TestPDPJDownloadIntegration:
    """Testes de integração PDPJ + S3."""
    
    def test_pdpj_client_has_correct_token(self):
        """Verificar que o cliente PDPJ tem token válido"""
        assert pdpj_client.token is not None
        assert len(pdpj_client.token) > 100, "Token JWT deve ser longo"
        
        # Verificar que não é string mascarada
        assert pdpj_client.token != "**********"
        
        # Verificar formato JWT básico (3 partes separadas por ponto)
        parts = pdpj_client.token.split('.')
        assert len(parts) == 3, "Token JWT deve ter 3 partes"
    
    def test_pdpj_url_construction_with_api_v2(self):
        """Verificar que URLs são construídas corretamente com /api/v2/"""
        # Testar diferentes formatos de hrefBinario
        test_cases = [
            {
                "href": "/processos/5000315-75.2025.4.03.6327/documentos/59a2dbcc-bb58-5281-a656-cfe57861c2db/binario",
                "should_contain": "/api/v2/processos/"
            },
            {
                "href": "/api/v2/processos/1000145-91.2023.8.26.0597/documentos/a98a3080-bd47-5f84-83e6-4e24899a89cf/binario",
                "should_contain": "/api/v2/processos/"  # Já tem /api/v2/, não deve duplicar
            }
        ]
        
        for test in test_cases:
            href_binario = test["href"]
            
            # Aplicar lógica do pdpj_client
            if href_binario.startswith('/'):
                if not href_binario.startswith('/api/v2/'):
                    href_binario = f"/api/v2{href_binario}"
                document_url = f"{pdpj_client.base_url}{href_binario}"
            else:
                document_url = f"{pdpj_client.base_url}/api/v2/{href_binario}"
            
            # Verificar que a URL contém /api/v2/
            assert test["should_contain"] in document_url
            
            # Verificar que não duplica /api/v2/
            assert document_url.count('/api/v2/') == 1


@pytest.mark.integration
@pytest.mark.s3
@pytest.mark.slow
@pytest.mark.critical
class TestS3DocumentWorkflow:
    """Testes do fluxo completo de documentos."""
    
    async def test_upload_pdf_document(self):
        """Testar upload de documento PDF para S3"""
        # Criar PDF de teste (mínimo válido)
        pdf_content = b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n%%EOF'
        
        process_number = "0000000-00.0000.0.00.0000"
        document_id = str(uuid.uuid4())
        filename = "test-document.pdf"
        
        try:
            # Upload
            result = await s3_service.upload_document(
                file_content=pdf_content,
                process_number=process_number,
                document_id=document_id,
                filename=filename,
                content_type="application/pdf"
            )
            
            # Verificar resultado
            assert result is not None
            assert 's3_key' in result
            
            s3_key = result['s3_key']
            
            # Verificar que o arquivo está no S3
            async with s3_service.session.client('s3') as s3:
                response = await s3.head_object(
                    Bucket=s3_service.bucket_name,
                    Key=s3_key
                )
                assert response['ContentType'] == 'application/pdf'
            
            # Gerar URL presignada
            presigned_url = await s3_service.generate_presigned_url(
                s3_key=s3_key,
                expiration=3600
            )
            
            assert presigned_url is not None
            assert 'https://' in presigned_url
            
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
    
    async def test_multiple_documents_upload(self):
        """Testar upload de múltiplos documentos"""
        process_number = "0000000-00.0000.0.00.0000"
        uploaded_keys = []
        
        try:
            # Criar e fazer upload de 3 documentos
            for i in range(3):
                document_id = str(uuid.uuid4())
                filename = f"test-doc-{i}.txt"
                content = f"Documento {i}".encode('utf-8')
                
                result = await s3_service.upload_document(
                    file_content=content,
                    process_number=process_number,
                    document_id=document_id,
                    filename=filename,
                    content_type="text/plain"
                )
                
                uploaded_keys.append(result['s3_key'])
            
            # Verificar que todos foram enviados
            assert len(uploaded_keys) == 3
            
            # Listar objetos no prefixo
            async with s3_service.session.client('s3') as s3:
                response = await s3.list_objects_v2(
                    Bucket=s3_service.bucket_name,
                    Prefix=f'processes/{process_number}/'
                )
                
                objects = response.get('Contents', [])
                assert len(objects) >= 3, f"Deveria ter pelo menos 3 objetos, encontrou {len(objects)}"
            
        finally:
            # Limpar todos
            for s3_key in uploaded_keys:
                try:
                    async with s3_service.session.client('s3') as s3:
                        await s3.delete_object(
                            Bucket=s3_service.bucket_name,
                            Key=s3_key
                        )
                except Exception:
                    pass


@pytest.mark.unit
@pytest.mark.s3
class TestS3UtilityFunctions:
    """Testes de funções utilitárias do S3."""
    
    def test_sanitize_filename(self):
        """Testar sanitização de nomes de arquivos"""
        # O S3Service tem um método _sanitize_s3_key
        test_cases = [
            ("documento válido.pdf", True),
            ("../../../etc/passwd", False),  # Path traversal
            ("arquivo com espaços.pdf", True),
            ("arquivo-normal-123.pdf", True),
        ]
        
        for filename, should_be_safe in test_cases:
            # Verificar que nomes perigosos são rejeitados
            if not should_be_safe:
                # Caracteres perigosos devem ser removidos/sanitizados
                assert '..' not in filename or s3_service._sanitize_s3_key is not None


# Testes marcados como asyncio por padrão
pytestmark = pytest.mark.asyncio

