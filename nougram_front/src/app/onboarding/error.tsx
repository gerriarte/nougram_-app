'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/Button';
import { apiRequest } from '@/lib/api-client';

type OnboardingErrorProps = {
    error: Error & { digest?: string };
    reset: () => void;
};

export default function OnboardingError({ error, reset }: OnboardingErrorProps) {
    const router = useRouter();
    const [clearing, setClearing] = useState(false);
    const [clearMessage, setClearMessage] = useState<string | null>(null);

    useEffect(() => {
        // Keep full trace in console for debugging in staging/prod.
        console.error('Onboarding route crashed:', error);
    }, [error]);

    const handleClearDraft = async () => {
        setClearing(true);
        setClearMessage(null);
        const response = await apiRequest('/onboarding/draft', {
            method: 'POST',
            body: JSON.stringify({ data: {} }),
        });
        setClearing(false);
        if (response.error) {
            setClearMessage(`No se pudo limpiar el borrador: ${response.error}`);
            return;
        }
        setClearMessage('Borrador limpiado. Reintentando...');
        reset();
    };

    return (
        <main className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
            <div className="max-w-xl w-full bg-white border border-gray-200 rounded-xl p-6 space-y-4 shadow-sm">
                <h1 className="text-xl font-bold text-gray-900">Ocurrió un error en onboarding</h1>
                <p className="text-sm text-gray-600">
                    Ya registramos el error en consola para diagnóstico. Puedes reintentar o limpiar el borrador guardado.
                </p>
                {error?.message && (
                    <p className="text-xs text-red-700 bg-red-50 border border-red-200 rounded p-2">
                        {error.message}
                    </p>
                )}
                {clearMessage && (
                    <p className="text-xs text-blue-700 bg-blue-50 border border-blue-200 rounded p-2">
                        {clearMessage}
                    </p>
                )}
                <div className="flex flex-wrap gap-2">
                    <Button onClick={reset}>
                        Reintentar
                    </Button>
                    <Button variant="secondary" onClick={handleClearDraft} disabled={clearing}>
                        {clearing ? 'Limpiando...' : 'Limpiar borrador'}
                    </Button>
                    <Button variant="secondary" onClick={() => router.push('/login')}>
                        Ir a login
                    </Button>
                </div>
            </div>
        </main>
    );
}
