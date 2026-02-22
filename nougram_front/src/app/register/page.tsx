'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { AlertTriangle, CheckCircle2, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Label } from '@/components/ui/Label';
import { Alert } from '@/components/ui/Alert';
import { apiRequest } from '@/lib/api-client';
import { setAuthToken } from '@/lib/auth';

type RegisterResponse = {
  access_token: string;
  token_type: string;
};

export default function RegisterPage() {
  const router = useRouter();
  const [organizationName, setOrganizationName] = useState('');
  const [organizationSlug, setOrganizationSlug] = useState('');
  const [adminFullName, setAdminFullName] = useState('');
  const [adminEmail, setAdminEmail] = useState('');
  const [adminPassword, setAdminPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const generateSlug = (name: string): string =>
    name
      .toLowerCase()
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .replace(/[^\w\s-]/g, '')
      .replace(/\s+/g, '-')
      .replace(/-+/g, '-')
      .trim()
      .slice(0, 50);

  const onOrganizationNameChange = (value: string) => {
    setOrganizationName(value);
    if (!organizationSlug) {
      setOrganizationSlug(generateSlug(value));
    }
  };

  const onSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);

    if (!organizationName.trim() || !adminEmail.trim() || !adminFullName.trim()) {
      setError('Completa todos los campos obligatorios.');
      return;
    }
    if (adminPassword.length < 8) {
      setError('La contraseña debe tener al menos 8 caracteres.');
      return;
    }
    if (adminPassword !== confirmPassword) {
      setError('Las contraseñas no coinciden.');
      return;
    }

    setSubmitting(true);
    const response = await apiRequest<RegisterResponse>('/organizations/register', {
      method: 'POST',
      body: JSON.stringify({
        organization_name: organizationName.trim(),
        organization_slug: organizationSlug.trim() || undefined,
        admin_email: adminEmail.trim(),
        admin_full_name: adminFullName.trim(),
        admin_password: adminPassword,
        subscription_plan: 'free',
      }),
    });
    setSubmitting(false);

    if (response.error || !response.data?.access_token) {
      setError(response.error || 'No fue posible crear la organización.');
      return;
    }

    setAuthToken(response.data.access_token);
    router.replace('/onboarding');
  };

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <div className="w-full max-w-lg rounded-2xl bg-white shadow-sm border border-gray-200 p-8 space-y-6">
        <div className="space-y-2 text-center">
          <h1 className="text-3xl font-bold tracking-tight text-gray-900">Crear organización</h1>
          <p className="text-sm text-system-gray">
            Configura tu cuenta principal para comenzar en Nougram.
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
            <Label htmlFor="organizationName">Nombre organización</Label>
            <Input
              id="organizationName"
              value={organizationName}
              onChange={(e) => onOrganizationNameChange(e.target.value)}
              required
              disabled={submitting}
              placeholder="Nougram Studio"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="organizationSlug">Slug</Label>
            <Input
              id="organizationSlug"
              value={organizationSlug}
              onChange={(e) => setOrganizationSlug(e.target.value)}
              disabled={submitting}
              placeholder="nougram-studio"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="adminFullName">Nombre administrador</Label>
            <Input
              id="adminFullName"
              value={adminFullName}
              onChange={(e) => setAdminFullName(e.target.value)}
              required
              disabled={submitting}
              placeholder="Nombre completo"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="adminEmail">Correo administrador</Label>
            <Input
              id="adminEmail"
              type="email"
              value={adminEmail}
              onChange={(e) => setAdminEmail(e.target.value)}
              required
              disabled={submitting}
              placeholder="admin@nougram.co"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="adminPassword">Contraseña</Label>
            <Input
              id="adminPassword"
              type="password"
              value={adminPassword}
              onChange={(e) => setAdminPassword(e.target.value)}
              required
              minLength={8}
              disabled={submitting}
              placeholder="Mínimo 8 caracteres"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="confirmPassword">Confirmar contraseña</Label>
            <Input
              id="confirmPassword"
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
              disabled={submitting}
              placeholder="Repite la contraseña"
            />
            {confirmPassword && adminPassword === confirmPassword && (
              <p className="text-xs text-green-700 flex items-center gap-1">
                <CheckCircle2 className="h-3 w-3" />
                Contraseñas coinciden
              </p>
            )}
          </div>

          <Button type="submit" className="w-full h-12 rounded-xl" disabled={submitting}>
            {submitting ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Creando cuenta...
              </>
            ) : (
              'Crear organización'
            )}
          </Button>
        </form>

        <p className="text-center text-sm text-system-gray">
          ¿Ya tienes cuenta?{' '}
          <Link href="/login" className="text-primary font-semibold hover:underline">
            Iniciar sesión
          </Link>
        </p>
      </div>
    </div>
  );
}
