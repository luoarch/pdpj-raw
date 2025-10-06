import { CheckCircle, AlertCircle, AlertTriangle, Clock, XCircle } from 'lucide-react';
import { Badge } from '@/components/atoms/badge';
import { cn } from '@/lib/utils';

interface StatusIndicatorProps {
  status: string;
  size?: 'sm' | 'md' | 'lg';
  showIcon?: boolean;
  className?: string;
}

export function StatusIndicator({ 
  status, 
  size = 'md', 
  showIcon = true, 
  className 
}: StatusIndicatorProps) {
  const getStatusConfig = (status: string) => {
    const normalizedStatus = status.toLowerCase();
    
    if (normalizedStatus.includes('healthy') || normalizedStatus.includes('online') || normalizedStatus.includes('ativo')) {
      return {
        variant: 'success' as const,
        icon: CheckCircle,
        label: 'Online',
      };
    }
    
    if (normalizedStatus.includes('degraded') || normalizedStatus.includes('warning') || normalizedStatus.includes('suspenso')) {
      return {
        variant: 'warning' as const,
        icon: AlertTriangle,
        label: 'Degradado',
      };
    }
    
    if (normalizedStatus.includes('error') || normalizedStatus.includes('offline') || normalizedStatus.includes('erro')) {
      return {
        variant: 'error' as const,
        icon: XCircle,
        label: 'Offline',
      };
    }
    
    if (normalizedStatus.includes('pending') || normalizedStatus.includes('loading') || normalizedStatus.includes('pendente')) {
      return {
        variant: 'info' as const,
        icon: Clock,
        label: 'Pendente',
      };
    }
    
    // Default
    return {
      variant: 'default' as const,
      icon: AlertCircle,
      label: status,
    };
  };

  const config = getStatusConfig(status);
  const Icon = config.icon;

  return (
    <div className={cn('flex items-center gap-2', className)}>
      {showIcon && (
        <Icon className={cn(
          'flex-shrink-0',
          size === 'sm' && 'h-3 w-3',
          size === 'md' && 'h-4 w-4',
          size === 'lg' && 'h-5 w-5'
        )} />
      )}
      <Badge variant={config.variant} size={size}>
        {config.label}
      </Badge>
    </div>
  );
}
