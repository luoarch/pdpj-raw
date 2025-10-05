# PDPJ Client - Guia Completo de Uso

## 📋 Visão Geral

O **PDPJClient** é um cliente otimizado para integração com a API PDPJ, desenvolvido com foco em alta performance, robustez e facilidade de uso. Inclui funcionalidades ultra-fast, controle de concorrência, cache inteligente e monitoramento avançado.

## 🚀 Características Principais

- **✅ Cliente Consolidado**: Unifica funcionalidades básicas e ultra-fast
- **✅ Controle de Concorrência**: Semáforos para limitar requisições simultâneas
- **✅ Cache de Sessão**: Cache inteligente com TTL para cookies de sessão
- **✅ Headers Centralizados**: Configuração centralizada de headers HTTP
- **✅ Timeouts Configuráveis**: Timeouts flexíveis via settings
- **✅ Download em Lote**: Paralelização otimizada com `asyncio.gather`
- **✅ Métricas Avançadas**: Monitoramento com alertas críticos
- **✅ Tratamento Robusto**: Tratamento sofisticado de erros e retry
- **✅ Validação de Token**: Validação JWT com diagnóstico detalhado

## 📦 Instalação e Configuração

### 1. Configuração Básica

```python
from app.services.pdpj_client import pdpj_client
from app.core.config import settings

# O cliente é inicializado automaticamente com as configurações do settings
# Configurações disponíveis em app/core/config.py:

# Timeouts
settings.pdpj_request_timeout = 30.0      # Timeout para requisições
settings.pdpj_download_timeout = 60.0     # Timeout para downloads
settings.pdpj_max_retries = 3             # Número de tentativas
settings.pdpj_retry_delay = 1.0           # Delay entre tentativas

# Conexões HTTP
settings.pdpj_max_connections = 10        # Max conexões simultâneas
settings.pdpj_max_keepalive = 5           # Max conexões keep-alive

# Concorrência
settings.max_concurrent_requests = 100    # Max requisições simultâneas
settings.max_concurrent_downloads = 50    # Max downloads simultâneos
```

### 2. Configuração de Token

```python
from pydantic import SecretStr
from app.core.config import settings

# Configurar token PDPJ
settings.pdpj_api_token = SecretStr("seu_token_jwt_aqui")
```

## 🔧 Uso Básico

### 1. Buscar Dados de Processo

```python
import asyncio

async def buscar_processo():
    # Buscar dados completos do processo
    processo = await pdpj_client.get_process_full("5000315-75.2025.4.03.6327")
    print(f"Processo: {processo['numeroProcesso']}")
    
    # Buscar apenas capa/resumo
    capa = await pdpj_client.get_process_cover("5000315-75.2025.4.03.6327")
    print(f"Classe: {capa.get('classe', 'N/A')}")

# Executar
asyncio.run(buscar_processo())
```

### 2. Buscar Documentos

```python
async def buscar_documentos():
    # Buscar lista de documentos
    documentos = await pdpj_client.get_process_documents("5000315-75.2025.4.03.6327")
    
    print(f"Encontrados {len(documentos)} documentos:")
    for doc in documentos:
        print(f"- {doc['nome']} ({doc['tipo']['nome']})")
        print(f"  hrefBinario: {doc.get('hrefBinario', 'N/A')}")

asyncio.run(buscar_documentos())
```

### 3. Download de Documento Individual

```python
async def download_documento():
    # Download com validação automática
    resultado = await pdpj_client.download_document(
        href_binario="/processos/5000315-75.2025.4.03.6327/documentos/abc123/binario",
        document_name="sentenca.pdf"
    )
    
    print(f"Download concluído:")
    print(f"- Tamanho: {resultado['size']} bytes")
    print(f"- Tipo: {resultado['extension']}")
    print(f"- Arquivo salvo: {resultado['saved_path']}")
    print(f"- Validação: {resultado['is_valid']}")

asyncio.run(download_documento())
```

## 🚀 Uso Avançado

### 1. Download em Lote Otimizado

```python
async def download_lote():
    # Preparar lista de documentos
    documentos = await pdpj_client.get_process_documents("5000315-75.2025.4.03.6327")
    
    # Preparar requests para download em lote
    batch_requests = []
    for doc in documentos[:5]:  # Primeiros 5 documentos
        batch_requests.append({
            'hrefBinario': doc.get('hrefBinario', ''),
            'document_name': doc.get('nome', 'documento')
        })
    
    # Executar download em lote (paralelo)
    resultados = await pdpj_client.batch_download_documents(batch_requests)
    
    # Analisar resultados
    sucessos = sum(1 for r in resultados if r.get('success', True))
    falhas = len(resultados) - sucessos
    
    print(f"Download em lote concluído:")
    print(f"- Sucessos: {sucessos}")
    print(f"- Falhas: {falhas}")
    print(f"- Taxa de sucesso: {sucessos/len(resultados)*100:.1f}%")

asyncio.run(download_lote())
```

