#!/usr/bin/env python3
"""
Script para testar download via portal web PDPJ
"""

import asyncio
import httpx
from loguru import logger

# Configurar logging
logger.add("test_portal_download.log", rotation="1 MB")

async def test_portal_download():
    """Testar download via portal web com sessão"""
    
    token = "eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICI1dnJEZ1hCS21FLTdFb3J2a0U1TXU5VmxJZF9JU2dsMnY3QWYyM25EdkRVIn0.eyJleHAiOjE3NTk3NzQ1MzcsImlhdCI6MTc1OTc0NTczNywiYXV0aF90aW1lIjoxNzU5NzQ1NjYyLCJqdGkiOiIyOWUzYzVjYy0yYzUyLTRjMGQtOTNjMC03OGVmNzQ5ZjNlZTgiLCJpc3MiOiJodHRwczovL3Nzby5jbG91ZC5wamUuanVzLmJyL2F1dGgvcmVhbG1zL3BqZSIsImF1ZCI6WyJicm9rZXIiLCJhY2NvdW50Il0sInN1YiI6IjUwM2Y5ZTc3LWIzY2EtNGE2NC05MjA0LTBmMDJmNjdhZTZhOCIsInR5cCI6IkJlYXJlciIsImF6cCI6InBvcnRhbGV4dGVybm8tZnJvbnRlbmQiLCJub25jZSI6Ijc3ODA2YTdiLTI1ZTItNGMwYi1hMTQ4LTllNDUzMzY3MDBmOSIsInNlc3Npb25fc3RhdGUiOiIyOTk5ZmI4NC1kNDk4LTRjOTMtOTQ1NS1iNDhlMzYyNTgxZmIiLCJhY3IiOiIwIiwiYWxsb3dlZC1vcmlnaW5zIjpbImh0dHBzOi8vcG9ydGFsZGVzZXJ2aWNvcy5wZHBqLmp1cy5iciJdLCJyZWFsbV9hY2Nlc3MiOnsicm9sZXMiOlsib2ZmbGluZV9hY2Nlc3MiLCJ1bWFfYXV0aG9yaXphdGlvbiJdfSwicmVzb3VyY2VfYWNjZXNzIjp7ImJyb2tlciI6eyJyb2xlcyI6WyJyZWFkLXRva2VuIl19LCJhY2NvdW50Ijp7InJvbGVzIjpbIm1hbmFnZS1hY2NvdW50IiwibWFuYWdlLWFjY291bnQtbGlua3MiLCJ2aWV3LXByb2ZpbGUiXX19LCJzY29wZSI6Im9wZW5pZCBwcm9maWxlIGVtYWlsIiwic2lkIjoiMjk5OWZiODQtZDQ5OC00YzkzLTk0NTUtYjQ4ZTM2MjU4MWZiIiwiQWNlc3NhUmVwb3NpdG9yaW8iOiJPayIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJuYW1lIjoiRlJBTkNJU0NPIEJSVU5PIE5PQlJFIERFIE1FTE8iLCJwcmVmZXJyZWRfdXNlcm5hbWUiOiIwNjMzMzE0NTM2MCIsImdpdmVuX25hbWUiOiJGUkFOQ0lTQ08gQlJVTk8gTk9CUkUgREUgTUVMTyIsImNvcnBvcmF0aXZvIjpbeyJzZXFfdXN1YXJpbyI6MTY1MDIzNjcsIm5vbV91c3VhcmlvIjoiRlJBTkNJU0NPIEJSVU5PIE5PQlJFIERFIE1FTE8iLCJudW1fY3BmIjoiMDYzMzMxNDUzNjAiLCJzaWdfdGlwb19jYXJnbyI6IkFEViIsImZsZ19hdGl2byI6IlMiLCJzZXFfc2lzdGVtYSI6MCwic2VxX3BlcmZpbCI6MCwiZHNjX29yZ2FvIjoiT0FCIiwic2VxX3RyaWJ1bmFsX3BhaSI6MCwiZHNjX2VtYWlsIjoibWVsb2ZhY2RpcmVpdG9AaG90bWFpbC5jb20iLCJzZXFfb3JnYW9fZXh0ZXJubyI6MCwiZHNjX29yZ2FvX2V4dGVybm8iOiJPQUIiLCJvYWIiOiJDRTQ0Njc0In1dLCJlbWFpbCI6Im1lbG9mYWNkaXJlaXRvQGhvdG1haWwuY29tIn0.CIat1hLgqV9vyLnhPfO6gE2XgZX2jtpuKwHo9ESuY2SdMEvXI3BoG3X54ScF6Z8QUPQw32FZ_rM_N38MKaSAgMzQEys2yE6a4PqJ8O4UUQTQ1R64XWXogaKX2aQdEaaGKv_fpsP9I7l8Mx_D-rStC_6K-BGWyK12chiyuBD2R22MBjGu8cxVWFZyneRxRVIRhZxNjpeBkS5nrdM5DCtXPhx3WkhUkMuRjy6MUyrAwMuRq4vxgYnl9Ya1Qey-UfxMcxqj4EqDP1UlWTAD8x-zyi5nCBcMKIiYK3xOr2FT3FIBeeLebmaf3c7K-A8PgmV0U4dI_Ipg_lWf7T22OqiStg"
    
    # URLs de teste
    base_url = "https://portaldeservicos.pdpj.jus.br"
    process_number = "1000145-91.2023.8.26.0597"
    document_id = "a98a3080-bd47-5f84-83e6-4e24899a89cf"
    
    # Headers para simular navegador
    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0"
    }
    
    logger.info("🔍 Testando download via portal web...")
    
    # Teste 1: Acessar página do processo primeiro
    process_url = f"{base_url}/processos/{process_number}"
    logger.info(f"📄 Teste 1: Acessando página do processo: {process_url}")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Primeiro, acessar a página do processo para estabelecer sessão
            response = await client.get(process_url, headers=headers)
            logger.info(f"📊 Status da página do processo: {response.status_code}")
            logger.info(f"📊 Content-Type: {response.headers.get('content-type', 'N/A')}")
            
            if response.status_code == 200:
                logger.info("✅ Página do processo acessada com sucesso")
                
                # Agora tentar o download do documento
                document_url = f"{base_url}/processos/{process_number}/documentos/{document_id}/binario"
                logger.info(f"📄 Teste 2: Tentando download: {document_url}")
                
                # Headers específicos para download
                download_headers = headers.copy()
                download_headers.update({
                    "Accept": "application/pdf,application/octet-stream,*/*",
                    "Sec-Fetch-Dest": "document",
                    "Sec-Fetch-Mode": "navigate",
                    "Referer": process_url
                })
                
                download_response = await client.get(document_url, headers=download_headers)
                
                logger.info(f"📊 Status do download: {download_response.status_code}")
                logger.info(f"📊 Content-Type: {download_response.headers.get('content-type', 'N/A')}")
                logger.info(f"📊 Content-Length: {download_response.headers.get('content-length', 'N/A')}")
                
                content = download_response.content
                logger.info(f"📊 Tamanho do conteúdo: {len(content)} bytes")
                
                # Verificar se é PDF
                if content.startswith(b'%PDF'):
                    logger.info("✅ SUCESSO! PDF válido encontrado!")
                    
                    # Salvar o PDF
                    with open("test_portal_download.pdf", "wb") as f:
                        f.write(content)
                    logger.info("💾 PDF salvo como test_portal_download.pdf")
                    
                    return True
                elif content.startswith(b'<!DOCTYPE html'):
                    logger.warning("⚠️ Ainda retorna HTML")
                    logger.info(f"🔍 Primeiros 200 bytes: {content[:200]}")
                else:
                    logger.info(f"🔍 Primeiros 100 bytes: {content[:100]}")
                    
            else:
                logger.error(f"❌ Erro ao acessar página do processo: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Erro: {e}")
    
    return False

