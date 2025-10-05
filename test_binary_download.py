#!/usr/bin/env python3
"""
Script para testar diferentes formas de baixar o binário dos documentos
"""

import asyncio
import httpx
import os
import base64
from loguru import logger
from typing import Dict, Any

# Configurar logging
logger.add("test_binary_download.log", rotation="1 MB")

# Base URL da API PDPJ
BASE_URL = "https://portaldeservicos.pdpj.jus.br"

# Token PDPJ
TOKEN = "eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICI1dnJEZ1hCS21FLTdFb3J2a0U1TXU5VmxJZF9JU2dsMnY3QWYyM25EdkRVIn0.eyJleHAiOjE3NTk2MjYzNDMsImlhdCI6MTc1OTYxMTA0OSwiYXV0aF90aW1lIjoxNzU5NTgzMTQzLCJqdGkiOiJiM2IzZGYxMC1mNjZmLTQzMmUtODAyZi0yNDk3MDU5NGEzZTEiLCJpc3MiOiJodHRwczovL3Nzby5jbG91ZC5wamUuanVzLmJyL2F1dGgvcmVhbG1zL3BqZSIsImF1ZCI6WyJicm9rZXIiLCJhY2NvdW50Il0sInN1YiI6IjUwM2Y5ZTc3LWIzY2EtNGE2NC05MjA0LTBmMDJmNjdhZTZhOCIsInR5cCI6IkJlYXJlciIsImF6cCI6InBvcnRhbGV4dGVybm8tZnJvbnRlbmQiLCJub25jZSI6ImE2YTI5NDlmLTVkMTUtNDRjZC04YTEzLWViMWE1NzhhMjMwOCIsInNlc3Npb25fc3RhdGUiOiI0NmFmMzFjZS1iYzljLTQ5ZDQtODFjYS0xMjA2NTdkNzYyMzciLCJhY3IiOiIwIiwiYWxsb3dlZC1vcmlnaW5zIjpbImh0dHBzOi8vcG9ydGFsZGVzZXJ2aWNvcy5wZHBqLmp1cy5iciJdLCJyZWFsbV9hY2Nlc3MiOnsicm9sZXMiOlsib2ZmbGluZV9hY2Nlc3MiLCJ1bWFfYXV0aG9yaXphdGlvbiJdfSwicmVzb3VyY2VfYWNjZXNzIjp7ImJyb2tlciI6eyJyb2xlcyI6WyJyZWFkLXRva2VuIl19LCJhY2NvdW50Ijp7InJvbGVzIjpbIm1hbmFnZS1hY2NvdW50IiwibWFuYWdlLWFjY291bnQtbGlua3MiLCJ2aWV3LXByb2ZpbGUiXX19LCJzY29wZSI6Im9wZW5pZCBwcm9maWxlIGVtYWlsIiwic2lkIjoiNDZhZjMxY2UtYmM5Yy00OWQ0LTgxY2EtMTIwNjU3ZDc2MjM3IiwiQWNlc3NhUmVwb3NpdG9yaW8iOiJPayIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJuYW1lIjoiRlJBTkNJU0NPIEJSVU5PIE5PQlJFIERFIE1FTE8iLCJwcmVmZXJyZWRfdXNlcm5hbWUiOiIwNjMzMzE0NTM2MCIsImdpdmVuX25hbWUiOiJGUkFOQ0lTQ08gQlJVTk8gTk9CUkUgREUgTUVMTyIsImNvcnBvcmF0aXZvIjpbeyJzZXFfdXN1YXJpbyI6MTY1MDIzNjcsIm5vbV91c3VhcmlvIjoiRlJBTkNJU0NPIEJSVU5PIE5PQlJFIERFIE1FTE8iLCJudW1fY3BmIjoiMDYzMzMxNDUzNjAiLCJzaWdfdGlwb19jYXJnbyI6IkFEViIsImZsZ19hdGl2byI6IlMiLCJzZXFfc2lzdGVtYSI6MCwic2VxX3BlcmZpbCI6MCwiZHNjX29yZ2FvIjoiT0FCIiwic2VxX3RyaWJ1bmFsX3BhaSI6MCwiZHNjX2VtYWlsIjoibWVsb2ZhY2RpcmVpdG9AaG90bWFpbC5jb20iLCJzZXFfb3JnYW9fZXh0ZXJubyI6MCwiZHNjX29yZ2FvX2V4dGVybm8iOiJPQUIiLCJvYWIiOiJDRTQ0Njc0In1dLCJlbWFpbCI6Im1lbG9mYWNkaXJlaXRvQGhvdG1haWwuY29tIn0.QjvsSE_I7Ih5UtmFt2r5kdP6MLfSsQHCXYqdtVkHFKVcRm2A27kNVGn7BIKT9QYtoI_0Vwl9cH7CjSOoB3zLWN24iTnNmVkxASS1vr40owbm2coVYXyJ646csChh3eFK_7TRZgVP-4u_0_lJ1VVtGCvZmlALTGZu9xd4Lk06B5Az7mlucZ0kxW4_x4eaHPKc3jjf5mXybxPRkkBtGREZ1EtcWFdpA84QSHYDEy9_8TV32N1E_3rQXXyPbyjQ6eR-4RRc6SDwzgykoXR6oo_hy47DzMnx6-C4MW2er7EWc1XHpyl4Sngy3ZJN3-9VIgktS-sY9-Xzugp3bzxiZL7OHQ"

