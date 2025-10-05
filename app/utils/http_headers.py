"""
Configuração centralizada de headers HTTP para diferentes tipos de requisições.
"""

from typing import Dict, Any, Optional
from datetime import datetime


class HTTPHeadersConfig:
    """Configuração centralizada de headers HTTP."""
    
    @staticmethod
    def get_default_headers(token: str) -> Dict[str, str]:
        """Headers padrão para requisições da API PDPJ."""
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "PDPJ-API-Client/1.0",
            "Accept": "application/json",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache"
        }
    
    @staticmethod
    def get_browser_headers(token: str, session_cookie: Optional[str] = None, 
                          process_number: Optional[str] = None) -> Dict[str, str]:
        """Headers que simulam navegador para downloads de documentos."""
        headers = {
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "en-US,en;q=0.9,pt;q=0.8",
            "authorization": f"Bearer {token}",
            "priority": "u=1, i",
            "sec-ch-ua": '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"macOS"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
        }
        
        # Adicionar cookie se fornecido
        if session_cookie:
            headers["cookie"] = f"JSESSIONID={session_cookie}"
        
        # Adicionar referer se processo fornecido
        if process_number:
            headers["referer"] = f"https://portaldeservicos.pdpj.jus.br/consulta/autosdigitais?processo={process_number}&dataDistribuicao=20250130131052"
        
        return headers
    
    @staticmethod
    def get_session_creation_headers(token: str) -> Dict[str, str]:
        """Headers para criação de sessão no portal."""
        return {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "pt-BR,pt;q=0.9,en;q=0.8",
            "authorization": f"Bearer {token}",
            "sec-ch-ua": '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"macOS"',
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "none",
            "sec-fetch-user": "?1",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
        }
    
    @staticmethod
    def get_health_check_headers(token: str) -> Dict[str, str]:
        """Headers para health check da API."""
        return {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "User-Agent": "PDPJ-Health-Check/1.0"
        }
    
    @staticmethod
    def update_headers_with_custom(original_headers: Dict[str, str], 
                                 custom_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """Atualizar headers originais com headers customizados."""
        if not custom_headers:
            return original_headers
        
        updated_headers = original_headers.copy()
        updated_headers.update(custom_headers)
        return updated_headers
    
    @staticmethod
    def get_headers_for_environment(environment: str, token: str) -> Dict[str, str]:
        """Obter headers apropriados para o ambiente (dev, staging, prod)."""
        base_headers = HTTPHeadersConfig.get_default_headers(token)
        
        if environment == "development":
            base_headers["X-Debug-Mode"] = "true"
            base_headers["X-Environment"] = "dev"
        elif environment == "staging":
            base_headers["X-Environment"] = "staging"
        elif environment == "production":
            base_headers["X-Environment"] = "prod"
            # Remover headers de debug se existirem
            base_headers.pop("X-Debug-Mode", None)
        
        return base_headers


# Funções de conveniência
def get_api_headers(token: str, custom_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """Obter headers para requisições da API."""
    headers = HTTPHeadersConfig.get_default_headers(token)
    return HTTPHeadersConfig.update_headers_with_custom(headers, custom_headers)


def get_download_headers(token: str, session_cookie: Optional[str] = None, 
                        process_number: Optional[str] = None) -> Dict[str, str]:
    """Obter headers para download de documentos."""
    return HTTPHeadersConfig.get_browser_headers(token, session_cookie, process_number)


def get_session_headers(token: str) -> Dict[str, str]:
    """Obter headers para criação de sessão."""
    return HTTPHeadersConfig.get_session_creation_headers(token)
