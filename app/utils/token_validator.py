"""
Utilitário para validação de tokens JWT da API PDPJ.
"""

import json
import base64
from datetime import datetime
from typing import Dict, Any, Optional
from loguru import logger


class TokenValidationResult:
    """Resultado da validação de token."""
    
    def __init__(self):
        self.is_valid: bool = True
        self.is_expired: bool = False
        self.hours_remaining: Optional[float] = None
        self.issuer: Optional[str] = None
        self.is_pje_token: bool = False
        self.is_pdpj_token: bool = False
        self.allowed_origins: list = []
        self.user_name: Optional[str] = None
        self.user_email: Optional[str] = None
        self.warnings: list = []
        self.errors: list = []


class PDPJTokenValidator:
    """Validador de tokens JWT para a API PDPJ."""
    
    @staticmethod
    def validate_token(token: str, base_url: str = None) -> TokenValidationResult:
        """
        Validar token JWT da API PDPJ e detectar problemas comuns.
        
        Args:
            token: Token JWT para validar
            base_url: URL base da API (opcional, para validação de origins)
            
        Returns:
            TokenValidationResult com informações da validação
        """
        result = TokenValidationResult()
        
        try:
            if not token:
                result.is_valid = False
                result.errors.append("Token não fornecido")
                logger.error("❌ Token PDPJ não configurado")
                return result
            
            # Decodificar JWT para análise
            # Converter SecretStr para string se necessário
            if hasattr(token, 'get_secret_value'):
                token_str = token.get_secret_value()
            else:
                token_str = str(token)
            parts = token_str.split('.')
            if len(parts) != 3:
                result.is_valid = False
                result.warnings.append("Token não é um JWT válido")
                logger.warning("⚠️ Token não é um JWT válido")
                return result
            
            # Decodificar payload
            payload = parts[1]
            payload += '=' * (4 - len(payload) % 4)
            decoded = base64.urlsafe_b64decode(payload)
            payload_data = json.loads(decoded)
            
            # Verificar expiração
            if 'exp' in payload_data:
                exp_date = datetime.fromtimestamp(payload_data['exp'])
                now = datetime.now()
                
                if now > exp_date:
                    result.is_valid = False
                    result.is_expired = True
                    result.errors.append(f"Token expirado em {exp_date}")
                    logger.error(f"❌ Token PDPJ expirado em {exp_date}")
                    return result
                else:
                    hours_left = (exp_date - now).total_seconds() / 3600
                    result.hours_remaining = hours_left
                    logger.info(f"✅ Token PDPJ válido por mais {hours_left:.1f} horas")
            
            # Verificar issuer
            issuer = payload_data.get('iss', '')
            result.issuer = issuer
            
            if 'pje.jus.br' in issuer:
                result.is_pje_token = True
                # PJE tokens funcionam com PDPJ, apenas informativo
                logger.info("ℹ️ Token PJE detectado (compatível com PDPJ)")
                logger.info(f"   Issuer: {issuer}")
                if base_url:
                    logger.info(f"   Base URL configurada: {base_url}")
                logger.info("   ✅ Token PJE é compatível com a API PDPJ")
            elif 'pdpj.jus.br' in issuer:
                result.is_pdpj_token = True
                logger.info("✅ Token é do PDPJ (correto)")
            else:
                result.warnings.append(f"Issuer desconhecido: {issuer}")
                logger.warning(f"⚠️ Issuer desconhecido: {issuer}")
            
            # Verificar allowed-origins
            allowed_origins = payload_data.get('allowed-origins', [])
            result.allowed_origins = allowed_origins
            
            if allowed_origins:
                logger.info(f"🔍 Origins permitidos: {allowed_origins}")
                # Verificar se a base URL está nos origins (mais flexível)
                if base_url:
                    base_domain = base_url.replace('https://', '').replace('http://', '').split('/')[0]
                    origins_domains = [origin.replace('https://', '').replace('http://', '').split('/')[0] for origin in allowed_origins]
                    if base_domain not in origins_domains:
                        logger.info(f"ℹ️ Base URL {base_url} usa domínio diferente dos origins, mas pode funcionar")
                    else:
                        logger.info(f"✅ Base URL {base_url} compatível com origins permitidos")
            
            # Informações do usuário
            result.user_name = payload_data.get('name', 'N/A')
            result.user_email = payload_data.get('email', 'N/A')
            logger.info(f"👤 Usuário: {result.user_name} ({result.user_email})")
            
        except Exception as e:
            result.is_valid = False
            result.errors.append(f"Erro ao validar token: {e}")
            logger.warning(f"⚠️ Erro ao validar token: {e}")
        
        return result
    
    @staticmethod
    def validate_and_log(token: str, base_url: str = None) -> bool:
        """
        Validar token e fazer log dos resultados.
        
        Args:
            token: Token JWT para validar
            base_url: URL base da API (opcional)
            
        Returns:
            True se o token é válido, False caso contrário
        """
        result = PDPJTokenValidator.validate_token(token, base_url)
        
        # Log de resumo
        if result.is_valid:
            if result.is_pje_token:
                logger.info("✅ Token PJE válido (compatível com PDPJ)")
            elif result.is_pdpj_token:
                logger.info("✅ Token PDPJ válido e correto")
            else:
                logger.info("✅ Token válido")
        else:
            logger.error("❌ Token inválido")
        
        return result


# Função de conveniência para compatibilidade
def validate_pdpj_token(token: str, base_url: str = None) -> bool:
    """
    Função de conveniência para validar token PDPJ.
    
    Args:
        token: Token JWT para validar
        base_url: URL base da API (opcional)
        
    Returns:
        True se o token é válido, False caso contrário
    """
    return PDPJTokenValidator.validate_and_log(token, base_url)
