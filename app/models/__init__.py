"""Modelos de banco de dados."""

from .process import Process
from .document import Document
from .user import User, UserRole
from app.core.database import Base

__all__ = ["Base", "Process", "Document", "User", "UserRole"]
