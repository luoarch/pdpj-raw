"""Schemas para status de processamento de processos."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class DocumentStatusResponse(BaseModel):
    """Status de um documento individual."""
    
    id: str = Field(..., description="ID numérico do documento")
    uuid: str = Field(..., description="UUID do documento (para download)")
    name: str = Field(..., description="Nome do documento")
    status: str = Field(..., description="Status: pending, processing, available, failed")
    size: Optional[int] = Field(None, description="Tamanho em bytes")
    mime_type: Optional[str] = Field(None, description="Tipo MIME")
    download_url: Optional[str] = Field(None, description="URL presignada S3 (se disponível)")
    error_message: Optional[str] = Field(None, description="Mensagem de erro (se falhou)")
    download_started_at: Optional[datetime] = Field(None, description="Início do download")
    download_completed_at: Optional[datetime] = Field(None, description="Conclusão do download")
    
    class Config:
        from_attributes = True


class ProcessStatusResponse(BaseModel):
    """Status completo do processamento de um processo."""
    
    process_number: str = Field(..., description="Número do processo")
    status: str = Field(..., description="Status geral: pending, processing, completed, failed")
    
    # Progresso
    total_documents: int = Field(..., description="Total de documentos")
    completed_documents: int = Field(..., description="Documentos completados")
    failed_documents: int = Field(..., description="Documentos com falha")
    pending_documents: int = Field(..., description="Documentos pendentes")
    processing_documents: int = Field(..., description="Documentos em processamento")
    progress_percentage: float = Field(..., description="Porcentagem de conclusão (0-100)")
    
    # Job info
    job_id: Optional[str] = Field(None, description="ID do job Celery (se houver)")
    webhook_url: Optional[str] = Field(None, description="URL do webhook (se configurado)")
    webhook_sent: bool = Field(False, description="Webhook foi enviado")
    webhook_sent_at: Optional[datetime] = Field(None, description="Data/hora envio webhook")
    
    # Timestamps
    created_at: Optional[datetime] = Field(None, description="Criação do job")
    started_at: Optional[datetime] = Field(None, description="Início do processamento")
    completed_at: Optional[datetime] = Field(None, description="Conclusão do processamento")
    
    # Documentos
    documents: List[DocumentStatusResponse] = Field(default_factory=list, description="Lista de documentos")
    
    class Config:
        from_attributes = True

