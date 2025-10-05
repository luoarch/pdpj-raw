#!/usr/bin/env python3
"""
Script para testar download de diferentes tipos de documentos usando hrefBinario
"""

import asyncio
import httpx
import os
from loguru import logger
from typing import List, Dict, Any

# Configurar logging
logger.add("test_document_types.log", rotation="1 MB")

# Base URL da API PDPJ
BASE_URL = "https://portaldeservicos.pdpj.jus.br"

# Token PDPJ
TOKEN = "eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICI1dnJEZ1hCS21FLTdFb3J2a0U1TXU5VmxJZF9JU2dsMnY3QWYyM25EdkRVIn0.eyJleHAiOjE3NTk2MjYzNDMsImlhdCI6MTc1OTYxMTA0OSwiYXV0aF90aW1lIjoxNzU5NTgzMTQzLCJqdGkiOiJiM2IzZGYxMC1mNjZmLTQzMmUtODAyZi0yNDk3MDU5NGEzZTEiLCJpc3MiOiJodHRwczovL3Nzby5jbG91ZC5wamUuanVzLmJyL2F1dGgvcmVhbG1zL3BqZSIsImF1ZCI6WyJicm9rZXIiLCJhY2NvdW50Il0sInN1YiI6IjUwM2Y5ZTc3LWIzY2EtNGE2NC05MjA0LTBmMDJmNjdhZTZhOCIsInR5cCI6IkJlYXJlciIsImF6cCI6InBvcnRhbGV4dGVybm8tZnJvbnRlbmQiLCJub25jZSI6ImE2YTI5NDlmLTVkMTUtNDRjZC04YTEzLWViMWE1NzhhMjMwOCIsInNlc3Npb25fc3RhdGUiOiI0NmFmMzFjZS1iYzljLTQ5ZDQtODFjYS0xMjA2NTdkNzYyMzciLCJhY3IiOiIwIiwiYWxsb3dlZC1vcmlnaW5zIjpbImh0dHBzOi8vcG9ydGFsZGVzZXJ2aWNvcy5wZHBqLmp1cy5iciJdLCJyZWFsbV9hY2Nlc3MiOnsicm9sZXMiOlsib2ZmbGluZV9hY2Nlc3MiLCJ1bWFfYXV0aG9yaXphdGlvbiJdfSwicmVzb3VyY2VfYWNjZXNzIjp7ImJyb2tlciI6eyJyb2xlcyI6WyJyZWFkLXRva2VuIl19LCJhY2NvdW50Ijp7InJvbGVzIjpbIm1hbmFnZS1hY2NvdW50IiwibWFuYWdlLWFjY291bnQtbGlua3MiLCJ2aWV3LXByb2ZpbGUiXX19LCJzY29wZSI6Im9wZW5pZCBwcm9maWxlIGVtYWlsIiwic2lkIjoiNDZhZjMxY2UtYmM5Yy00OWQ0LTgxY2EtMTIwNjU3ZDc2MjM3IiwiQWNlc3NhUmVwb3NpdG9yaW8iOiJPayIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJuYW1lIjoiRlJBTkNJU0NPIEJSVU5PIE5PQlJFIERFIE1FTE8iLCJwcmVmZXJyZWRfdXNlcm5hbWUiOiIwNjMzMzE0NTM2MCIsImdpdmVuX25hbWUiOiJGUkFOQ0lTQ08gQlJVTk8gTk9CUkUgREUgTUVMTyIsImNvcnBvcmF0aXZvIjpbeyJzZXFfdXN1YXJpbyI6MTY1MDIzNjcsIm5vbV91c3VhcmlvIjoiRlJBTkNJU0NPIEJSVU5PIE5PQlJFIERFIE1FTE8iLCJudW1fY3BmIjoiMDYzMzMxNDUzNjAiLCJzaWdfdGlwb19jYXJnbyI6IkFEViIsImZsZ19hdGl2byI6IlMiLCJzZXFfc2lzdGVtYSI6MCwic2VxX3BlcmZpbCI6MCwiZHNjX29yZ2FvIjoiT0FCIiwic2VxX3RyaWJ1bmFsX3BhaSI6MCwiZHNjX2VtYWlsIjoibWVsb2ZhY2RpcmVpdG9AaG90bWFpbC5jb20iLCJzZXFfb3JnYW9fZXh0ZXJubyI6MCwiZHNjX29yZ2FvX2V4dGVybm8iOiJPQUIiLCJvYWIiOiJDRTQ0Njc0In1dLCJlbWFpbCI6Im1lbG9mYWNkaXJlaXRvQGhvdG1haWwuY29tIn0.QjvsSE_I7Ih5UtmFt2r5kdP6MLfSsQHCXYqdtVkHFKVcRm2A27kNVGn7BIKT9QYtoI_0Vwl9cH7CjSOoB3zLWN24iTnNmVkxASS1vr40owbm2coVYXyJ646csChh3eFK_7TRZgVP-4u_0_lJ1VVtGCvZmlALTGZu9xd4Lk06B5Az7mlucZ0kxW4_x4eaHPKc3jjf5mXybxPRkkBtGREZ1EtcWFdpA84QSHYDEy9_8TV32N1E_3rQXXyPbyjQ6eR-4RRc6SDwzgykoXR6oo_hy47DzMnx6-C4MW2er7EWc1XHpyl4Sngy3ZJN3-9VIgktS-sY9-Xzugp3bzxiZL7OHQ"

