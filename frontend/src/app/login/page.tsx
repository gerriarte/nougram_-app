'use client';

import { Suspense, useEffect, useState } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { useRouter, useSearchParams } from 'next/navigation';
import { AlertTriangle, Eye, EyeOff, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Label } from '@/components/ui/Label';
import { Alert } from '@/components/ui/Alert';
import { useAuth } from '@/hooks/useAuth';
import { apiRequest } from '@/lib/api-client';
import { trackLoginAttempt, trackLoginResult } from '@/lib/analytics';

type OrganizationResponse = {
  id?: number;
  settings?: Record<string, unknown> | null;
};

async function resolveDefaultPostLoginRoute(): Promise<{ path: string; organizationId?: string }> {
  const orgResponse = await apiRequest<OrganizationResponse>('/organizations/me');
  if (orgResponse.error || !orgResponse.data) {
    return { path: '/dashboard' };
  }
  const onboardingCompleted = Boolean(
    (orgResponse.data.settings as Record<string, unknown> | null | undefined)?.onboarding_completed
  );
  const path = onboardingCompleted ? '/dashboard' : '/onboarding';
  const organizationId = orgResponse.data.id != null ? String(orgResponse.data.id) : undefined;
  return { path, organizationId };
}

function LoginPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { login, isAuthenticated, loading, user } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (loading || !isAuthenticated) return;
    if (user?.role === 'super_admin' && !user?.organization_id) {
      router.replace('/dashboard/super-admin/accounts');
      return;
    }
    const redirectParam = searchParams.get('redirect');
    const redirectToParam = redirectParam && redirectParam.startsWith('/') ? redirectParam : null;
    if (redirectToParam) {
      router.replace(redirectToParam);
      return;
    }
    void (async () => {
      const { path } = await resolveDefaultPostLoginRoute();
      router.replace(path);
    })();
  }, [loading, isAuthenticated, router, searchParams, user]);

  const onSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    const safeEmail = String(email ?? '').trim();
    const safePassword = String(password ?? '');
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(safeEmail)) {
      setSubmitting(false);
      setError('Ingresa un correo electrónico válido.');
      return;
    }
    trackLoginAttempt();
    const result = await login(safeEmail, safePassword);
    setSubmitting(false);

    if (!result.success) {
      trackLoginResult({ success: false });
      setError(result.error || 'Error al iniciar sesión');
      return;
    }

    // Support users must pick an active tenant before tenant-scoped modules.
    if (result.user?.role === 'super_admin' && !result.user?.organization_id) {
      trackLoginResult({
        success: true,
        user_id: result.user?.id,
      });
      router.replace('/dashboard/super-admin/accounts');
      return;
    }

    const redirectParam = searchParams.get('redirect');
    const redirectToParam = redirectParam && redirectParam.startsWith('/') ? redirectParam : null;
    if (redirectToParam) {
      trackLoginResult({
        success: true,
        user_id: result.user?.id,
      });
      router.replace(redirectToParam);
      return;
    }
    const { path, organizationId } = await resolveDefaultPostLoginRoute();
    trackLoginResult({
      success: true,
      user_id: result.user?.id,
      organization_id: organizationId,
    });
    router.replace(path);
  };

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <div className="w-full max-w-md rounded-2xl bg-white shadow-sm border border-gray-200 p-8 space-y-6">
        <div className="space-y-2 text-center">
          <div className="flex justify-center mb-3">
            <Image
              src="/brand/Logo-orange.svg"
              alt="Nougram"
              width={150}
              height={35}
              priority
            />
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-gray-900">Iniciar sesión</h1>
          <p className="text-sm text-system-gray">
            Accede a Nougram con tu cuenta de organización.
          </p>
        </div>

        <form onSubmit={onSubmit} className="space-y-4">
          {error && (
            <Alert variant="critical">
              <div className="flex items-start gap-2">
                <AlertTriangle className="h-4 w-4 mt-0.5" />
                <span>{error}</span>
              </div>
            </Alert>
          )}

          <div className="space-y-2">
            <Label htmlFor="email">Correo</Label>
            <Input
              id="email"
              type="email"
              autoComplete="email"
              value={email ?? ''}
              onChange={(e) => setEmail(e.target.value)}
              required
              disabled={submitting}
              placeholder="admin@tuagencia.com"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="password">Contraseña</Label>
            <div className="relative">
              <Input
                id="password"
                type={showPassword ? 'text' : 'password'}
                autoComplete="current-password"
                value={password ?? ''}
                onChange={(e) => setPassword(e.target.value)}
                required
                disabled={submitting}
                placeholder="Tu contraseña"
                className="pr-11"
              />
              <button
                type="button"
                className="absolute inset-y-0 right-0 flex items-center px-3 text-gray-500 hover:text-gray-700"
                onClick={() => setShowPassword((prev) => !prev)}
                aria-label={showPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'}
                disabled={submitting}
              >
                {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
            <div className="text-right">
              <Link href="/forgot-password" className="text-xs font-semibold text-primary hover:underline">
                ¿Olvidaste tu contraseña?
              </Link>
            </div>
          </div>

          <Button
            type="submit"
            className="w-full h-12 rounded-xl"
            disabled={submitting}
          >
            {submitting ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Ingresando...
              </>
            ) : (
              'Ingresar'
            )}
          </Button>
        </form>

        <p className="text-center text-sm text-system-gray">
          ¿No tienes cuenta?{' '}
          <Link href="/register" className="text-primary font-semibold hover:underline">
            Regístrate
          </Link>
        </p>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-background" />}>
      <LoginPageContent />
    </Suspense>
  );
}
