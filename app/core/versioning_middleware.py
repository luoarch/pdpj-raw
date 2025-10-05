"""Middleware para versionamento dinâmico da API."""

from typing import Optional
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger

from app.core.config import settings


class VersioningMiddleware(BaseHTTPMiddleware):
    """
    Middleware para versionamento dinâmico da API.
    
    Permite versionamento via:
    - Header: X-API-Version
    - Query parameter: version
    - Path prefix: /api/v1, /api/v2, etc.
    """
    
    def __init__(self, app, enable_header_versioning: bool = True, enable_query_versioning: bool = True):
        super().__init__(app)
        self.enable_header_versioning = enable_header_versioning
        self.enable_query_versioning = enable_query_versioning
        
        # Versões suportadas
        self.supported_versions = ["v1", "v2"]
        self.default_version = "v1"
        
        logger.info(f"VersioningMiddleware inicializado - Versões suportadas: {self.supported_versions}")
    
    async def dispatch(self, request: Request, call_next):
        """Processar request com versionamento."""
        try:
            # Detectar versão solicitada
            requested_version = self._detect_version(request)
            
            # Validar versão
            if requested_version and requested_version not in self.supported_versions:
                return JSONResponse(
                    status_code=400,
                    content={
                        "error": "Versão não suportada",
                        "requested_version": requested_version,
                        "supported_versions": self.supported_versions,
                        "default_version": self.default_version
                    }
                )
            
            # Adicionar informações de versão ao request
            request.state.api_version = requested_version or self.default_version
            request.state.version_source = self._get_version_source(request)
            
            # Log da versão detectada
            if requested_version:
                logger.debug(f"Versão detectada: {requested_version} (fonte: {request.state.version_source})")
            
            # Processar request
            response = await call_next(request)
            
            # Adicionar headers de versão na resposta
            response.headers["X-API-Version"] = request.state.api_version
            response.headers["X-API-Supported-Versions"] = ", ".join(self.supported_versions)
            
            return response
            
        except Exception as e:
            logger.error(f"Erro no VersioningMiddleware: {e}")
            return JSONResponse(
                status_code=500,
                content={"error": "Erro interno do servidor"}
            )
    
    def _detect_version(self, request: Request) -> Optional[str]:
        """Detectar versão solicitada pelo cliente."""
        
        # 1. Header X-API-Version
        if self.enable_header_versioning:
            header_version = request.headers.get("X-API-Version")
            if header_version:
                return header_version.strip()
        
        # 2. Query parameter version
        if self.enable_query_versioning:
            query_version = request.query_params.get("version")
            if query_version:
                return query_version.strip()
        
        # 3. Path prefix (já processado pelo FastAPI)
        # O FastAPI já processa o prefixo /api/v1, então não precisamos fazer nada aqui
        
        return None
    
    def _get_version_source(self, request: Request) -> str:
        """Identificar a fonte da versão detectada."""
        if request.headers.get("X-API-Version"):
            return "header"
        elif request.query_params.get("version"):
            return "query"
        else:
            return "default"


def create_versioning_middleware(app, **kwargs):
    """
    Factory para criar middleware de versionamento.
    
    Args:
        app: Aplicação FastAPI
        **kwargs: Argumentos para VersioningMiddleware
    
    Returns:
        VersioningMiddleware configurado
    """
    return VersioningMiddleware(app, **kwargs)


# Configuração padrão do middleware
def get_versioning_config() -> dict:
    """Obter configuração padrão do middleware de versionamento."""
    return {
        "enable_header_versioning": True,
        "enable_query_versioning": True,
        "supported_versions": ["v1", "v2"],
        "default_version": "v1"
    }
