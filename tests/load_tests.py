"""Testes de carga para validar performance ultra-rápida da API PDPJ."""

import asyncio
import time
import statistics
from typing import List, Dict, Any
import httpx
import pytest
from loguru import logger

# Configurações dos testes de carga
BASE_URL = "http://localhost:8000"
ULTRA_FAST_BASE_URL = f"{BASE_URL}/ultra-fast/processes"

# Dados de teste
TEST_PROCESS_NUMBERS = [
    "1000000-01.2023.8.26.0001",
    "1000001-01.2023.8.26.0001", 
    "1000002-01.2023.8.26.0001",
    "1000003-01.2023.8.26.0001",
    "1000004-01.2023.8.26.0001",
    "1000005-01.2023.8.26.0001",
    "1000006-01.2023.8.26.0001",
    "1000007-01.2023.8.26.0001",
    "1000008-01.2023.8.26.0001",
    "1000009-01.2023.8.26.0001"
] * 100  # 1000 processos


class LoadTestResults:
    """Classe para armazenar e analisar resultados dos testes de carga."""
    
    def __init__(self):
        self.results: List[Dict[str, Any]] = []
        self.start_time: float = 0
        self.end_time: float = 0
    
    def add_result(self, result: Dict[str, Any]):
        """Adicionar resultado de um teste."""
        self.results.append(result)
    
    def calculate_stats(self) -> Dict[str, Any]:
        """Calcular estatísticas dos resultados."""
        if not self.results:
            return {}
        
        response_times = [r.get("response_time", 0) for r in self.results]
        status_codes = [r.get("status_code", 0) for r in self.results]
        
        successful_requests = len([r for r in self.results if r.get("status_code") == 200])
        failed_requests = len(self.results) - successful_requests
        
        total_time = self.end_time - self.start_time
        
        return {
            "total_requests": len(self.results),
            "successful_requests": successful_requests,
            "failed_requests": failed_requests,
            "success_rate": (successful_requests / len(self.results)) * 100 if self.results else 0,
            "total_time": total_time,
            "requests_per_second": len(self.results) / total_time if total_time > 0 else 0,
            "response_time": {
                "min": min(response_times) if response_times else 0,
                "max": max(response_times) if response_times else 0,
                "mean": statistics.mean(response_times) if response_times else 0,
                "median": statistics.median(response_times) if response_times else 0,
                "p95": self._percentile(response_times, 95) if response_times else 0,
                "p99": self._percentile(response_times, 99) if response_times else 0,
            },
            "status_codes": dict(zip(*np.unique(status_codes, return_counts=True))) if status_codes else {}
        }
    
    def _percentile(self, data: List[float], percentile: float) -> float:
        """Calcular percentil."""
        if not data:
            return 0
        sorted_data = sorted(data)
        index = (percentile / 100) * (len(sorted_data) - 1)
        if index.is_integer():
            return sorted_data[int(index)]
        else:
            lower = sorted_data[int(index)]
            upper = sorted_data[int(index) + 1]
            return lower + (upper - lower) * (index - int(index))


async def make_request(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    **kwargs
) -> Dict[str, Any]:
    """Fazer uma requisição HTTP e medir o tempo."""
    start_time = time.time()
    
    try:
        response = await client.request(method, url, **kwargs)
        response_time = time.time() - start_time
        
        return {
            "status_code": response.status_code,
            "response_time": response_time,
            "success": response.status_code == 200,
            "response_size": len(response.content) if response.content else 0
        }
    except Exception as e:
        response_time = time.time() - start_time
        return {
            "status_code": 0,
            "response_time": response_time,
            "success": False,
            "error": str(e)
        }


