#!/usr/bin/env python3
"""
Script para resetar completamente o banco de dados e migrações do Alembic.
Remove todas as tabelas, limpa o histórico de migrações e recria tudo do zero.
"""

import os
import sys
import asyncio
import subprocess
from pathlib import Path
from loguru import logger
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Adicionar o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent))

# Configurar logging
logger.remove()
logger.add(sys.stdout, level="INFO", format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")

class DatabaseReset:
    """Classe para resetar completamente o banco de dados."""
    
    def __init__(self):
        self.confirmation_required = True
        
    async def confirm_reset(self):
        """Solicitar confirmação do usuário."""
        logger.warning("⚠️  ATENÇÃO: Esta operação irá:")
        logger.warning("   🗑️  Remover TODAS as tabelas do banco")
        logger.warning("   🗑️  Limpar TODO o histórico de migrações")
        logger.warning("   🗑️  Apagar TODOS os dados existentes")
        logger.warning("")
        logger.warning("💥 Esta ação é IRREVERSÍVEL!")
        logger.warning("")
        
        if self.confirmation_required:
            response = input("🤔 Tem certeza que deseja continuar? (digite 'RESET' para confirmar): ")
            if response != "RESET":
                logger.info("❌ Operação cancelada pelo usuário")
                return False
        
        logger.warning("🔥 Iniciando reset completo do banco...")
        return True
    
    async def check_database_connection(self):
        """Verificar conexão com o banco."""
        logger.info("🔌 VERIFICANDO CONEXÃO COM BANCO")
        logger.info("=" * 50)
        
        try:
            from app.core.database import AsyncSessionLocal
            from sqlalchemy import text
            
            async with AsyncSessionLocal() as session:
                result = await session.execute(text("SELECT 1 as test"))
                test_value = result.scalar()
                
                if test_value == 1:
                    logger.success("✅ Conexão com banco estabelecida")
                    return True
                else:
                    logger.error("❌ Conexão com banco falhou")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Erro na conexão: {str(e)}")
            return False
    
    async def drop_all_tables(self):
        """Remover todas as tabelas do banco."""
        logger.info("🗑️ REMOVENDO TODAS AS TABELAS")
        logger.info("=" * 50)
        
        try:
            from app.core.database import AsyncSessionLocal
            from sqlalchemy import text
            
            async with AsyncSessionLocal() as session:
                # Obter lista de todas as tabelas
                tables_query = text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_type = 'BASE TABLE'
                """)
                
                result = await session.execute(tables_query)
                tables = [row[0] for row in result.fetchall()]
                
                if not tables:
                    logger.info("📋 Nenhuma tabela encontrada")
                    return True
                
                logger.info(f"📋 Encontradas {len(tables)} tabelas para remover:")
                for table in tables:
                    logger.info(f"   🗑️ {table}")
                
                # Remover todas as tabelas
                for table in tables:
                    try:
                        drop_query = text(f'DROP TABLE IF EXISTS "{table}" CASCADE')
                        await session.execute(drop_query)
                        logger.success(f"   ✅ {table} removida")
                    except Exception as e:
                        logger.error(f"   ❌ Erro ao remover {table}: {str(e)}")
                
                await session.commit()
                logger.success("✅ Todas as tabelas removidas")
                return True
                
        except Exception as e:
            logger.error(f"❌ Erro ao remover tabelas: {str(e)}")
            return False
    
    def reset_alembic_history(self):
        """Resetar histórico do Alembic."""
        logger.info("🔄 RESETANDO HISTÓRICO DO ALEMBIC")
        logger.info("=" * 50)
        
        try:
            # Remover pasta de versões (se existir)
            versions_dir = Path("alembic/versions")
            if versions_dir.exists():
                import shutil
                shutil.rmtree(versions_dir)
                logger.success("✅ Pasta de versões removida")
            
            # Recriar pasta de versões
            versions_dir.mkdir(parents=True, exist_ok=True)
            logger.success("✅ Pasta de versões recriada")
            
            # Remover arquivo __init__.py se existir
            init_file = versions_dir / "__init__.py"
            if init_file.exists():
                init_file.unlink()
                logger.success("✅ __init__.py removido")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao resetar Alembic: {str(e)}")
            return False
    
    def create_initial_migration(self):
        """Criar migração inicial."""
        logger.info("📝 CRIANDO MIGRAÇÃO INICIAL")
        logger.info("=" * 50)
        
        try:
            # Criar migração inicial
            result = subprocess.run(
                ["alembic", "revision", "--autogenerate", "-m", "Initial migration"],
                capture_output=True,
                text=True,
                cwd=os.getcwd()
            )
            
            if result.returncode == 0:
                logger.success("✅ Migração inicial criada")
                logger.info("📝 Output:")
                for line in result.stdout.split('\n'):
                    if line.strip():
                        logger.info(f"   {line}")
                return True
            else:
                logger.error("❌ Erro ao criar migração inicial")
                logger.error(f"📝 Erro: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro ao criar migração: {str(e)}")
            return False
    
    async def apply_initial_migration(self):
        """Aplicar migração inicial."""
        logger.info("🚀 APLICANDO MIGRAÇÃO INICIAL")
        logger.info("=" * 50)
        
        try:
            # Aplicar migração
            result = subprocess.run(
                ["alembic", "upgrade", "head"],
                capture_output=True,
                text=True,
                cwd=os.getcwd()
            )
            
            if result.returncode == 0:
                logger.success("✅ Migração inicial aplicada")
                logger.info("📝 Output:")
                for line in result.stdout.split('\n'):
                    if line.strip():
                        logger.info(f"   {line}")
                return True
            else:
                logger.error("❌ Erro ao aplicar migração")
                logger.error(f"📝 Erro: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro ao aplicar migração: {str(e)}")
            return False
    
    async def verify_database_structure(self):
        """Verificar estrutura final do banco."""
        logger.info("🔍 VERIFICANDO ESTRUTURA FINAL")
        logger.info("=" * 50)
        
        try:
            from app.core.database import AsyncSessionLocal
            from sqlalchemy import text
            
            async with AsyncSessionLocal() as session:
                # Verificar tabelas criadas
                tables_query = text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_type = 'BASE TABLE'
                    ORDER BY table_name
                """)
                
                result = await session.execute(tables_query)
                tables = [row[0] for row in result.fetchall()]
                
                logger.info(f"📊 Tabelas criadas: {len(tables)}")
                for table in tables:
                    logger.success(f"   ✅ {table}")
                
                # Verificar versão do Alembic
                try:
                    version_query = text("SELECT version_num FROM alembic_version")
                    result = await session.execute(version_query)
                    version = result.scalar()
                    logger.success(f"📌 Versão do Alembic: {version}")
                except:
                    logger.warning("⚠️ Tabela alembic_version não encontrada")
                
                return len(tables) > 0
                
        except Exception as e:
            logger.error(f"❌ Erro ao verificar estrutura: {str(e)}")
            return False
    
    async def create_initial_data(self):
        """Criar dados iniciais."""
        logger.info("🌱 CRIANDO DADOS INICIAIS")
        logger.info("=" * 50)
        
        try:
            from app.core.database import AsyncSessionLocal
            from sqlalchemy import text
            
            async with AsyncSessionLocal() as session:
                # Criar usuário admin
                admin_query = text("""
                    INSERT INTO users (username, email, is_active, is_admin, created_at, updated_at)
                    VALUES ('admin', 'admin@pdpj.local', true, true, NOW(), NOW())
                    ON CONFLICT (username) DO NOTHING
                """)
                
                await session.execute(admin_query)
                await session.commit()
                
                logger.success("✅ Usuário admin criado")
                
                # Verificar contadores
                result = await session.execute(text("SELECT COUNT(*) FROM users"))
                user_count = result.scalar()
                logger.info(f"👤 Total de usuários: {user_count}")
                
                return True
                
        except Exception as e:
            logger.error(f"❌ Erro ao criar dados iniciais: {str(e)}")
            return False
    
    async def run_full_reset(self):
        """Executar reset completo do banco."""
        logger.info("🔥 INICIANDO RESET COMPLETO DO BANCO DE DADOS")
        logger.info("=" * 60)
        logger.info("")
        
        # Passo 1: Confirmação
        if not await self.confirm_reset():
            return False
        logger.info("")
        
        # Passo 2: Verificar conexão
        if not await self.check_database_connection():
            logger.error("💥 Falha na conexão - abortando")
            return False
        logger.info("")
        
        # Passo 3: Remover todas as tabelas
        if not await self.drop_all_tables():
            logger.error("💥 Falha ao remover tabelas - abortando")
            return False
        logger.info("")
        
        # Passo 4: Resetar histórico do Alembic
        if not self.reset_alembic_history():
            logger.error("💥 Falha ao resetar Alembic - abortando")
            return False
        logger.info("")
        
        # Passo 5: Criar migração inicial
        if not self.create_initial_migration():
            logger.error("💥 Falha ao criar migração - abortando")
            return False
        logger.info("")
        
        # Passo 6: Aplicar migração inicial
        if not await self.apply_initial_migration():
            logger.error("💥 Falha ao aplicar migração - abortando")
            return False
        logger.info("")
        
        # Passo 7: Verificar estrutura
        if not await self.verify_database_structure():
            logger.error("💥 Estrutura do banco inválida")
            return False
        logger.info("")
        
        # Passo 8: Criar dados iniciais
        await self.create_initial_data()
        logger.info("")
        
        # Resumo final
        logger.success("🎉 RESET COMPLETO DO BANCO CONCLUÍDO COM SUCESSO!")
        logger.info("=" * 60)
        logger.info("✅ Todas as tabelas antigas removidas")
        logger.info("✅ Histórico do Alembic resetado")
        logger.info("✅ Migração inicial criada e aplicada")
        logger.info("✅ Estrutura do banco validada")
        logger.info("✅ Dados iniciais criados")
        logger.info("")
        logger.info("🚀 Banco de dados pronto para uso!")
        logger.info("=" * 60)
        
        return True

async def main():
    """Função principal."""
    reset = DatabaseReset()
    
    try:
        success = await reset.run_full_reset()
        if success:
            logger.success("🎯 Reset do banco concluído com sucesso!")
            return 0
        else:
            logger.error("💥 Reset do banco falhou!")
            return 1
    except KeyboardInterrupt:
        logger.warning("⚠️ Reset interrompido pelo usuário")
        return 1
    except Exception as e:
        logger.error(f"💥 Erro inesperado: {str(e)}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
