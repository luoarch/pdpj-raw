"""Modelos para processos judiciais."""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Text, DateTime, JSON, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Process(Base):
    """Modelo para armazenar dados de processos judiciais."""
    
    __tablename__ = "processes"
    __table_args__ = {"schema": "pdpj"}
    
    # Identificação do processo
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    process_number: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    
    # Dados estruturados básicos
    court: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    subject: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Dados brutos da API PDPJ
    raw_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    cover_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    full_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Metadados
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow, 
        nullable=False
    )
    last_consultation: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Flags de controle
    has_documents: Mapped[bool] = mapped_column(default=False, nullable=False)
    documents_downloaded: Mapped[bool] = mapped_column(default=False, nullable=False)
    
    # Relacionamentos
    documents: Mapped[List["Document"]] = relationship(
        "Document", 
        back_populates="process",
        cascade="all, delete-orphan"
    )
    jobs: Mapped[List["ProcessJob"]] = relationship(
        "ProcessJob",
        back_populates="process",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Process(process_number='{self.process_number}', court='{self.court}')>"
