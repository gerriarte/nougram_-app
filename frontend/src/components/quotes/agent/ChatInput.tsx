'use client';

import React, { useState } from 'react';
import { Send } from 'lucide-react';
import { Button } from '@/components/ui/Button';

export function ChatInput({
  onSend,
  disabled,
}: {
  onSend: (value: string) => void;
  disabled?: boolean;
}) {
  const [value, setValue] = useState('');

  const submit = () => {
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setValue('');
  };

  return (
    <div className="flex items-end gap-2 border-t border-gray-200 p-3 bg-white">
      <textarea
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            submit();
          }
        }}
        placeholder="Describe el proyecto: tipo, cliente, alcance, plazos…"
        rows={2}
        disabled={disabled}
        className="flex-1 resize-none rounded-xl border border-gray-200 px-3 py-2 text-[13px] focus:outline-none focus:ring-2 focus:ring-primary disabled:opacity-60"
      />
      <Button onClick={submit} disabled={disabled} size="icon" className="h-10 w-10 rounded-xl">
        <Send size={16} />
      </Button>
    </div>
  );
}
