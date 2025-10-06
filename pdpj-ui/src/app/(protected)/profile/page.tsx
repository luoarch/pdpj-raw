'use client';

import { useQuery } from '@tanstack/react-query';
import { User, Mail, Calendar, Key, Activity, Settings, LogOut } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/atoms/card';
import { Button } from '@/components/atoms/button';
import { Badge } from '@/components/atoms/badge';
import { Avatar } from '@/components/atoms/avatar';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { useAuthStore } from '@/store/auth-store';
import { apiClient } from '@/lib/api-client';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';

export default function ProfilePage() {
  const { user, logout } = useAuthStore();

  const { data: profileData, isLoading } = useQuery({
    queryKey: ['user-profile'],
    queryFn: () => apiClient.getMyProfile(),
    enabled: !!user,
  });

  const formatDate = (dateString: string) => {
    try {
      return format(new Date(dateString), 'dd/MM/yyyy HH:mm', { locale: ptBR });
    } catch {
      return dateString;
    }
  };

  const getRoleVariant = (role?: string) => {
    switch (role?.toLowerCase()) {
      case 'admin':
        return 'error';
      case 'user':
        return 'info';
      default:
        return 'default';
    }
  };

  const getStatusVariant = (active?: boolean) => {
    return active ? 'success' : 'warning';
  };

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  const currentUser = profileData || user;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Meu Perfil
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Gerencie suas informações e configurações
          </p>
        </div>
        <Button variant="outline" onClick={logout}>
          <LogOut className="h-4 w-4 mr-2" />
          Sair
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Profile Info */}
        <div className="lg:col-span-1">
          <Card>
            <CardContent className="p-6">
              <div className="text-center">
                <Avatar
                  size="xl"
                  fallback={currentUser?.username?.charAt(0).toUpperCase() || 'U'}
                  className="mx-auto mb-4"
                />
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                  {currentUser?.username}
                </h2>
                <p className="text-gray-600 dark:text-gray-400 mb-4">
                  {currentUser?.email}
                </p>
                <div className="flex justify-center gap-2 mb-4">
                  <Badge variant={getRoleVariant(currentUser?.role)}>
                    {currentUser?.role || 'Usuário'}
                  </Badge>
                  <Badge variant={getStatusVariant(currentUser?.is_active)}>
                    {currentUser?.is_active ? 'Ativo' : 'Inativo'}
                  </Badge>
                </div>
                <Button variant="outline" size="sm">
                  <Settings className="h-4 w-4 mr-2" />
                  Editar Perfil
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Profile Details */}
        <div className="lg:col-span-2 space-y-6">
          {/* Personal Information */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <User className="h-5 w-5 mr-2" />
                Informações Pessoais
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Nome de Usuário
                  </label>
                  <p className="text-sm text-gray-900 dark:text-white font-mono">
                    {currentUser?.username}
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Email
                  </label>
                  <p className="text-sm text-gray-900 dark:text-white flex items-center">
                    <Mail className="h-4 w-4 mr-2" />
                    {currentUser?.email}
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Função
                  </label>
                  <p className="text-sm text-gray-900 dark:text-white">
                    {currentUser?.role || 'Usuário'}
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Status
                  </label>
                  <Badge variant={getStatusVariant(currentUser?.is_active)}>
                    {currentUser?.is_active ? 'Ativo' : 'Inativo'}
                  </Badge>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Account Information */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Key className="h-5 w-5 mr-2" />
                Informações da Conta
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    ID do Usuário
                  </label>
                  <p className="text-sm text-gray-900 dark:text-white font-mono">
                    {currentUser?.id}
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Chave da API
                  </label>
                  <p className="text-sm text-gray-900 dark:text-white font-mono break-all">
                    {currentUser?.api_key ? `${currentUser.api_key.substring(0, 20)}...` : 'N/A'}
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Conta criada em
                  </label>
                  <p className="text-sm text-gray-900 dark:text-white flex items-center">
                    <Calendar className="h-4 w-4 mr-2" />
                    {currentUser?.created_at ? formatDate(currentUser.created_at) : 'N/A'}
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Última atualização
                  </label>
                  <p className="text-sm text-gray-900 dark:text-white flex items-center">
                    <Calendar className="h-4 w-4 mr-2" />
                    {currentUser?.updated_at ? formatDate(currentUser.updated_at) : 'N/A'}
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Último acesso
                  </label>
                  <p className="text-sm text-gray-900 dark:text-white flex items-center">
                    <Activity className="h-4 w-4 mr-2" />
                    {currentUser?.last_access ? formatDate(currentUser.last_access) : 'Nunca'}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Rate Limiting */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Activity className="h-5 w-5 mr-2" />
                Limites de Taxa
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Requests por minuto
                  </label>
                  <p className="text-sm text-gray-900 dark:text-white">
                    {currentUser?.rate_limit_requests || 'N/A'}
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Janela de tempo (segundos)
                  </label>
                  <p className="text-sm text-gray-900 dark:text-white">
                    {currentUser?.rate_limit_window || 'N/A'}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Actions */}
          <Card>
            <CardHeader>
              <CardTitle>Ações</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                <Button variant="outline">
                  <Settings className="h-4 w-4 mr-2" />
                  Alterar Senha
                </Button>
                <Button variant="outline">
                  <Key className="h-4 w-4 mr-2" />
                  Regenerar API Key
                </Button>
                <Button variant="outline">
                  <User className="h-4 w-4 mr-2" />
                  Editar Perfil
                </Button>
                <Button variant="destructive" onClick={logout}>
                  <LogOut className="h-4 w-4 mr-2" />
                  Sair da Conta
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
