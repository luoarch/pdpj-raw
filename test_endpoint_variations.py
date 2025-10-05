#!/usr/bin/env python3
"""
Script para testar variações do endpoint de download
"""

import asyncio
import httpx
from loguru import logger

# Configurar logging
logger.add("test_endpoints.log", rotation="1 MB")

async def test_endpoint_variations():
    """Testar diferentes variações do endpoint de download"""
    
    token = "eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICI1dnJEZ1hCS21FLTdFb3J2a0U1TXU5VmxJZF9JU2dsMnY3QWYyM25EdkRVIn0.eyJleHAiOjE3NTk2MjYzNDMsImlhdCI6MTc1OTYxMTA0OSwiYXV0aF90aW1lIjoxNzU5NTgzMTQzLCJqdGkiOiJiM2IzZGYxMC1mNjZmLTQzMmUtODAyZi0yNDk3MDU5NGEzZTEiLCJpc3MiOiJodHRwczovL3Nzby5jbG91ZC5wamUuanVzLmJyL2F1dGgvcmVhbG1zL3BqZSIsImF1ZCI6WyJicm9rZXIiLCJhY2NvdW50Il0sInN1YiI6IjUwM2Y5ZTc3LWIzY2EtNGE2NC05MjA0LTBmMDJmNjdhZTZhOCIsInR5cCI6IkJlYXJlciIsImF6cCI6InBvcnRhbGV4dGVybm8tZnJvbnRlbmQiLCJub25jZSI6ImE2YTI5NDlmLTVkMTUtNDRjZC04YTEzLWViMWE1NzhhMjMwOCIsInNlc3Npb25fc3RhdGUiOiI0NmFmMzFjZS1iYzljLTQ5ZDQtODFjYS0xMjA2NTdkNzYyMzciLCJhY3IiOiIwIiwiYWxsb3dlZC1vcmlnaW5zIjpbImh0dHBzOi8vcG9ydGFsZGVzZXJ2aWNvcy5wZHBqLmp1cy5iciJdLCJyZWFsbV9hY2Nlc3MiOnsicm9sZXMiOlsib2ZmbGluZV9hY2Nlc3MiLCJ1bWFfYXV0aG9yaXphdGlvbiJdfSwicmVzb3VyY2VfYWNjZXNzIjp7ImJyb2tlciI6eyJyb2xlcyI6WyJyZWFkLXRva2VuIl19LCJhY2NvdW50Ijp7InJvbGVzIjpbIm1hbmFnZS1hY2NvdW50IiwibWFuYWdlLWFjY291bnQtbGlua3MiLCJ2aWV3LXByb2ZpbGUiXX19LCJzY29wZSI6Im9wZW5pZCBwcm9maWxlIGVtYWlsIiwic2lkIjoiNDZhZjMxY2UtYmM5Yy00OWQ0LTgxY2EtMTIwNjU3ZDc2MjM3IiwiQWNlc3NhUmVwb3NpdG9yaW8iOiJPayIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJuYW1lIjoiRlJBTkNJU0NPIEJSVU5PIE5PQlJFIERFIE1FTE8iLCJwcmVmZXJyZWRfdXNlcm5hbWUiOiIwNjMzMzE0NTM2MCIsImdpdmVuX25hbWUiOiJGUkFOQ0lTQ08gQlJVTk8gTk9CUkUgREUgTUVMTyIsImNvcnBvcmF0aXZvIjpbeyJzZXFfdXN1YXJpbyI6MTY1MDIzNjcsIm5vbV91c3VhcmlvIjoiRlJBTkNJU0NPIEJSVU5PIE5PQlJFIERFIE1FTE8iLCJudW1fY3BmIjoiMDYzMzMxNDUzNjAiLCJzaWdfdGlwb19jYXJnbyI6IkFEViIsImZsZ19hdGl2byI6IlMiLCJzZXFfc2lzdGVtYSI6MCwic2VxX3BlcmZpbCI6MCwiZHNjX29yZ2FvIjoiT0FCIiwic2VxX3RyaWJ1bmFsX3BhaSI6MCwiZHNjX2VtYWlsIjoibWVsb2ZhY2RpcmVpdG9AaG90bWFpbC5jb20iLCJzZXFfb3JnYW9fZXh0ZXJubyI6MCwiZHNjX29yZ2FvX2V4dGVybm8iOiJPQUIiLCJvYWIiOiJDRTQ0Njc0In1dLCJlbWFpbCI6Im1lbG9mYWNkaXJlaXRvQGhvdG1haWwuY29tIn0.QjvsSE_I7Ih5UtmFt2r5kdP6MLfSsQHCXYqdtVkHFKVcRm2A27kNVGn7BIKT9QYtoI_0Vwl9cH7CjSOoB3zLWn24iTnNmVkxASS1vr40owbm2coVYXyJ646csChh3eFK_7TRZgVP-4u_0_lJ1VVtGCvZmlALTGZu9xd4Lk06B5Az7mlucZ0kxW4_x4eaHPKc3jjf5mXybxPRkkBtGREZ1EtcWFdpA84QSHYDEy9_8TV32N1E_3rQXXyPbyjQ6eR-4RRc6SDwzgykoXR6oo_hy47DzMnx6-C4MW2er7EWc1XHpyl4Sngy3ZJN3-9VIgktS-sY9-Xzugp3bzxiZL7OHQ"
    base_url = "https://portaldeservicos.pdpj.jus.br"
    
    # Documento de teste
    process_number = "1000145-91.2023.8.26.0597"
    document_id = "a98a3080-bd47-5f84-83e6-4e24899a89cf"
    
    # Variações de endpoints para testar
    endpoints = [
        # Endpoint atual (que retorna HTML)
        f"/processos/{process_number}/documentos/{document_id}/binario",
        
        # Variações com /api/v2
        f"/api/v2/processos/{process_number}/documentos/{document_id}/binario",
        f"/api/v2/documentos/{document_id}/binario",
        
        # Variações sem /binario
        f"/processos/{process_number}/documentos/{document_id}",
        f"/api/v2/processos/{process_number}/documentos/{document_id}",
        f"/api/v2/documentos/{document_id}",
        
        # Variações com /download
        f"/processos/{process_number}/documentos/{document_id}/download",
        f"/api/v2/processos/{process_number}/documentos/{document_id}/download",
        
        # Variações com /arquivo
        f"/processos/{process_number}/documentos/{document_id}/arquivo",
        f"/api/v2/processos/{process_number}/documentos/{document_id}/arquivo",
        
        # Variações com /file
        f"/processos/{process_number}/documentos/{document_id}/file",
        f"/api/v2/processos/{process_number}/documentos/{document_id}/file",
    ]
    
    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": "PDPJ-API-Client/1.0",
        "Accept": "application/pdf, application/octet-stream, */*"
    }
    
    logger.info(f"🔍 Testando {len(endpoints)} variações de endpoints...")
    
    results = []
    
    for i, endpoint in enumerate(endpoints, 1):
        url = f"{base_url}{endpoint}"
        logger.info(f"📄 Teste {i}/{len(endpoints)}: {endpoint}")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers=headers)
                
                content_type = response.headers.get('content-type', 'N/A')
                content_length = len(response.content)
                
                # Verificar se é PDF
                is_pdf = response.content.startswith(b'%PDF')
                
                # Verificar se é HTML
                is_html = response.content.startswith(b'<!DOCTYPE html') or response.content.startswith(b'<html')
                
                result = {
                    "endpoint": endpoint,
                    "status": response.status_code,
                    "content_type": content_type,
                    "content_length": content_length,
                    "is_pdf": is_pdf,
                    "is_html": is_html,
                    "success": response.status_code == 200 and is_pdf
                }
                
                results.append(result)
                
                if result["success"]:
                    logger.info(f"✅ SUCESSO! PDF encontrado: {content_length} bytes")
                elif is_html:
                    logger.warning(f"⚠️ HTML retornado: {content_length} bytes")
                elif response.status_code == 404:
                    logger.error(f"❌ 404 Not Found")
                elif response.status_code == 401:
                    logger.error(f"❌ 401 Unauthorized")
                elif response.status_code == 403:
                    logger.error(f"❌ 403 Forbidden")
                else:
                    logger.info(f"📊 Status {response.status_code}: {content_type} ({content_length} bytes)")
                
        except Exception as e:
            logger.error(f"❌ Erro: {e}")
            results.append({
                "endpoint": endpoint,
                "error": str(e),
                "success": False
            })
    
    # Resumo dos resultados
    logger.info("=" * 60)
    logger.info("RESUMO DOS TESTES")
    logger.info("=" * 60)
    
    successful = [r for r in results if r.get("success", False)]
    html_responses = [r for r in results if r.get("is_html", False)]
    not_found = [r for r in results if r.get("status") == 404]
    
    logger.info(f"📊 Total de testes: {len(results)}")
    logger.info(f"✅ PDFs encontrados: {len(successful)}")
    logger.info(f"⚠️ Respostas HTML: {len(html_responses)}")
    logger.info(f"❌ 404 Not Found: {len(not_found)}")
    
    if successful:
        logger.info("\n🎉 ENDPOINTS QUE FUNCIONAM:")
        for result in successful:
            logger.info(f"   ✅ {result['endpoint']}")
    else:
        logger.info("\n❌ Nenhum endpoint retornou PDF válido")
        
        if html_responses:
            logger.info("\n⚠️ Endpoints que retornam HTML:")
            for result in html_responses:
                logger.info(f"   ⚠️ {result['endpoint']} (Status: {result['status']})")
    
    return results

async def main():
    """Função principal"""
    logger.info("🚀 Iniciando teste de variações de endpoints")
    results = await test_endpoint_variations()
    
    # Salvar resultados em arquivo
    with open("endpoint_test_results.txt", "w") as f:
        f.write("RESULTADOS DOS TESTES DE ENDPOINTS\n")
        f.write("=" * 50 + "\n\n")
        
        for result in results:
            f.write(f"Endpoint: {result['endpoint']}\n")
            f.write(f"Status: {result.get('status', 'N/A')}\n")
            f.write(f"Content-Type: {result.get('content_type', 'N/A')}\n")
            f.write(f"Tamanho: {result.get('content_length', 'N/A')} bytes\n")
            f.write(f"É PDF: {result.get('is_pdf', False)}\n")
            f.write(f"É HTML: {result.get('is_html', False)}\n")
            f.write(f"Sucesso: {result.get('success', False)}\n")
            f.write("-" * 30 + "\n")
    
    logger.info("💾 Resultados salvos em endpoint_test_results.txt")

if __name__ == "__main__":
    asyncio.run(main())
