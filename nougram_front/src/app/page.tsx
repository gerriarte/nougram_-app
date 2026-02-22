
'use client';

import React, { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useNougram } from '@/context/NougramCoreContext';
import { useAuth } from '@/hooks/useAuth';

export default function RootPage() {
  const { state } = useNougram();
  const { isAuthenticated, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (loading || !state.isHydrated) return;

    if (!isAuthenticated) {
      router.replace('/login');
      return;
    }

    // Critical Check: Is BCR configured?
    if (state.financials.bcr === 0) {
      router.replace('/onboarding');
    } else {
      router.replace('/dashboard');
    }

  }, [loading, isAuthenticated, state.isHydrated, state.financials.bcr, router]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center space-y-4 animate-pulse">
        <div className="w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full mx-auto animate-spin"></div>
        <p className="text-gray-500 font-medium">Cargando Nougram OS...</p>
      </div>
    </div>
  );
}