# Documento de teste (Petição inicial)
TEST_DOCUMENT = {
    "nome": "Petição Inicial",
    "hrefBinario": "/processos/1000145-91.2023.8.26.0597/documentos/ea480b7f-fac4-5c2c-a46f-c5d36f5d4335/binario",
    "document_id": "ea480b7f-fac4-5c2c-a46f-c5d36f5d4335"
}

async def test_different_endpoints():
    """Testar diferentes endpoints e abordagens para baixar o binário."""
    logger.info("🔍 Testando diferentes abordagens para download de binário")
    
    base_headers = {
        "Authorization": f"Bearer {TOKEN}",
        "User-Agent": "PDPJ-API-Client/1.0"
    }
    
    # Diferentes endpoints e abordagens para testar
    test_cases = [
        {
            "name": "Endpoint binario original",
            "url": f"{BASE_URL}{TEST_DOCUMENT['hrefBinario']}",
            "headers": {**base_headers, "Accept": "application/pdf,application/octet-stream,*/*"}
        },
        {
            "name": "Endpoint binario com Accept específico",
            "url": f"{BASE_URL}{TEST_DOCUMENT['hrefBinario']}",
            "headers": {**base_headers, "Accept": "application/octet-stream"}
        },
        {
            "name": "Endpoint binario com Content-Type",
            "url": f"{BASE_URL}{TEST_DOCUMENT['hrefBinario']}",
            "headers": {**base_headers, "Accept": "*/*", "Content-Type": "application/octet-stream"}
        },
        {
            "name": "Endpoint alternativo /download",
            "url": f"{BASE_URL}/processos/1000145-91.2023.8.26.0597/documentos/{TEST_DOCUMENT['document_id']}/download",
            "headers": {**base_headers, "Accept": "application/pdf,application/octet-stream,*/*"}
        },
        {
            "name": "Endpoint alternativo /file",
            "url": f"{BASE_URL}/processos/1000145-91.2023.8.26.0597/documentos/{TEST_DOCUMENT['document_id']}/file",
            "headers": {**base_headers, "Accept": "application/pdf,application/octet-stream,*/*"}
        },
        {
            "name": "Endpoint alternativo /content",
            "url": f"{BASE_URL}/processos/1000145-91.2023.8.26.0597/documentos/{TEST_DOCUMENT['document_id']}/content",
            "headers": {**base_headers, "Accept": "application/pdf,application/octet-stream,*/*"}
        },
        {
            "name": "Endpoint alternativo /raw",
            "url": f"{BASE_URL}/processos/1000145-91.2023.8.26.0597/documentos/{TEST_DOCUMENT['document_id']}/raw",
            "headers": {**base_headers, "Accept": "application/octet-stream"}
        },
        {
            "name": "Endpoint API v2 binario",
            "url": f"{BASE_URL}/api/v2/processos/1000145-91.2023.8.26.0597/documentos/{TEST_DOCUMENT['document_id']}/binario",
            "headers": {**base_headers, "Accept": "application/pdf,application/octet-stream,*/*"}
        },
        {
            "name": "Endpoint API v2 download",
            "url": f"{BASE_URL}/api/v2/processos/1000145-91.2023.8.26.0597/documentos/{TEST_DOCUMENT['document_id']}/download",
            "headers": {**base_headers, "Accept": "application/pdf,application/octet-stream,*/*"}
        },
        {
            "name": "Endpoint com Range header",
            "url": f"{BASE_URL}{TEST_DOCUMENT['hrefBinario']}",
            "headers": {**base_headers, "Accept": "application/pdf,application/octet-stream,*/*", "Range": "bytes=0-"}
        }
    ]
    
    results = []
    
    async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
        for i, test_case in enumerate(test_cases, 1):
            logger.info(f"📄 Teste {i}/{len(test_cases)}: {test_case['name']}")
            
            try:
                response = await client.get(test_case['url'], headers=test_case['headers'])
                
                result = {
                    "name": test_case['name'],
                    "url": test_case['url'],
                    "status_code": response.status_code,
                    "content_type": response.headers.get("content-type", "N/A"),
                    "content_length": len(response.content),
                    "is_pdf": response.content.startswith(b'%PDF'),
                    "is_html": response.content.startswith(b'<!DOCTYPE html') or response.content.startswith(b'<html'),
                    "is_json": response.content.startswith(b'{') or response.content.startswith(b'['),
                    "is_binary": not (response.content.startswith(b'<!DOCTYPE html') or 
                                    response.content.startswith(b'<html') or 
                                    response.content.startswith(b'{') or 
                                    response.content.startswith(b'[') or
                                    response.content.startswith(b'%PDF')),
                    "first_100_bytes": response.content[:100].hex() if len(response.content) > 0 else "empty"
                }
                
                if result["is_pdf"]:
                    logger.info(f"✅ {test_case['name']}: PDF válido ({result['content_length']} bytes)")
                elif result["is_html"]:
                    logger.warning(f"⚠️ {test_case['name']}: HTML ({result['content_length']} bytes)")
                elif result["is_json"]:
                    logger.info(f"📄 {test_case['name']}: JSON ({result['content_length']} bytes)")
                elif result["is_binary"]:
                    logger.info(f"🔧 {test_case['name']}: Binário ({result['content_length']} bytes)")
                else:
                    logger.warning(f"❓ {test_case['name']}: Tipo desconhecido ({result['content_length']} bytes)")
                
                results.append(result)
                
            except Exception as e:
                logger.error(f"❌ {test_case['name']}: Erro - {e}")
                results.append({
                    "name": test_case['name'],
                    "url": test_case['url'],
                    "error": str(e)
                })
            
            # Pequena pausa entre requests
            await asyncio.sleep(0.5)
    
    return results

