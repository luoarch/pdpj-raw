"""
Serviço para download de documentos grandes em chunks.
"""

import asyncio
import aiohttp
import hashlib
import time
import random
from typing import Dict, Any, Optional, AsyncGenerator, Tuple, List
from pathlib import Path
from loguru import logger

from app.core.dynamic_limits import get_current_limits
from app.services.s3_service import s3_service
from app.utils.monitoring_integration import record_download_metrics


class ChunkedDownloadService:
    """Serviço para download de documentos grandes em chunks."""
    
    def __init__(self):
        self.limits = get_current_limits()
        self.chunk_size = 1024 * 1024  # 1MB por chunk
        self.max_chunks = 1000  # Máximo de chunks por documento
        self.retry_attempts = 3
    
    async def download_large_document(
        self,
        document_url: str,
        document_name: str,
        headers: Dict[str, Any],
        process_number: str,
        document_id: str
    ) -> Dict[str, Any]:
        """Download de documento grande em chunks."""
        logger.info(f"📦 Iniciando download em chunks: {document_name}")
        
        start_time = time.time()
        chunks = []
        total_size = 0
        chunk_count = 0
        
        try:
            async with aiohttp.ClientSession() as session:
                # Primeiro, obter informações do arquivo
                file_info = await self._get_file_info(session, document_url, headers)
                total_size = file_info.get("content_length", 0)
                
                # Verificar se o arquivo é muito grande
                if total_size > self.limits.max_document_size_mb * 1024 * 1024:
                    raise ValueError(f"Documento muito grande: {total_size} bytes")
                
                # Calcular número de chunks necessários
                chunks_needed = (total_size + self.chunk_size - 1) // self.chunk_size
                if chunks_needed > self.max_chunks:
                    raise ValueError(f"Muitos chunks necessários: {chunks_needed}")
                
                logger.info(f"📊 Download em {chunks_needed} chunks de {self.chunk_size} bytes")
                
                # Download em chunks
                async for chunk_data, chunk_index in self._download_chunks(
                    session, document_url, headers, chunks_needed
                ):
                    chunks.append((chunk_index, chunk_data))
                    chunk_count += 1
                    total_size += len(chunk_data)
                    
                    # Log progresso a cada 10 chunks
                    if chunk_count % 10 == 0:
                        logger.info(f"📊 Progresso: {chunk_count}/{chunks_needed} chunks baixados")
                
                # Reconstruir arquivo
                logger.info("🔧 Reconstruindo arquivo a partir dos chunks")
                file_content = await self._reconstruct_file(chunks)
                
                # Verificar integridade
                if len(file_content) != total_size:
                    raise ValueError(f"Tamanho do arquivo inconsistente: {len(file_content)} != {total_size}")
                
                # Upload para S3
                s3_key = f"processos/{process_number}/documentos/{document_id}/{document_name}"
                await s3_service.upload_file(
                    file_content=file_content,
                    s3_key=s3_key,
                    content_type=file_info.get("content_type", "application/octet-stream")
                )
                
                # Gerar URL presignada
                download_url = await s3_service.generate_presigned_url(s3_key, expiration=3600)
                
                duration = time.time() - start_time
                record_download_metrics("success", duration)
                
                logger.info(f"✅ Download em chunks concluído: {document_name} ({total_size} bytes)")
                
                return {
                    "status": "success",
                    "filepath": s3_key,
                    "size": total_size,
                    "chunks": chunk_count,
                    "download_url": download_url,
                    "duration": duration,
                    "method": "chunked"
                }
                
        except Exception as e:
            duration = time.time() - start_time
            record_download_metrics("error", duration)
            logger.error(f"❌ Erro no download em chunks: {e}")
            raise
    
    async def _get_file_info(self, session: aiohttp.ClientSession, url: str, headers: Dict[str, Any]) -> Dict[str, Any]:
        """Obter informações do arquivo via HEAD request."""
        try:
            async with session.head(url, headers=headers) as response:
                if response.status == 200:
                    return {
                        "content_length": int(response.headers.get("Content-Length", 0)),
                        "content_type": response.headers.get("Content-Type", "application/octet-stream"),
                        "accept_ranges": response.headers.get("Accept-Ranges", "bytes")
                    }
                else:
                    raise aiohttp.ClientError(f"HEAD request falhou: {response.status}")
        except Exception as e:
            logger.warning(f"⚠️ Erro ao obter informações do arquivo: {e}")
            return {"content_length": 0, "content_type": "application/octet-stream"}
    
    async def _download_chunks(
        self,
        session: aiohttp.ClientSession,
        url: str,
        headers: Dict[str, Any],
        chunks_needed: int
    ) -> AsyncGenerator[Tuple[bytes, int], None]:
        """Download de chunks em paralelo."""
        semaphore = asyncio.Semaphore(self.limits.max_concurrent_downloads)
        
        async def download_single_chunk(chunk_index: int) -> Tuple[bytes, int]:
            """Download de um chunk específico."""
            async with semaphore:
                start_byte = chunk_index * self.chunk_size
                end_byte = start_byte + self.chunk_size - 1
                
                # Headers para range request
                chunk_headers = headers.copy()
                chunk_headers["Range"] = f"bytes={start_byte}-{end_byte}"
                
                for attempt in range(self.retry_attempts):
                    try:
                        async with session.get(url, headers=chunk_headers) as response:
                            if response.status in [200, 206]:  # 206 = Partial Content
                                chunk_data = await response.read()
                                return chunk_data, chunk_index
                            else:
                                raise aiohttp.ClientError(f"Chunk {chunk_index} falhou: {response.status}")
                    except Exception as e:
                        if attempt < self.retry_attempts - 1:
                            await asyncio.sleep(0.5 * (2 ** attempt))  # Backoff exponencial
                            continue
                        else:
                            raise e
        
        # Criar tasks para todos os chunks
        tasks = [download_single_chunk(i) for i in range(chunks_needed)]
        
        # Executar downloads em paralelo
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Processar resultados
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"❌ Erro no chunk: {result}")
                raise result
            else:
                chunk_data, chunk_index = result
                yield chunk_data, chunk_index
    
    async def _reconstruct_file(self, chunks: List[Tuple[int, bytes]]) -> bytes:
        """Reconstruir arquivo a partir dos chunks."""
        # Ordenar chunks por índice
        chunks.sort(key=lambda x: x[0])
        
        # Concatenar chunks
        file_content = b"".join(chunk_data for _, chunk_data in chunks)
        
        # Verificar integridade básica
        if len(file_content) == 0:
            raise ValueError("Arquivo reconstruído está vazio")
        
        return file_content
    
    async def download_with_progress(
        self,
        document_url: str,
        document_name: str,
        headers: Dict[str, Any],
        process_number: str,
        document_id: str,
        progress_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """Download com callback de progresso."""
        logger.info(f"📦 Download com progresso: {document_name}")
        
        start_time = time.time()
        chunks = []
        total_size = 0
        chunk_count = 0
        
        try:
            async with aiohttp.ClientSession() as session:
                # Obter informações do arquivo
                file_info = await self._get_file_info(session, document_url, headers)
                total_size = file_info.get("content_length", 0)
                
                if total_size == 0:
                    raise ValueError("Não foi possível determinar o tamanho do arquivo")
                
                # Calcular chunks necessários
                chunks_needed = (total_size + self.chunk_size - 1) // self.chunk_size
                
                # Download sequencial com progresso
                for chunk_index in range(chunks_needed):
                    start_byte = chunk_index * self.chunk_size
                    end_byte = min(start_byte + self.chunk_size - 1, total_size - 1)
                    
                    # Headers para range request
                    chunk_headers = headers.copy()
                    chunk_headers["Range"] = f"bytes={start_byte}-{end_byte}"
                    
                    async with session.get(document_url, headers=chunk_headers) as response:
                        if response.status in [200, 206]:
                            chunk_data = await response.read()
                            chunks.append((chunk_index, chunk_data))
                            chunk_count += 1
                            
                            # Calcular progresso
                            progress = (chunk_count / chunks_needed) * 100
                            
                            # Callback de progresso
                            if progress_callback:
                                await progress_callback(progress, chunk_count, chunks_needed)
                            
                            logger.debug(f"📊 Progresso: {progress:.1f}% ({chunk_count}/{chunks_needed})")
                        else:
                            raise aiohttp.ClientError(f"Chunk {chunk_index} falhou: {response.status}")
                
                # Reconstruir arquivo
                file_content = await self._reconstruct_file(chunks)
                
                # Upload para S3
                s3_key = f"processos/{process_number}/documentos/{document_id}/{document_name}"
                await s3_service.upload_file(
                    file_content=file_content,
                    s3_key=s3_key,
                    content_type=file_info.get("content_type", "application/octet-stream")
                )
                
                # Gerar URL presignada
                download_url = await s3_service.generate_presigned_url(s3_key, expiration=3600)
                
                duration = time.time() - start_time
                record_download_metrics("success", duration)
                
                logger.info(f"✅ Download com progresso concluído: {document_name} ({total_size} bytes)")
                
                return {
                    "status": "success",
                    "filepath": s3_key,
                    "size": total_size,
                    "chunks": chunk_count,
                    "download_url": download_url,
                    "duration": duration,
                    "method": "chunked_with_progress"
                }
                
        except Exception as e:
            duration = time.time() - start_time
            record_download_metrics("error", duration)
            logger.error(f"❌ Erro no download com progresso: {e}")
            raise
    
    def should_use_chunked_download(self, file_size: int) -> bool:
        """Determinar se deve usar download em chunks."""
        # Usar chunks para arquivos maiores que 10MB
        return file_size > 10 * 1024 * 1024
    
    def get_optimal_chunk_size(self, file_size: int) -> int:
        """Obter tamanho ótimo de chunk baseado no tamanho do arquivo."""
        if file_size < 100 * 1024 * 1024:  # < 100MB
            return 1024 * 1024  # 1MB
        elif file_size < 500 * 1024 * 1024:  # < 500MB
            return 2 * 1024 * 1024  # 2MB
        else:  # >= 500MB
            return 5 * 1024 * 1024  # 5MB


# Instância global
chunked_download_service = ChunkedDownloadService()
