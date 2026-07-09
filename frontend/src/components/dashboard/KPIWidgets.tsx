
'use client';

import React from 'react';
import { Card } from '@/components/ui/Card';
import {
    TrendingUp,
    TrendingDown,
    Minus,
    Target,
    Percent,
    DollarSign,
    PieChart,
    Activity,
    AlertCircle,
    ChevronRight,
    BarChart3,
} from 'lucide-react';
import { motion } from 'framer-motion';
import type { Quote } from '@/components/dashboard/QuoteCard';
import { formatMoneyAmount } from '@/lib/utils';
import type { DashboardKpiSummaryResponse } from '@/types/dashboard';

interface KPIWidgetsProps {
    kpiSummary: DashboardKpiSummaryResponse | null;
    kpiPreviousSummary?: DashboardKpiSummaryResponse | null;
    kpiLoading: boolean;
    kpiError: string | null;
}

type HealthBand = 'red' | 'amber' | 'green' | 'neutral';

/** Semáforo a partir del margen % (umbrales 15/25, consistentes con el cotizador). */
function marginBand(marginPct: number): HealthBand {
    if (marginPct < 15) return 'red';
    if (marginPct < 25) return 'amber';
    return 'green';
}

/** Semáforo a partir del win-rate %. */
function winRateBand(winRate: number): HealthBand {
    if (winRate < 20) return 'red';
    if (winRate < 40) return 'amber';
    return 'green';
}

/** Peor de dos bandas (rojo domina). 'neutral' solo si ambas lo son. */
function worstBand(a: HealthBand, b: HealthBand): HealthBand {
    const rank: Record<HealthBand, number> = { red: 0, amber: 1, green: 2, neutral: 3 };
    return rank[a] <= rank[b] ? a : b;
}

const HEALTH_CONFIG: Record<HealthBand, { label: string; desc: string; box: string; dot: string }> = {
    green: {
        label: 'Negocio saludable',
        desc: 'Margen y conversión por encima del objetivo en la ventana.',
        box: 'border-emerald-200 bg-emerald-50/70 text-emerald-900',
        dot: 'bg-emerald-500',
    },
    amber: {
        label: 'Requiere atención',
        desc: 'Margen o conversión por debajo del objetivo. Revisa el pipeline.',
        box: 'border-amber-200 bg-amber-50/70 text-amber-900',
        dot: 'bg-amber-500',
    },
    red: {
        label: 'En riesgo',
        desc: 'Margen o conversión en nivel crítico. Prioriza revisar cotizaciones.',
        box: 'border-red-200 bg-red-50/70 text-red-900',
        dot: 'bg-red-500',
    },
    neutral: {
        label: 'Sin datos suficientes',
        desc: 'Aún no hay propuestas en la ventana seleccionada.',
        box: 'border-gray-200 bg-gray-50 text-gray-600',
        dot: 'bg-gray-400',
    },
};

/** Flecha + variación en puntos vs. el periodo previo (null → no se muestra). */
function TrendBadge({ current, previous }: { current: number; previous: number | null }) {
    if (previous === null || !Number.isFinite(previous)) return null;
    const diff = Math.round((current - previous) * 10) / 10;
    if (Math.abs(diff) < 0.1) {
        return (
            <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-gray-400">
                <Minus size={12} strokeWidth={2.5} /> sin cambio vs. previo
            </span>
        );
    }
    const up = diff > 0;
    return (
        <span
            className={`inline-flex items-center gap-1 text-[11px] font-bold ${up ? 'text-emerald-600' : 'text-red-500'}`}
        >
            {up ? <TrendingUp size={12} strokeWidth={2.5} /> : <TrendingDown size={12} strokeWidth={2.5} />}
            {up ? '+' : ''}{diff} pts vs. previo
        </span>
    );
}

function formatRangeLabel(isoStart: string, isoEnd: string): string {
    try {
        const a = new Date(isoStart);
        const b = new Date(isoEnd);
        return `${a.toLocaleDateString('es-CO', { day: 'numeric', month: 'short', year: 'numeric' })} — ${b.toLocaleDateString('es-CO', { day: 'numeric', month: 'short', year: 'numeric' })}`;
    } catch {
        return `${isoStart} — ${isoEnd}`;
    }
}

