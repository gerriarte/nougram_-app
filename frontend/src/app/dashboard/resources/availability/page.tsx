
'use client';

import React from 'react';
import { AdminLayout } from '@/components/admin/layout/AdminLayout';
import { Activity, AlertCircle, BarChart3, Calendar, CheckCircle2, Filter, RefreshCw, TrendingUp, Users } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { capacityService, type CapacityState } from '@/services/capacityService';
import { formatDisplayNumber } from '@/lib/utils';

const ALL_STATES: CapacityState[] = ['tentative', 'committed', 'actual'];

function currentMonthRange(): { start: string; end: string } {
    const now = new Date();
    const year = now.getUTCFullYear();
    const month = now.getUTCMonth();
    const start = new Date(Date.UTC(year, month, 1));
    const end = new Date(Date.UTC(year, month + 1, 0));
    const toISODate = (d: Date) => d.toISOString().split('T')[0];
    return { start: toISODate(start), end: toISODate(end) };
}

function formatHours(value: number): string {
    return `${formatDisplayNumber(value, { minimumFractionDigits: 1, maximumFractionDigits: 1 })}h`;
}

function formatPercent(value: number): string {
    return `${formatDisplayNumber(value, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}%`;
}

const STATE_META: Record<CapacityState, { label: string; color: string; bg: string }> = {
    tentative: { label: 'Tentativo', color: 'bg-blue-400', bg: 'bg-blue-50 text-blue-700 border-blue-100' },
    committed: { label: 'Comprometido', color: 'bg-emerald-500', bg: 'bg-emerald-50 text-emerald-700 border-emerald-100' },
    actual: { label: 'Ejecutado', color: 'bg-violet-500', bg: 'bg-violet-50 text-violet-700 border-violet-100' },
};

function utilizationTone(ratio: number) {
    if (ratio > 1) {
        return {
            label: 'Crítica',
            text: 'text-red-600',
            bg: 'bg-red-50',
            border: 'border-red-100',
            bar: 'bg-red-500',
            Icon: AlertCircle,
        };
    }
    if (ratio >= 0.9) {
        return {
            label: 'Alta',
            text: 'text-amber-600',
            bg: 'bg-amber-50',
            border: 'border-amber-100',
            bar: 'bg-amber-500',
            Icon: TrendingUp,
        };
    }
    return {
        label: 'Normal',
        text: 'text-emerald-600',
        bg: 'bg-emerald-50',
        border: 'border-emerald-100',
        bar: 'bg-emerald-500',
        Icon: CheckCircle2,
    };
}

function KpiCard({
    label,
    value,
    hint,
    accent = 'text-gray-900',
    icon,
}: {
    label: string;
    value: string;
    hint: string;
    accent?: string;
    icon: React.ReactNode;
}) {
    return (
        <div className="rounded-2xl border border-gray-200 bg-white p-4 shadow-sm">
            <div className="mb-3 flex items-center justify-between gap-3">
                <p className="text-[10px] font-black uppercase tracking-[0.18em] text-gray-400">{label}</p>
                <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-surface-2 text-gray-500">{icon}</div>
            </div>
            <p className={`text-2xl font-black tracking-tight ${accent}`}>{value}</p>
            <p className="mt-1 text-[11.5px] text-gray-400">{hint}</p>
        </div>
    );
}

function toISODate(d: Date): string {
    return d.toISOString().split('T')[0];
}

function monthBucketsBetween(startDate: string, endDate: string): Array<{ label: string; start: string; end: string }> {
    const start = new Date(`${startDate}T00:00:00Z`);
    const end = new Date(`${endDate}T00:00:00Z`);
    if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime()) || start > end) {
        return [];
    }

    const buckets: Array<{ label: string; start: string; end: string }> = [];
    const cursor = new Date(Date.UTC(start.getUTCFullYear(), start.getUTCMonth(), 1));
    const endCursor = new Date(Date.UTC(end.getUTCFullYear(), end.getUTCMonth(), 1));
    while (cursor <= endCursor) {
        const year = cursor.getUTCFullYear();
        const month = cursor.getUTCMonth();
        const monthStart = new Date(Date.UTC(year, month, 1));
        const monthEnd = new Date(Date.UTC(year, month + 1, 0));
        const rangeStart = monthStart < start ? start : monthStart;
        const rangeEnd = monthEnd > end ? end : monthEnd;
        buckets.push({
            label: cursor.toLocaleDateString('es-CO', { month: 'short', year: '2-digit', timeZone: 'UTC' }),
            start: toISODate(rangeStart),
            end: toISODate(rangeEnd),
        });
        cursor.setUTCMonth(cursor.getUTCMonth() + 1);
    }
    return buckets.slice(0, 12);
}

