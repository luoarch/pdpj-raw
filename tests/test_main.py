"""Testes básicos para a aplicação principal."""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_endpoint():
    """Testar endpoint raiz."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["message"] == "PDPJ Process API"
    assert "version" in data
    assert data["version"] == "1.0.0"


def test_health_check():
    """Testar endpoint de verificação de saúde."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "healthy"


def test_processes_endpoint():
    """Testar endpoint de listagem de processos."""
    response = client.get("/processes/")
    assert response.status_code == 200
    # Deve retornar lista vazia inicialmente
    assert response.json() == []


def test_search_processes_empty():
    """Testar busca de processos com lista vazia."""
    response = client.post("/processes/search", json={
        "process_numbers": [],
        "include_documents": False,
        "force_refresh": False
    })
    assert response.status_code == 200
    data = response.json()
    assert data["total_requested"] == 0
    assert data["found"] == 0
