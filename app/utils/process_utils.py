"""Utilitários para processamento de números de processo judicial."""

import re
from typing import Optional


def normalize_process_number(process_number: str) -> str:
    """
    Normaliza um número de processo removendo pontos, hífens e espaços.
    
    Args:
        process_number: Número do processo (ex: "1000145-91.2023.8.26.0597")
        
    Returns:
        Número normalizado (ex: "10001459120238260597")
    """
    if not process_number:
        return ""
    
    # Remove pontos, hífens, espaços e outros caracteres não numéricos
    normalized = re.sub(r'[^\d]', '', process_number)
    
    return normalized


def format_process_number(process_number: str) -> str:
    """
    Formata um número de processo normalizado para exibição.
    
    Args:
        process_number: Número normalizado (ex: "10001459120238260597")
        
    Returns:
        Número formatado (ex: "1000145-91.2023.8.26.0597")
    """
    if not process_number or len(process_number) < 20:
        return process_number
    
    # Formato: NNNNNNN-DD.AAAA.J.TR.OOOO
    # Exemplo: 1000145-91.2023.8.26.0597
    if len(process_number) == 20:
        return f"{process_number[:7]}-{process_number[7:9]}.{process_number[9:13]}.{process_number[13:14]}.{process_number[14:16]}.{process_number[16:20]}"
    
    return process_number


def validate_process_number(process_number: str) -> bool:
    """
    Valida se um número de processo tem o formato correto.
    
    Args:
        process_number: Número do processo
        
    Returns:
        True se válido, False caso contrário
    """
    if not process_number:
        return False
    
    # Normalizar primeiro
    normalized = normalize_process_number(process_number)
    
    # Deve ter exatamente 20 dígitos
    return len(normalized) == 20 and normalized.isdigit()
