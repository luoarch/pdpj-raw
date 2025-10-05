#!/usr/bin/env python3
"""
Teste de verificação da limpeza de módulos redundantes.
"""

import os
import sys
from pathlib import Path
from loguru import logger

# Configurar logging
logger.remove()
logger.add(lambda msg: print(msg, end=""), level="INFO")

def test_cleanup_verification():
    """Verificar se a limpeza foi realizada corretamente."""
    
    print("🧹 VERIFICANDO LIMPEZA DE MÓDULOS REDUNDANTES")
    print("=" * 60)
    
    # Verificar se módulos antigos foram removidos
    removed_modules = [
        "app/services/advanced_cache_service.py",
        "app/services/monitoring_service.py",
        "app/services/ultra_fast_background_processor.py",
        "app/services/ultra_fast_database_service.py",
        "app/services/ultra_fast_document_service.py",
        "app/api/ultra_fast_processes.py"
    ]
    
    print("\n1️⃣ VERIFICANDO REMOÇÃO DE MÓDULOS ANTIGOS")
    print("-" * 50)
    
    for module in removed_modules:
        if os.path.exists(module):
            print(f"❌ Módulo ainda existe: {module}")
            return False
        else:
            print(f"✅ Módulo removido: {module}")
    
    # Verificar se novos módulos existem
    new_modules = [
        "app/core/dynamic_limits.py",
        "app/core/proactive_monitoring.py",
        "app/services/process_cache_service.py",
        "app/services/chunked_download_service.py",
        "app/utils/advanced_retry.py",
        "app/tasks/optimized_celery_tasks.py",
        "app/utils/pagination_utils.py",
        "app/utils/transaction_manager.py"
    ]
    
    print("\n2️⃣ VERIFICANDO EXISTÊNCIA DE NOVOS MÓDULOS")
    print("-" * 50)
    
    for module in new_modules:
        if os.path.exists(module):
            print(f"✅ Novo módulo existe: {module}")
        else:
            print(f"❌ Novo módulo não encontrado: {module}")
            return False
    
    # Verificar se imports foram atualizados
    print("\n3️⃣ VERIFICANDO ATUALIZAÇÃO DE IMPORTS")
    print("-" * 50)
    
    # Verificar app/api/monitoring.py
    try:
        with open("app/api/monitoring.py", "r") as f:
            content = f.read()
            
        if "from app.services.monitoring_service import" in content:
            print("❌ Import antigo ainda existe em monitoring.py")
            return False
        elif "from app.core.proactive_monitoring import" in content:
            print("✅ Imports atualizados em monitoring.py")
        else:
            print("⚠️ Imports não encontrados em monitoring.py")
            
    except Exception as e:
        print(f"❌ Erro ao verificar monitoring.py: {e}")
        return False
    
    # Verificar app/core/app_events.py
    try:
        with open("app/core/app_events.py", "r") as f:
            content = f.read()
            
        if "from app.services.advanced_cache_service import" in content:
            print("❌ Import antigo ainda existe em app_events.py")
            return False
        elif "from app.services.process_cache_service import" in content:
            print("✅ Imports atualizados em app_events.py")
        else:
            print("⚠️ Imports não encontrados em app_events.py")
            
    except Exception as e:
        print(f"❌ Erro ao verificar app_events.py: {e}")
        return False
    
    # Verificar app/core/router_config.py
    try:
        with open("app/core/router_config.py", "r") as f:
            content = f.read()
            
        if "ultra_fast_processes" in content:
            print("❌ Referência a ultra_fast_processes ainda existe em router_config.py")
            return False
        else:
            print("✅ Referências atualizadas em router_config.py")
            
    except Exception as e:
        print(f"❌ Erro ao verificar router_config.py: {e}")
        return False
    
    # Verificar se testes antigos foram removidos
    print("\n4️⃣ VERIFICANDO REMOÇÃO DE TESTES ANTIGOS")
    print("-" * 50)
    
    removed_tests = [
        "test_consolidated_client.py",
        "test_token_validator.py",
        "test_improved_client.py",
        "test_final_implementation.py"
    ]
    
    for test in removed_tests:
        if os.path.exists(test):
            print(f"❌ Teste antigo ainda existe: {test}")
            return False
        else:
            print(f"✅ Teste antigo removido: {test}")
    
    # Verificar se novos testes existem
    new_tests = [
        "test_enterprise_evolution.py",
        "test_improved_endpoints.py",
        "tests/load_tests_enterprise.py"
    ]
    
    for test in new_tests:
        if os.path.exists(test):
            print(f"✅ Novo teste existe: {test}")
        else:
            print(f"❌ Novo teste não encontrado: {test}")
            return False
    
    print("\n5️⃣ VERIFICANDO ESTRUTURA FINAL")
    print("-" * 50)
    
    # Verificar estrutura de diretórios
    expected_structure = {
        "app/core": ["dynamic_limits.py", "proactive_monitoring.py", "endpoint_rate_limiting.py"],
        "app/services": ["process_cache_service.py", "chunked_download_service.py"],
        "app/utils": ["advanced_retry.py", "pagination_utils.py", "transaction_manager.py"],
        "app/tasks": ["optimized_celery_tasks.py"]
    }
    
    for directory, files in expected_structure.items():
        if not os.path.exists(directory):
            print(f"❌ Diretório não existe: {directory}")
            return False
        
        for file in files:
            file_path = os.path.join(directory, file)
            if not os.path.exists(file_path):
                print(f"❌ Arquivo não existe: {file_path}")
                return False
            else:
                print(f"✅ Arquivo existe: {file_path}")
    
    print("\n🎉 VERIFICAÇÃO DE LIMPEZA CONCLUÍDA COM SUCESSO!")
    print("=" * 60)
    
    return True

