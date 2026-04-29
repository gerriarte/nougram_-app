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

function categoryPercent(value: number, total: number): string {
  if (!Number.isFinite(total) || total <= 0) return '0%';
  return `${Math.max(0, Math.min(100, (value / total) * 100))}%`;
}

function KpiCard({
  label,
  value,
  hint,
  icon,
  tint,
  accent,
}: {
  label: string;
  value: string;
  hint: string;
  icon: React.ReactNode;
  tint: string;
  accent: string;
}) {
  return (
    <div className="rounded-2xl border border-gray-200 bg-white p-4 shadow-sm">
      <div className="mb-3 flex items-start justify-between gap-3">
        <div>
          <p className="text-[10px] font-black uppercase tracking-[0.18em] text-gray-400">{label}</p>
          <p className="mt-1 text-[11.5px] text-gray-400">{hint}</p>
        </div>
        <div className={`flex h-9 w-9 items-center justify-center rounded-xl ${tint}`}>
          {icon}
        </div>
      </div>
      <p className={`text-2xl font-black tracking-tight ${accent}`}>{value}</p>
    </div>
  );
}

function CostBar({
  label,
  value,
  total,
  color,
  currency,
}: {
  label: string;
  value: number;
  total: number;
  color: string;
  currency: string;
}) {
  return (
    <div>
      <div className="mb-1.5 flex items-center justify-between gap-3 text-xs">
        <span className="font-bold text-gray-700">{label}</span>
        <span className="font-semibold tabular-nums text-gray-500">{formatCurrency(value, currency)}</span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-gray-100">
        <div className={`h-full rounded-full ${color}`} style={{ width: categoryPercent(value, total) }} />
      </div>
    </div>
  );
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
    const timer = window.setTimeout(() => {
      void load();
    }, 0);
    return () => window.clearTimeout(timer);
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
      <div className="space-y-8 pb-20">
        <div className="grid grid-cols-1 gap-5 xl:grid-cols-[1fr_380px]">
          <div>
            <p className="text-[10px] font-black uppercase tracking-[0.2em] text-primary">Finanzas operativas</p>
            <h1 className="mt-1 text-[28px] font-black tracking-tight text-gray-950">
              Costo de operación
            </h1>
            <p className="mt-1 max-w-2xl text-[14px] font-medium leading-6 text-gray-500">
              Reporte mensual de costos reales para <span className="font-bold text-gray-800">{companyName}</span>. Fuente única: backend financiero.
            </p>
            {meta && (
              <div className="mt-4 flex flex-wrap items-center gap-2">
                <span className="rounded-full border border-gray-200 bg-white px-3 py-1.5 text-[12px] font-semibold text-gray-500">
                  {meta.period_start} → {meta.period_end}
                </span>
                <span className="rounded-full border border-gray-200 bg-white px-3 py-1.5 text-[12px] font-semibold text-gray-500">
                  Moneda {meta.currency}
                </span>
                {meta.calculation_id && (
                  <span className="rounded-full border border-gray-200 bg-white px-3 py-1.5 font-mono text-[11px] font-semibold text-gray-400">
                    ID {meta.calculation_id.slice(0, 8)}
                  </span>
                )}
              </div>
            )}
          </div>

          <div className="overflow-hidden rounded-2xl border border-slate-800 bg-slate-900 p-5 text-white shadow-sm">
            <div className="mb-5 flex items-center justify-between gap-3">
              <div>
                <p className="text-[10px] font-black uppercase tracking-[0.18em] text-slate-400">Mes en curso</p>
                <p className="mt-1 text-sm text-slate-300">Costo operacional total</p>
              </div>
              <button
                type="button"
                onClick={() => void load()}
                disabled={loading}
                className="flex h-10 w-10 items-center justify-center rounded-xl border border-white/10 bg-white/10 text-white disabled:opacity-50"
                aria-label="Actualizar costo operacional"
              >
                <RefreshCw className={loading ? 'animate-spin' : ''} size={18} />
              </button>
            </div>
            <p className="text-4xl font-black tracking-tight">{formatCurrency(total, currency)}</p>
            <p className="mt-2 text-xs text-slate-400">
              Recursos, gastos fijos, amortización e impuestos operativos.
            </p>
            <div className="mt-5 h-2 overflow-hidden rounded-full bg-white/10">
              <div className="h-full rounded-full bg-primary" style={{ width: '100%' }} />
            </div>
          </div>
        </div>

        {/* Desglose por categoría */}
        <section className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <KpiCard
            label="Recursos"
            value={formatCurrency(resourceCosts, currency)}
            hint="Nómina + cargas"
            icon={<Wallet className="h-5 w-5 text-primary" />}
            tint="bg-primary-soft"
            accent="text-primary"
          />
          <KpiCard
            label="Gastos fijos"
            value={formatCurrency(fixedCosts, currency)}
            hint="Overhead mensual"
            icon={<Building2 className="h-5 w-5 text-emerald-600" />}
            tint="bg-emerald-50"
            accent="text-emerald-700"
          />
          <KpiCard
            label="Amortización"
            value={formatCurrency(amortization, currency)}
            hint="Activos mensualizados"
            icon={<PieChart className="h-5 w-5 text-amber-600" />}
            tint="bg-amber-50"
            accent="text-amber-700"
          />
          <KpiCard
            label="Impuestos"
            value={formatCurrency(taxCosts, currency)}
            hint="Operativos"
            icon={<Percent className="h-5 w-5 text-slate-600" />}
            tint="bg-slate-100"
            accent="text-slate-700"
          />
        </section>

        <section className="grid grid-cols-1 gap-5 lg:grid-cols-[1.1fr_0.9fr]">
          <div className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm">
            <div className="mb-5 flex items-center justify-between">
              <div>
                <p className="text-sm font-black text-gray-900">Composición del costo</p>
                <p className="mt-1 text-xs text-gray-400">Participación por categoría sobre el total mensual.</p>
              </div>
              <span className="rounded-full bg-surface-2 px-3 py-1 text-[11px] font-bold text-gray-500">
                Total {formatCurrency(total, currency)}
              </span>
            </div>
            <div className="space-y-4">
              <CostBar label="Recursos (nómina + cargas)" value={resourceCosts} total={total} color="bg-primary" currency={currency} />
              <CostBar label="Gastos fijos" value={fixedCosts} total={total} color="bg-emerald-500" currency={currency} />
              <CostBar label="Amortización" value={amortization} total={total} color="bg-amber-500" currency={currency} />
              <CostBar label="Impuestos operativos" value={taxCosts} total={total} color="bg-slate-500" currency={currency} />
            </div>
          </div>

          <div className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm">
            <h2 className="mb-5 flex items-center gap-2 text-sm font-black uppercase tracking-widest text-gray-400">
              <TrendingUp className="h-4 w-4 text-gray-500" />
              Margen objetivo vs efectivo
            </h2>
            <div className="grid grid-cols-1 gap-4">
              <div className="rounded-xl border border-primary/10 bg-primary-soft p-4">
                <p className="text-xs font-bold text-primary">Margen objetivo</p>
                <p className="mt-1 text-3xl font-black text-gray-900">
                  {data?.target_margin_configured != null ? formatPercent(data.target_margin_configured) : '—'}
                </p>
                <p className="mt-1 text-[11.5px] text-gray-500">Configurado en organización o promedio de servicios.</p>
              </div>
              <div className="rounded-xl border border-gray-200 bg-surface-2 p-4">
                <p className="text-xs font-bold text-gray-500">Margen efectivo observado</p>
                <p className="mt-1 text-3xl font-black text-gray-900">
                  {data?.effective_margin_observed != null ? formatPercent(data.effective_margin_observed) : '—'}
                </p>
                <p className="mt-1 text-[11.5px] text-gray-500">Proyectos Won del período.</p>
              </div>
            </div>
          </div>
        </section>

        {/* Integridad y metodología */}
        <section className="rounded-2xl border border-gray-200 bg-gray-50/80 p-6">
          <h2 className="mb-3 flex items-center gap-2 text-base font-black text-gray-800">
            <Info className="h-4 w-4" />
            Estado y metodología
          </h2>
          <div className="mb-4 flex flex-wrap items-center gap-3">
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
