"""Serviço para envio de webhooks com retry automático."""

import asyncio
import httpx
from typing import Dict, Any, Optional
from loguru import logger
from datetime import datetime


class WebhookService:
    """Serviço para envio de webhooks com retry, validação e segurança."""
    
    def __init__(self):
        self.max_retries = 3
        self.timeout = 30.0
        self.retry_delay = 2.0  # segundos (com backoff exponencial)
        self.verify_ssl = True  # Validar certificados SSL (produção)
    
    async def send_webhook(
        self,
        webhook_url: str,
        payload: Dict[str, Any],
        max_retries: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Enviar webhook com retry automático.
        
        Args:
            webhook_url: URL do webhook
            payload: Dados a enviar
            max_retries: Número máximo de tentativas (padrão: 3)
            
        Returns:
            Dict com resultado: {"success": bool, "status_code": int, ...}
        """
        retries = max_retries or self.max_retries
        last_error = None
        
        for attempt in range(1, retries + 1):
            try:
                logger.info(f"📤 Enviando webhook (tentativa {attempt}/{retries}): {webhook_url}")
                
                # Configurar cliente com validação SSL
                async with httpx.AsyncClient(
                    timeout=self.timeout,
                    verify=self.verify_ssl  # Validar certificados SSL
                ) as client:
                    response = await client.post(
                        webhook_url,
                        json=payload,
                        headers={
                            "Content-Type": "application/json",
                            "User-Agent": "PDPJ-API-Webhook/1.0",
                            "X-Webhook-Timestamp": datetime.utcnow().isoformat(),
                            "X-Webhook-Attempt": str(attempt),
                            "X-Webhook-ID": payload.get("job_id", "unknown")
                        }
                    )
                    
                    # VALIDAÇÃO CRÍTICA: Sucesso apenas se status 2xx
                    if 200 <= response.status_code < 300:
                        logger.info(f"✅ Webhook enviado com sucesso: HTTP {response.status_code}")
                        logger.info(f"📊 Resposta do webhook: {response.text[:200]}")
                        return {
                            "success": True,
                            "status_code": response.status_code,
                            "response_body": response.text[:500],  # Primeiros 500 chars
                            "attempt": attempt,
                            "timestamp": datetime.utcnow().isoformat(),
                            "ssl_verified": self.verify_ssl
                        }
                    else:
                        # Status fora de 200-299 = FALHA
                        last_error = f"HTTP {response.status_code}: {response.text[:200]}"
                        logger.error(f"❌ Webhook retornou status de erro: {response.status_code}")
                        logger.error(f"📄 Resposta: {response.text[:200]}")
                        
            except httpx.TimeoutException:
                last_error = f"Timeout após {self.timeout}s"
                logger.warning(f"⏰ Timeout no webhook (tentativa {attempt})")
                
            except httpx.ConnectError as e:
                last_error = f"Erro de conexão: {str(e)}"
                logger.warning(f"🔌 Erro de conexão no webhook (tentativa {attempt}): {e}")
            
            except httpx.HTTPStatusError as e:
                last_error = f"HTTP Error {e.response.status_code}: {str(e)}"
                logger.error(f"❌ HTTP Status Error no webhook (tentativa {attempt}): {e}")
                
            except httpx.SSLError as e:
                last_error = f"Erro de certificado SSL: {str(e)}"
                logger.error(f"🔒 SSL Error no webhook (tentativa {attempt}): {e}")
                logger.error(f"⚠️ Verifique se o certificado do webhook é válido!")
                
            except Exception as e:
                last_error = str(e)
                logger.error(f"❌ Erro no webhook (tentativa {attempt}): {e}")
            
            # Aguardar antes de retry (exceto na última tentativa)
            # Backoff exponencial: 2s, 4s, 8s
            if attempt < retries:
                wait_time = self.retry_delay * (2 ** (attempt - 1))
                logger.info(f"⏳ Aguardando {wait_time}s antes de nova tentativa...")
                await asyncio.sleep(wait_time)
        
        # Todas as tentativas falharam
        logger.error(f"❌ Webhook falhou após {retries} tentativas: {last_error}")
        return {
            "success": False,
            "error": last_error,
            "attempts": retries,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def validate_webhook_url(self, url: str) -> tuple[bool, Optional[str]]:
        """
        Validar formato e segurança de URL do webhook.
        
        Args:
            url: URL a validar
            
        Returns:
            Tuple (is_valid, error_message)
        """
        if not url:
            return False, "URL não pode ser vazia"
        
        # Validação de protocolo
        if not url.startswith(('http://', 'https://')):
            return False, "URL deve usar protocolo HTTP ou HTTPS"
        
        # SEGURANÇA: Recomendar HTTPS (bloquear HTTP em produção)
        if url.startswith('http://'):
            if url.startswith('http://localhost') or url.startswith('http://127.0.0.1'):
                logger.info(f"ℹ️ Webhook local usando HTTP: {url}")
            else:
                # Em produção, poderia bloquear HTTP
                from app.core.config import settings
                if getattr(settings, 'environment', 'development') == 'production':
                    return False, "Webhook deve usar HTTPS em produção (HTTP não permitido)"
                else:
                    logger.warning(f"⚠️ Webhook usando HTTP (inseguro): {url}")
                    logger.warning(f"⚠️ Em produção, apenas HTTPS será permitido!")
        
        # Validações básicas de formato
        from urllib.parse import urlparse
        try:
            parsed = urlparse(url)
            
            if not parsed.netloc:
                return False, "URL inválida: domínio não encontrado"
            
            # Verificar portas suspeitas (opcional)
            if parsed.port and parsed.port in [22, 23, 3389]:
                return False, f"Porta {parsed.port} não permitida para webhook"
            
        except Exception as e:
            return False, f"Erro ao validar URL: {str(e)}"
        
        return True, None
    
    async def test_webhook_connectivity(self, webhook_url: str) -> Dict[str, Any]:
        """
        Testar conectividade com webhook (sem payload completo).
        
        Args:
            webhook_url: URL a testar
            
        Returns:
            Dict com resultado do teste
        """
        logger.info(f"🧪 Testando conectividade com webhook: {webhook_url}")
        
        # Validar URL primeiro
        is_valid, error = self.validate_webhook_url(webhook_url)
        if not is_valid:
            return {
                "reachable": False,
                "error": error,
                "validation_failed": True
            }
        
        # Enviar payload de teste
        test_payload = {
            "test": True,
            "message": "Teste de conectividade do webhook PDPJ",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    webhook_url,
                    json=test_payload,
                    headers={
                        "Content-Type": "application/json",
                        "User-Agent": "PDPJ-API-Webhook-Test/1.0"
                    }
                )
                
                return {
                    "reachable": True,
                    "status_code": response.status_code,
                    "response_time_ms": response.elapsed.total_seconds() * 1000,
                    "accepts_json": response.status_code < 500
                }
                
        except httpx.TimeoutException:
            return {
                "reachable": False,
                "error": "Timeout (10s)",
                "timeout": True
            }
        except Exception as e:
            return {
                "reachable": False,
                "error": str(e)
            }


# Instância global do serviço
webhook_service = WebhookService()

