'use client';

import React, { useEffect, useState } from 'react';
import { AdminLayout } from '@/components/admin/layout/AdminLayout';
import { fetchOperationalCosts, type OperationalCostPayload } from '@/lib/operational-costs-api';
import { formatCurrency, formatDisplayNumber } from '@/lib/utils';
import { useNougram } from '@/context/NougramCoreContext';
import { apiRequest } from '@/lib/api-client';
import {
  TrendingUp,
  Wallet,
  Building2,
  PieChart,
  Percent,
  AlertCircle,
  Info,
  RefreshCw,
} from 'lucide-react';

function parseDecimal(s: string | null | undefined): number {
  if (s == null || s === '') return 0;
  const n = parseFloat(s);
  return Number.isFinite(n) ? n : 0;
}

function formatPercent(value: string | null | undefined): string {
  const n = parseDecimal(value);
  return `${formatDisplayNumber(n * 100, { minimumFractionDigits: 1, maximumFractionDigits: 1 })}%`;
}

export default function OperationalCostsPage() {
  const { state } = useNougram();
  const [data, setData] = useState<OperationalCostPayload | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [legalName, setLegalName] = useState<string>('');

  const load = async () => {
    setLoading(true);
    setError(null);
    const res = await fetchOperationalCosts('current_month');
    if (res.error || !res.data) {
      setError(res.error ?? 'No se pudo cargar el costo operacional.');
      setData(null);
    } else {
      setData(res.data);
    }
    setLoading(false);
  };

  useEffect(() => {
    void load();
  }, []);

  useEffect(() => {
    const loadOrganizationName = async () => {
      const response = await apiRequest<{ name?: string }>('/organizations/me');
      const backendName = (response.data?.name || '').trim();
      if (backendName) {
        setLegalName(backendName);
      }
    };
    void loadOrganizationName();
  }, []);

  const currency = data?.calculation_metadata?.currency ?? 'USD';
  const meta = data?.calculation_metadata;
  const stateName = (state.identity.name || '').trim();
  const companyName =
    legalName ||
    (stateName && stateName !== 'Mi Agencia' ? stateName : '') ||
    'Razón Social registrada';

  if (loading && !data) {
    return (
      <AdminLayout>
        <div className="flex flex-col items-center justify-center min-h-[320px] gap-4">
          <RefreshCw className="w-10 h-10 text-gray-400 animate-spin" />
          <p className="text-gray-500 font-medium">Cargando costo operacional…</p>
        </div>
      </AdminLayout>
    );
  }

  if (error && !data) {
    return (
      <AdminLayout>
        <div className="rounded-2xl border border-red-200 bg-red-50/80 p-6 flex items-start gap-4">
          <AlertCircle className="w-6 h-6 text-red-600 shrink-0 mt-0.5" />
          <div>
            <h2 className="font-bold text-red-900">Error</h2>
            <p className="text-red-800 mt-1">{error}</p>
            <button
              type="button"
              onClick={() => void load()}
              className="mt-4 px-4 py-2 rounded-xl bg-red-100 text-red-800 font-medium hover:bg-red-200 transition-colors"
            >
              Reintentar
            </button>
          </div>
        </div>
      </AdminLayout>
    );
  }

  const total = parseDecimal(data?.total_operational_cost);
  const resourceCosts = parseDecimal(data?.resource_costs);
  const fixedCosts = parseDecimal(data?.fixed_costs);
  const amortization = parseDecimal(data?.amortization);
  const taxCosts = parseDecimal(data?.tax_costs);

  return (
    <AdminLayout>
      <div className="space-y-10">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <h1 className="text-[22px] font-bold text-gray-900 tracking-tight">
              Costo de operación ({companyName})
            </h1>
            <p className="text-gray-500 font-medium mt-1">
              Reporte general de costos operacionales.
            </p>
          </div>
          <button
            type="button"
            onClick={() => void load()}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 rounded-xl border border-gray-200 bg-white text-gray-700 font-medium hover:bg-gray-50 disabled:opacity-50 transition-colors"
          >
            <RefreshCw className={loading ? 'animate-spin' : ''} size={18} />
            Actualizar
          </button>
        </div>

        {/* KPI: Total mensual */}
        <section className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
          <p className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">
            Costo operacional total (mes en curso)
          </p>
          <p className="text-3xl font-bold text-gray-900">
            {formatCurrency(total, currency)}
          </p>
          {meta && (
            <p className="text-sm text-gray-500 mt-2">
              Período: {meta.period_start} → {meta.period_end} · Moneda: {meta.currency}
              {meta.calculation_id && (
                <span className="ml-2 text-gray-400">· ID: {meta.calculation_id.slice(0, 8)}</span>
              )}
            </p>
          )}
        </section>

        {/* Desglose por categoría */}
        <section>
          <h2 className="text-lg font-bold text-gray-900 mb-4">Desglose por categoría</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="rounded-xl border border-gray-200 bg-white p-5 flex items-start gap-4">
              <div className="rounded-lg bg-primary-soft p-3">
                <Wallet className="w-5 h-5 text-primary" />
              </div>
              <div>
                <p className="text-xs font-bold text-gray-400 uppercase">Recursos (nómina + cargas)</p>
                <p className="text-xl font-bold text-gray-900 mt-1">
                  {formatCurrency(resourceCosts, currency)}
                </p>
              </div>
            </div>
            <div className="rounded-xl border border-gray-200 bg-white p-5 flex items-start gap-4">
              <div className="rounded-lg bg-emerald-50 p-3">
                <Building2 className="w-5 h-5 text-emerald-600" />
              </div>
              <div>
                <p className="text-xs font-bold text-gray-400 uppercase">Gastos fijos</p>
                <p className="text-xl font-bold text-gray-900 mt-1">
                  {formatCurrency(fixedCosts, currency)}
                </p>
              </div>
            </div>
            <div className="rounded-xl border border-gray-200 bg-white p-5 flex items-start gap-4">
              <div className="rounded-lg bg-amber-50 p-3">
                <PieChart className="w-5 h-5 text-amber-600" />
              </div>
              <div>
                <p className="text-xs font-bold text-gray-400 uppercase">Amortización</p>
                <p className="text-xl font-bold text-gray-900 mt-1">
                  {formatCurrency(amortization, currency)}
                </p>
              </div>
            </div>
            <div className="rounded-xl border border-gray-200 bg-white p-5 flex items-start gap-4">
              <div className="rounded-lg bg-slate-100 p-3">
                <Percent className="w-5 h-5 text-slate-600" />
              </div>
              <div>
                <p className="text-xs font-bold text-gray-400 uppercase">Impuestos operativos</p>
                <p className="text-xl font-bold text-gray-900 mt-1">
                  {formatCurrency(taxCosts, currency)}
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Margen objetivo vs efectivo */}
        <section className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-gray-600" />
            Margen objetivo vs margen efectivo
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <p className="text-sm font-medium text-gray-500">Margen objetivo (cotización)</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">
                {data?.target_margin_configured != null
                  ? formatPercent(data.target_margin_configured)
                  : '—'}
              </p>
              <p className="text-xs text-gray-400 mt-1">
                Configurado en organización o promedio de servicios
              </p>
            </div>
            <div>
              <p className="text-sm font-medium text-gray-500">Margen efectivo observado</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">
                {data?.effective_margin_observed != null
                  ? formatPercent(data.effective_margin_observed)
                  : '—'}
              </p>
              <p className="text-xs text-gray-400 mt-1">
                Proyectos Won en el período (ingresos − costos) / ingresos
              </p>
            </div>
          </div>
        </section>

        {/* Integridad y metodología */}
        <section className="rounded-2xl border border-gray-200 bg-gray-50/80 p-6">
          <h2 className="text-base font-bold text-gray-800 mb-3 flex items-center gap-2">
            <Info className="w-4 h-4" />
            Estado y metodología
          </h2>
          <div className="flex flex-wrap items-center gap-3 mb-4">
            <span
              className={
                data?.data_integrity_ok
                  ? 'px-3 py-1 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800'
                  : 'px-3 py-1 rounded-full text-xs font-bold bg-amber-100 text-amber-800'
              }
            >
              {data?.data_integrity_ok ? 'Datos completos' : 'Revisar integridad de datos'}
            </span>
            {meta?.formula_version && (
              <span className="text-xs text-gray-500">Fórmula v{meta.formula_version}</span>
            )}
          </div>
          <p className="text-sm text-gray-600 max-w-2xl">
            Todas las cifras provienen del backend. Este panel no realiza cálculos financieros en el
            navegador. Incluye: costos de recursos (nómina + cargas sociales), gastos fijos,
            amortización mensual de activos, impuestos operativos y total. El margen efectivo se
            calcula a partir de cotizaciones ganadas en el período.
          </p>
        </section>
      </div>
    </AdminLayout>
  );
}
