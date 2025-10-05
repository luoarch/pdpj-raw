#!/usr/bin/env python3
"""
Script isolado para testar download de documentos usando hrefBinario e hrefTexto
com URLs absolutas construídas a partir dos campos da API PDPJ.
"""

import asyncio
import httpx
import os
import json
from loguru import logger
from typing import List, Dict, Any

# Configurar logging
logger.add("test_document_download_isolated.log", rotation="1 MB")

# Base URL da API PDPJ
API_BASE_URL = "https://portaldeservicos.pdpj.jus.br"

# Token PDPJ atualizado
TOKEN = "eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICI1dnJEZ1hCS21FLTdFb3J2a0U1TXU5VmxJZF9JU2dsMnY3QWYyM25EdkRVIn0.eyJleHAiOjE3NTk2NTYyNjIsImlhdCI6MTc1OTYyNzQ2MywiYXV0aF90aW1lIjoxNzU5NjI3NDM3LCJqdGkiOiI4ZjUxOTAzMi0yNjQ3LTRmN2YtOTQxOS04ZGVjMWRmYzcxNzciLCJpc3MiOiJodHRwczovL3Nzby5jbG91ZC5wamUuanVzLmJyL2F1dGgvcmVhbG1zL3BqZSIsImF1ZCI6WyJicm9rZXIiLCJhY2NvdW50Il0sInN1YiI6IjUwM2Y5ZTc3LWIzY2EtNGE2NC05MjA0LTBmMDJmNjdhZTZhOCIsInR5cCI6IkJlYXJlciIsImF6cCI6InBvcnRhbGV4dGVybm8tZnJvbnRlbmQiLCJub25jZSI6ImMxNTdkYTY2LTY1YzctNDdjMC05ZGFhLWJkOGM3NzdlMDczYiIsInNlc3Npb25fc3RhdGUiOiIwOWRhODhjNC05NTA4LTQ0ZjktYTdmYi1lODk1Yzc4YTI5NmIiLCJhY3IiOiIwIiwiYWxsb3dlZC1vcmlnaW5zIjpbImh0dHBzOi8vcG9ydGFsZGVzZXJ2aWNvcy5wZHBqLmp1cy5iciJdLCJyZWFsbV9hY2Nlc3MiOnsicm9sZXMiOlsib2ZmbGluZV9hY2Nlc3MiLCJ1bWFfYXV0aG9yaXphdGlvbiJdfSwicmVzb3VyY2VfYWNjZXNzIjp7ImJyb2tlciI6eyJyb2xlcyI6WyJyZWFkLXRva2VuIl19LCJhY2NvdW50Ijp7InJvbGVzIjpbIm1hbmFnZS1hY2NvdW50IiwibWFuYWdlLWFjY291bnQtbGlua3MiLCJ2aWV3LXByb2ZpbGUiXX19LCJzY29wZSI6Im9wZW5pZCBwcm9maWxlIGVtYWlsIiwic2lkIjoiMDlkYTg4YzQtOTUwOC00NGY5LWE3ZmItZTg5NWM3OGEyOTZiIiwiQWNlc3NhUmVwb3NpdG9yaW8iOiJPayIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJuYW1lIjoiRlJBTkNJU0NPIEJSVU5PIE5PQlJFIERFIE1FTE8iLCJwcmVmZXJyZWRfdXNlcm5hbWUiOiIwNjMzMzE0NTM2MCIsImdpdmVuX25hbWUiOiJGUkFOQ0lTQ08gQlJVTk8gTk9CUkUgREUgTUVMTyIsImNvcnBvcmF0aXZvIjpbeyJzZXFfdXN1YXJpbyI6MTY1MDIzNjcsIm5vbV91c3VhcmlvIjoiRlJBTkNJU0NPIEJSVU5PIE5PQlJFIERFIE1FTE8iLCJudW1fY3BmIjoiMDYzMzMxNDUzNjAiLCJzaWdfdGlwb19jYXJnbyI6IkFEViIsImZsZ19hdGl2byI6IlMiLCJzZXFfc2lzdGVtYSI6MCwic2VxX3BlcmZpbCI6MCwiZHNjX29yZ2FvIjoiT0FCIiwic2VxX3RyaWJ1bmFsX3BhaSI6MCwiZHNjX2VtYWlsIjoibWVsb2ZhY2RpcmVpdG9AaG90bWFpbC5jb20iLCJzZXFfb3JnYW9fZXh0ZXJubyI6MCwiZHNjX29yZ2FvX2V4dGVybm8iOiJPQUIiLCJvYWIiOiJDRTQ0Njc0In1dLCJlbWFpbCI6Im1lbG9mYWNkaXJlaXRvQGhvdG1haWwuY29tIn0.RMK9Wu6irZ_QawfQ3yF-xP-W8vKfPP4hj1q5cKyZCTdPIWxA4RsAjEa83450IwqHht07gGOyNbCAjSUXcTIanIdj41Xe8t9N3rfXuBaBxO2WSmqWNlI_NF0S3NG_9Atd5fmo5qv2NluknGPtWDwk3NZjeC3vDc7qqk5-tJwJ3BnJoXvutcnNkDUWtstV0Q14itDoOERvdbMPqwcoJMotUD7ZYGa43PpP--sCx2YMTBBqzI8pqmILqAbyh0JpiCcse6zlpcgfQm8gqjO8Gm-JelCN7Kb9EUFUjvCIBxNIdrc7mhKZ-Mr7x_gMHEldrpGPESIiXTWDKbF3H62RFlpGZg"

