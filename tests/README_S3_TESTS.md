# 🧪 Guia de Testes S3 e PDPJ

## 📋 Testes Oficiais Adicionados

### Arquivos de Teste

1. **`test_s3_service.py`** - Testes do serviço S3
   - TestS3Configuration (2 testes) ✅
   - TestS3Connectivity (2 testes) ✅
   - TestS3Operations (5 testes) ✅
   - TestS3Health (1 teste) ✅
   - TestS3ErrorHandling (2 testes) ✅

2. **`test_pdpj_s3_integration.py`** - Testes de integração PDPJ + S3
   - TestPDPJDownloadIntegration (2 testes) ✅
   - TestS3DocumentWorkflow (2 testes) ✅
   - TestS3UtilityFunctions (1 teste) ✅

**Total:** 17 testes (14 críticos)

---

## 🚀 Executar Testes

### Todos os testes S3

```bash
./venv/bin/pytest tests/test_s3_service.py tests/test_pdpj_s3_integration.py -v
```

### Apenas testes críticos

```bash
./venv/bin/pytest -v -m critical
```

### Apenas testes S3

```bash
./venv/bin/pytest -v -m s3
```

### Apenas testes PDPJ

```bash
./venv/bin/pytest -v -m pdpj
```

### Testes rápidos (sem slow)

```bash
./venv/bin/pytest -v -m "critical and not slow"
```

---

## 🏷️ Marcadores Disponíveis

| Marcador | Descrição | Uso |
|----------|-----------|-----|
| `@pytest.mark.unit` | Testes unitários | Testes rápidos, sem I/O |
| `@pytest.mark.integration` | Testes de integração | Testam serviços externos |
| `@pytest.mark.slow` | Testes lentos | Podem demorar > 1s |
| `@pytest.mark.api` | Testes de API | Endpoints HTTP |
| `@pytest.mark.s3` | Testes S3 | AWS S3 específicos |
| `@pytest.mark.pdpj` | Testes PDPJ | API PDPJ específicos |
| `@pytest.mark.critical` | Testes críticos | **Devem passar antes de deploy** |

---

## 📊 Cobertura de Testes S3

### TestS3Configuration (crítico)
- ✅ `test_aws_credentials_loaded` - Credenciais do .env
- ✅ `test_s3_service_initialization` - Inicialização correta

### TestS3Connectivity (crítico, slow)
- ✅ `test_s3_connection` - Conectividade AWS
- ✅ `test_bucket_region` - Validação de região

### TestS3Operations (crítico, slow)
- ✅ `test_upload_download_cycle` - Upload → Download → Delete
- ✅ `test_upload_document_method` - S3Service.upload_document()
- ✅ `test_list_objects` - Listagem de objetos
- ✅ `test_generate_presigned_url` - URLs presignadas
- ✅ `test_delete_nonexistent_object` - Deleção segura

### TestS3Health (crítico)
- ✅ `test_health_check` - Health check do serviço

### TestS3ErrorHandling (integration)
- ✅ `test_download_nonexistent_object` - Erro controlado
- ✅ `test_upload_to_invalid_bucket` - Erro controlado

---

## 📊 Cobertura de Testes PDPJ + S3

### TestPDPJDownloadIntegration (crítico)
- ✅ `test_pdpj_client_has_correct_token` - Token JWT válido
- ✅ `test_pdpj_url_construction_with_api_v2` - URLs com /api/v2/

### TestS3DocumentWorkflow (crítico, slow)
- ✅ `test_upload_pdf_document` - Upload de PDF
- ✅ `test_multiple_documents_upload` - Upload em lote

---

## 🎯 Testes Críticos Antes de Deploy

Execute **SEMPRE** antes de fazer deploy:

```bash
./venv/bin/pytest -v -m critical
```

**Resultado esperado:**
```
14 passed, 3 deselected
```

Se algum teste crítico falhar, **NÃO FAZER DEPLOY** até corrigir!

---

## 🔍 Troubleshooting

### Testes falhando com erro 403

**Causa:** Permissões IAM incorretas

**Solução:**
```bash
./fix_s3_permissions.sh
```

### Testes falhando com "InvalidAccessKeyId"

**Causa:** Credenciais AWS incorretas no `.env`

**Solução:** Verificar variáveis no `.env`:
```bash
grep AWS_ .env
```

### Testes lentos

**Causa:** Operações reais no S3 levam tempo

**Solução:** Use marcador para pular testes lentos:
```bash
pytest -v -m "not slow"
```

---

## 📝 Adicionar Novos Testes S3

### Template para Teste Unitário

```python
@pytest.mark.unit
@pytest.mark.s3
class TestNovaFuncionalidade:
    def test_algo(self):
        # Seu teste aqui
        assert True
```

### Template para Teste de Integração

```python
@pytest.mark.integration
@pytest.mark.s3
@pytest.mark.critical
class TestNovaIntegracao:
    async def test_operacao_s3(self):
        # Teste assíncrono com S3 real
        test_id = str(uuid.uuid4())[:8]
        # ... seu código aqui
```

---

## 🎊 Status Atual

**Última Execução:** 2025-10-06  
**Testes Totais:** 17  
**Testes Críticos:** 14  
**Taxa de Sucesso:** 100% ✅  
**Tempo de Execução:** ~6s

---

## 📚 Comandos Úteis

```bash
# Executar todos os testes
pytest tests/

# Executar apenas testes S3
pytest -v -m s3

# Executar testes críticos
pytest -v -m critical

# Executar com cobertura
pytest --cov=app.services.s3_service tests/test_s3_service.py

# Executar em modo verbose com detalhes
pytest -vvv tests/test_s3_service.py

# Parar no primeiro erro
pytest -x tests/

# Executar teste específico
pytest tests/test_s3_service.py::TestS3Operations::test_upload_download_cycle -v
```

---

**IMPORTANTE:** Estes testes são **críticos** para garantir que o sistema de armazenamento de documentos funcione corretamente!

