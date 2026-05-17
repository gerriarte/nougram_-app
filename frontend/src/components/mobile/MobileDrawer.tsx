'use client';

import React, { useEffect } from 'react';
import { X } from 'lucide-react';

type MobileDrawerProps = {
  open: boolean;
  onClose: () => void;
  title?: string;
  children: React.ReactNode;
};

/**
 * Material-inspired modal drawer (touch-friendly). No extra UI deps.
 */
export function MobileDrawer({ open, onClose, title = 'Menú', children }: MobileDrawerProps) {
  useEffect(() => {
    if (!open) return;
    const prev = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = prev;
    };
  }, [open]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[100] md:hidden" role="dialog" aria-modal="true" aria-label={title}>
      <button
        type="button"
        className="absolute inset-0 bg-slate-900/40 backdrop-blur-[2px]"
        aria-label="Cerrar menú"
        onClick={onClose}
      />
      <div className="absolute left-0 top-0 bottom-0 w-[min(100vw-3rem,20rem)] bg-white shadow-2xl shadow-slate-900/15 flex flex-col">
        <div className="flex items-center justify-between px-4 py-4 border-b border-slate-100">
          <span className="text-sm font-bold text-slate-800 tracking-tight">{title}</span>
          <button
            type="button"
            onClick={onClose}
            className="h-10 w-10 rounded-xl border border-slate-200 flex items-center justify-center text-slate-600 hover:bg-slate-50"
            aria-label="Cerrar"
          >
            <X size={20} />
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-3">{children}</div>
      </div>
    </div>
  );
}
