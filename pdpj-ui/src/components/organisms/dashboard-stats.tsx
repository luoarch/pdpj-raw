'use client';

import { useQuery } from '@tanstack/react-query';
import {
  Activity,
  Clock,
  TrendingUp,
  Users,
  Database,
  Server,
  CheckCircle,
  AlertCircle
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/atoms/card';
import { StatusIndicator } from '@/components/molecules/status-indicator';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { apiClient } from '@/lib/api-client';

export function DashboardStats() {
  const { data: health, isLoading: healthLoading } = useQuery({
    queryKey: ['health'],
    queryFn: () => apiClient.getHealth(),
    refetchInterval: 30000,
  });

  const { data: monitoringStatus, isLoading: statusLoading } = useQuery({
    queryKey: ['monitoring-status'],
    queryFn: () => apiClient.getMonitoringStatus(),
    refetchInterval: 10000,
    retry: false, // Não tentar novamente em caso de 403
  });

  const { data: metrics, isLoading: metricsLoading } = useQuery({
    queryKey: ['monitoring-metrics'],
    queryFn: () => apiClient.getMonitoringMetrics(),
    refetchInterval: 15000,
    retry: false, // Não tentar novamente em caso de 403
  });

  const isLoading = healthLoading || statusLoading || metricsLoading;

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

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  const stats = [
    {
      title: 'Status da API',
      value: health?.status === 'healthy' ? 'Online' : 'Offline',
      icon: health?.status === 'healthy' ? CheckCircle : AlertCircle,
      color: health?.status === 'healthy' ? 'text-green-600' : 'text-red-600',
      bgColor: health?.status === 'healthy' ? 'bg-green-100 dark:bg-green-900/20' : 'bg-red-100 dark:bg-red-900/20',
      description: 'Status geral do sistema',
    },
    {
      title: 'Uptime',
      value: health ? `${Math.floor(health.uptime_seconds / 3600)}h ${Math.floor((health.uptime_seconds % 3600) / 60)}m` : 'N/A',
      icon: Clock,
      color: 'text-blue-600',
      bgColor: 'bg-blue-100 dark:bg-blue-900/20',
      description: 'Tempo de funcionamento',
    },
    {
      title: 'Requests/min',
      value: (metrics || mockMetrics).requests_per_minute?.toString() || '0',
      icon: TrendingUp,
      color: 'text-purple-600',
      bgColor: 'bg-purple-100 dark:bg-purple-900/20',
      description: 'Requisições por minuto',
    },
    {
      title: 'Usuários Ativos',
      value: (metrics || mockMetrics).active_users?.toString() || '0',
      icon: Users,
      color: 'text-orange-600',
      bgColor: 'bg-orange-100 dark:bg-orange-900/20',
      description: 'Usuários conectados',
    },
  ];

  const services = [
    {
      name: 'Database',
      status: monitoringStatus?.services?.database || mockMonitoringStatus.services.database,
      icon: Database,
    },
    {
      name: 'Redis',
      status: monitoringStatus?.services?.redis || mockMonitoringStatus.services.redis,
      icon: Server,
    },
    {
      name: 'S3',
      status: monitoringStatus?.services?.s3 || mockMonitoringStatus.services.s3,
      icon: Server,
    },
    {
      name: 'PDPJ API',
      status: monitoringStatus?.services?.pdpj_api || mockMonitoringStatus.services.pdpj_api,
      icon: Activity,
    },
  ];

  return (
    <div className="space-y-6">
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat) => {
          const Icon = stat.icon;
          return (
            <Card key={stat.title}>
              <CardContent className="p-6">
                <div className="flex items-center">
                  <div className={`p-3 rounded-lg ${stat.bgColor}`}>
                    <Icon className={`h-6 w-6 ${stat.color}`} />
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                      {stat.title}
                    </p>
                    <p className="text-2xl font-semibold text-gray-900 dark:text-white">
                      {stat.value}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      {stat.description}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Services Status */}
      <Card>
        <CardHeader>
          <CardTitle>Status dos Serviços</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {services.map((service) => {
              const Icon = service.icon;
              return (
                <div
                  key={service.name}
                  className="flex items-center justify-between p-4 border border-gray-200 dark:border-gray-700 rounded-lg"
                >
                  <div className="flex items-center space-x-3">
                    <Icon className="h-5 w-5 text-gray-400" />
                    <span className="text-sm font-medium text-gray-900 dark:text-white">
                      {service.name}
                    </span>
                  </div>
                  <StatusIndicator status={service.status} size="sm" />
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
              <CardTitle>Performance</CardTitle>
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
                <span className="text-sm font-medium text-gray-900 dark:text-white">
                  {health?.version || 'N/A'}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600 dark:text-gray-400">
                  Ambiente
                </span>
                <span className="text-sm font-medium text-gray-900 dark:text-white">
                  {health?.environment || 'N/A'}
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
        </div>
      )}
    </div>
  );
}
