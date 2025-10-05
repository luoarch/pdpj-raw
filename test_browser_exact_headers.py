#!/usr/bin/env python3
"""
Teste com headers EXATOS do navegador para download de documentos PDPJ.
Baseado na captura do Chrome DevTools fornecida pelo usuário.
"""

import asyncio
import httpx
import os
from loguru import logger
from typing import Dict, Any

# Configurar logging
logger.add("test_browser_exact_headers.log", rotation="1 MB")

# Token atualizado do navegador (mais recente)
TOKEN = "eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICI1dnJEZ1hCS21FLTdFb3J2a0U1TXU5VmxJZF9JU2dsMnY3QWYyM25EdkRVIn0.eyJleHAiOjE3NTk2OTU2MzMsImlhdCI6MTc1OTY2NjgzNCwiYXV0aF90aW1lIjoxNzU5NjY2ODMzLCJqdGkiOiI2Y2M1ZDZmMS0zZjEyLTRiYzUtODRlZC0zOTg0MmMwZDk4ZjciLCJpc3MiOiJodHRwczovL3Nzby5jbG91ZC5wamUuanVzLmJyL2F1dGgvcmVhbG1zL3BqZSIsImF1ZCI6WyJicm9rZXIiLCJhY2NvdW50Il0sInN1YiI6IjUwM2Y5ZTc3LWIzY2EtNGE2NC05MjA0LTBmMDJmNjdhZTZhOCIsInR5cCI6IkJlYXJlciIsImF6cCI6InBvcnRhbGV4dGVybm8tZnJvbnRlbmQiLCJub25jZSI6IjljNTA1MTgzLWVlMGUtNDljNy1iZTc2LWNhZjY1ZDg2MTNlMCIsInNlc3Npb25fc3RhdGUiOiIyNDBhNDdlNS1jMjQyLTQzMjAtYmYxZS1hNGE4ZDJkZjNhMTgiLCJhY3IiOiIxIiwiYWxsb3dlZC1vcmlnaW5zIjpbImh0dHBzOi8vcG9ydGFsZGVzZXJ2aWNvcy5wZHBqLmp1cy5iciJdLCJyZWFsbV9hY2Nlc3MiOnsicm9sZXMiOlsib2ZmbGluZV9hY2Nlc3MiLCJ1bWFfYXV0aG9yaXphdGlvbiJdfSwicmVzb3VyY2VfYWNjZXNzIjp7ImJyb2tlciI6eyJyb2xlcyI6WyJyZWFkLXRva2VuIl19LCJhY2NvdW50Ijp7InJvbGVzIjpbIm1hbmFnZS1hY2NvdW50IiwibWFuYWdlLWFjY291bnQtbGlua3MiLCJ2aWV3LXByb2ZpbGUiXX19LCJzY29wZSI6Im9wZW5pZCBwcm9maWxlIGVtYWlsIiwic2lkIjoiMjQwYTQ3ZTUtYzI0Mi00MzIwLWJmMWUtYTRhOGQyZGYzYTE4IiwiQWNlc3NhUmVwb3NpdG9yaW8iOiJPayIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJuYW1lIjoiRlJBTkNJU0NPIEJSVU5PIE5PQlJFIERFIE1FTE8iLCJwcmVmZXJyZWRfdXNlcm5hbWUiOiIwNjMzMzE0NTM2MCIsImdpdmVuX25hbWUiOiJGUkFOQ0lTQ08gQlJVTk8gTk9CUkUgREUgTUVMTyIsImNvcnBvcmF0aXZvIjpbeyJzZXFfdXN1YXJpbyI6MTY1MDIzNjcsIm5vbV91c3VhcmlvIjoiRlJBTkNJU0NPIEJSVU5PIE5PQlJFIERFIE1FTE8iLCJudW1fY3BmIjoiMDYzMzMxNDUzNjAiLCJzaWdfdGlwb19jYXJnbyI6IkFEViIsImZsZ19hdGl2byI6IlMiLCJzZXFfc2lzdGVtYSI6MCwic2VxX3BlcmZpbCI6MCwiZHNjX29yZ2FvIjoiT0FCIiwic2VxX3RyaWJ1bmFsX3BhaSI6MCwiZHNjX2VtYWlsIjoibWVsb2ZhY2RpcmVpdG9AaG90bWFpbC5jb20iLCJzZXFfb3JnYW9fZXh0ZXJubyI6MCwiZHNjX29yZ2FvX2V4dGVybm8iOiJPQUIiLCJvYWIiOiJDRTQ0Njc0In1dLCJlbWFpbCI6Im1lbG9mYWNkaXJlaXRvQGhvdG1haWwuY29tIn0.n4xg0xV6hTjycFFjOodxfd9ts3PyFwV0oTVkxOe_XRhxwrw2HTkARv3rfEEz-rUEUkZ_PDhLCKZoR-toe4xE-l8JgfErt1a3AXBPskdUWD3U0xzjuLkJf_-v-p60dQmN8OIQ_6F2xHzBZgWAXRqJBvZucZXGbgQrAXnt8Hx0JzUTLBRmVxIwXIc8jtpTHrES0VWBoAXK1HxhI-dIAGiPlWXyMekJKyZ7-chujnfj653qRR2B5kxZjtS-NKu3i_VvpHQMhnEV_OzjIpKK5XI_JbhsEv8L86TnhvU-TcGuLEsfr9Gx7X50-piELQ3jPsL3EeXUMO61T8UV4cKYIDQsZA"

