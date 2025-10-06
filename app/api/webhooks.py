"""Endpoints para testes e gerenciamento de webhooks."""

from fastapi import APIRouter, Request, HTTPException, status
from pydantic import BaseModel, HttpUrl
from typing import Optional, Dict, Any
from loguru import logger
from datetime import datetime

from app.services.webhook_service import webhook_service

router = APIRouter(tags=["webhooks"])


class WebhookTestRequest(BaseModel):
    """Request para testar webhook."""
    webhook_url: str
    test_payload: Optional[Dict[str, Any]] = None


class WebhookValidationRequest(BaseModel):
    """Request para validar URL de webhook."""
    webhook_url: str


@router.post("/webhook-test-receiver")
async def webhook_test_receiver(request: Request):
    """
    Endpoint de teste para receber webhooks.
    Use este endpoint para testar se webhooks estão funcionando.
    """
    try:
        payload = await request.json()
        
        # Log detalhado do webhook recebido
        logger.info("=" * 60)
        logger.info("📥 WEBHOOK RECEBIDO")
        logger.info("=" * 60)
        logger.info(f"⏰ Timestamp: {datetime.utcnow().isoformat()}")
        logger.info(f"📊 Headers: {dict(request.headers)}")
        logger.info(f"📦 Payload keys: {list(payload.keys())}")
        
        if payload.get("test"):
            logger.info("🧪 Este é um webhook de TESTE")
        
        if payload.get("process_number"):
            logger.info(f"📁 Processo: {payload.get('process_number')}")
            logger.info(f"📊 Status: {payload.get('status')}")
            logger.info(f"📄 Documentos: {payload.get('total_documents')}")
            logger.info(f"✅ Completados: {payload.get('completed_documents')}")
            logger.info(f"❌ Falharam: {payload.get('failed_documents')}")
        
        logger.info("=" * 60)
        
        return {
            "received": True,
            "timestamp": datetime.utcnow().isoformat(),
            "payload_keys": list(payload.keys()),
            "message": "Webhook recebido com sucesso!",
            "test": payload.get("test", False),
            "process_number": payload.get("process_number"),
            "status": payload.get("status")
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao processar webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Erro ao processar webhook: {str(e)}"
        )


@router.post("/webhook-validate")
async def validate_webhook_url(request: WebhookValidationRequest):
    """
    Validar se uma URL de webhook é válida.
    
    Verifica:
    - Formato da URL
    - Protocolo (HTTP/HTTPS)
    - Domínio válido
    - Porta permitida
    """
    logger.info(f"🔍 Validando URL: {request.webhook_url}")
    
    is_valid, error = webhook_service.validate_webhook_url(request.webhook_url)
    
    if is_valid:
        return {
            "valid": True,
            "url": request.webhook_url,
            "message": "URL válida para webhook"
        }
    else:
        return {
            "valid": False,
            "url": request.webhook_url,
            "error": error,
            "message": "URL inválida para webhook"
        }


@router.post("/webhook-test-connectivity")
async def test_webhook_connectivity(request: WebhookTestRequest):
    """
    Testar conectividade com um webhook.
    
    Envia um payload de teste para verificar se o webhook está acessível.
    """
    logger.info(f"🧪 Testando conectividade com: {request.webhook_url}")
    
    # Validar URL primeiro
    is_valid, error = webhook_service.validate_webhook_url(request.webhook_url)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"URL inválida: {error}"
        )
    
    # Testar conectividade
    result = await webhook_service.test_webhook_connectivity(request.webhook_url)
    
    if result.get("reachable"):
        return {
            "success": True,
            "url": request.webhook_url,
            "status_code": result.get("status_code"),
            "response_time_ms": result.get("response_time_ms"),
            "message": "Webhook acessível e funcionando"
        }
    else:
        return {
            "success": False,
            "url": request.webhook_url,
            "error": result.get("error"),
            "message": "Webhook não está acessível"
        }


@router.post("/webhook-send-test")
async def send_test_webhook(request: WebhookTestRequest):
    """
    Enviar um webhook de teste com payload customizado.
    
    Use este endpoint para testar o envio de webhooks com retry automático.
    """
    logger.info(f"📤 Enviando webhook de teste para: {request.webhook_url}")
    
    # Validar URL
    is_valid, error = webhook_service.validate_webhook_url(request.webhook_url)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"URL inválida: {error}"
        )
    
    # Payload padrão ou customizado
    payload = request.test_payload or {
        "test": True,
        "message": "Webhook de teste da API PDPJ",
        "timestamp": datetime.utcnow().isoformat(),
        "process_number": "0000000-00.0000.0.00.0000",
        "status": "completed",
        "total_documents": 10,
        "completed_documents": 10,
        "failed_documents": 0
    }
    
    # Enviar webhook
    result = await webhook_service.send_webhook(request.webhook_url, payload)
    
    if result.get("success"):
        return {
            "success": True,
            "url": request.webhook_url,
            "status_code": result.get("status_code"),
            "attempts": result.get("attempt"),
            "message": "Webhook enviado com sucesso!"
        }
    else:
        return {
            "success": False,
            "url": request.webhook_url,
            "error": result.get("error"),
            "attempts": result.get("attempts"),
            "message": "Falha ao enviar webhook após todas as tentativas"
        }

