#!/usr/bin/env python3
"""
Script para configurar e migrar o banco de dados.
Verifica se as tabelas existem e executa migrações se necessário.
"""

import os
import sys
import asyncio
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

class DatabaseSetup:
    """Classe para configurar e migrar o banco de dados."""
    
    def __init__(self):
        self.required_tables = ['processes', 'documents', 'users']
        self.migration_commands = []
        
    async def check_database_connection(self):
        """Verificar conexão com o banco de dados."""
        logger.info("🔌 VERIFICANDO CONEXÃO COM BANCO DE DADOS")
        logger.info("=" * 50)
        
        try:
            from app.core.database import AsyncSessionLocal
            from sqlalchemy import text
            
            async with AsyncSessionLocal() as session:
                result = await session.execute(text("SELECT 1 as test"))
                test_value = result.scalar()
                
                if test_value == 1:
                    logger.success("✅ Conexão com banco de dados estabelecida")
                    return True
                else:
                    logger.error("❌ Conexão com banco falhou - valor de teste incorreto")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Erro na conexão com banco: {str(e)}")
            return False
    
    async def check_existing_tables(self):
        """Verificar quais tabelas já existem."""
        logger.info("📋 VERIFICANDO TABELAS EXISTENTES")
        logger.info("=" * 50)
        
        try:
            from app.core.database import AsyncSessionLocal
            from sqlalchemy import text
            
            async with AsyncSessionLocal() as session:
                # Consultar tabelas existentes
                tables_query = text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_type = 'BASE TABLE'
                    ORDER BY table_name
                """)
                
                result = await session.execute(tables_query)
                existing_tables = [row[0] for row in result.fetchall()]
                
                logger.info(f"📊 Tabelas encontradas: {len(existing_tables)}")
                for table in existing_tables:
                    logger.info(f"   ✅ {table}")
                
                # Verificar tabelas necessárias
                missing_tables = []
                for required_table in self.required_tables:
                    if required_table not in existing_tables:
                        missing_tables.append(required_table)
                        logger.warning(f"   ❌ {required_table} - FALTANDO")
                    else:
                        logger.success(f"   ✅ {required_table} - EXISTE")
                
                return existing_tables, missing_tables
                
        except Exception as e:
            logger.error(f"❌ Erro ao verificar tabelas: {str(e)}")
            return [], self.required_tables
    
    async def check_alembic_status(self):
        """Verificar status das migrações do Alembic."""
        logger.info("🔄 VERIFICANDO STATUS DAS MIGRAÇÕES ALEMBIC")
        logger.info("=" * 50)
        
        try:
            import subprocess
            import os
            
            # Verificar se alembic.ini existe
            alembic_ini = Path("alembic.ini")
            if not alembic_ini.exists():
                logger.error("❌ arquivo alembic.ini não encontrado")
                return False
            
            # Verificar versão atual
            result = subprocess.run(
                ["alembic", "current"],
                capture_output=True,
                text=True,
                cwd=os.getcwd()
            )
            
            if result.returncode == 0:
                current_version = result.stdout.strip()
                logger.info(f"📌 Versão atual do banco: {current_version}")
                
                # Verificar se há migrações pendentes
                result = subprocess.run(
                    ["alembic", "heads"],
                    capture_output=True,
                    text=True,
                    cwd=os.getcwd()
                )
                
                if result.returncode == 0:
                    head_version = result.stdout.strip()
                    logger.info(f"📌 Versão mais recente disponível: {head_version}")
                    
                    if current_version == head_version:
                        logger.success("✅ Banco está atualizado")
                        return True
                    else:
                        logger.warning("⚠️ Banco precisa ser atualizado")
                        return False
                else:
                    logger.error(f"❌ Erro ao verificar versão head: {result.stderr}")
                    return False
            else:
                logger.error(f"❌ Erro ao verificar versão atual: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro ao verificar Alembic: {str(e)}")
            return False
    
    async def run_migrations(self):
        """Executar migrações do banco de dados."""
        logger.info("🚀 EXECUTANDO MIGRAÇÕES DO BANCO DE DADOS")
        logger.info("=" * 50)
        
        try:
            import subprocess
            import os
            
            # Executar upgrade
            logger.info("📈 Executando upgrade do banco...")
            result = subprocess.run(
                ["alembic", "upgrade", "head"],
                capture_output=True,
                text=True,
                cwd=os.getcwd()
            )
            
            if result.returncode == 0:
                logger.success("✅ Migrações executadas com sucesso")
                logger.info("📝 Output:")
                for line in result.stdout.split('\n'):
                    if line.strip():
                        logger.info(f"   {line}")
                return True
            else:
                logger.error("❌ Erro ao executar migrações")
                logger.error(f"📝 Erro: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro ao executar migrações: {str(e)}")
            return False
    
    async def create_initial_data(self):
        """Criar dados iniciais se necessário."""
        logger.info("🌱 VERIFICANDO DADOS INICIAIS")
        logger.info("=" * 50)
        
        try:
            from app.core.database import AsyncSessionLocal
            from sqlalchemy import text
            
            async with AsyncSessionLocal() as session:
                # Verificar se há usuários
                result = await session.execute(text("SELECT COUNT(*) FROM users"))
                user_count = result.scalar()
                
                if user_count == 0:
                    logger.info("👤 Nenhum usuário encontrado - criando usuário admin...")
                    
                    # Criar usuário admin básico
                    admin_query = text("""
                        INSERT INTO users (username, email, is_active, is_admin, created_at)
                        VALUES ('admin', 'admin@pdpj.local', true, true, NOW())
                        ON CONFLICT (username) DO NOTHING
                    """)
                    
                    await session.execute(admin_query)
                    await session.commit()
                    
                    logger.success("✅ Usuário admin criado")
                else:
                    logger.info(f"👤 {user_count} usuários encontrados")
                
                # Verificar se há processos
                result = await session.execute(text("SELECT COUNT(*) FROM processes"))
                process_count = result.scalar()
                logger.info(f"📄 {process_count} processos encontrados")
                
                # Verificar se há documentos
                result = await session.execute(text("SELECT COUNT(*) FROM documents"))
                document_count = result.scalar()
                logger.info(f"📎 {document_count} documentos encontrados")
                
                return True
                
        except Exception as e:
            logger.error(f"❌ Erro ao verificar dados iniciais: {str(e)}")
            return False
    
    async def validate_database_structure(self):
        """Validar estrutura final do banco."""
        logger.info("🔍 VALIDANDO ESTRUTURA FINAL DO BANCO")
        logger.info("=" * 50)
        
        try:
            from app.core.database import AsyncSessionLocal
            from sqlalchemy import text
            
            async with AsyncSessionLocal() as session:
                # Verificar estrutura das tabelas principais
                tables_to_check = {
                    'users': ['id', 'username', 'email', 'is_active', 'is_admin', 'created_at'],
                    'processes': ['id', 'process_number', 'court', 'created_at', 'updated_at'],
                    'documents': ['id', 'process_id', 'document_name', 'file_path', 'created_at']
                }
                
                all_valid = True
                
                for table_name, expected_columns in tables_to_check.items():
                    # Verificar se tabela existe
                    table_check = text("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_schema = 'public' 
                            AND table_name = :table_name
                        )
                    """)
                    
                    result = await session.execute(table_check, {"table_name": table_name})
                    table_exists = result.scalar()
                    
                    if not table_exists:
                        logger.error(f"❌ Tabela {table_name} não existe")
                        all_valid = False
                        continue
                    
                    # Verificar colunas
                    columns_query = text("""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_schema = 'public' 
                        AND table_name = :table_name
                        ORDER BY ordinal_position
                    """)
                    
                    result = await session.execute(columns_query, {"table_name": table_name})
                    existing_columns = [row[0] for row in result.fetchall()]
                    
                    missing_columns = []
                    for expected_col in expected_columns:
                        if expected_col not in existing_columns:
                            missing_columns.append(expected_col)
                    
                    if missing_columns:
                        logger.error(f"❌ Tabela {table_name} - colunas faltando: {missing_columns}")
                        all_valid = False
                    else:
                        logger.success(f"✅ Tabela {table_name} - estrutura válida")
                
                return all_valid
                
        except Exception as e:
            logger.error(f"❌ Erro ao validar estrutura: {str(e)}")
            return False
    
    async def run_full_setup(self):
        """Executar configuração completa do banco."""
        logger.info("🗄️ INICIANDO CONFIGURAÇÃO COMPLETA DO BANCO DE DADOS")
        logger.info("=" * 60)
        logger.info("")
        
        # Passo 1: Verificar conexão
        if not await self.check_database_connection():
            logger.error("💥 Falha na conexão com banco - abortando")
            return False
        logger.info("")
        
        # Passo 2: Verificar tabelas existentes
        existing_tables, missing_tables = await self.check_existing_tables()
        logger.info("")
        
        # Passo 3: Verificar status do Alembic
        alembic_ok = await self.check_alembic_status()
        logger.info("")
        
        # Passo 4: Executar migrações se necessário
        if missing_tables or not alembic_ok:
            logger.warning("⚠️ Migrações necessárias detectadas")
            if not await self.run_migrations():
                logger.error("💥 Falha nas migrações - abortando")
                return False
            logger.info("")
        else:
            logger.success("✅ Nenhuma migração necessária")
            logger.info("")
        
        # Passo 5: Verificar dados iniciais
        await self.create_initial_data()
        logger.info("")
        
        # Passo 6: Validar estrutura final
        if not await self.validate_database_structure():
            logger.error("💥 Estrutura do banco inválida")
            return False
        
        # Resumo final
        logger.success("🎉 CONFIGURAÇÃO DO BANCO CONCLUÍDA COM SUCESSO!")
        logger.info("=" * 60)
        logger.info("✅ Conexão com banco funcionando")
        logger.info("✅ Todas as tabelas necessárias existem")
        logger.info("✅ Migrações aplicadas (se necessário)")
        logger.info("✅ Dados iniciais verificados")
        logger.info("✅ Estrutura do banco validada")
        logger.info("")
        logger.info("🚀 Banco de dados pronto para uso!")
        logger.info("=" * 60)
        
        return True

async def main():
    """Função principal."""
    setup = DatabaseSetup()
    
    try:
        success = await setup.run_full_setup()
        if success:
            logger.success("🎯 Setup do banco concluído com sucesso!")
            return 0
        else:
            logger.error("💥 Setup do banco falhou!")
            return 1
    except KeyboardInterrupt:
        logger.warning("⚠️ Setup interrompido pelo usuário")
        return 1
    except Exception as e:
        logger.error(f"💥 Erro inesperado: {str(e)}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
