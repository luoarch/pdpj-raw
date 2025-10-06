"""Modelo para tracking de jobs de download de processos."""

from datetime import datetime
from typing import Optional
from enum import Enum
from sqlalchemy import String, Text, DateTime, JSON, BigInteger, ForeignKey, Integer, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class JobStatus(str, Enum):
    """Status do job de processamento."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ProcessJob(Base):
    """Modelo para tracking de jobs de download de processos."""
    
    __tablename__ = "process_jobs"
    __table_args__ = {"schema": "pdpj"}
    
    # Identificação
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    job_id: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    
    # Relacionamento com processo
    process_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("pdpj.processes.id", ondelete="CASCADE"), nullable=False, index=True)
    process: Mapped["Process"] = relationship("Process", back_populates="jobs")
    
    # Webhook
    webhook_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    webhook_sent: Mapped[bool] = mapped_column(default=False, nullable=False)
    webhook_sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    webhook_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    webhook_last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Status e progresso
    status: Mapped[str] = mapped_column(String(20), default=JobStatus.PENDING.value, nullable=False, index=True)
    total_documents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completed_documents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_documents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    progress_percentage: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Metadados
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    job_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    def update_progress(self):
        """Atualizar porcentagem de progresso."""
        if self.total_documents > 0:
            self.progress_percentage = (self.completed_documents / self.total_documents) * 100
    
    @property
    def is_active(self) -> bool:
        """Job está ativo (pending ou processing)."""
        return self.status in [JobStatus.PENDING.value, JobStatus.PROCESSING.value]
    
    @property
    def duration_seconds(self) -> Optional[float]:
        """Duração do job em segundos."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        elif self.started_at:
            return (datetime.utcnow() - self.started_at).total_seconds()
        return None
    
    def __repr__(self) -> str:
        return f"<ProcessJob(job_id='{self.job_id}', status='{self.status}', progress={self.progress_percentage:.1f}%)>"

