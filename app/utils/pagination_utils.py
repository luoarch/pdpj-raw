"""
Utilitários para paginação de resultados.
"""

from typing import List, Dict, Any, Optional, Tuple
from fastapi import Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from app.models import Process, Document


class PaginationParams(BaseModel):
    """Parâmetros de paginação."""
    skip: int = Field(default=0, ge=0, description="Número de itens a pular")
    limit: int = Field(default=100, ge=1, le=1000, description="Número máximo de itens por página")
    
    @property
    def offset(self) -> int:
        """Offset para consultas SQL."""
        return self.skip
    
    @property
    def page(self) -> int:
        """Número da página (baseado em 1)."""
        return (self.skip // self.limit) + 1


class PaginatedResponse(BaseModel):
    """Resposta paginada."""
    items: List[Any] = Field(description="Lista de itens da página atual")
    total: int = Field(description="Total de itens")
    page: int = Field(description="Página atual")
    pages: int = Field(description="Total de páginas")
    has_next: bool = Field(description="Se existe próxima página")
    has_prev: bool = Field(description="Se existe página anterior")
    next_page: Optional[int] = Field(default=None, description="Número da próxima página")
    prev_page: Optional[int] = Field(default=None, description="Número da página anterior")


def create_pagination_params(
    skip: int = Query(0, ge=0, description="Número de itens a pular"),
    limit: int = Query(100, ge=1, le=1000, description="Número máximo de itens por página")
) -> PaginationParams:
    """Criar parâmetros de paginação para endpoints FastAPI."""
    return PaginationParams(skip=skip, limit=limit)


def paginate_results(
    items: List[Any],
    total: int,
    pagination: PaginationParams
) -> PaginatedResponse:
    """Criar resposta paginada."""
    pages = (total + pagination.limit - 1) // pagination.limit  # Ceiling division
    current_page = pagination.page
    
    has_next = current_page < pages
    has_prev = current_page > 1
    
    next_page = current_page + 1 if has_next else None
    prev_page = current_page - 1 if has_prev else None
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=current_page,
        pages=pages,
        has_next=has_next,
        has_prev=has_prev,
        next_page=next_page,
        prev_page=prev_page
    )


def apply_pagination_to_query(query, pagination: PaginationParams):
    """Aplicar paginação a uma query SQLAlchemy."""
    return query.offset(pagination.offset).limit(pagination.limit)


class DocumentPaginationParams(PaginationParams):
    """Parâmetros de paginação específicos para documentos."""
    sort_by: str = Field(default="created_at", description="Campo para ordenação")
    sort_order: str = Field(default="desc", description="Ordem da ordenação (asc/desc)")
    filter_type: Optional[str] = Field(default=None, description="Filtrar por tipo de documento")
    filter_downloaded: Optional[bool] = Field(default=None, description="Filtrar por status de download")


def create_document_pagination_params(
    skip: int = Query(0, ge=0, description="Número de documentos a pular"),
    limit: int = Query(50, ge=1, le=500, description="Número máximo de documentos por página"),
    sort_by: str = Query("created_at", description="Campo para ordenação"),
    sort_order: str = Query("desc", description="Ordem da ordenação (asc/desc)"),
    filter_type: Optional[str] = Query(None, description="Filtrar por tipo de documento"),
    filter_downloaded: Optional[bool] = Query(None, description="Filtrar por status de download")
) -> DocumentPaginationParams:
    """Criar parâmetros de paginação para documentos."""
    return DocumentPaginationParams(
        skip=skip,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
        filter_type=filter_type,
        filter_downloaded=filter_downloaded
    )


def apply_document_filters(query, pagination: DocumentPaginationParams):
    """Aplicar filtros e ordenação para documentos."""
    # Aplicar filtros
    if pagination.filter_type:
        query = query.filter(Document.type == pagination.filter_type)
    
    if pagination.filter_downloaded is not None:
        query = query.filter(Document.downloaded == pagination.filter_downloaded)
    
    # Aplicar ordenação
    sort_column = getattr(Document, pagination.sort_by, Document.created_at)
    if pagination.sort_order.lower() == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())
    
    # Aplicar paginação
    return apply_pagination_to_query(query, pagination)


class ProcessPaginationParams(PaginationParams):
    """Parâmetros de paginação específicos para processos."""
    sort_by: str = Field(default="updated_at", description="Campo para ordenação")
    sort_order: str = Field(default="desc", description="Ordem da ordenação (asc/desc)")
    filter_court: Optional[str] = Field(default=None, description="Filtrar por tribunal")
    filter_has_documents: Optional[bool] = Field(default=None, description="Filtrar por presença de documentos")


def create_process_pagination_params(
    skip: int = Query(0, ge=0, description="Número de processos a pular"),
    limit: int = Query(100, ge=1, le=1000, description="Número máximo de processos por página"),
    sort_by: str = Query("updated_at", description="Campo para ordenação"),
    sort_order: str = Query("desc", description="Ordem da ordenação (asc/desc)"),
    filter_court: Optional[str] = Query(None, description="Filtrar por tribunal"),
    filter_has_documents: Optional[bool] = Query(None, description="Filtrar por presença de documentos")
) -> ProcessPaginationParams:
    """Criar parâmetros de paginação para processos."""
    return ProcessPaginationParams(
        skip=skip,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
        filter_court=filter_court,
        filter_has_documents=filter_has_documents
    )


def apply_process_filters(query, pagination: ProcessPaginationParams):
    """Aplicar filtros e ordenação para processos."""
    # Aplicar filtros
    if pagination.filter_court:
        query = query.filter(Process.court == pagination.filter_court)
    
    if pagination.filter_has_documents is not None:
        query = query.filter(Process.has_documents == pagination.filter_has_documents)
    
    # Aplicar ordenação
    sort_column = getattr(Process, pagination.sort_by, Process.updated_at)
    if pagination.sort_order.lower() == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())
    
    # Aplicar paginação
    return apply_pagination_to_query(query, pagination)
