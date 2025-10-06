'use client';

import { Badge } from '@/components/atoms/badge';
import { Clock, Loader2, CheckCircle, XCircle } from 'lucide-react';
import { DocumentStatus } from '@/lib/api-client';

interface DocumentStatusBadgeProps {
  status: DocumentStatus;
  size?: 'sm' | 'md' | 'lg';
  showIcon?: boolean;
}

export function DocumentStatusBadge({
  status,
  size = 'md',
  showIcon = true,
}: DocumentStatusBadgeProps) {
  const getStatusConfig = (status: DocumentStatus) => {
    switch (status) {
      case 'pending':
        return {
          variant: 'default' as const,
          label: 'Pendente',
          icon: Clock,
          color: 'text-gray-600',
        };
      case 'processing':
        return {
          variant: 'info' as const,
          label: 'Processando',
          icon: Loader2,
          color: 'text-blue-600',
        };
      case 'available':
        return {
          variant: 'success' as const,
          label: 'Disponível',
          icon: CheckCircle,
          color: 'text-green-600',
        };
      case 'failed':
        return {
          variant: 'error' as const,
          label: 'Falhou',
          icon: XCircle,
          color: 'text-red-600',
        };
      default:
        return {
          variant: 'default' as const,
          label: status,
          icon: Clock,
          color: 'text-gray-600',
        };
    }
  };

  const config = getStatusConfig(status);
  const Icon = config.icon;

  return (
    <Badge variant={config.variant} size={size} className="inline-flex items-center gap-1">
      {showIcon && <Icon className={`h-3 w-3 ${config.color} ${status === 'processing' ? 'animate-spin' : ''}`} />}
      {config.label}
    </Badge>
  );
}

