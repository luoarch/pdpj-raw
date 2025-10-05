#!/usr/bin/env python3
"""
Script para investigar os JSONs de erro retornados pelos endpoints /api/v2/
"""

import asyncio
import httpx
import json
from loguru import logger

# Configurar logging
logger.add("investigate_json_errors.log", rotation="1 MB")

# Base URL da API PDPJ
BASE_URL = "https://portaldeservicos.pdpj.jus.br"

# Token PDPJ atualizado
TOKEN = "eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICI1dnJEZ1hCS21FLTdFb3J2a0U1TXU5VmxJZF9JU2dsMnY3QWYyM25EdkRVIn0.eyJleHAiOjE3NTk2NTYyNjIsImlhdCI6MTc1OTYyNzQ2MywiYXV0aF90aW1lIjoxNzU5NjI3NDM3LCJqdGkiOiI4ZjUxOTAzMi0yNjQ3LTRmN2YtOTQxOS04ZGVjMWRmYzcxNzciLCJpc3MiOiJodHRwczovL3Nzby5jbG91ZC5wamUuanVzLmJyL2F1dGgvcmVhbG1zL3BqZSIsImF1ZCI6WyJicm9rZXIiLCJhY2NvdW50Il0sInN1YiI6IjUwM2Y5ZTc3LWIzY2EtNGE2NC05MjA0LTBmMDJmNjdhZTZhOCIsInR5cCI6IkJlYXJlciIsImF6cCI6InBvcnRhbGV4dGVybm8tZnJvbnRlbmQiLCJub25jZSI6ImMxNTdkYTY2LTY1YzctNDdjMC05ZGFhLWJkOGM3NzdlMDczYiIsInNlc3Npb25fc3RhdGUiOiIwOWRhODhjNC05NTA4LTQ0ZjktYTdmYi1lODk1Yzc4YTI5NmIiLCJhY3IiOiIwIiwiYWxsb3dlZC1vcmlnaW5zIjpbImh0dHBzOi8vcG9ydGFsZGVzZXJ2aWNvcy5wZHBqLmp1cy5iciJdLCJyZWFsbV9hY2Nlc3MiOnsicm9sZXMiOlsib2ZmbGluZV9hY2Nlc3MiLCJ1bWFfYXV0aG9yaXphdGlvbiJdfSwicmVzb3VyY2VfYWNjZXNzIjp7ImJyb2tlciI6eyJyb2xlcyI6WyJyZWFkLXRva2VuIl19LCJhY2NvdW50Ijp7InJvbGVzIjpbIm1hbmFnZS1hY2NvdW50IiwibWFuYWdlLWFjY291bnQtbGlua3MiLCJ2aWV3LXByb2ZpbGUiXX19LCJzY29wZSI6Im9wZW5pZCBwcm9maWxlIGVtYWlsIiwic2lkIjoiMDlkYTg4YzQtOTUwOC00NGY5LWE3ZmItZTg5NWM3OGEyOTZiIiwiQWNlc3NhUmVwb3NpdG9yaW8iOiJPayIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJuYW1lIjoiRlJBTkNJU0NPIEJSVU5PIE5PQlJFIERFIE1FTE8iLCJwcmVmZXJyZWRfdXNlcm5hbWUiOiIwNjMzMzE0NTM2MCIsImdpdmVuX25hbWUiOiJGUkFOQ0lTQ08gQlJVTk8gTk9CUkUgREUgTUVMTyIsImNvcnBvcmF0aXZvIjpbeyJzZXFfdXN1YXJpbyI6MTY1MDIzNjcsIm5vbV91c3VhcmlvIjoiRlJBTkNJU0NPIEJSVU5PIE5PQlJFIERFIE1FTE8iLCJudW1fY3BmIjoiMDYzMzMxNDUzNjAiLCJzaWdfdGlwb19jYXJnbyI6IkFEViIsImZsZ19hdGl2byI6IlMiLCJzZXFfc2lzdGVtYSI6MCwic2VxX3BlcmZpbCI6MCwiZHNjX29yZ2FvIjoiT0FCIiwic2VxX3RyaWJ1bmFsX3BhaSI6MCwiZHNjX2VtYWlsIjoibWVsb2ZhY2RpcmVpdG9AaG90bWFpbC5jb20iLCJzZXFfb3JnYW9fZXh0ZXJubyI6MCwiZHNjX29yZ2FvX2V4dGVybm8iOiJPQUIiLCJvYWIiOiJDRTQ0Njc0In1dLCJlbWFpbCI6Im1lbG9mYWNkaXJlaXRvQGhvdG1haWwuY29tIn0.RMK9Wu6irZ_QawfQ3yF-xP-W8vKfPP4hj1q5cKyZCTdPIWxA4RsAjEa83450IwqHht07gGOyNbCAjSUXcTIanIdj41Xe8t9N3rfXuBaBxO2WSmqWNlI_NF0S3NG_9Atd5fmo5qv2NluknGPtWDwk3NZjeC3vDc7qqk5-tJwJ3BnJoXvutcnNkDUWtstV0Q14itDoOERvdbMPqwcoJMotUD7ZYGa43PpP--sCx2YMTBBqzI8pqmILqAbyh0JpiCcse6zlpcgfQm8gqjO8Gm-JelCN7Kb9EUFUjvCIBxNIdrc7mhKZ-Mr7x_gMHEldrpGPESIiXTWDKbF3H62RFlpGZg"