### 2. Monitoramento e Métricas

```python
async def monitorar_performance():
    # Executar algumas operações
    await pdpj_client.get_process_documents("5000315-75.2025.4.03.6327")
    
    # Obter métricas detalhadas
    metrics = pdpj_client.get_metrics()
    
    print("📊 Métricas de Performance:")
    print(f"- Requisições feitas: {metrics['requests_made']}")
    print(f"- Downloads bem-sucedidos: {metrics['downloads_successful']}")
    print(f"- Downloads falharam: {metrics['downloads_failed']}")
    print(f"- Taxa de sucesso: {metrics['success_rate']*100:.1f}%")
    print(f"- Taxa de erro: {metrics['error_rate']*100:.1f}%")
    print(f"- Tempo médio de requisição: {metrics['avg_request_time']:.3f}s")
    print(f"- Tempo médio de download: {metrics['avg_download_time']:.3f}s")
    
    # Status de saúde
    print(f"\n🏥 Status de Saúde: {metrics['health_status']}")
    
    # Alertas críticos
    if metrics['alerts']:
        print("\n🚨 Alertas:")
        for alert in metrics['alerts']:
            print(f"- {alert}")
    else:
        print("\n✅ Nenhum alerta crítico")

asyncio.run(monitorar_performance())
```

### 3. Configuração de Timeout Customizado

```python
async def download_com_timeout():
    # Download com timeout customizado
    resultado = await pdpj_client.download_document(
        href_binario="/processos/5000315-75.2025.4.03.6327/documentos/abc123/binario",
        document_name="documento_grande.pdf",
        timeout=120.0  # 2 minutos
    )
    
    print(f"Download com timeout customizado: {resultado['size']} bytes")

asyncio.run(download_com_timeout())
```

## 🔍 Validação de Token

### Validação Automática

```python
from app.utils.token_validator import PDPJTokenValidator

# Validação simples
is_valid = PDPJTokenValidator.validate_and_log(token, base_url)

# Validação detalhada
result = PDPJTokenValidator.validate_token(token, base_url)
print(f"Token válido: {result.is_valid}")
print(f"Horas restantes: {result.hours_remaining}")
print(f"É token PJE: {result.is_pje_token}")
print(f"É token PDPJ: {result.is_pdpj_token}")
print(f"Usuário: {result.user_name}")
```

## 🏗️ Arquitetura e Componentes

### Estrutura do Cliente

```
PDPJClient
├── Configurações (timeouts, retries, conexões)
├── Semáforos (controle de concorrência)
├── Métricas (performance e alertas)
├── Validação de Token (JWT)
├── Requisições HTTP (httpx + aiohttp)
├── Download de Documentos (com validação)
├── Cache de Sessão (cookies)
└── Headers Centralizados
```

### Componentes Auxiliares

- **SessionManager**: Cache inteligente de cookies de sessão
- **TokenValidator**: Validação e diagnóstico de tokens JWT
- **FileValidator**: Validação e processamento de arquivos
- **HTTPHeadersConfig**: Configuração centralizada de headers

## 🚨 Tratamento de Erros

### Tipos de Erro Comuns

```python
from app.services.pdpj_client import PDPJClientError

try:
    resultado = await pdpj_client.download_document(href_binario)
except PDPJClientError as e:
    if "401" in str(e):
        print("❌ Token inválido ou expirado")
    elif "404" in str(e):
        print("❌ Processo ou documento não encontrado")
    elif "timeout" in str(e).lower():
        print("⏰ Timeout na requisição")
    else:
        print(f"❌ Erro: {e}")
except asyncio.TimeoutError:
    print("⏰ Timeout global da operação")
except Exception as e:
    print(f"❌ Erro inesperado: {e}")
```

## 📈 Otimizações de Performance

### 1. Configurações Recomendadas

```python
# Para alta performance
settings.pdpj_max_connections = 20
settings.pdpj_max_keepalive = 10
settings.max_concurrent_requests = 200
settings.max_concurrent_downloads = 100

# Para estabilidade
settings.pdpj_request_timeout = 45.0
settings.pdpj_download_timeout = 90.0
settings.pdpj_max_retries = 5
```

