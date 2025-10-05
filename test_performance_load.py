#!/usr/bin/env python3
"""
Script para testes de performance e carga do sistema PDPJ.

Este script testa:
1. Performance de endpoints individuais
2. Carga com múltiplas requisições simultâneas
3. Limites de rate limiting
4. Performance de downloads em lote
5. Uso de memória e CPU
6. Tempo de resposta sob carga
7. Estabilidade do sistema
"""

import asyncio
import time
import psutil
import statistics
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import aiohttp
import httpx
from loguru import logger

# Configurar logging
logger.remove()
logger.add(
    "logs/performance_test.log",
    rotation="10 MB",
    retention="7 days",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}"
)
logger.add(
    lambda msg: print(msg, end=""),
    level="INFO",
    format="<green>{time:HH:mm:ss}</green> | <level>{level}</level> | {message}"
)

@dataclass
class PerformanceResult:
    """Resultado de um teste de performance."""
    test_name: str
    success: bool
    duration: float
    requests_count: int
    success_rate: float
    avg_response_time: float
    min_response_time: float
    max_response_time: float
    p95_response_time: float
    p99_response_time: float
    memory_usage_mb: float
    cpu_usage_percent: float
    errors: List[str]
    details: Dict[str, Any]

class PerformanceTester:
    """Classe para executar testes de performance e carga."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.results: List[PerformanceResult] = []
        self.session = None
        
    async def __aenter__(self):
        """Context manager entry."""
        self.session = httpx.AsyncClient(
            timeout=httpx.Timeout(60.0),
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20)
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self.session:
            await self.session.aclose()
    
    def get_system_metrics(self) -> Tuple[float, float]:
        """Obter métricas do sistema (CPU e memória)."""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            memory_mb = memory.used / 1024 / 1024
            return cpu_percent, memory_mb
        except Exception as e:
            logger.warning(f"Erro ao obter métricas do sistema: {e}")
            return 0.0, 0.0
    
    def calculate_percentiles(self, values: List[float]) -> Dict[str, float]:
        """Calcular percentis de uma lista de valores."""
        if not values:
            return {"p50": 0, "p95": 0, "p99": 0}
        
        sorted_values = sorted(values)
        n = len(sorted_values)
        
        return {
            "p50": sorted_values[int(n * 0.5)],
            "p95": sorted_values[int(n * 0.95)],
            "p99": sorted_values[int(n * 0.99)]
        }
    
    async def test_single_endpoint_performance(self, endpoint: str, iterations: int = 10) -> PerformanceResult:
        """Testar performance de um endpoint individual."""
        logger.info(f"🔍 Testando performance do endpoint: {endpoint}")
        
        start_time = time.time()
        response_times = []
        errors = []
        success_count = 0
        
        for i in range(iterations):
            try:
                request_start = time.time()
                response = await self.session.get(f"{self.base_url}{endpoint}")
                request_duration = time.time() - request_start
                
                if response.status_code == 200:
                    success_count += 1
                    response_times.append(request_duration)
                else:
                    errors.append(f"HTTP {response.status_code}")
                    
            except Exception as e:
                errors.append(str(e))
        
        total_duration = time.time() - start_time
        cpu_usage, memory_usage = self.get_system_metrics()
        
        # Calcular estatísticas
        avg_response_time = statistics.mean(response_times) if response_times else 0
        min_response_time = min(response_times) if response_times else 0
        max_response_time = max(response_times) if response_times else 0
        percentiles = self.calculate_percentiles(response_times)
        
        result = PerformanceResult(
            test_name=f"Single Endpoint: {endpoint}",
            success=success_count > 0,
            duration=total_duration,
            requests_count=iterations,
            success_rate=(success_count / iterations) * 100,
            avg_response_time=avg_response_time,
            min_response_time=min_response_time,
            max_response_time=max_response_time,
            p95_response_time=percentiles["p95"],
            p99_response_time=percentiles["p99"],
            memory_usage_mb=memory_usage,
            cpu_usage_percent=cpu_usage,
            errors=errors,
            details={
                "endpoint": endpoint,
                "iterations": iterations,
                "success_count": success_count,
                "response_times": response_times[:5]  # Primeiros 5 para debug
            }
        )
        
        self.results.append(result)
        return result
    
    async def test_concurrent_requests(self, endpoint: str, concurrent_users: int, requests_per_user: int) -> PerformanceResult:
        """Testar requisições concorrentes."""
        logger.info(f"⚡ Testando {concurrent_users} usuários concorrentes, {requests_per_user} req/usuário")
        
        async def user_session():
            """Simular uma sessão de usuário."""
            user_response_times = []
            user_errors = []
            
            for _ in range(requests_per_user):
                try:
                    request_start = time.time()
                    response = await self.session.get(f"{self.base_url}{endpoint}")
                    request_duration = time.time() - request_start
                    
                    if response.status_code == 200:
                        user_response_times.append(request_duration)
                    else:
                        user_errors.append(f"HTTP {response.status_code}")
                        
                except Exception as e:
                    user_errors.append(str(e))
            
            return user_response_times, user_errors
        
        start_time = time.time()
        
        # Executar usuários concorrentes
        tasks = [user_session() for _ in range(concurrent_users)]
        user_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        total_duration = time.time() - start_time
        cpu_usage, memory_usage = self.get_system_metrics()
        
        # Consolidar resultados
        all_response_times = []
        all_errors = []
        success_count = 0
        
        for result in user_results:
            if isinstance(result, Exception):
                all_errors.append(str(result))
            else:
                response_times, errors = result
                all_response_times.extend(response_times)
                all_errors.extend(errors)
                success_count += len(response_times)
        
        total_requests = concurrent_users * requests_per_user
        
        # Calcular estatísticas
        avg_response_time = statistics.mean(all_response_times) if all_response_times else 0
        min_response_time = min(all_response_times) if all_response_times else 0
        max_response_time = max(all_response_times) if all_response_times else 0
        percentiles = self.calculate_percentiles(all_response_times)
        
        result = PerformanceResult(
            test_name=f"Concurrent Load: {concurrent_users} users",
            success=success_count > 0,
            duration=total_duration,
            requests_count=total_requests,
            success_rate=(success_count / total_requests) * 100,
            avg_response_time=avg_response_time,
            min_response_time=min_response_time,
            max_response_time=max_response_time,
            p95_response_time=percentiles["p95"],
            p99_response_time=percentiles["p99"],
            memory_usage_mb=memory_usage,
            cpu_usage_percent=cpu_usage,
            errors=all_errors[:10],  # Primeiros 10 erros
            details={
                "concurrent_users": concurrent_users,
                "requests_per_user": requests_per_user,
                "total_requests": total_requests,
                "success_count": success_count,
                "throughput_rps": total_requests / total_duration if total_duration > 0 else 0
            }
        )
        
        self.results.append(result)
        return result
    
    async def test_rate_limiting(self, endpoint: str, requests_per_second: int, duration_seconds: int) -> PerformanceResult:
        """Testar rate limiting."""
        logger.info(f"🚦 Testando rate limiting: {requests_per_second} req/s por {duration_seconds}s")
        
        start_time = time.time()
        response_times = []
        errors = []
        success_count = 0
        rate_limited_count = 0
        
        request_interval = 1.0 / requests_per_second
        
        while time.time() - start_time < duration_seconds:
            try:
                request_start = time.time()
                response = await self.session.get(f"{self.base_url}{endpoint}")
                request_duration = time.time() - request_start
                
                if response.status_code == 200:
                    success_count += 1
                    response_times.append(request_duration)
                elif response.status_code == 429:
                    rate_limited_count += 1
                    errors.append("Rate Limited (429)")
                else:
                    errors.append(f"HTTP {response.status_code}")
                    
            except Exception as e:
                errors.append(str(e))
            
            # Aguardar intervalo para manter taxa
            await asyncio.sleep(request_interval)
        
        total_duration = time.time() - start_time
        cpu_usage, memory_usage = self.get_system_metrics()
        
        total_requests = success_count + rate_limited_count + len(errors)
        
        # Calcular estatísticas
        avg_response_time = statistics.mean(response_times) if response_times else 0
        min_response_time = min(response_times) if response_times else 0
        max_response_time = max(response_times) if response_times else 0
        percentiles = self.calculate_percentiles(response_times)
        
        result = PerformanceResult(
            test_name=f"Rate Limiting: {requests_per_second} req/s",
            success=success_count > 0,
            duration=total_duration,
            requests_count=total_requests,
            success_rate=(success_count / total_requests) * 100 if total_requests > 0 else 0,
            avg_response_time=avg_response_time,
            min_response_time=min_response_time,
            max_response_time=max_response_time,
            p95_response_time=percentiles["p95"],
            p99_response_time=percentiles["p99"],
            memory_usage_mb=memory_usage,
            cpu_usage_percent=cpu_usage,
            errors=errors[:10],
            details={
                "target_rps": requests_per_second,
                "duration_seconds": duration_seconds,
                "success_count": success_count,
                "rate_limited_count": rate_limited_count,
                "actual_rps": total_requests / total_duration if total_duration > 0 else 0
            }
        )
        
        self.results.append(result)
        return result
    
    async def test_memory_stress(self, endpoint: str, duration_seconds: int = 30) -> PerformanceResult:
        """Testar uso de memória sob stress."""
        logger.info(f"🧠 Teste de stress de memória por {duration_seconds}s")
        
        start_time = time.time()
        response_times = []
        errors = []
        success_count = 0
        memory_samples = []
        
        while time.time() - start_time < duration_seconds:
            try:
                request_start = time.time()
                response = await self.session.get(f"{self.base_url}{endpoint}")
                request_duration = time.time() - request_start
                
                if response.status_code == 200:
                    success_count += 1
                    response_times.append(request_duration)
                else:
                    errors.append(f"HTTP {response.status_code}")
                    
            except Exception as e:
                errors.append(str(e))
            
            # Amostrar memória a cada 5 segundos
            if len(memory_samples) == 0 or time.time() - start_time > len(memory_samples) * 5:
                _, memory_usage = self.get_system_metrics()
                memory_samples.append(memory_usage)
            
            # Pequena pausa para não sobrecarregar
            await asyncio.sleep(0.1)
        
        total_duration = time.time() - start_time
        cpu_usage, final_memory = self.get_system_metrics()
        
        # Calcular estatísticas de memória
        max_memory = max(memory_samples) if memory_samples else final_memory
        avg_memory = statistics.mean(memory_samples) if memory_samples else final_memory
        
        # Calcular estatísticas de resposta
        avg_response_time = statistics.mean(response_times) if response_times else 0
        min_response_time = min(response_times) if response_times else 0
        max_response_time = max(response_times) if response_times else 0
        percentiles = self.calculate_percentiles(response_times)
        
        result = PerformanceResult(
            test_name=f"Memory Stress: {duration_seconds}s",
            success=success_count > 0,
            duration=total_duration,
            requests_count=success_count + len(errors),
            success_rate=(success_count / (success_count + len(errors))) * 100 if (success_count + len(errors)) > 0 else 0,
            avg_response_time=avg_response_time,
            min_response_time=min_response_time,
            max_response_time=max_response_time,
            p95_response_time=percentiles["p95"],
            p99_response_time=percentiles["p99"],
            memory_usage_mb=max_memory,
            cpu_usage_percent=cpu_usage,
            errors=errors[:10],
            details={
                "duration_seconds": duration_seconds,
                "success_count": success_count,
                "memory_samples": len(memory_samples),
                "max_memory_mb": max_memory,
                "avg_memory_mb": avg_memory,
                "memory_growth_mb": max_memory - (memory_samples[0] if memory_samples else 0)
            }
        )
        
        self.results.append(result)
        return result
    
    def print_result(self, result: PerformanceResult):
        """Imprimir resultado de um teste."""
        status = "✅ PASSOU" if result.success else "❌ FALHOU"
        
        logger.info(f"{status} | {result.test_name}")
        logger.info(f"   ⏱️  Duração: {result.duration:.2f}s")
        logger.info(f"   📊 Requisições: {result.requests_count}")
        logger.info(f"   ✅ Taxa de sucesso: {result.success_rate:.1f}%")
        logger.info(f"   ⚡ Tempo médio: {result.avg_response_time*1000:.1f}ms")
        logger.info(f"   📈 P95: {result.p95_response_time*1000:.1f}ms, P99: {result.p99_response_time*1000:.1f}ms")
        logger.info(f"   🧠 Memória: {result.memory_usage_mb:.1f}MB")
        logger.info(f"   💻 CPU: {result.cpu_usage_percent:.1f}%")
        
        if result.errors:
            logger.warning(f"   ⚠️  Erros: {len(result.errors)} (primeiros: {result.errors[:3]})")
        
        # Detalhes específicos
        if "throughput_rps" in result.details:
            logger.info(f"   🚀 Throughput: {result.details['throughput_rps']:.1f} req/s")
        
        if "rate_limited_count" in result.details:
            logger.info(f"   🚦 Rate Limited: {result.details['rate_limited_count']} vezes")
        
        if "memory_growth_mb" in result.details:
            logger.info(f"   📈 Crescimento memória: {result.details['memory_growth_mb']:.1f}MB")
    
    def print_summary(self):
        """Imprimir resumo de todos os testes."""
        if not self.results:
            logger.warning("Nenhum resultado para exibir")
            return
        
        logger.info("\n" + "="*80)
        logger.info("📊 RESUMO DOS TESTES DE PERFORMANCE E CARGA")
        logger.info("="*80)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.success)
        total_duration = sum(r.duration for r in self.results)
        
        logger.info(f"⏱️  Duração total: {total_duration:.2f} segundos")
        logger.info(f"📈 Total de testes: {total_tests}")
        logger.info(f"✅ Testes aprovados: {passed_tests}")
        logger.info(f"❌ Testes falharam: {total_tests - passed_tests}")
        logger.info(f"📊 Taxa de sucesso: {(passed_tests/total_tests)*100:.1f}%")
        
        # Estatísticas de performance
        all_avg_times = [r.avg_response_time for r in self.results if r.avg_response_time > 0]
        all_success_rates = [r.success_rate for r in self.results]
        
        if all_avg_times:
            logger.info(f"\n⚡ PERFORMANCE:")
            logger.info(f"   • Tempo médio de resposta: {statistics.mean(all_avg_times)*1000:.1f}ms")
            logger.info(f"   • Melhor tempo: {min(all_avg_times)*1000:.1f}ms")
            logger.info(f"   • Pior tempo: {max(all_avg_times)*1000:.1f}ms")
        
        if all_success_rates:
            logger.info(f"\n📊 CONFIABILIDADE:")
            logger.info(f"   • Taxa de sucesso média: {statistics.mean(all_success_rates):.1f}%")
            logger.info(f"   • Melhor taxa: {max(all_success_rates):.1f}%")
            logger.info(f"   • Pior taxa: {min(all_success_rates):.1f}%")
        
        # Uso de recursos
        max_memory = max(r.memory_usage_mb for r in self.results)
        max_cpu = max(r.cpu_usage_percent for r in self.results)
        
        logger.info(f"\n💻 RECURSOS:")
        logger.info(f"   • Pico de memória: {max_memory:.1f}MB")
        logger.info(f"   • Pico de CPU: {max_cpu:.1f}%")
        
        # Recomendações
        logger.info(f"\n💡 RECOMENDAÇÕES:")
        
        if passed_tests == total_tests:
            logger.success("🎉 EXCELENTE! Todos os testes passaram!")
        elif passed_tests >= total_tests * 0.8:
            logger.info("✅ BOM! Maioria dos testes passou, alguns ajustes podem ser necessários.")
        else:
            logger.warning("⚠️ ATENÇÃO! Muitos testes falharam, revisão necessária.")
        
        # Verificar performance
        if all_avg_times and statistics.mean(all_avg_times) > 1.0:
            logger.warning("⚠️ Tempos de resposta altos detectados (>1s)")
        
        if max_memory > 1000:
            logger.warning("⚠️ Alto uso de memória detectado (>1GB)")
        
        if max_cpu > 80:
            logger.warning("⚠️ Alto uso de CPU detectado (>80%)")

async def run_all_tests():
    """Executar todos os testes de performance."""
    logger.info("🚀 INICIANDO TESTES DE PERFORMANCE E CARGA")
    logger.info("="*60)
    
    async with PerformanceTester() as tester:
        # Teste 1: Performance de endpoints individuais
        logger.info("\n🔍 FASE 1: TESTES DE ENDPOINTS INDIVIDUAIS")
        logger.info("-" * 50)
        
        endpoints = [
            "/health",
            "/api/v1/processes",
            "/api/v1/monitoring/status"
        ]
        
        for endpoint in endpoints:
            try:
                result = await tester.test_single_endpoint_performance(endpoint, iterations=20)
                tester.print_result(result)
            except Exception as e:
                logger.error(f"Erro no teste {endpoint}: {e}")
        
        # Teste 2: Carga concorrente
        logger.info("\n⚡ FASE 2: TESTES DE CARGA CONCORRENTE")
        logger.info("-" * 50)
        
        load_scenarios = [
            (5, 10),   # 5 usuários, 10 req cada
            (10, 5),   # 10 usuários, 5 req cada
            (20, 3),   # 20 usuários, 3 req cada
        ]
        
        for users, req_per_user in load_scenarios:
            try:
                result = await tester.test_concurrent_requests("/health", users, req_per_user)
                tester.print_result(result)
            except Exception as e:
                logger.error(f"Erro no teste de carga {users}x{req_per_user}: {e}")
        
        # Teste 3: Rate limiting
        logger.info("\n🚦 FASE 3: TESTES DE RATE LIMITING")
        logger.info("-" * 50)
        
        rate_scenarios = [
            (10, 10),  # 10 req/s por 10s
            (20, 10),  # 20 req/s por 10s
            (50, 5),   # 50 req/s por 5s
        ]
        
        for rps, duration in rate_scenarios:
            try:
                result = await tester.test_rate_limiting("/health", rps, duration)
                tester.print_result(result)
            except Exception as e:
                logger.error(f"Erro no teste de rate limiting {rps}req/s: {e}")
        
        # Teste 4: Stress de memória
        logger.info("\n🧠 FASE 4: TESTES DE STRESS DE MEMÓRIA")
        logger.info("-" * 50)
        
        try:
            result = await tester.test_memory_stress("/health", duration_seconds=20)
            tester.print_result(result)
        except Exception as e:
            logger.error(f"Erro no teste de stress de memória: {e}")
        
        # Resumo final
        tester.print_summary()

def main():
    """Função principal."""
    try:
        asyncio.run(run_all_tests())
    except KeyboardInterrupt:
        logger.info("\n⏹️ Testes interrompidos pelo usuário")
    except Exception as e:
        logger.error(f"❌ Erro durante os testes: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
