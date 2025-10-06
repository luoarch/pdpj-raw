#!/usr/bin/env python3
"""Teste simples para ver se Celery task funciona."""

from app.tasks.download_tasks import download_process_documents_async

# Tentar agendar task
try:
    print("🧪 Testando agendamento de task Celery...")
    
    job = download_process_documents_async.apply_async(
        args=[999, "TEST-PROCESS", None],
        task_id="test-job-123",
        queue='documents'
    )
    
    print(f"✅ Task agendada com sucesso!")
    print(f"   Job ID: {job.id}")
    print(f"   Status: {job.status}")
    print(f"   Queue: documents")
    
except Exception as e:
    print(f"❌ Erro ao agendar task: {e}")
    import traceback
    traceback.print_exc()

