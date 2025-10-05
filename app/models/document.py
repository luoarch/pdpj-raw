"""Modelos para documentos de processos."""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, DateTime, JSON, BigInteger, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Document(Base):
    """Modelo para armazenar metadados de documentos de processos."""
    
    __tablename__ = "documents"
    __table_args__ = {"schema": "pdpj"}
    
    # Identificação do documento
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    document_id: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    
    # Relacionamento com processo
    process_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("pdpj.processes.id"), nullable=False)
    process: Mapped["Process"] = relationship("Process", back_populates="documents")
    
    # Metadados do documento
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    size: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    mime_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Informações de armazenamento
    s3_key: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    s3_bucket: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    download_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Dados brutos da API PDPJ
    raw_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Metadados
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow, 
        nullable=False
    )
    
    # Flags de controle
    downloaded: Mapped[bool] = mapped_column(default=False, nullable=False)
    available: Mapped[bool] = mapped_column(default=True, nullable=False)
    
    def __repr__(self) -> str:
        return f"<Document(document_id='{self.document_id}', name='{self.name}')>"