# Documento de teste
TEST_DOCUMENT = {
    "nome": "Petição Inicial",
    "hrefBinario": "/processos/1000145-91.2023.8.26.0597/documentos/ea480b7f-fac4-5c2c-a46f-c5d36f5d4335/binario",
    "document_id": "ea480b7f-fac4-5c2c-a46f-c5d36f5d4335"
}

async def investigate_json_errors():
    """Investigar os JSONs de erro retornados pelos endpoints /api/v2/."""
    logger.info("🔍 Investigando JSONs de erro dos endpoints /api/v2/")
    
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "User-Agent": "PDPJ-API-Client/1.0",
        "Accept": "application/json"
    }
    
    document_id = TEST_DOCUMENT['document_id']
    process_number = "1000145-91.2023.8.26.0597"
    
    # URLs que retornaram JSON de erro
    error_urls = [
        {
            "name": "Endpoint documento (404)",
            "url": f"{BASE_URL}/api/v2/processos/{process_number}/documentos/{document_id}",
            "expected_status": 404
        },
        {
            "name": "Endpoint binario (500)",
            "url": f"{BASE_URL}/api/v2/processos/{process_number}/documentos/{document_id}/binario",
            "expected_status": 500
        }
    ]
    
    results = []
    
    async with httpx.AsyncClient(verify=False, timeout=60.0) as client:
        for test_case in error_urls:
            logger.info(f"📄 Investigando: {test_case['name']}")
            logger.info(f"🔗 URL: {test_case['url']}")
            
            try:
                response = await client.get(test_case['url'], headers=headers)
                
                logger.info(f"📊 Status: {response.status_code}")
                logger.info(f"📊 Content-Type: {response.headers.get('content-type', 'N/A')}")
                logger.info(f"📊 Content-Length: {len(response.content)}")
                
                # Tentar decodificar JSON
                try:
                    json_data = response.json()
                    logger.info("📄 JSON decodificado com sucesso:")
                    logger.info(f"🔍 Conteúdo: {json.dumps(json_data, indent=2, ensure_ascii=False)}")
                    
                    result = {
                        "name": test_case['name'],
                        "url": test_case['url'],
                        "status_code": response.status_code,
                        "json_data": json_data,
                        "success": True
                    }
                    
                except json.JSONDecodeError as e:
                    logger.error(f"❌ Erro ao decodificar JSON: {e}")
                    logger.info(f"🔍 Conteúdo bruto: {response.text}")
                    
                    result = {
                        "name": test_case['name'],
                        "url": test_case['url'],
                        "status_code": response.status_code,
                        "raw_content": response.text,
                        "success": False
                    }
                
                results.append(result)
                
            except Exception as e:
                logger.error(f"❌ Erro na requisição: {e}")
                results.append({
                    "name": test_case['name'],
                    "url": test_case['url'],
                    "error": str(e),
                    "success": False
                })
            
            # Pequena pausa entre requests
            await asyncio.sleep(0.5)
    
    return results

