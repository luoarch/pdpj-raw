"""
Utilitários para validação e processamento de arquivos.
"""

import os
import mimetypes
from typing import Optional, Dict, Any, Tuple
from loguru import logger


class FileValidator:
    """Validador de tipos de arquivo e conteúdo."""
    
    # Mapeamento de tipos MIME para extensões
    MIME_TO_EXTENSION = {
        'application/pdf': '.pdf',
        'text/html': '.html',
        'text/plain': '.txt',
        'application/msword': '.doc',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
        'image/jpeg': '.jpg',
        'image/png': '.png',
        'image/gif': '.gif',
        'application/zip': '.zip',
        'application/x-rar-compressed': '.rar',
    }
    
    # Assinaturas de arquivo (magic numbers)
    FILE_SIGNATURES = {
        b'%PDF': '.pdf',
        b'<!DOCTYPE html': '.html',
        b'<html': '.html',
        b'PK\x03\x04': '.zip',  # ZIP files
        b'Rar!': '.rar',  # RAR files
        b'\xff\xd8\xff': '.jpg',  # JPEG
        b'\x89PNG\r\n\x1a\n': '.png',  # PNG
        b'GIF87a': '.gif',  # GIF87a
        b'GIF89a': '.gif',  # GIF89a
    }
    
    @classmethod
    def detect_file_type(cls, content: bytes, content_type: Optional[str] = None) -> Tuple[str, str]:
        """
        Detectar tipo de arquivo baseado no conteúdo e Content-Type.
        
        Args:
            content: Conteúdo binário do arquivo
            content_type: Content-Type do header HTTP
            
        Returns:
            Tupla (extensão, tipo_detectado)
        """
        # Primeiro, tentar detectar pela assinatura do arquivo
        for signature, extension in cls.FILE_SIGNATURES.items():
            if content.startswith(signature):
                return extension, f"Detectado por assinatura: {signature}"
        
        # Se não encontrou assinatura, usar Content-Type
        if content_type:
            extension = cls.MIME_TO_EXTENSION.get(content_type)
            if extension:
                return extension, f"Detectado por Content-Type: {content_type}"
        
        # Fallback: tentar detectar pelo conteúdo
        if content.startswith(b'<'):
            return '.html', "Detectado como HTML pelo conteúdo"
        
        # Se não conseguiu detectar, usar extensão genérica
        return '.bin', "Tipo não detectado, usando .bin"
    
    @classmethod
    def get_safe_filename(cls, original_name: str, detected_extension: str) -> str:
        """
        Gerar nome de arquivo seguro.
        
        Args:
            original_name: Nome original do arquivo
            detected_extension: Extensão detectada
            
        Returns:
            Nome de arquivo seguro
        """
        # Remover caracteres perigosos
        safe_name = "".join(c for c in original_name if c.isalnum() or c in (' ', '-', '_', '.'))
        safe_name = safe_name.strip()
        
        # Se o nome estiver vazio, usar nome genérico
        if not safe_name:
            safe_name = "documento"
        
        # Garantir que tenha a extensão correta
        if not safe_name.lower().endswith(detected_extension.lower()):
            # Remover extensão existente se houver
            name_without_ext = safe_name.rsplit('.', 1)[0] if '.' in safe_name else safe_name
            safe_name = f"{name_without_ext}{detected_extension}"
        
        return safe_name
    
    @classmethod
    def validate_document_content(cls, content: bytes, expected_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Validar conteúdo do documento.
        
        Args:
            content: Conteúdo binário
            expected_type: Tipo esperado (opcional)
            
        Returns:
            Dicionário com informações de validação
        """
        result = {
            'is_valid': True,
            'size': len(content),
            'detected_type': None,
            'extension': None,
            'warnings': [],
            'errors': []
        }
        
        # Verificar se o conteúdo não está vazio
        if len(content) == 0:
            result['is_valid'] = False
            result['errors'].append("Arquivo vazio")
            return result
        
        # Detectar tipo do arquivo
        extension, detection_method = cls.detect_file_type(content)
        result['detected_type'] = detection_method
        result['extension'] = extension
        
        # Verificar se é HTML do portal (erro comum)
        if content.startswith(b'<html') and b'portal' in content.lower()[:1000]:
            result['warnings'].append("Possível HTML do portal web em vez do documento")
        
        # Verificar tamanho mínimo
        if len(content) < 100:
            result['warnings'].append("Arquivo muito pequeno, pode estar corrompido")
        
        # Verificar se corresponde ao tipo esperado
        if expected_type:
            if expected_type.lower() == 'pdf' and not content.startswith(b'%PDF'):
                result['warnings'].append("Esperado PDF mas não é um PDF válido")
            elif expected_type.lower() == 'html' and not content.startswith(b'<'):
                result['warnings'].append("Esperado HTML mas não é HTML válido")
        
        return result
    
    @classmethod
    def save_document(cls, content: bytes, filename: str, directory: str = "downloads") -> str:
        """
        Salvar documento com validação e nome seguro.
        
        Args:
            content: Conteúdo binário
            filename: Nome do arquivo
            directory: Diretório de destino
            
        Returns:
            Caminho do arquivo salvo
        """
        # Criar diretório se não existir
        os.makedirs(directory, exist_ok=True)
        
        # Detectar tipo e gerar nome seguro
        extension, _ = cls.detect_file_type(content)
        safe_filename = cls.get_safe_filename(filename, extension)
        
        # Caminho completo
        file_path = os.path.join(directory, safe_filename)
        
        # Salvar arquivo
        with open(file_path, 'wb') as f:
            f.write(content)
        
        logger.info(f"💾 Arquivo salvo: {file_path} ({len(content)} bytes)")
        return file_path


# Função de conveniência
def process_document_download(content: bytes, original_name: str, content_type: Optional[str] = None, 
                            directory: str = "downloads") -> Dict[str, Any]:
    """
    Processar download de documento com validação completa.
    
    Args:
        content: Conteúdo binário
        original_name: Nome original
        content_type: Content-Type
        directory: Diretório de destino
        
    Returns:
        Dicionário com informações do processamento
    """
    # Validar conteúdo
    validation = FileValidator.validate_document_content(content, content_type)
    
    # Salvar arquivo
    if validation['is_valid']:
        file_path = FileValidator.save_document(content, original_name, directory)
        validation['saved_path'] = file_path
    else:
        validation['saved_path'] = None
    
    return validation
