'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import {
  Building2,
  ArrowLeft,
  Users,
  CreditCard,
  Save,
  RefreshCw,
  Coins,
  IdCard,
  FileText,
  MapPin,
} from 'lucide-react';
import { AdminLayout } from '@/components/admin/layout/AdminLayout';
import { apiRequest } from '@/lib/api-client';
import { useAuth } from '@/hooks/useAuth';
import { settingsService } from '@/services/settingsService';
import { useNougram } from '@/context/NougramCoreContext';

type OrganizationSettings = {
  nit?: string;
  employee_count?: number;
  origin_country?: string;
  origin_city?: string;
  [key: string]: unknown;
};

type OrganizationResponse = {
  id: number;
  name: string;
  slug: string;
  subscription_plan?: string | null;
  subscription_status?: string | null;
  user_count?: number | null;
  settings?: OrganizationSettings | null;
};

export default function OrganizationPage() {
  const { user } = useAuth();
  const { updateIdentity } = useNougram();

  const [organization, setOrganization] = useState<OrganizationResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [legalNameDraft, setLegalNameDraft] = useState('');
  const [nitDraft, setNitDraft] = useState('');
  const [employeeCountDraft, setEmployeeCountDraft] = useState('');
  const [originCountryDraft, setOriginCountryDraft] = useState('');
  const [originCityDraft, setOriginCityDraft] = useState('');

  const [planDraft, setPlanDraft] = useState('free');
  const [currencyDraft, setCurrencyDraft] = useState('COP');
  const [availableCurrencies, setAvailableCurrencies] = useState<string[]>(['USD', 'COP', 'ARS', 'EUR', 'PEN', 'MXN']);

  const [savingProfile, setSavingProfile] = useState(false);
  const [savingPlan, setSavingPlan] = useState(false);
  const [savingCurrency, setSavingCurrency] = useState(false);

  const [profileMessage, setProfileMessage] = useState<string | null>(null);
  const [planMessage, setPlanMessage] = useState<string | null>(null);
  const [currencyMessage, setCurrencyMessage] = useState<string | null>(null);

  const canManageCompanyProfile =
    user?.role === 'owner' || user?.role === 'super_admin' || user?.role === 'admin_financiero';
  const canManageSubscription = user?.role === 'owner' || user?.role === 'super_admin';
  const canManageCurrency = user?.role === 'owner' || user?.role === 'super_admin';

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

      const [organizationResponse, currencyResponse] = await Promise.all([
        apiRequest<OrganizationResponse>('/organizations/me'),
        settingsService.getCurrencySettings(),
      ]);

      if (organizationResponse.error || !organizationResponse.data) {
        setError(organizationResponse.error || 'No se pudo cargar la información de la empresa.');
        setLoading(false);
        return;
      }

      const org = organizationResponse.data;
      const orgSettings = (org.settings || {}) as OrganizationSettings;

      setOrganization(org);
      setLegalNameDraft(org.name || '');
      setNitDraft(String(orgSettings.nit || ''));
      setEmployeeCountDraft(
        orgSettings.employee_count != null ? String(orgSettings.employee_count) : ''
      );
      setOriginCountryDraft(String(orgSettings.origin_country || ''));
      setOriginCityDraft(String(orgSettings.origin_city || ''));
      setPlanDraft(org.subscription_plan || 'free');

      if (currencyResponse?.primary_currency) {
        setCurrencyDraft(currencyResponse.primary_currency);
      }
      if (currencyResponse?.available_currencies?.length) {
        const codes = currencyResponse.available_currencies
          .map((option) => option?.code)
          .filter((code): code is string => Boolean(code));
        if (codes.length) setAvailableCurrencies(codes);
      }

      setLoading(false);
    };

    void loadOrganization();
  }, []);

  const handleSaveCompanyProfile = async () => {
    if (!organization) return;
    setProfileMessage(null);

    const normalizedName = legalNameDraft.trim();
    if (!normalizedName) {
      setProfileMessage('La razón social es obligatoria.');
      return;
    }

    const parsedEmployeeCount = employeeCountDraft.trim() === ''
      ? null
      : Number(employeeCountDraft);

    if (parsedEmployeeCount != null && (!Number.isFinite(parsedEmployeeCount) || parsedEmployeeCount < 0)) {
      setProfileMessage('El número de empleados debe ser un valor mayor o igual a 0.');
      return;
    }

    setSavingProfile(true);
    const response = await apiRequest<OrganizationResponse>(`/organizations/${organization.id}`, {
      method: 'PUT',
      body: JSON.stringify({
        name: normalizedName,
        settings: {
          nit: nitDraft.trim() || null,
          employee_count: parsedEmployeeCount,
          origin_country: originCountryDraft.trim() || null,
          origin_city: originCityDraft.trim() || null,
        },
      }),
    });
    setSavingProfile(false);

    if (response.error || !response.data) {
      setProfileMessage(response.error || 'No se pudo guardar la ficha de empresa.');
      return;
    }

    const org = response.data;
    const orgSettings = (org.settings || {}) as OrganizationSettings;
    setOrganization(org);
    setLegalNameDraft(org.name || '');
    setNitDraft(String(orgSettings.nit || ''));
    setEmployeeCountDraft(orgSettings.employee_count != null ? String(orgSettings.employee_count) : '');
    setOriginCountryDraft(String(orgSettings.origin_country || ''));
    setOriginCityDraft(String(orgSettings.origin_city || ''));
    updateIdentity({ name: org.name });
    setProfileMessage('Ficha de empresa actualizada correctamente.');
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

  const handleSaveCurrency = async () => {
    setCurrencyMessage(null);
    setSavingCurrency(true);
    const updated = await settingsService.updatePrimaryCurrency(currencyDraft);
    setSavingCurrency(false);

    if (!updated) {
      setCurrencyMessage('No se pudo actualizar la moneda principal.');
      return;
    }

    updateIdentity({ primaryCurrency: updated.primary_currency as 'COP' | 'USD' | 'EUR' | 'ARS' | 'PEN' | 'MXN' });
    setCurrencyDraft(updated.primary_currency);
    if (updated.available_currencies?.length) {
      const codes = updated.available_currencies
        .map((option) => option?.code)
        .filter((code): code is string => Boolean(code));
      if (codes.length) setAvailableCurrencies(codes);
    }
    setCurrencyMessage('Moneda principal actualizada correctamente.');
  };

  return (
    <AdminLayout>
      <div className="max-w-6xl mx-auto px-6 py-10 space-y-8">
        <div className="space-y-4">
          <Link
            href="/dashboard"
            className="inline-flex items-center gap-2 rounded-xl border border-gray-200 bg-white px-3 py-1.5 text-xs font-bold text-gray-700 hover:bg-gray-50 transition-colors"
          >
            <ArrowLeft size={14} />
            Volver al dashboard
          </Link>

          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gray-900 rounded-xl flex items-center justify-center text-white">
              <Building2 size={22} strokeWidth={1.5} />
            </div>
            <div>
              <h1 className="text-[22px] font-bold text-gray-900 tracking-tight">Empresa</h1>
              <p className="text-system-gray font-medium">Ficha general de la empresa</p>
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
          <>
            <section className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm space-y-5">
              <div>
                <h2 className="text-xl font-bold text-gray-900">Datos de empresa</h2>
                <p className="text-sm text-gray-500 mt-1">
                  Registra la información base para uso administrativo y reportes.
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <label className="space-y-1.5">
                  <span className="text-xs font-semibold text-gray-500 uppercase tracking-wide flex items-center gap-1">
                    <FileText size={13} /> Razón Social
                  </span>
                  <input
                    value={legalNameDraft}
                    onChange={(event) => setLegalNameDraft(event.target.value)}
                    disabled={!canManageCompanyProfile}
                    className="w-full h-11 rounded-xl border border-gray-200 px-3 text-sm font-semibold text-gray-900 focus:outline-none focus:ring-2 focus:ring-gray-400/30 disabled:bg-gray-100 disabled:text-gray-500"
                    placeholder="Razón social"
                  />
                </label>

                <label className="space-y-1.5">
                  <span className="text-xs font-semibold text-gray-500 uppercase tracking-wide flex items-center gap-1">
                    <IdCard size={13} /> NIT
                  </span>
                  <input
                    value={nitDraft}
                    onChange={(event) => setNitDraft(event.target.value)}
                    disabled={!canManageCompanyProfile}
                    className="w-full h-11 rounded-xl border border-gray-200 px-3 text-sm font-semibold text-gray-900 focus:outline-none focus:ring-2 focus:ring-gray-400/30 disabled:bg-gray-100 disabled:text-gray-500"
                    placeholder="NIT"
                  />
                </label>

                <label className="space-y-1.5">
                  <span className="text-xs font-semibold text-gray-500 uppercase tracking-wide flex items-center gap-1">
                    <Users size={13} /> Número de empleados
                  </span>
                  <input
                    type="number"
                    min={0}
                    value={employeeCountDraft}
                    onChange={(event) => setEmployeeCountDraft(event.target.value)}
                    disabled={!canManageCompanyProfile}
                    className="w-full h-11 rounded-xl border border-gray-200 px-3 text-sm font-semibold text-gray-900 focus:outline-none focus:ring-2 focus:ring-gray-400/30 disabled:bg-gray-100 disabled:text-gray-500"
                    placeholder="Ej: 25"
                  />
                </label>

                <label className="space-y-1.5">
                  <span className="text-xs font-semibold text-gray-500 uppercase tracking-wide flex items-center gap-1">
                    <MapPin size={13} /> País de origen
                  </span>
                  <input
                    value={originCountryDraft}
                    onChange={(event) => setOriginCountryDraft(event.target.value)}
                    disabled={!canManageCompanyProfile}
                    className="w-full h-11 rounded-xl border border-gray-200 px-3 text-sm font-semibold text-gray-900 focus:outline-none focus:ring-2 focus:ring-gray-400/30 disabled:bg-gray-100 disabled:text-gray-500"
                    placeholder="Ej: Colombia"
                  />
                </label>

                <label className="space-y-1.5 md:col-span-2">
                  <span className="text-xs font-semibold text-gray-500 uppercase tracking-wide flex items-center gap-1">
                    <MapPin size={13} /> Ciudad de origen
                  </span>
                  <input
                    value={originCityDraft}
                    onChange={(event) => setOriginCityDraft(event.target.value)}
                    disabled={!canManageCompanyProfile}
                    className="w-full h-11 rounded-xl border border-gray-200 px-3 text-sm font-semibold text-gray-900 focus:outline-none focus:ring-2 focus:ring-gray-400/30 disabled:bg-gray-100 disabled:text-gray-500"
                    placeholder="Ej: Bogotá"
                  />
                </label>
              </div>

              <div className="flex items-center gap-3">
                <button
                  type="button"
                  onClick={handleSaveCompanyProfile}
                  disabled={savingProfile || !canManageCompanyProfile}
                  className="inline-flex items-center gap-2 rounded-xl bg-gray-900 px-4 py-2.5 text-xs font-bold text-white hover:bg-gray-700 disabled:opacity-60"
                >
                  {savingProfile ? <RefreshCw size={14} className="animate-spin" /> : <Save size={14} />}
                  Guardar ficha de empresa
                </button>
                {!canManageCompanyProfile && (
                  <p className="text-xs font-semibold text-amber-600">
                    No tienes permisos para editar la ficha de empresa.
                  </p>
                )}
              </div>

              {profileMessage && (
                <p className={`text-xs font-semibold ${profileMessage.includes('correctamente') ? 'text-green-600' : 'text-red-600'}`}>
                  {profileMessage}
                </p>
              )}
            </section>

            <section className="grid grid-cols-1 lg:grid-cols-3 gap-4">
              <div className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm lg:col-span-2 space-y-4">
                <h3 className="text-lg font-bold text-gray-900">Configuración operativa</h3>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <p className="text-xs font-semibold uppercase tracking-wide text-system-gray flex items-center gap-1">
                      <CreditCard size={13} /> Tipo de suscripción
                    </p>
                    <select
                      value={planDraft}
                      onChange={(event) => setPlanDraft(event.target.value)}
                      disabled={!canManageSubscription}
                      className="w-full h-11 rounded-xl border border-gray-200 px-3 text-sm font-semibold text-gray-900 focus:outline-none focus:ring-2 focus:ring-gray-400/30 disabled:bg-gray-100 disabled:text-gray-500"
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
                      className="inline-flex items-center gap-2 rounded-xl bg-gray-900 px-3 py-2 text-xs font-bold text-white hover:bg-gray-700 disabled:opacity-60"
                    >
                      {savingPlan ? <RefreshCw size={14} className="animate-spin" /> : <Save size={14} />}
                      Guardar suscripción
                    </button>
                    {planMessage && (
                      <p className={`text-xs font-semibold ${planMessage.includes('actualizado') ? 'text-green-600' : 'text-red-600'}`}>
                        {planMessage}
                      </p>
                    )}
                  </div>

                  <div className="space-y-2">
                    <p className="text-xs font-semibold uppercase tracking-wide text-system-gray flex items-center gap-1">
                      <Coins size={13} /> Moneda principal de operación
                    </p>
                    <select
                      value={currencyDraft}
                      onChange={(event) => setCurrencyDraft(event.target.value)}
                      disabled={!canManageCurrency}
                      className="w-full h-11 rounded-xl border border-gray-200 px-3 text-sm font-semibold text-gray-900 focus:outline-none focus:ring-2 focus:ring-gray-400/30 disabled:bg-gray-100 disabled:text-gray-500"
                    >
                      {availableCurrencies.map((currencyCode) => (
                        <option key={currencyCode} value={currencyCode}>
                          {currencyCode}
                        </option>
                      ))}
                    </select>
                    <button
                      type="button"
                      onClick={handleSaveCurrency}
                      disabled={savingCurrency || !canManageCurrency}
                      className="inline-flex items-center gap-2 rounded-xl bg-gray-900 px-3 py-2 text-xs font-bold text-white hover:bg-gray-700 disabled:opacity-60"
                    >
                      {savingCurrency ? <RefreshCw size={14} className="animate-spin" /> : <Save size={14} />}
                      Guardar moneda
                    </button>
                    {currencyMessage && (
                      <p className={`text-xs font-semibold ${currencyMessage.includes('correctamente') ? 'text-green-600' : 'text-red-600'}`}>
                        {currencyMessage}
                      </p>
                    )}
                  </div>
                </div>
              </div>

              <div className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm space-y-3">
                <h3 className="text-sm font-bold uppercase tracking-wide text-system-gray">Referencia</h3>
                <div>
                  <p className="text-xs text-gray-500">Slug</p>
                  <p className="text-lg font-bold text-gray-900 break-all">{organization.slug}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">Usuarios activos</p>
                  <p className="text-lg font-bold text-gray-900">{organization.user_count ?? 0}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">Estado de suscripción</p>
                  <p className="text-sm font-semibold text-gray-800">{organization.subscription_status || 'active'}</p>
                </div>
              </div>
            </section>
          </>
        )}
      </div>
    </AdminLayout>
  );
}
