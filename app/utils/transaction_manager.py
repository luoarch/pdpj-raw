"""
Gerenciador de transações para operações de banco de dados.
"""

import asyncio
from typing import Dict, List, Optional, Any, Callable, TypeVar, Generic
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from loguru import logger

T = TypeVar('T')


class TransactionManager:
    """Gerenciador de transações com rollback automático."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self._savepoints: List[str] = []
        self._rollback_operations: List[Callable] = []
    
    @asynccontextmanager
    async def transaction(self, savepoint_name: Optional[str] = None):
        """Context manager para transação com rollback automático."""
        savepoint = None
        try:
            if savepoint_name:
                savepoint = await self.db.begin_nested()
                self._savepoints.append(savepoint_name)
                logger.debug(f"🔄 Criando savepoint: {savepoint_name}")
            else:
                await self.db.begin()
                logger.debug("🔄 Iniciando transação")
            
            yield self.db
            
            if savepoint:
                await self.db.commit()
                logger.debug(f"✅ Savepoint commitado: {savepoint_name}")
            else:
                await self.db.commit()
                logger.debug("✅ Transação commitada")
                
        except Exception as e:
            if savepoint:
                await self.db.rollback()
                logger.error(f"❌ Rollback do savepoint: {savepoint_name}")
            else:
                await self.db.rollback()
                logger.error("❌ Rollback da transação")
            
            # Executar operações de rollback registradas
            await self._execute_rollback_operations()
            raise e
    
    def add_rollback_operation(self, operation: Callable):
        """Adicionar operação a ser executada em caso de rollback."""
        self._rollback_operations.append(operation)
    
    async def _execute_rollback_operations(self):
        """Executar operações de rollback registradas."""
        for operation in reversed(self._rollback_operations):
            try:
                if asyncio.iscoroutinefunction(operation):
                    await operation()
                else:
                    operation()
            except Exception as e:
                logger.error(f"❌ Erro na operação de rollback: {e}")
    
    async def execute_with_retry(self, operation: Callable, max_retries: int = 3) -> Any:
        """Executar operação com retry automático."""
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                if asyncio.iscoroutinefunction(operation):
                    return await operation()
                else:
                    return operation()
            except Exception as e:
                last_exception = e
                logger.warning(f"⚠️ Tentativa {attempt + 1} falhou: {e}")
                
                if attempt < max_retries - 1:
                    await asyncio.sleep(0.1 * (2 ** attempt))  # Backoff exponencial
                    continue
        
        logger.error(f"❌ Operação falhou após {max_retries} tentativas")
        raise last_exception


class BatchTransactionManager:
    """Gerenciador de transações para operações em lote."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self._batch_size = 100
        self._operations: List[Dict[str, Any]] = []
    
    def set_batch_size(self, size: int):
        """Definir tamanho do lote."""
        self._batch_size = size
    
    def add_operation(self, operation_type: str, data: Any, **kwargs):
        """Adicionar operação ao lote."""
        self._operations.append({
            "type": operation_type,
            "data": data,
            "kwargs": kwargs
        })
    
    async def execute_batch(self) -> Dict[str, int]:
        """Executar todas as operações em lotes."""
        if not self._operations:
            return {"processed": 0, "errors": 0}
        
        logger.info(f"🚀 Executando lote de {len(self._operations)} operações")
        
        processed = 0
        errors = 0
        
        # Processar em lotes
        for i in range(0, len(self._operations), self._batch_size):
            batch = self._operations[i:i + self._batch_size]
            
            try:
                async with TransactionManager(self.db).transaction():
                    batch_processed, batch_errors = await self._process_batch(batch)
                    processed += batch_processed
                    errors += batch_errors
                    
            except Exception as e:
                logger.error(f"❌ Erro no lote {i//self._batch_size + 1}: {e}")
                errors += len(batch)
        
        logger.info(f"✅ Lote executado: {processed} processados, {errors} erros")
        return {"processed": processed, "errors": errors}
    
    async def _process_batch(self, batch: List[Dict[str, Any]]) -> tuple[int, int]:
        """Processar um lote de operações."""
        processed = 0
        errors = 0
        
        for operation in batch:
            try:
                if operation["type"] == "add":
                    self.db.add(operation["data"])
                elif operation["type"] == "merge":
                    await self.db.merge(operation["data"])
                elif operation["type"] == "delete":
                    await self.db.delete(operation["data"])
                elif operation["type"] == "update":
                    # Implementar update específico se necessário
                    pass
                
                processed += 1
                
            except Exception as e:
                logger.error(f"❌ Erro na operação {operation['type']}: {e}")
                errors += 1
        
        await self.db.commit()
        return processed, errors
    
    def clear_operations(self):
        """Limpar operações pendentes."""
        self._operations.clear()


# Funções de conveniência
async def with_transaction(db: AsyncSession, operation: Callable, savepoint_name: Optional[str] = None):
    """Executar operação dentro de uma transação."""
    async with TransactionManager(db).transaction(savepoint_name):
        return await operation()


async def with_batch_transaction(db: AsyncSession, operations: List[Dict[str, Any]], batch_size: int = 100):
    """Executar operações em lote dentro de transações."""
    manager = BatchTransactionManager(db)
    manager.set_batch_size(batch_size)
    
    for operation in operations:
        manager.add_operation(**operation)
    
    return await manager.execute_batch()
