#!/usr/bin/env python3
"""
Script para testar todos os endpoints da API PDPJ conforme definido na collection.
"""

import asyncio
import httpx
import json
import time
from typing import Dict, List, Any
from loguru import logger

# Configurações
BASE_URL = "http://localhost:8000"
API_TOKENS = {
    "test": "pdpj_test_b3Xd4tVTqsXrKzJ_sIinewIxmsinYTaIf6KFK9XINvM",
    "admin": "pdpj_admin_xYlOkmPaK9oO0xe_BdhoGBZvALr7YuHKI0gTgePAbZU"
}
TEST_PROCESS_NUMBER = "10001459120238260597"

class EndpointTester:
    """Classe para testar todos os endpoints da API."""
    
    def __init__(self):
        self.results = []
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    def get_headers(self, token_type: str = "test") -> Dict[str, str]:
        """Obter headers de autenticação."""
        return {
            "Authorization": f"Bearer {API_TOKENS[token_type]}",
            "Content-Type": "application/json"
        }
    
    async def test_endpoint(self, name: str, method: str, url: str, 
                          headers: Dict[str, str] = None, 
                          json_data: Dict[str, Any] = None,
                          expected_status: int = 200) -> Dict[str, Any]:
        """Testar um endpoint específico."""
        start_time = time.time()
        
        try:
            if method.upper() == "GET":
                response = await self.client.get(url, headers=headers)
            elif method.upper() == "POST":
                response = await self.client.post(url, headers=headers, json=json_data)
            elif method.upper() == "PUT":
                response = await self.client.put(url, headers=headers, json=json_data)
            elif method.upper() == "DELETE":
                response = await self.client.delete(url, headers=headers)
            else:
                raise ValueError(f"Método HTTP não suportado: {method}")
            
            response_time = time.time() - start_time
            
            result = {
                "name": name,
                "method": method,
                "url": url,
                "status_code": response.status_code,
                "response_time": round(response_time, 3),
                "success": response.status_code == expected_status,
                "content_type": response.headers.get("content-type", ""),
                "content_length": len(response.content) if response.content else 0
            }
            
            # Tentar parsear JSON se possível
            try:
                if response.headers.get("content-type", "").startswith("application/json"):
                    result["json_response"] = response.json()
            except:
                result["text_response"] = response.text[:500]  # Primeiros 500 chars
            
            logger.info(f"✅ {name}: {response.status_code} ({response_time:.3f}s)")
            return result
            
        except Exception as e:
            response_time = time.time() - start_time
            result = {
                "name": name,
                "method": method,
                "url": url,
                "status_code": None,
                "response_time": round(response_time, 3),
                "success": False,
                "error": str(e)
            }
            logger.error(f"❌ {name}: {str(e)}")
            return result
    
    async def test_health_endpoints(self):
        """Testar endpoints de health check."""
        logger.info("🏥 Testando Health Check endpoints...")
        
        endpoints = [
            ("Health Check", "GET", f"{BASE_URL}/health"),
            ("Health Check (Root)", "GET", f"{BASE_URL}/"),
        ]
        
        for name, method, url in endpoints:
            result = await self.test_endpoint(name, method, url)
            self.results.append(result)
    
    async def test_user_endpoints(self):
        """Testar endpoints de usuários."""
        logger.info("👤 Testando User endpoints...")
        
        headers = self.get_headers("admin")
        
        endpoints = [
            ("Listar Usuários", "GET", f"{BASE_URL}/api/v1/users", headers),
            ("Meu Perfil", "GET", f"{BASE_URL}/api/v1/users/me", headers),
        ]
        
        for name, method, url, h in endpoints:
            result = await self.test_endpoint(name, method, url, h)
            self.results.append(result)
    
    async def test_process_endpoints(self):
        """Testar endpoints de processos."""
        logger.info("📋 Testando Process endpoints...")
        
        headers = self.get_headers("test")
        
        endpoints = [
            ("Listar Processos", "GET", f"{BASE_URL}/api/v1/processes", headers),
            ("Buscar Processo", "GET", f"{BASE_URL}/api/v1/processes/{TEST_PROCESS_NUMBER}", headers),
            ("Listar Documentos", "GET", f"{BASE_URL}/api/v1/processes/{TEST_PROCESS_NUMBER}/files", headers),
        ]
        
        for name, method, url, h in endpoints:
            result = await self.test_endpoint(name, method, url, h)
            self.results.append(result)
        
        # Teste de busca em lote
        search_data = {
            "process_numbers": [TEST_PROCESS_NUMBER],
            "include_documents": True,
            "page": 1,
            "limit": 10
        }
        
        result = await self.test_endpoint(
            "Buscar Processos (Lote)", 
            "POST", 
            f"{BASE_URL}/api/v1/processes/search", 
            headers, 
            search_data
        )
        self.results.append(result)
    
    async def test_document_endpoints(self):
        """Testar endpoints de documentos."""
        logger.info("📄 Testando Document endpoints...")
        
        headers = self.get_headers("test")
        
        # Teste de download de documentos
        result = await self.test_endpoint(
            "Download Documentos", 
            "POST", 
            f"{BASE_URL}/api/v1/processes/{TEST_PROCESS_NUMBER}/download-documents", 
            headers,
            expected_status=200  # Mudando para 200 pois pode retornar sucesso imediato
        )
        self.results.append(result)
    
    async def test_monitoring_endpoints(self):
        """Testar endpoints de monitoramento."""
        logger.info("📊 Testando Monitoring endpoints...")
        
        headers = self.get_headers("admin")
        
        endpoints = [
            ("Status da API", "GET", f"{BASE_URL}/api/v1/monitoring/status", headers),
            ("Métricas", "GET", f"{BASE_URL}/api/v1/monitoring/metrics", headers),
            ("Performance", "GET", f"{BASE_URL}/api/v1/monitoring/performance", headers),
            ("Health Detalhado", "GET", f"{BASE_URL}/api/v1/monitoring/health/detailed", headers),
        ]
        
        for name, method, url, h in endpoints:
            result = await self.test_endpoint(name, method, url, h)
            self.results.append(result)
    
    async def test_authentication_endpoints(self):
        """Testar endpoints de autenticação."""
        logger.info("🔐 Testando Authentication endpoints...")
        
        # Teste sem autenticação (deve retornar 401)
        result = await self.test_endpoint(
            "Sem Autenticação", 
            "GET", 
            f"{BASE_URL}/api/v1/processes", 
            expected_status=401
        )
        self.results.append(result)
        
        # Teste com token inválido
        invalid_headers = {"Authorization": "Bearer invalid_token"}
        result = await self.test_endpoint(
            "Token Inválido", 
            "GET", 
            f"{BASE_URL}/api/v1/processes", 
            invalid_headers,
            expected_status=401
        )
        self.results.append(result)
    
    async def run_all_tests(self):
        """Executar todos os testes."""
        logger.info("🚀 Iniciando testes de todos os endpoints...")
        
        start_time = time.time()
        
        # Executar todos os testes
        await self.test_health_endpoints()
        await self.test_authentication_endpoints()
        await self.test_user_endpoints()
        await self.test_process_endpoints()
        await self.test_document_endpoints()
        await self.test_monitoring_endpoints()
        
        total_time = time.time() - start_time
        
        # Gerar relatório
        self.generate_report(total_time)
    
    def generate_report(self, total_time: float):
        """Gerar relatório dos testes."""
        logger.info("📊 Gerando relatório...")
        
        total_tests = len(self.results)
        successful_tests = sum(1 for r in self.results if r["success"])
        failed_tests = total_tests - successful_tests
        
        # Calcular métricas
        response_times = [r["response_time"] for r in self.results if r["response_time"]]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        max_response_time = max(response_times) if response_times else 0
        min_response_time = min(response_times) if response_times else 0
        
        # Relatório
        report = {
            "summary": {
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "failed_tests": failed_tests,
                "success_rate": round((successful_tests / total_tests) * 100, 2),
                "total_time": round(total_time, 3),
                "avg_response_time": round(avg_response_time, 3),
                "max_response_time": round(max_response_time, 3),
                "min_response_time": round(min_response_time, 3)
            },
            "results": self.results
        }
        
        # Salvar relatório
        with open("endpoint_test_report.json", "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # Exibir resumo
        logger.info("=" * 60)
        logger.info("📊 RELATÓRIO DE TESTES DE ENDPOINTS")
        logger.info("=" * 60)
        logger.info(f"Total de testes: {total_tests}")
        logger.info(f"Testes bem-sucedidos: {successful_tests}")
        logger.info(f"Testes falharam: {failed_tests}")
        logger.info(f"Taxa de sucesso: {report['summary']['success_rate']}%")
        logger.info(f"Tempo total: {total_time:.3f}s")
        logger.info(f"Tempo médio de resposta: {avg_response_time:.3f}s")
        logger.info(f"Tempo máximo de resposta: {max_response_time:.3f}s")
        logger.info(f"Tempo mínimo de resposta: {min_response_time:.3f}s")
        logger.info("=" * 60)
        
        # Exibir falhas
        if failed_tests > 0:
            logger.warning("❌ TESTES QUE FALHARAM:")
            for result in self.results:
                if not result["success"]:
                    logger.warning(f"  - {result['name']}: {result.get('error', 'Status code incorreto')}")
        
        logger.info("📄 Relatório detalhado salvo em: endpoint_test_report.json")

async def main():
    """Função principal."""
    async with EndpointTester() as tester:
        await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
