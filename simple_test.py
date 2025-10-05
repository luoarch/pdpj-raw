#!/usr/bin/env python3
"""
Teste simples para verificar endpoints de documentos.
"""

import time
import requests

API_BASE = "http://localhost:8000"
API_KEY = "pdpj_admin_xYlOkmPaK9oO0xe_BdhoGBZvALr7YuHKI0gTgePAbZU"
PROCESS_NUMBER = "1000145-91.2023.8.26.0597"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

def test_endpoint(url, description):
    print(f"\n🔍 Testando: {description}")
    print(f"📍 URL: {url}")
    
    start_time = time.time()
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        end_time = time.time()
        
        response_time = end_time - start_time
        
        print(f"⏱️  Tempo: {response_time:.3f}s")
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                total_docs = data.get('total_documents', 0)
                downloaded_docs = data.get('downloaded_documents', 0)
                print(f"📁 Total de documentos: {total_docs}")
                print(f"⬇️  Documentos baixados: {downloaded_docs}")
                print(f"✅ Sucesso!")
            except:
                print(f"❌ Resposta não é JSON válido")
        else:
            print(f"❌ Erro: {response.text[:100]}...")
            
    except Exception as e:
        end_time = time.time()
        response_time = end_time - start_time
        print(f"💥 Exceção após {response_time:.3f}s: {str(e)}")

def test_download_endpoint():
    url = f"{API_BASE}/api/v1/processes/{PROCESS_NUMBER}/download-documents"
    print(f"\n⬇️  Testando download de documentos")
    print(f"📍 URL: {url}")
    
    start_time = time.time()
    
    try:
        response = requests.post(url, headers=headers, timeout=30)
        end_time = time.time()
        
        response_time = end_time - start_time
        
        print(f"⏱️  Tempo: {response_time:.3f}s")
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code in [200, 202]:
            try:
                data = response.json()
                print(f"📄 Resposta: {data}")
                print(f"✅ Sucesso!")
            except:
                print(f"❌ Resposta não é JSON válido")
        else:
            print(f"❌ Erro: {response.text[:100]}...")
            
    except Exception as e:
        end_time = time.time()
        response_time = end_time - start_time
        print(f"💥 Exceção após {response_time:.3f}s: {str(e)}")

if __name__ == "__main__":
    print("🚀 Testando endpoints de documentos")
    print(f"🎯 Processo: {PROCESS_NUMBER}")
    
    # Testar endpoints de listagem
    test_endpoint(
        f"{API_BASE}/api/v1/processes/{PROCESS_NUMBER}/files",
        "Listar documentos (endpoint normal)"
    )
    
    test_endpoint(
        f"{API_BASE}/api/v1/ultra-fast/processes/{PROCESS_NUMBER}/files",
        "Listar documentos (endpoint ultra-fast)"
    )
    
    # Testar endpoint de download
    test_download_endpoint()
    
    print(f"\n🎉 Testes concluídos!")
