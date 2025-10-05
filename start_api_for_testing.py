#!/usr/bin/env python3
"""
Script para iniciar a API PDPJ para testes de performance.
"""

import subprocess
import time
import signal
import sys
import os
from pathlib import Path

def start_api():
    """Iniciar a API PDPJ."""
    print("🚀 Iniciando API PDPJ para testes...")
    
    # Verificar se estamos no diretório correto
    if not Path("app/main.py").exists():
        print("❌ Arquivo app/main.py não encontrado!")
        return None
    
    try:
        # Iniciar a API em background
        process = subprocess.Popen(
            ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        print(f"✅ API iniciada com PID: {process.pid}")
        print("⏳ Aguardando API ficar disponível...")
        
        # Aguardar API ficar disponível
        import requests
        max_attempts = 30
        for attempt in range(max_attempts):
            try:
                response = requests.get("http://localhost:8000/health", timeout=2)
                if response.status_code == 200:
                    print("✅ API está disponível!")
                    return process
            except:
                pass
            
            time.sleep(1)
            print(f"   Tentativa {attempt + 1}/{max_attempts}...")
        
        print("❌ API não ficou disponível a tempo")
        process.terminate()
        return None
        
    except Exception as e:
        print(f"❌ Erro ao iniciar API: {e}")
        return None

def cleanup_process(process):
    """Limpar processo da API."""
    if process:
        print("🛑 Parando API...")
        try:
            process.terminate()
            process.wait(timeout=5)
            print("✅ API parada com sucesso")
        except subprocess.TimeoutExpired:
            print("⚠️ Forçando parada da API...")
            process.kill()
            process.wait()
        except Exception as e:
            print(f"⚠️ Erro ao parar API: {e}")

def main():
    """Função principal."""
    process = None
    
    try:
        # Iniciar API
        process = start_api()
        if not process:
            print("❌ Não foi possível iniciar a API")
            return 1
        
        print("\n🎯 API rodando! Execute os testes de performance agora.")
        print("💡 Pressione Ctrl+C para parar a API e sair")
        
        # Manter API rodando
        while True:
            time.sleep(1)
            
            # Verificar se processo ainda está rodando
            if process.poll() is not None:
                print("❌ API parou inesperadamente")
                break
                
    except KeyboardInterrupt:
        print("\n⏹️ Interrompido pelo usuário")
    except Exception as e:
        print(f"❌ Erro: {e}")
    finally:
        cleanup_process(process)
    
    return 0

if __name__ == "__main__":
    exit(main())