async def test_ultra_fast_search_small_batch():
    """Teste de carga para busca de pequeno lote (10 processos)."""
    logger.info("🧪 Iniciando teste de carga: Busca pequeno lote (10 processos)")
    
    results = LoadTestResults()
    results.start_time = time.time()
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Preparar dados de teste
        test_data = {
            "process_numbers": TEST_PROCESS_NUMBERS[:10],
            "include_documents": False,
            "force_refresh": False
        }
        
        # Executar 100 requisições simultâneas
        tasks = []
        for _ in range(100):
            task = make_request(
                client,
                "POST",
                f"{ULTRA_FAST_BASE_URL}/search",
                json=test_data
            )
            tasks.append(task)
        
        # Executar todas as requisições em paralelo
        test_results = await asyncio.gather(*tasks)
        
        # Processar resultados
        for result in test_results:
            results.add_result(result)
    
    results.end_time = time.time()
    stats = results.calculate_stats()
    
    logger.info(f"✅ Teste pequeno lote concluído:")
    logger.info(f"   Total de requisições: {stats['total_requests']}")
    logger.info(f"   Taxa de sucesso: {stats['success_rate']:.2f}%")
    logger.info(f"   Requests/segundo: {stats['requests_per_second']:.2f}")
    logger.info(f"   Tempo médio de resposta: {stats['response_time']['mean']:.3f}s")
    logger.info(f"   P95: {stats['response_time']['p95']:.3f}s")
    
    # Assertions
    assert stats['success_rate'] >= 95.0, f"Taxa de sucesso muito baixa: {stats['success_rate']:.2f}%"
    assert stats['requests_per_second'] >= 50.0, f"Throughput muito baixo: {stats['requests_per_second']:.2f} req/s"
    assert stats['response_time']['mean'] <= 2.0, f"Tempo de resposta muito alto: {stats['response_time']['mean']:.3f}s"


async def test_ultra_fast_search_medium_batch():
    """Teste de carga para busca de médio lote (100 processos)."""
    logger.info("🧪 Iniciando teste de carga: Busca médio lote (100 processos)")
    
    results = LoadTestResults()
    results.start_time = time.time()
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        # Preparar dados de teste
        test_data = {
            "process_numbers": TEST_PROCESS_NUMBERS[:100],
            "include_documents": False,
            "force_refresh": False
        }
        
        # Executar 20 requisições simultâneas
        tasks = []
        for _ in range(20):
            task = make_request(
                client,
                "POST",
                f"{ULTRA_FAST_BASE_URL}/search",
                json=test_data
            )
            tasks.append(task)
        
        # Executar todas as requisições em paralelo
        test_results = await asyncio.gather(*tasks)
        
        # Processar resultados
        for result in test_results:
            results.add_result(result)
    
    results.end_time = time.time()
    stats = results.calculate_stats()
    
    logger.info(f"✅ Teste médio lote concluído:")
    logger.info(f"   Total de requisições: {stats['total_requests']}")
    logger.info(f"   Taxa de sucesso: {stats['success_rate']:.2f}%")
    logger.info(f"   Requests/segundo: {stats['requests_per_second']:.2f}")
    logger.info(f"   Tempo médio de resposta: {stats['response_time']['mean']:.3f}s")
    logger.info(f"   P95: {stats['response_time']['p95']:.3f}s")
    
    # Assertions
    assert stats['success_rate'] >= 90.0, f"Taxa de sucesso muito baixa: {stats['success_rate']:.2f}%"
    assert stats['requests_per_second'] >= 10.0, f"Throughput muito baixo: {stats['requests_per_second']:.2f} req/s"
    assert stats['response_time']['mean'] <= 10.0, f"Tempo de resposta muito alto: {stats['response_time']['mean']:.3f}s"


