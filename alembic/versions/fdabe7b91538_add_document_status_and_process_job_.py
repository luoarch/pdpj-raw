"""Add document status and process job tracking with optimizations

Revision ID: fdabe7b91538
Revises: 928e2eac0eb7
Create Date: 2025-10-06 09:09:48.114086

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fdabe7b91538'
down_revision = '928e2eac0eb7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade database schema."""
    # Criar tipo ENUM para DocumentStatus
    documentstatus_enum = sa.Enum('PENDING', 'PROCESSING', 'AVAILABLE', 'FAILED', name='documentstatus', schema='pdpj')
    documentstatus_enum.create(op.get_bind(), checkfirst=True)
    
    # Adicionar novos campos à tabela documents
    op.add_column('documents', sa.Column('status', sa.Enum('PENDING', 'PROCESSING', 'AVAILABLE', 'FAILED', name='documentstatus', schema='pdpj'), nullable=False, server_default='PENDING'), schema='pdpj')
    op.add_column('documents', sa.Column('error_message', sa.Text(), nullable=True), schema='pdpj')
    op.add_column('documents', sa.Column('download_started_at', sa.DateTime(), nullable=True), schema='pdpj')
    op.add_column('documents', sa.Column('download_completed_at', sa.DateTime(), nullable=True), schema='pdpj')
    
    # Criar índices nos novos campos
    op.create_index(op.f('ix_pdpj_documents_status'), 'documents', ['status'], unique=False, schema='pdpj')
    op.create_index(op.f('ix_pdpj_documents_download_started_at'), 'documents', ['download_started_at'], unique=False, schema='pdpj')
    
    # Adicionar índice em process_id se não existir
    try:
        op.create_index(op.f('ix_pdpj_documents_process_id'), 'documents', ['process_id'], unique=False, schema='pdpj')
    except:
        pass  # Índice já existe
    
    # Criar nova tabela process_jobs
    op.create_table('process_jobs',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('job_id', sa.String(length=100), nullable=False),
        sa.Column('process_id', sa.BigInteger(), nullable=False),
        sa.Column('webhook_url', sa.Text(), nullable=True),
        sa.Column('webhook_sent', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('webhook_sent_at', sa.DateTime(), nullable=True),
        sa.Column('webhook_attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('webhook_last_error', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('total_documents', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('completed_documents', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('failed_documents', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('progress_percentage', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('job_metadata', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['process_id'], ['pdpj.processes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        schema='pdpj'
    )
    
    # Criar índices na nova tabela
    op.create_index(op.f('ix_pdpj_process_jobs_job_id'), 'process_jobs', ['job_id'], unique=True, schema='pdpj')
    op.create_index(op.f('ix_pdpj_process_jobs_process_id'), 'process_jobs', ['process_id'], unique=False, schema='pdpj')
    op.create_index(op.f('ix_pdpj_process_jobs_status'), 'process_jobs', ['status'], unique=False, schema='pdpj')
    
    # Sincronizar status de documentos existentes
    op.execute("""
        UPDATE pdpj.documents 
        SET status = CASE 
            WHEN downloaded = true THEN 'AVAILABLE'::pdpj.documentstatus
            ELSE 'PENDING'::pdpj.documentstatus
        END
    """)


def downgrade() -> None:
    """Downgrade database schema."""
    # Remover tabela process_jobs
    op.drop_index(op.f('ix_pdpj_process_jobs_status'), table_name='process_jobs', schema='pdpj')
    op.drop_index(op.f('ix_pdpj_process_jobs_process_id'), table_name='process_jobs', schema='pdpj')
    op.drop_index(op.f('ix_pdpj_process_jobs_job_id'), table_name='process_jobs', schema='pdpj')
    op.drop_table('process_jobs', schema='pdpj')
    
    # Remover índices dos novos campos em documents
    op.drop_index(op.f('ix_pdpj_documents_download_started_at'), table_name='documents', schema='pdpj')
    op.drop_index(op.f('ix_pdpj_documents_status'), table_name='documents', schema='pdpj')
    
    # Remover novos campos de documents
    op.drop_column('documents', 'download_completed_at', schema='pdpj')
    op.drop_column('documents', 'download_started_at', schema='pdpj')
    op.drop_column('documents', 'error_message', schema='pdpj')
    op.drop_column('documents', 'status', schema='pdpj')
    
    # Remover tipo ENUM
    sa.Enum(name='documentstatus', schema='pdpj').drop(op.get_bind(), checkfirst=True)
