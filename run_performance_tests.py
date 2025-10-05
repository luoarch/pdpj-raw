#!/usr/bin/env python3
"""
Script para executar testes de performance com API automática.
"""

import subprocess
import time
import signal
import sys
import os
import asyncio
import requests
from pathlib import Path

class APIManager:
    """Gerenciador da API para testes."""
    
    def __init__(self):
        self.process = None
        self.api_url = "http://localhost:8000"
    
    def start_api(self):
        """Iniciar a API."""
        print("🚀 Iniciando API PDPJ...")
        
        try:
            self.process = subprocess.Popen(
                ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            print(f"✅ API iniciada com PID: {self.process.pid}")
            return self.wait_for_api()
            
        except Exception as e:
            print(f"❌ Erro ao iniciar API: {e}")
            return False
    
    def wait_for_api(self, max_wait=30):
        """Aguardar API ficar disponível."""
        print("⏳ Aguardando API ficar disponível...")
        
        for attempt in range(max_wait):
            try:
                response = requests.get(f"{self.api_url}/health", timeout=2)
                if response.status_code == 200:
                    print("✅ API está disponível!")
                    return True
            except:
                pass
            
            time.sleep(1)
            print(f"   Tentativa {attempt + 1}/{max_wait}...")
        
        print("❌ API não ficou disponível a tempo")
        return False
    
    def stop_api(self):
        """Parar a API."""
        if self.process:
            print("🛑 Parando API...")
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
                print("✅ API parada com sucesso")
            except subprocess.TimeoutExpired:
                print("⚠️ Forçando parada da API...")
                self.process.kill()
                self.process.wait()
            except Exception as e:
                print(f"⚠️ Erro ao parar API: {e}")
    
    def is_running(self):
        """Verificar se API está rodando."""
        return self.process and self.process.poll() is None

async def run_performance_tests():
    """Executar testes de performance."""
    print("🧪 Executando testes de performance...")
    
    try:
        # Executar script de performance
        result = subprocess.run(
            ["python", "test_performance_load.py"],
            capture_output=True,
            text=True,
            timeout=300  # 5 minutos timeout
        )
        
        print("📊 RESULTADOS DOS TESTES:")
        print("=" * 50)
        print(result.stdout)
        
        if result.stderr:
            print("⚠️ ERROS:")
            print(result.stderr)
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("⏰ Testes excederam o tempo limite (5 minutos)")
        return False
    except Exception as e:
        print(f"❌ Erro ao executar testes: {e}")
        return False

def main():
    """Função principal."""
    api_manager = APIManager()
    
    try:
        # Iniciar API
        if not api_manager.start_api():
            print("❌ Não foi possível iniciar a API")
            return 1
        
        # Aguardar um pouco para garantir estabilidade
        print("⏳ Aguardando estabilização da API...")
        time.sleep(3)
        
        # Executar testes
        print("\n" + "="*60)
        print("🧪 INICIANDO TESTES DE PERFORMANCE")
        print("="*60)
        
        success = asyncio.run(run_performance_tests())
        
        if success:
            print("\n🎉 Testes de performance concluídos com sucesso!")
        else:
            print("\n⚠️ Alguns testes falharam, verifique os logs acima")
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n⏹️ Interrompido pelo usuário")
        return 1
    except Exception as e:
        print(f"❌ Erro: {e}")
        return 1
    finally:
        api_manager.stop_api()

if __name__ == "__main__":
    exit(main())
