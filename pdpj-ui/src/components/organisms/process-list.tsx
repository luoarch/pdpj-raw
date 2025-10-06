'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Process } from '@/lib/api-client';
import { apiClient } from '@/lib/api-client';
import { ProcessCard } from '@/components/molecules/process-card';
import { SearchForm } from '@/components/molecules/search-form';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { Button } from '@/components/atoms/button';
import { ChevronLeft, ChevronRight, RefreshCw } from 'lucide-react';

interface ProcessListProps {
  onProcessSelect?: (process: Process) => void;
  onProcessDownload?: (process: Process) => void;
}

export function ProcessList({ onProcessSelect, onProcessDownload }: ProcessListProps) {
  const [page, setPage] = useState(1);
  const [searchQuery, setSearchQuery] = useState('');
  const limit = 12;

  // Query para buscar processos
  const {
    data: processesData,
    isLoading,
    error,
    refetch
  } = useQuery({
    queryKey: ['processes', page, limit, searchQuery],
    queryFn: async () => {
      // Usar apenas o endpoint de listagem disponível
      const result = await apiClient.getProcesses(page, limit);
      console.log('API Response:', result); // Debug log

      // Filtrar processos localmente por número do processo
      let filteredProcesses = result.processes || [];
      if (searchQuery.trim()) {
        filteredProcesses = filteredProcesses.filter(process =>
          process.process_number.toLowerCase().includes(searchQuery.toLowerCase())
        );
      }

      return {
        processes: filteredProcesses,
        total: filteredProcesses.length,
        page: result.page || 1,
        limit: result.limit || limit,
      };
    },
    placeholderData: (previousData) => previousData,
  });

  const handleSearch = (data: any) => {
    setSearchQuery(data.query || '');
    setPage(1); // Reset para primeira página
  };

  const handleRefresh = () => {
    refetch();
  };

  const totalPages = processesData?.total ? Math.ceil(processesData.total / limit) : 0;

  if (error) {
    return (
      <div className="text-center py-12">
        <div className="text-red-600 dark:text-red-400 mb-4">
          Erro ao carregar processos
        </div>
        <Button onClick={handleRefresh} variant="outline">
          <RefreshCw className="h-4 w-4 mr-2" />
          Tentar novamente
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Busca */}
      <SearchForm onSearch={handleSearch} loading={isLoading} />

      {/* Controles */}
      <div className="flex items-center justify-between">
        <div className="text-sm text-gray-600 dark:text-gray-400">
          {processesData?.total && (
            <>
              Mostrando {((page - 1) * limit) + 1} a {Math.min(page * limit, processesData.total)} de {processesData.total} processos
            </>
          )}
        </div>
        <Button onClick={handleRefresh} variant="outline" size="sm">
          <RefreshCw className="h-4 w-4 mr-2" />
          Atualizar
        </Button>
      </div>

      {/* Lista de processos */}
      {isLoading ? (
        <div className="flex justify-center py-12">
          <LoadingSpinner size="lg" />
        </div>
      ) : processesData?.processes && processesData.processes.length === 0 ? (
        <div className="text-center py-12">
          <div className="text-gray-500 dark:text-gray-400 mb-4">
            Nenhum processo encontrado
          </div>
          <p className="text-sm text-gray-400 dark:text-gray-500">
            Tente ajustar os filtros de busca ou verifique se há processos disponíveis.
          </p>
        </div>
      ) : (
        <>
          {/* Grid de processos */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {processesData?.processes?.map((process) => (
              <ProcessCard
                key={process.id}
                process={process}
                onView={onProcessSelect}
                onDownload={onProcessDownload}
              />
            ))}
          </div>

          {/* Paginação */}
          {totalPages > 1 && (
            <div className="flex items-center justify-center space-x-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage(page - 1)}
                disabled={page === 1}
              >
                <ChevronLeft className="h-4 w-4" />
                Anterior
              </Button>

              <div className="flex items-center space-x-1">
                {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                  const pageNumber = Math.max(1, Math.min(totalPages - 4, page - 2)) + i;
                  return (
                    <Button
                      key={pageNumber}
                      variant={pageNumber === page ? 'primary' : 'outline'}
                      size="sm"
                      onClick={() => setPage(pageNumber)}
                      className="w-8 h-8 p-0"
                    >
                      {pageNumber}
                    </Button>
                  );
                })}
              </div>

              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage(page + 1)}
                disabled={page === totalPages}
              >
                Próximo
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