# Diferentes tipos de documentos para testar (baseado na resposta da API)
DOCUMENT_TESTS = [
    {
        "nome": "Petição Inicial",
        "tipo": "Petição (Outras)",
        "hrefBinario": "/processos/1000145-91.2023.8.26.0597/documentos/ea480b7f-fac4-5c2c-a46f-c5d36f5d4335/binario",
        "expected_type": "application/pdf"
    },
    {
        "nome": "Procuração",
        "tipo": "Instrumento de Procuração", 
        "hrefBinario": "/processos/1000145-91.2023.8.26.0597/documentos/712e8ec4-3184-5a04-b653-0a185cade86f/binario",
        "expected_type": "application/pdf"
    },
    {
        "nome": "Contrato Social",
        "tipo": "Contrato (Outros)",
        "hrefBinario": "/processos/1000145-91.2023.8.26.0597/documentos/57724d78-0d83-52e2-bb87-2e414b8c293f/binario",
        "expected_type": "application/pdf"
    },
    {
        "nome": "Certidão de Matrícula",
        "tipo": "Certidão",
        "hrefBinario": "/processos/1000145-91.2023.8.26.0597/documentos/f27823c7-c74d-5c2d-a1e4-e0cef1e2910a/binario",
        "expected_type": "application/pdf"
    },
    {
        "nome": "Boletim de Ocorrência",
        "tipo": "Boletim de Ocorrência",
        "hrefBinario": "/processos/1000145-91.2023.8.26.0597/documentos/6cf98c78-81ff-5c94-bb26-aa66ea775c43/binario",
        "expected_type": "application/pdf"
    },
    {
        "nome": "Documento Diverso",
        "tipo": "Documentos Diversos",
        "hrefBinario": "/processos/1000145-91.2023.8.26.0597/documentos/407a1cdd-be6b-5484-a031-f1115b3072d1/binario",
        "expected_type": "application/pdf"
    },
    {
        "nome": "Decisão",
        "tipo": "Decisão",
        "hrefBinario": "/processos/1000145-91.2023.8.26.0597/documentos/950522d5-c2d2-5e9e-88d9-ed352b511e13/binario",
        "expected_type": "application/pdf"
    },
    {
        "nome": "Guia de Custas",
        "tipo": "Guia",
        "hrefBinario": "/processos/1000145-91.2023.8.26.0597/documentos/47a1eff9-3c65-58c0-80e8-a71a6d971319/binario",
        "expected_type": "application/pdf"
    }
]

