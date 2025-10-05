"""
Gerenciador de sessões para a API PDPJ.
Mantém cookies de sessão ativos para melhorar taxa de sucesso nos downloads.
"""

import asyncio
import httpx
from typing import Optional, Dict, Any
from loguru import logger
from datetime import datetime, timedelta
import re
import hashlib


class SessionManager:
    """Gerenciador de sessões para manter cookies ativos com cache inteligente."""
    
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url
        self.token = token
        self.session_cookie: Optional[str] = None
        self.session_expires: Optional[datetime] = None
        self._lock = asyncio.Lock()
        
        # Cache de sessões por token (para múltiplas instâncias)
        self._session_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_ttl = timedelta(minutes=25)  # TTL menor que expiração real (30min)
        
    async def get_session_cookie(self) -> Optional[str]:
        """Obter cookie de sessão ativo ou criar um novo com cache inteligente."""
        async with self._lock:
            # Gerar chave de cache baseada no token
            token_hash = hashlib.md5(self.token.encode()).hexdigest()
            
            # Verificar cache global primeiro
            if token_hash in self._session_cache:
                cached_session = self._session_cache[token_hash]
                if datetime.now() < cached_session['expires']:
                    logger.debug(f"🍪 Usando cookie de sessão do cache: {cached_session['cookie'][:20]}...")
                    return cached_session['cookie']
                else:
                    # Cache expirado, remover
                    del self._session_cache[token_hash]
            
            # Verificar se temos um cookie válido local
            if self.session_cookie and self.session_expires and datetime.now() < self.session_expires:
                logger.debug(f"🍪 Usando cookie de sessão local: {self.session_cookie[:20]}...")
                # Atualizar cache global
                self._session_cache[token_hash] = {
                    'cookie': self.session_cookie,
                    'expires': self.session_expires
                }
                return self.session_cookie
            
            # Criar nova sessão
            await self._create_new_session()
            
            # Atualizar cache global se sessão foi criada com sucesso
            if self.session_cookie and self.session_expires:
                self._session_cache[token_hash] = {
                    'cookie': self.session_cookie,
                    'expires': self.session_expires
                }
            
            return self.session_cookie
    
    async def _create_new_session(self):
        """Criar uma nova sessão acessando a página do portal."""
        try:
            logger.info("🔄 Criando nova sessão...")
            
            # Headers para simular navegador
            headers = {
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "accept-encoding": "gzip, deflate, br, zstd",
                "accept-language": "pt-BR,pt;q=0.9,en;q=0.8",
                "authorization": f"Bearer {self.token}",
                "sec-ch-ua": '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"macOS"',
                "sec-fetch-dest": "document",
                "sec-fetch-mode": "navigate",
                "sec-fetch-site": "none",
                "sec-fetch-user": "?1",
                "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
            }
            
            # Acessar página principal do portal para estabelecer sessão
            portal_url = f"{self.base_url.replace('/api/v2', '')}/consulta/autosdigitais"
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(portal_url, headers=headers)
                
                if response.status_code == 200:
                    # Extrair JSESSIONID dos cookies
                    set_cookies = response.headers.get_list('set-cookie')
                    for cookie in set_cookies:
                        if 'JSESSIONID=' in cookie:
                            # Extrair JSESSIONID
                            match = re.search(r'JSESSIONID=([^;]+)', cookie)
                            if match:
                                self.session_cookie = match.group(1)
                                # Sessão válida por 30 minutos
                                self.session_expires = datetime.now() + timedelta(minutes=30)
                                logger.success(f"✅ Nova sessão criada: {self.session_cookie[:20]}...")
                                return
                    
                    logger.warning("⚠️ Sessão criada mas JSESSIONID não encontrado")
                else:
                    logger.error(f"❌ Erro ao criar sessão: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"❌ Erro ao criar nova sessão: {e}")
    
    async def refresh_session(self):
        """Forçar renovação da sessão."""
        async with self._lock:
            self.session_cookie = None
            self.session_expires = None
            await self._create_new_session()
    
    def is_session_valid(self) -> bool:
        """Verificar se a sessão atual é válida."""
        return (self.session_cookie is not None and 
                self.session_expires is not None and 
                datetime.now() < self.session_expires)


# Instância global do gerenciador de sessões
_session_manager: Optional[SessionManager] = None


def get_session_manager(base_url: str, token: str) -> SessionManager:
    """Obter instância global do gerenciador de sessões."""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager(base_url, token)
    return _session_manager


async def get_active_session_cookie(base_url: str, token: str) -> Optional[str]:
    """Obter cookie de sessão ativo."""
    manager = get_session_manager(base_url, token)
    return await manager.get_session_cookie()
