'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { AlertTriangle, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Label } from '@/components/ui/Label';
import { Alert } from '@/components/ui/Alert';
import { useAuth } from '@/hooks/useAuth';

export default function LoginPage() {
  const router = useRouter();
  const { login, isAuthenticated, loading } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!loading && isAuthenticated) {
      router.replace('/dashboard');
    }
  }, [loading, isAuthenticated, router]);

  const onSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    const result = await login(email.trim(), password);
    setSubmitting(false);

    if (!result.success) {
      setError(result.error || 'Error al iniciar sesión');
      return;
    }
    router.replace('/dashboard');
  };

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <div className="w-full max-w-md rounded-2xl bg-white shadow-sm border border-gray-200 p-8 space-y-6">
        <div className="space-y-2 text-center">
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
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              disabled={submitting}
              placeholder="admin@tuagencia.com"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="password">Contraseña</Label>
            <Input
              id="password"
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              disabled={submitting}
              placeholder="Tu contraseña"
            />
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
