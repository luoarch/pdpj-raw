#!/usr/bin/env python3
"""
Script para testar com o token atualizado
"""

import asyncio
import httpx
import os
from loguru import logger

# Configurar logging
logger.add("test_updated_token.log", rotation="1 MB")

# Base URL da API PDPJ
BASE_URL = "https://portaldeservicos.pdpj.jus.br"

# Token PDPJ atualizado (você deve atualizar este valor)
TOKEN = "eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICI1dnJEZ1hCS21FLTdFb3J2a0U1TXU5VmxJZF9JU2dsMnY3QWYyM25EdkRVIn0.eyJleHAiOjE3NTk2NTYyNjIsImlhdCI6MTc1OTYyNzQ2MywiYXV0aF90aW1lIjoxNzU5NjI3NDM3LCJqdGkiOiI4ZjUxOTAzMi0yNjQ3LTRmN2YtOTQxOS04ZGVjMWRmYzcxNzciLCJpc3MiOiJodHRwczovL3Nzby5jbG91ZC5wamUuanVzLmJyL2F1dGgvcmVhbG1zL3BqZSIsImF1ZCI6WyJicm9rZXIiLCJhY2NvdW50Il0sInN1YiI6IjUwM2Y5ZTc3LWIzY2EtNGE2NC05MjA0LTBmMDJmNjdhZTZhOCIsInR5cCI6IkJlYXJlciIsImF6cCI6InBvcnRhbGV4dGVybm8tZnJvbnRlbmQiLCJub25jZSI6ImMxNTdkYTY2LTY1YzctNDdjMC05ZGFhLWJkOGM3NzdlMDczYiIsInNlc3Npb25fc3RhdGUiOiIwOWRhODhjNC05NTA4LTQ0ZjktYTdmYi1lODk1Yzc4YTI5NmIiLCJhY3IiOiIwIiwiYWxsb3dlZC1vcmlnaW5zIjpbImh0dHBzOi8vcG9ydGFsZGVzZXJ2aWNvcy5wZHBqLmp1cy5iciJdLCJyZWFsbV9hY2Nlc3MiOnsicm9sZXMiOlsib2ZmbGluZV9hY2Nlc3MiLCJ1bWFfYXV0aG9yaXphdGlvbiJdfSwicmVzb3VyY2VfYWNjZXNzIjp7ImJyb2tlciI6eyJyb2xlcyI6WyJyZWFkLXRva2VuIl19LCJhY2NvdW50Ijp7InJvbGVzIjpbIm1hbmFnZS1hY2NvdW50IiwibWFuYWdlLWFjY291bnQtbGlua3MiLCJ2aWV3LXByb2ZpbGUiXX19LCJzY29wZSI6Im9wZW5pZCBwcm9maWxlIGVtYWlsIiwic2lkIjoiMDlkYTg4YzQtOTUwOC00NGY5LWE3ZmItZTg5NWM3OGEyOTZiIiwiQWNlc3NhUmVwb3NpdG9yaW8iOiJPayIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJuYW1lIjoiRlJBTkNJU0NPIEJSVU5PIE5PQlJFIERFIE1FTE8iLCJwcmVmZXJyZWRfdXNlcm5hbWUiOiIwNjMzMzE0NTM2MCIsImdpdmVuX25hbWUiOiJGUkFOQ0lTQ08gQlJVTk8gTk9CUkUgREUgTUVMTyIsImNvcnBvcmF0aXZvIjpbeyJzZXFfdXN1YXJpbyI6MTY1MDIzNjcsIm5vbV91c3VhcmlvIjoiRlJBTkNJU0NPIEJSVU5PIE5PQlJFIERFIE1FTE8iLCJudW1fY3BmIjoiMDYzMzMxNDUzNjAiLCJzaWdfdGlwb19jYXJnbyI6IkFEViIsImZsZ19hdGl2byI6IlMiLCJzZXFfc2lzdGVtYSI6MCwic2VxX3BlcmZpbCI6MCwiZHNjX29yZ2FvIjoiT0FCIiwic2VxX3RyaWJ1bmFsX3BhaSI6MCwiZHNjX2VtYWlsIjoibWVsb2ZhY2RpcmVpdG9AaG90bWFpbC5jb20iLCJzZXFfb3JnYW9fZXh0ZXJubyI6MCwiZHNjX29yZ2FvX2V4dGVybm8iOiJPQUIiLCJvYWIiOiJDRTQ0Njc0In1dLCJlbWFpbCI6Im1lbG9mYWNkaXJlaXRvQGhvdG1haWwuY29tIn0.RMK9Wu6irZ_QawfQ3yF-xP-W8vKfPP4hj1q5cKyZCTdPIWxA4RsAjEa83450IwqHht07gGOyNbCAjSUXcTIanIdj41Xe8t9N3rfXuBaBxO2WSmqWNlI_NF0S3NG_9Atd5fmo5qv2NluknGPtWDwk3NZjeC3vDc7qqk5-tJwJ3BnJoXvutcnNkDUWtstV0Q14itDoOERvdbMPqwcoJMotUD7ZYGa43PpP--sCx2YMTBBqzI8pqmILqAbyh0JpiCcse6zlpcgfQm8gqjO8Gm-JelCN7Kb9EUFUjvCIBxNIdrc7mhKZ-Mr7x_gMHEldrpGPESIiXTWDKbF3H62RFlpGZg"

