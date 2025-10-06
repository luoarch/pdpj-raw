import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { apiClient, ProcessStatusResponse } from '@/lib/api-client';

interface DownloadJob {
  processNumber: string;
  processId: string;
  status: ProcessStatusResponse;
  startedAt: Date;
  lastUpdated: Date;
  webhookUrl?: string;
}

interface DownloadsState {
  // Estado
  activeDownloads: Map<string, DownloadJob>;
  completedDownloads: DownloadJob[];
  pollingIntervals: Map<string, NodeJS.Timeout>;

  // Ações
  startDownload: (processNumber: string, processId: string, webhookUrl?: string) => void;
  updateDownloadStatus: (processNumber: string, status: ProcessStatusResponse) => void;
  removeDownload: (processNumber: string) => void;
  clearCompleted: () => void;
  startPolling: (processNumber: string) => void;
  stopPolling: (processNumber: string) => void;
  getDownload: (processNumber: string) => DownloadJob | undefined;
  isDownloading: (processNumber: string) => boolean;
}

export const useDownloadsStore = create<DownloadsState>()(
  persist(
    (set, get) => ({
      activeDownloads: new Map(),
      completedDownloads: [],
      pollingIntervals: new Map(),

      startDownload: (processNumber: string, processId: string, webhookUrl?: string) => {
        const newJob: DownloadJob = {
          processNumber,
          processId,
          webhookUrl,
          status: {
            overall_status: webhookUrl ? 'pending' : 'processing',
            progress_percentage: 0,
            total_documents: 0,
            completed_documents: 0,
            pending_documents: 0,
            processing_documents: 0,
            available_documents: 0,
            failed_documents: 0,
            documents: [],
          },
          startedAt: new Date(),
          lastUpdated: new Date(),
        };

        set((state) => {
          const newMap = new Map(state.activeDownloads);
          newMap.set(processNumber, newJob);
          return { activeDownloads: newMap };
        });

        // Iniciar polling
        get().startPolling(processNumber);
      },

      updateDownloadStatus: (processNumber: string, status: ProcessStatusResponse) => {
        set((state) => {
          const newMap = new Map(state.activeDownloads);
          const existingJob = newMap.get(processNumber);

          if (existingJob) {
            const updatedJob = {
              ...existingJob,
              status,
              lastUpdated: new Date(),
            };

            // Se completou ou falhou, mover para completedDownloads
            if (status.overall_status === 'completed' || status.overall_status === 'failed') {
              newMap.delete(processNumber);
              get().stopPolling(processNumber);

              return {
                activeDownloads: newMap,
                completedDownloads: [...state.completedDownloads, updatedJob],
              };
            }

            newMap.set(processNumber, updatedJob);
          }

          return { activeDownloads: newMap };
        });
      },

      removeDownload: (processNumber: string) => {
        get().stopPolling(processNumber);
        set((state) => {
          const newMap = new Map(state.activeDownloads);
          newMap.delete(processNumber);
          return { activeDownloads: newMap };
        });
      },

      clearCompleted: () => {
        set({ completedDownloads: [] });
      },

      startPolling: (processNumber: string) => {
        // Parar polling anterior se existir
        get().stopPolling(processNumber);

        const intervalId = setInterval(async () => {
          try {
            const status = await apiClient.getProcessStatus(processNumber);
            get().updateDownloadStatus(processNumber, status);

            // Parar polling se completou ou falhou
            if (status.overall_status === 'completed' || status.overall_status === 'failed') {
              get().stopPolling(processNumber);
            }
          } catch (error) {
            console.error('Erro ao buscar status:', error);
            // Continuar polling mesmo com erro
          }
        }, 3000); // 3 segundos

        set((state) => {
          const newMap = new Map(state.pollingIntervals);
          newMap.set(processNumber, intervalId);
          return { pollingIntervals: newMap };
        });
      },

      stopPolling: (processNumber: string) => {
        const intervalId = get().pollingIntervals.get(processNumber);
        if (intervalId) {
          clearInterval(intervalId);
          set((state) => {
            const newMap = new Map(state.pollingIntervals);
            newMap.delete(processNumber);
            return { pollingIntervals: newMap };
          });
        }
      },

      getDownload: (processNumber: string) => {
        return get().activeDownloads.get(processNumber);
      },

      isDownloading: (processNumber: string) => {
        return get().activeDownloads.has(processNumber);
      },
    }),
    {
      name: 'pdpj-downloads-storage',
      partialize: (state) => ({
        completedDownloads: state.completedDownloads,
      }),
    }
  )
);

