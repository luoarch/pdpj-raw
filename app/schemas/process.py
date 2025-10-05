"""Schemas para processos judiciais."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ProcessBase(BaseModel):
    """Schema base para processos."""
    process_number: str = Field(..., description="Número do processo judicial")
    court: Optional[str] = Field(None, description="Tribunal do processo")
    subject: Optional[str] = Field(None, description="Assunto do processo")
    status: Optional[str] = Field(None, description="Status atual do processo")


class ProcessCreate(ProcessBase):
    """Schema para criação de processo."""
    pass


class ProcessUpdate(BaseModel):
    """Schema para atualização de processo."""
    court: Optional[str] = None
    subject: Optional[str] = None
    status: Optional[str] = None
    raw_data: Optional[Dict[str, Any]] = None
    cover_data: Optional[Dict[str, Any]] = None
    full_data: Optional[Dict[str, Any]] = None
    has_documents: Optional[bool] = None
    documents_downloaded: Optional[bool] = None


class ProcessResponse(ProcessBase):
    """Schema para resposta de processo."""
    id: int
    created_at: datetime
    updated_at: datetime
    last_consultation: Optional[datetime] = None
    has_documents: bool = False
    documents_downloaded: bool = False
    full_data: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


class ProcessSearchRequest(BaseModel):
    """Schema para requisição de busca de processos."""
    process_numbers: List[str] = Field(..., description="Lista de números de processos", max_items=4000)
    include_documents: bool = Field(False, description="Incluir download de documentos")
    force_refresh: bool = Field(False, description="Forçar atualização mesmo se em cache")


class ProcessSearchResponse(BaseModel):
    """Schema para resposta de busca de processos."""
    total_requested: int
    found: int
    not_found: List[str] = Field(default_factory=list)
    processes: List[ProcessResponse] = Field(default_factory=list)
    batch_id: Optional[str] = Field(None, description="ID do lote para processamento assíncrono")


class ProcessFilesResponse(BaseModel):
    """Schema para resposta de arquivos do processo."""
    process_number: str
    documents: List[Dict[str, Any]] = Field(default_factory=list)
    total_documents: int = 0
    downloaded_documents: int = 0
