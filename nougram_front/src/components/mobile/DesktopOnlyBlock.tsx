'use client';

import React from 'react';
import { Monitor } from 'lucide-react';
import { Button } from '@/components/ui/Button';

/**
 * Full-viewport message when a desktop-only module is opened on a small screen.
 */
export function DesktopOnlyBlock() {
  const copyUrl = () => {
    if (typeof window === 'undefined') return;
    const url = window.location.href;
    void navigator.clipboard.writeText(url).catch(() => {
      // ignore
    });
  };

  return (
    <div className="min-h-[calc(100vh-5rem)] flex items-center justify-center p-6 bg-gradient-to-b from-slate-50 to-white">
      <div
        className="max-w-md w-full rounded-3xl border border-slate-200/80 bg-white/90 backdrop-blur-md shadow-lg shadow-slate-200/50 p-8 text-center space-y-6"
        role="alert"
        aria-live="polite"
      >
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-primary/10 text-primary">
          <Monitor className="h-8 w-8" strokeWidth={1.75} aria-hidden />
        </div>
        <div className="space-y-2">
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">
            Disponible solo en escritorio
          </h1>
          <p className="text-sm text-slate-600 leading-relaxed">
            Costos, finanzas y administración avanzada están optimizados para pantalla grande. Abre Nougram
            desde tu computador para continuar.
          </p>
        </div>
        <div className="flex flex-col gap-3">
          <Button
            type="button"
            className="w-full h-12 rounded-2xl font-bold"
            onClick={() => {
              if (typeof window !== 'undefined') window.location.assign('/dashboard');
            }}
          >
            Ir al panel comercial
          </Button>
          <Button type="button" variant="secondary" className="w-full h-12 rounded-2xl font-semibold" onClick={copyUrl}>
            Copiar enlace de esta página
          </Button>
        </div>
        <p className="text-xs text-slate-400">
          Tip: guarda el enlace y ábrelo cuando estés en escritorio.
        </p>
      </div>
    </div>
  );
}
