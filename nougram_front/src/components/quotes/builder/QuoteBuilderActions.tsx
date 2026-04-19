'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/Button';
import { useQuoteBuilder } from '@/context/QuoteBuilderContext';

type QuoteBuilderActionsProps = {
  variant: 'mobile' | 'desktop';
};

export function QuoteBuilderActions({ variant }: QuoteBuilderActionsProps) {
  const { state, isValid, saveQuote } = useQuoteBuilder();
  const router = useRouter();

  const handleSave = async (options?: { goToProposal?: boolean; goToDashboard?: boolean }) => {
    try {
      const projectId = await saveQuote();
      if (options?.goToProposal && projectId) {
        router.push(`/dashboard/quotes/${projectId}/proposal`);
      } else if (options?.goToDashboard) {
        router.push('/dashboard');
      }
    } catch (e) {
      const message = e instanceof Error ? e.message : 'Error guardando cotización';
      alert(message);
    }
  };

  if (variant === 'mobile') {
    return (
      <div className="rounded-2xl border border-gray-200 bg-white p-3 shadow-sm">
        <p className="text-xs font-semibold text-gray-500 mb-2.5 leading-snug">
          Revisa el resumen de rentabilidad arriba. Luego guarda, cancela o crea la propuesta.
        </p>
        <div className="grid grid-cols-2 gap-2">
          <Button
            variant="secondary"
            type="button"
            onClick={() => handleSave({ goToDashboard: true })}
            className="h-10 rounded-xl text-sm font-semibold"
          >
            Guardar
          </Button>
          <Button
            variant="ghost"
            type="button"
            onClick={() => (state.id ? router.push('/dashboard') : router.back())}
            className="h-10 rounded-xl text-sm font-semibold"
          >
            Cancelar
          </Button>
        </div>
        <Button
          type="button"
          className={`mt-2 w-full h-10 rounded-xl text-sm font-bold ${isValid ? 'bg-gray-900 hover:bg-gray-700 text-white shadow-md' : 'bg-gray-100 text-gray-400 cursor-not-allowed'}`}
          disabled={!isValid}
          onClick={() => handleSave({ goToProposal: true })}
        >
          Crear propuesta
        </Button>
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-gray-200 bg-white/95 backdrop-blur-xl shadow-lg p-3">
      <div className="flex flex-col sm:flex-row gap-2 sm:gap-3 sm:justify-end">
        <Button variant="secondary" type="button" onClick={() => handleSave({ goToDashboard: true })} className="w-full sm:w-auto h-10 rounded-xl md:rounded-md">
          Guardar
        </Button>
        <Button
          variant="ghost"
          type="button"
          onClick={() => (state.id ? router.push('/dashboard') : router.back())}
          className="w-full sm:w-auto h-10 rounded-xl md:rounded-md"
        >
          Cancelar
        </Button>
        <Button
          type="button"
          className={`w-full sm:w-auto h-10 rounded-xl md:rounded-md font-semibold ${isValid ? 'bg-gray-900 hover:bg-gray-700 text-white' : 'bg-gray-100 text-gray-400 cursor-not-allowed'}`}
          disabled={!isValid}
          onClick={() => handleSave({ goToProposal: true })}
        >
          Crear propuesta
        </Button>
      </div>
    </div>
  );
}
