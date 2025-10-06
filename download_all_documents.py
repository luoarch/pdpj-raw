#!/usr/bin/env python3
"""
Script para baixar todos os documentos de um processo e armazenar no S3.
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any
import httpx
from loguru import logger

# Configurar logging
logger.add("download_logs.log", rotation="10 MB", retention="7 days")

# Configurações
BASE_URL = "http://localhost:8000"
ADMIN_TOKEN = "pdpj_admin_xYlOkmPaK9oO0xe_BdhoGBZvALr7YuHKI0gTgePAbZU"
PROCESS_NUMBER = "1011745-77.2025.8.11.0041"  # Processo novo com token válido

class DocumentDownloader:
    """Classe para baixar todos os documentos de um processo."""
    
    def __init__(self):
        self.base_url = BASE_URL
        self.headers = {
            "Authorization": f"Bearer {ADMIN_TOKEN}",
            "Content-Type": "application/json"
        }
        self.downloaded_count = 0
        self.failed_count = 0
        self.results = []
    
    async def get_process_documents(self) -> List[Dict[str, Any]]:
        """Obter lista de documentos do processo."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/v1/processes/{PROCESS_NUMBER}/files",
                headers=self.headers
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"📄 Encontrados {len(data['documents'])} documentos")
                return data['documents']
            else:
                logger.error(f"❌ Erro ao obter documentos: {response.status_code}")
                return []
    
    async def download_document(self, document_id: str, document_name: str) -> Dict[str, Any]:
        """Baixar um documento específico."""
        try:
            logger.info(f"⬇️ Baixando: {document_name} (ID: {document_id})")
            
            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/processes/{PROCESS_NUMBER}/download-document/{document_id}",
                    headers=self.headers
                )
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"✅ Baixado: {document_name}")
                    self.downloaded_count += 1
                    return {
                        "document_id": document_id,
                        "name": document_name,
                        "status": "success",
                        "result": result
                    }
                else:
                    logger.error(f"❌ Erro ao baixar {document_name}: {response.status_code}")
                    self.failed_count += 1
                    return {
                        "document_id": document_id,
                        "name": document_name,
                        "status": "failed",
                        "error": f"HTTP {response.status_code}: {response.text}"
                    }
                    
        except Exception as e:
            logger.error(f"❌ Exceção ao baixar {document_name}: {e}")
            self.failed_count += 1
            return {
                "document_id": document_id,
                "name": document_name,
                "status": "error",
                "error": str(e)
            }
    
    async def download_all_documents(self):
        """Baixar todos os documentos do processo."""
        logger.info(f"🚀 Iniciando download de todos os documentos do processo: {PROCESS_NUMBER}")
        
        # Obter lista de documentos
        documents = await self.get_process_documents()
        
        if not documents:
            logger.error("❌ Nenhum documento encontrado")
            return
        
        logger.info(f"📊 Total de documentos para baixar: {len(documents)}")
        
        # Baixar documentos em lotes para evitar sobrecarga
        batch_size = 5
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            logger.info(f"📦 Processando lote {i//batch_size + 1}: {len(batch)} documentos")
            
            # Criar tasks para o lote atual
            tasks = []
            for doc in batch:
                if not doc.get('downloaded', True):  # Só baixar se não foi baixado
                    # Usar UUID ao invés de ID numérico
                    document_uuid = doc.get('uuid', doc['id'])
                    task = self.download_document(document_uuid, doc['name'])
                    tasks.append(task)
            
            # Executar downloads do lote em paralelo
            if tasks:
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for result in batch_results:
                    if isinstance(result, Exception):
                        logger.error(f"❌ Erro no lote: {result}")
                        self.failed_count += 1
                    else:
                        self.results.append(result)
                
                # Pequena pausa entre lotes
                await asyncio.sleep(2)
        
        # Gerar relatório final
        await self.generate_report()
    
    async def generate_report(self):
        """Gerar relatório final do download."""
        logger.info("📊 Relatório Final:")
        logger.info(f"✅ Documentos baixados com sucesso: {self.downloaded_count}")
        logger.info(f"❌ Documentos com falha: {self.failed_count}")
        logger.info(f"📄 Total processado: {len(self.results)}")
        
        # Salvar relatório em arquivo
        report = {
            "process_number": PROCESS_NUMBER,
            "timestamp": str(asyncio.get_event_loop().time()),
            "summary": {
                "total_documents": len(self.results),
                "downloaded_successfully": self.downloaded_count,
                "failed": self.failed_count
            },
            "details": self.results
        }
        
        with open(f"download_report_{PROCESS_NUMBER.replace('-', '_').replace('.', '_')}.json", "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📄 Relatório salvo em: download_report_{PROCESS_NUMBER.replace('-', '_').replace('.', '_')}.json")

async def main():
    """Função principal."""
    downloader = DocumentDownloader()
    await downloader.download_all_documents()

if __name__ == "__main__":
    print("🚀 Iniciando download de todos os documentos...")
    print(f"📋 Processo: {PROCESS_NUMBER}")
    print(f"🌐 API: {BASE_URL}")
    print("-" * 50)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️ Download interrompido pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro fatal: {e}")
        sys.exit(1)
    
    print("\n✅ Download concluído!")
