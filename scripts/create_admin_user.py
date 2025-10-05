#!/usr/bin/env python3
"""Script para criar usuário administrador inicial."""

import asyncio
import sys
import os
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import AsyncSessionLocal
from app.models import User, UserRole
from sqlalchemy import select
import secrets


async def create_admin_user():
    """Criar usuário administrador inicial."""
    
    async with AsyncSessionLocal() as db:
        # Verificar se já existe um admin
        result = await db.execute(
            select(User).where(User.role == UserRole.ADMIN)
        )
        existing_admin = result.scalar_one_or_none()
        
        if existing_admin:
            print(f"✅ Usuário administrador já existe: {existing_admin.username}")
            return
        
        # Criar usuário admin
        admin_api_key = f"pdpj_admin_{secrets.token_urlsafe(32)}"
        
        admin_user = User(
            username="admin",
            email="admin@pdpj.local",
            api_key=admin_api_key,
            role=UserRole.ADMIN,
            rate_limit_requests=1000,  # Limite mais alto para admin
            rate_limit_window=60,
            active=True
        )
        
        db.add(admin_user)
        await db.commit()
        await db.refresh(admin_user)
        
        print("🎉 Usuário administrador criado com sucesso!")
        print(f"📋 Detalhes do usuário:")
        print(f"   Username: {admin_user.username}")
        print(f"   Email: {admin_user.email}")
        print(f"   Role: {admin_user.role.value}")
        print(f"   API Key: {admin_api_key}")
        print()
        print("🔐 Use esta API Key para autenticação:")
        print(f"   Authorization: Bearer {admin_api_key}")
        print()
        print("⚠️  IMPORTANTE: Guarde esta API Key em local seguro!")


async def create_test_user():
    """Criar usuário de teste."""
    
    async with AsyncSessionLocal() as db:
        # Verificar se já existe um usuário de teste
        result = await db.execute(
            select(User).where(User.username == "test_user")
        )
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            print(f"✅ Usuário de teste já existe: {existing_user.username}")
            return
        
        # Criar usuário de teste
        test_api_key = f"pdpj_test_{secrets.token_urlsafe(32)}"
        
        test_user = User(
            username="test_user",
            email="test@pdpj.local",
            api_key=test_api_key,
            role=UserRole.USER,
            rate_limit_requests=100,
            rate_limit_window=60,
            active=True
        )
        
        db.add(test_user)
        await db.commit()
        await db.refresh(test_user)
        
        print("🎉 Usuário de teste criado com sucesso!")
        print(f"📋 Detalhes do usuário:")
        print(f"   Username: {test_user.username}")
        print(f"   Email: {test_user.email}")
        print(f"   Role: {test_user.role.value}")
        print(f"   API Key: {test_api_key}")
        print()
        print("🔐 Use esta API Key para autenticação:")
        print(f"   Authorization: Bearer {test_api_key}")


async def main():
    """Função principal."""
    print("🚀 Criando usuários iniciais para PDPJ API...")
    print()
    
    try:
        await create_admin_user()
        print()
        await create_test_user()
        print()
        print("✅ Todos os usuários foram criados com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro ao criar usuários: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
