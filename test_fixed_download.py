#!/usr/bin/env python3
"""
Script para testar o download com a correção /api/v2/
"""

import asyncio
import httpx
from loguru import logger

logger.add("test_fixed_download.log", rotation="1 MB")

async def test_url_construction():
    """Testar construção de URL com /api/v2/"""
    
    base_url = "https://portaldeservicos.pdpj.jus.br"
    
    # Exemplos de hrefBinario
    test_cases = [
        {
            "href": "/processos/5000315-75.2025.4.03.6327/documentos/59a2dbcc-bb58-5281-a656-cfe57861c2db/binario",
            "expected": "https://portaldeservicos.pdpj.jus.br/api/v2/processos/5000315-75.2025.4.03.6327/documentos/59a2dbcc-bb58-5281-a656-cfe57861c2db/binario"
        },
        {
            "href": "processos/1000145-91.2023.8.26.0597/documentos/a98a3080-bd47-5f84-83e6-4e24899a89cf/binario",
            "expected": "https://portaldeservicos.pdpj.jus.br/api/v2/processos/1000145-91.2023.8.26.0597/documentos/a98a3080-bd47-5f84-83e6-4e24899a89cf/binario"
        }
    ]
    
    logger.info("🔧 Testando construção de URLs...")
    
    for i, test in enumerate(test_cases, 1):
        href_binario = test["href"]
        expected = test["expected"]
        
        # Simular a lógica do código atualizado
        if href_binario.startswith('/'):
            if not href_binario.startswith('/api/v2/'):
                href_binario = f"/api/v2{href_binario}"
            document_url = f"{base_url}{href_binario}"
        else:
            document_url = f"{base_url}/api/v2/{href_binario}"
        
        is_correct = document_url == expected
        symbol = "✅" if is_correct else "❌"
        
        logger.info(f"{symbol} Teste {i}: {is_correct}")
        logger.info(f"  href original: {test['href']}")
        logger.info(f"  URL gerada:    {document_url}")
        logger.info(f"  URL esperada:  {expected}")
        logger.info("")

