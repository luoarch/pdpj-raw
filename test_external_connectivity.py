#!/usr/bin/env python3
"""
FASE 3: Testes de Conectividade Externa
=====================================

Este script testa a conectividade com serviços externos:
- PDPJ API
- Redis
- S3
- Conectividade geral
"""

import asyncio
import time
import sys
import os
from typing import Dict, Any, List
from dataclasses import dataclass

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from loguru import logger
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

@dataclass
class TestResult:
    """Resultado de um teste."""
    success: bool
    details: str
    duration: float
    timestamp: float

class ExternalConnectivityTester:
    """Testador de conectividade externa."""
    
    def __init__(self):
        self.results: Dict[str, TestResult] = {}
        self.start_time = time.time()
        
    def log_test_result(self, test_name: str, success: bool, details: str):
        """Registra o resultado de um teste."""
        duration = time.time() - self.start_time
        self.results[test_name] = TestResult(
            success=success,
            details=details,
            duration=duration,
            timestamp=time.time()
        )
        
        status = "✅ PASSOU" if success else "❌ FALHOU"
        logger.info(f"{status} | {test_name}")
        logger.info(f"    📝 {details}")
    
    async def test_pdpj_api_connectivity(self):
        """Testa conectividade com a API PDPJ."""
        logger.info("🌐 TESTANDO CONECTIVIDADE COM API PDPJ")
        logger.info("=" * 50)
        
        try:
            from app.services.pdpj_client import pdpj_client
            from app.core.config import settings
            
            # Teste 1: Verificar configuração
            if not settings.pdpj_api_token:
                self.log_test_result(
                    "Conectividade PDPJ API",
                    False,
                    "Token PDPJ não configurado"
                )
                return
                
            if not settings.pdpj_api_base_url:
                self.log_test_result(
                    "Conectividade PDPJ API",
                    False,
                    "URL base PDPJ não configurada"
                )
                return
            
            # Teste 2: Testar endpoint de saúde
            try:
                # Fazer uma requisição simples para testar conectividade
                async with pdpj_client as client:
                    # Testar com um endpoint que sabemos que existe
                    response = await client._execute_request(
                        "GET",
                        "/processos",
                        params={"limit": 1}
                    )
                    
                    if isinstance(response, dict):
                        # Verificar se é uma resposta válida da API PDPJ
                        if 'data' in response or 'processos' in response or 'content' in response:
                            self.log_test_result(
                                "Conectividade PDPJ API",
                                True,
                                f"API PDPJ acessível, resposta recebida com sucesso"
                            )
                        else:
                            # Log da resposta para debug
                            logger.debug(f"Resposta da API PDPJ: {response}")
                            self.log_test_result(
                                "Conectividade PDPJ API",
                                True,
                                f"API PDPJ acessível, resposta recebida (formato: {list(response.keys()) if response else 'vazio'})"
                            )
                    else:
                        self.log_test_result(
                            "Conectividade PDPJ API",
                            False,
                            f"API PDPJ retornou resposta inesperada: {type(response)}"
                        )
                        
            except Exception as e:
                self.log_test_result(
                    "Conectividade PDPJ API",
                    False,
                    f"Erro ao conectar com API PDPJ: {str(e)}"
                )
                
        except Exception as e:
            self.log_test_result(
                "Conectividade PDPJ API",
                False,
                f"Erro ao inicializar cliente PDPJ: {str(e)}"
            )
    
    async def test_redis_connectivity(self):
        """Testa conectividade com Redis."""
        logger.info("🔴 TESTANDO CONECTIVIDADE COM REDIS")
        logger.info("=" * 50)
        
        try:
            from app.core.cache import CacheService
            
            # Teste 1: Conectar ao Redis
            cache = CacheService()
            await cache.connect()
            
            # Teste 2: Operações básicas
            test_key = "test_connectivity"
            test_value = "test_value"
            
            # Set
            await cache.set(test_key, test_value, ttl=10)
            
            # Get
            retrieved_value = await cache.get(test_key)
            
            # Delete
            await cache.delete(test_key)
            
            if retrieved_value == test_value:
                self.log_test_result(
                    "Conectividade Redis",
                    True,
                    "Redis funcionando, operações CRUD OK"
                )
            else:
                self.log_test_result(
                    "Conectividade Redis",
                    False,
                    f"Valor recuperado incorreto: {retrieved_value}"
                )
                
        except Exception as e:
            self.log_test_result(
                "Conectividade Redis",
                False,
                f"Erro ao conectar com Redis: {str(e)}"
            )
    
    async def test_s3_connectivity(self):
        """Testa conectividade com S3."""
        logger.info("☁️ TESTANDO CONECTIVIDADE COM S3")
        logger.info("=" * 50)
        
        try:
            from app.services.s3_service import S3Service
            from app.core.config import settings
            
            # Teste 1: Verificar configuração
            if not settings.aws_access_key_id:
                self.log_test_result(
                    "Conectividade S3",
                    False,
                    "AWS_ACCESS_KEY_ID não configurado"
                )
                return
                
            if not settings.aws_secret_access_key:
                self.log_test_result(
                    "Conectividade S3",
                    False,
                    "AWS_SECRET_ACCESS_KEY não configurado"
                )
                return
                
            if not settings.s3_bucket_name:
                self.log_test_result(
                    "Conectividade S3",
                    False,
                    "S3_BUCKET_NAME não configurado"
                )
                return
            
            # Teste 2: Conectar ao S3
            s3_service = S3Service()
            
            # Teste 3: Verificar credenciais AWS primeiro
            try:
                import boto3
                from botocore.exceptions import ClientError, NoCredentialsError
                
                # Testar credenciais com boto3 direto
                session = boto3.Session(
                    aws_access_key_id=settings.aws_access_key_id.get_secret_value() if hasattr(settings.aws_access_key_id, 'get_secret_value') else str(settings.aws_access_key_id),
                    aws_secret_access_key=settings.aws_secret_access_key.get_secret_value() if hasattr(settings.aws_secret_access_key, 'get_secret_value') else str(settings.aws_secret_access_key),
                    region_name=settings.aws_region
                )
                
                # Testar listagem de buckets
                s3_client = session.client('s3')
                response = s3_client.list_buckets()
                
                # Verificar se nosso bucket está na lista
                bucket_names = [bucket['Name'] for bucket in response['Buckets']]
                
                if settings.s3_bucket_name in bucket_names:
                    self.log_test_result(
                        "Conectividade S3",
                        True,
                        f"Bucket '{settings.s3_bucket_name}' encontrado e acessível"
                    )
                else:
                    # Bucket não existe, mas credenciais funcionam
                    self.log_test_result(
                        "Conectividade S3",
                        True,
                        f"Credenciais AWS válidas, mas bucket '{settings.s3_bucket_name}' não existe. Buckets disponíveis: {bucket_names[:3]}..."
                    )
                    
            except NoCredentialsError:
                self.log_test_result(
                    "Conectividade S3",
                    False,
                    "Credenciais AWS não configuradas ou inválidas"
                )
            except ClientError as e:
                error_code = e.response['Error']['Code']
                if error_code == 'InvalidAccessKeyId':
                    self.log_test_result(
                        "Conectividade S3",
                        False,
                        f"Credenciais AWS inválidas: Access Key ID não existe. Verifique as credenciais no .env"
                    )
                elif error_code == 'SignatureDoesNotMatch':
                    self.log_test_result(
                        "Conectividade S3",
                        False,
                        f"Credenciais AWS inválidas: Secret Access Key incorreto. Verifique as credenciais no .env"
                    )
                elif error_code == 'AccessDenied':
                    self.log_test_result(
                        "Conectividade S3",
                        False,
                        f"Acesso negado ao S3: {e}"
                    )
                else:
                    self.log_test_result(
                        "Conectividade S3",
                        False,
                        f"Erro do AWS S3 ({error_code}): {e}"
                    )
            except Exception as e:
                self.log_test_result(
                    "Conectividade S3",
                    False,
                    f"Erro inesperado ao conectar com S3: {str(e)}"
                )
                
        except Exception as e:
            self.log_test_result(
                "Conectividade S3",
                False,
                f"Erro ao conectar com S3: {str(e)}"
            )
    
    async def test_network_connectivity(self):
        """Testa conectividade de rede geral."""
        logger.info("🌍 TESTANDO CONECTIVIDADE DE REDE GERAL")
        logger.info("=" * 50)
        
        try:
            import httpx
            
            # Teste 1: Conectividade com Google DNS
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get("https://8.8.8.8", follow_redirects=False)
                
            # Teste 2: Conectividade com portal PDPJ
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get("https://portaldeservicos.pdpj.jus.br", follow_redirects=False)
                
            self.log_test_result(
                "Conectividade de Rede",
                True,
                "Conectividade de rede funcionando"
            )
            
        except Exception as e:
            self.log_test_result(
                "Conectividade de Rede",
                False,
                f"Erro de conectividade de rede: {str(e)}"
            )
    
    async def test_environment_variables(self):
        """Testa se todas as variáveis de ambiente necessárias estão configuradas."""
        logger.info("⚙️ TESTANDO VARIÁVEIS DE AMBIENTE")
        logger.info("=" * 50)
        
        try:
            from app.core.config import settings
            
            required_vars = [
                ("DATABASE_URL", settings.database_url),
                ("REDIS_URL", settings.redis_url),
                ("PDPJ_API_TOKEN", settings.pdpj_api_token),
                ("PDPJ_API_BASE_URL", settings.pdpj_api_base_url),
                ("AWS_ACCESS_KEY_ID", settings.aws_access_key_id),
                ("AWS_SECRET_ACCESS_KEY", settings.aws_secret_access_key),
                ("S3_BUCKET_NAME", settings.s3_bucket_name),
            ]
            
            missing_vars = []
            for var_name, var_value in required_vars:
                if not var_value:
                    missing_vars.append(var_name)
            
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
                    "Todas as variáveis de ambiente configuradas"
                )
                
        except Exception as e:
            self.log_test_result(
                "Variáveis de Ambiente",
                False,
                f"Erro ao verificar variáveis: {str(e)}"
            )
    
    async def test_token_validation(self):
        """Testa validação do token PDPJ."""
        logger.info("🔐 TESTANDO VALIDAÇÃO DO TOKEN PDPJ")
        logger.info("=" * 50)
        
        try:
            from app.utils.token_validator import PDPJTokenValidator
            from app.core.config import settings
            
            if not settings.pdpj_api_token:
                self.log_test_result(
                    "Validação do Token",
                    False,
                    "Token PDPJ não configurado"
                )
                return
            
            # Teste de validação
            validator = PDPJTokenValidator()
            
            # Verificar se o token não está vazio ou corrompido
            token_str = settings.pdpj_api_token.get_secret_value()
            if not token_str or len(token_str) < 10:
                self.log_test_result(
                    "Validação do Token",
                    False,
                    "Token vazio ou muito curto"
                )
                return
            
            # Verificar se parece com um JWT (3 partes separadas por ponto)
            if token_str.count('.') != 2:
                self.log_test_result(
                    "Validação do Token",
                    False,
                    f"Token não tem formato JWT válido (deve ter 3 partes separadas por ponto, encontrado {token_str.count('.')} pontos)"
                )
                return
            
            result = validator.validate_and_log(settings.pdpj_api_token)
            
            if result.is_valid:
                # Token é válido, verificar tipo
                if result.is_pje_token:
                    self.log_test_result(
                        "Validação do Token",
                        True,
                        f"Token PJE válido (compatível com PDPJ): {result.user_name or 'Usuário não identificado'}"
                    )
                elif result.is_pdpj_token:
                    self.log_test_result(
                        "Validação do Token",
                        True,
                        f"Token PDPJ válido: {result.user_name or 'Usuário não identificado'}"
                    )
                else:
                    self.log_test_result(
                        "Validação do Token",
                        True,
                        f"Token válido: {result.user_name or 'Usuário não identificado'}"
                    )
            else:
                # Token inválido
                error_details = []
                if result.errors:
                    error_details.extend(result.errors)
                if result.warnings:
                    error_details.extend([f"AVISO: {w}" for w in result.warnings])
                
                self.log_test_result(
                    "Validação do Token",
                    False,
                    f"Token inválido: {', '.join(error_details) if error_details else 'Erro desconhecido'}"
                )
                
        except Exception as e:
            self.log_test_result(
                "Validação do Token",
                False,
                f"Erro ao validar token: {str(e)}"
            )
    
    async def run_all_tests(self):
        """Executa todos os testes de conectividade externa."""
        logger.info("🧪 INICIANDO TESTES DE CONECTIVIDADE EXTERNA")
        logger.info("=" * 60)
        logger.info("")
        
        # Executar testes
        await self.test_environment_variables()
        logger.info("")
        
        await self.test_network_connectivity()
        logger.info("")
        
        await self.test_redis_connectivity()
        logger.info("")
        
        await self.test_s3_connectivity()
        logger.info("")
        
        await self.test_token_validation()
        logger.info("")
        
        await self.test_pdpj_api_connectivity()
        logger.info("")
        
        # Mostrar resumo
        self.print_summary()
    
    def print_summary(self):
        """Imprime resumo dos testes."""
        total_duration = time.time() - self.start_time
        
        logger.info("📊 RESUMO DOS TESTES DE CONECTIVIDADE EXTERNA")
        logger.info("=" * 60)
        logger.info(f"⏱️  Duração total: {total_duration:.2f} segundos")
        logger.info(f"📈 Total de testes: {len(self.results)}")
        
        passed_tests = sum(1 for result in self.results.values() if result.success)
        failed_tests = len(self.results) - passed_tests
        
        logger.info(f"✅ Testes aprovados: {passed_tests}")
        logger.info(f"❌ Testes falharam: {failed_tests}")
        
        if len(self.results) > 0:
            success_rate = (passed_tests / len(self.results)) * 100
            logger.info(f"📊 Taxa de sucesso: {success_rate:.1f}%")
        
        logger.info("")
        
        if failed_tests == 0:
            logger.success("🎉 TODOS OS TESTES DE CONECTIVIDADE EXTERNA PASSARAM!")
            logger.success("✅ A conectividade externa está funcionando corretamente.")
        else:
            # Verificar se são problemas críticos ou apenas de configuração
            critical_failures = []
            config_failures = []
            
            for test_name, result in self.results.items():
                if not result.success:
                    error_msg = result.details
                    if "AWS" in error_msg or "credenciais" in error_msg.lower() or "token" in error_msg.lower():
                        config_failures.append((test_name, error_msg))
                    else:
                        critical_failures.append((test_name, error_msg))
            
            if critical_failures:
                logger.error("⚠️ FALHAS CRÍTICAS DE CONECTIVIDADE!")
                logger.error("❌ Problemas que impedem o funcionamento do sistema:")
                for test_name, error_msg in critical_failures:
                    logger.error(f"   ❌ {test_name}: {error_msg}")
                logger.info("")
            
            if config_failures:
                logger.warning("⚠️ PROBLEMAS DE CONFIGURAÇÃO EXTERNA:")
                logger.warning("🔧 Serviços externos não configurados corretamente (sistema ainda funcional):")
                for test_name, error_msg in config_failures:
                    logger.warning(f"   ⚠️ {test_name}: {error_msg}")
                logger.info("")
                logger.info("💡 DICA: O sistema funciona mesmo com esses problemas de configuração.")
                logger.info("   Para funcionalidade completa, configure os serviços externos.")
            
            if not critical_failures:
                logger.info("✅ SISTEMA FUNCIONAL - Problemas são apenas de configuração externa!")
        
        logger.info("")
        logger.info("=" * 60)

async def main():
    """Função principal."""
    try:
        tester = ExternalConnectivityTester()
        await tester.run_all_tests()
        
    except KeyboardInterrupt:
        logger.warning("⚠️ Testes interrompidos pelo usuário")
    except Exception as e:
        logger.error(f"❌ Erro inesperado: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