# Documentos de teste do processo TRF3
TEST_DOCUMENTS = [
    {
        "sequencia": 1,
        "nome": "Petição inicial.pdf",
        "tipo": "Petição inicial",
        "hrefBinario": "/processos/5000315-75.2025.4.03.6327/documentos/266683ef-f200-52d4-9172-19e3dc3c567d/binario",
        "hrefTexto": "/processos/5000315-75.2025.4.03.6327/documentos/266683ef-f200-52d4-9172-19e3dc3c567d/texto",
        "arquivo": {
            "tipo": "application/pdf",
            "tamanho": 279343
        }
    },
    {
        "sequencia": 2,
        "nome": "0.1 PROCURAÇÃO.pdf",
        "tipo": "Procuração/substabelecimento com reserva de poderes",
        "hrefBinario": "/processos/5000315-75.2025.4.03.6327/documentos/b097776a-bf95-5f86-b613-909e557cf08b/binario",
        "hrefTexto": "/processos/5000315-75.2025.4.03.6327/documentos/b097776a-bf95-5f86-b613-909e557cf08b/texto",
        "arquivo": {
            "tipo": "application/pdf",
            "tamanho": 478981
        }
    },
    {
        "sequencia": 3,
        "nome": "1. RG.pdf",
        "tipo": "Documento de Identificação",
        "hrefBinario": "/processos/5000315-75.2025.4.03.6327/documentos/4c999c37-5e71-5343-ba3c-256c502c5fad/binario",
        "hrefTexto": "/processos/5000315-75.2025.4.03.6327/documentos/4c999c37-5e71-5343-ba3c-256c502c5fad/texto",
        "arquivo": {
            "tipo": "application/pdf",
            "tamanho": 105078
        }
    },
    {
        "sequencia": 27,
        "nome": "Pedido de Desistência.pdf",
        "tipo": "Pedido de Desistência",
        "hrefBinario": "/processos/5000315-75.2025.4.03.6327/documentos/bafbfdb2-ab94-5ca0-9cb3-b6e80376a632/binario",
        "hrefTexto": "/processos/5000315-75.2025.4.03.6327/documentos/bafbfdb2-ab94-5ca0-9cb3-b6e80376a632/texto",
        "arquivo": {
            "tipo": "application/pdf",
            "tamanho": 49197
        }
    },
    {
        "sequencia": 29,
        "nome": "Sentença.html",
        "tipo": "Sentença",
        "hrefBinario": "/processos/5000315-75.2025.4.03.6327/documentos/5e0131cb-2a0a-5f82-9d2c-4b74bc677824/binario",
        "hrefTexto": "/processos/5000315-75.2025.4.03.6327/documentos/5e0131cb-2a0a-5f82-9d2c-4b74bc677824/texto",
        "arquivo": {
            "tipo": "text/html",
            "tamanho": 13257
        }
    }
]

OUTPUT_DIR = "data/document_downloads"
os.makedirs(OUTPUT_DIR, exist_ok=True)