async def test_alternative_api_endpoints():
    """Testar endpoints alternativos da API v2."""
    logger.info("🔄 Testando endpoints alternativos da API v2")
    
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "User-Agent": "PDPJ-API-Client/1.0",
        "Accept": "application/json"
    }
    
    process_number = "1000145-91.2023.8.26.0597"
    
    # Endpoints alternativos para testar
    alternative_endpoints = [
        f"{BASE_URL}/api/v2/processos/{process_number}",
        f"{BASE_URL}/api/v2/processos/{process_number}/documentos",
        f"{BASE_URL}/api/v2/processos/{process_number}/tramitacoes",
        f"{BASE_URL}/api/v2/processos/{process_number}/partes",
        f"{BASE_URL}/api/v2/processos/{process_number}/movimentacoes"
    ]
    
    results = []
    
    async with httpx.AsyncClient(verify=False, timeout=60.0) as client:
        for endpoint in alternative_endpoints:
            logger.info(f"📄 Testando: {endpoint}")
            
            try:
                response = await client.get(endpoint, headers=headers)
                
                logger.info(f"📊 Status: {response.status_code}")
                logger.info(f"📊 Content-Type: {response.headers.get('content-type', 'N/A')}")
                logger.info(f"📊 Content-Length: {len(response.content)}")
                
                if response.status_code == 200:
                    try:
                        json_data = response.json()
                        logger.info("✅ JSON válido recebido")
                        logger.info(f"🔍 Chaves: {list(json_data.keys()) if isinstance(json_data, dict) else 'Array'}")
                        
                        result = {
                            "endpoint": endpoint,
                            "status_code": response.status_code,
                            "success": True,
                            "json_data": json_data
                        }
                        
                    except json.JSONDecodeError:
                        logger.warning("⚠️ Resposta não é JSON válido")
                        result = {
                            "endpoint": endpoint,
                            "status_code": response.status_code,
                            "success": False,
                            "raw_content": response.text[:200]
                        }
                else:
                    logger.warning(f"⚠️ Status {response.status_code}")
                    result = {
                        "endpoint": endpoint,
                        "status_code": response.status_code,
                        "success": False,
                        "raw_content": response.text[:200]
                    }
                
                results.append(result)
                
            except Exception as e:
                logger.error(f"❌ Erro: {e}")
                results.append({
                    "endpoint": endpoint,
                    "error": str(e),
                    "success": False
                })
            
            # Pequena pausa entre requests
            await asyncio.sleep(0.5)
    
    return results

async def main():
    """Função principal."""
    logger.info("🚀 Investigando JSONs de erro e testando endpoints alternativos")
    
    # Teste 1: Investigar JSONs de erro
    logger.info("=" * 60)
    logger.info("TESTE 1: Investigar JSONs de erro")
    logger.info("=" * 60)
    error_results = await investigate_json_errors()
    
    # Teste 2: Endpoints alternativos
    logger.info("\n" + "=" * 60)
    logger.info("TESTE 2: Endpoints alternativos da API v2")
    logger.info("=" * 60)
    alternative_results = await test_alternative_api_endpoints()
    
    # Análise dos resultados
    logger.info("\n📊 ANÁLISE DOS RESULTADOS:")
    logger.info("=" * 60)
    
    # Resultados dos erros
    logger.info("📋 TESTE 1 - JSONs de erro:")
    for result in error_results:
        if result.get("success"):
            logger.info(f"  ✅ {result['name']}: {result['status_code']} - JSON válido")
        else:
            logger.info(f"  ❌ {result['name']}: {result.get('status_code', 'Erro')} - {result.get('error', 'JSON inválido')}")
    
    # Resultados dos endpoints alternativos
    logger.info("\n📋 TESTE 2 - Endpoints alternativos:")
    for result in alternative_results:
        if result.get("success"):
            logger.info(f"  ✅ {result['endpoint']}: {result['status_code']} - JSON válido")
        else:
            logger.info(f"  ❌ {result['endpoint']}: {result.get('status_code', 'Erro')} - {result.get('error', 'Falha')}")
    
    # Salvar resultados
    with open("json_errors_investigation.json", "w") as f:
        json.dump({
            "error_investigation": error_results,
            "alternative_endpoints": alternative_results
        }, f, indent=2, ensure_ascii=False)
    
    logger.info("💾 Resultados salvos em json_errors_investigation.json")
    logger.info("🏁 Investigação concluída")

if __name__ == "__main__":
    asyncio.run(main())
