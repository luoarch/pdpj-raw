#!/usr/bin/env python3
"""
Script para testar a funcionalidade de documentos e medir performance.
"""

import asyncio
import time
import httpx
import json
from typing import Dict, Any

# Configurações
API_BASE_URL = "http://localhost:8000"
API_KEY = "pdpj_admin_xYlOkmPaK9oO0xe_BdhoGBZvALr7YuHKI0gTgePAbZU"
PROCESS_NUMBER = "1000145-91.2023.8.26.0597"

# Headers padrão
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

async def test_endpoint_performance(
    client: httpx.AsyncClient, 
    endpoint: str, 
    description: str
) -> Dict[str, Any]:
    """Testa um endpoint e mede o tempo de resposta."""
    print(f"\n🔍 Testando: {description}")
    print(f"📍 Endpoint: {endpoint}")
    
    start_time = time.time()
    
    try:
        response = await client.get(endpoint, headers=HEADERS)
        end_time = time.time()
        
        response_time = end_time - start_time
        
        result = {
            "endpoint": endpoint,
            "description": description,
            "status_code": response.status_code,
            "response_time": response_time,
            "success": response.status_code == 200,
            "response_size": len(response.content) if response.content else 0
        }
        
        if response.status_code == 200:
            try:
                data = response.json()
                result["data"] = data
                
                # Extrair informações específicas
                if "documents" in data:
                    result["total_documents"] = data.get("total_documents", 0)
                    result["downloaded_documents"] = data.get("downloaded_documents", 0)
                    result["documents_with_urls"] = len([d for d in data.get("documents", []) if d.get("download_url")])
                
                print(f"✅ Sucesso! Tempo: {response_time:.3f}s")
                print(f"📊 Status: {response.status_code}")
                print(f"📄 Tamanho da resposta: {result['response_size']} bytes")
                
                if "total_documents" in result:
                    print(f"📁 Total de documentos: {result['total_documents']}")
                    print(f"⬇️  Documentos baixados: {result['downloaded_documents']}")
                    print(f"🔗 Documentos com URLs: {result['documents_with_urls']}")
                
            except json.JSONDecodeError:
                result["error"] = "Resposta não é JSON válido"
                print(f"❌ Erro: Resposta não é JSON válido")
        else:
            result["error"] = response.text
            print(f"❌ Erro! Status: {response.status_code}")
            print(f"📝 Resposta: {response.text[:200]}...")
        
        return result
        
    except Exception as e:
        end_time = time.time()
        response_time = end_time - start_time
        
        result = {
            "endpoint": endpoint,
            "description": description,
            "status_code": None,
            "response_time": response_time,
            "success": False,
            "error": str(e)
        }
        
        print(f"💥 Exceção! Tempo: {response_time:.3f}s")
        print(f"❌ Erro: {str(e)}")
        
        return result

async def test_download_documents_endpoint(
    client: httpx.AsyncClient, 
    process_number: str
) -> Dict[str, Any]:
    """Testa o endpoint de download de documentos."""
    endpoint = f"{API_BASE_URL}/api/v1/processes/{process_number}/download-documents"
    
    print(f"\n⬇️  Testando download de documentos")
    print(f"📍 Endpoint: {endpoint}")
    
    start_time = time.time()
    
    try:
        response = await client.post(endpoint, headers=HEADERS)
        end_time = time.time()
        
        response_time = end_time - start_time
        
        result = {
            "endpoint": endpoint,
            "description": "Download de documentos",
            "status_code": response.status_code,
            "response_time": response_time,
            "success": response.status_code in [200, 202],
            "response_size": len(response.content) if response.content else 0
        }
        
        if response.status_code in [200, 202]:
            try:
                data = response.json()
                result["data"] = data
                
                print(f"✅ Sucesso! Tempo: {response_time:.3f}s")
                print(f"📊 Status: {response.status_code}")
                print(f"📄 Resposta: {json.dumps(data, indent=2, ensure_ascii=False)}")
                
            except json.JSONDecodeError:
                result["error"] = "Resposta não é JSON válido"
                print(f"❌ Erro: Resposta não é JSON válido")
        else:
            result["error"] = response.text
            print(f"❌ Erro! Status: {response.status_code}")
            print(f"📝 Resposta: {response.text[:200]}...")
        
        return result
        
    except Exception as e:
        end_time = time.time()
        response_time = end_time - start_time
        
        result = {
            "endpoint": endpoint,
            "description": "Download de documentos",
            "status_code": None,
            "response_time": response_time,
            "success": False,
            "error": str(e)
        }
        
        print(f"💥 Exceção! Tempo: {response_time:.3f}s")
        print(f"❌ Erro: {str(e)}")
        
        return result

