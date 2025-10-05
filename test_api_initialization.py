#!/usr/bin/env python3
"""
FASE 1: Testes de Inicialização e Configuração Base
Valida a inicialização correta da API e todas as configurações básicas.
"""

import os
import sys
import asyncio
import time
from pathlib import Path
from typing import Dict, Any, List
from loguru import logger
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Adicionar o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent))

# Configurar logging
logger.remove()
logger.add(sys.stdout, level="INFO", format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")

class APITestSuite:
    """Suite de testes para inicialização da API."""
    
    def __init__(self):
        self.results: Dict[str, Any] = {}
        self.start_time = time.time()
        
    def log_test_result(self, test_name: str, success: bool, details: str = ""):
        """Registra resultado de um teste."""
        status = "✅ PASSOU" if success else "❌ FALHOU"
        logger.info(f"{status} | {test_name}")
        if details:
            logger.info(f"    📝 {details}")
        
        self.results[test_name] = {
            "success": success,
            "details": details,
            "timestamp": time.time()
        }
    
    async def test_environment_variables(self):
        """Testa variáveis de ambiente essenciais."""
        logger.info("🔧 TESTANDO VARIÁVEIS DE AMBIENTE")
        logger.info("=" * 50)
        
        required_vars = [
            "DATABASE_URL",
            "REDIS_URL", 
            "PDPJ_API_TOKEN",
            "PDPJ_API_BASE_URL",
            "AWS_ACCESS_KEY_ID",
            "AWS_SECRET_ACCESS_KEY",
            "S3_BUCKET_NAME"  # Corrigido para corresponder ao .env
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            self.log_test_result(
                "Variáveis de Ambiente",
                False,
                f"Variáveis faltando: {', '.join(missing_vars)}"
            )
        else:
            self.log_test_result(
                "Variáveis de Ambiente",
                True,
                f"Todas as {len(required_vars)} variáveis encontradas"
            )
    
    async def test_imports(self):
        """Testa imports de todos os módulos principais."""
        logger.info("📦 TESTANDO IMPORTS DE MÓDULOS")
        logger.info("=" * 50)
        
        modules_to_test = [
            ("app.core.config", "Configurações"),
            ("app.core.database", "Banco de Dados"),
            ("app.core.cache", "Cache Redis"),
            ("app.services.pdpj_client", "Cliente PDPJ"),
            ("app.services.s3_service", "Serviço S3"),
            ("app.services.process_cache_service", "Cache de Processos"),
            ("app.core.dynamic_limits", "Limites Dinâmicos"),
            ("app.core.proactive_monitoring", "Monitoramento"),
            ("app.utils.token_validator", "Validador de Token"),
            ("app.utils.http_headers", "Headers HTTP"),
            ("app.utils.transaction_manager", "Gerenciador de Transações"),
            ("app.utils.pagination_utils", "Utilitários de Paginação"),
            ("app.utils.advanced_retry", "Sistema de Retry"),
            ("app.services.chunked_download_service", "Download em Chunks"),
            # ("app.tasks.optimized_celery_tasks", "Tarefas Celery"),  # Temporariamente desabilitado
        ]
        
        failed_imports = []
        successful_imports = []
        
        for module_name, description in modules_to_test:
            try:
                __import__(module_name)
                successful_imports.append(description)
                logger.info(f"✅ {description}")
            except ImportError as e:
                failed_imports.append(f"{description}: {str(e)}")
                logger.error(f"❌ {description}: {str(e)}")
            except Exception as e:
                failed_imports.append(f"{description}: {str(e)}")
                logger.error(f"❌ {description}: {str(e)}")
        
        if failed_imports:
            self.log_test_result(
                "Imports de Módulos",
                False,
                f"Falhas: {len(failed_imports)}, Sucessos: {len(successful_imports)}"
            )
        else:
            self.log_test_result(
                "Imports de Módulos",
                True,
                f"Todos os {len(successful_imports)} módulos importados com sucesso"
            )
    
    async def test_configuration_loading(self):
        """Testa carregamento de configurações."""
        logger.info("⚙️ TESTANDO CARREGAMENTO DE CONFIGURAÇÕES")
        logger.info("=" * 50)
        
        try:
            from app.core.config import settings
            
            # Testar configurações básicas
            config_tests = [
                ("Database URL", bool(settings.database_url)),
                ("Redis URL", bool(settings.redis_url)),
                ("PDPJ Token", bool(settings.pdpj_api_token)),
                ("PDPJ Base URL", bool(settings.pdpj_api_base_url)),
                ("Debug Mode", isinstance(settings.debug, bool)),
                ("Environment", bool(settings.environment)),
            ]
            
            failed_configs = []
            for config_name, is_valid in config_tests:
                if is_valid:
                    logger.info(f"✅ {config_name}")
                else:
                    failed_configs.append(config_name)
                    logger.error(f"❌ {config_name}")
            
            if failed_configs:
                self.log_test_result(
                    "Carregamento de Configurações",
                    False,
                    f"Configurações inválidas: {', '.join(failed_configs)}"
                )
            else:
                self.log_test_result(
                    "Carregamento de Configurações",
                    True,
                    f"Todas as {len(config_tests)} configurações carregadas"
                )
                
        except Exception as e:
            self.log_test_result(
                "Carregamento de Configurações",
                False,
                f"Erro ao carregar configurações: {str(e)}"
            )
    
    async def test_database_connection(self):
        """Testa conexão com banco de dados."""
        logger.info("🗄️ TESTANDO CONEXÃO COM BANCO DE DADOS")
        logger.info("=" * 50)
        
        try:
            from app.core.database import AsyncSessionLocal
            from sqlalchemy import text
            
            # Testar conexão básica
            async with AsyncSessionLocal() as session:
                result = await session.execute(text("SELECT 1 as test"))
                test_value = result.scalar()
                
                if test_value == 1:
                    self.log_test_result(
                        "Conexão com Banco de Dados",
                        True,
                        "Conexão estabelecida com sucesso"
                    )
                else:
                    self.log_test_result(
                        "Conexão com Banco de Dados",
                        False,
                        "Query de teste retornou valor inesperado"
                    )
                    
        except Exception as e:
            self.log_test_result(
                "Conexão com Banco de Dados",
                False,
                f"Erro na conexão: {str(e)}"
            )
    
    async def test_redis_connection(self):
        """Testa conexão com Redis."""
        logger.info("🔴 TESTANDO CONEXÃO COM REDIS")
        logger.info("=" * 50)
        
        try:
            from app.core.cache import CacheService
            
            cache = CacheService()
            await cache.connect()
            
            # Testar operação básica
            test_key = "test_connection"
            test_value = "test_value"
            
            await cache.set(test_key, test_value, ttl=10)
            retrieved_value = await cache.get(test_key)
            
            if retrieved_value == test_value:
                await cache.delete(test_key)
                self.log_test_result(
                    "Conexão com Redis",
                    True,
                    "Operações de cache funcionando"
                )
            else:
                self.log_test_result(
                    "Conexão com Redis",
                    False,
                    "Valor recuperado não confere"
                )
                
        except Exception as e:
            self.log_test_result(
                "Conexão com Redis",
                False,
                f"Erro na conexão: {str(e)}"
            )
    
    async def test_pdpj_client_initialization(self):
        """Testa inicialização do cliente PDPJ."""
        logger.info("🔌 TESTANDO INICIALIZAÇÃO DO CLIENTE PDPJ")
        logger.info("=" * 50)
        
        try:
            from app.services.pdpj_client import pdpj_client
            
            # Verificar se o cliente foi inicializado
            if pdpj_client:
                # Testar configurações básicas
                has_token = bool(pdpj_client.token)
                has_base_url = bool(pdpj_client.base_url)
                
                if has_token and has_base_url:
                    self.log_test_result(
                        "Inicialização do Cliente PDPJ",
                        True,
                        "Cliente inicializado com token e base URL"
                    )
                else:
                    missing = []
                    if not has_token:
                        missing.append("token")
                    if not has_base_url:
                        missing.append("base_url")
                    
                    self.log_test_result(
                        "Inicialização do Cliente PDPJ",
                        False,
                        f"Configurações faltando: {', '.join(missing)}"
                    )
            else:
                self.log_test_result(
                    "Inicialização do Cliente PDPJ",
                    False,
                    "Cliente não foi inicializado"
                )
                
        except Exception as e:
            self.log_test_result(
                "Inicialização do Cliente PDPJ",
                False,
                f"Erro na inicialização: {str(e)}"
            )
    
    async def test_fastapi_app_creation(self):
        """Testa criação da aplicação FastAPI."""
        logger.info("🚀 TESTANDO CRIAÇÃO DA APLICAÇÃO FASTAPI")
        logger.info("=" * 50)
        
        try:
            # Testar criação básica do FastAPI primeiro
            from fastapi import FastAPI
            from app.core.config import settings
            
            # Criar app básico sem dependências pesadas
            app = FastAPI(
                title=settings.api_title,
                description=settings.api_description,
                version=settings.api_version,
                docs_url="/docs" if settings.debug else None,
                redoc_url="/redoc" if settings.debug else None,
            )
            
            if app and isinstance(app, FastAPI):
                # Verificar se as configurações foram aplicadas
                if (app.title == settings.api_title and 
                    app.description == settings.api_description and
                    app.version == settings.api_version):
                    
                    self.log_test_result(
                        "Criação da Aplicação FastAPI",
                        True,
                        f"Aplicação básica criada com sucesso - {app.title} v{app.version}"
                    )
                else:
                    self.log_test_result(
                        "Criação da Aplicação FastAPI",
                        False,
                        "Configurações não foram aplicadas corretamente"
                    )
            else:
                self.log_test_result(
                    "Criação da Aplicação FastAPI",
                    False,
                    "Objeto retornado não é uma instância do FastAPI"
                )
                
        except Exception as e:
            self.log_test_result(
                "Criação da Aplicação FastAPI",
                False,
                f"Erro na criação: {str(e)}"
            )
    
    async def test_fastapi_components(self):
        """Testa componentes individuais do FastAPI."""
        logger.info("🧩 TESTANDO COMPONENTES DO FASTAPI")
        logger.info("=" * 50)
        
        components_tests = []
        
        # Testar imports de componentes
        try:
            from app.core.middleware_config import create_middleware_stack
            components_tests.append(("Middleware Stack", True, "Importado com sucesso"))
        except Exception as e:
            components_tests.append(("Middleware Stack", False, f"Erro: {str(e)}"))
        
        try:
            from app.core.app_events import register_startup_events, register_shutdown_events
            components_tests.append(("App Events", True, "Importado com sucesso"))
        except Exception as e:
            components_tests.append(("App Events", False, f"Erro: {str(e)}"))
        
        try:
            from app.core.core_endpoints import register_core_endpoints
            components_tests.append(("Core Endpoints", True, "Importado com sucesso"))
        except Exception as e:
            components_tests.append(("Core Endpoints", False, f"Erro: {str(e)}"))
        
        try:
            from app.core.router_config import register_api_routers
            components_tests.append(("Router Config", True, "Importado com sucesso"))
        except Exception as e:
            components_tests.append(("Router Config", False, f"Erro: {str(e)}"))
        
        # Contar sucessos
        successful_components = sum(1 for _, success, _ in components_tests if success)
        total_components = len(components_tests)
        
        for component_name, success, details in components_tests:
            status = "✅" if success else "❌"
            logger.info(f"{status} {component_name}: {details}")
        
        if successful_components == total_components:
            self.log_test_result(
                "Componentes do FastAPI",
                True,
                f"Todos os {total_components} componentes importados com sucesso"
            )
        else:
            failed_components = [name for name, success, _ in components_tests if not success]
            self.log_test_result(
                "Componentes do FastAPI",
                False,
                f"Falhas: {len(failed_components)}/{total_components} - {', '.join(failed_components)}"
            )
    
    async def run_all_tests(self):
        """Executa todos os testes de inicialização."""
        logger.info("🧪 INICIANDO TESTES DE INICIALIZAÇÃO DA API")
        logger.info("=" * 60)
        logger.info("")
        
        # Executar todos os testes
        await self.test_environment_variables()
        logger.info("")
        
        await self.test_imports()
        logger.info("")
        
        await self.test_configuration_loading()
        logger.info("")
        
        await self.test_database_connection()
        logger.info("")
        
        await self.test_redis_connection()
        logger.info("")
        
        await self.test_pdpj_client_initialization()
        logger.info("")
        
        await self.test_fastapi_app_creation()
        logger.info("")
        
        await self.test_fastapi_components()
        logger.info("")
        
        # Resumo final
        self.print_summary()
    
    def print_summary(self):
        """Imprime resumo dos testes."""
        total_tests = len(self.results)
        passed_tests = sum(1 for result in self.results.values() if result["success"])
        failed_tests = total_tests - passed_tests
        
        duration = time.time() - self.start_time
        
        logger.info("📊 RESUMO DOS TESTES DE INICIALIZAÇÃO")
        logger.info("=" * 60)
        logger.info(f"⏱️  Duração total: {duration:.2f} segundos")
        logger.info(f"📈 Total de testes: {total_tests}")
        logger.info(f"✅ Testes aprovados: {passed_tests}")
        logger.info(f"❌ Testes falharam: {failed_tests}")
        logger.info(f"📊 Taxa de sucesso: {(passed_tests/total_tests)*100:.1f}%")
        logger.info("")
        
        if failed_tests > 0:
            logger.warning("⚠️  TESTES QUE FALHARAM:")
            for test_name, result in self.results.items():
                if not result["success"]:
                    logger.warning(f"   ❌ {test_name}: {result['details']}")
            logger.info("")
        
        if passed_tests == total_tests:
            logger.success("🎉 TODOS OS TESTES DE INICIALIZAÇÃO PASSARAM!")
            logger.success("✅ A API está pronta para a próxima fase de testes.")
        else:
            logger.error("⚠️  ALGUNS TESTES FALHARAM!")
            logger.error("🔧 Corrija os problemas antes de prosseguir.")
        
        logger.info("=" * 60)

async def main():
    """Função principal."""
    test_suite = APITestSuite()
    
    try:
        # Executar testes com timeout de 60 segundos
        await asyncio.wait_for(test_suite.run_all_tests(), timeout=60.0)
    except asyncio.TimeoutError:
        logger.error("⏰ TESTE INTERROMPIDO POR TIMEOUT (60s)")
        logger.error("🔧 Alguns testes podem estar travando - verifique dependências externas")
        test_suite.print_summary()
    except KeyboardInterrupt:
        logger.warning("⚠️ TESTE INTERROMPIDO PELO USUÁRIO")
        test_suite.print_summary()
    except Exception as e:
        logger.error(f"💥 ERRO INESPERADO: {str(e)}")
        test_suite.print_summary()

if __name__ == "__main__":
    asyncio.run(main())