async def test_ultra_fast_search_large_batch():
    """Teste de carga para busca de grande lote (1000 processos)."""
    logger.info("🧪 Iniciando teste de carga: Busca grande lote (1000 processos)")
    
    results = LoadTestResults()
    results.start_time = time.time()
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        # Preparar dados de teste
        test_data = {
            "process_numbers": TEST_PROCESS_NUMBERS[:1000],
            "include_documents": False,
            "force_refresh": False
        }
        
        # Executar 5 requisições simultâneas
        tasks = []
        for _ in range(5):
            task = make_request(
                client,
                "POST",
                f"{ULTRA_FAST_BASE_URL}/search",
                json=test_data
            )
            tasks.append(task)
        
        # Executar todas as requisições em paralelo
        test_results = await asyncio.gather(*tasks)
        
        # Processar resultados
        for result in test_results:
            results.add_result(result)
    
    results.end_time = time.time()
    stats = results.calculate_stats()
    
    logger.info(f"✅ Teste grande lote concluído:")
    logger.info(f"   Total de requisições: {stats['total_requests']}")
    logger.info(f"   Taxa de sucesso: {stats['success_rate']:.2f}%")
    logger.info(f"   Requests/segundo: {stats['requests_per_second']:.2f}")
    logger.info(f"   Tempo médio de resposta: {stats['response_time']['mean']:.3f}s")
    logger.info(f"   P95: {stats['response_time']['p95']:.3f}s")
    
    # Assertions - Meta: 1000 processos em menos de 60 segundos
    assert stats['success_rate'] >= 80.0, f"Taxa de sucesso muito baixa: {stats['success_rate']:.2f}%"
    assert stats['response_time']['mean'] <= 60.0, f"Tempo de resposta muito alto: {stats['response_time']['mean']:.3f}s"
    assert stats['response_time']['p95'] <= 90.0, f"P95 muito alto: {stats['response_time']['p95']:.3f}s"


async def test_single_process_performance():
    """Teste de performance para busca de processo único."""
    logger.info("🧪 Iniciando teste de carga: Busca processo único")
    
    results = LoadTestResults()
    results.start_time = time.time()
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Executar 200 requisições simultâneas
        tasks = []
        for i in range(200):
            process_number = TEST_PROCESS_NUMBERS[i % len(TEST_PROCESS_NUMBERS)]
            task = make_request(
                client,
                "GET",
                f"{ULTRA_FAST_BASE_URL}/{process_number}"
            )
            tasks.append(task)
        
        # Executar todas as requisições em paralelo
        test_results = await asyncio.gather(*tasks)
        
        # Processar resultados
        for result in test_results:
            results.add_result(result)
    
    results.end_time = time.time()
    stats = results.calculate_stats()
    
    logger.info(f"✅ Teste processo único concluído:")
    logger.info(f"   Total de requisições: {stats['total_requests']}")
    logger.info(f"   Taxa de sucesso: {stats['success_rate']:.2f}%")
    logger.info(f"   Requests/segundo: {stats['requests_per_second']:.2f}")
    logger.info(f"   Tempo médio de resposta: {stats['response_time']['mean']:.3f}s")
    logger.info(f"   P95: {stats['response_time']['p95']:.3f}s")
    
    # Assertions
    assert stats['success_rate'] >= 95.0, f"Taxa de sucesso muito baixa: {stats['success_rate']:.2f}%"
    assert stats['requests_per_second'] >= 100.0, f"Throughput muito baixo: {stats['requests_per_second']:.2f} req/s"
    assert stats['response_time']['mean'] <= 1.0, f"Tempo de resposta muito alto: {stats['response_time']['mean']:.3f}s"


