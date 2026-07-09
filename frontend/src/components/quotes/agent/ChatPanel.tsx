'use client';

import React, { useEffect, useRef } from 'react';
import { Sparkles } from 'lucide-react';
import { MessageBubble } from './MessageBubble';
import { ChatInput } from './ChatInput';

export type ChatMessage = { role: string; content: string };

export function ChatPanel({
  messages,
  onSend,
  loading,
}: {
  messages: ChatMessage[];
  onSend: (value: string) => void;
  loading: boolean;
}) {
  const bottomRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  return (
    <div className="flex flex-col h-full rounded-2xl border border-gray-200 bg-gray-50 overflow-hidden">
      <div className="flex items-center gap-2 border-b border-gray-200 bg-white px-4 py-3">
        <Sparkles size={18} className="text-primary" />
        <h2 className="text-[14px] font-bold text-gray-900">Agente de Cotización</h2>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {messages.map((message, index) => (
          <MessageBubble key={index} role={message.role} content={message.content} />
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="rounded-2xl rounded-bl-sm bg-white border border-gray-200 px-4 py-2.5 text-[13px] text-gray-400">
              Pensando…
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <ChatInput onSend={onSend} disabled={loading} />
    </div>
  );
}