async def test_base64_approach():
    """Testar se existe um endpoint que retorna o binário em base64."""
    logger.info("🔍 Testando abordagem com base64")
    
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "User-Agent": "PDPJ-API-Client/1.0",
        "Accept": "application/json"
    }
    
    # Tentar endpoints que podem retornar base64
    base64_endpoints = [
        f"{BASE_URL}/api/v2/processos/1000145-91.2023.8.26.0597/documentos/{TEST_DOCUMENT['document_id']}",
        f"{BASE_URL}/api/v2/processos/1000145-91.2023.8.26.0597/documentos/{TEST_DOCUMENT['document_id']}/data",
        f"{BASE_URL}/api/v2/processos/1000145-91.2023.8.26.0597/documentos/{TEST_DOCUMENT['document_id']}/base64"
    ]
    
    async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
        for endpoint in base64_endpoints:
            try:
                logger.info(f"📄 Testando: {endpoint}")
                response = await client.get(endpoint, headers=headers)
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        logger.info(f"📊 JSON recebido: {list(data.keys()) if isinstance(data, dict) else 'Array'}")
                        
                        # Procurar por campos que podem conter base64
                        if isinstance(data, dict):
                            for key, value in data.items():
                                if isinstance(value, str) and len(value) > 100:
                                    # Tentar decodificar como base64
                                    try:
                                        decoded = base64.b64decode(value)
                                        if decoded.startswith(b'%PDF'):
                                            logger.info(f"🎉 Encontrado PDF em base64 no campo '{key}'!")
                                            return {"success": True, "field": key, "data": decoded}
                                    except:
                                        pass
                        
                    except Exception as e:
                        logger.warning(f"⚠️ Não é JSON válido: {e}")
                
            except Exception as e:
                logger.error(f"❌ Erro no endpoint {endpoint}: {e}")
    
    return {"success": False}

async def main():
    """Função principal."""
    logger.info("🚀 Iniciando teste de download de binário")
    
    # Teste 1: Diferentes endpoints
    logger.info("=" * 60)
    logger.info("TESTE 1: Diferentes endpoints")
    logger.info("=" * 60)
    results = await test_different_endpoints()
    
    # Análise dos resultados
    logger.info("\n📊 ANÁLISE DOS RESULTADOS:")
    for result in results:
        if "error" not in result:
            status = "✅ PDF" if result.get("is_pdf") else "🔧 BINÁRIO" if result.get("is_binary") else "📄 JSON" if result.get("is_json") else "⚠️ HTML"
            logger.info(f"  {status} {result['name']} - {result.get('content_length', 0)} bytes")
    
    # Teste 2: Abordagem base64
    logger.info("\n" + "=" * 60)
    logger.info("TESTE 2: Abordagem base64")
    logger.info("=" * 60)
    base64_result = await test_base64_approach()
    
    if base64_result["success"]:
        logger.info("🎉 Sucesso com base64!")
    else:
        logger.info("❌ Base64 não funcionou")
    
    # Salvar resultados
    with open("binary_test_results.json", "w") as f:
        import json
        json.dump({"endpoint_tests": results, "base64_test": base64_result}, f, indent=2, ensure_ascii=False)
    
    logger.info("💾 Resultados salvos em binary_test_results.json")
    logger.info("🏁 Teste concluído")

if __name__ == "__main__":
    asyncio.run(main())
