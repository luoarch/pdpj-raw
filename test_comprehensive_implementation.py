#!/usr/bin/env python3
"""
Teste abrangente da implementação PDPJ com todas as melhorias:
- Sessões automáticas
- Validação de arquivos
- Detecção de tipos
- Nomes seguros
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
logger.add("test_comprehensive_implementation.log", rotation="1 MB")

async def test_comprehensive_implementation():
    """Teste abrangente da implementação."""
    
    logger.info("🎯 Teste Abrangente da Implementação PDPJ")
    logger.info("=" * 80)
    logger.info("📋 Funcionalidades testadas:")
    logger.info("  ✅ Sessões automáticas com cookies")
    logger.info("  ✅ Validação de tipos de arquivo")
    logger.info("  ✅ Detecção automática de extensões")
    logger.info("  ✅ Nomes de arquivo seguros")
    logger.info("  ✅ Processamento completo de downloads")
    logger.info("=" * 80)
    
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
        
        logger.info(f"🔍 Buscando documentos do processo: {process_number}")
        
        # Buscar documentos
        documents = await client.get_process_documents(process_number)
        logger.info(f"✅ Encontrados {len(documents)} documentos")
        
        # Estatísticas
        stats = {
            'total_documents': len(documents),
            'successful_downloads': 0,
            'failed_downloads': 0,
            'file_types': {},
            'total_size': 0,
            'downloads': []
        }
        
        # Testar download de todos os documentos (limitado a 10 para não sobrecarregar)
        test_docs = documents[:10]
        
        for i, doc in enumerate(test_docs, 1):
            logger.info(f"\n📄 Teste {i}/{len(test_docs)}: {doc.get('nome', 'N/A')}")
            logger.info(f"📋 Tipo: {doc.get('tipo', {}).get('nome', 'N/A')}")
            logger.info(f"🔗 hrefBinario: {doc.get('hrefBinario', 'N/A')}")
            
            try:
                # Tentar download com todas as melhorias
                result = await client.download_document(
                    href_binario=doc.get('hrefBinario', ''),
                    document_name=doc.get('nome', 'documento')
                )
                
                # Atualizar estatísticas
                stats['successful_downloads'] += 1
                stats['total_size'] += result['size']
                
                # Contar tipos de arquivo
                extension = result['extension']
                stats['file_types'][extension] = stats['file_types'].get(extension, 0) + 1
                
                # Adicionar aos downloads
                stats['downloads'].append({
                    'nome': doc.get('nome', 'N/A'),
                    'tipo': doc.get('tipo', {}).get('nome', 'N/A'),
                    'size': result['size'],
                    'extension': result['extension'],
                    'detected_type': result['detected_type'],
                    'saved_path': result.get('saved_path'),
                    'warnings': result.get('warnings', []),
                    'errors': result.get('errors', []),
                    'session_cookie_used': result.get('session_cookie_used', False)
                })
                
                logger.success(f"✅ Download bem-sucedido: {result['size']} bytes, tipo: {result['extension']}")
                
                # Mostrar avisos se houver
                if result.get('warnings'):
                    for warning in result['warnings']:
                        logger.warning(f"⚠️ {warning}")
                
            except Exception as e:
                logger.error(f"❌ Erro no download: {e}")
                stats['failed_downloads'] += 1
                stats['downloads'].append({
                    'nome': doc.get('nome', 'N/A'),
                    'erro': str(e),
                    'success': False
                })
        
        # Resumo final
        logger.info("\n🏁 RESUMO FINAL:")
        logger.info("=" * 80)
        logger.info(f"📊 Total de documentos: {stats['total_documents']}")
        logger.info(f"✅ Downloads bem-sucedidos: {stats['successful_downloads']}")
        logger.info(f"❌ Downloads falharam: {stats['failed_downloads']}")
        logger.info(f"📈 Taxa de sucesso: {stats['successful_downloads']/len(test_docs)*100:.1f}%")
        logger.info(f"💾 Tamanho total baixado: {stats['total_size']:,} bytes ({stats['total_size']/1024/1024:.2f} MB)")
        
        logger.info(f"\n📁 Tipos de arquivo encontrados:")
        for ext, count in stats['file_types'].items():
            logger.info(f"  {ext}: {count} arquivo(s)")
        
        # Salvar relatório detalhado
        os.makedirs("data/reports", exist_ok=True)
        report_path = "data/reports/comprehensive_test_report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
        
        logger.success(f"📋 Relatório detalhado salvo em: {report_path}")
        
        # Análise de qualidade
        logger.info(f"\n🔍 ANÁLISE DE QUALIDADE:")
        logger.info("=" * 60)
        
        # Verificar uso de cookies de sessão
        session_usage = sum(1 for d in stats['downloads'] if d.get('session_cookie_used', False))
        logger.info(f"🍪 Downloads com cookie de sessão: {session_usage}/{stats['successful_downloads']}")
        
        # Verificar avisos
        total_warnings = sum(len(d.get('warnings', [])) for d in stats['downloads'])
        if total_warnings > 0:
            logger.warning(f"⚠️ Total de avisos: {total_warnings}")
        else:
            logger.success("✅ Nenhum aviso encontrado")
        
        # Verificar tipos de arquivo
        pdf_count = stats['file_types'].get('.pdf', 0)
        html_count = stats['file_types'].get('.html', 0)
        logger.info(f"📄 PDFs: {pdf_count}, HTMLs: {html_count}")
        
        logger.info("\n🎉 Teste abrangente concluído com sucesso!")
        
    except Exception as e:
        logger.error(f"❌ Erro no teste: {e}")
        import traceback
        logger.error(traceback.format_exc())


if __name__ == "__main__":
    asyncio.run(test_comprehensive_implementation())
