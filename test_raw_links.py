#!/usr/bin/env python3
"""
Script para acessar links e salvar o que quer que seja retornado
"""

import asyncio
import httpx
import os
from loguru import logger
from typing import Dict, Any

# Configurar logging
logger.add("test_raw_links.log", rotation="1 MB")

# Base URL da API PDPJ
BASE_URL = "https://portaldeservicos.pdpj.jus.br"

# Token PDPJ
TOKEN = "eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICI1dnJEZ1hCS21FLTdFb3J2a0U1TXU5VmxJZF9JU2dsMnY3QWYyM25EdkRVIn0.eyJleHAiOjE3NTk2MjYzNDMsImlhdCI6MTc1OTYxMTA0OSwiYXV0aF90aW1lIjoxNzU5NTgzMTQzLCJqdGkiOiJiM2IzZGYxMC1mNjZmLTQzMmUtODAyZi0yNDk3MDU5NGEzZTEiLCJpc3MiOiJodHRwczovL3Nzby5jbG91ZC5wamUuanVzLmJyL2F1dGgvcmVhbG1zL3BqZSIsImF1ZCI6WyJicm9rZXIiLCJhY2NvdW50Il0sInN1YiI6IjUwM2Y5ZTc3LWIzY2EtNGE2NC05MjA0LTBmMDJmNjdhZTZhOCIsInR5cCI6IkJlYXJlciIsImF6cCI6InBvcnRhbGV4dGVybm8tZnJvbnRlbmQiLCJub25jZSI6ImE2YTI5NDlmLTVkMTUtNDRjZC04YTEzLWViMWE1NzhhMjMwOCIsInNlc3Npb25fc3RhdGUiOiI0NmFmMzFjZS1iYzljLTQ5ZDQtODFjYS0xMjA2NTdkNzYyMzciLCJhY3IiOiIwIiwiYWxsb3dlZC1vcmlnaW5zIjpbImh0dHBzOi8vcG9ydGFsZGVzZXJ2aWNvcy5wZHBqLmp1cy5iciJdLCJyZWFsbV9hY2Nlc3MiOnsicm9sZXMiOlsib2ZmbGluZV9hY2Nlc3MiLCJ1bWFfYXV0aG9yaXphdGlvbiJdfSwicmVzb3VyY2VfYWNjZXNzIjp7ImJyb2tlciI6eyJyb2xlcyI6WyJyZWFkLXRva2VuIl19LCJhY2NvdW50Ijp7InJvbGVzIjpbIm1hbmFnZS1hY2NvdW50IiwibWFuYWdlLWFjY291bnQtbGlua3MiLCJ2aWV3LXByb2ZpbGUiXX19LCJzY29wZSI6Im9wZW5pZCBwcm9maWxlIGVtYWlsIiwic2lkIjoiNDZhZjMxY2UtYmM5Yy00OWQ0LTgxY2EtMTIwNjU3ZDc2MjM3IiwiQWNlc3NhUmVwb3NpdG9yaW8iOiJPayIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJuYW1lIjoiRlJBTkNJU0NPIEJSVU5PIE5PQlJFIERFIE1FTE8iLCJwcmVmZXJyZWRfdXNlcm5hbWUiOiIwNjMzMzE0NTM2MCIsImdpdmVuX25hbWUiOiJGUkFOQ0lTQ08gQlJVTk8gTk9CUkUgREUgTUVMTyIsImNvcnBvcmF0aXZvIjpbeyJzZXFfdXN1YXJpbyI6MTY1MDIzNjcsIm5vbV91c3VhcmlvIjoiRlJBTkNJU0NPIEJSVU5PIE5PQlJFIERFIE1FTE8iLCJudW1fY3BmIjoiMDYzMzMxNDUzNjAiLCJzaWdfdGlwb19jYXJnbyI6IkFEViIsImZsZ19hdGl2byI6IlMiLCJzZXFfc2lzdGVtYSI6MCwic2VxX3BlcmZpbCI6MCwiZHNjX29yZ2FvIjoiT0FCIiwic2VxX3RyaWJ1bmFsX3BhaSI6MCwiZHNjX2VtYWlsIjoibWVsb2ZhY2RpcmVpdG9AaG90bWFpbC5jb20iLCJzZXFfb3JnYW9fZXh0ZXJubyI6MCwiZHNjX29yZ2FvX2V4dGVybm8iOiJPQUIiLCJvYWIiOiJDRTQ0Njc0In1dLCJlbWFpbCI6Im1lbG9mYWNkaXJlaXRvQGhvdG1haWwuY29tIn0.QjvsSE_I7Ih5UtmFt2r5kdP6MLfSsQHCXYqdtVkHFKVcRm2A27kNVGn7BIKT9QYtoI_0Vwl9cH7CjSOoB3zLWN24iTnNmVkxASS1vr40owbm2coVYXyJ646csChh3eFK_7TRZgVP-4u_0_lJ1VVtGCvZmlALTGZu9xd4Lk06B5Az7mlucZ0kxW4_x4eaHPKc3jjf5mXybxPRkkBtGREZ1EtcWFdpA84QSHYDEy9_8TV32N1E_3rQXXyPbyjQ6eR-4RRc6SDwzgykoXR6oo_hy47DzMnx6-C4MW2er7EWc1XHpyl4Sngy3ZJN3-9VIgktS-sY9-Xzugp3bzxiZL7OHQ"