export default function AvailabilityPage() {
    const defaultRange = React.useMemo(() => currentMonthRange(), []);
    const [periodStart, setPeriodStart] = React.useState(defaultRange.start);
    const [periodEnd, setPeriodEnd] = React.useState(defaultRange.end);
    const [selectedStates, setSelectedStates] = React.useState<CapacityState[]>(ALL_STATES);
    const [loading, setLoading] = React.useState(true);
    const [trendLoading, setTrendLoading] = React.useState(true);
    const [error, setError] = React.useState<string | null>(null);
    const [overview, setOverview] = React.useState<Awaited<ReturnType<typeof capacityService.getOverview>> | null>(null);
    const [monthlyTrend, setMonthlyTrend] = React.useState<
        Array<{ label: string; tentative: number; committed: number; actual: number; total: number }>
    >([]);
    const [hoveredMonth, setHoveredMonth] = React.useState<{
        label: string;
        tentative: number;
        committed: number;
        actual: number;
        total: number;
    } | null>(null);

    const loadOverview = React.useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const [data, trend] = await Promise.all([
                capacityService.getOverview(periodStart, periodEnd, selectedStates),
                (async () => {
                    setTrendLoading(true);
                    const buckets = monthBucketsBetween(periodStart, periodEnd);
                    const monthly = await Promise.all(
                        buckets.map(async (bucket) => {
                            const bucketOverview = await capacityService.getOverview(bucket.start, bucket.end, selectedStates);
                            return {
                                label: bucket.label,
                                tentative: bucketOverview.totals.tentativeHours,
                                committed: bucketOverview.totals.committedHours,
                                actual: bucketOverview.totals.actualHours,
                                total: bucketOverview.totals.totalHours,
                            };
                        })
                    );
                    return monthly;
                })(),
            ]);
            setOverview(data);
            setMonthlyTrend(trend);
        } catch (err) {
            const message = err instanceof Error ? err.message : 'Error cargando capacidad.';
            setError(message);
        } finally {
            setLoading(false);
            setTrendLoading(false);
        }
    }, [periodStart, periodEnd, selectedStates]);

    React.useEffect(() => {
        void loadOverview();
    }, [loadOverview]);

    const toggleState = (state: CapacityState) => {
        setSelectedStates((prev) => {
            if (prev.includes(state)) {
                const next = prev.filter((s) => s !== state);
                return next.length > 0 ? next : prev;
            }
            return [...prev, state];
        });
    };

    const applyQuickRange = (monthsBack: number) => {
        const now = new Date();
        const currentMonthStart = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), 1));
        const rangeStart = new Date(Date.UTC(currentMonthStart.getUTCFullYear(), currentMonthStart.getUTCMonth() - (monthsBack - 1), 1));
        const rangeEnd = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth() + 1, 0));
        setPeriodStart(toISODate(rangeStart));
        setPeriodEnd(toISODate(rangeEnd));
    };

    const members = overview?.members || [];
    const totalCapacity = members.reduce((sum, member) => sum + member.capacityHours, 0);
    const utilizationRatio = totalCapacity > 0 ? (overview?.totals.totalHours || 0) / totalCapacity : 0;
    const utilization = utilizationTone(utilizationRatio);
    const UtilizationIcon = utilization.Icon;
    const overloadedCount = members.filter((member) => member.utilizationRatio > 1).length;
    const highLoadCount = members.filter((member) => member.utilizationRatio >= 0.9 && member.utilizationRatio <= 1).length;

    if (loading) {
        return (
            <AdminLayout>
                <div className="flex h-screen items-center justify-center">
                    Cargando disponibilidad del equipo...
                </div>
            </AdminLayout>
        );
    }

    return (
        <AdminLayout>
            <div className="space-y-8 pb-20">
                <div className="grid grid-cols-1 gap-5 xl:grid-cols-[1fr_340px]">
                    <div>
                        <p className="text-[10px] font-black uppercase tracking-[0.2em] text-primary">Operación</p>
                        <h1 className="mt-1 text-[28px] font-black tracking-tight text-gray-950">Capacidad del Equipo</h1>
                        <p className="mt-1 max-w-2xl text-[14px] font-medium leading-6 text-gray-500">
                            Seguimiento de ocupación, compromisos y capacidad disponible por periodo, miembro y equipo.
                        </p>
                        <div className="mt-4 flex flex-wrap items-center gap-2">
                            {[3, 6, 12].map((months) => (
                                <button
                                    key={months}
                                    type="button"
                                    onClick={() => applyQuickRange(months)}
                                    className="rounded-full border border-gray-200 bg-white px-3 py-1.5 text-[12px] font-bold text-gray-600 hover:border-gray-900 hover:text-gray-900"
                                >
                                    Últimos {months} meses
                                </button>
                            ))}
                            <span className="rounded-full border border-gray-200 bg-white px-3 py-1.5 text-[12px] font-semibold text-gray-400">
                                {periodStart} → {periodEnd}
                            </span>
                        </div>
                    </div>

                    <div className="overflow-hidden rounded-2xl border border-slate-800 bg-slate-900 p-5 text-white shadow-sm">
                        <div className="mb-4 flex items-center justify-between gap-3">
                            <div>
                                <p className="text-[10px] font-black uppercase tracking-[0.18em] text-slate-400">Utilización global</p>
                                <p className="mt-1 text-sm text-slate-300">Total asignado vs capacidad disponible</p>
                            </div>
                            <div className={`flex h-10 w-10 items-center justify-center rounded-xl ${utilization.bg} ${utilization.text}`}>
                                <UtilizationIcon size={18} />
                            </div>
                        </div>
                        <div className="flex items-end justify-between gap-4">
                            <div>
                                <p className="text-4xl font-black tracking-tight">{formatPercent(utilizationRatio * 100)}</p>
                                <p className={`mt-1 text-xs font-bold uppercase tracking-wide ${utilization.text}`}>{utilization.label}</p>
                            </div>
                            <div className="text-right text-xs text-slate-400">
                                <p>{formatHours(overview?.totals.totalHours || 0)} asignadas</p>
                                <p>{formatHours(totalCapacity)} capacidad</p>
                            </div>
                        </div>
                        <div className="mt-4 h-2 overflow-hidden rounded-full bg-white/10">
                            <div className={`h-full rounded-full ${utilization.bar}`} style={{ width: `${Math.min(utilizationRatio * 100, 100)}%` }} />
                        </div>
                    </div>
                </div>

                <div className="rounded-2xl border border-gray-200 bg-white p-4 md:p-5 shadow-sm">
                    <div className="mb-4 flex items-center justify-between gap-3">
                        <div className="flex items-center gap-2">
                            <Filter size={16} className="text-gray-500" />
                            <h2 className="text-sm font-bold uppercase tracking-wider text-gray-700">Filtros</h2>
                        </div>
                        <Button variant="secondary" className="flex items-center gap-2" onClick={() => void loadOverview()}>
                            <RefreshCw size={16} />
                            Actualizar
                        </Button>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                        <div className="space-y-1">
                            <label className="text-xs font-semibold text-gray-500">Desde</label>
                            <input
                                type="date"
                                value={periodStart}
                                onChange={(e) => setPeriodStart(e.target.value)}
                                className="w-full h-9 rounded-lg border border-gray-200 px-3 text-sm"
                            />
                        </div>
                        <div className="space-y-1">
                            <label className="text-xs font-semibold text-gray-500">Hasta</label>
                            <input
                                type="date"
                                value={periodEnd}
                                onChange={(e) => setPeriodEnd(e.target.value)}
                                className="w-full h-9 rounded-lg border border-gray-200 px-3 text-sm"
                            />
                        </div>
                        <div className="space-y-1">
                            <label className="text-xs font-semibold text-gray-500">Estados</label>
                            <div className="flex min-h-9 flex-wrap items-center gap-2 rounded-md border border-gray-200 px-3 py-1">
                                {ALL_STATES.map((state) => (
                                    <label key={state} className={`flex items-center gap-1.5 rounded-full border px-2 py-1 text-xs font-semibold ${STATE_META[state].bg}`}>
                                        <input
                                            type="checkbox"
                                            checked={selectedStates.includes(state)}
                                            onChange={() => toggleState(state)}
                                        />
                                        {STATE_META[state].label}
                                    </label>
                                ))}
                            </div>
                        </div>
                    </div>
                    <div className="mt-3">
                        <div className="flex flex-wrap items-center gap-2">
                            <Button className="bg-gray-900 hover:bg-gray-700 text-white flex items-center gap-2 rounded-lg" onClick={() => void loadOverview()}>
                                <Calendar size={14} />
                                Aplicar filtros
                            </Button>
                        </div>
                    </div>
                </div>

                {error && (
                    <div className="rounded-xl border border-red-200 bg-red-50 text-red-700 px-4 py-3 text-sm">
                        {error}
                    </div>
                )}

                <div className="grid grid-cols-1 gap-3 md:grid-cols-4">
                    <KpiCard label="Tentativo" value={formatHours(overview?.totals.tentativeHours || 0)} hint="Reservas estimadas" accent="text-blue-600" icon={<Calendar size={15} />} />
                    <KpiCard label="Comprometido" value={formatHours(overview?.totals.committedHours || 0)} hint="Trabajo confirmado" accent="text-emerald-600" icon={<CheckCircle2 size={15} />} />
                    <KpiCard label="Ejecutado" value={formatHours(overview?.totals.actualHours || 0)} hint="Horas reales" accent="text-violet-600" icon={<Activity size={15} />} />
                    <KpiCard label="Alertas" value={`${overloadedCount + highLoadCount}`} hint={`${overloadedCount} críticas · ${highLoadCount} altas`} accent={overloadedCount > 0 ? 'text-red-600' : 'text-gray-900'} icon={<AlertCircle size={15} />} />
                </div>

                <div className="grid grid-cols-1 gap-8">
                    <div className="rounded-2xl border border-gray-200 bg-white p-4 md:p-5 shadow-sm">
                        <div className="flex items-center gap-2 px-1 mb-4">
                            <BarChart3 size={18} className="text-gray-400" />
                            <h2 className="text-sm font-black text-gray-400 uppercase tracking-widest">Tendencia Mensual (Stacked)</h2>
                        </div>
                        {trendLoading ? (
                            <div className="h-44 flex items-center justify-center text-sm text-gray-400">Cargando tendencia mensual...</div>
                        ) : monthlyTrend.length === 0 ? (
                            <div className="h-44 flex items-center justify-center text-sm text-gray-400">Sin datos para la tendencia mensual.</div>
                        ) : (
                            <div>
                                <div className="flex items-center gap-4 text-xs mb-3">
                                    <span className="inline-flex items-center gap-1.5"><span className="w-3 h-3 rounded bg-blue-400" />Tentative</span>
                                    <span className="inline-flex items-center gap-1.5"><span className="w-3 h-3 rounded bg-emerald-500" />Committed</span>
                                    <span className="inline-flex items-center gap-1.5"><span className="w-3 h-3 rounded bg-violet-500" />Actual</span>
                                </div>
                                <div className="grid grid-cols-2 md:grid-cols-6 gap-3">
                                    {monthlyTrend.map((month) => {
                                        const maxTotal = Math.max(...monthlyTrend.map((m) => m.total), 1);
                                        const barHeight = 120;
                                        const monthHeight = (month.total / maxTotal) * barHeight;
                                        const tentativeH = month.total > 0 ? (month.tentative / month.total) * monthHeight : 0;
                                        const committedH = month.total > 0 ? (month.committed / month.total) * monthHeight : 0;
                                        const actualH = month.total > 0 ? (month.actual / month.total) * monthHeight : 0;
                                        return (
                                            <div
                                                key={month.label}
                                                className="flex flex-col items-center"
                                                onMouseEnter={() => setHoveredMonth(month)}
                                                onMouseLeave={() => setHoveredMonth((prev) => (prev?.label === month.label ? null : prev))}
                                            >
                                                <div className="text-[10px] text-gray-500 mb-1">{formatHours(month.total)}</div>
                                                <div className="w-10 h-[120px] rounded-md bg-gray-100 border border-gray-200 flex flex-col-reverse overflow-hidden">
                                                    <div style={{ height: `${actualH}px` }} className="bg-violet-500" />
                                                    <div style={{ height: `${committedH}px` }} className="bg-emerald-500" />
                                                    <div style={{ height: `${tentativeH}px` }} className="bg-blue-400" />
                                                </div>
                                                <div className="mt-2 text-[11px] font-semibold text-gray-600">{month.label}</div>
                                            </div>
                                        );
                                    })}
                                </div>
                                {hoveredMonth && (
                                    <div className="mt-4 rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-xs text-gray-700">
                                        <div className="font-bold text-gray-900 mb-1">{hoveredMonth.label}</div>
                                        <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                                            <span>Tentative: {formatHours(hoveredMonth.tentative)}</span>
                                            <span>Committed: {formatHours(hoveredMonth.committed)}</span>
                                            <span>Actual: {formatHours(hoveredMonth.actual)}</span>
                                            <span className="font-semibold">Total: {formatHours(hoveredMonth.total)}</span>
                                        </div>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>

                    <div className="rounded-2xl border border-gray-200 bg-white p-4 md:p-5 shadow-sm">
                        <div className="mb-5 flex flex-col gap-3 px-1 sm:flex-row sm:items-center sm:justify-between">
                            <div className="flex items-center gap-2">
                                <Users size={18} className="text-gray-400" />
                                <div>
                                    <h2 className="text-sm font-black uppercase tracking-widest text-gray-400">Resumen por Miembro</h2>
                                    <p className="mt-0.5 text-xs text-gray-400">Semáforo de ocupación individual</p>
                                </div>
                            </div>
                            <div className="flex items-center gap-3 text-[10px] font-bold uppercase tracking-wider text-gray-500">
                                <span className="inline-flex items-center gap-1.5"><span className="h-2 w-2 rounded-full bg-emerald-500" />Normal</span>
                                <span className="inline-flex items-center gap-1.5"><span className="h-2 w-2 rounded-full bg-amber-500" />Alta</span>
                                <span className="inline-flex items-center gap-1.5"><span className="h-2 w-2 rounded-full bg-red-500" />Crítica</span>
                            </div>
                        </div>
                        {(overview?.members || []).length === 0 ? (
                            <div className="rounded-xl border border-dashed border-gray-200 bg-surface-2 px-4 py-8 text-center text-sm text-gray-400">
                                No hay ocupación por miembro en el periodo seleccionado.
                            </div>
                        ) : (
                            <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
                                {(overview?.members || []).map((member) => {
                                    const tone = utilizationTone(member.utilizationRatio);
                                    const Icon = tone.Icon;
                                    const initials = member.name.split(' ').map((part) => part[0]).slice(0, 2).join('').toUpperCase();
                                    const overHours = Math.max(member.totalHours - member.capacityHours, 0);
                                    return (
                                        <div key={member.teamMemberId} className="rounded-2xl border border-gray-100 bg-white p-4 shadow-sm transition-all hover:border-primary/20 hover:shadow-md">
                                            <div className="mb-4 flex items-start justify-between gap-3">
                                                <div className="flex min-w-0 items-center gap-3">
                                                    <div className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-full border-2 border-white text-xs font-black shadow-sm ring-1 ring-gray-100 ${tone.bg} ${tone.text}`}>
                                                        {initials || 'U'}
                                                    </div>
                                                    <div className="min-w-0">
                                                        <p className="truncate text-sm font-black text-gray-900">{member.name}</p>
                                                        <p className="mt-1 truncate text-[10.5px] font-bold uppercase tracking-tight text-gray-400">{member.role}</p>
                                                    </div>
                                                </div>
                                                <Icon size={17} className={tone.text} />
                                            </div>

                                            <div className="space-y-3">
                                                <div className="flex items-end justify-between">
                                                    <div>
                                                        <span className="text-[9px] font-black uppercase tracking-wide text-gray-400">Uso de capacidad</span>
                                                        <p className={`text-2xl font-black leading-none ${tone.text}`}>
                                                            {formatPercent(member.utilizationRatio * 100)}
                                                        </p>
                                                    </div>
                                                    <div className="text-right">
                                                        <span className="text-[11px] font-bold text-gray-600">{formatHours(member.totalHours)}</span>
                                                        <span className="mx-1 text-[11px] text-gray-300">/</span>
                                                        <span className="text-[11px] font-medium text-gray-400">{formatHours(member.capacityHours)}</span>
                                                    </div>
                                                </div>
                                                <div className="relative h-2 w-full overflow-hidden rounded-full bg-gray-100">
                                                    <div className={`h-full rounded-full transition-all ${tone.bar}`} style={{ width: `${Math.min(member.utilizationRatio * 100, 100)}%` }} />
                                                    {member.utilizationRatio > 1 && <div className="absolute inset-0 animate-pulse bg-red-500/20" />}
                                                </div>
                                                <div className="grid grid-cols-3 gap-2 text-[10.5px]">
                                                    <div className="rounded-lg bg-blue-50 px-2 py-1.5 text-blue-700">
                                                        <p className="font-bold">Tent.</p>
                                                        <p>{formatHours(member.tentativeHours)}</p>
                                                    </div>
                                                    <div className="rounded-lg bg-emerald-50 px-2 py-1.5 text-emerald-700">
                                                        <p className="font-bold">Comm.</p>
                                                        <p>{formatHours(member.committedHours)}</p>
                                                    </div>
                                                    <div className="rounded-lg bg-violet-50 px-2 py-1.5 text-violet-700">
                                                        <p className="font-bold">Actual</p>
                                                        <p>{formatHours(member.actualHours)}</p>
                                                    </div>
                                                </div>
                                            </div>

                                            {overHours > 0 && (
                                                <div className="mt-3 rounded-lg border border-red-100 bg-red-50 px-3 py-2 text-[10px] font-black uppercase tracking-wide text-red-600">
                                                    Requerido: {formatHours(overHours)} excedidas
                                                </div>
                                            )}
                                        </div>
                                    );
                                })}
                            </div>
                        )}
                    </div>

                    <div className="space-y-4">
                        <div className="flex items-center gap-2 px-1">
                            <BarChart3 size={18} className="text-gray-400" />
                            <h2 className="text-sm font-black text-gray-400 uppercase tracking-widest">Resumen por Equipo</h2>
                        </div>
                        <div className="overflow-x-auto rounded-xl border border-gray-200 bg-white">
                            <table className="w-full text-sm">
                                <thead className="bg-gray-50 text-gray-600">
                                    <tr>
                                        <th className="px-4 py-3 text-left font-semibold">Equipo</th>
                                        <th className="px-4 py-3 text-right font-semibold">Tentative</th>
                                        <th className="px-4 py-3 text-right font-semibold">Committed</th>
                                        <th className="px-4 py-3 text-right font-semibold">Actual</th>
                                        <th className="px-4 py-3 text-right font-semibold">Total</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {(overview?.cells || []).length === 0 ? (
                                        <tr>
                                            <td colSpan={5} className="px-4 py-6 text-center text-gray-400">
                                                No hay ocupación por equipo en el periodo seleccionado.
                                            </td>
                                        </tr>
                                    ) : (
                                        (overview?.cells || []).map((cell) => (
                                            <tr key={cell.cellId} className="border-t border-gray-100">
                                                <td className="px-4 py-3 font-medium text-gray-900">{cell.cellName}</td>
                                                <td className="px-4 py-3 text-right text-gray-600">{formatHours(cell.tentativeHours)}</td>
                                                <td className="px-4 py-3 text-right text-gray-600">{formatHours(cell.committedHours)}</td>
                                                <td className="px-4 py-3 text-right text-gray-600">{formatHours(cell.actualHours)}</td>
                                                <td className="px-4 py-3 text-right font-semibold text-gray-900">{formatHours(cell.totalHours)}</td>
                                            </tr>
                                        ))
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </AdminLayout>
    );
}
