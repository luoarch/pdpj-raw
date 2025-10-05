"""Aplicação principal FastAPI para API PDPJ Ultra-Fast Edition."""

from app.core.app_factory import create_fastapi_app

# Criar instância da aplicação usando factory
app = create_fastapi_app()
