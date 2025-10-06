'use client';

import { FileText, Calendar, User, Download, Eye } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/atoms/card';
import { Button } from '@/components/atoms/button';
import { Badge } from '@/components/atoms/badge';
import { Process } from '@/lib/api-client';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';

interface ProcessCardProps {
  process: Process;
  onView?: (process: Process) => void;
  onDownload?: (process: Process) => void;
}

export function ProcessCard({ process, onView, onDownload }: ProcessCardProps) {
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

  const formatDate = (dateString: string) => {
    try {
      return format(new Date(dateString), 'dd/MM/yyyy', { locale: ptBR });
    } catch {
      return dateString;
    }
  };

  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex-1 min-w-0">
            <CardTitle className="text-lg font-semibold text-gray-900 dark:text-white truncate">
              {process.title || 'Processo sem título'}
            </CardTitle>
            <p className="text-sm text-gray-600 dark:text-gray-400 font-mono mt-1">
              {process.process_number}
            </p>
          </div>
          <Badge variant={getStatusVariant(process.status)}>
            {process.status}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="pt-0">
        <div className="space-y-3">
          {/* Informações do processo */}
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div className="flex items-center text-gray-600 dark:text-gray-400">
              <Calendar className="h-4 w-4 mr-2" />
              <span>Criado em {formatDate(process.created_at)}</span>
            </div>
            {process.documents_count !== undefined && (
              <div className="flex items-center text-gray-600 dark:text-gray-400">
                <FileText className="h-4 w-4 mr-2" />
                <span>{process.documents_count} documentos</span>
              </div>
            )}
          </div>

          {/* Partes envolvidas */}
          {process.parties && process.parties.length > 0 && (
            <div className="text-sm">
              <div className="flex items-center text-gray-600 dark:text-gray-400 mb-1">
                <User className="h-4 w-4 mr-2" />
                <span className="font-medium">Partes:</span>
              </div>
              <div className="text-gray-500 dark:text-gray-400 ml-6">
                {process.parties.slice(0, 2).join(', ')}
                {process.parties.length > 2 && ` e mais ${process.parties.length - 2}`}
              </div>
            </div>
          )}

          {/* Ações */}
          <div className="flex gap-2 pt-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => onView?.(process)}
              className="flex-1"
            >
              <Eye className="h-4 w-4 mr-2" />
              Visualizar
            </Button>
            {process.documents_count && process.documents_count > 0 && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => onDownload?.(process)}
                className="flex-1"
              >
                <Download className="h-4 w-4 mr-2" />
                Download
              </Button>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
