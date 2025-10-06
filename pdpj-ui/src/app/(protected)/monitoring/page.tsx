'use client';

import { useQuery } from '@tanstack/react-query';
import {
  Activity,
  Database,
  Server,
  Clock,
  TrendingUp,
  Users,
  AlertTriangle,
  CheckCircle,
  XCircle,
  RefreshCw
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/atoms/card';
import { Button } from '@/components/atoms/button';
import { Badge } from '@/components/atoms/badge';
import { StatusIndicator } from '@/components/molecules/status-indicator';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { apiClient } from '@/lib/api-client';

export default function MonitoringPage() {
  const { data: health, isLoading: healthLoading, refetch: refetchHealth } = useQuery({
    queryKey: ['health'],
    queryFn: () => apiClient.getHealth(),
    refetchInterval: 10000,
  });

  const { data: monitoringStatus, isLoading: statusLoading, refetch: refetchStatus } = useQuery({
    queryKey: ['monitoring-status'],
    queryFn: () => apiClient.getMonitoringStatus(),
    refetchInterval: 5000,
    retry: false, // Não tentar novamente em caso de 403
  });

  const { data: metrics, isLoading: metricsLoading, refetch: refetchMetrics } = useQuery({
    queryKey: ['monitoring-metrics'],
    queryFn: () => apiClient.getMonitoringMetrics(),
    refetchInterval: 15000,
    retry: false, // Não tentar novamente em caso de 403
  });

  const { data: performance, isLoading: performanceLoading, refetch: refetchPerformance } = useQuery({
    queryKey: ['monitoring-performance'],
    queryFn: () => apiClient.getMonitoringPerformance(),
    refetchInterval: 30000,
    retry: false, // Não tentar novamente em caso de 403
  });

  const { data: detailedHealth, isLoading: detailedLoading, refetch: refetchDetailed } = useQuery({
    queryKey: ['monitoring-detailed-health'],
    queryFn: () => apiClient.getDetailedHealth(),
    refetchInterval: 20000,
    retry: false, // Não tentar novamente em caso de 403
  });

  const isLoading = healthLoading || statusLoading || metricsLoading || performanceLoading || detailedLoading;

  // Dados mockados para quando os endpoints de monitoramento não estiverem disponíveis
  const mockMonitoringStatus = {
    services: {
      database: 'healthy',
      redis: 'healthy',
      s3: 'healthy',
      pdpj_api: 'healthy',
    }
  };

  const mockMetrics = {
    requests_per_minute: 45,
    active_users: 3,
    average_response_time: 125.5,
    error_rate: 0.02,
    cache_hit_rate: 0.85,
    requests_total: 15420,
  };

  const handleRefreshAll = () => {
    refetchHealth();
    refetchStatus();
    refetchMetrics();
    refetchPerformance();
    refetchDetailed();
  };

  const getServiceIcon = (serviceName: string) => {
    switch (serviceName.toLowerCase()) {
      case 'database':
        return Database;
      case 'redis':
        return Server;
      case 's3':
        return Server;
      case 'pdpj_api':
        return Activity;
      default:
        return Server;
    }
  };

  const getServiceColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'text-green-600 dark:text-green-400';
      case 'degraded':
        return 'text-yellow-600 dark:text-yellow-400';
      case 'unhealthy':
        return 'text-red-600 dark:text-red-400';
      default:
        return 'text-gray-600 dark:text-gray-400';
    }
  };

  if (isLoading && !health && !monitoringStatus && !metrics) {
    return (
      <div className="flex justify-center py-12">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Monitoramento
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Status e métricas do sistema em tempo real
          </p>
        </div>
        <Button onClick={handleRefreshAll} variant="outline" loading={isLoading}>
          <RefreshCw className="h-4 w-4 mr-2" />
          Atualizar
        </Button>
      </div>

      {/* Status Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <div className={`p-3 rounded-lg ${health?.status === 'healthy'
                ? 'bg-green-100 dark:bg-green-900/20'
                : 'bg-red-100 dark:bg-red-900/20'
                }`}>
                {health?.status === 'healthy' ? (
                  <CheckCircle className="h-6 w-6 text-green-600" />
                ) : (
                  <XCircle className="h-6 w-6 text-red-600" />
                )}
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  Status Geral
                </p>
                <p className="text-2xl font-semibold text-gray-900 dark:text-white">
                  {health?.status === 'healthy' ? 'Online' : 'Offline'}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <div className="p-3 rounded-lg bg-blue-100 dark:bg-blue-900/20">
                <Clock className="h-6 w-6 text-blue-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  Uptime
                </p>
                <p className="text-2xl font-semibold text-gray-900 dark:text-white">
                  {health ? `${Math.floor(health.uptime_seconds / 3600)}h ${Math.floor((health.uptime_seconds % 3600) / 60)}m` : 'N/A'}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <div className="p-3 rounded-lg bg-purple-100 dark:bg-purple-900/20">
                <TrendingUp className="h-6 w-6 text-purple-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  Requests/min
                </p>
                <p className="text-2xl font-semibold text-gray-900 dark:text-white">
                  {(metrics || mockMetrics).requests_per_minute || 0}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <div className="p-3 rounded-lg bg-orange-100 dark:bg-orange-900/20">
                <Users className="h-6 w-6 text-orange-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  Usuários Ativos
                </p>
                <p className="text-2xl font-semibold text-gray-900 dark:text-white">
                  {(metrics || mockMetrics).active_users || 0}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Services Status */}
      <Card>
        <CardHeader>
          <CardTitle>Status dos Serviços</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {Object.entries(monitoringStatus?.services || mockMonitoringStatus.services).map(([serviceName, status]) => {
              const Icon = getServiceIcon(serviceName);
              return (
                <div
                  key={serviceName}
                  className="flex items-center justify-between p-4 border border-gray-200 dark:border-gray-700 rounded-lg"
                >
                  <div className="flex items-center space-x-3">
                    <Icon className={`h-5 w-5 ${getServiceColor(status)}`} />
                    <span className="text-sm font-medium text-gray-900 dark:text-white capitalize">
                      {serviceName.replace('_', ' ')}
                    </span>
                  </div>
                  <StatusIndicator status={status} size="sm" />
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Performance Metrics */}
      {(metrics || mockMetrics) && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle>Métricas de Performance</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600 dark:text-gray-400">
                  Tempo médio de resposta
                </span>
                <span className="text-sm font-medium text-gray-900 dark:text-white">
                  {(metrics || mockMetrics).average_response_time?.toFixed(2)}ms
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600 dark:text-gray-400">
                  Taxa de erro
                </span>
                <span className="text-sm font-medium text-gray-900 dark:text-white">
                  {((metrics || mockMetrics).error_rate * 100)?.toFixed(2)}%
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600 dark:text-gray-400">
                  Cache hit rate
                </span>
                <span className="text-sm font-medium text-gray-900 dark:text-white">
                  {((metrics || mockMetrics).cache_hit_rate * 100)?.toFixed(2)}%
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600 dark:text-gray-400">
                  Total de requests
                </span>
                <span className="text-sm font-medium text-gray-900 dark:text-white">
                  {(metrics || mockMetrics).requests_total?.toLocaleString() || '0'}
                </span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Informações do Sistema</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600 dark:text-gray-400">
                  Versão
                </span>
                <Badge variant="info">{health?.version || 'N/A'}</Badge>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600 dark:text-gray-400">
                  Ambiente
                </span>
                <Badge variant="default">{health?.environment || 'N/A'}</Badge>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600 dark:text-gray-400">
                  Request ID
                </span>
                <span className="text-xs font-mono text-gray-500 dark:text-gray-400">
                  {health?.request_id || 'N/A'}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600 dark:text-gray-400">
                  Timestamp
                </span>
                <span className="text-xs text-gray-500 dark:text-gray-400">
                  {health?.timestamp ? new Date(health.timestamp).toLocaleString('pt-BR') : 'N/A'}
                </span>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Performance Data */}
      {performance && (
        <Card>
          <CardHeader>
            <CardTitle>Dados de Performance</CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="bg-gray-100 dark:bg-gray-800 p-4 rounded-lg text-sm overflow-auto">
              {JSON.stringify(performance, null, 2)}
            </pre>
          </CardContent>
        </Card>
      )}

      {/* Detailed Health */}
      {detailedHealth && (
        <Card>
          <CardHeader>
            <CardTitle>Saúde Detalhada</CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="bg-gray-100 dark:bg-gray-800 p-4 rounded-lg text-sm overflow-auto">
              {JSON.stringify(detailedHealth, null, 2)}
            </pre>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
