#!/usr/bin/env python3
"""
Script robusto para download de documentos PDPJ seguindo as melhores práticas:
- Montagem correta de URLs absolutas
- Autenticação JWT adequada
- Headers apropriados
- Tratamento de erros robusto
- Extensões de arquivo corretas
"""

import asyncio
import httpx
import os
import json
from loguru import logger
from typing import List, Dict, Any, Optional
from pathlib import Path

# Configurar logging
logger.add("test_robust_document_download.log", rotation="1 MB")

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

OUTPUT_DIR = "data/robust_downloads"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def get_file_extension_from_mime_type(mime_type: str) -> str:
    """Extrai a extensão do arquivo a partir do tipo MIME."""
    mime_to_extension = {
        "application/pdf": "pdf",
        "text/html": "html",
        "text/plain": "txt",
        "image/jpeg": "jpg",
        "image/png": "png",
        "application/msword": "doc",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
        "application/vnd.ms-excel": "xls",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "xlsx"
    }
    return mime_to_extension.get(mime_type, mime_type.split("/")[-1] if "/" in mime_type else "bin")

def build_absolute_url(api_base_url: str, href: str) -> str:
    """Constrói URL absoluta a partir da base da API e href relativo."""
    return api_base_url + href

def get_robust_headers(token: str) -> Dict[str, str]:
    """Retorna headers robustos para requisições à API PDPJ."""
    return {
        "Authorization": f"Bearer {token}",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/pdf,application/octet-stream,text/html,text/plain,*/*",
        "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache"
    }

async def baixar_documento_robusto(
    client: httpx.AsyncClient, 
    api_base_url: str, 
    href: str, 
    token: str, 
    output_path: str, 
    document_info: Dict[str, Any],
    download_type: str = "binario"
) -> Dict[str, Any]:
    """
    Baixa documento de forma robusta seguindo as melhores práticas.
    
    Args:
        client: Cliente HTTP assíncrono
        api_base_url: URL base da API
        href: Caminho relativo do documento
        token: Token JWT de autenticação
        output_path: Caminho para salvar o arquivo
        document_info: Informações do documento
        download_type: Tipo de download ("binario" ou "texto")
    """
    # Construir URL absoluta
    url = build_absolute_url(api_base_url, href)
    
    # Headers robustos
    headers = get_robust_headers(token)
    
    # Headers específicos baseados no tipo de download
    if download_type == "binario":
        headers["Accept"] = "application/pdf,application/octet-stream,image/*,*/*"
    else:
        headers["Accept"] = "text/html,text/plain,application/json,*/*"
    
    try:
        logger.info(f"🔗 Baixando {download_type}: {url}")
        logger.info(f"📋 Documento: {document_info['nome']}")
        logger.info(f"📊 Tamanho esperado: {document_info['arquivo']['tamanho']} bytes")
        
        # Fazer requisição com timeout e redirects
        response = await client.get(
            url, 
            headers=headers, 
            timeout=60.0, 
            follow_redirects=True
        )
        
        content = response.content
        content_type = response.headers.get("Content-Type", "N/A")
        content_length = len(content)
        
        logger.info(f"📊 Status: {response.status_code}")
        logger.info(f"📊 Content-Type: {content_type}")
        logger.info(f"📊 Content-Length: {content_length}")
        logger.info(f"📊 Content-Length esperado: {document_info['arquivo']['tamanho']} bytes")
        
        # Verificar se o download foi bem-sucedido
        if response.status_code == 200:
            # Verificar se é PDF válido
            if download_type == "binario" and ("application/pdf" in content_type or content.startswith(b"%PDF")):
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
                    "is_pdf": True,
                    "is_valid_size": abs(content_length - document_info['arquivo']['tamanho']) < 1000
                }
            elif download_type == "texto" and ("text/html" in content_type or "text/plain" in content_type):
                logger.info("📄 Conteúdo de texto detectado!")
                with open(output_path, "wb") as f:
                    f.write(content)
                logger.info(f"💾 Texto salvo em: {output_path}")
                
                return {
                    "success": True,
                    "status_code": response.status_code,
                    "content_type": content_type,
                    "content_length": content_length,
                    "file_saved": output_path,
                    "is_text": True
                }
            elif "text/html" in content_type and content.startswith(b"<!DOCTYPE html"):
                logger.warning("⚠️ HTML do portal web retornado")
                # Salvar para análise
                with open(output_path, "wb") as f:
                    f.write(content)
                logger.info(f"💾 HTML salvo para análise: {output_path}")
                
                return {
                    "success": False,
                    "status_code": response.status_code,
                    "content_type": content_type,
                    "content_length": content_length,
                    "file_saved": output_path,
                    "error": "HTML do portal web retornado",
                    "is_portal_html": True
                }
            else:
                logger.info(f"📄 Conteúdo inesperado: {content_type}")
                # Salvar mesmo assim para análise
                with open(output_path, "wb") as f:
                    f.write(content)
                logger.info(f"💾 Arquivo salvo para análise: {output_path}")
                
                return {
                    "success": True,
                    "status_code": response.status_code,
                    "content_type": content_type,
                    "content_length": content_length,
                    "file_saved": output_path,
                    "is_unexpected": True
                }
        else:
            logger.error(f"❌ Erro HTTP: {response.status_code}")
            return {
                "success": False,
                "status_code": response.status_code,
                "content_type": content_type,
                "content_length": content_length,
                "error": f"HTTP {response.status_code}",
                "response_text": response.text[:200] if hasattr(response, 'text') else None
            }
            
    except httpx.HTTPStatusError as e:
        logger.error(f"❌ Erro HTTP: {e}")
        return {
            "success": False,
            "error": f"HTTP {e.response.status_code}: {e}",
            "status_code": e.response.status_code if hasattr(e, 'response') else None
        }
    except httpx.RequestError as e:
        logger.error(f"❌ Erro de requisição: {e}")
        return {
            "success": False,
            "error": f"Request error: {e}"
        }
    except Exception as e:
        logger.error(f"❌ Erro inesperado: {e}")
        return {
            "success": False,
            "error": f"Unexpected error: {e}"
        }