def test_module_imports():
    """Testar se os novos módulos podem ser importados corretamente."""
    
    print("\n🧪 TESTANDO IMPORTS DOS NOVOS MÓDULOS")
    print("=" * 50)
    
    try:
        # Testar imports dos novos módulos
        from app.core.dynamic_limits import environment_limits, get_current_limits
        print("✅ dynamic_limits importado com sucesso")
        
        from app.core.proactive_monitoring import proactive_monitor, get_active_alerts
        print("✅ proactive_monitoring importado com sucesso")
        
        from app.services.process_cache_service import process_cache_service
        print("✅ process_cache_service importado com sucesso")
        
        from app.services.chunked_download_service import chunked_download_service
        print("✅ chunked_download_service importado com sucesso")
        
        from app.utils.advanced_retry import advanced_retry, RetryConfigs
        print("✅ advanced_retry importado com sucesso")
        
        from app.utils.pagination_utils import create_process_pagination_params
        print("✅ pagination_utils importado com sucesso")
        
        from app.utils.transaction_manager import TransactionManager
        print("✅ transaction_manager importado com sucesso")
        
        print("\n✅ TODOS OS IMPORTS FUNCIONARAM CORRETAMENTE!")
        return True
        
    except Exception as e:
        print(f"\n❌ ERRO NO IMPORT: {e}")
        return False

if __name__ == "__main__":
    print("🧹 INICIANDO VERIFICAÇÃO DE LIMPEZA")
    print("=" * 60)
    
    # Verificar limpeza
    cleanup_success = test_cleanup_verification()
    
    # Testar imports
    imports_success = test_module_imports()
    
    # Resultado final
    print("\n" + "=" * 60)
    if cleanup_success and imports_success:
        print("🎉 LIMPEZA DE MÓDULOS REDUNDANTES CONCLUÍDA COM SUCESSO!")
        print("✅ Todos os módulos antigos foram removidos")
        print("✅ Todos os novos módulos estão funcionando")
        print("✅ Imports foram atualizados corretamente")
        print("✅ Estrutura está limpa e organizada")
    else:
        print("❌ ALGUNS PROBLEMAS FORAM ENCONTRADOS")
        print("⚠️ Verifique os logs para detalhes")
    
    print("=" * 60)
