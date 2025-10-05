"""Cliente otimizado para integração com a API PDPJ com funcionalidades ultra-fast."""

import asyncio
import time
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import httpx
import aiohttp
from aiohttp import ClientSession, TCPConnector, ClientTimeout
from loguru import logger
try:
    from asyncio import timeout as asyncio_timeout
except ImportError:
    # Fallback para versões mais antigas do Python
    asyncio_timeout = None

from app.core.config import settings
from app.services.session_manager import get_active_session_cookie
from app.utils.file_utils import process_document_download
from app.utils.token_validator import PDPJTokenValidator
from app.utils.http_headers import get_api_headers, get_download_headers
from app.utils.monitoring_integration import (
    record_request_metrics, 
    record_download_metrics, 
    record_error_metrics,
    update_client_metrics
)


class PDPJClientError(Exception):
    """Exceção customizada para erros da API PDPJ."""
    pass


class PDPJClient:
    """Cliente otimizado para a API PDPJ com funcionalidades ultra-fast e controle de concorrência."""
    
    def __init__(self):
        self.base_url = settings.pdpj_api_base_url.rstrip('/')
        # Converter SecretStr para string
        self.token = settings.pdpj_api_token.get_secret_value() if hasattr(settings.pdpj_api_token, 'get_secret_value') else str(settings.pdpj_api_token)
        
        # Configurações de timeout e retry (configuráveis via settings)
        self.timeout = getattr(settings, 'pdpj_request_timeout', 30.0)
        self.download_timeout = getattr(settings, 'pdpj_download_timeout', 60.0)
        self.max_retries = getattr(settings, 'pdpj_max_retries', 3)
        self.retry_delay = getattr(settings, 'pdpj_retry_delay', 1.0)
        
        # Configurações de conexão HTTP
        self.max_connections = getattr(settings, 'pdpj_max_connections', 10)
        self.max_keepalive = getattr(settings, 'pdpj_max_keepalive', 5)
        
        # Controle de concorrência
        self.max_concurrent_requests = getattr(settings, 'max_concurrent_requests', 10)
        self.max_concurrent_downloads = getattr(settings, 'max_concurrent_downloads', 5)
        
        # Cliente HTTP persistente para alta performance
        self._persistent_client: Optional[httpx.AsyncClient] = None
        self._client_lock = asyncio.Lock()
        
        # Semáforos para controle de concorrência (funcionalidades ultra-fast)
        self._request_semaphore = asyncio.Semaphore(self.max_concurrent_requests)
        self._download_semaphore = asyncio.Semaphore(self.max_concurrent_downloads)
        
        # Métricas de performance expandidas
        self._metrics = {
            "requests_made": 0,
            "downloads_successful": 0,
            "downloads_failed": 0,
            "total_request_time": 0.0,
            "total_download_time": 0.0,
            "http_errors": {
                "401": 0,  # Token inválido
                "404": 0,  # Processo não encontrado
                "429": 0,  # Rate limit
                "500": 0,  # Erro interno do servidor
                "timeout": 0,  # Timeouts
                "other": 0  # Outros erros HTTP
            },
            "session_cache_hits": 0,
            "session_cache_misses": 0,
            "concurrent_requests": 0,
            "max_concurrent_reached": 0,
            "last_error": None,
            "last_error_time": None
        }
        
        # Validar token na inicialização
        self._validate_token()
    
    def _validate_token(self):
        """Validar o token PDPJ usando o utilitário centralizado."""
        PDPJTokenValidator.validate_and_log(self.token, self.base_url)
    
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        use_semaphore: bool = True
    ) -> Dict[str, Any]:
        """Fazer requisição HTTP para a API PDPJ com controle de concorrência."""
        
        # Usar semáforo se solicitado
        if use_semaphore:
            async with self._request_semaphore:
                # Verificar concorrência atual
                current_concurrent = self._metrics['concurrent_requests']
                if current_concurrent >= self.max_concurrent_requests:
                    self._metrics['max_concurrent_reached'] += 1
                    logger.warning(f"⚠️ Limite de concorrência atingido: {current_concurrent}/{self.max_concurrent_requests}")
                    logger.warning(f"⚠️ Total de vezes que limite foi atingido: {self._metrics['max_concurrent_reached']}")
                
                return await self._execute_request(method, endpoint, params, data, headers)
        else:
            return await self._execute_request(method, endpoint, params, data, headers)
    
    async def _execute_request(
        self, 
        method: str, 
        endpoint: str, 
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        headers: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Executar requisição HTTP real."""
        
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        # Headers padrão usando configuração centralizada
        default_headers = get_api_headers(self.token, headers)
        
        # DEBUG: Log detalhado da requisição (apenas em modo debug)
        if getattr(settings, 'debug', False):
            logger.debug(f"🔍 DEBUG - Iniciando requisição {method} para {url}")
            logger.debug(f"🔍 DEBUG - Headers: {default_headers}")
            logger.debug(f"🔍 DEBUG - Token (primeiros 50 chars): {self.token[:50] if self.token else 'VAZIO'}...")
            logger.debug(f"🔍 DEBUG - Base URL: {self.base_url}")
            logger.debug(f"🔍 DEBUG - Endpoint: {endpoint}")
            logger.debug(f"🔍 DEBUG - Params: {params}")
            logger.debug(f"🔍 DEBUG - Data: {data}")
        
        # Usar cliente HTTP persistente para alta performance
        client = await self._get_persistent_client()
        
        # Iniciar medição de tempo para métricas
        start_time = time.time()
        
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"Fazendo requisição {method} para {url} (tentativa {attempt + 1})")
                
                response = await client.request(
                    method=method,
                    url=url,
                    params=params,
                    json=data,
                    headers=default_headers
                )
                
                # DEBUG: Log detalhado da resposta (apenas em modo debug)
                if getattr(settings, 'debug', False):
                    logger.debug(f"🔍 DEBUG - Resposta recebida: Status {response.status_code}")
                    logger.debug(f"🔍 DEBUG - Headers da resposta: {dict(response.headers)}")
                
                # Verificar status da resposta e incrementar métricas
                if response.status_code == 200:
                    try:
                        result = response.json()
                        if getattr(settings, 'debug', False):
                            logger.debug(f"🔍 DEBUG - Resposta JSON: {str(result)[:200]}...")
                        
                        # Validação básica de schema
                        self._validate_response_schema(result, endpoint)
                        
                        # Registrar métricas de sucesso
                        duration = time.time() - start_time
                        record_request_metrics(method, endpoint, 200, duration)
                        
                        return result
                    except Exception as json_error:
                        logger.error(f"❌ Erro ao decodificar JSON da resposta: {json_error}")
                        logger.error(f"❌ Conteúdo da resposta: {response.text[:500]}...")
                        self._metrics['http_errors']['other'] += 1
                        duration = time.time() - start_time
                        record_error_metrics("json_decode_error", endpoint, str(json_error))
                        record_request_metrics(method, endpoint, 200, duration)  # Status 200 mas erro JSON
                        raise PDPJClientError(f"Resposta inválida da API: {json_error}")
                elif response.status_code == 404:
                    logger.warning(f"Processo não encontrado: {url}")
                    self._metrics['http_errors']['404'] += 1
                    duration = time.time() - start_time
                    record_error_metrics("not_found", endpoint, "Processo não encontrado")
                    record_request_metrics(method, endpoint, 404, duration)
                    raise PDPJClientError("Processo não encontrado")
                elif response.status_code == 401:
                    logger.error("Token PDPJ inválido ou expirado")
                    logger.error(f"🔍 DEBUG - Resposta de erro 401: {response.text}")
                    logger.error(f"🔍 DEBUG - Token usado: {self.token[:50]}...")
                    logger.error(f"🔍 DEBUG - Headers enviados: {default_headers}")
                    self._metrics['http_errors']['401'] += 1
                    duration = time.time() - start_time
                    record_error_metrics("unauthorized", endpoint, "Token inválido")
                    record_request_metrics(method, endpoint, 401, duration)
                    raise PDPJClientError("Token de autenticação inválido")
                elif response.status_code == 429:
                    logger.warning("Rate limit atingido na API PDPJ")
                    self._metrics['http_errors']['429'] += 1
                    duration = time.time() - start_time
                    record_error_metrics("rate_limit", endpoint, "Rate limit atingido")
                    record_request_metrics(method, endpoint, 429, duration)
                    # Implementar backoff adaptativo
                    await self._handle_rate_limit(attempt)
                    if attempt < self.max_retries - 1:
                        continue
                    raise PDPJClientError("Rate limit atingido")
                elif response.status_code >= 500:
                    logger.error(f"Erro do servidor HTTP {response.status_code}: {response.text}")
                    self._metrics['http_errors']['500'] += 1
                    duration = time.time() - start_time
                    record_error_metrics("server_error", endpoint, f"Erro {response.status_code}")
                    record_request_metrics(method, endpoint, response.status_code, duration)
                    response.raise_for_status()
                else:
                    logger.error(f"Erro HTTP {response.status_code}: {response.text}")
                    logger.error(f"🔍 DEBUG - Resposta completa: {response.text}")
                    self._metrics['http_errors']['other'] += 1
                    duration = time.time() - start_time
                    record_error_metrics("http_error", endpoint, f"Erro {response.status_code}")
                    record_request_metrics(method, endpoint, response.status_code, duration)
                    response.raise_for_status()
                    
            except httpx.TimeoutException:
                logger.warning(f"Timeout na requisição para {url} (tentativa {attempt + 1})")
                self._metrics['http_errors']['timeout'] += 1
                duration = time.time() - start_time
                record_error_metrics("timeout", endpoint, "Timeout na requisição")
                record_request_metrics(method, endpoint, 0, duration)  # Status 0 para timeout
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))
                    continue
                raise PDPJClientError("Timeout na requisição")
            
            except httpx.RequestError as e:
                logger.error(f"Erro de requisição para {url}: {e}")
                self._metrics['http_errors']['other'] += 1
                duration = time.time() - start_time
                record_error_metrics("request_error", endpoint, str(e))
                record_request_metrics(method, endpoint, 0, duration)  # Status 0 para erro de requisição
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))
                    continue
                raise PDPJClientError(f"Erro de requisição: {e}")
            
            raise PDPJClientError("Máximo de tentativas excedido")
    
    async def _handle_rate_limit(self, attempt: int) -> None:
        """Implementar backoff adaptativo para rate limiting."""
        # Calcular delay baseado no número de tentativas e erros 429
        base_delay = self.retry_delay
        exponential_delay = base_delay * (2 ** attempt)
        
        # Adicionar jitter para evitar thundering herd
        import random
        jitter = random.uniform(0.1, 0.5)
        final_delay = exponential_delay + jitter
        
        # Limitar delay máximo
        max_delay = 30.0
        final_delay = min(final_delay, max_delay)
        
        logger.warning(f"🔄 Rate limit detectado - aguardando {final_delay:.2f}s antes da tentativa {attempt + 1}")
        await asyncio.sleep(final_delay)
        
        # Implementar redução adaptativa de concorrência se muitos 429s
        recent_429s = self._metrics['http_errors']['429']
        if recent_429s > 5 and recent_429s % 5 == 0:  # A cada 5 erros 429
            old_limit = self.max_concurrent_requests
            self.max_concurrent_requests = max(1, int(self.max_concurrent_requests * 0.8))
            logger.warning(f"🔄 Reduzindo limite de concorrência de {old_limit} para {self.max_concurrent_requests} devido a rate limiting")
    
    def _validate_response_schema(self, response_data: Any, endpoint: str) -> None:
        """Validar schema básico das respostas da API."""
        try:
            # Validações específicas por endpoint
            if "processos" in endpoint:
                if isinstance(response_data, list):
                    # Lista de processos
                    for item in response_data[:3]:  # Validar apenas primeiros 3
                        if not isinstance(item, dict):
                            logger.debug(f"ℹ️ Item da lista não é dict: {type(item)}")
                            continue
                        # Verificar campos alternativos para número do processo
                        process_fields = ["numeroProcesso", "numero", "processo", "numero_processo"]
                        if not any(field in item for field in process_fields):
                            logger.debug(f"ℹ️ Campos de processo não encontrados em item da lista (campos disponíveis: {list(item.keys())[:5]})")
                elif isinstance(response_data, dict):
                    # Processo único
                    process_fields = ["numeroProcesso", "numero", "processo", "numero_processo"]
                    if not any(field in response_data for field in process_fields):
                        logger.debug(f"ℹ️ Campos de processo não encontrados na resposta (campos disponíveis: {list(response_data.keys())[:5]})")
            
            elif "documentos" in endpoint:
                if isinstance(response_data, list):
                    # Lista de documentos
                    for item in response_data[:3]:  # Validar apenas primeiros 3
                        if not isinstance(item, dict):
                            logger.warning(f"⚠️ Item da lista de documentos não é dict: {type(item)}")
                            continue
                        if "nome" not in item:
                            logger.warning(f"⚠️ Campo 'nome' ausente em documento")
            
            # Validação geral
            if response_data is None:
                logger.warning(f"⚠️ Resposta vazia (None) para endpoint: {endpoint}")
            elif isinstance(response_data, str) and len(response_data.strip()) == 0:
                logger.warning(f"⚠️ Resposta string vazia para endpoint: {endpoint}")
                
        except Exception as e:
            logger.warning(f"⚠️ Erro na validação de schema: {e}")
            # Não falhar a requisição por problemas de validação
    
    async def _get_persistent_client(self) -> httpx.AsyncClient:
        """Obter ou criar cliente HTTP persistente para alta performance."""
        async with self._client_lock:
            if self._persistent_client is None or self._persistent_client.is_closed:
                self._persistent_client = httpx.AsyncClient(
                    timeout=self.timeout,
                    limits=httpx.Limits(
                        max_connections=self.max_connections,
                        max_keepalive_connections=self.max_keepalive
                    ),
                    # Configurações adicionais para performance
                    http2=True,  # Suporte HTTP/2
                    follow_redirects=True,
                    verify=True
                )
                logger.debug("🔧 Cliente HTTP persistente criado")
            return self._persistent_client
    
    async def _close_persistent_client(self) -> None:
        """Fechar cliente HTTP persistente."""
        async with self._client_lock:
            if self._persistent_client and not self._persistent_client.is_closed:
                await self._persistent_client.aclose()
                self._persistent_client = None
                logger.debug("🔧 Cliente HTTP persistente fechado")
    
    async def __aenter__(self):
        """Context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - fechar cliente persistente."""
        await self._close_persistent_client()
    
    async def get_process_cover(self, process_number: str) -> Dict[str, Any]:
        """Obter dados da capa (resumo) do processo."""
        try:
            logger.info(f"Buscando capa do processo {process_number}")
            
            # Endpoint para buscar resumo via query parameter
            endpoint = f"processos?numeroProcesso={process_number}"
            
            response = await self._make_request("GET", endpoint)
            
            # Adicionar metadados
            response["_metadata"] = {
                "process_number": process_number,
                "data_type": "cover",
                "fetched_at": datetime.utcnow().isoformat(),
                "source": "pdpj_api"
            }
            
            logger.info(f"Capa do processo {process_number} obtida com sucesso")
            return response
            
        except Exception as e:
            logger.error(f"Erro ao buscar capa do processo {process_number}: {e}")
            raise PDPJClientError(f"Erro ao buscar capa: {e}")
    
    async def get_process_full(self, process_number: str) -> Dict[str, Any]:
        """Obter dados completos do processo (incluindo histórico e documentos)."""
        try:
            logger.info(f"Buscando dados completos do processo {process_number}")
            
            # Endpoint para buscar dados completos via path parameter
            endpoint = f"processos/{process_number}"
            
            response = await self._make_request("GET", endpoint)
            
            # A resposta pode ser uma lista com um item ou um dicionário
            if isinstance(response, list) and len(response) > 0:
                # Se for lista, pegar o primeiro item
                process_data = response[0]
            else:
                # Se for dicionário, usar diretamente
                process_data = response
            
            # Adicionar metadados
            process_data["_metadata"] = {
                "process_number": process_number,
                "data_type": "full",
                "fetched_at": datetime.utcnow().isoformat(),
                "source": "pdpj_api"
            }
            
            logger.info(f"Dados completos do processo {process_number} obtidos com sucesso")
            return process_data
            
        except Exception as e:
            logger.error(f"Erro ao buscar dados completos do processo {process_number}: {e}")
            raise PDPJClientError(f"Erro ao buscar dados completos: {e}")
    
    async def get_process_documents(self, process_number: str) -> List[Dict[str, Any]]:
        """Obter lista de documentos do processo."""
        try:
            logger.info(f"Buscando documentos do processo {process_number}")
            logger.info(f"🔍 DEBUG - Token atual: {self.token[:50] if self.token else 'VAZIO'}...")
            logger.info(f"🔍 DEBUG - Base URL: {self.base_url}")
            
            # Usar endpoint correto: dados completos do processo (inclui documentos)
            logger.info("🔧 Usando endpoint correto: /api/v2/processos/{numero}")
            full_data = await self.get_process_full(process_number)
            
            # Extrair documentos da tramitação atual (onde estão os documentos)
            documents = []
            tramitacao_atual = full_data.get("tramitacaoAtual", {})
            if tramitacao_atual:
                tram_docs = tramitacao_atual.get("documentos", [])
                documents.extend(tram_docs)
                logger.info(f"✅ Encontrados {len(documents)} documentos na tramitação atual")
            
            # Também verificar tramitações (se existirem)
            tramitacoes = full_data.get("tramitacoes", [])
            for tramitacao in tramitacoes:
                tram_docs = tramitacao.get("documentos", [])
                documents.extend(tram_docs)
            
            logger.info(f"✅ Total de {len(documents)} documentos encontrados")
            return documents
            
        except Exception as e:
            logger.error(f"Erro ao buscar documentos do processo {process_number}: {e}")
            raise PDPJClientError(f"Erro ao buscar documentos: {e}")
    
    async def download_document(
        self, 
        href_binario: str, 
        document_name: str = None, 
        session_cookie: str = None,
        timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """Baixar um documento específico via portal web PDPJ com headers do navegador e validação."""
        try:
            logger.info(f"🌐 Baixando documento via portal web: {href_binario}")
            
            # Usar timeout configurável
            download_timeout = timeout or self.download_timeout
            
            # Construir URL completa do documento
            if href_binario.startswith('/'):
                document_url = f"{self.base_url}{href_binario}"
            else:
                document_url = f"{self.base_url}/{href_binario}"
            
            logger.debug(f"🔧 URL completa do documento: {document_url}")
            
            # Obter cookie de sessão se não fornecido
            if not session_cookie:
                session_cookie = await get_active_session_cookie(self.base_url, self.token)
            
            # Headers do navegador usando configuração centralizada
            process_number = self._extract_process_number_from_href(href_binario)
            headers = get_download_headers(self.token, session_cookie, process_number)
            
            if session_cookie:
                logger.debug(f"🍪 Usando cookie de sessão: {session_cookie[:20]}...")
            
            # Usar timeout explícito (compatível com versões do Python)
            if asyncio_timeout:
                async with asyncio_timeout(download_timeout):
                    async with httpx.AsyncClient(timeout=download_timeout) as client:
                        return await self._execute_download(client, document_url, headers, document_name)
            else:
                # Fallback para versões sem asyncio.timeout
                async with httpx.AsyncClient(timeout=download_timeout) as client:
                    return await self._execute_download(client, document_url, headers, document_name)
                    
        except Exception as e:
            logger.error(f"❌ Erro no download do documento: {e}")
            raise PDPJClientError(f"Erro no download: {e}")
    
    async def _execute_download(self, client: httpx.AsyncClient, document_url: str, headers: Dict, document_name: str) -> Dict[str, Any]:
        """Executar download do documento."""
        try:
            response = await client.get(document_url, headers=headers)
            
            logger.info(f"📊 Status: {response.status_code}")
            logger.info(f"📊 Content-Type: {response.headers.get('content-type', 'N/A')}")
            logger.info(f"📊 Content-Length: {response.headers.get('content-length', 'N/A')}")
            
            if response.status_code == 200:
                content = response.content
                content_type = response.headers.get('content-type', '')
                
                # Processar download com validação
                result = process_document_download(
                    content=content,
                    original_name=document_name or "documento",
                    content_type=content_type,
                    directory="data/downloads"
                )
                
                # Adicionar informações da requisição
                result.update({
                    'url': document_url,
                    'status_code': response.status_code,
                    'content_type': content_type,
                    'session_cookie_used': 'session_cookie' in headers.get('cookie', ''),
                    'download_timestamp': datetime.utcnow().isoformat()
                })
                
                logger.info(f"✅ Download processado: {result['size']} bytes, tipo: {result['extension']}")
                return result
            else:
                logger.error(f"❌ Erro no download: {response.status_code}")
                raise PDPJClientError(f"Erro ao baixar documento: HTTP {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Erro ao baixar documento: {e}")
            raise PDPJClientError(f"Erro ao baixar documento: {e}")
    
    async def batch_download_documents(
        self, 
        document_requests: List[Dict[str, Any]]  # Lista de dicts com hrefBinario e document_name
    ) -> List[Dict[str, Any]]:
        """Baixar múltiplos documentos em paralelo com controle de concorrência otimizado."""
        try:
            logger.info(f"🚀 Iniciando download em lote de {len(document_requests)} documentos")
            
            # Criar tasks para download paralelo
            tasks = []
            for i, doc_request in enumerate(document_requests):
                href_binario = doc_request.get('hrefBinario', '')
                document_name = doc_request.get('document_name', f'documento_{i+1}')
                session_cookie = doc_request.get('session_cookie')
                
                # Criar task com wrapper para capturar erros
                task = self._download_document_with_error_handling(
                    href_binario, document_name, session_cookie, doc_request
                )
                tasks.append(task)
            
            # Executar downloads em paralelo com asyncio.gather
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Processar resultados
            processed_results = []
            for result in results:
                if isinstance(result, Exception):
                    error_result = {
                        'success': False,
                        'error': str(result),
                        'original_request': getattr(result, 'original_request', {})
                    }
                    processed_results.append(error_result)
                    self._metrics['downloads_failed'] += 1
                else:
                    processed_results.append(result)
                    self._metrics['downloads_successful'] += 1
            
            logger.info(f"✅ Download em lote concluído: {len(processed_results)} resultados")
            return processed_results
            
        except Exception as e:
            logger.error(f"❌ Erro no download em lote: {e}")
            raise PDPJClientError(f"Erro no download em lote: {e}")
    
    async def _download_document_with_error_handling(
        self, 
        href_binario: str, 
        document_name: str, 
        session_cookie: str, 
        original_request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Wrapper para download de documento com tratamento de erro."""
        try:
            result = await self.download_document(href_binario, document_name, session_cookie)
            result['original_request'] = original_request
            return result
        except Exception as e:
            # Adicionar informação do request original ao erro
            error = PDPJClientError(f"Erro ao baixar documento: {e}")
            error.original_request = original_request
            raise error
    
    def get_metrics(self) -> Dict[str, Any]:
        """Obter métricas de performance do cliente com análise crítica."""
        total_downloads = self._metrics['downloads_successful'] + self._metrics['downloads_failed']
        total_errors = sum(self._metrics['http_errors'].values())
        
        # Calcular métricas derivadas
        metrics = {
            **self._metrics,
            "avg_request_time": self._metrics['total_request_time'] / max(1, self._metrics['requests_made']),
            "avg_download_time": self._metrics['total_download_time'] / max(1, self._metrics['downloads_successful']),
            "success_rate": self._metrics['downloads_successful'] / max(1, total_downloads),
            "error_rate": total_errors / max(1, self._metrics['requests_made']),
            "session_cache_hit_rate": self._metrics['session_cache_hits'] / max(1, self._metrics['session_cache_hits'] + self._metrics['session_cache_misses']),
            "concurrent_utilization": self._metrics['concurrent_requests'] / self.max_concurrent_requests,
            "health_status": self._get_health_status(),
            "alerts": self._get_alerts()
        }
        
        # Atualizar métricas de monitoramento externo
        update_client_metrics(metrics)
        
        return metrics
    
    def _get_health_status(self) -> str:
        """Determinar status de saúde do cliente."""
        error_rate = self._metrics['http_errors']['401'] + self._metrics['http_errors']['500']
        total_requests = self._metrics['requests_made']
        
        if total_requests == 0:
            return "unknown"
        elif error_rate / total_requests > 0.1:  # Mais de 10% de erros críticos
            return "critical"
        elif error_rate / total_requests > 0.05:  # Mais de 5% de erros críticos
            return "warning"
        else:
            return "healthy"
    
    def _get_alerts(self) -> List[str]:
        """Obter alertas críticos baseados nas métricas."""
        alerts = []
        
        # Verificar taxa de erro alta
        total_requests = self._metrics['requests_made']
        if total_requests > 10:
            error_rate = sum(self._metrics['http_errors'].values()) / total_requests
            if error_rate > 0.2:  # Mais de 20% de erros
                alerts.append(f"ALTA_TAXA_ERRO: {error_rate*100:.1f}% de requisições falharam")
        
        # Verificar muitos erros 401 (token)
        if self._metrics['http_errors']['401'] > 5:
            alerts.append(f"TOKEN_PROBLEMAS: {self._metrics['http_errors']['401']} erros 401 detectados")
        
        # Verificar muitos timeouts
        if self._metrics['http_errors']['timeout'] > 3:
            alerts.append(f"TIMEOUTS_FREQUENTES: {self._metrics['http_errors']['timeout']} timeouts detectados")
        
        # Verificar utilização alta de concorrência
        if self._metrics['max_concurrent_reached'] > 0:
            alerts.append(f"CONCORRENCIA_LIMITE: {self._metrics['max_concurrent_reached']} vezes limite atingido")
        
        # Verificar cache de sessão baixo
        total_sessions = self._metrics['session_cache_hits'] + self._metrics['session_cache_misses']
        if total_sessions > 10:
            cache_hit_rate = self._metrics['session_cache_hits'] / total_sessions
            if cache_hit_rate < 0.5:  # Menos de 50% de hit rate
                alerts.append(f"CACHE_SESSAO_BAIXO: {cache_hit_rate*100:.1f}% de hit rate")
        
        return alerts
    
    def _extract_process_number_from_href(self, href_binario: str) -> str:
        """Extrair número do processo do hrefBinario."""
        try:
            # hrefBinario: /processos/1000145-91.2023.8.26.0597/documentos/.../binario
            parts = href_binario.split('/')
            if len(parts) >= 3 and parts[1] == 'processos':
                return parts[2]
            return None
        except Exception:
            return None
    
    async def batch_get_processes(
        self, 
        process_numbers: List[str],
        include_documents: bool = False
    ) -> Dict[str, Any]:
        """Obter múltiplos processos em lote."""
        try:
            logger.info(f"Buscando {len(process_numbers)} processos em lote")
            
            # TODO: Ajustar endpoint conforme documentação real da API PDPJ
            endpoint = "processos/batch"
            
            data = {
                "process_numbers": process_numbers,
                "include_documents": include_documents,
                "data_type": "full"
            }
            
            response = await self._make_request("POST", endpoint, data=data)
            
            logger.info(f"Busca em lote concluída: {len(process_numbers)} processos solicitados")
            return response
            
        except Exception as e:
            logger.error(f"Erro na busca em lote: {e}")
            raise PDPJClientError(f"Erro na busca em lote: {e}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Verificar saúde da API PDPJ."""
        try:
            endpoint = "health"  # TODO: Ajustar conforme API real
            response = await self._make_request("GET", endpoint)
            
            return {
                "status": "healthy",
                "api_version": response.get("version", "unknown"),
                "checked_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Health check da API PDPJ falhou: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "checked_at": datetime.utcnow().isoformat()
            }


# Instância global do cliente PDPJ (agora com funcionalidades ultra-fast)
pdpj_client = PDPJClient()

# Alias para compatibilidade com código existente
ultra_fast_pdpj_client = pdpj_client
