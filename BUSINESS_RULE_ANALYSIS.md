# 📋 Análise: Regra de Negócio - Entrega de Documentos com Callback

## 🎯 Nova Regra de Negócio Proposta

### Fluxo Principal

1. **Consulta ao Processo**
   - Endpoint: `GET /processes/{numero}?webhook_url={url}` (webhook opcional)
   - Inicia download assíncrono de TODOS os documentos em paralelo
   - Retorna resposta imediata

2. **Resposta Inicial**
   - **Com webhook:** Documentos com status `"pending"`, callback será enviado
   - **Sem webhook:** Documentos com status `"processing"`, consultar status depois

3. **Processamento Assíncrono**
   - Download de documentos da API PDPJ
   - Upload para S3
   - Geração de URLs presignadas

4. **Entrega**
   - **Com webhook:** POST automático para webhook_url quando completo
   - **Sem webhook:** Endpoint `GET /processes/{id}/status` para consulta

---

## 📊 Implementação Atual

### Endpoints Existentes

| Endpoint | Método | Função Atual |
|----------|--------|--------------|
| `GET /{numero}` | GET | Busca processo (só metadados) |
| `POST /{numero}/download-documents` | POST | **Registra** metadados (NÃO baixa fisicamente) |
| `POST /{numero}/download-document/{id}` | POST | Baixa **1 documento** e upload S3 |
| `POST /{numero}/download-all-documents` | POST | Baixa **TODOS** em lotes (recém criado) |
| `GET /{numero}/files` | GET | Lista documentos com URLs S3 (se baixados) |

### Características Atuais

✅ **O que já temos:**
- Upload para S3 funcionando
- URLs presignadas (1 hora)
- Download individual
- Download em massa (novo)
- Celery para tarefas assíncronas

❌ **O que falta:**
- Webhook callback opcional
- Status `"pending"` vs `"processing"`
- Download automático na consulta do processo
- Endpoint `/status` para acompanhamento
- Callback automático quando completo
- Job tracking no Celery

---

## 🔍 Diferenças Identificadas

### 1. **Fluxo de Consulta**

| Aspecto | Atual | Proposto |
|---------|-------|----------|
| `GET /processes/{numero}` | Só retorna metadados | **Inicia download assíncrono** + retorna dados |
| Download automático | ❌ Não | ✅ Sim (em background) |
| Webhook opcional | ❌ Não existe | ✅ Parâmetro opcional |

### 2. **Status de Documentos**

| Situação | Atual | Proposto |
|----------|-------|----------|
| Não baixado | `downloaded: false` | `status: "pending"` ou `"processing"` |
| Em download | `downloaded: false` | `status: "processing"` |
| Completo | `downloaded: true` | `status: "available"` + link |
| Erro | `downloaded: false` | `status: "failed"` + erro |

### 3. **Endpoints de Status**

| Endpoint | Atual | Proposto |
|----------|-------|----------|
| `/processes/{id}/status` | ❌ Não existe | ✅ **Novo endpoint** |
| Acompanhamento de progresso | ❌ Não tem | ✅ Retorna progresso (X de Y) |

### 4. **Callback Webhook**

| Funcionalidade | Atual | Proposto |
|----------------|-------|----------|
| Webhook callback | ❌ Não existe | ✅ POST automático quando completo |
| Payload do callback | N/A | Processo completo + links S3 |
| Retry de callback | N/A | Tentar reenviar se falhar |

### 5. **Processamento Assíncrono**

| Aspecto | Atual | Proposto |
|---------|-------|----------|
| Celery tasks | ✅ Existe | ✅ Usar para download assíncrono |
| Job tracking | ❌ Básico | ✅ Track status detalhado |
| Progresso em tempo real | ❌ Não | ✅ Porcentagem de conclusão |

---

## 📝 Roadmap de Implementação

### **FASE 1: Preparação e Modelos** 🏗️

**1.1. Adicionar campos ao modelo Document**
- [ ] Campo `status` (enum: pending, processing, available, failed)
- [ ] Campo `error_message` (string, nullable)
- [ ] Campo `download_started_at` (timestamp)
- [ ] Campo `download_completed_at` (timestamp)

**1.2. Adicionar modelo ProcessJob**
- [ ] Tabela para tracking de jobs
- [ ] Campos: id, process_id, webhook_url, status, progress, total_documents, completed_documents
- [ ] Timestamps: created_at, started_at, completed_at

**1.3. Migration**
- [ ] Criar migration Alembic
- [ ] Executar migration
- [ ] **TESTE:** Verificar que tabelas foram criadas

---

### **FASE 2: Endpoint de Status** 📊

**2.1. Criar endpoint GET /{numero}/status**
- [ ] Retornar status do processo
- [ ] Incluir progresso (X de Y documentos)
- [ ] Incluir documentos com status individual
- [ ] **TESTE:** Consultar status de processo existente

**2.2. Schema de resposta**
- [ ] `ProcessStatusResponse` com progresso
- [ ] `DocumentStatus` enum
- [ ] **TESTE:** Validação do schema

---

### **FASE 3: Webhook System** 🔔

**3.1. Serviço de Webhook**
- [ ] Criar `app/services/webhook_service.py`
- [ ] Método `send_webhook(url, payload)`
- [ ] Retry automático (3 tentativas)
- [ ] Timeout configurável
- [ ] **TESTE:** Enviar webhook para endpoint de teste

