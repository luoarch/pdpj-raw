'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { ProcessList } from '@/components/organisms/process-list';
import { Process } from '@/lib/api-client';

export default function ProcessesPage() {
  const router = useRouter();

  const handleProcessSelect = (process: Process) => {
    router.push(`/processes/${process.process_number}`);
  };

  const handleProcessDownload = async (process: Process) => {
    // Implementar download de documentos
    console.log('Download process:', process);
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
    </div>
  );
}