### 2. Monitoramento de Performance

```python
# Verificar utilização de concorrência
metrics = pdpj_client.get_metrics()
utilization = metrics['concurrent_utilization']
if utilization > 0.8:
    print("⚠️ Alta utilização de concorrência")

# Verificar cache de sessão
cache_hit_rate = metrics['session_cache_hit_rate']
if cache_hit_rate < 0.7:
    print("⚠️ Cache de sessão com baixo hit rate")
```

## 🔧 Troubleshooting

### Problemas Comuns

1. **Token PJE vs PDPJ**
   ```python
   # Verificar se está usando token correto
   result = PDPJTokenValidator.validate_token(token)
   if result.is_pje_token:
       print("⚠️ Usando token PJE em vez de PDPJ")
   ```

2. **Alta Taxa de Erro**
   ```python
   metrics = pdpj_client.get_metrics()
   if metrics['error_rate'] > 0.1:
       print("🚨 Taxa de erro alta - verificar configurações")
   ```

3. **Timeouts Frequentes**
   ```python
   # Aumentar timeouts
   settings.pdpj_request_timeout = 60.0
   settings.pdpj_download_timeout = 120.0
   ```

## 📚 Exemplos Completos

### Exemplo 1: Processamento Completo de Processo

```python
async def processar_processo_completo(numero_processo):
    """Processar processo completo com todos os documentos."""
    
    try:
        # 1. Buscar dados do processo
        print(f"🔍 Buscando dados do processo {numero_processo}")
        processo = await pdpj_client.get_process_full(numero_processo)
        print(f"✅ Processo encontrado: {processo['numeroProcesso']}")
        
        # 2. Buscar documentos
        print("📄 Buscando documentos...")
        documentos = await pdpj_client.get_process_documents(numero_processo)
        print(f"✅ Encontrados {len(documentos)} documentos")
        
        # 3. Download em lote
        if documentos:
            print("🚀 Iniciando download em lote...")
            batch_requests = [
                {
                    'hrefBinario': doc.get('hrefBinario', ''),
                    'document_name': doc.get('nome', f'doc_{i}')
                }
                for i, doc in enumerate(documentos)
            ]
            
            resultados = await pdpj_client.batch_download_documents(batch_requests)
            
            # 4. Relatório final
            sucessos = sum(1 for r in resultados if r.get('success', True))
            print(f"✅ Processamento concluído: {sucessos}/{len(resultados)} documentos baixados")
            
            # 5. Métricas
            metrics = pdpj_client.get_metrics()
            print(f"📊 Performance: {metrics['success_rate']*100:.1f}% sucesso")
            
    except Exception as e:
        print(f"❌ Erro no processamento: {e}")

# Executar
asyncio.run(processar_processo_completo("5000315-75.2025.4.03.6327"))
```

### Exemplo 2: Monitoramento Contínuo

```python
async def monitoramento_continuo():
    """Monitoramento contínuo com alertas."""
    
    while True:
        try:
            # Executar operação de teste
            await pdpj_client.get_process_cover("5000315-75.2025.4.03.6327")
            
            # Verificar métricas
            metrics = pdpj_client.get_metrics()
            
            # Alertas críticos
            if metrics['health_status'] == 'critical':
                print("🚨 ALERTA CRÍTICO: Sistema com problemas")
                for alert in metrics['alerts']:
                    print(f"   - {alert}")
            
            # Log de status
            print(f"📊 Status: {metrics['health_status']} | "
                  f"Sucesso: {metrics['success_rate']*100:.1f}% | "
                  f"Erro: {metrics['error_rate']*100:.1f}%")
            
            # Aguardar próxima verificação
            await asyncio.sleep(60)  # 1 minuto
            
        except Exception as e:
            print(f"❌ Erro no monitoramento: {e}")
            await asyncio.sleep(30)  # Aguardar menos em caso de erro

# Executar monitoramento (Ctrl+C para parar)
# asyncio.run(monitoramento_continuo())
```

## 🎯 Conclusão

O PDPJClient é uma solução robusta e otimizada para integração com a API PDPJ, oferecendo:

- **Alta Performance**: Paralelização e otimizações avançadas
- **Robustez**: Tratamento sofisticado de erros e retry
- **Monitoramento**: Métricas detalhadas e alertas críticos
- **Facilidade de Uso**: API simples e intuitiva
- **Configurabilidade**: Flexibilidade para diferentes cenários

Para mais informações, consulte a documentação dos componentes auxiliares ou entre em contato com a equipe de desenvolvimento.
