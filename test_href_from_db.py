#!/usr/bin/env python3
"""
Testar download usando hrefBinario real do banco de dados
"""

import asyncio
import httpx
from loguru import logger

async def test_href_from_db():
    """Testar hrefBinario que está no banco"""
    
    # Token válido
    token = "eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICI1dnJEZ1hCS21FLTdFb3J2a0U1TXU5VmxJZF9JU2dsMnY3QWYyM25EdkRVIn0.eyJleHAiOjE3NTk3NzQ1MzcsImlhdCI6MTc1OTc0NTczNywiYXV0aF90aW1lIjoxNzU5NzQ1NjYyLCJqdGkiOiIyOWUzYzVjYy0yYzUyLTRjMGQtOTNjMC03OGVmNzQ5ZjNlZTgiLCJpc3MiOiJodHRwczovL3Nzby5jbG91ZC5wamUuanVzLmJyL2F1dGgvcmVhbG1zL3BqZSIsImF1ZCI6WyJicm9rZXIiLCJhY2NvdW50Il0sInN1YiI6IjUwM2Y5ZTc3LWIzY2EtNGE2NC05MjA0LTBmMDJmNjdhZTZhOCIsInR5cCI6IkJlYXJlciIsImF6cCI6InBvcnRhbGV4dGVybm8tZnJvbnRlbmQiLCJub25jZSI6Ijc3ODA2YTdiLTI1ZTItNGMwYi1hMTQ4LTllNDUzMzY3MDBmOSIsInNlc3Npb25fc3RhdGUiOiIyOTk5ZmI4NC1kNDk4LTRjOTMtOTQ1NS1iNDhlMzYyNTgxZmIiLCJhY3IiOiIwIiwiYWxsb3dlZC1vcmlnaW5zIjpbImh0dHBzOi8vcG9ydGFsZGVzZXJ2aWNvcy5wZHBqLmp1cy5iciJdLCJyZWFsbV9hY2Nlc3MiOnsicm9sZXMiOlsib2ZmbGluZV9hY2Nlc3MiLCJ1bWFfYXV0aG9yaXphdGlvbiJdfSwicmVzb3VyY2VfYWNjZXNzIjp7ImJyb2tlciI6eyJyb2xlcyI6WyJyZWFkLXRva2VuIl19LCJhY2NvdW50Ijp7InJvbGVzIjpbIm1hbmFnZS1hY2NvdW50IiwibWFuYWdlLWFjY291bnQtbGlua3MiLCJ2aWV3LXByb2ZpbGUiXX19LCJzY29wZSI6Im9wZW5pZCBwcm9maWxlIGVtYWlsIiwic2lkIjoiMjk5OWZiODQtZDQ5OC00YzkzLTk0NTUtYjQ4ZTM2MjU4MWZiIiwiQWNlc3NhUmVwb3NpdG9yaW8iOiJPayIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJuYW1lIjoiRlJBTkNJU0NPIEJSVU5PIE5PQlJFIERFIE1FTE8iLCJwcmVmZXJyZWRfdXNlcm5hbWUiOiIwNjMzMzE0NTM2MCIsImdpdmVuX25hbWUiOiJGUkFOQ0lTQ08gQlJVTk8gTk9CUkUgREUgTUVMTyIsImNvcnBvcmF0aXZvIjpbeyJzZXFfdXN1YXJpbyI6MTY1MDIzNjcsIm5vbV91c3VhcmlvIjoiRlJBTkNJU0NPIEJSVU5PIE5PQlJFIERFIE1FTE8iLCJudW1fY3BmIjoiMDYzMzMxNDUzNjAiLCJzaWdfdGlwb19jYXJnbyI6IkFEViIsImZsZ19hdGl2byI6IlMiLCJzZXFfc2lzdGVtYSI6MCwic2VxX3BlcmZpbCI6MCwiZHNjX29yZ2FvIjoiT0FCIiwic2VxX3RyaWJ1bmFsX3BhaSI6MCwiZHNjX2VtYWlsIjoibWVsb2ZhY2RpcmVpdG9AaG90bWFpbC5jb20iLCJzZXFfb3JnYW9fZXh0ZXJubyI6MCwiZHNjX29yZ2FvX2V4dGVybm8iOiJPQUIiLCJvYWIiOiJDRTQ0Njc0In1dLCJlbWFpbCI6Im1lbG9mYWNkaXJlaXRvQGhvdG1haWwuY29tIn0.CIat1hLgqV9vyLnhPfO6gE2XgZX2jtpuKwHo9ESuY2SdMEvXI3BoG3X54ScF6Z8QUPQw32FZ_rM_N38MKaSAgMzQEys2yE6a4PqJ8O4UUQTQ1R64XWXogaKX2aQdEaaGKv_fpsP9I7l8Mx_D-rStC_6K-BGWyK12chiyuBD2R22MBjGu8cxVWFZyneRxRVIRhZxNjpeBkS5nrdM5DCtXPhx3WkhUkMuRjy6MUyrAwMuRq4vxgYnl9Ya1Qey-UfxMcxqj4EqDP1UlWTAD8x-zyi5nCBcMKIiYK3xOr2FT3FIBeeLebmaf3c7K-A8PgmV0U4dI_Ipg_lWf7T22OqiStg"
    
    # hrefBinario real do banco de dados
    href_binario = "/processos/5029295-47.2024.4.03.6301/documentos/35703e1f-8b68-50ee-98ed-23e20edc7580/binario"
    
    # Construir URL com /api/v2/
    base_url = "https://portaldeservicos.pdpj.jus.br"
    if not href_binario.startswith('/api/v2/'):
        href_binario = f"/api/v2{href_binario}"
    document_url = f"{base_url}{href_binario}"
    
    logger.info(f"🔗 Testando hrefBinario do banco:")
    logger.info(f"   URL: {document_url}")
    
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
                if content.startswith(b'%PDF') or content.startswith(b'<!DOCTYPE'):
                    content_type = "PDF" if content.startswith(b'%PDF') else "HTML"
                    logger.info(f"📄 Tipo: {content_type}")
                    logger.info(f"📊 Tamanho: {len(content)} bytes")
                    
                    if content_type == "PDF":
                        logger.success("✅ PDF válido baixado do banco!")
                        return True
                    else:
                        logger.warning("⚠️ Retornou HTML ao invés de PDF")
            elif response.status_code == 404:
                logger.error("❌ Documento não encontrado na API PDPJ (404)")
                logger.warning("💡 O documento pode ter sido removido ou arquivado")
            else:
                logger.error(f"❌ Erro: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Erro: {e}")
    
    return False

async def main():
    logger.info("🧪 Testando hrefBinario do banco de dados")
    logger.info("="*60)
    
    success = await test_href_from_db()
    
    if success:
        logger.success("\n✅ hrefBinario do banco funciona!")
        logger.info("💡 O problema não é com nosso código!")
    else:
        logger.error("\n❌ hrefBinario do banco retorna 404")
        logger.info("💡 Possíveis causas:")
        logger.info("   1. Documento foi removido/arquivado")
        logger.info("   2. hrefBinario desatualizado")
        logger.info("   3. Processo precisa ser atualizado")

if __name__ == "__main__":
    asyncio.run(main())