async def test_robust_document_downloads():
    """Testar download robusto de todos os documentos."""
    logger.info("🚀 Testando download robusto de documentos")
    
    results = []
    
    async with httpx.AsyncClient(verify=False, timeout=60.0) as client:
        for doc in TEST_DOCUMENTS:
            logger.info(f"\n{'='*60}")
            logger.info(f"📄 Testando documento: {doc['nome']}")
            logger.info(f"📋 Tipo: {doc['tipo']}")
            logger.info(f"📊 Tamanho esperado: {doc['arquivo']['tamanho']} bytes")
            logger.info(f"📊 Tipo MIME: {doc['arquivo']['tipo']}")
            logger.info(f"{'='*60}")
            
            # Preparar caminhos de saída
            doc_name_safe = doc["nome"].replace(" ", "_").replace("/", "_").replace(".", "_")
            mime_type = doc["arquivo"]["tipo"]
            extension = get_file_extension_from_mime_type(mime_type)
            
            output_binario = os.path.join(OUTPUT_DIR, f"{doc['sequencia']:02d}_{doc_name_safe}_binario.{extension}")
            output_texto = os.path.join(OUTPUT_DIR, f"{doc['sequencia']:02d}_{doc_name_safe}_texto.{extension}")
            
            # Testar download binário
            logger.info("\n" + "="*50)
            logger.info("TESTE 1: Download Binário Robusto")
            logger.info("="*50)
            result_binario = await baixar_documento_robusto(
                client, API_BASE_URL, doc["hrefBinario"], TOKEN, 
                output_binario, doc, "binario"
            )
            
            # Testar download texto
            logger.info("\n" + "="*50)
            logger.info("TESTE 2: Download Texto Robusto")
            logger.info("="*50)
            result_texto = await baixar_documento_robusto(
                client, API_BASE_URL, doc["hrefTexto"], TOKEN, 
                output_texto, doc, "texto"
            )
            
            # Consolidar resultados
            doc_result = {
                "documento": doc["nome"],
                "sequencia": doc["sequencia"],
                "tipo": doc["tipo"],
                "tamanho_esperado": doc["arquivo"]["tamanho"],
                "tipo_esperado": doc["arquivo"]["tipo"],
                "href_binario": doc["hrefBinario"],
                "href_texto": doc["hrefTexto"],
                "url_binario": build_absolute_url(API_BASE_URL, doc["hrefBinario"]),
                "url_texto": build_absolute_url(API_BASE_URL, doc["hrefTexto"]),
                "download_binario": result_binario,
                "download_texto": result_texto
            }
            
            results.append(doc_result)
            
            # Pequena pausa entre documentos
            await asyncio.sleep(1.0)
    
    return results