# URL exata do teste (baseada na captura do DevTools)
TEST_URL = "https://portaldeservicos.pdpj.jus.br/api/v2/processos/5000315-75.2025.4.03.6327/documentos/41d3e2fd-bd4b-5737-ba8d-644292c5b09c/binario"

# Headers EXATOS do navegador (copiados do DevTools)
BROWSER_HEADERS = {
    "accept": "*/*",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "en-US,en;q=0.9,pt;q=0.8",
    "authorization": f"Bearer {TOKEN}",
    "cookie": "tour-primeira-notificacao-%2Fconsulta=true; tour-primeira-notificacao-%2Fhome=true; tour-primeira-notificacao-%2Fconsulta%2Fautosdigitais=true; JSESSIONID=EE1393D2A4345F83FC30E4FF25B440F3",
    "priority": "u=1, i",
    "referer": "https://portaldeservicos.pdpj.jus.br/consulta/autosdigitais?processo=5000315-75.2025.4.03.6327&dataDistribuicao=20250130131052",
    "sec-ch-ua": '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
}


async def test_browser_exact_headers():
    """Testa download com headers exatos do navegador."""
    
    logger.info("🎯 Teste com Headers Exatos do Navegador")
    logger.info("=" * 60)
    logger.info(f"🔗 URL: {TEST_URL}")
    logger.info(f"🍪 Cookie JSESSIONID: EE1393D2A4345F83FC30E4FF25B440F3")
    logger.info(f"🔗 Referer: {BROWSER_HEADERS['referer']}")
    logger.info("=" * 60)
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Fazer requisição com headers exatos do navegador
            response = await client.get(TEST_URL, headers=BROWSER_HEADERS)
            
            logger.info(f"📊 Status: {response.status_code}")
            logger.info(f"📊 Content-Type: {response.headers.get('content-type', 'N/A')}")
            logger.info(f"📊 Content-Length: {response.headers.get('content-length', 'N/A')}")
            logger.info(f"📊 Content-Disposition: {response.headers.get('content-disposition', 'N/A')}")
            
            # Verificar se é PDF
            content = response.content
            logger.info(f"📊 Tamanho do conteúdo: {len(content)} bytes")
            
            if content.startswith(b'%PDF'):
                logger.success("✅ PDF VÁLIDO DETECTADO!")
                logger.info(f"📄 Início do PDF: {content[:50]}")
                
                # Salvar PDF
                os.makedirs("data/browser_downloads", exist_ok=True)
                filename = "data/browser_downloads/sentenca_browser_headers.pdf"
                with open(filename, 'wb') as f:
                    f.write(content)
                logger.success(f"💾 PDF salvo em: {filename}")
                
                return True
                
            elif content.startswith(b'<html') or b'<html' in content[:1000]:
                logger.warning("⚠️ HTML retornado (não é PDF)")
                logger.info(f"📄 Início do HTML: {content[:200].decode('utf-8', errors='ignore')}")
                
                # Salvar HTML para análise
                os.makedirs("data/browser_downloads", exist_ok=True)
                filename = "data/browser_downloads/sentenca_browser_headers.html"
                with open(filename, 'wb') as f:
                    f.write(content)
                logger.info(f"💾 HTML salvo em: {filename}")
                
                return False
                
            else:
                logger.info(f"📄 Tipo de conteúdo desconhecido")
                logger.info(f"📄 Início: {content[:100]}")
                
                # Salvar para análise
                os.makedirs("data/browser_downloads", exist_ok=True)
                filename = "data/browser_downloads/sentenca_browser_headers_unknown.bin"
                with open(filename, 'wb') as f:
                    f.write(content)
                logger.info(f"💾 Conteúdo salvo em: {filename}")
                
                return False
                
    except Exception as e:
        logger.error(f"❌ Erro na requisição: {e}")
        return False