async def test_concurrent_mixed_workload():
    """Teste de carga mista com diferentes tipos de requisições."""
    logger.info("🧪 Iniciando teste de carga: Workload misto")
    
    results = LoadTestResults()
    results.start_time = time.time()
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        tasks = []
        
        # 50 requisições de processo único
        for i in range(50):
            process_number = TEST_PROCESS_NUMBERS[i % len(TEST_PROCESS_NUMBERS)]
            task = make_request(
                client,
                "GET",
                f"{ULTRA_FAST_BASE_URL}/{process_number}"
            )
            tasks.append(task)
        
        # 20 requisições de busca pequena (10 processos)
        for _ in range(20):
            test_data = {
                "process_numbers": TEST_PROCESS_NUMBERS[:10],
                "include_documents": False,
                "force_refresh": False
            }
            task = make_request(
                client,
                "POST",
                f"{ULTRA_FAST_BASE_URL}/search",
                json=test_data
            )
            tasks.append(task)
        
        # 10 requisições de busca média (100 processos)
        for _ in range(10):
            test_data = {
                "process_numbers": TEST_PROCESS_NUMBERS[:100],
                "include_documents": False,
                "force_refresh": False
            }
            task = make_request(
                client,
                "POST",
                f"{ULTRA_FAST_BASE_URL}/search",
                json=test_data
            )
            tasks.append(task)
        
        # Executar todas as requisições em paralelo
        test_results = await asyncio.gather(*tasks)
        
        # Processar resultados
        for result in test_results:
            results.add_result(result)
    
    results.end_time = time.time()
    stats = results.calculate_stats()
    
    logger.info(f"✅ Teste workload misto concluído:")
    logger.info(f"   Total de requisições: {stats['total_requests']}")
    logger.info(f"   Taxa de sucesso: {stats['success_rate']:.2f}%")
    logger.info(f"   Requests/segundo: {stats['requests_per_second']:.2f}")
    logger.info(f"   Tempo médio de resposta: {stats['response_time']['mean']:.3f}s")
    logger.info(f"   P95: {stats['response_time']['p95']:.3f}s")
    
    # Assertions
    assert stats['success_rate'] >= 90.0, f"Taxa de sucesso muito baixa: {stats['success_rate']:.2f}%"
    assert stats['requests_per_second'] >= 50.0, f"Throughput muito baixo: {stats['requests_per_second']:.2f} req/s"


async def test_health_check_performance():
    """Teste de performance do endpoint de health check."""
    logger.info("🧪 Iniciando teste de carga: Health check")
    
    results = LoadTestResults()
    results.start_time = time.time()
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Executar 500 requisições simultâneas
        tasks = []
        for _ in range(500):
            task = make_request(
                client,
                "GET",
                f"{BASE_URL}/health"
            )
            tasks.append(task)
        
        # Executar todas as requisições em paralelo
        test_results = await asyncio.gather(*tasks)
        
        # Processar resultados
        for result in test_results:
            results.add_result(result)
    
    results.end_time = time.time()
    stats = results.calculate_stats()
    
    logger.info(f"✅ Teste health check concluído:")
    logger.info(f"   Total de requisições: {stats['total_requests']}")
    logger.info(f"   Taxa de sucesso: {stats['success_rate']:.2f}%")
    logger.info(f"   Requests/segundo: {stats['requests_per_second']:.2f}")
    logger.info(f"   Tempo médio de resposta: {stats['response_time']['mean']:.3f}s")
    logger.info(f"   P95: {stats['response_time']['p95']:.3f}s")
    
    # Assertions
    assert stats['success_rate'] >= 99.0, f"Taxa de sucesso muito baixa: {stats['success_rate']:.2f}%"
    assert stats['requests_per_second'] >= 500.0, f"Throughput muito baixo: {stats['requests_per_second']:.2f} req/s"
    assert stats['response_time']['mean'] <= 0.1, f"Tempo de resposta muito alto: {stats['response_time']['mean']:.3f}s"


async def run_all_load_tests():
    """Executar todos os testes de carga."""
    logger.info("🚀 Iniciando bateria completa de testes de carga")
    
    start_time = time.time()
    
    try:
        # Executar todos os testes
        await test_health_check_performance()
        await test_single_process_performance()
        await test_ultra_fast_search_small_batch()
        await test_ultra_fast_search_medium_batch()
        await test_ultra_fast_search_large_batch()
        await test_concurrent_mixed_workload()
        
        total_time = time.time() - start_time
        
        logger.info(f"🎉 Todos os testes de carga concluídos com sucesso em {total_time:.2f}s")
        logger.info("✅ Performance validada: Sistema capaz de processar 1000 processos em < 60s")
        
    except Exception as e:
        logger.error(f"❌ Falha nos testes de carga: {e}")
        raise


if __name__ == "__main__":
    # Executar testes de carga
    asyncio.run(run_all_load_tests())