# Documentos de teste
TEST_DOCUMENTS = [
    {
        "nome": "Petição Inicial",
        "hrefBinario": "/processos/1000145-91.2023.8.26.0597/documentos/ea480b7f-fac4-5c2c-a46f-c5d36f5d4335/binario",
        "document_id": "ea480b7f-fac4-5c2c-a46f-c5d36f5d4335"
    },
    {
        "nome": "Procuração",
        "hrefBinario": "/processos/1000145-91.2023.8.26.0597/documentos/712e8ec4-3184-5a04-b653-0a185cade86f/binario",
        "document_id": "712e8ec4-3184-5a04-b653-0a185cade86f"
    },
    {
        "nome": "Decisão",
        "hrefBinario": "/processos/1000145-91.2023.8.26.0597/documentos/950522d5-c2d2-5e9e-88d9-ed352b511e13/binario",
        "document_id": "950522d5-c2d2-5e9e-88d9-ed352b511e13"
    }
]

async def test_raw_link_access():
    """Acessar links e salvar o que quer que seja retornado."""
    logger.info("🔍 Acessando links e salvando conteúdo bruto")
    
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "User-Agent": "PDPJ-API-Client/1.0",
        "Accept": "*/*"
    }
    
    # Criar diretório para salvar arquivos
    output_dir = "data/raw_downloads"
    os.makedirs(output_dir, exist_ok=True)
    
    results = []
    
    async with httpx.AsyncClient(verify=False, timeout=60.0) as client:
        for i, doc in enumerate(TEST_DOCUMENTS, 1):
            logger.info(f"📄 Teste {i}/{len(TEST_DOCUMENTS)}: {doc['nome']}")
            
            # URL completa
            full_url = f"{BASE_URL}{doc['hrefBinario']}"
            logger.info(f"🔗 URL: {full_url}")
            
            try:
                response = await client.get(full_url, headers=headers)
                
                # Salvar conteúdo bruto
                filename = f"{doc['document_id']}_{doc['nome'].replace(' ', '_')}.raw"
                filepath = os.path.join(output_dir, filename)
                
                with open(filepath, "wb") as f:
                    f.write(response.content)
                
                # Analisar o conteúdo
                content_type = response.headers.get("content-type", "N/A")
                content_length = len(response.content)
                
                # Detectar tipo de conteúdo
                content_preview = response.content[:200] if content_length > 0 else b""
                
                result = {
                    "documento": doc['nome'],
                    "document_id": doc['document_id'],
                    "url": full_url,
                    "status_code": response.status_code,
                    "content_type": content_type,
                    "content_length": content_length,
                    "filename": filename,
                    "filepath": filepath,
                    "content_preview_hex": content_preview.hex(),
                    "content_preview_text": content_preview.decode('utf-8', errors='ignore')[:100],
                    "is_pdf": response.content.startswith(b'%PDF'),
                    "is_html": response.content.startswith(b'<!DOCTYPE html') or response.content.startswith(b'<html'),
                    "is_json": response.content.startswith(b'{') or response.content.startswith(b'['),
                    "is_xml": response.content.startswith(b'<?xml') or response.content.startswith(b'<'),
                    "is_binary": not any([
                        response.content.startswith(b'<!DOCTYPE html'),
                        response.content.startswith(b'<html'),
                        response.content.startswith(b'{'),
                        response.content.startswith(b'['),
                        response.content.startswith(b'<?xml'),
                        response.content.startswith(b'<')
                    ]) and content_length > 0
                }
                
                # Log do resultado
                if result["is_pdf"]:
                    logger.info(f"✅ {doc['nome']}: PDF válido ({content_length} bytes)")
                elif result["is_html"]:
                    logger.warning(f"⚠️ {doc['nome']}: HTML ({content_length} bytes)")
                elif result["is_json"]:
                    logger.info(f"📄 {doc['nome']}: JSON ({content_length} bytes)")
                elif result["is_xml"]:
                    logger.info(f"📄 {doc['nome']}: XML ({content_length} bytes)")
                elif result["is_binary"]:
                    logger.info(f"🔧 {doc['nome']}: Binário ({content_length} bytes)")
                else:
                    logger.warning(f"❓ {doc['nome']}: Tipo desconhecido ({content_length} bytes)")
                
                logger.info(f"💾 Salvo em: {filepath}")
                logger.info(f"📊 Content-Type: {content_type}")
                logger.info(f"🔍 Preview (hex): {content_preview.hex()[:50]}...")
                logger.info(f"🔍 Preview (text): {result['content_preview_text']}")
                
                results.append(result)
                
            except Exception as e:
                logger.error(f"❌ {doc['nome']}: Erro - {e}")
                results.append({
                    "documento": doc['nome'],
                    "document_id": doc['document_id'],
                    "url": full_url,
                    "error": str(e)
                })
            
            # Pequena pausa entre requests
            await asyncio.sleep(1)
    
    return results

