'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Building2, ArrowLeft, Users, CreditCard, Hash, Save, RefreshCw } from 'lucide-react';
import { AdminLayout } from '@/components/admin/layout/AdminLayout';
import { apiRequest } from '@/lib/api-client';
import { useAuth } from '@/hooks/useAuth';

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
  const { user } = useAuth();
  const [organization, setOrganization] = useState<OrganizationResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [nameDraft, setNameDraft] = useState('');
  const [planDraft, setPlanDraft] = useState('free');
  const [savingName, setSavingName] = useState(false);
  const [savingPlan, setSavingPlan] = useState(false);
  const [nameMessage, setNameMessage] = useState<string | null>(null);
  const [planMessage, setPlanMessage] = useState<string | null>(null);

  const canManageSubscription = user?.role === 'owner' || user?.role === 'super_admin';

  const PLAN_OPTIONS = [
    { value: 'free', label: 'Free' },
    { value: 'starter', label: 'Starter' },
    { value: 'professional', label: 'Professional' },
    { value: 'enterprise', label: 'Enterprise' },
  ];

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
      setNameDraft(response.data.name || '');
      setPlanDraft(response.data.subscription_plan || 'free');
      setLoading(false);
    };

    void loadOrganization();
  }, []);

  const handleSaveName = async () => {
    if (!organization) return;
    const trimmed = nameDraft.trim();
    setNameMessage(null);
    if (!trimmed) {
      setNameMessage('El nombre de la empresa es obligatorio.');
      return;
    }

    setSavingName(true);
    const response = await apiRequest<OrganizationResponse>(`/organizations/${organization.id}`, {
      method: 'PUT',
      body: JSON.stringify({ name: trimmed }),
    });
    setSavingName(false);

    if (response.error || !response.data) {
      setNameMessage(response.error || 'No se pudo guardar el nombre de la empresa.');
      return;
    }

    setOrganization(response.data);
    setNameDraft(response.data.name);
    setNameMessage('Nombre actualizado correctamente.');
  };

  const handleSavePlan = async () => {
    if (!organization) return;
    setPlanMessage(null);

    setSavingPlan(true);
    const response = await apiRequest<OrganizationResponse>(`/organizations/${organization.id}/subscription`, {
      method: 'PUT',
      body: JSON.stringify({ plan: planDraft }),
    });
    setSavingPlan(false);

    if (response.error || !response.data) {
      setPlanMessage(response.error || 'No se pudo actualizar el tipo de suscripción.');
      return;
    }

    setOrganization(response.data);
    setPlanDraft(response.data.subscription_plan || 'free');
    setPlanMessage('Tipo de suscripción actualizado.');
  };

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
              <div className="space-y-3">
                <input
                  value={nameDraft}
                  onChange={(event) => setNameDraft(event.target.value)}
                  className="w-full h-11 rounded-xl border border-gray-200 px-3 text-sm font-semibold text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500/30"
                  placeholder="Nombre de la empresa"
                />
                <button
                  type="button"
                  onClick={handleSaveName}
                  disabled={savingName}
                  className="inline-flex items-center gap-2 rounded-xl bg-blue-600 px-3 py-2 text-xs font-bold text-white hover:bg-blue-700 disabled:opacity-60"
                >
                  {savingName ? <RefreshCw size={14} className="animate-spin" /> : <Save size={14} />}
                  Guardar nombre
                </button>
                {nameMessage && (
                  <p className={`text-xs font-semibold ${nameMessage.includes('correctamente') ? 'text-green-600' : 'text-red-600'}`}>
                    {nameMessage}
                  </p>
                )}
              </div>
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
                Tipo de suscripción
              </p>
              <div className="space-y-3">
                <select
                  value={planDraft}
                  onChange={(event) => setPlanDraft(event.target.value)}
                  disabled={!canManageSubscription}
                  className="w-full h-11 rounded-xl border border-gray-200 px-3 text-sm font-semibold text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500/30 disabled:bg-gray-100 disabled:text-gray-500"
                >
                  {PLAN_OPTIONS.map((plan) => (
                    <option key={plan.value} value={plan.value}>
                      {plan.label}
                    </option>
                  ))}
                </select>
                <button
                  type="button"
                  onClick={handleSavePlan}
                  disabled={savingPlan || !canManageSubscription}
                  className="inline-flex items-center gap-2 rounded-xl bg-blue-600 px-3 py-2 text-xs font-bold text-white hover:bg-blue-700 disabled:opacity-60"
                >
                  {savingPlan ? <RefreshCw size={14} className="animate-spin" /> : <Save size={14} />}
                  Guardar suscripción
                </button>
                {!canManageSubscription && (
                  <p className="text-xs font-semibold text-amber-600">
                    Solo Owner o Super Admin pueden cambiar la suscripción.
                  </p>
                )}
                {planMessage && (
                  <p className={`text-xs font-semibold ${planMessage.includes('actualizado') ? 'text-green-600' : 'text-red-600'}`}>
                    {planMessage}
                  </p>
                )}
              </div>
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
