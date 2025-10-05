"""Endpoints para gerenciamento de usuários."""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from pydantic import BaseModel, Field
import secrets

from app.core.database import get_db
from app.core.security import get_current_user, require_admin
# from app.core.rate_limiting import limiter
from app.models import User, UserRole

router = APIRouter(tags=["users"])


class UserCreate(BaseModel):
    """Schema para criação de usuário."""
    username: str = Field(..., description="Nome de usuário")
    email: Optional[str] = Field(None, description="Email do usuário")
    role: UserRole = Field(default=UserRole.USER, description="Role do usuário")
    rate_limit_requests: Optional[int] = Field(None, description="Limite de requisições personalizado")
    rate_limit_window: Optional[int] = Field(None, description="Janela de tempo personalizada")


class UserUpdate(BaseModel):
    """Schema para atualização de usuário."""
    email: Optional[str] = None
    role: Optional[UserRole] = None
    rate_limit_requests: Optional[int] = None
    rate_limit_window: Optional[int] = None
    active: Optional[bool] = None


class UserResponse(BaseModel):
    """Schema para resposta de usuário."""
    id: int
    username: str
    email: Optional[str] = None
    role: UserRole
    rate_limit_requests: Optional[int] = None
    rate_limit_window: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    last_access: Optional[datetime] = None
    active: bool
    
    class Config:
        from_attributes = True


class UserCreateResponse(BaseModel):
    """Schema para resposta de criação de usuário."""
    user: UserResponse
    api_key: str


@router.get("", response_model=List[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin())
):
    """Listar usuários (apenas admin)."""
    try:
        result = await db.execute(
            select(User)
            .offset(skip)
            .limit(limit)
            .order_by(User.created_at.desc())
        )
        users = result.scalars().all()
        
        return [UserResponse.model_validate(user) for user in users]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao listar usuários: {str(e)}"
        )


@router.post("", response_model=UserCreateResponse)
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin())
):
    """Criar novo usuário (apenas admin)."""
    try:
        # Verificar se username já existe
        result = await db.execute(
            select(User).where(User.username == user_data.username)
        )
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username já existe"
            )
        
        # Gerar API key única
        api_key = f"pdpj_{secrets.token_urlsafe(32)}"
        
        # Criar usuário
        user = User(
            username=user_data.username,
            email=user_data.email,
            api_key=api_key,
            role=user_data.role,
            rate_limit_requests=user_data.rate_limit_requests,
            rate_limit_window=user_data.rate_limit_window
        )
        
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        return UserCreateResponse(
            user=UserResponse.model_validate(user),
            api_key=api_key
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao criar usuário: {str(e)}"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Obter informações do usuário atual."""
    return UserResponse.model_validate(current_user)


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Atualizar informações do usuário atual."""
    try:
        # Usuários comuns não podem alterar role ou status ativo
        if current_user.role != UserRole.ADMIN:
            if user_update.role is not None:
                user_update.role = None
            if user_update.active is not None:
                user_update.active = None
        
        # Atualizar apenas campos não nulos
        update_data = user_update.model_dump(exclude_unset=True)
        
        if update_data:
            await db.execute(
                update(User)
                .where(User.id == current_user.id)
                .values(**update_data)
            )
            await db.commit()
            
            # Recarregar usuário atualizado
            result = await db.execute(
                select(User).where(User.id == current_user.id)
            )
            updated_user = result.scalar_one()
            
            return UserResponse.model_validate(updated_user)
        
        return UserResponse.model_validate(current_user)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao atualizar usuário: {str(e)}"
        )


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin())
):
    """Atualizar usuário (apenas admin)."""
    try:
        # Buscar usuário
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado"
            )
        
        # Atualizar apenas campos não nulos
        update_data = user_update.model_dump(exclude_unset=True)
        
        if update_data:
            await db.execute(
                update(User)
                .where(User.id == user_id)
                .values(**update_data)
            )
            await db.commit()
            
            # Recarregar usuário atualizado
            result = await db.execute(
                select(User).where(User.id == user_id)
            )
            updated_user = result.scalar_one()
            
            return UserResponse.model_validate(updated_user)
        
        return UserResponse.model_validate(user)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao atualizar usuário: {str(e)}"
        )


@router.post("/{user_id}/regenerate-api-key", response_model=dict)
async def regenerate_api_key(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin())
):
    """Regenerar API key de um usuário (apenas admin)."""
    try:
        # Buscar usuário
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado"
            )
        
        # Gerar nova API key
        new_api_key = f"pdpj_{secrets.token_urlsafe(32)}"
        
        # Atualizar API key
        await db.execute(
            update(User)
            .where(User.id == user_id)
            .values(api_key=new_api_key)
        )
        await db.commit()
        
        return {
            "message": "API key regenerada com sucesso",
            "api_key": new_api_key
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao regenerar API key: {str(e)}"
        )


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin())
):
    """Deletar usuário (apenas admin)."""
    try:
        # Não permitir deletar a si mesmo
        if user_id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Não é possível deletar seu próprio usuário"
            )
        
        # Buscar usuário
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado"
            )
        
        # Deletar usuário
        await db.delete(user)
        await db.commit()
        
        return {"message": "Usuário deletado com sucesso"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao deletar usuário: {str(e)}"
        )
