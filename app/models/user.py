"""Modelos para usuários e autenticação."""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, Boolean, BigInteger, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
import enum


class UserRole(str, enum.Enum):
    """Roles de usuário."""
    ADMIN = "admin"
    USER = "user"
    READONLY = "readonly"


class User(Base):
    """Modelo para usuários da API."""
    
    __tablename__ = "users"
    __table_args__ = {"schema": "pdpj"}
    
    # Identificação do usuário
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Autenticação
    api_key: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    role: Mapped[UserRole] = mapped_column(SQLEnum(UserRole), default=UserRole.USER, nullable=False)
    
    # Configurações de rate limiting
    rate_limit_requests: Mapped[Optional[int]] = mapped_column(nullable=True)
    rate_limit_window: Mapped[Optional[int]] = mapped_column(nullable=True)
    
    # Metadados
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow, 
        nullable=False
    )
    last_access: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Flags de controle
    active: Mapped[bool] = mapped_column(default=True, nullable=False)
    
    def __repr__(self) -> str:
        return f"<User(username='{self.username}', role='{self.role}')>"
