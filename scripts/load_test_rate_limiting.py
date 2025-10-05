#!/usr/bin/env python3
"""Script de teste de carga para o middleware de rate limiting."""

import asyncio
import aiohttp
import time
import statistics
import argparse
import json
from typing import List, Dict, Any
from dataclasses import dataclass
import sys
import os

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@dataclass
class TestResult:
    """Resultado de um teste de carga."""
    total_requests: int
    successful_requests: int
    rate_limited_requests: int
    failed_requests: int
    total_time: float
    requests_per_second: float
    average_response_time: float
    min_response_time: float
    max_response_time: float
    median_response_time: float
    p95_response_time: float
    p99_response_time: float


class RateLimitingLoadTester:
    """Classe para executar testes de carga no middleware de rate limiting."""
    
    def __init__(self, base_url: str, rate_limit_requests: int = 100, rate_limit_window: int = 60):
        self.base_url = base_url.rstrip('/')
        self.rate_limit_requests = rate_limit_requests
        self.rate_limit_window = rate_limit_window
        self.session = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        connector = aiohttp.TCPConnector(limit=100, limit_per_host=50)
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(connector=connector, timeout=timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def make_request(self, endpoint: str = "/api/test") -> Dict[str, Any]:
        """Fazer uma requisição e coletar métricas."""
        url = f"{self.base_url}{endpoint}"
        
        start_time = time.time()
        
        try:
            async with self.session.get(url) as response:
                end_time = time.time()
                response_time = end_time - start_time
                
                # Obter headers de rate limiting
                rate_limit_remaining = response.headers.get("X-RateLimit-Remaining")
                rate_limit_reset = response.headers.get("X-RateLimit-Reset")
                request_id = response.headers.get("X-Request-ID")
                
                return {
                    "status_code": response.status_code,
                    "response_time": response_time,
                    "rate_limit_remaining": rate_limit_remaining,
                    "rate_limit_reset": rate_limit_reset,
                    "request_id": request_id,
                    "success": response.status == 200,
                    "rate_limited": response.status == 429,
                    "error": None
                }
                
        except Exception as e:
            end_time = time.time()
            response_time = end_time - start_time
            
            return {
                "status_code": 0,
                "response_time": response_time,
                "rate_limit_remaining": None,
                "rate_limit_reset": None,
                "request_id": None,
                "success": False,
                "rate_limited": False,
                "error": str(e)
            }
    
    async def run_concurrent_test(self, 
                                 concurrent_requests: int = 10, 
                                 duration_seconds: int = 60,
                                 endpoint: str = "/api/test") -> TestResult:
        """Executar teste de carga com requisições concorrentes."""
        
        print(f"🚀 Iniciando teste de carga:")
        print(f"   - Requisições concorrentes: {concurrent_requests}")
        print(f"   - Duração: {duration_seconds} segundos")
        print(f"   - Endpoint: {endpoint}")
        print(f"   - Rate limit configurado: {self.rate_limit_requests} req/{self.rate_limit_window}s")
        print()
        
        start_time = time.time()
        end_time = start_time + duration_seconds
        
        response_times = []
        results = []
        
        # Criar tasks para requisições concorrentes
        async def worker(worker_id: int):
            """Worker para fazer requisições."""
            worker_results = []
            
            while time.time() < end_time:
                result = await self.make_request(endpoint)
                worker_results.append(result)
                response_times.append(result["response_time"])
                
                # Pequena pausa para evitar spam excessivo
                await asyncio.sleep(0.01)
            
            return worker_results
        
        # Executar workers concorrentes
        tasks = [worker(i) for i in range(concurrent_requests)]
        all_results = await asyncio.gather(*tasks)
        
        # Consolidar resultados
        for worker_results in all_results:
            results.extend(worker_results)
        
        total_time = time.time() - start_time
        
        return self._analyze_results(results, total_time)
    
    async def run_rate_limit_test(self, 
                                 requests_to_exceed_limit: int = None,
                                 endpoint: str = "/api/test") -> TestResult:
        """Executar teste específico para verificar rate limiting."""
        
        if requests_to_exceed_limit is None:
            requests_to_exceed_limit = self.rate_limit_requests + 10
        
        print(f"🎯 Teste de rate limiting:")
        print(f"   - Requisições: {requests_to_exceed_limit}")
        print(f"   - Rate limit: {self.rate_limit_requests} req/{self.rate_limit_window}s")
        print(f"   - Endpoint: {endpoint}")
        print()
        
        start_time = time.time()
        response_times = []
        results = []
        
        for i in range(requests_to_exceed_limit):
            result = await self.make_request(endpoint)
            results.append(result)
            response_times.append(result["response_time"])
            
            # Log progresso
            if (i + 1) % 10 == 0:
                remaining = self._get_remaining_from_result(result)
                print(f"   Requisição {i + 1}/{requests_to_exceed_limit} - "
                      f"Status: {result['status_code']} - "
                      f"Remaining: {remaining}")
        
        total_time = time.time() - start_time
        
        return self._analyze_results(results, total_time)
    
    def _analyze_results(self, results: List[Dict[str, Any]], total_time: float) -> TestResult:
        """Analisar resultados do teste."""
        
        total_requests = len(results)
        successful_requests = sum(1 for r in results if r["success"])
        rate_limited_requests = sum(1 for r in results if r["rate_limited"])
        failed_requests = sum(1 for r in results if not r["success"] and not r["rate_limited"])
        
        response_times = [r["response_time"] for r in results if r["response_time"] > 0]
        
        if response_times:
            average_response_time = statistics.mean(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
            median_response_time = statistics.median(response_times)
            
            # Calcular percentis
            sorted_times = sorted(response_times)
            p95_index = int(len(sorted_times) * 0.95)
            p99_index = int(len(sorted_times) * 0.99)
            
            p95_response_time = sorted_times[p95_index] if p95_index < len(sorted_times) else max_response_time
            p99_response_time = sorted_times[p99_index] if p99_index < len(sorted_times) else max_response_time
        else:
            average_response_time = min_response_time = max_response_time = 0
            median_response_time = p95_response_time = p99_response_time = 0
        
        requests_per_second = total_requests / total_time if total_time > 0 else 0
        
        return TestResult(
            total_requests=total_requests,
            successful_requests=successful_requests,
            rate_limited_requests=rate_limited_requests,
            failed_requests=failed_requests,
            total_time=total_time,
            requests_per_second=requests_per_second,
            average_response_time=average_response_time,
            min_response_time=min_response_time,
            max_response_time=max_response_time,
            median_response_time=median_response_time,
            p95_response_time=p95_response_time,
            p99_response_time=p99_response_time
        )
    
    def _get_remaining_from_result(self, result: Dict[str, Any]) -> str:
        """Obter remaining de rate limit do resultado."""
        remaining = result.get("rate_limit_remaining")
        if remaining is not None:
            return str(remaining)
        return "N/A"
    
    def print_results(self, result: TestResult, test_name: str = "Teste"):
        """Imprimir resultados do teste."""
        print(f"\n📊 Resultados do {test_name}:")
        print(f"{'='*50}")
        print(f"Total de requisições:     {result.total_requests}")
        print(f"Requisições bem-sucedidas: {result.successful_requests}")
        print(f"Rate limited:             {result.rate_limited_requests}")
        print(f"Falhas:                   {result.failed_requests}")
        print(f"Tempo total:              {result.total_time:.2f}s")
        print(f"Requisições/segundo:      {result.requests_per_second:.2f}")
        print()
        print("Tempos de resposta:")
        print(f"  Média:                  {result.average_response_time*1000:.2f}ms")
        print(f"  Mínimo:                 {result.min_response_time*1000:.2f}ms")
        print(f"  Máximo:                 {result.max_response_time*1000:.2f}ms")
        print(f"  Mediana:                {result.median_response_time*1000:.2f}ms")
        print(f"  P95:                    {result.p95_response_time*1000:.2f}ms")
        print(f"  P99:                    {result.p99_response_time*1000:.2f}ms")
        
        # Análise de rate limiting
        if result.rate_limited_requests > 0:
            rate_limit_percentage = (result.rate_limited_requests / result.total_requests) * 100
            print(f"\n✅ Rate limiting funcionando: {rate_limit_percentage:.1f}% das requisições foram limitadas")
        else:
            print(f"\n⚠️  Rate limiting não ativado - nenhuma requisição foi limitada")
        
        # Análise de performance
        if result.average_response_time > 1.0:
            print(f"⚠️  Tempo de resposta alto: {result.average_response_time*1000:.2f}ms")
        else:
            print(f"✅ Performance boa: {result.average_response_time*1000:.2f}ms")
        
        print(f"{'='*50}\n")


async def run_comprehensive_test(base_url: str, rate_limit_requests: int = 100, rate_limit_window: int = 60):
    """Executar suite completa de testes."""
    
    print("🧪 Suite de Testes de Rate Limiting")
    print("="*60)
    
    async with RateLimitingLoadTester(base_url, rate_limit_requests, rate_limit_window) as tester:
        
        # Teste 1: Teste de carga normal
        print("\n1️⃣ Teste de Carga Normal")
        result1 = await tester.run_concurrent_test(
            concurrent_requests=5,
            duration_seconds=30,
            endpoint="/api/test"
        )
        tester.print_results(result1, "Carga Normal")
        
        # Teste 2: Teste de rate limiting
        print("\n2️⃣ Teste de Rate Limiting")
        result2 = await tester.run_rate_limit_test(
            requests_to_exceed_limit=rate_limit_requests + 20,
            endpoint="/api/test"
        )
        tester.print_results(result2, "Rate Limiting")
        
        # Teste 3: Teste de alta concorrência
        print("\n3️⃣ Teste de Alta Concorrência")
        result3 = await tester.run_concurrent_test(
            concurrent_requests=20,
            duration_seconds=10,
            endpoint="/api/test"
        )
        tester.print_results(result3, "Alta Concorrência")
        
        # Resumo final
        print("\n📋 Resumo Final:")
        print(f"Rate limiting funcionando: {'✅' if result2.rate_limited_requests > 0 else '❌'}")
        print(f"Performance estável: {'✅' if result3.average_response_time < 0.5 else '❌'}")
        print(f"Sem falhas críticas: {'✅' if result1.failed_requests == 0 else '❌'}")


async def main():
    """Função principal."""
    parser = argparse.ArgumentParser(description="Teste de carga para rate limiting")
    parser.add_argument("--url", default="http://localhost:8000", help="URL base da API")
    parser.add_argument("--rate-limit", type=int, default=100, help="Rate limit configurado")
    parser.add_argument("--window", type=int, default=60, help="Janela de rate limit em segundos")
    parser.add_argument("--test-type", choices=["comprehensive", "load", "rate-limit"], 
                       default="comprehensive", help="Tipo de teste")
    parser.add_argument("--concurrent", type=int, default=10, help="Requisições concorrentes")
    parser.add_argument("--duration", type=int, default=60, help="Duração em segundos")
    parser.add_argument("--requests", type=int, help="Número de requisições para teste de rate limit")
    
    args = parser.parse_args()
    
    try:
        async with RateLimitingLoadTester(args.url, args.rate_limit, args.window) as tester:
            
            if args.test_type == "comprehensive":
                await run_comprehensive_test(args.url, args.rate_limit, args.window)
                
            elif args.test_type == "load":
                result = await tester.run_concurrent_test(
                    concurrent_requests=args.concurrent,
                    duration_seconds=args.duration
                )
                tester.print_results(result, "Teste de Carga")
                
            elif args.test_type == "rate-limit":
                result = await tester.run_rate_limit_test(
                    requests_to_exceed_limit=args.requests or (args.rate_limit + 10)
                )
                tester.print_results(result, "Teste de Rate Limiting")
    
    except KeyboardInterrupt:
        print("\n⚠️ Teste interrompido pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro durante o teste: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
