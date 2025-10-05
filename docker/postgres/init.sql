-- Script de inicialização do banco de dados PostgreSQL
-- Este arquivo é executado automaticamente quando o container PostgreSQL é criado

-- Criar extensões necessárias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Criar schema para a aplicação
CREATE SCHEMA IF NOT EXISTS pdpj;

-- Configurar timezone
SET timezone = 'America/Sao_Paulo';

-- Log da inicialização
DO $$
BEGIN
    RAISE NOTICE 'Banco de dados PDPJ inicializado com sucesso!';
END $$;
