
'use client';

import React from 'react';
import { AdminLayout } from '@/components/admin/layout/AdminLayout';
import { BarChart3, Calendar, Filter, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { capacityService, type CapacityState } from '@/services/capacityService';

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
    return `${value.toFixed(1)}h`;
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
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div>
                        <h1 className="text-2xl font-black text-gray-900 tracking-tight">Capacidad del Equipo</h1>
                        <p className="text-gray-500 font-medium">Seguimiento de ocupación por periodo y estado operativo.</p>
                    </div>
                    <div className="flex items-center gap-3">
                        <Button variant="secondary" className="flex items-center gap-2" onClick={() => void loadOverview()}>
                            <RefreshCw size={16} />
                            Actualizar
                        </Button>
                    </div>
                </div>

                <div className="rounded-2xl border border-gray-200 bg-white p-4 md:p-5 shadow-sm">
                    <div className="flex items-center gap-2 mb-4">
                        <Filter size={16} className="text-gray-500" />
                        <h2 className="text-sm font-bold text-gray-700 uppercase tracking-wider">Filtros</h2>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                        <div className="space-y-1">
                            <label className="text-xs font-semibold text-gray-500">Desde</label>
                            <input
                                type="date"
                                value={periodStart}
                                onChange={(e) => setPeriodStart(e.target.value)}
                                className="w-full h-9 rounded-md border border-gray-200 px-3 text-sm"
                            />
                        </div>
                        <div className="space-y-1">
                            <label className="text-xs font-semibold text-gray-500">Hasta</label>
                            <input
                                type="date"
                                value={periodEnd}
                                onChange={(e) => setPeriodEnd(e.target.value)}
                                className="w-full h-9 rounded-md border border-gray-200 px-3 text-sm"
                            />
                        </div>
                        <div className="space-y-1">
                            <label className="text-xs font-semibold text-gray-500">Estados</label>
                            <div className="h-9 rounded-md border border-gray-200 px-3 flex items-center gap-3">
                                {ALL_STATES.map((state) => (
                                    <label key={state} className="text-xs text-gray-700 flex items-center gap-1.5">
                                        <input
                                            type="checkbox"
                                            checked={selectedStates.includes(state)}
                                            onChange={() => toggleState(state)}
                                        />
                                        {state}
                                    </label>
                                ))}
                            </div>
                        </div>
                    </div>
                    <div className="mt-3">
                        <Button className="bg-blue-600 hover:bg-blue-700 text-white flex items-center gap-2" onClick={() => void loadOverview()}>
                            <Calendar size={14} />
                            Aplicar filtros
                        </Button>
                    </div>
                </div>

                {error && (
                    <div className="rounded-xl border border-red-200 bg-red-50 text-red-700 px-4 py-3 text-sm">
                        {error}
                    </div>
                )}

                <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
                    <div className="rounded-xl border border-gray-200 bg-white p-4">
                        <p className="text-xs text-gray-500 font-semibold uppercase">Tentative</p>
                        <p className="text-xl font-black text-gray-900">{formatHours(overview?.totals.tentativeHours || 0)}</p>
                    </div>
                    <div className="rounded-xl border border-gray-200 bg-white p-4">
                        <p className="text-xs text-gray-500 font-semibold uppercase">Committed</p>
                        <p className="text-xl font-black text-gray-900">{formatHours(overview?.totals.committedHours || 0)}</p>
                    </div>
                    <div className="rounded-xl border border-gray-200 bg-white p-4">
                        <p className="text-xs text-gray-500 font-semibold uppercase">Actual</p>
                        <p className="text-xl font-black text-gray-900">{formatHours(overview?.totals.actualHours || 0)}</p>
                    </div>
                    <div className="rounded-xl border border-gray-200 bg-white p-4">
                        <p className="text-xs text-gray-500 font-semibold uppercase">Total</p>
                        <p className="text-xl font-black text-blue-700">{formatHours(overview?.totals.totalHours || 0)}</p>
                    </div>
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
                                            <div key={month.label} className="flex flex-col items-center">
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
                            </div>
                        )}
                    </div>

                    <div className="rounded-2xl border border-gray-200 bg-white p-4 md:p-5 shadow-sm">
                        <div className="flex items-center gap-2 px-1 mb-3">
                            <BarChart3 size={18} className="text-gray-400" />
                            <h2 className="text-sm font-black text-gray-400 uppercase tracking-widest">Resumen por Miembro</h2>
                        </div>
                        <div className="overflow-x-auto">
                            <table className="w-full text-sm">
                                <thead className="bg-gray-50 text-gray-600">
                                    <tr>
                                        <th className="px-4 py-3 text-left font-semibold">Miembro</th>
                                        <th className="px-4 py-3 text-left font-semibold">Rol</th>
                                        <th className="px-4 py-3 text-right font-semibold">Capacidad</th>
                                        <th className="px-4 py-3 text-right font-semibold">Tentative</th>
                                        <th className="px-4 py-3 text-right font-semibold">Committed</th>
                                        <th className="px-4 py-3 text-right font-semibold">Actual</th>
                                        <th className="px-4 py-3 text-right font-semibold">Utilización</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {(overview?.members || []).length === 0 ? (
                                        <tr>
                                            <td colSpan={7} className="px-4 py-6 text-center text-gray-400">
                                                No hay ocupación por miembro en el periodo seleccionado.
                                            </td>
                                        </tr>
                                    ) : (
                                        (overview?.members || []).map((member) => (
                                            <tr key={member.teamMemberId} className="border-t border-gray-100">
                                                <td className="px-4 py-3 font-medium text-gray-900">{member.name}</td>
                                                <td className="px-4 py-3 text-gray-600">{member.role}</td>
                                                <td className="px-4 py-3 text-right text-gray-600">{formatHours(member.capacityHours)}</td>
                                                <td className="px-4 py-3 text-right text-gray-600">{formatHours(member.tentativeHours)}</td>
                                                <td className="px-4 py-3 text-right text-gray-600">{formatHours(member.committedHours)}</td>
                                                <td className="px-4 py-3 text-right text-gray-600">{formatHours(member.actualHours)}</td>
                                                <td className="px-4 py-3 text-right font-semibold text-gray-900">
                                                    {(member.utilizationRatio * 100).toFixed(1)}%
                                                </td>
                                            </tr>
                                        ))
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </div>

                    <div className="space-y-4">
                        <div className="flex items-center gap-2 px-1">
                            <BarChart3 size={18} className="text-gray-400" />
                            <h2 className="text-sm font-black text-gray-400 uppercase tracking-widest">Resumen por Célula</h2>
                        </div>
                        <div className="overflow-x-auto rounded-xl border border-gray-200 bg-white">
                            <table className="w-full text-sm">
                                <thead className="bg-gray-50 text-gray-600">
                                    <tr>
                                        <th className="px-4 py-3 text-left font-semibold">Célula</th>
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
                                                No hay ocupación por célula en el periodo seleccionado.
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