export function KPIWidgets({ kpiSummary, kpiPreviousSummary, kpiLoading, kpiError }: KPIWidgetsProps) {
    type KpiCard = {
        title: string;
        value: string;
        icon: React.ComponentType<{ size?: number; strokeWidth?: number }>;
        color: string;
        bg: string;
        subtitle?: string;
        trend?: React.ReactNode;
    };

    if (kpiLoading) {
        return (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
                {[1, 2, 3, 4, 5].map((i) => (
                    <Card key={i} className="p-5 h-[140px] animate-pulse bg-gray-100/80" />
                ))}
            </div>
        );
    }

    if (kpiError || !kpiSummary) {
        return (
            <Card className="p-6 border-amber-200 bg-amber-50/60">
                <p className="text-sm font-bold text-amber-900">
                    {kpiError || 'No hay datos de KPI para mostrar.'}
                </p>
                <p className="text-xs text-amber-800/80 mt-2">
                    Métricas basadas en la última cotización guardada por proyecto (excluye borradores).
                </p>
            </Card>
        );
    }

    const { kpis, currency, meta } = kpiSummary;
    const rangeHint = formatRangeLabel(meta.applied_start, meta.applied_end);

    // --- KPIs derivados (responden "¿gano o pierdo?") ---
    const hasData = kpis.numeroPropuestasRealizadas > 0;
    const winRate = hasData
        ? (kpis.numeroPropuestasGanadas / kpis.numeroPropuestasRealizadas) * 100
        : 0;
    const marginPct = kpis.totalCotizadoConImpuestos > 0
        ? (kpis.margenNetoTotal / kpis.totalCotizadoConImpuestos) * 100
        : 0;

    // --- Comparación vs. periodo previo (tendencia) ---
    const prev = kpiPreviousSummary?.kpis ?? null;
    const prevWinRate = prev && prev.numeroPropuestasRealizadas > 0
        ? (prev.numeroPropuestasGanadas / prev.numeroPropuestasRealizadas) * 100
        : null;
    const prevMarginPct = prev && prev.totalCotizadoConImpuestos > 0
        ? (prev.margenNetoTotal / prev.totalCotizadoConImpuestos) * 100
        : null;

    // --- Semáforo de salud (peor entre margen y win-rate) ---
    const health: HealthBand = hasData
        ? worstBand(marginBand(marginPct), winRateBand(winRate))
        : 'neutral';
    const healthCfg = HEALTH_CONFIG[health];
    const mBand = marginBand(marginPct);

    const cards: KpiCard[] = [
        {
            title: 'Win-rate (conversión)',
            value: hasData ? `${winRate.toFixed(0)}%` : '—',
            icon: Target,
            color: 'text-indigo-600',
            bg: 'bg-indigo-50/70',
            subtitle: `${kpis.numeroPropuestasGanadas}/${kpis.numeroPropuestasRealizadas} ganadas`,
            trend: <TrendBadge current={winRate} previous={prevWinRate} />,
        },
        {
            title: 'Margen % promedio',
            value: hasData ? `${marginPct.toFixed(1)}%` : '—',
            icon: Percent,
            color: mBand === 'red' ? 'text-red-600' : mBand === 'amber' ? 'text-amber-600' : 'text-emerald-600',
            bg: mBand === 'red' ? 'bg-red-50/70' : mBand === 'amber' ? 'bg-amber-50/70' : 'bg-emerald-50/70',
            subtitle: 'Margen neto / total cotizado',
            trend: <TrendBadge current={marginPct} previous={prevMarginPct} />,
        },
        {
            title: 'Total cotizado (impuestos)',
            value: `${currency} ${formatMoneyAmount(kpis.totalCotizadoConImpuestos)}`,
            icon: DollarSign,
            color: 'text-primary',
            bg: 'bg-primary-soft/60',
            subtitle: 'Última versión / proyecto',
        },
        {
            title: 'Costo operacional',
            value: `${currency} ${formatMoneyAmount(kpis.costoTotalOperacional)}`,
            icon: Activity,
            color: 'text-violet-600',
            bg: 'bg-violet-50/60',
        },
        {
            title: 'Margen neto total',
            value: `${currency} ${formatMoneyAmount(kpis.margenNetoTotal)}`,
            icon: TrendingUp,
            color: 'text-emerald-600',
            bg: 'bg-emerald-50/60',
        },
        {
            title: 'Propuestas realizadas',
            value: String(kpis.numeroPropuestasRealizadas),
            icon: BarChart3,
            color: 'text-slate-600',
            bg: 'bg-slate-50/80',
            subtitle: 'Proyectos no Draft en ventana',
        },
        {
            title: 'Propuestas ganadas',
            value: String(kpis.numeroPropuestasGanadas),
            icon: PieChart,
            color: 'text-green-600',
            bg: 'bg-green-50/60',
            subtitle: 'Estado Won en misma ventana',
        },
    ];

    return (
        <div className="space-y-3">
            <p className="text-[11px] font-semibold text-gray-500 tracking-wide">
                KPI por actualización de cotización · {rangeHint} · {meta.timezone}
            </p>

            {/* Semáforo de salud: responde "¿gano o pierdo?" de un vistazo */}
            <div className={`flex items-center gap-3 rounded-2xl border px-4 py-3 ${healthCfg.box}`}>
                <span className={`w-2.5 h-2.5 rounded-full flex-shrink-0 ${healthCfg.dot}`} />
                <div className="min-w-0">
                    <p className="text-[13.5px] font-bold leading-tight">{healthCfg.label}</p>
                    <p className="text-[12px] opacity-80 leading-snug">{healthCfg.desc}</p>
                </div>
                {hasData && (
                    <div className="ml-auto flex items-center gap-4 text-right flex-shrink-0">
                        <div>
                            <p className="text-[9px] font-black uppercase tracking-widest opacity-70">Margen</p>
                            <p className="text-[15px] font-bold leading-none">{marginPct.toFixed(1)}%</p>
                        </div>
                        <div>
                            <p className="text-[9px] font-black uppercase tracking-widest opacity-70">Win-rate</p>
                            <p className="text-[15px] font-bold leading-none">{winRate.toFixed(0)}%</p>
                        </div>
                    </div>
                )}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
                {cards.map((metric, index) => (
                    <motion.div
                        key={metric.title}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: index * 0.06 }}
                    >
                        <Card className="p-5 hover:shadow-[0_20px_40px_rgba(0,0,0,0.06)] transition-all duration-500 group h-full border border-gray-100/80">
                            <div className="flex justify-between items-start mb-4">
                                <div
                                    className={`w-10 h-10 rounded-[14px] flex items-center justify-center ${metric.bg} ${metric.color} group-hover:scale-105 transition-transform duration-500`}
                                >
                                    <metric.icon size={20} strokeWidth={1.5} />
                                </div>
                            </div>
                            <div>
                                <p className="text-[10px] font-bold text-gray-500 uppercase tracking-[0.15em] mb-2">
                                    {metric.title}
                                </p>
                                <h3 className="text-2xl font-bold text-gray-900 tracking-tight">{metric.value}</h3>
                                {metric.subtitle && (
                                    <p className="text-xs text-gray-500 mt-2 font-medium flex items-center gap-1.5">
                                        <span className="w-1.5 h-1.5 rounded-full bg-gray-300" />
                                        {metric.subtitle}
                                    </p>
                                )}
                                {metric.trend && <div className="mt-2">{metric.trend}</div>}
                            </div>
                        </Card>
                    </motion.div>
                ))}
            </div>
        </div>
    );
}

