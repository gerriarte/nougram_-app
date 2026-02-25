'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Building2, ArrowLeft, Users, CreditCard, Hash } from 'lucide-react';
import { AdminLayout } from '@/components/admin/layout/AdminLayout';
import { apiRequest } from '@/lib/api-client';

type OrganizationResponse = {
  id: number;
  name: string;
  slug: string;
  subscription_plan?: string | null;
  subscription_status?: string | null;
  user_count?: number | null;
  settings?: Record<string, unknown> | null;
};

export default function OrganizationPage() {
  const [organization, setOrganization] = useState<OrganizationResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadOrganization = async () => {
      setLoading(true);
      setError(null);

      const response = await apiRequest<OrganizationResponse>('/organizations/me');
      if (response.error || !response.data) {
        setError(response.error || 'No se pudo cargar la información de la empresa.');
        setLoading(false);
        return;
      }

      setOrganization(response.data);
      setLoading(false);
    };

    void loadOrganization();
  }, []);

  return (
    <AdminLayout>
      <div className="max-w-5xl mx-auto px-6 py-12 space-y-8">
        <div className="space-y-4">
          <Link
            href="/dashboard"
            className="inline-flex items-center gap-2 rounded-xl border border-gray-200 bg-white px-3 py-1.5 text-xs font-bold text-gray-700 hover:bg-gray-50 transition-colors"
          >
            <ArrowLeft size={14} />
            Volver al dashboard
          </Link>

          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center text-white shadow-lg shadow-blue-500/20">
              <Building2 size={22} strokeWidth={1.5} />
            </div>
            <div>
              <h1 className="text-4xl font-bold text-gray-900 tracking-tight">Empresa</h1>
              <p className="text-system-gray font-medium">Configuración del tenant actual</p>
            </div>
          </div>
        </div>

        {loading && (
          <div className="rounded-2xl border border-gray-200 bg-white p-6 text-sm text-system-gray">
            Cargando información de la empresa...
          </div>
        )}

        {!loading && error && (
          <div className="rounded-2xl border border-red-200 bg-red-50 p-6 text-sm text-red-700">
            {error}
          </div>
        )}

        {!loading && organization && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="rounded-2xl border border-gray-200 bg-white p-5">
              <p className="text-xs font-semibold uppercase tracking-wide text-system-gray mb-1">
                Nombre
              </p>
              <p className="text-lg font-bold text-gray-900">{organization.name}</p>
            </div>

            <div className="rounded-2xl border border-gray-200 bg-white p-5">
              <p className="text-xs font-semibold uppercase tracking-wide text-system-gray mb-1 flex items-center gap-1">
                <Hash size={13} />
                Slug
              </p>
              <p className="text-lg font-bold text-gray-900">{organization.slug}</p>
            </div>

            <div className="rounded-2xl border border-gray-200 bg-white p-5">
              <p className="text-xs font-semibold uppercase tracking-wide text-system-gray mb-1 flex items-center gap-1">
                <CreditCard size={13} />
                Plan
              </p>
              <p className="text-lg font-bold text-gray-900">{organization.subscription_plan || 'free'}</p>
            </div>

            <div className="rounded-2xl border border-gray-200 bg-white p-5">
              <p className="text-xs font-semibold uppercase tracking-wide text-system-gray mb-1 flex items-center gap-1">
                <Users size={13} />
                Usuarios
              </p>
              <p className="text-lg font-bold text-gray-900">{organization.user_count ?? 0}</p>
            </div>
          </div>
        )}
      </div>
    </AdminLayout>
  );
}