async def baixar_documento_binario(client: httpx.AsyncClient, url: str, token: str, output_path: str, document_info: Dict[str, Any]) -> Dict[str, Any]:
    """Baixar documento binário usando URL absoluta construída."""
    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": "PDPJ-API-Client/1.0",
        "Accept": "application/pdf,application/octet-stream,text/html,*/*"
    }
    
    try:
        logger.info(f"🔗 Baixando: {url}")
        response = await client.get(url, headers=headers, timeout=60.0, follow_redirects=True)
        
        content = response.content
        content_type = response.headers.get("Content-Type", "N/A")
        content_length = len(content)
        
        logger.info(f"📊 Status: {response.status_code}")
        logger.info(f"📊 Content-Type: {content_type}")
        logger.info(f"📊 Content-Length: {content_length}")
        
        if response.status_code == 200:
            # Verificar se é PDF válido
            if "application/pdf" in content_type or content.startswith(b"%PDF"):
                logger.info("🎉 PDF válido detectado!")
                with open(output_path, "wb") as f:
                    f.write(content)
                logger.info(f"💾 PDF salvo em: {output_path}")
                
                return {
                    "success": True,
                    "status_code": response.status_code,
                    "content_type": content_type,
                    "content_length": content_length,
                    "file_saved": output_path,
                    "is_pdf": True
                }
            elif "text/html" in content_type or content.startswith(b"<!DOCTYPE html"):
                logger.warning("⚠️ HTML retornado (portal web)")
                return {
                    "success": False,
                    "status_code": response.status_code,
                    "content_type": content_type,
                    "content_length": content_length,
                    "error": "HTML retornado (portal web)",
                    "is_pdf": False
                }
            else:
                logger.info(f"📄 Conteúdo inesperado: {content_type}")
                # Salvar mesmo assim para análise
                with open(output_path, "wb") as f:
                    f.write(content)
                logger.info(f"💾 Arquivo salvo em: {output_path}")
                
                return {
                    "success": True,
                    "status_code": response.status_code,
                    "content_type": content_type,
                    "content_length": content_length,
                    "file_saved": output_path,
                    "is_pdf": False
                }
        else:
            logger.error(f"❌ Erro HTTP: {response.status_code}")
            return {
                "success": False,
                "status_code": response.status_code,
                "content_type": content_type,
                "content_length": content_length,
                "error": f"HTTP {response.status_code}",
                "is_pdf": False
            }
            
    except Exception as e:
        logger.error(f"❌ Erro na requisição: {e}")
        return {
            "success": False,
            "error": str(e),
            "is_pdf": False
        }

async def baixar_documento_texto(client: httpx.AsyncClient, url: str, token: str, output_path: str, document_info: Dict[str, Any]) -> Dict[str, Any]:
    """Baixar documento texto usando URL absoluta construída."""
    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": "PDPJ-API-Client/1.0",
        "Accept": "text/html,text/plain,application/json,*/*"
    }
    
    try:
        logger.info(f"🔗 Baixando texto: {url}")
        response = await client.get(url, headers=headers, timeout=60.0, follow_redirects=True)
        
        content = response.content
        content_type = response.headers.get("Content-Type", "N/A")
        content_length = len(content)
        
        logger.info(f"📊 Status: {response.status_code}")
        logger.info(f"📊 Content-Type: {content_type}")
        logger.info(f"📊 Content-Length: {content_length}")
        
        if response.status_code == 200:
            # Salvar o conteúdo
            with open(output_path, "wb") as f:
                f.write(content)
            logger.info(f"💾 Texto salvo em: {output_path}")
            
            return {
                "success": True,
                "status_code": response.status_code,
                "content_type": content_type,
                "content_length": content_length,
                "file_saved": output_path
            }
        else:
            logger.error(f"❌ Erro HTTP: {response.status_code}")
            return {
                "success": False,
                "status_code": response.status_code,
                "content_type": content_type,
                "content_length": content_length,
                "error": f"HTTP {response.status_code}"
            }
            
    except Exception as e:
        logger.error(f"❌ Erro na requisição: {e}")
        return {
            "success": False,
            "error": str(e)
        }

