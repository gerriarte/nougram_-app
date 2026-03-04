'use client';

import { Suspense, useState } from 'react';
import Link from 'next/link';
import { useSearchParams, useRouter } from 'next/navigation';
import { AlertTriangle, CheckCircle2, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Alert } from '@/components/ui/Alert';
import { apiRequest } from '@/lib/api-client';

type VerifyEmailResponse = {
  message: string;
};

function VerifyEmailContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const token = searchParams.get('token') || '';
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const onVerify = async () => {
    setError(null);
    setSuccess(null);

    if (!token) {
      setError('El enlace de verificación es inválido.');
      return;
    }

    setSubmitting(true);
    const response = await apiRequest<VerifyEmailResponse>('/auth/verify-email', {
      method: 'POST',
      body: JSON.stringify({ token }),
    });
    setSubmitting(false);

    if (response.error) {
      setError(response.error || 'No se pudo verificar el correo.');
      return;
    }

    setSuccess(response.data?.message || 'Correo verificado correctamente.');
    setTimeout(() => router.replace('/login'), 1500);
  };

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <div className="w-full max-w-md rounded-2xl bg-white shadow-sm border border-gray-200 p-8 space-y-6">
        <div className="space-y-2 text-center">
          <h1 className="text-3xl font-bold tracking-tight text-gray-900">Verificar correo</h1>
          <p className="text-sm text-system-gray">
            Confirma tu cuenta para poder iniciar sesión.
          </p>
        </div>

        {error && (
          <Alert variant="critical">
            <div className="flex items-start gap-2">
              <AlertTriangle className="h-4 w-4 mt-0.5" />
              <span>{error}</span>
            </div>
          </Alert>
        )}

        {success && (
          <Alert variant="success">
            <div className="flex items-start gap-2">
              <CheckCircle2 className="h-4 w-4 mt-0.5" />
              <span>{success}</span>
            </div>
          </Alert>
        )}

        <Button className="w-full h-12 rounded-xl" onClick={onVerify} disabled={submitting || !!success}>
          {submitting ? (
            <>
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              Verificando...
            </>
          ) : (
            'Verificar correo'
          )}
        </Button>

        <p className="text-center text-sm text-system-gray">
          <Link href="/login" className="text-primary font-semibold hover:underline">
            Ir a iniciar sesión
          </Link>
        </p>
      </div>
    </div>
  );
}

export default function VerifyEmailPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-background" />}>
      <VerifyEmailContent />
    </Suspense>
  );
}

