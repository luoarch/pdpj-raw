'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import { Search, Download, Eye, FileText } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/atoms/card';
import { Button } from '@/components/atoms/button';
import { Input } from '@/components/atoms/input';
import { Badge } from '@/components/atoms/badge';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { apiClient, Process } from '@/lib/api-client';
import { useDownloadsStore } from '@/store/downloads-store';
import { useAppStore } from '@/store/app-store';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';

export default function SearchPage() {
  const router = useRouter();
  const [searchQuery, setSearchQuery] = useState('');
  const { startDownload, isDownloading } = useDownloadsStore();
  const { addNotification } = useAppStore();

  const { data: searchResults, isLoading, error, refetch } = useQuery({
    queryKey: ['search', searchQuery],
    queryFn: async () => {
      if (!searchQuery.trim()) {
        return null;
      }

      // Usar apenas o endpoint de listagem disponível
      const result = await apiClient.getProcesses(1, 50);

      // Filtrar processos localmente por número do processo
      let filteredProcesses = result.processes || [];

      if (searchQuery.trim()) {
        filteredProcesses = filteredProcesses.filter(process =>
          process.process_number.toLowerCase().includes(searchQuery.trim().toLowerCase())
        );
      }

      return {
        processes: filteredProcesses,
        total: filteredProcesses.length,
        page: 1,
        limit: 50,
        not_found: []
      };
    },
    enabled: false, // Só executa quando clicamos em buscar
  });

  const handleSearch = () => {
    if (searchQuery.trim()) {
      refetch();
    }
  };

  const handleClear = () => {
    setSearchQuery('');
  };

  const formatDate = (dateString: string) => {
    try {
      return format(new Date(dateString), 'dd/MM/yyyy', { locale: ptBR });
    } catch {
      return dateString;
    }
  };

  const getStatusVariant = (status: string) => {
    switch (status.toLowerCase()) {
      case 'ativo':
      case 'em andamento':
        return 'success';
      case 'suspenso':
      case 'pausado':
        return 'warning';
      case 'arquivado':
      case 'finalizado':
        return 'default';
      default:
        return 'info';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Buscar Processo
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Consulte um processo pela primeira vez usando o número do processo
        </p>
      </div>

      {/* Search Form */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Search className="h-5 w-5 mr-2" />
            Nova Consulta
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Campo de busca principal */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Número do Processo
            </label>
            <Input
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Ex: 1000145-91.2023.8.26.0597"
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
            />
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
              Digite o número completo do processo que deseja consultar
            </p>
          </div>


          {/* Botões de ação */}
          <div className="flex gap-2">
            <Button onClick={handleSearch} loading={isLoading}>
              <Search className="h-4 w-4 mr-2" />
              Consultar
            </Button>
            <Button variant="outline" onClick={handleClear}>
              Limpar
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Results */}
      {isLoading && (
        <div className="flex justify-center py-12">
          <LoadingSpinner size="lg" />
        </div>
      )}

      {error && (
        <Card>
          <CardContent className="p-6 text-center">
            <div className="text-red-600 dark:text-red-400 mb-4">
              Erro ao buscar processos
            </div>
            <Button onClick={() => refetch()} variant="outline">
              Tentar novamente
            </Button>
          </CardContent>
        </Card>
      )}

      {searchResults && (
        <div className="space-y-4">
          {/* Resultados header */}
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              Resultados da Consulta
            </h2>
            <Badge variant="info">
              {searchResults.processes.length} processo(s) encontrado(s)
            </Badge>
          </div>

          {/* Lista de resultados */}
          {searchResults.processes.length === 0 ? (
            <Card>
              <CardContent className="p-6 text-center">
                <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-500 dark:text-gray-400">
                  Nenhum processo encontrado com os critérios especificados.
                </p>
              </CardContent>
            </Card>
          ) : (
            <div className="grid grid-cols-1 gap-4">
              {searchResults.processes.map((process: Process) => (
                <Card key={process.id} className="hover:shadow-md transition-shadow">
                  <CardContent className="p-6">
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex-1">
                        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                          {process.title || 'Processo sem título'}
                        </h3>
                        <p className="text-sm text-gray-600 dark:text-gray-400 font-mono">
                          {process.process_number}
                        </p>
                      </div>
                      <Badge variant={getStatusVariant(process.status)}>
                        {process.status}
                      </Badge>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4 text-sm">
                      <div className="flex items-center text-gray-600 dark:text-gray-400">
                        <FileText className="h-4 w-4 mr-2" />
                        <span>Criado em {formatDate(process.created_at)}</span>
                      </div>
                      {process.documents_count !== undefined && (
                        <div className="flex items-center text-gray-600 dark:text-gray-400">
                          <FileText className="h-4 w-4 mr-2" />
                          <span>{process.documents_count} documentos</span>
                        </div>
                      )}
                      <div className="flex items-center text-gray-600 dark:text-gray-400">
                        <span>Atualizado em {formatDate(process.updated_at)}</span>
                      </div>
                    </div>

                    {/* Partes envolvidas */}
                    {process.parties && process.parties.length > 0 && (
                      <div className="mb-4">
                        <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                          Partes Envolvidas:
                        </p>
                        <p className="text-sm text-gray-600 dark:text-gray-400">
                          {process.parties.slice(0, 3).join(', ')}
                          {process.parties.length > 3 && ` e mais ${process.parties.length - 3}`}
                        </p>
                      </div>
                    )}

                    {/* Ações */}
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => router.push(`/processes/${process.process_number}`)}
                      >
                        <Eye className="h-4 w-4 mr-2" />
                        Visualizar
                      </Button>
                      {process.documents_count && process.documents_count > 0 && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={async () => {
                            if (isDownloading(process.process_number)) {
                              addNotification({
                                type: 'warning',
                                title: 'Download em Andamento',
                                message: 'Este processo já está sendo baixado.',
                              });
                              return;
                            }

                            try {
                              await apiClient.getProcessWithAutoDownload(process.process_number, true);
                              startDownload(process.process_number, process.id);

                              addNotification({
                                type: 'success',
                                title: 'Download Iniciado',
                                message: `Download de ${process.documents_count} documento(s) iniciado.`,
                              });

                              // Redirecionar para página de downloads
                              router.push('/downloads');
                            } catch (error) {
                              addNotification({
                                type: 'error',
                                title: 'Erro ao Iniciar Download',
                                message: error instanceof Error ? error.message : 'Erro desconhecido',
                              });
                            }
                          }}
                        >
                          <Download className="h-4 w-4 mr-2" />
                          Download Assíncrono
                        </Button>
                      )}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}

          {/* Processos não encontrados */}
          {searchResults.not_found && searchResults.not_found.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-red-600 dark:text-red-400">
                  Processos Não Encontrados
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {searchResults.not_found.map((number, index) => (
                    <div key={index} className="text-sm text-gray-600 dark:text-gray-400 font-mono">
                      {number}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </div>
  );
}
