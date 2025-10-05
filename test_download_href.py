#!/usr/bin/env python3
"""
Script de teste para download de documentos usando hrefBinario
"""

import asyncio
import httpx
import os
from loguru import logger

# Configurar logging
logger.add("test_download.log", rotation="1 MB")

async def test_download_href():
    """Testar download usando hrefBinario"""
    
    # Token PDPJ (mesmo usado anteriormente)
    token = "eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICI1dnJEZ1hCS21FLTdFb3J2a0U1TXU5VmxJZF9JU2dsMnY3QWYyM25EdkRVIn0.eyJleHAiOjE3NTk2MjYzNDMsImlhdCI6MTc1OTYxMTA0OSwiYXV0aF90aW1lIjoxNzU5NTgzMTQzLCJqdGkiOiJiM2IzZGYxMC1mNjZmLTQzMmUtODAyZi0yNDk3MDU5NGEzZTEiLCJpc3MiOiJodHRwczovL3Nzby5jbG91ZC5wamUuanVzLmJyL2F1dGgvcmVhbG1zL3BqZSIsImF1ZCI6WyJicm9rZXIiLCJhY2NvdW50Il0sInN1YiI6IjUwM2Y5ZTc3LWIzY2EtNGE2NC05MjA0LTBmMDJmNjdhZTZhOCIsInR5cCI6IkJlYXJlciIsImF6cCI6InBvcnRhbGV4dGVybm8tZnJvbnRlbmQiLCJub25jZSI6ImE2YTI5NDlmLTVkMTUtNDRjZC04YTEzLWViMWE1NzhhMjMwOCIsInNlc3Npb25fc3RhdGUiOiI0NmFmMzFjZS1iYzljLTQ5ZDQtODFjYS0xMjA2NTdkNzYyMzciLCJhY3IiOiIwIiwiYWxsb3dlZC1vcmlnaW5zIjpbImh0dHBzOi8vcG9ydGFsZGVzZXJ2aWNvcy5wZHBqLmp1cy5iciJdLCJyZWFsbV9hY2Nlc3MiOnsicm9sZXMiOlsib2ZmbGluZV9hY2Nlc3MiLCJ1bWFfYXV0aG9yaXphdGlvbiJdfSwicmVzb3VyY2VfYWNjZXNzIjp7ImJyb2tlciI6eyJyb2xlcyI6WyJyZWFkLXRva2VuIl19LCJhY2NvdW50Ijp7InJvbGVzIjpbIm1hbmFnZS1hY2NvdW50IiwibWFuYWdlLWFjY291bnQtbGlua3MiLCJ2aWV3LXByb2ZpbGUiXX19LCJzY29wZSI6Im9wZW5pZCBwcm9maWxlIGVtYWlsIiwic2lkIjoiNDZhZjMxY2UtYmM5Yy00OWQ0LTgxY2EtMTIwNjU3ZDc2MjM3IiwiQWNlc3NhUmVwb3NpdG9yaW8iOiJPayIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJuYW1lIjoiRlJBTkNJU0NPIEJSVU5PIE5PQlJFIERFIE1FTE8iLCJwcmVmZXJyZWRfdXNlcm5hbWUiOiIwNjMzMzE0NTM2MCIsImdpdmVuX25hbWUiOiJGUkFOQ0lTQ08gQlJVTk8gTk9CUkUgREUgTUVMTyIsImNvcnBvcmF0aXZvIjpbeyJzZXFfdXN1YXJpbyI6MTY1MDIzNjcsIm5vbV91c3VhcmlvIjoiRlJBTkNJU0NPIEJSVU5PIE5PQlJFIERFIE1FTE8iLCJudW1fY3BmIjoiMDYzMzMxNDUzNjAiLCJzaWdfdGlwb19jYXJnbyI6IkFEViIsImZsZ19hdGl2byI6IlMiLCJzZXFfc2lzdGVtYSI6MCwic2VxX3BlcmZpbCI6MCwiZHNjX29yZ2FvIjoiT0FCIiwic2VxX3RyaWJ1bmFsX3BhaSI6MCwiZHNjX2VtYWlsIjoibWVsb2ZhY2RpcmVpdG9AaG90bWFpbC5jb20iLCJzZXFfb3JnYW9fZXh0ZXJubyI6MCwiZHNjX29yZ2FvX2V4dGVybm8iOiJPQUIiLCJvYWIiOiJDRTQ0Njc0In1dLCJlbWFpbCI6Im1lbG9mYWNkaXJlaXRvQGhvdG1haWwuY29tIn0.QjvsSE_I7Ih5UtmFt2r5kdP6MLfSsQHCXYqdtVkHFKVcRm2A27kNVGn7BIKT9QYtoI_0Vwl9cH7CjSOoB3zLWn24iTnNmVkxASS1vr40owbm2coVYXyJ646csChh3eFK_7TRZgVP-4u_0_lJ1VVtGCvZmlALTGZu9xd4Lk06B5Az7mlucZ0kxW4_x4eaHPKc3jjf5mXybxPRkkBtGREZ1EtcWFdpA84QSHYDEy9_8TV32N1E_3rQXXyPbyjQ6eR-4RRc6SDwzgykoXR6oo_hy47DzMnx6-C4MW2er7EWc1XHpyl4Sngy3ZJN3-9VIgktS-sY9-Xzugp3bzxiZL7OHQ"
    
    # Base URL da API PDPJ
    base_url = "https://portaldeservicos.pdpj.jus.br"
    
    # hrefBinario de um documento específico (peguei da saída do terminal)
    href_binario = "/processos/1000145-91.2023.8.26.0597/documentos/a98a3080-bd47-5f84-83e6-4e24899a89cf/binario"
    
    # Construir URL completa
    if href_binario.startswith('/'):
        document_url = f"{base_url}{href_binario}"
    else:
        document_url = f"{base_url}/{href_binario}"
    
    logger.info(f"🔧 Testando download com hrefBinario")
    logger.info(f"🔧 URL completa: {document_url}")
    logger.info(f"🔧 Token: {token[:50]}...")
    
    # Headers para a requisição
    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": "PDPJ-API-Client/1.0",
        "Accept": "application/octet-stream, application/pdf, */*"
    }
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            logger.info(f"⬇️ Iniciando download...")
            
            response = await client.get(
                document_url,
                headers=headers
            )
            
            logger.info(f"📊 Status Code: {response.status_code}")
            logger.info(f"📊 Headers da resposta: {dict(response.headers)}")
            
            if response.status_code == 200:
                content = response.content
                logger.info(f"✅ Download bem-sucedido!")
                logger.info(f"📁 Tamanho do arquivo: {len(content)} bytes")
                logger.info(f"📁 Content-Type: {response.headers.get('content-type', 'N/A')}")
                
                # Salvar arquivo para verificação
                filename = "test_document.pdf"
                with open(filename, "wb") as f:
                    f.write(content)
                
                logger.info(f"💾 Arquivo salvo como: {filename}")
                
                # Verificar se é um PDF válido
                if content.startswith(b'%PDF'):
                    logger.info("✅ Arquivo é um PDF válido!")
                else:
                    logger.warning("⚠️ Arquivo não parece ser um PDF válido")
                    logger.info(f"🔍 Primeiros 100 bytes: {content[:100]}")
                
                return True
                
            else:
                logger.error(f"❌ Erro no download: HTTP {response.status_code}")
                logger.error(f"❌ Resposta: {response.text}")
                return False
                
    except Exception as e:
        logger.error(f"❌ Erro durante o download: {e}")
        return False

