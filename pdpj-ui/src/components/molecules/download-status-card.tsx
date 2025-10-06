'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/atoms/card';
import { Badge } from '@/components/atoms/badge';
import { Button } from '@/components/atoms/button';
import { ProgressBar } from './progress-bar';
import { DocumentStatusBadge } from './document-status-badge';
import { ProcessStatusResponse } from '@/lib/api-client';
import { FileText, Download, X, RefreshCw } from 'lucide-react';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';

interface DownloadStatusCardProps {
  processNumber: string;
  status: ProcessStatusResponse;
  onRefresh?: () => void;
  onCancel?: () => void;
  onDownloadDocument?: (documentId: string, downloadUrl: string) => void;
}

export function DownloadStatusCard({
  processNumber,
  status,
  onRefresh,
  onCancel,
  onDownloadDocument,
}: DownloadStatusCardProps) {
  const getOverallStatusVariant = (overallStatus: string) => {
    switch (overallStatus) {
      case 'pending':
        return 'default';
      case 'processing':
        return 'info';
      case 'completed':
        return 'success';
      case 'failed':
        return 'error';
      default:
        return 'default';
    }
  };

  const getProgressVariant = () => {
    if (status.overall_status === 'completed') return 'success';
    if (status.overall_status === 'failed') return 'error';
    if (status.progress_percentage > 50) return 'success';
    if (status.progress_percentage > 25) return 'warning';
    return 'default';
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'N/A';
    try {
      return format(new Date(dateString), 'dd/MM/yyyy HH:mm', { locale: ptBR });
    } catch {
      return dateString;
    }
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <FileText className="h-5 w-5 text-gray-600 dark:text-gray-400" />
            <div>
              <CardTitle className="text-lg">
                Processo {processNumber}
              </CardTitle>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                {status.total_documents} documento(s) total
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant={getOverallStatusVariant(status.overall_status)}>
              {status.overall_status === 'pending' && 'Pendente'}
              {status.overall_status === 'processing' && 'Processando'}
              {status.overall_status === 'completed' && 'Concluído'}
              {status.overall_status === 'failed' && 'Falhou'}
            </Badge>
            {onRefresh && (
              <Button variant="ghost" size="sm" onClick={onRefresh}>
                <RefreshCw className="h-4 w-4" />
              </Button>
            )}
            {onCancel && status.overall_status === 'processing' && (
              <Button variant="ghost" size="sm" onClick={onCancel}>
                <X className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Progress Bar */}
        <div>
          <ProgressBar
            progress={status.progress_percentage}
            label="Progresso Geral"
            variant={getProgressVariant()}
            size="lg"
          />
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
            <p className="text-sm text-gray-600 dark:text-gray-400">Completos</p>
            <p className="text-2xl font-bold text-green-600 dark:text-green-400">
              {status.completed_documents}
            </p>
          </div>
          <div className="text-center p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
            <p className="text-sm text-gray-600 dark:text-gray-400">Processando</p>
            <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">
              {status.processing_documents}
            </p>
          </div>
          <div className="text-center p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
            <p className="text-sm text-gray-600 dark:text-gray-400">Pendentes</p>
            <p className="text-2xl font-bold text-gray-600 dark:text-gray-400">
              {status.pending_documents}
            </p>
          </div>
          <div className="text-center p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
            <p className="text-sm text-gray-600 dark:text-gray-400">Falhas</p>
            <p className="text-2xl font-bold text-red-600 dark:text-red-400">
              {status.failed_documents}
            </p>
          </div>
        </div>

        {/* Documents List */}
        {status.documents && status.documents.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-3">
              Documentos ({status.documents.length})
            </h4>
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {status.documents.map((doc) => (
                <div
                  key={doc.id}
                  className="flex items-center justify-between p-3 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                >
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                      {doc.name}
                    </p>
                    {doc.error_message && (
                      <p className="text-xs text-red-600 dark:text-red-400 mt-1">
                        {doc.error_message}
                      </p>
                    )}
                    {doc.downloaded_at && (
                      <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                        Baixado em: {formatDate(doc.downloaded_at)}
                      </p>
                    )}
                  </div>
                  <div className="flex items-center gap-2 ml-4">
                    <DocumentStatusBadge status={doc.status} size="sm" />
                    {doc.download_url && onDownloadDocument && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onDownloadDocument(doc.id, doc.download_url!)}
                      >
                        <Download className="h-4 w-4" />
                      </Button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Timestamps */}
        {status.started_at && (
          <div className="text-sm text-gray-600 dark:text-gray-400 space-y-1">
            <p>Iniciado em: {formatDate(status.started_at)}</p>
            {status.estimated_completion && status.overall_status === 'processing' && (
              <p>Conclusão estimada: {formatDate(status.estimated_completion)}</p>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

