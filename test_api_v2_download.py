#!/usr/bin/env python3
"""
Script para testar download usando /api/v2/ como na requisição que funcionou
"""

import asyncio
import httpx
from loguru import logger

# Configurar logging
logger.add("test_api_v2_download.log", rotation="1 MB")

async def test_api_v2_download():
    """Testar download usando /api/v2/ no caminho"""
    
    # Token e dados de teste (mesmo da requisição que funcionou)
    token = "eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICI1dnJEZ1hCS21FLTdFb3J2a0U1TXU5VmxJZF9JU2dsMnY3QWYyM25EdkRVIn0.eyJleHAiOjE3NTk3NzQ1MzcsImlhdCI6MTc1OTc0NTczNywiYXV0aF90aW1lIjoxNzU5NzQ1NjYyLCJqdGkiOiIyOWUzYzVjYy0yYzUyLTRjMGQtOTNjMC03OGVmNzQ5ZjNlZTgiLCJpc3MiOiJodHRwczovL3Nzby5jbG91ZC5wamUuanVzLmJyL2F1dGgvcmVhbG1zL3BqZSIsImF1ZCI6WyJicm9rZXIiLCJhY2NvdW50Il0sInN1YiI6IjUwM2Y5ZTc3LWIzY2EtNGE2NC05MjA0LTBmMDJmNjdhZTZhOCIsInR5cCI6IkJlYXJlciIsImF6cCI6InBvcnRhbGV4dGVybm8tZnJvbnRlbmQiLCJub25jZSI6Ijc3ODA2YTdiLTI1ZTItNGMwYi1hMTQ4LTllNDUzMzY3MDBmOSIsInNlc3Npb25fc3RhdGUiOiIyOTk5ZmI4NC1kNDk4LTRjOTMtOTQ1NS1iNDhlMzYyNTgxZmIiLCJhY3IiOiIwIiwiYWxsb3dlZC1vcmlnaW5zIjpbImh0dHBzOi8vcG9ydGFsZGVzZXJ2aWNvcy5wZHBqLmp1cy5iciJdLCJyZWFsbV9hY2Nlc3MiOnsicm9sZXMiOlsib2ZmbGluZV9hY2Nlc3MiLCJ1bWFfYXV0aG9yaXphdGlvbiJdfSwicmVzb3VyY2VfYWNjZXNzIjp7ImJyb2tlciI6eyJyb2xlcyI6WyJyZWFkLXRva2VuIl19LCJhY2NvdW50Ijp7InJvbGVzIjpbIm1hbmFnZS1hY2NvdW50IiwibWFuYWdlLWFjY291bnQtbGlua3MiLCJ2aWV3LXByb2ZpbGUiXX19LCJzY29wZSI6Im9wZW5pZCBwcm9maWxlIGVtYWlsIiwic2lkIjoiMjk5OWZiODQtZDQ5OC00YzkzLTk0NTUtYjQ4ZTM2MjU4MWZiIiwiQWNlc3NhUmVwb3NpdG9yaW8iOiJPayIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJuYW1lIjoiRlJBTkNJU0NPIEJSVU5PIE5PQlJFIERFIE1FTE8iLCJwcmVmZXJyZWRfdXNlcm5hbWUiOiIwNjMzMzE0NTM2MCIsImdpdmVuX25hbWUiOiJGUkFOQ0lTQ08gQlJVTk8gTk9CUkUgREUgTUVMTyIsImNvcnBvcmF0aXZvIjpbeyJzZXFfdXN1YXJpbyI6MTY1MDIzNjcsIm5vbV91c3VhcmlvIjoiRlJBTkNJU0NPIEJSVU5PIE5PQlJFIERFIE1FTE8iLCJudW1fY3BmIjoiMDYzMzMxNDUzNjAiLCJzaWdfdGlwb19jYXJnbyI6IkFEViIsImZsZ19hdGl2byI6IlMiLCJzZXFfc2lzdGVtYSI6MCwic2VxX3BlcmZpbCI6MCwiZHNjX29yZ2FvIjoiT0FCIiwic2VxX3RyaWJ1bmFsX3BhaSI6MCwiZHNjX2VtYWlsIjoibWVsb2ZhY2RpcmVpdG9AaG90bWFpbC5jb20iLCJzZXFfb3JnYW9fZXh0ZXJubyI6MCwiZHNjX29yZ2FvX2V4dGVybm8iOiJPQUIiLCJvYWIiOiJDRTQ0Njc0In1dLCJlbWFpbCI6Im1lbG9mYWNkaXJlaXRvQGhvdG1haWwuY29tIn0.CIat1hLgqV9vyLnhPfO6gE2XgZX2jtpuKwHo9ESuY2SdMEvXI3BoG3X54ScF6Z8QUPQw32FZ_rM_N38MKaSAgMzQEys2yE6a4PqJ8O4UUQTQ1R64XWXogaKX2aQdEaaGKv_fpsP9I7l8Mx_D-rStC_6K-BGWyK12chiyuBD2R22MBjGu8cxVWFZyneRxRVIRhZxNjpeBkS5nrdM5DCtXPhx3WkhUkMuRjy6MUyrAwMuRq4vxgYnl9Ya1Qey-UfxMcxqj4EqDP1UlWTAD8x-zyi5nCBcMKIiYK3xOr2FT3FIBeeLebmaf3c7K-A8PgmV0U4dI_Ipg_lWf7T22OqiStg"
    
    # Dados do teste
    process_number = "5000315-75.2025.4.03.6327"
    document_id = "59a2dbcc-bb58-5281-a656-cfe57861c2db"
    
    # URL usando /api/v2/ (formato correto!)
    url = f"https://portaldeservicos.pdpj.jus.br/api/v2/processos/{process_number}/documentos/{document_id}/binario"
    
    logger.info(f"🔍 Testando URL: {url}")
    
    # Headers exatamente como na requisição que funcionou
    headers = {
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "en-US,en;q=0.9,pt;q=0.8",
        "authorization": f"Bearer {token}",
        "cookie": "tour-primeira-notificacao-%2Fconsulta=true; tour-primeira-notificacao-%2Fhome=true; tour-primeira-notificacao-%2Fconsulta%2Fautosdigitais=true; JSESSIONID=3874E11A1A52B4280AB445D4B4D2E6C0",
        "priority": "u=1, i",
        "referer": f"https://portaldeservicos.pdpj.jus.br/consulta/autosdigitais?processo={process_number}&dataDistribuicao=20250130131052",
        "sec-ch-ua": '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            logger.info("📡 Fazendo requisição...")
            response = await client.get(url, headers=headers)
            
            logger.info(f"📊 Status: {response.status_code}")
            logger.info(f"📊 Content-Type: {response.headers.get('content-type', 'N/A')}")
            logger.info(f"📊 Content-Length: {response.headers.get('content-length', 'N/A')}")
            logger.info(f"📊 Content-Disposition: {response.headers.get('content-disposition', 'N/A')}")
            
            if response.status_code == 200:
                content = response.content
                logger.info(f"📊 Tamanho do conteúdo: {len(content)} bytes")
                
                # Verificar se é PDF
                if content.startswith(b'%PDF'):
                    logger.info("✅ SUCESSO! PDF válido baixado!")
                    
                    # Salvar PDF
                    filename = f"test_api_v2_download_{document_id}.pdf"
                    with open(filename, "wb") as f:
                        f.write(content)
                    logger.info(f"💾 PDF salvo como: {filename}")
                    
                    return True
                else:
                    logger.warning("⚠️ Não é PDF")
                    logger.info(f"🔍 Primeiros 200 bytes: {content[:200]}")
            else:
                logger.error(f"❌ Erro: {response.status_code}")
                logger.error(f"🔍 Resposta: {response.text[:500]}")
                
        except Exception as e:
            logger.error(f"❌ Erro: {e}")
            return False
    
    return False

async def test_another_document():
    """Testar com outro documento para confirmar que funciona de forma consistente"""
    
    token = "eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICI1dnJEZ1hCS21FLTdFb3J2a0U1TXU5VmxJZF9JU2dsMnY3QWYyM25EdkRVIn0.eyJleHAiOjE3NTk3NzQ1MzcsImlhdCI6MTc1OTc0NTczNywiYXV0aF90aW1lIjoxNzU5NzQ1NjYyLCJqdGkiOiIyOWUzYzVjYy0yYzUyLTRjMGQtOTNjMC03OGVmNzQ5ZjNlZTgiLCJpc3MiOiJodHRwczovL3Nzby5jbG91ZC5wamUuanVzLmJyL2F1dGgvcmVhbG1zL3BqZSIsImF1ZCI6WyJicm9rZXIiLCJhY2NvdW50Il0sInN1YiI6IjUwM2Y5ZTc3LWIzY2EtNGE2NC05MjA0LTBmMDJmNjdhZTZhOCIsInR5cCI6IkJlYXJlciIsImF6cCI6InBvcnRhbGV4dGVybm8tZnJvbnRlbmQiLCJub25jZSI6Ijc3ODA2YTdiLTI1ZTItNGMwYi1hMTQ4LTllNDUzMzY3MDBmOSIsInNlc3Npb25fc3RhdGUiOiIyOTk5ZmI4NC1kNDk4LTRjOTMtOTQ1NS1iNDhlMzYyNTgxZmIiLCJhY3IiOiIwIiwiYWxsb3dlZC1vcmlnaW5zIjpbImh0dHBzOi8vcG9ydGFsZGVzZXJ2aWNvcy5wZHBqLmp1cy5iciJdLCJyZWFsbV9hY2Nlc3MiOnsicm9sZXMiOlsib2ZmbGluZV9hY2Nlc3MiLCJ1bWFfYXV0aG9yaXphdGlvbiJdfSwicmVzb3VyY2VfYWNjZXNzIjp7ImJyb2tlciI6eyJyb2xlcyI6WyJyZWFkLXRva2VuIl19LCJhY2NvdW50Ijp7InJvbGVzIjpbIm1hbmFnZS1hY2NvdW50IiwibWFuYWdlLWFjY291bnQtbGlua3MiLCJ2aWV3LXByb2ZpbGUiXX19LCJzY29wZSI6Im9wZW5pZCBwcm9maWxlIGVtYWlsIiwic2lkIjoiMjk5OWZiODQtZDQ5OC00YzkzLTk0NTUtYjQ4ZTM2MjU4MWZiIiwiQWNlc3NhUmVwb3NpdG9yaW8iOiJPayIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJuYW1lIjoiRlJBTkNJU0NPIEJSVU5PIE5PQlJFIERFIE1FTE8iLCJwcmVmZXJyZWRfdXNlcm5hbWUiOiIwNjMzMzE0NTM2MCIsImdpdmVuX25hbWUiOiJGUkFOQ0lTQ08gQlJVTk8gTk9CUkUgREUgTUVMTyIsImNvcnBvcmF0aXZvIjpbeyJzZXFfdXN1YXJpbyI6MTY1MDIzNjcsIm5vbV91c3VhcmlvIjoiRlJBTkNJU0NPIEJSVU5PIE5PQlJFIERFIE1FTE8iLCJudW1fY3BmIjoiMDYzMzMxNDUzNjAiLCJzaWdfdGlwb19jYXJnbyI6IkFEViIsImZsZ19hdGl2byI6IlMiLCJzZXFfc2lzdGVtYSI6MCwic2VxX3BlcmZpbCI6MCwiZHNjX29yZ2FvIjoiT0FCIiwic2VxX3RyaWJ1bmFsX3BhaSI6MCwiZHNjX2VtYWlsIjoibWVsb2ZhY2RpcmVpdG9AaG90bWFpbC5jb20iLCJzZXFfb3JnYW9fZXh0ZXJubyI6MCwiZHNjX29yZ2FvX2V4dGVybm8iOiJPQUIiLCJvYWIiOiJDRTQ0Njc0In1dLCJlbWFpbCI6Im1lbG9mYWNkaXJlaXRvQGhvdG1haWwuY29tIn0.CIat1hLgqV9vyLnhPfO6gE2XgZX2jtpuKwHo9ESuY2SdMEvXI3BoG3X54ScF6Z8QUPQw32FZ_rM_N38MKaSAgMzQEys2yE6a4PqJ8O4UUQTQ1R64XWXogaKX2aQdEaaGKv_fpsP9I7l8Mx_D-rStC_6K-BGWyK12chiyuBD2R22MBjGu8cxVWFZyneRxRVIRhZxNjpeBkS5nrdM5DCtXPhx3WkhUkMuRjy6MUyrAwMuRq4vxgYnl9Ya1Qey-UfxMcxqj4EqDP1UlWTAD8x-zyi5nCBcMKIiYK3xOr2FT3FIBeeLebmaf3c7K-A8PgmV0U4dI_Ipg_lWf7T22OqiStg"
    
    # Usar o processo do teste original
    process_number = "5029295-47.2024.4.03.6301"
    document_id = "333049132"
    
    url = f"https://portaldeservicos.pdpj.jus.br/api/v2/processos/{process_number}/documentos/{document_id}/binario"
    
    logger.info(f"\n🔍 Testando segundo documento: {url}")
    
    headers = {
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "en-US,en;q=0.9,pt;q=0.8",
        "authorization": f"Bearer {token}",
        "priority": "u=1, i",
        "referer": f"https://portaldeservicos.pdpj.jus.br/consulta/autosdigitais?processo={process_number}",
        "sec-ch-ua": '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            logger.info("📡 Fazendo requisição...")
            response = await client.get(url, headers=headers)
            
            logger.info(f"📊 Status: {response.status_code}")
            logger.info(f"📊 Content-Type: {response.headers.get('content-type', 'N/A')}")
            logger.info(f"📊 Content-Length: {response.headers.get('content-length', 'N/A')}")
            
            if response.status_code == 200:
                content = response.content
                logger.info(f"📊 Tamanho do conteúdo: {len(content)} bytes")
                
                if content.startswith(b'%PDF'):
                    logger.info("✅ SUCESSO! PDF válido baixado!")
                    filename = f"test_api_v2_download_{document_id}.pdf"
                    with open(filename, "wb") as f:
                        f.write(content)
                    logger.info(f"💾 PDF salvo como: {filename}")
                    return True
                else:
                    logger.warning("⚠️ Não é PDF")
                    logger.info(f"🔍 Primeiros 200 bytes: {content[:200]}")
            else:
                logger.error(f"❌ Erro: {response.status_code}")
                logger.error(f"🔍 Resposta: {response.text[:500]}")
                
        except Exception as e:
            logger.error(f"❌ Erro: {e}")
            return False
    
    return False

async def main():
    """Função principal"""
    logger.info("🚀 Iniciando testes com /api/v2/")
    
    # Teste 1: Documento que sabemos que funciona
    logger.info("\n" + "="*60)
    logger.info("Teste 1: Documento conhecido")
    logger.info("="*60)
    success1 = await test_api_v2_download()
    
    # Teste 2: Outro documento
    logger.info("\n" + "="*60)
    logger.info("Teste 2: Documento do teste original")
    logger.info("="*60)
    success2 = await test_another_document()
    
    # Resumo
    logger.info("\n" + "="*60)
    logger.info("RESUMO DOS TESTES")
    logger.info("="*60)
    logger.info(f"Teste 1: {'✅ SUCESSO' if success1 else '❌ FALHOU'}")
    logger.info(f"Teste 2: {'✅ SUCESSO' if success2 else '❌ FALHOU'}")
    
    if success1 or success2:
        logger.info("\n💡 CONCLUSÃO: /api/v2/ FUNCIONA!")
        logger.info("📝 Próximo passo: Atualizar o código para usar /api/v2/")
    else:
        logger.error("\n❌ Nenhum teste funcionou. Verificar token ou outros parâmetros.")
    
    logger.info("\n🏁 Testes concluídos")

if __name__ == "__main__":
    asyncio.run(main())