async def test_real_download():
    """Testar download real usando o código corrigido"""
    
    token = "eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICI1dnJEZ1hCS21FLTdFb3J2a0U1TXU5VmxJZF9JU2dsMnY3QWYyM25EdkRVIn0.eyJleHAiOjE3NTk3NzQ1MzcsImlhdCI6MTc1OTc0NTczNywiYXV0aF90aW1lIjoxNzU5NzQ1NjYyLCJqdGkiOiIyOWUzYzVjYy0yYzUyLTRjMGQtOTNjMC03OGVmNzQ5ZjNlZTgiLCJpc3MiOiJodHRwczovL3Nzby5jbG91ZC5wamUuanVzLmJyL2F1dGgvcmVhbG1zL3BqZSIsImF1ZCI6WyJicm9rZXIiLCJhY2NvdW50Il0sInN1YiI6IjUwM2Y5ZTc3LWIzY2EtNGE2NC05MjA0LTBmMDJmNjdhZTZhOCIsInR5cCI6IkJlYXJlciIsImF6cCI6InBvcnRhbGV4dGVybm8tZnJvbnRlbmQiLCJub25jZSI6Ijc3ODA2YTdiLTI1ZTItNGMwYi1hMTQ4LTllNDUzMzY3MDBmOSIsInNlc3Npb25fc3RhdGUiOiIyOTk5ZmI4NC1kNDk4LTRjOTMtOTQ1NS1iNDhlMzYyNTgxZmIiLCJhY3IiOiIwIiwiYWxsb3dlZC1vcmlnaW5zIjpbImh0dHBzOi8vcG9ydGFsZGVzZXJ2aWNvcy5wZHBqLmp1cy5iciJdLCJyZWFsbV9hY2Nlc3MiOnsicm9sZXMiOlsib2ZmbGluZV9hY2Nlc3MiLCJ1bWFfYXV0aG9yaXphdGlvbiJdfSwicmVzb3VyY2VfYWNjZXNzIjp7ImJyb2tlciI6eyJyb2xlcyI6WyJyZWFkLXRva2VuIl19LCJhY2NvdW50Ijp7InJvbGVzIjpbIm1hbmFnZS1hY2NvdW50IiwibWFuYWdlLWFjY291bnQtbGlua3MiLCJ2aWV3LXByb2ZpbGUiXX19LCJzY29wZSI6Im9wZW5pZCBwcm9maWxlIGVtYWlsIiwic2lkIjoiMjk5OWZiODQtZDQ5OC00YzkzLTk0NTUtYjQ4ZTM2MjU4MWZiIiwiQWNlc3NhUmVwb3NpdG9yaW8iOiJPayIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJuYW1lIjoiRlJBTkNJU0NPIEJSVU5PIE5PQlJFIERFIE1FTE8iLCJwcmVmZXJyZWRfdXNlcm5hbWUiOiIwNjMzMzE0NTM2MCIsImdpdmVuX25hbWUiOiJGUkFOQ0lTQ08gQlJVTk8gTk9CUkUgREUgTUVMTyIsImNvcnBvcmF0aXZvIjpbeyJzZXFfdXN1YXJpbyI6MTY1MDIzNjcsIm5vbV91c3VhcmlvIjoiRlJBTkNJU0NPIEJSVU5PIE5PQlJFIERFIE1FTE8iLCJudW1fY3BmIjoiMDYzMzMxNDUzNjAiLCJzaWdfdGlwb19jYXJnbyI6IkFEViIsImZsZ19hdGl2byI6IlMiLCJzZXFfc2lzdGVtYSI6MCwic2VxX3BlcmZpbCI6MCwiZHNjX29yZ2FvIjoiT0FCIiwic2VxX3RyaWJ1bmFsX3BhaSI6MCwiZHNjX2VtYWlsIjoibWVsb2ZhY2RpcmVpdG9AaG90bWFpbC5jb20iLCJzZXFfb3JnYW9fZXh0ZXJubyI6MCwiZHNjX29yZ2FvX2V4dGVybm8iOiJPQUIiLCJvYWIiOiJDRTQ0Njc0In1dLCJlbWFpbCI6Im1lbG9mYWNkaXJlaXRvQGhvdG1haWwuY29tIn0.CIat1hLgqV9vyLnhPfO6gE2XgZX2jtpuKwHo9ESuY2SdMEvXI3BoG3X54ScF6Z8QUPQw32FZ_rM_N38MKaSAgMzQEys2yE6a4PqJ8O4UUQTQ1R64XWXogaKX2aQdEaaGKv_fpsP9I7l8Mx_D-rStC_6K-BGWyK12chiyuBD2R22MBjGu8cxVWFZyneRxRVIRhZxNjpeBkS5nrdM5DCtXPhx3WkhUkMuRjy6MUyrAwMuRq4vxgYnl9Ya1Qey-UfxMcxqj4EqDP1UlWTAD8x-zyi5nCBcMKIiYK3xOr2FT3FIBeeLebmaf3c7K-A8PgmV0U4dI_Ipg_lWf7T22OqiStg"
    
    base_url = "https://portaldeservicos.pdpj.jus.br"
    href_binario = "/processos/5000315-75.2025.4.03.6327/documentos/59a2dbcc-bb58-5281-a656-cfe57861c2db/binario"
    
    # Aplicar a lógica de construção de URL
    if href_binario.startswith('/'):
        if not href_binario.startswith('/api/v2/'):
            href_binario = f"/api/v2{href_binario}"
        document_url = f"{base_url}{href_binario}"
    else:
        document_url = f"{base_url}/api/v2/{href_binario}"
    
    logger.info(f"📡 Testando download real...")
    logger.info(f"🔗 URL: {document_url}")
    
    headers = {
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "en-US,en;q=0.9,pt;q=0.8",
        "authorization": f"Bearer {token}",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(document_url, headers=headers)
            
            logger.info(f"📊 Status: {response.status_code}")
            logger.info(f"📊 Content-Type: {response.headers.get('content-type', 'N/A')}")
            logger.info(f"📊 Content-Length: {response.headers.get('content-length', 'N/A')}")
            
            if response.status_code == 200:
                content = response.content
                if content.startswith(b'%PDF'):
                    logger.info(f"✅ PDF válido baixado! ({len(content)} bytes)")
                    return True
                else:
                    logger.warning(f"⚠️ Não é PDF")
            else:
                logger.error(f"❌ Erro: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Erro: {e}")
    
    return False

async def main():
    """Função principal"""
    logger.info("🚀 Testando correção de URL com /api/v2/\n")
    
    # Teste 1: Construção de URLs
    await test_url_construction()
    
    # Teste 2: Download real
    logger.info("\n" + "="*60)
    logger.info("Teste de download real")
    logger.info("="*60)
    success = await test_real_download()
    
    if success:
        logger.info("\n✅ SUCESSO! A correção funciona!")
    else:
        logger.error("\n❌ Algo ainda não está funcionando")
    
    logger.info("\n🏁 Testes concluídos")

if __name__ == "__main__":
    asyncio.run(main())

