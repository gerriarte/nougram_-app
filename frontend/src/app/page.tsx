
'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  useNougram,
  decideRootRoute,
  BCR_HYDRATION_TIMEOUT_MS,
} from '@/context/NougramCoreContext';
import { useAuth } from '@/hooks/useAuth';
import { isAuthenticated as hasStoredSession } from '@/lib/auth';

/**
 * Techo total del spinner. Vencido este plazo la pantalla decide con lo que haya,
 * sin volver a mirar ninguna bandera que dependa de un request.
 */
const ROOT_DECISION_CEILING_MS = BCR_HYDRATION_TIMEOUT_MS + 2_000;

export default function RootPage() {
  const { state } = useNougram();
  const { isAuthenticated, loading } = useAuth();
  const router = useRouter();
  const [bailedOut, setBailedOut] = useState(false);

  // H18 — red de seguridad real: este timer no cuelga de ningún fetch, y su
  // resultado tampoco. `loading` (useAuth → GET /auth/me) e `isHydrated`
  // (NougramCoreContext → GET /settings/equipment) salen por `fetch`, que no tiene
  // timeout: con el backend colgado a nivel TCP ninguno de los dos settlea nunca.
  // Por eso la guarda de espera vive DENTRO de decideRootRoute y queda desactivada
  // cuando `bailedOut` es true, en vez de estar detrás de esas banderas.
  useEffect(() => {
    const timeoutId = setTimeout(() => setBailedOut(true), ROOT_DECISION_CEILING_MS);
    return () => clearTimeout(timeoutId);
  }, []);

  useEffect(() => {
    const destination = decideRootRoute({
      authLoading: loading,
      isAuthenticated,
      // Lectura sincrónica de localStorage: es lo único que sigue siendo confiable
      // cuando la sesión nunca terminó de resolverse contra el backend.
      hasStoredSession: hasStoredSession(),
      isHydrated: state.isHydrated,
      bcr: state.financials.bcr,
      bcrSource: state.financials.bcrSource,
      bailedOut,
    });

    if (destination) {
      router.replace(destination);
    }
  }, [
    loading,
    isAuthenticated,
    state.isHydrated,
    state.financials.bcr,
    state.financials.bcrSource,
    bailedOut,
    router,
  ]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center space-y-4 animate-pulse">
        <div className="w-12 h-12 border-4 border-gray-900 border-t-transparent rounded-full mx-auto animate-spin"></div>
        <p className="text-gray-500 font-medium">Cargando Nougram OS...</p>
      </div>
    </div>
  );
}
