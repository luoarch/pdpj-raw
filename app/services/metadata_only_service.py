"""
Serviço para extrair apenas metadados dos documentos PDPJ.
Como a API não suporta download direto, focamos nos metadados úteis.
"""

from typing import List, Dict, Any, Optional
from loguru import logger
from datetime import datetime
import json


class MetadataOnlyService:
    """Serviço para extrair metadados de documentos sem tentar download."""
    
    def __init__(self):
        self.logger = logger
    
    def extract_document_metadata(self, process_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extrai metadados úteis dos documentos de um processo.
        
        Args:
            process_data: Dados completos do processo da API PDPJ
            
        Returns:
            Lista de metadados dos documentos
        """
        try:
            documents = process_data.get("documentos", [])
            metadata_list = []
            
            for doc in documents:
                metadata = self._extract_single_document_metadata(doc)
                if metadata:
                    metadata_list.append(metadata)
            
            self.logger.info(f"✅ Extraídos metadados de {len(metadata_list)} documentos")
            return metadata_list
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao extrair metadados: {e}")
            return []
    
    def _extract_single_document_metadata(self, doc: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extrai metadados de um único documento."""
        try:
            # Informações básicas
            metadata = {
                "sequencia": doc.get("sequencia"),
                "nome": doc.get("nome"),
                "data_juntada": doc.get("dataHoraJuntada"),
                "nivel_sigilo": doc.get("nivelSigilo"),
                "id_codex": doc.get("idCodex"),
                "id_origem": doc.get("idOrigem"),
            }
            
            # Informações do tipo
            tipo_info = doc.get("tipo", {})
            if tipo_info:
                metadata.update({
                    "tipo_nome": tipo_info.get("nome"),
                    "tipo_codigo": tipo_info.get("codigo"),
                    "tipo_id_codex": tipo_info.get("idCodex"),
                    "tipo_id_origem": tipo_info.get("idOrigem"),
                })
            
            # Informações do arquivo
            arquivo_info = doc.get("arquivo", {})
            if arquivo_info:
                metadata.update({
                    "tipo_mime": arquivo_info.get("tipo"),
                    "tamanho_bytes": arquivo_info.get("tamanho"),
                    "quantidade_paginas": arquivo_info.get("quantidadePaginas"),
                    "quantidade_imagens": arquivo_info.get("quantidadeImagens"),
                    "tamanho_texto": arquivo_info.get("tamanhoTexto"),
                })
            
            # URLs (para referência, mesmo que não funcionem para download direto)
            metadata.update({
                "href_binario": doc.get("hrefBinario"),
                "href_texto": doc.get("hrefTexto"),
                "url_binario": f"https://portaldeservicos.pdpj.jus.br{doc.get('hrefBinario', '')}" if doc.get("hrefBinario") else None,
                "url_texto": f"https://portaldeservicos.pdpj.jus.br{doc.get('hrefTexto', '')}" if doc.get("hrefTexto") else None,
            })
            
            # Informações adicionais úteis
            metadata.update({
                "download_disponivel": False,  # Sempre False para PDPJ
                "motivo_limite": "API PDPJ não suporta download direto - redireciona para portal web",
                "data_extracao": datetime.now().isoformat(),
            })
            
            return metadata
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao extrair metadados do documento: {e}")
            return None
    
    def format_document_summary(self, metadata_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Formata um resumo dos documentos para apresentação.
        
        Args:
            metadata_list: Lista de metadados dos documentos
            
        Returns:
            Resumo formatado
        """
        try:
            if not metadata_list:
                return {"total": 0, "documentos": [], "resumo": "Nenhum documento encontrado"}
            
            # Estatísticas gerais
            total_docs = len(metadata_list)
            total_size = sum(doc.get("tamanho_bytes", 0) for doc in metadata_list)
            
            # Contagem por tipo
            tipos = {}
            for doc in metadata_list:
                tipo = doc.get("tipo_nome", "Desconhecido")
                tipos[tipo] = tipos.get(tipo, 0) + 1
            
            # Documentos mais recentes
            docs_ordenados = sorted(
                metadata_list, 
                key=lambda x: x.get("data_juntada", ""), 
                reverse=True
            )
            
            resumo = {
                "total_documentos": total_docs,
                "tamanho_total_bytes": total_size,
                "tamanho_total_mb": round(total_size / (1024 * 1024), 2),
                "tipos_documentos": tipos,
                "documentos_recentes": docs_ordenados[:5],  # 5 mais recentes
                "limite_download": "API PDPJ não suporta download direto",
                "recomendacao": "Acesse o portal web para download dos documentos",
                "data_geracao": datetime.now().isoformat()
            }
            
            return resumo
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao formatar resumo: {e}")
            return {"erro": str(e)}
    
    def save_metadata_to_file(self, metadata_list: List[Dict[str, Any]], filename: str) -> bool:
        """
        Salva metadados em arquivo JSON.
        
        Args:
            metadata_list: Lista de metadados
            filename: Nome do arquivo para salvar
            
        Returns:
            True se salvou com sucesso, False caso contrário
        """
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(metadata_list, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"✅ Metadados salvos em {filename}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao salvar metadados: {e}")
            return False


# Exemplo de uso
if __name__ == "__main__":
    # Exemplo de dados de processo
    exemplo_processo = {
        "documentos": [
            {
                "sequencia": 1,
                "nome": "Petição inicial.pdf",
                "dataHoraJuntada": "2025-01-30T13:10:52.632",
                "nivelSigilo": "PUBLICO",
                "idCodex": 23675888974,
                "idOrigem": "352172548",
                "tipo": {
                    "codigo": 202,
                    "nome": "Petição inicial",
                    "idCodex": 119551,
                    "idOrigem": "12"
                },
                "hrefBinario": "/processos/5000315-75.2025.4.03.6327/documentos/266683ef-f200-52d4-9172-19e3dc3c567d/binario",
                "hrefTexto": "/processos/5000315-75.2025.4.03.6327/documentos/266683ef-f200-52d4-9172-19e3dc3c567d/texto",
                "arquivo": {
                    "tipo": "application/pdf",
                    "tamanho": 279343,
                    "quantidadePaginas": 0,
                    "quantidadeImagens": 0,
                    "tamanhoTexto": 34414
                }
            }
        ]
    }
    
    # Testar o serviço
    service = MetadataOnlyService()
    metadata = service.extract_document_metadata(exemplo_processo)
    resumo = service.format_document_summary(metadata)
    
    print("📊 Metadados extraídos:")
    print(json.dumps(metadata, indent=2, ensure_ascii=False))
    
    print("\n📋 Resumo:")
    print(json.dumps(resumo, indent=2, ensure_ascii=False))