async def test_alternative_approaches():
    """Testar abordagens alternativas"""
    
    token = "eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICI1dnJEZ1hCS21FLTdFb3J2a0U1TXU5VmxJZF9JU2dsMnY3QWYyM25EdkRVIn0.eyJleHAiOjE3NTk2MjYzNDMsImlhdCI6MTc1OTYxMTA0OSwiYXV0aF90aW1lIjoxNzU5NTgzMTQzLCJqdGkiOiJiM2IzZGYxMC1mNjZmLTQzMmUtODAyZi0yNDk3MDU5NGEzZTEiLCJpc3MiOiJodHRwczovL3Nzby5jbG91ZC5wamUuanVzLmJyL2F1dGgvcmVhbG1zL3BqZSIsImF1ZCI6WyJicm9rZXIiLCJhY2NvdW50Il0sInN1YiI6IjUwM2Y5ZTc3LWIzY2EtNGE2NC05MjA0LTBmMDJmNjdhZTZhOCIsInR5cCI6IkJlYXJlciIsImF6cCI6InBvcnRhbGV4dGVybm8tZnJvbnRlbmQiLCJub25jZSI6ImE2YTI5NDlmLTVkMTUtNDRjZC04YTEzLWViMWE1NzhhMjMwOCIsInNlc3Npb25fc3RhdGUiOiI0NmFmMzFjZS1iYzljLTQ5ZDQtODFjYS0xMjA2NTdkNzYyMzciLCJhY3IiOiIwIiwiYWxsb3dlZC1vcmlnaW5zIjpbImh0dHBzOi8vcG9ydGFsZGVzZXJ2aWNvcy5wZHBqLmp1cy5iciJdLCJyZWFsbV9hY2Nlc3MiOnsicm9sZXMiOlsib2ZmbGluZV9hY2Nlc3MiLCJ1bWFfYXV0aG9yaXphdGlvbiJdfSwicmVzb3VyY2VfYWNjZXNzIjp7ImJyb2tlciI6eyJyb2xlcyI6WyJyZWFkLXRva2VuIl19LCJhY2NvdW50Ijp7InJvbGVzIjpbIm1hbmFnZS1hY2NvdW50IiwibWFuYWdlLWFjY291bnQtbGlua3MiLCJ2aWV3LXByb2ZpbGUiXX19LCJzY29wZSI6Im9wZW5pZCBwcm9maWxlIGVtYWlsIiwic2lkIjoiNDZhZjMxY2UtYmM5Yy00OWQ0LTgxY2EtMTIwNjU3ZDc2MjM3IiwiQWNlc3NhUmVwb3NpdG9yaW8iOiJPayIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJuYW1lIjoiRlJBTkNJU0NPIEJSVU5PIE5PQlJFIERFIE1FTE8iLCJwcmVmZXJyZWRfdXNlcm5hbWUiOiIwNjMzMzE0NTM2MCIsImdpdmVuX25hbWUiOiJGUkFOQ0lTQ08gQlJVTk8gTk9CUkUgREUgTUVMTyIsImNvcnBvcmF0aXZvIjpbeyJzZXFfdXN1YXJpbyI6MTY1MDIzNjcsIm5vbV91c3VhcmlvIjoiRlJBTkNJU0NPIEJSVU5PIE5PQlJFIERFIE1FTE8iLCJudW1fY3BmIjoiMDYzMzMxNDUzNjAiLCJzaWdfdGlwb19jYXJnbyI6IkFEViIsImZsZ19hdGl2byI6IlMiLCJzZXFfc2lzdGVtYSI6MCwic2VxX3BlcmZpbCI6MCwiZHNjX29yZ2FvIjoiT0FCIiwic2VxX3RyaWJ1bmFsX3BhaSI6MCwiZHNjX2VtYWlsIjoibWVsb2ZhY2RpcmVpdG9AaG90bWFpbC5jb20iLCJzZXFfb3JnYW9fZXh0ZXJubyI6MCwiZHNjX29yZ2FvX2V4dGVybm8iOiJPQUIiLCJvYWIiOiJDRTQ0Njc0In1dLCJlbWFpbCI6Im1lbG9mYWNkaXJlaXRvQGhvdG1haWwuY29tIn0.QjvsSE_I7Ih5UtmFt2r5kdP6MLfSsQHCXYqdtVkHFKVcRm2A27kNVGn7BIKT9QYtoI_0Vwl9cH7CjSOoB3zLWn24iTnNmVkxASS1vr40owbm2coVYXyJ646csChh3eFK_7TRZgVP-4u_0_lJ1VVtGCvZmlALTGZu9xd4Lk06B5Az7mlucZ0kxW4_x4eaHPKc3jjf5mXybxPRkkBtGREZ1EtcWFdpA84QSHYDEy9_8TV32N1E_3rQXXyPbyjQ6eR-4RRc6SDwzgykoXR6oo_hy47DzMnx6-C4MW2er7EWc1XHpyl4Sngy3ZJN3-9VIgktS-sY9-Xzugp3bzxiZL7OHQ"
    
    base_url = "https://portaldeservicos.pdpj.jus.br"
    process_number = "1000145-91.2023.8.26.0597"
    document_id = "a98a3080-bd47-5f84-83e6-4e24899a89cf"
    
    # Testar diferentes abordagens
    approaches = [
        {
            "name": "Com Referer e Cookies",
            "headers": {
                "Authorization": f"Bearer {token}",
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Accept": "application/pdf,*/*",
                "Referer": f"{base_url}/processos/{process_number}",
                "Cookie": f"access_token={token}"
            }
        },
        {
            "name": "Com X-Requested-With",
            "headers": {
                "Authorization": f"Bearer {token}",
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Accept": "application/pdf,*/*",
                "X-Requested-With": "XMLHttpRequest",
                "Referer": f"{base_url}/processos/{process_number}"
            }
        },
        {
            "name": "Com Accept-Encoding específico",
            "headers": {
                "Authorization": f"Bearer {token}",
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Accept": "application/pdf,application/octet-stream",
                "Accept-Encoding": "identity",
                "Referer": f"{base_url}/processos/{process_number}"
            }
        }
    ]
    
    document_url = f"{base_url}/processos/{process_number}/documentos/{document_id}/binario"
    
    for i, approach in enumerate(approaches, 1):
        logger.info(f"📄 Teste {i}: {approach['name']}")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(document_url, headers=approach['headers'])
                
                logger.info(f"📊 Status: {response.status_code}")
                logger.info(f"📊 Content-Type: {response.headers.get('content-type', 'N/A')}")
                
                content = response.content
                
                if content.startswith(b'%PDF'):
                    logger.info("✅ SUCESSO! PDF encontrado!")
                    with open(f"test_approach_{i}.pdf", "wb") as f:
                        f.write(content)
                    return True
                else:
                    logger.warning(f"⚠️ Não é PDF: {len(content)} bytes")
                    
            except Exception as e:
                logger.error(f"❌ Erro: {e}")
    
    return False

async def main():
    """Função principal"""
    logger.info("🚀 Iniciando testes de download via portal")
    
    # Teste 1: Download via portal
    success1 = await test_portal_download()
    
    if not success1:
        logger.info("🔄 Tentando abordagens alternativas...")
        success2 = await test_alternative_approaches()
        
        if not success2:
            logger.error("❌ Nenhuma abordagem funcionou")
            logger.info("💡 Conclusão: A API PDPJ não suporta download direto de documentos")
            logger.info("💡 Solução: Implementar scraping do portal web ou usar API alternativa")
    
    logger.info("🏁 Testes concluídos")

if __name__ == "__main__":
    asyncio.run(main())
