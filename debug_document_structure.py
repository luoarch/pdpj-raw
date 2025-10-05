#!/usr/bin/env python3
"""
Debug da estrutura de documentos retornada pela API.
"""

import asyncio
import os
import json
from loguru import logger
from app.services.pdpj_client import PDPJClient
from dotenv import load_dotenv
from pydantic import SecretStr

# Carregar variáveis do .env
load_dotenv()

# Configurar logging
logger.add("debug_document_structure.log", rotation="1 MB")

async def debug_document_structure():
    """Debug da estrutura de documentos."""
    
    logger.info("🔍 Debug da Estrutura de Documentos")
    logger.info("=" * 60)
    
    try:
        # Configurações do .env
        token = os.getenv("PDPJ_API_TOKEN")
        if not token:
            logger.error("❌ PDPJ_API_TOKEN não encontrado no .env")
            return
        
        # Atualizar o token no settings
        from app.core.config import settings
        settings.pdpj_api_token = SecretStr(token)
        
        client = PDPJClient()
        
        # Processo de teste
        process_number = "5000315-75.2025.4.03.6327"
        
        logger.info(f"🔍 Buscando dados completos do processo: {process_number}")
        
        # Buscar dados completos
        full_data = await client.get_process_full(process_number)
        
        logger.info(f"✅ Dados obtidos: {len(str(full_data))} caracteres")
        
        # Salvar dados completos para análise
        os.makedirs("data/debug", exist_ok=True)
        with open("data/debug/full_process_data.json", "w", encoding="utf-8") as f:
            json.dump(full_data, f, indent=2, ensure_ascii=False)
        
        logger.info("💾 Dados salvos em data/debug/full_process_data.json")
        
        # Analisar estrutura
        logger.info("\n📊 ANÁLISE DA ESTRUTURA:")
        logger.info("=" * 60)
        
        # Verificar chaves principais
        logger.info(f"🔑 Chaves principais: {list(full_data.keys())}")
        
        # Verificar tramitações
        tramitacoes = full_data.get("tramitacoes", [])
        logger.info(f"📋 Número de tramitações: {len(tramitacoes)}")
        
        if tramitacoes:
            logger.info(f"🔍 Primeira tramitação - chaves: {list(tramitacoes[0].keys())}")
            
            # Verificar documentos na primeira tramitação
            docs = tramitacoes[0].get("documentos", [])
            logger.info(f"📄 Documentos na primeira tramitação: {len(docs)}")
            
            if docs:
                logger.info(f"🔍 Primeiro documento - chaves: {list(docs[0].keys())}")
                logger.info(f"📄 Nome do primeiro documento: {docs[0].get('nome', 'N/A')}")
        
        # Verificar se há documentos diretamente no processo
        documentos_diretos = full_data.get("documentos", [])
        logger.info(f"📄 Documentos diretos no processo: {len(documentos_diretos)}")
        
        # Verificar tramitacaoAtual
        tramitacao_atual = full_data.get("tramitacaoAtual", {})
        logger.info(f"📋 Tramitação atual - chaves: {list(tramitacao_atual.keys())}")
        
        docs_atual = tramitacao_atual.get("documentos", [])
        logger.info(f"📄 Documentos na tramitação atual: {len(docs_atual)}")
        
        # Contar total de documentos em todas as tramitações
        total_docs = 0
        for i, tram in enumerate(tramitacoes):
            docs = tram.get("documentos", [])
            total_docs += len(docs)
            if docs:
                logger.info(f"📋 Tramitação {i+1}: {len(docs)} documentos")
        
        logger.info(f"📊 Total de documentos em todas as tramitações: {total_docs}")
        
        # Se não encontrou documentos, mostrar estrutura completa
        if total_docs == 0:
            logger.warning("⚠️ Nenhum documento encontrado. Estrutura completa:")
            logger.info(json.dumps(full_data, indent=2, ensure_ascii=False)[:2000] + "...")
        
    except Exception as e:
        logger.error(f"❌ Erro no debug: {e}")
        import traceback
        logger.error(traceback.format_exc())


if __name__ == "__main__":
    asyncio.run(debug_document_structure())