async def main():
    """Função principal para executar todos os testes."""
    print("🚀 Iniciando testes de performance da funcionalidade de documentos")
    print(f"🎯 Processo: {PROCESS_NUMBER}")
    print(f"🌐 API Base: {API_BASE_URL}")
    
    # Lista de endpoints para testar
    endpoints_to_test = [
        {
            "endpoint": f"{API_BASE_URL}/api/v1/processes/{PROCESS_NUMBER}/files",
            "description": "Listar documentos (endpoint normal)"
        },
        {
            "endpoint": f"{API_BASE_URL}/api/v1/ultra-fast/processes/{PROCESS_NUMBER}/files",
            "description": "Listar documentos (endpoint ultra-fast)"
        }
    ]
    
    results = []
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Testar endpoints de listagem
        for test_case in endpoints_to_test:
            result = await test_endpoint_performance(
                client, 
                test_case["endpoint"], 
                test_case["description"]
            )
            results.append(result)
            
            # Pequena pausa entre testes
            await asyncio.sleep(1)
        
        # Testar endpoint de download
        download_result = await test_download_documents_endpoint(client, PROCESS_NUMBER)
        results.append(download_result)
        
        # Aguardar um pouco e testar novamente os endpoints de listagem
        print(f"\n⏳ Aguardando 5 segundos para testar novamente...")
        await asyncio.sleep(5)
        
        print(f"\n🔄 Testando novamente após download...")
        for test_case in endpoints_to_test:
            result = await test_endpoint_performance(
                client, 
                test_case["endpoint"], 
                f"{test_case['description']} (após download)"
            )
            results.append(result)
            
            await asyncio.sleep(1)
    
    # Resumo dos resultados
    print(f"\n" + "="*80)
    print(f"📊 RESUMO DOS TESTES")
    print(f"="*80)
    
    successful_tests = [r for r in results if r["success"]]
    failed_tests = [r for r in results if not r["success"]]
    
    print(f"✅ Testes bem-sucedidos: {len(successful_tests)}")
    print(f"❌ Testes falharam: {len(failed_tests)}")
    
    if successful_tests:
        print(f"\n📈 PERFORMANCE DOS TESTES BEM-SUCEDIDOS:")
        for result in successful_tests:
            print(f"  • {result['description']}: {result['response_time']:.3f}s")
    
    if failed_tests:
        print(f"\n❌ TESTES QUE FALHARAM:")
        for result in failed_tests:
            print(f"  • {result['description']}: {result.get('error', 'Erro desconhecido')}")
    
    # Comparação de performance
    normal_endpoint = [r for r in successful_tests if "normal" in r["description"]]
    ultra_fast_endpoint = [r for r in successful_tests if "ultra-fast" in r["description"]]
    
    if normal_endpoint and ultra_fast_endpoint:
        print(f"\n⚡ COMPARAÇÃO DE PERFORMANCE:")
        normal_time = normal_endpoint[0]["response_time"]
        ultra_fast_time = ultra_fast_endpoint[0]["response_time"]
        
        print(f"  • Endpoint normal: {normal_time:.3f}s")
        print(f"  • Endpoint ultra-fast: {ultra_fast_time:.3f}s")
        
        if ultra_fast_time < normal_time:
            improvement = ((normal_time - ultra_fast_time) / normal_time) * 100
            print(f"  🚀 Ultra-fast é {improvement:.1f}% mais rápido!")
        else:
            print(f"  ⚠️  Ultra-fast não foi mais rápido neste teste")
    
    # Salvar resultados em arquivo
    with open("test_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n💾 Resultados salvos em: test_results.json")
    print(f"🎉 Testes concluídos!")

if __name__ == "__main__":
    asyncio.run(main())
