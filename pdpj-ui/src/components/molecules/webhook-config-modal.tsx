'use client';

import { useState } from 'react';
import { Card } from '@/components/atoms/card';
import { Button } from '@/components/atoms/button';
import { Input } from '@/components/atoms/input';
import { Badge } from '@/components/atoms/badge';
import { X, Check, AlertCircle, Loader2, Webhook } from 'lucide-react';
import { apiClient } from '@/lib/api-client';

interface WebhookConfigModalProps {
  onClose: () => void;
  onConfigured: (webhookUrl: string) => void;
}

export function WebhookConfigModal({ onClose, onConfigured }: WebhookConfigModalProps) {
  const [webhookUrl, setWebhookUrl] = useState('');
  const [isValidating, setIsValidating] = useState(false);
  const [isTesting, setIsTesting] = useState(false);
  const [validationResult, setValidationResult] = useState<{
    valid: boolean;
    error?: string;
  } | null>(null);
  const [testResult, setTestResult] = useState<{
    success: boolean;
    error?: string;
  } | null>(null);

  const handleValidate = async () => {
    if (!webhookUrl.trim()) return;

    setIsValidating(true);
    setValidationResult(null);

    try {
      const result = await apiClient.validateWebhookUrl({ webhook_url: webhookUrl });
      setValidationResult({
        valid: result.valid,
        error: result.error,
      });
    } catch (error) {
      setValidationResult({
        valid: false,
        error: 'Erro ao validar URL',
      });
    } finally {
      setIsValidating(false);
    }
  };

  const handleTestConnectivity = async () => {
    if (!webhookUrl.trim()) return;

    setIsTesting(true);
    setTestResult(null);

    try {
      const result = await apiClient.testWebhookConnectivity({ webhook_url: webhookUrl });
      setTestResult({
        success: result.success,
        error: result.error,
      });
    } catch (error) {
      setTestResult({
        success: false,
        error: 'Erro ao testar conectividade',
      });
    } finally {
      setIsTesting(false);
    }
  };

  const handleConfirm = () => {
    if (validationResult?.valid) {
      onConfigured(webhookUrl);
    }
  };

  const isValid = validationResult?.valid === true;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <Card className="w-full max-w-2xl m-4">
        <div className="p-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 dark:bg-blue-900/20 rounded-lg">
                <Webhook className="h-6 w-6 text-blue-600" />
              </div>
              <div>
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                  Configurar Webhook
                </h2>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Receba notificação quando o download concluir
                </p>
              </div>
            </div>
            <Button variant="ghost" size="sm" onClick={onClose}>
              <X className="h-5 w-5" />
            </Button>
          </div>

          {/* Form */}
          <div className="space-y-4">
            {/* URL Input */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                URL do Webhook
              </label>
              <Input
                value={webhookUrl}
                onChange={(e) => {
                  setWebhookUrl(e.target.value);
                  setValidationResult(null);
                  setTestResult(null);
                }}
                placeholder="https://myapp.com/webhook/callback"
                type="url"
              />
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                A URL deve usar HTTPS em produção
              </p>
            </div>

            {/* Validation Result */}
            {validationResult && (
              <div className={`p-4 rounded-lg border ${validationResult.valid
                  ? 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800'
                  : 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800'
                }`}>
                <div className="flex items-center gap-2">
                  {validationResult.valid ? (
                    <Check className="h-5 w-5 text-green-600" />
                  ) : (
                    <AlertCircle className="h-5 w-5 text-red-600" />
                  )}
                  <p className={`text-sm font-medium ${validationResult.valid
                      ? 'text-green-800 dark:text-green-200'
                      : 'text-red-800 dark:text-red-200'
                    }`}>
                    {validationResult.valid ? 'URL válida!' : 'URL inválida'}
                  </p>
                </div>
                {validationResult.error && (
                  <p className="text-sm text-red-700 dark:text-red-300 mt-1 ml-7">
                    {validationResult.error}
                  </p>
                )}
              </div>
            )}

            {/* Test Result */}
            {testResult && (
              <div className={`p-4 rounded-lg border ${testResult.success
                  ? 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800'
                  : 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800'
                }`}>
                <div className="flex items-center gap-2">
                  {testResult.success ? (
                    <Check className="h-5 w-5 text-green-600" />
                  ) : (
                    <AlertCircle className="h-5 w-5 text-red-600" />
                  )}
                  <p className={`text-sm font-medium ${testResult.success
                      ? 'text-green-800 dark:text-green-200'
                      : 'text-red-800 dark:text-red-200'
                    }`}>
                    {testResult.success ? 'Webhook acessível!' : 'Webhook não acessível'}
                  </p>
                </div>
                {testResult.error && (
                  <p className="text-sm text-red-700 dark:text-red-300 mt-1 ml-7">
                    {testResult.error}
                  </p>
                )}
              </div>
            )}

            {/* Info Box */}
            <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
              <h4 className="text-sm font-semibold text-blue-900 dark:text-blue-100 mb-2">
                Como funciona?
              </h4>
              <ul className="text-sm text-blue-800 dark:text-blue-200 space-y-1">
                <li>• O download será processado em background</li>
                <li>• Você receberá um callback quando concluir</li>
                <li>• O payload incluirá links S3 para todos os documentos</li>
                <li>• Retry automático em caso de falha (3 tentativas)</li>
              </ul>
            </div>

            {/* Actions */}
            <div className="flex flex-col gap-2">
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  onClick={handleValidate}
                  loading={isValidating}
                  disabled={!webhookUrl.trim()}
                  className="flex-1"
                >
                  {isValidating ? (
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  ) : (
                    <Check className="h-4 w-4 mr-2" />
                  )}
                  Validar URL
                </Button>
                <Button
                  variant="outline"
                  onClick={handleTestConnectivity}
                  loading={isTesting}
                  disabled={!isValid}
                  className="flex-1"
                >
                  {isTesting ? (
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  ) : (
                    <Webhook className="h-4 w-4 mr-2" />
                  )}
                  Testar Conectividade
                </Button>
              </div>

              <div className="flex gap-2">
                <Button
                  onClick={handleConfirm}
                  disabled={!isValid}
                  className="flex-1"
                >
                  <Check className="h-4 w-4 mr-2" />
                  Confirmar e Iniciar Download
                </Button>
                <Button variant="outline" onClick={onClose}>
                  Cancelar
                </Button>
              </div>
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
}

