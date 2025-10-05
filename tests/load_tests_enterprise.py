"""
Testes de carga específicos para cenários enterprise.
"""

import asyncio
import time
import random
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor
import aiohttp
from loguru import logger

from app.core.dynamic_limits import get_current_limits, Environment
from app.services.process_cache_service import process_cache_service
from app.utils.advanced_retry import retry_http
from app.core.proactive_monitoring import proactive_monitor


class LoadTestRunner:
    """Executor de testes de carga."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.limits = get_current_limits()
        self.results = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "response_times": [],
            "errors": [],
            "start_time": None,
            "end_time": None
        }
    
    async def run_concurrent_requests(self, endpoint: str, num_requests: int, concurrency: int = 10):
        """Executar requisições concorrentes."""
        logger.info(f"🚀 Iniciando teste de carga: {num_requests} requisições com concorrência {concurrency}")
        
        self.results["start_time"] = time.time()
        
        # Criar semáforo para controlar concorrência
        semaphore = asyncio.Semaphore(concurrency)
        
        async def make_request(request_id: int):
            async with semaphore:
                try:
                    start_time = time.time()
                    
                    async with aiohttp.ClientSession() as session:
                        async with session.get(f"{self.base_url}{endpoint}") as response:
                            duration = time.time() - start_time
                            
                            self.results["total_requests"] += 1
                            self.results["response_times"].append(duration)
                            
                            if response.status == 200:
                                self.results["successful_requests"] += 1
                            else:
                                self.results["failed_requests"] += 1
                                self.results["errors"].append({
                                    "request_id": request_id,
                                    "status": response.status,
                                    "duration": duration
                                })
                    
                    # Registrar métricas
                    proactive_monitor.record_request("GET", endpoint, response.status, duration)
                    
                except Exception as e:
                    self.results["failed_requests"] += 1
                    self.results["errors"].append({
                        "request_id": request_id,
                        "error": str(e)
                    })
                    logger.error(f"❌ Erro na requisição {request_id}: {e}")
        
        # Criar tasks para todas as requisições
        tasks = [make_request(i) for i in range(num_requests)]
        
        # Executar em paralelo
        await asyncio.gather(*tasks, return_exceptions=True)
        
        self.results["end_time"] = time.time()
        
        # Calcular estatísticas
        self._calculate_statistics()
        
        return self.results
    
    def _calculate_statistics(self):
        """Calcular estatísticas dos resultados."""
        if not self.results["response_times"]:
            return
        
        response_times = self.results["response_times"]
        
        self.results["statistics"] = {
            "total_duration": self.results["end_time"] - self.results["start_time"],
            "requests_per_second": self.results["total_requests"] / (self.results["end_time"] - self.results["start_time"]),
            "success_rate": self.results["successful_requests"] / self.results["total_requests"] if self.results["total_requests"] > 0 else 0,
            "average_response_time": sum(response_times) / len(response_times),
            "min_response_time": min(response_times),
            "max_response_time": max(response_times),
            "p95_response_time": sorted(response_times)[int(len(response_times) * 0.95)],
            "p99_response_time": sorted(response_times)[int(len(response_times) * 0.99)]
        }
    
    def print_results(self):
        """Imprimir resultados do teste."""
        print("\n" + "=" * 60)
        print("📊 RESULTADOS DO TESTE DE CARGA")
        print("=" * 60)
        
        print(f"Total de requisições: {self.results['total_requests']}")
        print(f"Requisições bem-sucedidas: {self.results['successful_requests']}")
        print(f"Requisições falharam: {self.results['failed_requests']}")
        
        if "statistics" in self.results:
            stats = self.results["statistics"]
            print(f"Taxa de sucesso: {stats['success_rate']:.2%}")
            print(f"Requisições por segundo: {stats['requests_per_second']:.2f}")
            print(f"Tempo médio de resposta: {stats['average_response_time']:.3f}s")
            print(f"Tempo mínimo de resposta: {stats['min_response_time']:.3f}s")
            print(f"Tempo máximo de resposta: {stats['max_response_time']:.3f}s")
            print(f"P95 tempo de resposta: {stats['p95_response_time']:.3f}s")
            print(f"P99 tempo de resposta: {stats['p99_response_time']:.3f}s")
        
        print("=" * 60)


class EnterpriseLoadTests:
    """Testes de carga específicos para cenários enterprise."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.limits = get_current_limits()
    
    async def test_concurrent_process_search(self, num_requests: int = 1000, concurrency: int = 50):
        """Teste de busca concorrente de processos."""
        logger.info(f"🧪 Teste: Busca concorrente de processos ({num_requests} requisições, {concurrency} concorrência)")
        
        runner = LoadTestRunner(self.base_url)
        results = await runner.run_concurrent_requests("/processes/", num_requests, concurrency)
        
        # Verificar se atende aos requisitos
        success_rate = results["statistics"]["success_rate"]
        avg_response_time = results["statistics"]["average_response_time"]
        
        if success_rate >= 0.95 and avg_response_time <= 2.0:
            logger.info("✅ Teste de busca concorrente PASSOU")
        else:
            logger.warning(f"⚠️ Teste de busca concorrente FALHOU: {success_rate:.2%} sucesso, {avg_response_time:.3f}s resposta")
        
        return results
    
    async def test_batch_process_search(self, batch_sizes: List[int] = [10, 50, 100, 500]):
        """Teste de busca em lote de processos."""
        logger.info(f"🧪 Teste: Busca em lote de processos (tamanhos: {batch_sizes})")
        
        results = {}
        
        for batch_size in batch_sizes:
            logger.info(f"📦 Testando lote de {batch_size} processos")
            
            # Gerar números de processo fictícios
            process_numbers = [f"5000000-{i:02d}.2025.4.03.6327" for i in range(batch_size)]
            
            start_time = time.time()
            
            try:
                async with aiohttp.ClientSession() as session:
                    payload = {"process_numbers": process_numbers}
                    
                    async with session.post(
                        f"{self.base_url}/processes/search",
                        json=payload
                    ) as response:
                        duration = time.time() - start_time
                        
                        results[batch_size] = {
                            "status_code": response.status,
                            "duration": duration,
                            "success": response.status == 200
                        }
                        
                        if response.status == 200:
                            data = await response.json()
                            results[batch_size]["found"] = data.get("found", 0)
                            results[batch_size]["not_found"] = len(data.get("not_found", []))
                        
                        logger.info(f"✅ Lote {batch_size}: {response.status} em {duration:.3f}s")
                        
            except Exception as e:
                results[batch_size] = {
                    "status_code": 0,
                    "duration": time.time() - start_time,
                    "success": False,
                    "error": str(e)
                }
                logger.error(f"❌ Lote {batch_size} falhou: {e}")
        
        return results
    
    async def test_document_download_load(self, num_downloads: int = 100, concurrency: int = 10):
        """Teste de carga para download de documentos."""
        logger.info(f"🧪 Teste: Download de documentos ({num_downloads} downloads, {concurrency} concorrência)")
        
        # Simular downloads (em produção, usar endpoints reais)
        results = {
            "total_downloads": num_downloads,
            "successful_downloads": 0,
            "failed_downloads": 0,
            "download_times": [],
            "errors": []
        }
        
        semaphore = asyncio.Semaphore(concurrency)
        
        async def simulate_download(download_id: int):
            async with semaphore:
                try:
                    start_time = time.time()
                    
                    # Simular download (substituir por chamada real)
                    await asyncio.sleep(random.uniform(0.1, 2.0))
                    
                    duration = time.time() - start_time
                    results["download_times"].append(duration)
                    results["successful_downloads"] += 1
                    
                    logger.debug(f"✅ Download {download_id} concluído em {duration:.3f}s")
                    
                except Exception as e:
                    results["failed_downloads"] += 1
                    results["errors"].append({"download_id": download_id, "error": str(e)})
                    logger.error(f"❌ Download {download_id} falhou: {e}")
        
        # Executar downloads
        tasks = [simulate_download(i) for i in range(num_downloads)]
        await asyncio.gather(*tasks, return_exceptions=True)
        
        # Calcular estatísticas
        if results["download_times"]:
            results["statistics"] = {
                "average_download_time": sum(results["download_times"]) / len(results["download_times"]),
                "min_download_time": min(results["download_times"]),
                "max_download_time": max(results["download_times"]),
                "success_rate": results["successful_downloads"] / results["total_downloads"]
            }
        
        return results
    
    async def test_memory_usage_under_load(self, duration_minutes: int = 5):
        """Teste de uso de memória sob carga."""
        logger.info(f"🧪 Teste: Uso de memória sob carga ({duration_minutes} minutos)")
        
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        results = {
            "initial_memory_mb": initial_memory / 1024 / 1024,
            "peak_memory_mb": initial_memory / 1024 / 1024,
            "final_memory_mb": 0,
            "memory_growth_mb": 0,
            "test_duration": duration_minutes
        }
        
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        
        # Executar carga contínua
        while time.time() < end_time:
            # Simular carga
            await self.test_concurrent_process_search(100, 10)
            
            # Verificar uso de memória
            current_memory = process.memory_info().rss
            current_memory_mb = current_memory / 1024 / 1024
            
            if current_memory_mb > results["peak_memory_mb"]:
                results["peak_memory_mb"] = current_memory_mb
            
            # Aguardar antes da próxima iteração
            await asyncio.sleep(10)
        
        results["final_memory_mb"] = process.memory_info().rss / 1024 / 1024
        results["memory_growth_mb"] = results["final_memory_mb"] - results["initial_memory_mb"]
        
        return results
    
    async def test_rate_limiting(self, requests_per_second: int = 100, duration_seconds: int = 60):
        """Teste de rate limiting."""
        logger.info(f"🧪 Teste: Rate limiting ({requests_per_second} req/s por {duration_seconds}s)")
        
        results = {
            "total_requests": 0,
            "rate_limited_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "rate_limit_hits": []
        }
        
        start_time = time.time()
        end_time = start_time + duration_seconds
        
        # Calcular intervalo entre requisições
        interval = 1.0 / requests_per_second
        
        while time.time() < end_time:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{self.base_url}/processes/") as response:
                        results["total_requests"] += 1
                        
                        if response.status == 200:
                            results["successful_requests"] += 1
                        elif response.status == 429:
                            results["rate_limited_requests"] += 1
                            results["rate_limit_hits"].append(time.time())
                        else:
                            results["failed_requests"] += 1
                
                # Aguardar intervalo
                await asyncio.sleep(interval)
                
            except Exception as e:
                results["failed_requests"] += 1
                logger.error(f"❌ Erro no teste de rate limiting: {e}")
        
        return results
    
    async def run_all_tests(self):
        """Executar todos os testes de carga."""
        logger.info("🚀 INICIANDO TESTES DE CARGA ENTERPRISE")
        logger.info("=" * 60)
        
        all_results = {}
        
        try:
            # Teste 1: Busca concorrente
            all_results["concurrent_search"] = await self.test_concurrent_process_search(1000, 50)
            
            # Teste 2: Busca em lote
            all_results["batch_search"] = await self.test_batch_process_search([10, 50, 100, 500])
            
            # Teste 3: Download de documentos
            all_results["document_download"] = await self.test_document_download_load(100, 10)
            
            # Teste 4: Uso de memória
            all_results["memory_usage"] = await self.test_memory_usage_under_load(2)  # 2 minutos para teste
            
            # Teste 5: Rate limiting
            all_results["rate_limiting"] = await self.test_rate_limiting(50, 30)  # 50 req/s por 30s
            
            logger.info("✅ TODOS OS TESTES DE CARGA CONCLUÍDOS")
            
        except Exception as e:
            logger.error(f"❌ Erro durante os testes de carga: {e}")
        
        return all_results


async def main():
    """Função principal para executar testes de carga."""
    logger.info("🧪 INICIANDO TESTES DE CARGA ENTERPRISE")
    
    # Configurar ambiente de teste
    from app.core.dynamic_limits import environment_limits
    environment_limits._current_environment = Environment.TESTING
    
    # Executar testes
    load_tests = EnterpriseLoadTests()
    results = await load_tests.run_all_tests()
    
    # Imprimir resumo
    print("\n" + "=" * 60)
    print("📊 RESUMO DOS TESTES DE CARGA")
    print("=" * 60)
    
    for test_name, test_results in results.items():
        print(f"\n{test_name.upper()}:")
        if isinstance(test_results, dict):
            for key, value in test_results.items():
                if isinstance(value, (int, float)):
                    print(f"  {key}: {value}")
                elif isinstance(value, dict) and "statistics" in value:
                    stats = value["statistics"]
                    print(f"  Taxa de sucesso: {stats.get('success_rate', 0):.2%}")
                    print(f"  Tempo médio: {stats.get('average_response_time', 0):.3f}s")
    
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
