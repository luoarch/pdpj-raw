"""Sistema de autenticação e segurança."""

from datetime import datetime
from typing import Optional
from fastapi import HTTPException, status, Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.config import settings
from app.models.user import User

# Configurar HTTPBearer
security = HTTPBearer(auto_error=False)


async def get_current_user(
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Obter usuário atual baseado na API key."""
    
    # Verificar se o header de autorização está presente
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key é obrigatória",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extrair a API key do header
    try:
        scheme, api_key = authorization.split(" ", 1)
        if scheme.lower() != "bearer":
            raise ValueError("Esquema de autenticação inválido")
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Formato de autorização inválido. Use: Bearer <api_key>",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Buscar usuário no banco de dados
    result = await db.execute(
        select(User).where(User.api_key == api_key)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key inválida",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verificar se o usuário está ativo
    if not user.active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário inativo",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Atualizar último acesso
    user.last_access = datetime.utcnow()
    await db.commit()
    
    return user


async def get_current_user_optional(
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """Obter usuário atual de forma opcional (para endpoints que podem ser públicos)."""
    
    if not authorization:
        return None
    
    try:
        return await get_current_user(authorization, db)
    except HTTPException:
        return None


def require_role(required_role: str):
    """Decorator para verificar roles de usuário."""
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        from app.models.user import UserRole
        
        # Admin tem acesso a tudo
        if current_user.role == UserRole.ADMIN:
            return current_user
        
        # Verificar se o usuário tem a role necessária
        if current_user.role.value != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acesso negado. Role necessária: {required_role}"
            )
        
        return current_user
    
    return role_checker


def require_admin():
    """Decorator para verificar se o usuário é admin."""
    return require_role("admin")


def require_user_or_admin():
    """Decorator para verificar se o usuário é user ou admin."""
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        from app.models.user import UserRole
        
        if current_user.role in [UserRole.USER, UserRole.ADMIN]:
            return current_user
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado. Role necessária: user ou admin"
        )
    
    return role_checker
