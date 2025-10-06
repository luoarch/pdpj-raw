"""Serviço para integração com AWS S3."""

import uuid
import asyncio
import re
import os
import time
import random
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import aioboto3
from botocore.exceptions import ClientError
from loguru import logger

from app.core.config import settings


class S3ServiceError(Exception):
    """Exceção customizada para erros do S3."""
    pass


class S3Service:
    """
    Serviço para operações com AWS S3 em ambiente assíncrono.
    
    Este serviço fornece uma interface completa para interagir com AWS S3,
    incluindo upload, download, listagem, metadados e health checks.
    
    Exemplos de uso:
    
    ```python
    # Upload de documento
    s3_service = S3Service()
    result = await s3_service.upload_document(
        file_content=b"conteudo do arquivo",
        process_number="1234567-89.2023.4.03.0001",
        filename="documento.pdf",
        content_type="application/pdf"
    )
    
    # Download de documento
    content = await s3_service.download_document("processes/1234567-89.2023.4.03.0001/documents/uuid/documento.pdf")
    
    # Listar documentos de um processo
    documents = await s3_service.list_process_documents("1234567-89.2023.4.03.0001")
    
    # Verificar se bucket existe
    exists = await s3_service.bucket_exists()
    
    # Health check
    health = await s3_service.health_check()
    ```
    
    Características:
    - Sanitização automática de nomes de arquivos
    - Timeouts configuráveis para operações
    - Formatação consistente de datetimes
    - Tratamento robusto de erros AWS
    - Logging detalhado para monitoramento
    """
    
    def __init__(self):
        self.bucket_name = settings.s3_bucket_name
        self.region = settings.aws_region
        
        # CORREÇÃO: Extrair valores corretos do SecretStr
        self.access_key_id = settings.aws_access_key_id.get_secret_value() if hasattr(settings.aws_access_key_id, 'get_secret_value') else str(settings.aws_access_key_id)
        self.secret_access_key = settings.aws_secret_access_key.get_secret_value() if hasattr(settings.aws_secret_access_key, 'get_secret_value') else str(settings.aws_secret_access_key)
        
        # Configurar sessão boto3 com timeout
        self.session = aioboto3.Session(
            aws_access_key_id=self.access_key_id,
            aws_secret_access_key=self.secret_access_key,
            region_name=self.region
        )
        
        # Configurações de timeout
        self.operation_timeout = 30  # segundos
        self.upload_timeout = 300    # 5 minutos para uploads grandes
        self.download_timeout = 180  # 3 minutos para downloads
        
        # Pool de conexões para processamento massivo (configurável)
        self.pool_size = getattr(settings, 's3_pool_size', 10)
        self._client_pool = asyncio.Queue(maxsize=self.pool_size)
        self._pool_initialized = False
        self._pool_lock = asyncio.Lock()
        
        # Configurações de concorrência (configuráveis)
        self.max_concurrent_operations = getattr(settings, 's3_max_concurrent', 50)
        self._operation_semaphore = asyncio.BoundedSemaphore(self.max_concurrent_operations)
        
        # Configurações de retry (configuráveis)
        self.max_retries = getattr(settings, 's3_max_retries', 3)
        self.base_delay = getattr(settings, 's3_base_delay', 1.0)  # segundos
        self.max_delay = getattr(settings, 's3_max_delay', 60.0)  # segundos
        
        # Configurações de monitoramento
        self.enable_metrics = getattr(settings, 's3_enable_metrics', True)
        self.metrics_retention = getattr(settings, 's3_metrics_retention', 3600)  # 1 hora
        
        # Métricas avançadas
        self._metrics = {
            'total_operations': 0,
            'successful_operations': 0,
            'failed_operations': 0,
            'retry_operations': 0,
            'average_latency': 0.0,
            'active_connections': 0,
            'throughput_per_second': 0.0,
            'error_rate': 0.0,
            'last_reset': time.time()
        }
        
        # Histórico de métricas para análise
        self._metrics_history = []
        self._max_history_size = 1000
    
    async def _initialize_pool(self):
        """Inicializar pool de conexões S3."""
        if self._pool_initialized:
            return
            
        async with self._pool_lock:
            if self._pool_initialized:
                return
                
            # Criar conexões para o pool
            for _ in range(self.pool_size):
                # Criar cliente real do S3
                client = await self.session.client('s3').__aenter__()
                await self._client_pool.put(client)
            
            self._pool_initialized = True
            logger.info(f"Pool de conexões S3 inicializado com {self.pool_size} conexões")
    
    async def _get_client_from_pool(self):
        """Obter cliente do pool de conexões."""
        await self._initialize_pool()
        return await self._client_pool.get()
    
    async def _return_client_to_pool(self, client):
        """Retornar cliente ao pool."""
        await self._client_pool.put(client)
    
    async def _with_pooled_client(self, operation, timeout: Optional[int] = None):
        """Executar operação com cliente do pool."""
        timeout = timeout or self.operation_timeout
        
        # Para operações simples, usar cliente direto
        async with self.session.client('s3') as s3:
            return await asyncio.wait_for(operation(s3), timeout=timeout)
    
    async def _get_client(self):
        """Obter cliente S3 com contexto async adequado."""
        # Criar cliente por operação para garantir contexto async correto
        return self.session.client('s3')
    
    async def _with_client(self, operation, timeout: Optional[int] = None):
        """Executar operação com cliente S3 em contexto async."""
        timeout = timeout or self.operation_timeout
        
        async with self.session.client('s3') as s3:
            return await asyncio.wait_for(operation(s3), timeout=timeout)
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitizar nome de arquivo para S3."""
        # Remover caracteres especiais e substituir espaços
        sanitized = re.sub(r'[<>:"|?*\x00-\x1f]', '_', filename)
        sanitized = re.sub(r'\s+', '_', sanitized)  # Substituir espaços por underscore
        sanitized = re.sub(r'_{2,}', '_', sanitized)  # Remover underscores duplos
        sanitized = sanitized.strip('_')  # Remover underscores do início/fim
        
        # Limitar tamanho
        if len(sanitized) > 200:
            name, ext = os.path.splitext(sanitized)
            sanitized = name[:200-len(ext)] + ext
        
        return sanitized or "unnamed_file"
    
    def _format_datetime(self, dt: datetime) -> str:
        """Formatar datetime para string ISO."""
        return dt.isoformat() if dt else None
    
    async def _retry_with_backoff(self, operation, *args, **kwargs):
        """Executar operação com retry e backoff exponencial."""
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                start_time = time.time()
                result = await operation(*args, **kwargs)
                
                # Atualizar métricas
                latency = time.time() - start_time
                self._update_metrics(success=True, latency=latency)
                
                return result
                
            except (ClientError, asyncio.TimeoutError, Exception) as e:
                last_exception = e
                
                if attempt < self.max_retries:
                    # Calcular delay com backoff exponencial e jitter
                    delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                    jitter = random.uniform(0, delay * 0.1)  # 10% de jitter
                    total_delay = delay + jitter
                    
                    self._metrics['retry_operations'] += 1
                    logger.warning(f"Tentativa {attempt + 1} falhou, tentando novamente em {total_delay:.2f}s: {e}")
                    await asyncio.sleep(total_delay)
                else:
                    self._update_metrics(success=False, latency=0)
                    logger.error(f"Todas as tentativas falharam: {e}")
                    raise
        
        raise last_exception
    
    def _update_metrics(self, success: bool, latency: float):
        """Atualizar métricas do serviço."""
        if not self.enable_metrics:
            return
            
        current_time = time.time()
        
        # Atualizar contadores básicos
        self._metrics['total_operations'] += 1
        if success:
            self._metrics['successful_operations'] += 1
        else:
            self._metrics['failed_operations'] += 1
        
        # Calcular latência média
        total_ops = self._metrics['total_operations']
        if total_ops > 0:
            self._metrics['average_latency'] = (
                (self._metrics['average_latency'] * (total_ops - 1) + latency) / total_ops
            )
        
        # Calcular throughput (operações por segundo)
        time_elapsed = current_time - self._metrics['last_reset']
        if time_elapsed > 0:
            self._metrics['throughput_per_second'] = total_ops / time_elapsed
        
        # Calcular taxa de erro
        if total_ops > 0:
            self._metrics['error_rate'] = self._metrics['failed_operations'] / total_ops
        
        # Adicionar ao histórico
        self._metrics_history.append({
            'timestamp': current_time,
            'success': success,
            'latency': latency,
            'total_operations': total_ops,
            'error_rate': self._metrics['error_rate']
        })
        
        # Limitar tamanho do histórico
        if len(self._metrics_history) > self._max_history_size:
            self._metrics_history = self._metrics_history[-self._max_history_size:]
    
    async def batch_upload_documents(
        self, 
        documents: List[Dict[str, Any]], 
        max_concurrent: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Upload em batch de múltiplos documentos com controle de concorrência.
        
        Args:
            documents: Lista de dicionários com 'file_content', 'process_number', 'filename', etc.
            max_concurrent: Número máximo de uploads simultâneos
            
        Returns:
            Lista de resultados dos uploads
        """
        max_concurrent = max_concurrent or min(10, len(documents))
        semaphore = asyncio.BoundedSemaphore(max_concurrent)
        
        async def upload_single_doc(doc_data):
            async with semaphore:
                return await self.upload_document(**doc_data)
        
        # Executar uploads em paralelo
        tasks = [upload_single_doc(doc) for doc in documents]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Processar resultados
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    'index': i,
                    'success': False,
                    'error': str(result),
                    'document': documents[i]
                })
            else:
                processed_results.append({
                    'index': i,
                    'success': True,
                    'result': result,
                    'document': documents[i]
                })
        
        return processed_results
    
    async def batch_download_documents(
        self, 
        s3_keys: List[str], 
        max_concurrent: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Download em batch de múltiplos documentos com controle de concorrência.
        
        Args:
            s3_keys: Lista de chaves S3 para download
            max_concurrent: Número máximo de downloads simultâneos
            
        Returns:
            Lista de resultados dos downloads
        """
        max_concurrent = max_concurrent or min(10, len(s3_keys))
        semaphore = asyncio.BoundedSemaphore(max_concurrent)
        
        async def download_single_doc(s3_key):
            async with semaphore:
                return await self.download_document(s3_key)
        
        # Executar downloads em paralelo
        tasks = [download_single_doc(key) for key in s3_keys]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Processar resultados
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    'index': i,
                    'success': False,
                    'error': str(result),
                    's3_key': s3_keys[i]
                })
            else:
                processed_results.append({
                    'index': i,
                    'success': True,
                    'content': result,
                    's3_key': s3_keys[i],
                    'size': len(result)
                })
        
        return processed_results
    
    def get_metrics(self) -> Dict[str, Any]:
        """Obter métricas de performance do serviço."""
        current_time = time.time()
        
        return {
            **self._metrics,
            'pool_size': self._client_pool.qsize(),
            'pool_initialized': self._pool_initialized,
            'max_concurrent_operations': self.max_concurrent_operations,
            'pool_config_size': self.pool_size,
            'uptime_seconds': current_time - self._metrics['last_reset'],
            'history_size': len(self._metrics_history),
            'success_rate': 1.0 - self._metrics['error_rate'] if self._metrics['total_operations'] > 0 else 0.0
        }
    
    def get_metrics_history(self, last_n: Optional[int] = None) -> List[Dict[str, Any]]:
        """Obter histórico de métricas."""
        if last_n:
            return self._metrics_history[-last_n:]
        return self._metrics_history.copy()
    
    def reset_metrics(self):
        """Resetar métricas do serviço."""
        self._metrics = {
            'total_operations': 0,
            'successful_operations': 0,
            'failed_operations': 0,
            'retry_operations': 0,
            'average_latency': 0.0,
            'active_connections': 0,
            'throughput_per_second': 0.0,
            'error_rate': 0.0,
            'last_reset': time.time()
        }
        self._metrics_history.clear()
        logger.info("Métricas do S3Service resetadas")
    
    def _validate_s3_key_components(self, process_number: str, document_id: str, filename: str):
        """Validar componentes da chave S3."""
        # Caracteres inválidos para S3 keys
        invalid_chars = r'[<>:"|?*\x00-\x1f]'
        
        if re.search(invalid_chars, process_number):
            raise S3ServiceError(f"process_number contém caracteres inválidos: {process_number}")
        if re.search(invalid_chars, document_id):
            raise S3ServiceError(f"document_id contém caracteres inválidos: {document_id}")
        if re.search(invalid_chars, filename):
            raise S3ServiceError(f"filename contém caracteres inválidos: {filename}")
        
        # Verificar tamanho máximo (1024 caracteres para S3 key)
        if len(process_number) > 200:
            raise S3ServiceError("process_number muito longo (máximo 200 caracteres)")
        if len(document_id) > 200:
            raise S3ServiceError("document_id muito longo (máximo 200 caracteres)")
        if len(filename) > 200:
            raise S3ServiceError("filename muito longo (máximo 200 caracteres)")
    
    def _generate_s3_key(self, process_number: str, document_id: str, filename: str) -> str:
        """Gerar chave única para o S3."""
        # Formato: processes/{process_number}/documents/{document_id}/{filename}
        return f"processes/{process_number}/documents/{document_id}/{filename}"
    
    def _generate_document_id(self) -> str:
        """Gerar ID único para documento."""
        return str(uuid.uuid4())
    
    async def bucket_exists(self, bucket_name: Optional[str] = None) -> bool:
        """Verificar se o bucket existe."""
        bucket_name = bucket_name or self.bucket_name
        
        try:
            async def check_bucket(s3):
                await s3.head_bucket(Bucket=bucket_name)
                return True
            
            return await self._retry_with_backoff(self._with_pooled_client, check_bucket)
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                return False
            else:
                logger.error(f"Erro ao verificar bucket {bucket_name}: {e}")
                raise S3ServiceError(f"Erro ao verificar bucket: {e}")
        except Exception as e:
            logger.error(f"Erro inesperado ao verificar bucket {bucket_name}: {e}")
            raise S3ServiceError(f"Erro inesperado: {e}")
    
    async def upload_document(
        self,
        file_content: bytes,
        process_number: str,
        document_id: Optional[str] = None,
        filename: Optional[str] = None,
        content_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Fazer upload de documento para S3."""
        
        try:
            if not document_id:
                document_id = self._generate_document_id()
            
            if not filename:
                filename = f"document_{document_id}"
            
            # Sanitizar nome do arquivo
            filename = self._sanitize_filename(filename)
            
            if not content_type:
                content_type = "application/octet-stream"
            
            # Validar componentes da chave S3
            self._validate_s3_key_components(process_number, document_id, filename)
            
            s3_key = self._generate_s3_key(process_number, document_id, filename)
            
            logger.info(f"Fazendo upload para S3: {s3_key}")
            
            async def upload_operation(s3):
                await s3.put_object(
                    Bucket=self.bucket_name,
                    Key=s3_key,
                    Body=file_content,
                    ContentType=content_type,
                    Metadata={
                        'process_number': process_number,
                        'document_id': document_id,
                        'uploaded_at': datetime.utcnow().isoformat(),
                        'file_size': str(len(file_content))
                    }
                )
            
            await self._retry_with_backoff(
                self._with_pooled_client, 
                upload_operation, 
                timeout=self.upload_timeout
            )
            
            logger.info(f"Upload concluído: {s3_key} ({len(file_content)} bytes)")
            
            return {
                "s3_key": s3_key,
                "document_id": document_id,
                "bucket": self.bucket_name,
                "file_size": len(file_content),
                "content_type": content_type,
                "uploaded_at": datetime.utcnow().isoformat()
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            logger.error(f"Erro do AWS S3 ({error_code}): {e}")
            raise S3ServiceError(f"Erro do AWS S3: {e}")
        
        except Exception as e:
            logger.error(f"Erro inesperado no upload S3: {e}")
            raise S3ServiceError(f"Erro no upload: {e}")
    
    async def generate_presigned_url(
        self,
        s3_key: str,
        expiration: int = 3600,
        http_method: str = "GET"
    ) -> str:
        """Gerar URL presignada para download."""
        
        try:
            logger.info(f"Gerando URL presignada para: {s3_key}")
            
            async with self.session.client('s3') as s3:
                url = await s3.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': self.bucket_name, 'Key': s3_key},
                    ExpiresIn=expiration
                )
            
            logger.info(f"URL presignada gerada: {s3_key}")
            return url
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            logger.error(f"Erro ao gerar URL presignada ({error_code}): {e}")
            raise S3ServiceError(f"Erro ao gerar URL presignada: {e}")
        
        except Exception as e:
            logger.error(f"Erro inesperado ao gerar URL presignada: {e}")
            raise S3ServiceError(f"Erro ao gerar URL: {e}")
    
    async def download_document(self, s3_key: str) -> bytes:
        """Baixar documento do S3."""
        
        try:
            logger.info(f"Baixando documento do S3: {s3_key}")
            
            async with self.session.client('s3') as s3:
                response = await s3.get_object(
                    Bucket=self.bucket_name,
                    Key=s3_key
                )
                
                content = await response['Body'].read()
            
            logger.info(f"Download concluído: {s3_key} ({len(content)} bytes)")
            return content
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchKey':
                raise S3ServiceError(f"Documento não encontrado: {s3_key}")
            logger.error(f"Erro do AWS S3 ({error_code}): {e}")
            raise S3ServiceError(f"Erro do AWS S3: {e}")
        
        except Exception as e:
            logger.error(f"Erro inesperado no download S3: {e}")
            raise S3ServiceError(f"Erro no download: {e}")
    
    async def delete_document(self, s3_key: str) -> bool:
        """Deletar documento do S3."""
        
        try:
            logger.info(f"Deletando documento do S3: {s3_key}")
            
            async with self.session.client('s3') as s3:
                await s3.delete_object(
                    Bucket=self.bucket_name,
                    Key=s3_key
                )
            
            logger.info(f"Documento deletado: {s3_key}")
            return True
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            logger.error(f"Erro do AWS S3 ({error_code}): {e}")
            return False
        
        except Exception as e:
            logger.error(f"Erro inesperado ao deletar do S3: {e}")
            return False
    
    async def document_exists(self, s3_key: str) -> bool:
        """Verificar se documento existe no S3."""
        
        try:
            async with self.session.client('s3') as s3:
                await s3.head_object(
                    Bucket=self.bucket_name,
                    Key=s3_key
                )
            return True
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                return False
            logger.error(f"Erro do AWS S3 ({error_code}): {e}")
            return False
        
        except Exception as e:
            logger.error(f"Erro inesperado ao verificar documento: {e}")
            return False
    
    async def get_document_metadata(self, s3_key: str) -> Optional[Dict[str, Any]]:
        """Obter metadados do documento."""
        
        try:
            async with self.session.client('s3') as s3:
                response = await s3.head_object(
                    Bucket=self.bucket_name,
                    Key=s3_key
                )
                
                metadata = {
                    "content_type": response.get('ContentType'),
                    "content_length": response.get('ContentLength'),
                    "last_modified": self._format_datetime(response.get('LastModified')),
                    "etag": response.get('ETag'),
                    "metadata": response.get('Metadata', {})
                }
                
                return metadata
                
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                return None
            logger.error(f"Erro do AWS S3 ({error_code}): {e}")
            return None
        
        except Exception as e:
            logger.error(f"Erro inesperado ao obter metadados: {e}")
            return None
    
    async def list_process_documents(self, process_number: str) -> list[Dict[str, Any]]:
        """Listar documentos de um processo."""
        
        try:
            prefix = f"processes/{process_number}/documents/"
            documents = []
            
            async with self.session.client('s3') as s3:
                paginator = s3.get_paginator('list_objects_v2')
                
                async for page in paginator.paginate(Bucket=self.bucket_name, Prefix=prefix):
                    if 'Contents' in page:
                        for obj in page['Contents']:
                            documents.append({
                                "s3_key": obj['Key'],
                                "size": obj['Size'],
                                "last_modified": self._format_datetime(obj['LastModified']),
                                "etag": obj['ETag']
                            })
            
            logger.info(f"Encontrados {len(documents)} documentos para processo {process_number}")
            return documents
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            logger.error(f"Erro do AWS S3 ({error_code}): {e}")
            return []
        
        except Exception as e:
            logger.error(f"Erro inesperado ao listar documentos: {e}")
            return []
    
    async def health_check(self) -> Dict[str, Any]:
        """Verificar saúde do serviço S3."""
        
        try:
            async with self.session.client('s3') as s3:
                # Tentar listar objetos do bucket
                await s3.head_bucket(Bucket=self.bucket_name)
                
                return {
                    "status": "healthy",
                    "bucket": self.bucket_name,
                    "region": self.region,
                    "checked_at": datetime.utcnow().isoformat()
                }
                
        except ClientError as e:
            error_code = e.response['Error']['Code']
            logger.error(f"Health check S3 falhou ({error_code}): {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "bucket": self.bucket_name,
                "checked_at": datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Health check S3 falhou: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "checked_at": datetime.utcnow().isoformat()
            }
    
    async def __aenter__(self):
        """Context manager entry."""
        await self._initialize_pool()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup do pool."""
        await self._cleanup_pool()
    
    async def _cleanup_pool(self):
        """Limpar pool de conexões."""
        if not self._pool_initialized:
            return
            
        async with self._pool_lock:
            if not self._pool_initialized:
                return
                
            # Fechar todas as conexões do pool
            while not self._client_pool.empty():
                try:
                    client = await asyncio.wait_for(self._client_pool.get(), timeout=1.0)
                    await client.close()
                except asyncio.TimeoutError:
                    break
                except Exception as e:
                    logger.warning(f"Erro ao fechar cliente do pool: {e}")
            
            self._pool_initialized = False
            logger.info("Pool de conexões S3 limpo")


# Instância global do serviço S3
s3_service = S3Service()