async def test_multiple_documents():
    """Testa múltiplos documentos com headers do navegador."""
    
    # Lista de documentos para testar (baseados nos dados do processo)
    documents = [
        {
            "nome": "Sentença.html",
            "url": "https://portaldeservicos.pdpj.jus.br/api/v2/processos/5000315-75.2025.4.03.6327/documentos/41d3e2fd-bd4b-5737-ba8d-644292c5b09c/binario",
            "tipo_esperado": "HTML"
        },
        {
            "nome": "Pedido de Desistência.pdf", 
            "url": "https://portaldeservicos.pdpj.jus.br/api/v2/processos/5000315-75.2025.4.03.6327/documentos/bafbfdb2-ab94-5ca0-9cb3-b6e80376a632/binario",
            "tipo_esperado": "PDF"
        },
        {
            "nome": "Petição Intercorrente.pdf",
            "url": "https://portaldeservicos.pdpj.jus.br/api/v2/processos/5000315-75.2025.4.03.6327/documentos/59a2dbcc-bb58-5281-a656-cfe57861c2db/binario", 
            "tipo_esperado": "PDF"
        }
    ]
    
    logger.info("🎯 Teste de Múltiplos Documentos com Headers do Navegador")
    logger.info("=" * 80)
    
    results = []
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for i, doc in enumerate(documents, 1):
            logger.info(f"\n📄 Teste {i}: {doc['nome']}")
            logger.info(f"🔗 URL: {doc['url']}")
            logger.info(f"📋 Tipo esperado: {doc['tipo_esperado']}")
            logger.info("-" * 60)
            
            try:
                response = await client.get(doc['url'], headers=BROWSER_HEADERS)
                content = response.content
                
                logger.info(f"📊 Status: {response.status_code}")
                logger.info(f"📊 Content-Type: {response.headers.get('content-type', 'N/A')}")
                logger.info(f"📊 Tamanho: {len(content)} bytes")
                
                # Determinar tipo de conteúdo
                if content.startswith(b'%PDF'):
                    content_type = "PDF"
                    extension = "pdf"
                elif content.startswith(b'<html') or b'<html' in content[:1000]:
                    content_type = "HTML"
                    extension = "html"
                else:
                    content_type = "UNKNOWN"
                    extension = "bin"
                
                logger.info(f"📊 Tipo detectado: {content_type}")
                
                # Salvar arquivo
                os.makedirs("data/browser_downloads", exist_ok=True)
                filename = f"data/browser_downloads/{i:02d}_{doc['nome'].replace(' ', '_').replace('.', '_')}.{extension}"
                with open(filename, 'wb') as f:
                    f.write(content)
                logger.success(f"💾 Arquivo salvo: {filename}")
                
                results.append({
                    "nome": doc['nome'],
                    "tipo_esperado": doc['tipo_esperado'],
                    "tipo_detectado": content_type,
                    "tamanho": len(content),
                    "status": response.status_code,
                    "sucesso": content_type == doc['tipo_esperado']
                })
                
            except Exception as e:
                logger.error(f"❌ Erro no documento {doc['nome']}: {e}")
                results.append({
                    "nome": doc['nome'],
                    "erro": str(e),
                    "sucesso": False
                })
    
    # Resumo dos resultados
    logger.info("\n📊 RESUMO DOS RESULTADOS:")
    logger.info("=" * 60)
    
    sucessos = sum(1 for r in results if r.get('sucesso', False))
    total = len(results)
    
    logger.info(f"✅ Sucessos: {sucessos}/{total}")
    
    for result in results:
        if result.get('sucesso', False):
            logger.success(f"✅ {result['nome']}: {result['tipo_detectado']} ({result['tamanho']} bytes)")
        else:
            logger.error(f"❌ {result['nome']}: {result.get('erro', 'Falhou')}")
    
    return results


async def main():
    """Função principal."""
    logger.info("🚀 Iniciando Teste com Headers Exatos do Navegador")
    logger.info("=" * 80)
    
    # Teste 1: Documento específico (Sentença)
    logger.info("🎯 TESTE 1: Documento Específico (Sentença)")
    success1 = await test_browser_exact_headers()
    
    # Teste 2: Múltiplos documentos
    logger.info("\n🎯 TESTE 2: Múltiplos Documentos")
    results = await test_multiple_documents()
    
    # Resultado final
    logger.info("\n🏁 RESULTADO FINAL:")
    logger.info("=" * 60)
    
    if success1:
        logger.success("🎉 SUCESSO! Headers do navegador funcionam para download!")
        logger.info("💡 A chave está nos cookies JSESSIONID e referer corretos")
    else:
        logger.warning("⚠️ Ainda não funcionou com headers do navegador")
    
    sucessos = sum(1 for r in results if r.get('sucesso', False))
    total = len(results)
    logger.info(f"📊 Taxa de sucesso: {sucessos}/{total} ({sucessos/total*100:.1f}%)")


if __name__ == "__main__":
    asyncio.run(main())
