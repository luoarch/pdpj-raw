"""Gerenciador de transições de status de documentos e jobs."""

from typing import Optional, Dict, List
from loguru import logger

from app.models.document import DocumentStatus
from app.models.process_job import JobStatus


class StatusManager:
    """Gerenciar transições de status e validações."""
    
    # Mapa de transições válidas para DocumentStatus
    DOCUMENT_TRANSITIONS: Dict[DocumentStatus, List[DocumentStatus]] = {
        DocumentStatus.PENDING: [
            DocumentStatus.PROCESSING,  # Iniciou download
            DocumentStatus.FAILED,      # Falha antes de iniciar
        ],
        DocumentStatus.PROCESSING: [
            DocumentStatus.AVAILABLE,   # Download e upload S3 completo
            DocumentStatus.FAILED,      # Falha durante processamento
        ],
        DocumentStatus.AVAILABLE: [
            # Estado final - nenhuma transição permitida
        ],
        DocumentStatus.FAILED: [
            DocumentStatus.PROCESSING,  # Retry - tentar novamente
        ],
    }
    
    # Mapa de transições válidas para JobStatus
    JOB_TRANSITIONS: Dict[JobStatus, List[JobStatus]] = {
        JobStatus.PENDING: [
            JobStatus.PROCESSING,  # Iniciou execução
            JobStatus.CANCELLED,   # Cancelado antes de iniciar
            JobStatus.FAILED,      # Falha ao iniciar
        ],
        JobStatus.PROCESSING: [
            JobStatus.COMPLETED,   # Completado com sucesso
            JobStatus.FAILED,      # Falha durante execução
            JobStatus.CANCELLED,   # Cancelado durante execução
        ],
        JobStatus.COMPLETED: [
            # Estado final - nenhuma transição permitida
        ],
        JobStatus.FAILED: [
            JobStatus.PROCESSING,  # Retry - tentar novamente
        ],
        JobStatus.CANCELLED: [
            JobStatus.PROCESSING,  # Reativar job cancelado
        ],
    }
    
    @staticmethod
    def get_initial_document_status(has_webhook: bool) -> DocumentStatus:
        """
        Determinar status inicial do documento baseado em webhook.
        
        Args:
            has_webhook: Se webhook foi configurado
            
        Returns:
            Status inicial apropriado
        """
        return DocumentStatus.PENDING if has_webhook else DocumentStatus.PROCESSING
    
    @staticmethod
    def can_transition_document(
        current: DocumentStatus, 
        target: DocumentStatus
    ) -> tuple[bool, Optional[str]]:
        """
        Verificar se transição de status de documento é válida.
        
        Args:
            current: Status atual
            target: Status desejado
            
        Returns:
            Tuple (is_valid, error_message)
        """
        valid_transitions = StatusManager.DOCUMENT_TRANSITIONS.get(current, [])
        
        if target in valid_transitions:
            return True, None
        
        # Transição não permitida
        valid_list = [s.value for s in valid_transitions]
        error = f"Transição inválida: {current.value} → {target.value}. Válidas: {valid_list}"
        logger.warning(f"⚠️ {error}")
        return False, error
    
    @staticmethod
    def can_transition_job(
        current: JobStatus, 
        target: JobStatus
    ) -> tuple[bool, Optional[str]]:
        """
        Verificar se transição de status de job é válida.
        
        Args:
            current: Status atual
            target: Status desejado
            
        Returns:
            Tuple (is_valid, error_message)
        """
        valid_transitions = StatusManager.JOB_TRANSITIONS.get(current, [])
        
        if target in valid_transitions:
            return True, None
        
        # Transição não permitida
        valid_list = [s.value for s in valid_transitions]
        error = f"Transição inválida: {current.value} → {target.value}. Válidas: {valid_list}"
        logger.warning(f"⚠️ {error}")
        return False, error
    
    @staticmethod
    def get_next_valid_statuses_document(current: DocumentStatus) -> List[DocumentStatus]:
        """Obter lista de status válidos a partir do atual (documento)."""
        return StatusManager.DOCUMENT_TRANSITIONS.get(current, [])
    
    @staticmethod
    def get_next_valid_statuses_job(current: JobStatus) -> List[JobStatus]:
        """Obter lista de status válidos a partir do atual (job)."""
        return StatusManager.JOB_TRANSITIONS.get(current, [])
    
    @staticmethod
    def is_final_status_document(status: DocumentStatus) -> bool:
        """Verificar se é um status final (documento)."""
        return status == DocumentStatus.AVAILABLE
    
    @staticmethod
    def is_final_status_job(status: JobStatus) -> bool:
        """Verificar se é um status final (job)."""
        return status in [JobStatus.COMPLETED, JobStatus.CANCELLED]
    
    @staticmethod
    def validate_status_transition_document(
        current: str,
        target: str
    ) -> tuple[bool, Optional[str]]:
        """
        Validar transição de status (string values).
        
        Args:
            current: Status atual (string)
            target: Status desejado (string)
            
        Returns:
            Tuple (is_valid, error_message)
        """
        try:
            current_enum = DocumentStatus(current)
            target_enum = DocumentStatus(target)
            return StatusManager.can_transition_document(current_enum, target_enum)
        except ValueError as e:
            return False, f"Status inválido: {e}"
    
    @staticmethod
    def validate_status_transition_job(
        current: str,
        target: str
    ) -> tuple[bool, Optional[str]]:
        """
        Validar transição de status de job (string values).
        
        Args:
            current: Status atual (string)
            target: Status desejado (string)
            
        Returns:
            Tuple (is_valid, error_message)
        """
        try:
            current_enum = JobStatus(current)
            target_enum = JobStatus(target)
            return StatusManager.can_transition_job(current_enum, target_enum)
        except ValueError as e:
            return False, f"Status inválido: {e}"


# Instância global
status_manager = StatusManager()