async def main():
    """Função principal."""
    logger.info("🎯 Teste Robusto de Download de Documentos PDPJ")
    logger.info("=" * 60)
    logger.info("📋 Seguindo melhores práticas:")
    logger.info("  ✅ URLs absolutas construídas corretamente")
    logger.info("  ✅ Headers robustos incluídos")
    logger.info("  ✅ Autenticação JWT adequada")
    logger.info("  ✅ Extensões de arquivo corretas")
    logger.info("  ✅ Tratamento de erros robusto")
    logger.info("=" * 60)
    
    results = await test_robust_document_downloads()
    
    # Análise dos resultados
    logger.info("\n📊 ANÁLISE DOS RESULTADOS:")
    logger.info("=" * 60)
    
    total_docs = len(results)
    binario_success = sum(1 for r in results if r["download_binario"].get("success", False))
    texto_success = sum(1 for r in results if r["download_texto"].get("success", False))
    pdf_success = sum(1 for r in results if r["download_binario"].get("is_pdf", False))
    portal_html_count = sum(1 for r in results if r["download_binario"].get("is_portal_html", False))
    
    logger.info(f"📈 Total de documentos testados: {total_docs}")
    logger.info(f"✅ Downloads binários bem-sucedidos: {binario_success}")
    logger.info(f"✅ Downloads de texto bem-sucedidos: {texto_success}")
    logger.info(f"🎉 PDFs válidos baixados: {pdf_success}")
    logger.info(f"⚠️ Respostas HTML do portal: {portal_html_count}")
    
    logger.info("\n📋 DETALHES POR DOCUMENTO:")
    for r in results:
        logger.info(f"\n📄 {r['documento']} (Seq: {r['sequencia']})")
        logger.info(f"  📋 Tipo: {r['tipo']}")
        logger.info(f"  📊 Tamanho esperado: {r['tamanho_esperado']} bytes")
        logger.info(f"  📊 Tipo MIME: {r['tipo_esperado']}")
        
        # Resultado binário
        bin_result = r["download_binario"]
        if bin_result.get("success"):
            if bin_result.get("is_pdf"):
                size_valid = "✅" if bin_result.get("is_valid_size") else "⚠️"
                logger.info(f"  🎉 Binário: PDF válido ({bin_result['content_length']} bytes) {size_valid}")
            elif bin_result.get("is_unexpected"):
                logger.info(f"  📄 Binário: Conteúdo inesperado ({bin_result['content_length']} bytes, {bin_result['content_type']})")
            else:
                logger.info(f"  ✅ Binário: Sucesso ({bin_result['content_length']} bytes, {bin_result['content_type']})")
        else:
            if bin_result.get("is_portal_html"):
                logger.info(f"  ⚠️ Binário: HTML do portal ({bin_result['content_length']} bytes)")
            else:
                logger.info(f"  ❌ Binário: {bin_result.get('error', 'Falha')}")
        
        # Resultado texto
        txt_result = r["download_texto"]
        if txt_result.get("success"):
            if txt_result.get("is_text"):
                logger.info(f"  ✅ Texto: Conteúdo de texto ({txt_result['content_length']} bytes, {txt_result['content_type']})")
            else:
                logger.info(f"  ✅ Texto: Sucesso ({txt_result['content_length']} bytes, {txt_result['content_type']})")
        else:
            logger.info(f"  ❌ Texto: {txt_result.get('error', 'Falha')}")
    
    # Salvar resultados
    results_filename = os.path.join(OUTPUT_DIR, "robust_download_results.json")
    with open(results_filename, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    logger.info(f"\n💾 Resultados salvos em {results_filename}")
    
    if pdf_success > 0:
        logger.info("🎉 SUCESSO! Pelo menos um PDF foi baixado com sucesso!")
    elif portal_html_count == total_docs:
        logger.warning("⚠️ CONFIRMADO: Todos os downloads retornam HTML do portal web")
        logger.info("💡 A API PDPJ não suporta download direto de documentos")
    else:
        logger.warning("⚠️ Resultados mistos. Verifique os logs para detalhes.")
    
    logger.info("🏁 Teste robusto concluído")

if __name__ == "__main__":
    asyncio.run(main())