type AlertType = 'critical' | 'warning' | 'info';
type PipelineAlert = {
    id: string;
    type: AlertType;
    text: string;
    action: string;
};

interface AlertsWidgetProps {
    quotes: Quote[];
}

export function AlertsWidget({ quotes }: AlertsWidgetProps) {
    const criticalMarginCount = quotes.filter((q) => q.margin < 15 && q.status !== 'accepted').length;
    const viewedNoDecisionCount = quotes.filter((q) => q.status === 'viewed').length;
    const draftCount = quotes.filter((q) => q.status === 'draft').length;

    const alerts: PipelineAlert[] = [];
    if (criticalMarginCount > 0) {
        alerts.push({
            id: 'critical-margin',
            type: 'critical',
            text: `${criticalMarginCount} cotización${criticalMarginCount === 1 ? '' : 'es'} con rentabilidad crítica (<15%)`,
            action: 'Revisar'
        });
    }
    if (viewedNoDecisionCount > 0) {
        alerts.push({
            id: 'viewed-followup',
            type: 'warning',
            text: `${viewedNoDecisionCount} cotización${viewedNoDecisionCount === 1 ? '' : 'es'} vistas sin cierre`,
            action: 'Seguir'
        });
    }
    if (draftCount > 0) {
        alerts.push({
            id: 'draft-pending',
            type: 'info',
            text: `${draftCount} borrador${draftCount === 1 ? '' : 'es'} pendiente${draftCount === 1 ? '' : 's'} de envío`,
            action: 'Ver'
        });
    }

    return (
        <Card className="p-5 h-full">
            <div className="flex items-center justify-between mb-4">
                <div>
                    <h3 className="text-lg font-bold text-gray-900 tracking-tight">Atención Requerida</h3>
                    <p className="text-[10px] font-black text-system-gray uppercase tracking-widest mt-1">Acciones pendientes</p>
                </div>
                <span className="w-8 h-8 bg-red-50 text-red-600 text-xs font-black flex items-center justify-center rounded-xl border border-red-100/50">
                    {alerts.length}
                </span>
            </div>

            {alerts.length === 0 ? (
                <div className="text-sm text-gray-500 font-medium py-8 text-center">
                    Sin alertas por ahora. El pipeline se ve saludable.
                </div>
            ) : (
                <div className="space-y-4">
                    {alerts.map((alert) => (
                        <motion.div
                            whileHover={{ x: 4 }}
                            key={alert.id}
                            className="flex items-start gap-4 p-4 rounded-2xl hover:bg-gray-50/50 transition-all group cursor-pointer border border-transparent hover:border-gray-100/50"
                        >
                            <div className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 ${alert.type === 'critical' ? 'bg-red-50 text-red-500' :
                                alert.type === 'warning' ? 'bg-orange-50 text-orange-600' :
                                    'bg-primary-soft text-primary'
                                }`}>
                                <AlertCircle size={20} strokeWidth={1.5} />
                            </div>
                            <div className="flex-1 pt-0.5">
                                <p className="text-sm text-gray-700 font-bold leading-snug tracking-tight mb-1">{alert.text}</p>
                                <span className="text-[11px] font-black text-primary uppercase tracking-widest flex items-center gap-1">
                                    {alert.action} <ChevronRight size={10} strokeWidth={3} />
                                </span>
                            </div>
                        </motion.div>
                    ))}
                </div>
            )}
        </Card>
    );
}
