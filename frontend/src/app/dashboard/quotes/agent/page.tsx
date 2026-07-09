'use client';

import React, { useCallback, useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import { ArrowLeft } from 'lucide-react';
import { AdminLayout } from '@/components/admin/layout/AdminLayout';
import { Button } from '@/components/ui/Button';
import { Alert } from '@/components/ui/Alert';
import { useNougram } from '@/context/NougramCoreContext';
import { ChatPanel, type ChatMessage } from '@/components/quotes/agent/ChatPanel';
import { QuoteEstimatePanel } from '@/components/quotes/agent/QuoteEstimatePanel';
import {
  confirmDraft,
  createConversation,
  sendMessage,
  type QuoteAgentEstimate,
} from '@/lib/quote-agent';

const GREETING: ChatMessage = {
  role: 'assistant',
  content:
    '¡Hola! Contame sobre el proyecto que querés cotizar: tipo de trabajo, cliente, alcance y plazos. Con eso te propongo servicios y horas, y calculo el precio al instante. ✨',
};

export default function QuoteAgentPage() {
  const router = useRouter();
  const { state } = useNougram();
  const currency = state.identity.primaryCurrency;
  const quoteAgentEnabled = state.features.quoteAgentEnabled;

  const [conversationId, setConversationId] = useState<number | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([GREETING]);
  const [estimate, setEstimate] = useState<QuoteAgentEstimate | null>(null);
  const [loading, setLoading] = useState(false);
  const [confirming, setConfirming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const initRef = useRef(false);

  useEffect(() => {
    if (!quoteAgentEnabled || initRef.current) return;
    initRef.current = true;
    void (async () => {
      const response = await createConversation();
      if (response.error || !response.data) {
        setError(response.error || 'No se pudo iniciar la conversación.');
        return;
      }
      setConversationId(response.data.id);
    })();
  }, [quoteAgentEnabled]);

  const handleSend = useCallback(
    async (content: string) => {
      if (!conversationId || loading) return;
      setError(null);
      setMessages((prev) => [...prev, { role: 'user', content }]);
      setLoading(true);
      const response = await sendMessage(conversationId, content);
      setLoading(false);
      if (response.error || !response.data) {
        setError(response.error || 'No se pudo procesar el mensaje.');
        return;
      }
      const assistant = response.data.assistant_message;
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: assistant.content || '' },
      ]);
      if (response.data.estimate) {
        setEstimate(response.data.estimate);
      }
    },
    [conversationId, loading]
  );

  const handleConfirm = useCallback(
    async (clientName: string) => {
      if (!conversationId || confirming) return;
      setError(null);
      setConfirming(true);
      const response = await confirmDraft(conversationId, {
        client_name: clientName,
        allow_low_margin: Boolean(estimate?.below_minimum_margin),
      });
      setConfirming(false);
      if (response.error || !response.data) {
        setError(response.error || 'No se pudo crear el borrador.');
        return;
      }
      router.push(`/dashboard/quotes/${response.data.project_id}/edit`);
    },
    [conversationId, confirming, estimate, router]
  );

  if (!quoteAgentEnabled) {
    return (
      <AdminLayout hideRightPanel>
        <div className="max-w-[600px] mx-auto py-16">
          <Alert variant="info">
            <p className="font-semibold">El Agente de Cotización no está habilitado</p>
            <p>
              Este módulo se activa por cuenta. Contactá al administrador para habilitarlo.
            </p>
          </Alert>
        </div>
      </AdminLayout>
    );
  }

  return (
    <AdminLayout hideRightPanel>
      <div className="max-w-[1400px] mx-auto space-y-3 h-[calc(100vh-120px)] flex flex-col">
        <div className="flex items-center gap-3 shrink-0">
          <Button
            variant="ghost"
            size="icon"
            className="shrink-0 h-9 w-9 rounded-xl border border-gray-200"
            onClick={() => router.back()}
          >
            <ArrowLeft size={16} />
          </Button>
          <div>
            <h1 className="text-[22px] font-bold tracking-tight text-gray-900">Cotizar con IA ✨</h1>
            <p className="text-[13px] text-gray-500">
              Describí el proyecto y creá un borrador editable en segundos.
            </p>
          </div>
        </div>

        {error && (
          <Alert variant="critical" className="shrink-0">
            <p>{error}</p>
          </Alert>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 flex-1 min-h-0">
          <ChatPanel messages={messages} onSend={handleSend} loading={loading} />
          <QuoteEstimatePanel
            estimate={estimate}
            currency={currency}
            confirming={confirming}
            onConfirm={handleConfirm}
          />
        </div>
      </div>
    </AdminLayout>
  );
}