async def test_multiple_documents():
    """Testar download de múltiplos documentos"""
    
    # Lista de hrefBinario para testar
    href_list = [
        "/processos/1000145-91.2023.8.26.0597/documentos/a98a3080-bd47-5f84-83e6-4e24899a89cf/binario",
        "/processos/1000145-91.2023.8.26.0597/documentos/f6ef169c-3fb3-5977-8f84-363cbef0f82d/binario",
        "/processos/1000145-91.2023.8.26.0597/documentos/e0512bb3-71f9-52ce-8d8a-1503930825b1/binario"
    ]
    
    token = "eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICI1dnJEZ1hCS21FLTdFb3J2a0U1TXU5VmxJZF9JU2dsMnY3QWYyM25EdkRVIn0.eyJleHAiOjE3NTk2MjYzNDMsImlhdCI6MTc1OTYxMTA0OSwiYXV0aF90aW1lIjoxNzU5NTgzMTQzLCJqdGkiOiJiM2IzZGYxMC1mNjZmLTQzMmUtODAyZi0yNDk3MDU5NGEzZTEiLCJpc3MiOiJodHRwczovL3Nzby5jbG91ZC5wamUuanVzLmJyL2F1dGgvcmVhbG1zL3BqZSIsImF1ZCI6WyJicm9rZXIiLCJhY2NvdW50Il0sInN1YiI6IjUwM2Y5ZTc3LWIzY2EtNGE2NC05MjA0LTBmMDJmNjdhZTZhOCIsInR5cCI6IkJlYXJlciIsImF6cCI6InBvcnRhbGV4dGVybm8tZnJvbnRlbmQiLCJub25jZSI6ImE2YTI5NDlmLTVkMTUtNDRjZC04YTEzLWViMWE1NzhhMjMwOCIsInNlc3Npb25fc3RhdGUiOiI0NmFmMzFjZS1iYzljLTQ5ZDQtODFjYS0xMjA2NTdkNzYyMzciLCJhY3IiOiIwIiwiYWxsb3dlZC1vcmlnaW5zIjpbImh0dHBzOi8vcG9ydGFsZGVzZXJ2aWNvcy5wZHBqLmp1cy5iciJdLCJyZWFsbV9hY2Nlc3MiOnsicm9sZXMiOlsib2ZmbGluZV9hY2Nlc3MiLCJ1bWFfYXV0aG9yaXphdGlvbiJdfSwicmVzb3VyY2VfYWNjZXNzIjp7ImJyb2tlciI6eyJyb2xlcyI6WyJyZWFkLXRva2VuIl19LCJhY2NvdW50Ijp7InJvbGVzIjpbIm1hbmFnZS1hY2NvdW50IiwibWFuYWdlLWFjY291bnQtbGlua3MiLCJ2aWV3LXByb2ZpbGUiXX19LCJzY29wZSI6Im9wZW5pZCBwcm9maWxlIGVtYWlsIiwic2lkIjoiNDZhZjMxY2UtYmM5Yy00OWQ0LTgxY2EtMTIwNjU3ZDc2MjM3IiwiQWNlc3NhUmVwb3NpdG9yaW8iOiJPayIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJuYW1lIjoiRlJBTkNJU0NPIEJSVU5PIE5PQlJFIERFIE1FTE8iLCJwcmVmZXJyZWRfdXNlcm5hbWUiOiIwNjMzMzE0NTM2MCIsImdpdmVuX25hbWUiOiJGUkFOQ0lTQ08gQlJVTk8gTk9CUkUgREUgTUVMTyIsImNvcnBvcmF0aXZvIjpbeyJzZXFfdXN1YXJpbyI6MTY1MDIzNjcsIm5vbV91c3VhcmlvIjoiRlJBTkNJU0NPIEJSVU5PIE5PQlJFIERFIE1FTE8iLCJudW1fY3BmIjoiMDYzMzMxNDUzNjAiLCJzaWdfdGlwb19jYXJnbyI6IkFEViIsImZsZ19hdGl2byI6IlMiLCJzZXFfc2lzdGVtYSI6MCwic2VxX3BlcmZpbCI6MCwiZHNjX29yZ2FvIjoiT0FCIiwic2VxX3RyaWJ1bmFsX3BhaSI6MCwiZHNjX2VtYWlsIjoibWVsb2ZhY2RpcmVpdG9AaG90bWFpbC5jb20iLCJzZXFfb3JnYW9fZXh0ZXJubyI6MCwiZHNjX29yZ2FvX2V4dGVybm8iOiJPQUIiLCJvYWIiOiJDRTQ0Njc0In1dLCJlbWFpbCI6Im1lbG9mYWNkaXJlaXRvQGhvdG1haWwuY29tIn0.QjvsSE_I7Ih5UtmFt2r5kdP6MLfSsQHCXYqdtVkHFKVcRm2A27kNVGn7BIKT9QYtoI_0Vwl9cH7CjSOoB3zLWn24iTnNmVkxASS1vr40owbm2coVYXyJ646csChh3eFK_7TRZgVP-4u_0_lJ1VVtGCvZmlALTGZu9xd4Lk06B5Az7mlucZ0kxW4_x4eaHPKc3jjf5mXybxPRkkBtGREZ1EtcWFdpA84QSHYDEy9_8TV32N1E_3rQXXyPbyjQ6eR-4RRc6SDwzgykoXR6oo_hy47DzMnx6-C4MW2er7EWc1XHpyl4Sngy3ZJN3-9VIgktS-sY9-Xzugp3bzxiZL7OHQ"
    base_url = "https://portaldeservicos.pdpj.jus.br"
    
    logger.info(f"🔄 Testando download de {len(href_list)} documentos...")
    
    results = []
    
    for i, href_binario in enumerate(href_list, 1):
        logger.info(f"📄 Testando documento {i}/{len(href_list)}")
        
        # Construir URL completa
        if href_binario.startswith('/'):
            document_url = f"{base_url}{href_binario}"
        else:
            document_url = f"{base_url}/{href_binario}"
        
        headers = {
            "Authorization": f"Bearer {token}",
            "User-Agent": "PDPJ-API-Client/1.0"
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(document_url, headers=headers)
                
                if response.status_code == 200:
                    content = response.content
                    filename = f"test_document_{i}.pdf"
                    
                    with open(filename, "wb") as f:
                        f.write(content)
                    
                    results.append({
                        "href": href_binario,
                        "success": True,
                        "size": len(content),
                        "filename": filename
                    })
                    
                    logger.info(f"✅ Documento {i} baixado: {len(content)} bytes -> {filename}")
                else:
                    results.append({
                        "href": href_binario,
                        "success": False,
                        "error": f"HTTP {response.status_code}"
                    })
                    
                    logger.error(f"❌ Documento {i} falhou: HTTP {response.status_code}")
                    
        except Exception as e:
            results.append({
                "href": href_binario,
                "success": False,
                "error": str(e)
            })
            
            logger.error(f"❌ Documento {i} erro: {e}")
    
    # Resumo dos resultados
    successful = len([r for r in results if r["success"]])
    logger.info(f"📊 Resumo: {successful}/{len(href_list)} documentos baixados com sucesso")
    
    return results

async def main():
    """Função principal"""
    logger.info("🚀 Iniciando testes de download com hrefBinario")
    
    # Teste 1: Download de um documento
    logger.info("=" * 50)
    logger.info("TESTE 1: Download de um documento")
    logger.info("=" * 50)
    
    success = await test_download_href()
    
    if success:
        logger.info("✅ Teste 1 passou!")
    else:
        logger.error("❌ Teste 1 falhou!")
    
    # Teste 2: Download de múltiplos documentos
    logger.info("=" * 50)
    logger.info("TESTE 2: Download de múltiplos documentos")
    logger.info("=" * 50)
    
    results = await test_multiple_documents()
    
    logger.info("=" * 50)
    logger.info("RESUMO FINAL")
    logger.info("=" * 50)
    
    successful = len([r for r in results if r["success"]])
    total = len(results)
    
    logger.info(f"📊 Total de testes: {total}")
    logger.info(f"✅ Sucessos: {successful}")
    logger.info(f"❌ Falhas: {total - successful}")
    
    if successful == total:
        logger.info("🎉 Todos os testes passaram!")
    else:
        logger.warning("⚠️ Alguns testes falharam")

if __name__ == "__main__":
    asyncio.run(main())