async def test_document_download(doc_info: Dict[str, str]) -> Dict[str, Any]:
    """Testar download de um documento específico."""
    logger.info(f"🔍 Testando: {doc_info['nome']} ({doc_info['tipo']})")
    
    full_url = f"{BASE_URL}{doc_info['hrefBinario']}"
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "User-Agent": "PDPJ-API-Client/1.0",
        "Accept": "application/pdf,application/octet-stream,*/*"
    }
    
    try:
        async with httpx.AsyncClient(verify=False) as client:
            response = await client.get(full_url, headers=headers, timeout=30.0)
            
            result = {
                "nome": doc_info["nome"],
                "tipo": doc_info["tipo"],
                "hrefBinario": doc_info["hrefBinario"],
                "status_code": response.status_code,
                "content_type": response.headers.get("content-type", "N/A"),
                "content_length": len(response.content),
                "success": False,
                "is_pdf": False,
                "is_html": False,
                "error": None
            }
            
            if response.status_code == 200:
                content = response.content
                
                # Verificar tipo de conteúdo
                if content.startswith(b'%PDF'):
                    result["is_pdf"] = True
                    result["success"] = True
                    logger.info(f"✅ {doc_info['nome']}: PDF válido ({len(content)} bytes)")
                elif content.startswith(b'<!DOCTYPE html') or content.startswith(b'<html'):
                    result["is_html"] = True
                    logger.warning(f"⚠️ {doc_info['nome']}: Retornou HTML ({len(content)} bytes)")
                else:
                    logger.warning(f"⚠️ {doc_info['nome']}: Conteúdo desconhecido ({len(content)} bytes)")
                    logger.debug(f"Primeiros 100 bytes: {content[:100]}")
            else:
                result["error"] = f"HTTP {response.status_code}"
                logger.error(f"❌ {doc_info['nome']}: {response.status_code}")
            
            return result
            
    except Exception as e:
        logger.error(f"❌ {doc_info['nome']}: Erro - {e}")
        return {
            "nome": doc_info["nome"],
            "tipo": doc_info["tipo"],
            "hrefBinario": doc_info["hrefBinario"],
            "success": False,
            "error": str(e)
        }

async def test_all_document_types():
    """Testar todos os tipos de documentos."""
    logger.info("🚀 Iniciando teste de diferentes tipos de documentos")
    logger.info(f"📊 Total de documentos para testar: {len(DOCUMENT_TESTS)}")
    
    results = []
    
    for i, doc_info in enumerate(DOCUMENT_TESTS, 1):
        logger.info(f"📄 Teste {i}/{len(DOCUMENT_TESTS)}")
        result = await test_document_download(doc_info)
        results.append(result)
        
        # Pequena pausa entre requests
        await asyncio.sleep(0.5)
    
    # Análise dos resultados
    logger.info("=" * 60)
    logger.info("📊 ANÁLISE DOS RESULTADOS")
    logger.info("=" * 60)
    
    total_tests = len(results)
    successful_pdfs = sum(1 for r in results if r.get("is_pdf"))
    html_responses = sum(1 for r in results if r.get("is_html"))
    errors = sum(1 for r in results if r.get("error"))
    
    logger.info(f"📈 Total de testes: {total_tests}")
    logger.info(f"✅ PDFs válidos: {successful_pdfs}")
    logger.info(f"⚠️ Respostas HTML: {html_responses}")
    logger.info(f"❌ Erros: {errors}")
    
    # Detalhes por tipo
    logger.info("\n📋 DETALHES POR TIPO DE DOCUMENTO:")
    for result in results:
        status = "✅ PDF" if result.get("is_pdf") else "⚠️ HTML" if result.get("is_html") else "❌ ERRO"
        logger.info(f"  {status} {result['nome']} ({result['tipo']}) - {result.get('content_length', 0)} bytes")
    
    # Salvar resultados em arquivo
    with open("document_test_results.json", "w") as f:
        import json
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    logger.info("💾 Resultados salvos em document_test_results.json")
    
    return results

async def main():
    """Função principal."""
    logger.info("🎯 Teste de diferentes tipos de documentos PDPJ")
    results = await test_all_document_types()
    
    # Conclusão
    successful_pdfs = sum(1 for r in results if r.get("is_pdf"))
    total_tests = len(results)
    
    if successful_pdfs == total_tests:
        logger.info("🎉 Todos os documentos foram baixados como PDF válido!")
    elif successful_pdfs > 0:
        logger.info(f"⚠️ {successful_pdfs}/{total_tests} documentos foram baixados como PDF válido")
    else:
        logger.error("❌ Nenhum documento foi baixado como PDF válido")
    
    logger.info("🏁 Teste concluído")

if __name__ == "__main__":
    asyncio.run(main())