async def test_alternative_urls():
    """Testar URLs alternativas para o mesmo documento."""
    logger.info("🔄 Testando URLs alternativas")
    
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "User-Agent": "PDPJ-API-Client/1.0",
        "Accept": "*/*"
    }
    
    # Usar o primeiro documento para teste
    doc = TEST_DOCUMENTS[0]
    document_id = doc['document_id']
    process_number = "1000145-91.2023.8.26.0597"
    
    # URLs alternativas para testar
    alternative_urls = [
        f"{BASE_URL}/processos/{process_number}/documentos/{document_id}",
        f"{BASE_URL}/processos/{process_number}/documentos/{document_id}/download",
        f"{BASE_URL}/processos/{process_number}/documentos/{document_id}/file",
        f"{BASE_URL}/processos/{process_number}/documentos/{document_id}/content",
        f"{BASE_URL}/processos/{process_number}/documentos/{document_id}/raw",
        f"{BASE_URL}/api/v2/processos/{process_number}/documentos/{document_id}",
        f"{BASE_URL}/api/v2/processos/{process_number}/documentos/{document_id}/binario",
        f"{BASE_URL}/api/v2/processos/{process_number}/documentos/{document_id}/download",
        f"{BASE_URL}/api/v2/processos/{process_number}/documentos/{document_id}/file",
        f"{BASE_URL}/api/v2/processos/{process_number}/documentos/{document_id}/content"
    ]
    
    output_dir = "data/raw_downloads"
    os.makedirs(output_dir, exist_ok=True)
    
    results = []
    
    async with httpx.AsyncClient(verify=False, timeout=60.0) as client:
        for i, url in enumerate(alternative_urls, 1):
            logger.info(f"📄 Teste alternativo {i}/{len(alternative_urls)}: {url}")
            
            try:
                response = await client.get(url, headers=headers)
                
                # Salvar conteúdo bruto
                url_safe = url.replace("/", "_").replace(":", "_").replace("?", "_")
                filename = f"alternative_{i}_{url_safe}.raw"
                filepath = os.path.join(output_dir, filename)
                
                with open(filepath, "wb") as f:
                    f.write(response.content)
                
                # Analisar o conteúdo
                content_type = response.headers.get("content-type", "N/A")
                content_length = len(response.content)
                content_preview = response.content[:200] if content_length > 0 else b""
                
                result = {
                    "url": url,
                    "status_code": response.status_code,
                    "content_type": content_type,
                    "content_length": content_length,
                    "filename": filename,
                    "filepath": filepath,
                    "content_preview_hex": content_preview.hex(),
                    "content_preview_text": content_preview.decode('utf-8', errors='ignore')[:100],
                    "is_pdf": response.content.startswith(b'%PDF'),
                    "is_html": response.content.startswith(b'<!DOCTYPE html') or response.content.startswith(b'<html'),
                    "is_json": response.content.startswith(b'{') or response.content.startswith(b'['),
                    "is_xml": response.content.startswith(b'<?xml') or response.content.startswith(b'<'),
                    "is_binary": not any([
                        response.content.startswith(b'<!DOCTYPE html'),
                        response.content.startswith(b'<html'),
                        response.content.startswith(b'{'),
                        response.content.startswith(b'['),
                        response.content.startswith(b'<?xml'),
                        response.content.startswith(b'<')
                    ]) and content_length > 0
                }
                
                # Log do resultado
                if result["is_pdf"]:
                    logger.info(f"✅ PDF válido ({content_length} bytes)")
                elif result["is_html"]:
                    logger.warning(f"⚠️ HTML ({content_length} bytes)")
                elif result["is_json"]:
                    logger.info(f"📄 JSON ({content_length} bytes)")
                elif result["is_xml"]:
                    logger.info(f"📄 XML ({content_length} bytes)")
                elif result["is_binary"]:
                    logger.info(f"🔧 Binário ({content_length} bytes)")
                else:
                    logger.warning(f"❓ Tipo desconhecido ({content_length} bytes)")
                
                logger.info(f"💾 Salvo em: {filepath}")
                logger.info(f"📊 Content-Type: {content_type}")
                logger.info(f"🔍 Preview: {result['content_preview_text']}")
                
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
    logger.info("🚀 Iniciando teste de acesso a links brutos")
    
    # Teste 1: Links originais
    logger.info("=" * 60)
    logger.info("TESTE 1: Links originais dos documentos")
    logger.info("=" * 60)
    results1 = await test_raw_link_access()
    
    # Teste 2: URLs alternativas
    logger.info("\n" + "=" * 60)
    logger.info("TESTE 2: URLs alternativas")
    logger.info("=" * 60)
    results2 = await test_alternative_urls()
    
    # Análise dos resultados
    logger.info("\n📊 ANÁLISE DOS RESULTADOS:")
    logger.info("=" * 60)
    
    # Resultados do teste 1
    logger.info("📋 TESTE 1 - Links originais:")
    for result in results1:
        if "error" not in result:
            status = "✅ PDF" if result.get("is_pdf") else "🔧 BINÁRIO" if result.get("is_binary") else "📄 JSON" if result.get("is_json") else "📄 XML" if result.get("is_xml") else "⚠️ HTML"
            logger.info(f"  {status} {result['documento']} - {result.get('content_length', 0)} bytes")
    
    # Resultados do teste 2
    logger.info("\n📋 TESTE 2 - URLs alternativas:")
    for result in results2:
        if "error" not in result:
            status = "✅ PDF" if result.get("is_pdf") else "🔧 BINÁRIO" if result.get("is_binary") else "📄 JSON" if result.get("is_json") else "📄 XML" if result.get("is_xml") else "⚠️ HTML"
            logger.info(f"  {status} {result['url']} - {result.get('content_length', 0)} bytes")
    
    # Salvar resultados
    with open("raw_link_test_results.json", "w") as f:
        import json
        json.dump({
            "teste_1_links_originais": results1,
            "teste_2_urls_alternativas": results2
        }, f, indent=2, ensure_ascii=False)
    
    logger.info("💾 Resultados salvos em raw_link_test_results.json")
    logger.info("🏁 Teste concluído")

if __name__ == "__main__":
    asyncio.run(main())