# Documento de teste
TEST_DOCUMENT = {
    "nome": "Petição Inicial",
    "hrefBinario": "/processos/1000145-91.2023.8.26.0597/documentos/ea480b7f-fac4-5c2c-a46f-c5d36f5d4335/binario",
    "document_id": "ea480b7f-fac4-5c2c-a46f-c5d36f5d4335"
}

async def test_updated_token():
    """Testar com o token atualizado."""
    logger.info("🔍 Testando com token atualizado")
    
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "User-Agent": "PDPJ-API-Client/1.0",
        "Accept": "*/*"
    }
    
    # Criar diretório para salvar arquivos
    output_dir = "data/updated_token_test"
    os.makedirs(output_dir, exist_ok=True)
    
    # URL completa
    full_url = f"{BASE_URL}{TEST_DOCUMENT['hrefBinario']}"
    logger.info(f"🔗 URL: {full_url}")
    
    async with httpx.AsyncClient(verify=False, timeout=60.0) as client:
        try:
            response = await client.get(full_url, headers=headers)
            
            # Salvar conteúdo bruto
            filename = f"{TEST_DOCUMENT['document_id']}_{TEST_DOCUMENT['nome'].replace(' ', '_')}.raw"
            filepath = os.path.join(output_dir, filename)
            
            with open(filepath, "wb") as f:
                f.write(response.content)
            
            # Analisar o conteúdo
            content_type = response.headers.get("content-type", "N/A")
            content_length = len(response.content)
            content_preview = response.content[:200] if content_length > 0 else b""
            
            logger.info(f"📊 Status: {response.status_code}")
            logger.info(f"📊 Content-Type: {content_type}")
            logger.info(f"📊 Content-Length: {content_length}")
            logger.info(f"💾 Salvo em: {filepath}")
            
            # Detectar tipo de conteúdo
            if response.content.startswith(b'%PDF'):
                logger.info("✅ PDF válido detectado!")
                return True
            elif response.content.startswith(b'<!DOCTYPE html') or response.content.startswith(b'<html'):
                logger.warning("⚠️ Ainda retorna HTML")
                logger.info(f"🔍 Preview: {content_preview.decode('utf-8', errors='ignore')[:100]}")
                return False
            elif response.content.startswith(b'{') or response.content.startswith(b'['):
                logger.info("📄 JSON detectado")
                logger.info(f"🔍 Preview: {content_preview.decode('utf-8', errors='ignore')[:100]}")
                return False
            else:
                logger.info("🔧 Conteúdo binário detectado")
                logger.info(f"🔍 Preview (hex): {content_preview.hex()[:50]}...")
                return True
                
        except Exception as e:
            logger.error(f"❌ Erro: {e}")
            return False

