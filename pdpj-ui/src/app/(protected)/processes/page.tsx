'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { ProcessList } from '@/components/organisms/process-list';
import { WebhookConfigModal } from '@/components/molecules/webhook-config-modal';
import { Process, apiClient } from '@/lib/api-client';
import { useDownloadsStore } from '@/store/downloads-store';
import { useAppStore } from '@/store/app-store';
import { Download, Webhook } from 'lucide-react';

export default function ProcessesPage() {
  const router = useRouter();
  const [showWebhookModal, setShowWebhookModal] = useState(false);
  const [selectedProcess, setSelectedProcess] = useState<Process | null>(null);

  const { startDownload, isDownloading } = useDownloadsStore();
  const { addNotification } = useAppStore();

  const handleProcessSelect = (process: Process) => {
    router.push(`/processes/${process.process_number}`);
  };

  const handleProcessDownload = async (process: Process) => {
    setSelectedProcess(process);

    // Verificar se já está baixando
    if (isDownloading(process.process_number)) {
      addNotification({
        type: 'warning',
        title: 'Download em Andamento',
        message: 'Este processo já está sendo baixado.',
      });
      return;
    }

    // Mostrar opções de download
    setShowWebhookModal(true);
  };

  const handleStartSimpleDownload = async () => {
    if (!selectedProcess) return;

    try {
      // Iniciar download assíncrono sem webhook
      await apiClient.getProcessWithAutoDownload(selectedProcess.process_number, true);

      // Registrar no store
      startDownload(selectedProcess.process_number, selectedProcess.id);

      addNotification({
        type: 'success',
        title: 'Download Iniciado',
        message: `Download de ${selectedProcess.documents_count || 'N/A'} documento(s) iniciado em background.`,
      });

      setShowWebhookModal(false);
      setSelectedProcess(null);
    } catch (error) {
      addNotification({
        type: 'error',
        title: 'Erro ao Iniciar Download',
        message: error instanceof Error ? error.message : 'Erro desconhecido',
      });
    }
  };

  const handleStartWebhookDownload = async (webhookUrl: string) => {
    if (!selectedProcess) return;

    try {
      // Iniciar download assíncrono com webhook
      await apiClient.getProcessWithWebhook(
        selectedProcess.process_number,
        webhookUrl,
        true
      );

      // Registrar no store
      startDownload(selectedProcess.process_number, selectedProcess.id, webhookUrl);

      addNotification({
        type: 'success',
        title: 'Download Agendado',
        message: 'Você receberá uma notificação via webhook quando concluir.',
        duration: 8000,
      });

      setShowWebhookModal(false);
      setSelectedProcess(null);
    } catch (error) {
      addNotification({
        type: 'error',
        title: 'Erro ao Agendar Download',
        message: error instanceof Error ? error.message : 'Erro desconhecido',
      });
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Meus Processos
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Processos que você já consultou anteriormente
        </p>
      </div>

      {/* Process List */}
      <ProcessList
        onProcessSelect={handleProcessSelect}
        onProcessDownload={handleProcessDownload}
      />

      {/* Webhook Config Modal */}
      {showWebhookModal && selectedProcess && (
        <WebhookConfigModal
          onClose={() => {
            setShowWebhookModal(false);
            setSelectedProcess(null);
          }}
          onConfigured={handleStartWebhookDownload}
        />
      )}
    </div>
  );
}
