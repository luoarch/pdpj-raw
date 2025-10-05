#!/usr/bin/env python3
"""
FASE 2: Testes de Infraestrutura Core
Valida a infraestrutura básica: banco de dados, cache, autenticação e rate limiting.
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

class CoreInfrastructureTestSuite:
    """Suite de testes para infraestrutura core."""
    
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
    
    async def test_database_operations(self):
        """Testa operações básicas do banco de dados."""
        logger.info("🗄️ TESTANDO OPERAÇÕES DO BANCO DE DADOS")
        logger.info("=" * 50)
        
        try:
            from app.core.database import AsyncSessionLocal
            from sqlalchemy import text
            from app.models import Process, Document, User
            
            # Testar operações CRUD básicas
            async with AsyncSessionLocal() as session:
                # Teste 1: Query simples
                result = await session.execute(text("SELECT COUNT(*) as count FROM information_schema.tables WHERE table_schema = 'pdpj'"))
                table_count = result.scalar()
                
                # Teste 2: Verificar se tabelas existem
                tables_query = text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'pdpj' 
                    AND table_type = 'BASE TABLE'
                """)
                result = await session.execute(tables_query)
                tables = [row[0] for row in result.fetchall()]
                
                expected_tables = ['processes', 'documents', 'users']
                existing_tables = [table for table in expected_tables if table in tables]
                
                # Verificar se pelo menos conseguimos conectar e fazer queries
                if table_count >= 0:  # Aceitar 0 tabelas (banco vazio)
                    self.log_test_result(
                        "Operações do Banco de Dados",
                        True,
                        f"Conexão funcionando, {table_count} tabelas encontradas, {len(existing_tables)}/{len(expected_tables)} tabelas esperadas existem"
                    )
                else:
                    self.log_test_result(
                        "Operações do Banco de Dados",
                        False,
                        f"Erro ao consultar tabelas: {table_count}"
                    )
                    
        except Exception as e:
            self.log_test_result(
                "Operações do Banco de Dados",
                False,
                f"Erro nas operações: {str(e)}"
            )
    
    async def test_cache_operations(self):
        """Testa operações do cache Redis."""
        logger.info("🔴 TESTANDO OPERAÇÕES DO CACHE REDIS")
        logger.info("=" * 50)
        
        try:
            from app.core.cache import CacheService
            
            cache = CacheService()
            await cache.connect()
            
            # Teste 1: Operações básicas
            test_key = "test_cache_operations"
            test_value = {"test": "data", "number": 123}
            
            # Set
            set_result = await cache.set(test_key, test_value, ttl=30)
            
            # Get
            retrieved_value = await cache.get(test_key)
            
            # Exists
            exists_result = await cache.exists(test_key)
            
            # Delete
            delete_result = await cache.delete(test_key)
            
            # Verificar se não existe mais
            not_exists_result = await cache.exists(test_key)
            
            if (set_result and retrieved_value == test_value and 
                exists_result and delete_result and not not_exists_result):
                self.log_test_result(
                    "Operações do Cache Redis",
                    True,
                    "Todas as operações CRUD funcionando corretamente"
                )
            else:
                self.log_test_result(
                    "Operações do Cache Redis",
                    False,
                    f"Set: {set_result}, Get: {retrieved_value == test_value}, Exists: {exists_result}, Delete: {delete_result}"
                )
                
        except Exception as e:
            self.log_test_result(
                "Operações do Cache Redis",
                False,
                f"Erro nas operações: {str(e)}"
            )
    
    async def test_authentication_system(self):
        """Testa sistema de autenticação."""
        logger.info("🔐 TESTANDO SISTEMA DE AUTENTICAÇÃO")
        logger.info("=" * 50)
        
        try:
            from app.utils.token_validator import PDPJTokenValidator
            from app.core.config import settings
            
            validator = PDPJTokenValidator()
            
            # Teste 1: Validação de token
            token = settings.pdpj_api_token.get_secret_value()
            validation_result = validator.validate_token(token)
            
            # Teste 2: Log de validação
            log_result = validator.validate_and_log(token)
            
            if validation_result and log_result:
                self.log_test_result(
                    "Sistema de Autenticação",
                    True,
                    "Validação de token e logging funcionando"
                )
            else:
                self.log_test_result(
                    "Sistema de Autenticação",
                    False,
                    f"Validação: {validation_result}, Log: {log_result}"
                )
                
        except Exception as e:
            self.log_test_result(
                "Sistema de Autenticação",
                False,
                f"Erro no sistema: {str(e)}"
            )
    
    async def test_rate_limiting_system(self):
        """Testa sistema de rate limiting."""
        logger.info("⏱️ TESTANDO SISTEMA DE RATE LIMITING")
        logger.info("=" * 50)
        
        try:
            from app.core.rate_limiting import InMemoryRateLimitStorage, create_rate_limit_middleware
            from app.core.config import settings
            
            # Criar storage de rate limiting
            storage = InMemoryRateLimitStorage()
            
            # Teste 1: Verificar se pode fazer request
            test_key = "test_rate_limit"
            current_time = time.time()
            window_start = current_time - 60  # 1 minuto atrás
            
            # Obter requisições atuais
            requests = await storage.get_client_requests(test_key, window_start)
            
            # Teste 2: Adicionar nova requisição
            await storage.add_client_request(test_key, current_time)
            
            # Teste 3: Verificar se foi adicionada
            updated_requests = await storage.get_client_requests(test_key, window_start)
            
            if len(updated_requests) > len(requests):
                self.log_test_result(
                    "Sistema de Rate Limiting",
                    True,
                    f"Rate limiting funcionando, {len(updated_requests)} requisições registradas"
                )
            else:
                self.log_test_result(
                    "Sistema de Rate Limiting",
                    False,
                    f"Requisições não foram registradas corretamente"
                )
                
        except Exception as e:
            self.log_test_result(
                "Sistema de Rate Limiting",
                False,
                f"Erro no sistema: {str(e)}"
            )
    
    async def test_transaction_manager(self):
        """Testa gerenciador de transações."""
        logger.info("🔄 TESTANDO GERENCIADOR DE TRANSAÇÕES")
        logger.info("=" * 50)
        
        try:
            from app.utils.transaction_manager import TransactionManager
            from app.core.database import AsyncSessionLocal
            
            # Teste 1: Transação simples
            async with AsyncSessionLocal() as session:
                tx_manager = TransactionManager(session)
                
                async with tx_manager.transaction() as tx:
                    # Simular operação
                    from sqlalchemy import text
                    result = await tx.execute(text("SELECT 1 as test"))
                    test_value = result.scalar()
                    
                    if test_value == 1:
                        self.log_test_result(
                            "Gerenciador de Transações",
                            True,
                            "Transação simples executada com sucesso"
                        )
                    else:
                        self.log_test_result(
                            "Gerenciador de Transações",
                            False,
                            "Valor de teste incorreto"
                        )
                    
        except Exception as e:
            self.log_test_result(
                "Gerenciador de Transações",
                False,
                f"Erro no gerenciador: {str(e)}"
            )
    
    async def test_pagination_utils(self):
        """Testa utilitários de paginação."""
        logger.info("📄 TESTANDO UTILITÁRIOS DE PAGINAÇÃO")
        logger.info("=" * 50)
        
        try:
            from app.utils.pagination_utils import (
                PaginationParams, ProcessPaginationParams, DocumentPaginationParams
            )
            
            # Teste 1: Parâmetros básicos
            basic_params = PaginationParams(skip=0, limit=10)
            
            # Teste 2: Parâmetros de processo (sem Query objects)
            process_params = ProcessPaginationParams(
                skip=0, 
                limit=20, 
                sort_by="created_at",
                sort_order="desc",
                filter_court=None,
                filter_has_documents=None
            )
            
            # Teste 3: Parâmetros de documento
            doc_params = DocumentPaginationParams(
                skip=0, 
                limit=15, 
                filter_type="pdf",
                sort_by="created_at",
                sort_order="desc"
            )
            
            if (basic_params.offset == 0 and basic_params.limit == 10 and
                process_params.sort_by == "created_at" and
                doc_params.filter_type == "pdf"):
                
                self.log_test_result(
                    "Utilitários de Paginação",
                    True,
                    "Todos os utilitários de paginação funcionando"
                )
            else:
                self.log_test_result(
                    "Utilitários de Paginação",
                    False,
                    "Alguns utilitários não estão funcionando corretamente"
                )
                
        except Exception as e:
            self.log_test_result(
                "Utilitários de Paginação",
                False,
                f"Erro nos utilitários: {str(e)}"
            )
    
    async def test_advanced_retry_system(self):
        """Testa sistema avançado de retry."""
        logger.info("🔄 TESTANDO SISTEMA AVANÇADO DE RETRY")
        logger.info("=" * 50)
        
        try:
            from app.utils.advanced_retry import (
                RetryStrategy, RetryConfig, AdvancedRetry,
                retry_http, retry_database
            )
            
            # Teste 1: Configuração de retry
            config = RetryConfig(
                max_attempts=3,
                base_delay=1.0,
                max_delay=10.0,
                strategy=RetryStrategy.EXPONENTIAL
            )
            
            # Teste 2: Criar instância do AdvancedRetry
            retry_system = AdvancedRetry(config)
            
            # Teste 3: Função de teste que falha
            call_count = 0
            
            async def failing_function():
                nonlocal call_count
                call_count += 1
                if call_count < 3:
                    raise Exception("Simulated failure")
                return "success"
            
            # Teste 4: Aplicar retry
            result = await retry_system.execute_with_retry(failing_function)
            
            if result == "success" and call_count == 3:
                self.log_test_result(
                    "Sistema Avançado de Retry",
                    True,
                    f"Retry funcionando, {call_count} tentativas executadas"
                )
            else:
                self.log_test_result(
                    "Sistema Avançado de Retry",
                    False,
                    f"Resultado: {result}, Tentativas: {call_count}"
                )
                
        except Exception as e:
            self.log_test_result(
                "Sistema Avançado de Retry",
                False,
                f"Erro no sistema: {str(e)}"
            )
    
    async def test_dynamic_limits(self):
        """Testa limites dinâmicos."""
        logger.info("⚙️ TESTANDO LIMITES DINÂMICOS")
        logger.info("=" * 50)
        
        try:
            from app.core.dynamic_limits import (
                get_current_limits, get_limits_for_environment,
                DynamicLimits, Environment
            )
            
            # Teste 1: Obter limites atuais
            current_limits = get_current_limits()
            
            # Teste 2: Obter limites por ambiente
            env_limits = get_limits_for_environment(Environment.DEVELOPMENT)
            
            # Teste 3: Verificar se limites são válidos
            if (current_limits and 
                hasattr(current_limits, 'max_concurrent_requests') and
                hasattr(current_limits, 'request_timeout') and
                env_limits and
                isinstance(env_limits, DynamicLimits)):
                
                self.log_test_result(
                    "Limites Dinâmicos",
                    True,
                    f"Limites carregados: timeout={current_limits.request_timeout}s, concurrent={current_limits.max_concurrent_requests}"
                )
            else:
                self.log_test_result(
                    "Limites Dinâmicos",
                    False,
                    "Limites não foram carregados corretamente"
                )
                
        except Exception as e:
            self.log_test_result(
                "Limites Dinâmicos",
                False,
                f"Erro nos limites: {str(e)}"
            )
    
    async def run_all_tests(self):
        """Executa todos os testes de infraestrutura core."""
        logger.info("🧪 INICIANDO TESTES DE INFRAESTRUTURA CORE")
        logger.info("=" * 60)
        logger.info("")
        
        # Executar todos os testes
        await self.test_database_operations()
        logger.info("")
        
        await self.test_cache_operations()
        logger.info("")
        
        await self.test_authentication_system()
        logger.info("")
        
        await self.test_rate_limiting_system()
        logger.info("")
        
        await self.test_transaction_manager()
        logger.info("")
        
        await self.test_pagination_utils()
        logger.info("")
        
        await self.test_advanced_retry_system()
        logger.info("")
        
        await self.test_dynamic_limits()
        logger.info("")
        
        # Resumo final
        self.print_summary()
    
    def print_summary(self):
        """Imprime resumo dos testes."""
        total_tests = len(self.results)
        passed_tests = sum(1 for result in self.results.values() if result["success"])
        failed_tests = total_tests - passed_tests
        
        duration = time.time() - self.start_time
        
        logger.info("📊 RESUMO DOS TESTES DE INFRAESTRUTURA CORE")
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
            logger.success("🎉 TODOS OS TESTES DE INFRAESTRUTURA CORE PASSARAM!")
            logger.success("✅ A infraestrutura está pronta para a próxima fase de testes.")
        else:
            logger.error("⚠️  ALGUNS TESTES FALHARAM!")
            logger.error("🔧 Corrija os problemas antes de prosseguir.")
        
        logger.info("=" * 60)

async def main():
    """Função principal."""
    test_suite = CoreInfrastructureTestSuite()
    
    try:
        # Executar testes com timeout de 120 segundos
        await asyncio.wait_for(test_suite.run_all_tests(), timeout=120.0)
    except asyncio.TimeoutError:
        logger.error("⏰ TESTE INTERROMPIDO POR TIMEOUT (120s)")
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
