#!/usr/bin/env python3
"""
Testar download do processo novo: 1011745-77.2025.8.11.0041
"""

import asyncio
import httpx
from loguru import logger

async def test_document_from_new_process():
    """Testar documento do processo novo"""
    
    token = "eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICI1dnJEZ1hCS21FLTdFb3J2a0U1TXU5VmxJZF9JU2dsMnY3QWYyM25EdkRVIn0.eyJleHAiOjE3NTk3NzQ1MzcsImlhdCI6MTc1OTc0NTczNywiYXV0aF90aW1lIjoxNzU5NzQ1NjYyLCJqdGkiOiIyOWUzYzVjYy0yYzUyLTRjMGQtOTNjMC03OGVmNzQ5ZjNlZTgiLCJpc3MiOiJodHRwczovL3Nzby5jbG91ZC5wamUuanVzLmJyL2F1dGgvcmVhbG1zL3BqZSIsImF1ZCI6WyJicm9rZXIiLCJhY2NvdW50Il0sInN1YiI6IjUwM2Y5ZTc3LWIzY2EtNGE2NC05MjA0LTBmMDJmNjdhZTZhOCIsInR5cCI6IkJlYXJlciIsImF6cCI6InBvcnRhbGV4dGVybm8tZnJvbnRlbmQiLCJub25jZSI6Ijc3ODA2YTdiLTI1ZTItNGMwYi1hMTQ4LTllNDUzMzY3MDBmOSIsInNlc3Npb25fc3RhdGUiOiIyOTk5ZmI4NC1kNDk4LTRjOTMtOTQ1NS1iNDhlMzYyNTgxZmIiLCJhY3IiOiIwIiwiYWxsb3dlZC1vcmlnaW5zIjpbImh0dHBzOi8vcG9ydGFsZGVzZXJ2aWNvcy5wZHBqLmp1cy5iciJdLCJyZWFsbV9hY2Nlc3MiOnsicm9sZXMiOlsib2ZmbGluZV9hY2Nlc3MiLCJ1bWFfYXV0aG9yaXphdGlvbiJdfSwicmVzb3VyY2VfYWNjZXNzIjp7ImJyb2tlciI6eyJyb2xlcyI6WyJyZWFkLXRva2VuIl19LCJhY2NvdW50Ijp7InJvbGVzIjpbIm1hbmFnZS1hY2NvdW50IiwibWFuYWdlLWFjY291bnQtbGlua3MiLCJ2aWV3LXByb2ZpbGUiXX19LCJzY29wZSI6Im9wZW5pZCBwcm9maWxlIGVtYWlsIiwic2lkIjoiMjk5OWZiODQtZDQ5OC00YzkzLTk0NTUtYjQ4ZTM2MjU4MWZiIiwiQWNlc3NhUmVwb3NpdG9yaW8iOiJPayIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJuYW1lIjoiRlJBTkNJU0NPIEJSVU5PIE5PQlJFIERFIE1FTE8iLCJwcmVmZXJyZWRfdXNlcm5hbWUiOiIwNjMzMzE0NTM2MCIsImdpdmVuX25hbWUiOiJGUkFOQ0lTQ08gQlJVTk8gTk9CUkUgREUgTUVMTyIsImNvcnBvcmF0aXZvIjpbeyJzZXFfdXN1YXJpbyI6MTY1MDIzNjcsIm5vbV91c3VhcmlvIjoiRlJBTkNJU0NPIEJSVU5PIE5PQlJFIERFIE1FTE8iLCJudW1fY3BmIjoiMDYzMzMxNDUzNjAiLCJzaWdfdGlwb19jYXJnbyI6IkFEViIsImZsZ19hdGl2byI6IlMiLCJzZXFfc2lzdGVtYSI6MCwic2VxX3BlcmZpbCI6MCwiZHNjX29yZ2FvIjoiT0FCIiwic2VxX3RyaWJ1bmFsX3BhaSI6MCwiZHNjX2VtYWlsIjoibWVsb2ZhY2RpcmVpdG9AaG90bWFpbC5jb20iLCJzZXFfb3JnYW9fZXh0ZXJubyI6MCwiZHNjX29yZ2FvX2V4dGVybm8iOiJPQUIiLCJvYWIiOiJDRTQ0Njc0In1dLCJlbWFpbCI6Im1lbG9mYWNkaXJlaXRvQGhvdG1haWwuY29tIn0.CIat1hLgqV9vyLnhPfO6gE2XgZX2jtpuKwHo9ESuY2SdMEvXI3BoG3X54ScF6Z8QUPQw32FZ_rM_N38MKaSAgMzQEys2yE6a4PqJ8O4UUQTQ1R64XWXogaKX2aQdEaaGKv_fpsP9I7l8Mx_D-rStC_6K-BGWyK12chiyuBD2R22MBjGu8cxVWFZyneRxRVIRhZxNjpeBkS5nrdM5DCtXPhx3WkhUkMuRjy6MUyrAwMuRq4vxgYnl9Ya1Qey-UfxMcxqj4EqDP1UlWTAD8x-zyi5nCBcMKIiYK3xOr2FT3FIBeeLebmaf3c7K-A8PgmV0U4dI_Ipg_lWf7T22OqiStg"
    
    # URL do documento do processo novo
    url = "https://portaldeservicos.pdpj.jus.br/api/v2/processos/1011745-77.2025.8.11.0041/documentos/2ddcbba6-255f-5653-a58e-a0d7561474f9/binario"
    
    logger.info(f"🔗 Testando documento do processo novo:")
    logger.info(f"   Processo: 1011745-77.2025.8.11.0041")
    logger.info(f"   UUID: 2ddcbba6-255f-5653-a58e-a0d7561474f9")
    logger.info(f"   URL: {url}")
    
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
            response = await client.get(url, headers=headers)
            
            logger.info(f"📊 Status: {response.status_code}")
            logger.info(f"📊 Content-Type: {response.headers.get('content-type', 'N/A')}")
            logger.info(f"📊 Content-Length: {response.headers.get('content-length', 'N/A')}")
            
            if response.status_code == 200:
                content = response.content
                logger.info(f"📊 Tamanho: {len(content)} bytes")
                
                if content.startswith(b'%PDF'):
                    logger.success("✅ PDF válido baixado!")
                    return True
                else:
                    logger.warning(f"⚠️ Não é PDF - Primeiros 100 bytes: {content[:100]}")
            elif response.status_code == 404:
                logger.error("❌ Documento não encontrado (404)")
                logger.warning("💡 Token pode não ter acesso a este processo/tribunal")
            elif response.status_code == 401:
                logger.error("❌ Token inválido ou expirado (401)")
            else:
                logger.error(f"❌ Erro {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Erro: {e}")
    
    return False

async def main():
    logger.info("🧪 Teste: Processo Novo vs Processo que Funcionou")
    logger.info("="*60)
    
    success = await test_document_from_new_process()
    
    if success:
        logger.success("\n✅ Documento do processo novo FUNCIONA!")
        logger.info("💡 Pode prosseguir com downloads!")
    else:
        logger.error("\n❌ Documento do processo novo NÃO funciona")
        logger.info("\n💡 Conclusão:")
        logger.info("   O teste isolado funcionou com processo: 5000315-75.2025.4.03.6327 (TRF3)")
        logger.info("   Este processo é: 1011745-77.2025.8.11.0041 (TJMT)")
        logger.info("   Possível causa: Token só tem acesso a processos de tribunais específicos")

if __name__ == "__main__":
    asyncio.run(main())

