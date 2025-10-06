'use client';

import { useQuery } from '@tanstack/react-query';
import {
  User,
  FileText,
  Clock,
  Activity,
  TrendingUp,
  Calendar,
  Key,
  BarChart3,
  Download,
  Eye,
  Search
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/atoms/card';
import { Badge } from '@/components/atoms/badge';
import { Button } from '@/components/atoms/button';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { apiClient } from '@/lib/api-client';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import { useAuthStore } from '@/store/auth-store';

export function UserDashboard() {
  const { user } = useAuthStore();

  // Query para buscar dados do usuário
  const { data: profileData, isLoading: profileLoading } = useQuery({
    queryKey: ['user-profile'],
    queryFn: () => apiClient.getMyProfile(),
    enabled: !!user,
  });

  // Query para buscar processos recentes do usuário
  const { data: recentProcesses, isLoading: processesLoading } = useQuery({
    queryKey: ['recent-processes'],
    queryFn: () => apiClient.getProcesses(1, 5), // Últimos 5 processos
    enabled: !!user,
  });

  // Query para health check (para mostrar se a API está funcionando)
  const { data: healthData, isLoading: healthLoading } = useQuery({
    queryKey: ['health'],
    queryFn: () => apiClient.getHealth(),
    refetchInterval: 30000,
  });

  const isLoading = profileLoading || processesLoading || healthLoading;

  const formatDate = (dateString: string) => {
    try {
      return format(new Date(dateString), 'dd/MM/yyyy HH:mm', { locale: ptBR });
    } catch {
      return dateString;
    }
  };

  const getStatusVariant = (status: string) => {
    switch (status?.toLowerCase()) {
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

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  const currentUser = profileData || user;
  const processes = recentProcesses?.processes || [];

  return (
    <div className="space-y-6">
      {/* Welcome Section */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg p-6 text-white">
        <div>
          <h1 className="text-2xl font-bold mb-2">
            Bem-vindo, {currentUser?.username}!
          </h1>
          <p className="text-blue-100">
            Aqui está um resumo das suas atividades no PDPJ
          </p>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <div className="p-3 rounded-lg bg-blue-100 dark:bg-blue-900/20">
                <FileText className="h-6 w-6 text-blue-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  Total de Processos
                </p>
                <p className="text-2xl font-semibold text-gray-900 dark:text-white">
                  {recentProcesses?.total || 0}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <div className="p-3 rounded-lg bg-green-100 dark:bg-green-900/20">
                <Activity className="h-6 w-6 text-green-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  Último Acesso
                </p>
                <p className="text-sm font-semibold text-gray-900 dark:text-white">
                  {currentUser?.last_access ? formatDate(currentUser.last_access) : 'Nunca'}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <div className="p-3 rounded-lg bg-purple-100 dark:bg-purple-900/20">
                <Key className="h-6 w-6 text-purple-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  Limite de Requests
                </p>
                <p className="text-2xl font-semibold text-gray-900 dark:text-white">
                  {currentUser?.rate_limit_requests || 'N/A'}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <div className="p-3 rounded-lg bg-orange-100 dark:bg-orange-900/20">
                <Clock className="h-6 w-6 text-orange-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  Janela de Tempo
                </p>
                <p className="text-2xl font-semibold text-gray-900 dark:text-white">
                  {currentUser?.rate_limit_window || 'N/A'}s
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

    </div>
  );
}