async def test_multiple_endpoints():
    """Testar múltiplos endpoints com o token atualizado."""
    logger.info("🔄 Testando múltiplos endpoints")
    
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "User-Agent": "PDPJ-API-Client/1.0",
        "Accept": "*/*"
    }
    
    document_id = TEST_DOCUMENT['document_id']
    process_number = "1000145-91.2023.8.26.0597"
    
    # URLs para testar
    test_urls = [
        f"{BASE_URL}{TEST_DOCUMENT['hrefBinario']}",
        f"{BASE_URL}/processos/{process_number}/documentos/{document_id}",
        f"{BASE_URL}/processos/{process_number}/documentos/{document_id}/download",
        f"{BASE_URL}/api/v2/processos/{process_number}/documentos/{document_id}",
        f"{BASE_URL}/api/v2/processos/{process_number}/documentos/{document_id}/binario"
    ]
    
    results = []
    
    async with httpx.AsyncClient(verify=False, timeout=60.0) as client:
        for i, url in enumerate(test_urls, 1):
            logger.info(f"📄 Teste {i}/{len(test_urls)}: {url}")
            
            try:
                response = await client.get(url, headers=headers)
                
                content_type = response.headers.get("content-type", "N/A")
                content_length = len(response.content)
                
                result = {
                    "url": url,
                    "status_code": response.status_code,
                    "content_type": content_type,
                    "content_length": content_length,
                    "is_pdf": response.content.startswith(b'%PDF'),
                    "is_html": response.content.startswith(b'<!DOCTYPE html') or response.content.startswith(b'<html'),
                    "is_json": response.content.startswith(b'{') or response.content.startswith(b'['),
                    "is_binary": not any([
                        response.content.startswith(b'<!DOCTYPE html'),
                        response.content.startswith(b'<html'),
                        response.content.startswith(b'{'),
                        response.content.startswith(b'[')
                    ]) and content_length > 0
                }
                
                if result["is_pdf"]:
                    logger.info(f"✅ PDF válido ({content_length} bytes)")
                elif result["is_html"]:
                    logger.warning(f"⚠️ HTML ({content_length} bytes)")
                elif result["is_json"]:
                    logger.info(f"📄 JSON ({content_length} bytes)")
                elif result["is_binary"]:
                    logger.info(f"🔧 Binário ({content_length} bytes)")
                else:
                    logger.warning(f"❓ Tipo desconhecido ({content_length} bytes)")
                
                results.append(result)
                
            except Exception as e:
                logger.error(f"❌ Erro: {e}")
                results.append({
                    "url": url,
                    "error": str(e)
                })
            
            # Pequena pausa entre requests
            await asyncio.sleep(0.5)
    
    return results

async def main():
    """Função principal."""
    logger.info("🚀 Testando com token atualizado")
    
    # Verificar se o token foi atualizado
    if TOKEN == "SEU_TOKEN_ATUALIZADO_AQUI":
        logger.error("❌ Por favor, atualize o TOKEN no script antes de executar")
        return
    
    # Teste 1: Endpoint principal
    logger.info("=" * 60)
    logger.info("TESTE 1: Endpoint principal")
    logger.info("=" * 60)
    success = await test_updated_token()
    
    if success:
        logger.info("🎉 Sucesso! Documento baixado como PDF ou binário")
    else:
        logger.info("⚠️ Ainda retorna HTML ou outro formato")
    
    # Teste 2: Múltiplos endpoints
    logger.info("\n" + "=" * 60)
    logger.info("TESTE 2: Múltiplos endpoints")
    logger.info("=" * 60)
    results = await test_multiple_endpoints()
    
    # Análise dos resultados
    logger.info("\n📊 ANÁLISE DOS RESULTADOS:")
    for result in results:
        if "error" not in result:
            status = "✅ PDF" if result.get("is_pdf") else "🔧 BINÁRIO" if result.get("is_binary") else "📄 JSON" if result.get("is_json") else "⚠️ HTML"
            logger.info(f"  {status} {result['url']} - {result.get('content_length', 0)} bytes")
    
    # Salvar resultados
    with open("updated_token_test_results.json", "w") as f:
        import json
        json.dump({"teste_1_sucesso": success, "teste_2_resultados": results}, f, indent=2, ensure_ascii=False)
    
    logger.info("💾 Resultados salvos em updated_token_test_results.json")
    logger.info("🏁 Teste concluído")

if __name__ == "__main__":
    asyncio.run(main())
