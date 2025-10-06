import { DashboardStats } from '@/components/organisms/dashboard-stats';

export default function SystemMonitoringPage() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Monitoramento do Sistema
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Visão geral do sistema PDPJ e métricas de performance
        </p>
      </div>

      {/* System Monitoring Stats */}
      <DashboardStats />
    </div>
  );
}