async def test_document_downloads():
    """Testar download de todos os documentos usando URLs absolutas."""
    logger.info("🚀 Testando download de documentos usando URLs absolutas")
    
    results = []
    
    async with httpx.AsyncClient(verify=False, timeout=60.0) as client:
        for doc in TEST_DOCUMENTS:
            logger.info(f"\n📄 Testando documento: {doc['nome']}")
            logger.info(f"📋 Tipo: {doc['tipo']}")
            logger.info(f"📊 Tamanho esperado: {doc['arquivo']['tamanho']} bytes")
            
            # Construir URLs absolutas
            url_binario = API_BASE_URL + doc["hrefBinario"]
            url_texto = API_BASE_URL + doc["hrefTexto"]
            
            logger.info(f"🔗 URL Binário: {url_binario}")
            logger.info(f"🔗 URL Texto: {url_texto}")
            
            # Preparar caminhos de saída
            doc_name_safe = doc["nome"].replace(" ", "_").replace("/", "_")
            output_binario = os.path.join(OUTPUT_DIR, f"{doc['sequencia']:02d}_{doc_name_safe}")
            output_texto = os.path.join(OUTPUT_DIR, f"{doc['sequencia']:02d}_{doc_name_safe}.texto")
            
            # Testar download binário
            logger.info("=" * 50)
            logger.info("TESTE 1: Download Binário")
            logger.info("=" * 50)
            result_binario = await baixar_documento_binario(client, url_binario, TOKEN, output_binario, doc)
            
            # Testar download texto
            logger.info("\n" + "=" * 50)
            logger.info("TESTE 2: Download Texto")
            logger.info("=" * 50)
            result_texto = await baixar_documento_texto(client, url_texto, TOKEN, output_texto, doc)
            
            # Consolidar resultados
            doc_result = {
                "documento": doc["nome"],
                "sequencia": doc["sequencia"],
                "tipo": doc["tipo"],
                "tamanho_esperado": doc["arquivo"]["tamanho"],
                "tipo_esperado": doc["arquivo"]["tipo"],
                "url_binario": url_binario,
                "url_texto": url_texto,
                "download_binario": result_binario,
                "download_texto": result_texto
            }
            
            results.append(doc_result)
            
            # Pequena pausa entre documentos
            await asyncio.sleep(1.0)
    
    return results

async def main():
    """Função principal."""
    logger.info("🎯 Teste de Download de Documentos - URLs Absolutas")
    logger.info("=" * 60)
    
    results = await test_document_downloads()
    
    # Análise dos resultados
    logger.info("\n📊 ANÁLISE DOS RESULTADOS:")
    logger.info("=" * 60)
    
    total_docs = len(results)
    binario_success = sum(1 for r in results if r["download_binario"].get("success", False))
    texto_success = sum(1 for r in results if r["download_texto"].get("success", False))
    pdf_success = sum(1 for r in results if r["download_binario"].get("is_pdf", False))
    
    logger.info(f"📈 Total de documentos testados: {total_docs}")
    logger.info(f"✅ Downloads binários bem-sucedidos: {binario_success}")
    logger.info(f"✅ Downloads de texto bem-sucedidos: {texto_success}")
    logger.info(f"🎉 PDFs válidos baixados: {pdf_success}")
    
    logger.info("\n📋 DETALHES POR DOCUMENTO:")
    for r in results:
        logger.info(f"\n📄 {r['documento']} (Seq: {r['sequencia']})")
        logger.info(f"  📋 Tipo: {r['tipo']}")
        logger.info(f"  📊 Tamanho esperado: {r['tamanho_esperado']} bytes")
        
        # Resultado binário
        bin_result = r["download_binario"]
        if bin_result.get("success"):
            if bin_result.get("is_pdf"):
                logger.info(f"  🎉 Binário: PDF válido ({bin_result['content_length']} bytes)")
            else:
                logger.info(f"  ✅ Binário: Sucesso ({bin_result['content_length']} bytes, {bin_result['content_type']})")
        else:
            logger.info(f"  ❌ Binário: {bin_result.get('error', 'Falha')}")
        
        # Resultado texto
        txt_result = r["download_texto"]
        if txt_result.get("success"):
            logger.info(f"  ✅ Texto: Sucesso ({txt_result['content_length']} bytes, {txt_result['content_type']})")
        else:
            logger.info(f"  ❌ Texto: {txt_result.get('error', 'Falha')}")
    
    # Salvar resultados
    results_filename = os.path.join(OUTPUT_DIR, "document_download_results.json")
    with open(results_filename, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    logger.info(f"\n💾 Resultados salvos em {results_filename}")
    
    if pdf_success > 0:
        logger.info("🎉 SUCESSO! Pelo menos um PDF foi baixado com sucesso!")
    else:
        logger.warning("⚠️ Nenhum PDF válido foi baixado. Verifique os logs para detalhes.")
    
    logger.info("🏁 Teste concluído")

if __name__ == "__main__":
    asyncio.run(main())