**3.2. Validação de webhook_url**
- [ ] Validar formato URL
- [ ] Verificar protocolo (https recomendado)
- [ ] **TESTE:** Rejeitar URLs inválidas

---

### **FASE 4: Download Assíncrono na Consulta** ⚡

**4.1. Modificar GET /{numero}**
- [ ] Aceitar parâmetro `webhook_url` (opcional)
- [ ] Aceitar parâmetro `auto_download` (default: true)
- [ ] Se `auto_download=true`, agendar download assíncrono
- [ ] Retornar documentos com status inicial
- [ ] **TESTE:** Consultar processo com auto_download

**4.2. Celery Task para download em massa**
- [ ] Criar task `download_process_documents_async`
- [ ] Aceitar: process_id, webhook_url (opcional)
- [ ] Baixar todos os documentos em paralelo (lotes de 5)
- [ ] Atualizar status progressivamente
- [ ] **TESTE:** Executar task manualmente

**4.3. Callback quando completo**
- [ ] Ao finalizar task, se webhook_url existe
- [ ] Montar payload completo do processo
- [ ] Enviar POST para webhook_url
- [ ] Registrar sucesso/falha
- [ ] **TESTE:** Verificar callback recebido

---

### **FASE 5: Gerenciamento de Status** 📈

**5.1. Atualizar status dos documentos**
- [ ] `"pending"` → quando criado (com webhook)
- [ ] `"processing"` → quando criado (sem webhook) ou download iniciou
- [ ] `"available"` → quando upload S3 completo
- [ ] `"failed"` → se erro no download/upload
- [ ] **TESTE:** Verificar transições de status

**5.2. Progresso em tempo real**
- [ ] Atualizar `ProcessJob` durante download
- [ ] Calcular porcentagem (completed/total * 100)
- [ ] **TESTE:** Consultar progresso durante download

---

### **FASE 6: Idempotência e Cache** 🔄

**6.1. Prevenir duplicação**
- [ ] Verificar se job já existe antes de criar novo
- [ ] Se em progresso, retornar job_id existente
- [ ] Se completo, retornar dados cached
- [ ] **TESTE:** Consultar mesmo processo 2x rapidamente

**6.2. TTL de links S3**
- [ ] Regenerar links se expirados
- [ ] Cache de links com TTL
- [ ] **TESTE:** Verificar regeneração de link expirado

---

### **FASE 7: Tratamento de Erros** 🛡️

**7.1. Retry de downloads**
- [ ] Retry automático em caso de falha (3x)
- [ ] Backoff exponencial
- [ ] Marcar como failed se esgotar tentativas
- [ ] **TESTE:** Simular falha e verificar retry

**7.2. Retry de webhook**
- [ ] Retry automático do callback (3x)
- [ ] Registrar tentativas
- [ ] Email/alert se falhar definitivamente
- [ ] **TESTE:** Webhook indisponível temporariamente

---

### **FASE 8: Segurança e Validação** 🔒

**8.1. Validação de webhook**
- [ ] Whitelist de domínios permitidos (opcional)
- [ ] Timeout de 30s máximo
- [ ] Verificar resposta (200-299 = sucesso)
- [ ] **TESTE:** Webhook malicioso/lento

**8.2. Rate limiting**
- [ ] Limitar chamadas de download em massa
- [ ] Prevenir abuse
- [ ] **TESTE:** Exceder limite

---

### **FASE 9: Documentação e Exemplos** 📚

**9.1. Atualizar docs**
- [ ] Documentar novo fluxo
- [ ] Exemplos de uso com/sem webhook
- [ ] Schema do payload do callback
- [ ] **TESTE:** Seguir documentação

**9.2. Collection Postman**
- [ ] Adicionar requests novos
- [ ] Exemplos de callback
- [ ] **TESTE:** Importar e executar

---

### **FASE 10: Testes E2E e Deploy** 🚀

**10.1. Testes end-to-end**
- [ ] Fluxo completo com webhook
- [ ] Fluxo completo sem webhook
- [ ] Fluxo com falhas e recuperação
- [ ] **TESTE:** Todos cenários

**10.2. Performance**
- [ ] Load test com 100 processos simultâneos
- [ ] Verificar consumo de recursos
- [ ] **TESTE:** Métricas OK

**10.3. Deploy**
- [ ] Staging
- [ ] Validação
- [ ] Produção

---

## 📊 Estimativa de Esforço

| Fase | Complexidade | Tempo Estimado | Prioridade |
|------|--------------|----------------|------------|
| FASE 1 | Média | 1-2h | 🔴 Alta |
| FASE 2 | Baixa | 1h | 🔴 Alta |
| FASE 3 | Média | 2h | 🔴 Alta |
| FASE 4 | Alta | 3-4h | 🔴 Alta |
| FASE 5 | Média | 2h | 🟡 Média |
| FASE 6 | Média | 2h | 🟡 Média |
| FASE 7 | Alta | 2-3h | 🟡 Média |
| FASE 8 | Média | 1-2h | 🟢 Baixa |
| FASE 9 | Baixa | 1h | 🟢 Baixa |
| FASE 10 | Alta | 2-3h | 🔴 Alta |

**Total Estimado:** 17-22 horas de desenvolvimento

---

## 🎯 Próximos Passos

**Vamos começar com FASE 1** - criar os modelos e migrations necessários.

Confirme para iniciar a implementação passo a passo, testando cada etapa antes de avançar!

