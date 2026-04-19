import * as React from "react";
import { BCRSummary } from "@/types/admin";
import { formatCurrency, formatDisplayNumber } from "@/lib/utils";
import { AlertCircle, ChevronDown, ChevronUp, TrendingUp } from "lucide-react";
import { cn } from "@/lib/utils";

interface BCRSummaryCardProps {
    summary: BCRSummary | null;
    isLoading?: boolean;
}

function Row({ label, value }: { label: string; value: string }) {
    return (
        <div className="flex items-center justify-between">
            <span className="text-[12px] text-gray-500">{label}</span>
            <span className="text-[12.5px] font-semibold text-gray-800 tabular-nums">{value}</span>
        </div>
    );
}

export function BCRSummaryCard({ summary, isLoading }: BCRSummaryCardProps) {
    const [isExpanded, setIsExpanded] = React.useState(false);
    const summaryCurrency = (summary?.primary_currency || "COP").toUpperCase();

    if (isLoading) {
        return (
            <div className="rounded-2xl border border-gray-200 bg-white shadow-sm overflow-hidden animate-pulse">
                <div className="p-4 space-y-3">
                    <div className="h-3 w-24 bg-gray-200 rounded-full" />
                    <div className="h-8 w-36 bg-gray-200 rounded-full" />
                    <div className="h-3 w-full bg-gray-200 rounded-full" />
                    <div className="h-3 w-3/4 bg-gray-200 rounded-full" />
                </div>
            </div>
        );
    }

    if (!summary || summary.active_team_members === 0) {
        return (
            <div className="rounded-2xl border border-amber-200 bg-warning-soft p-4 space-y-2">
                <div className="flex items-center gap-2 text-amber-700">
                    <AlertCircle size={14} />
                    <span className="text-[12.5px] font-semibold">Sin cálculo de BCR</span>
                </div>
                <p className="text-[12px] text-amber-600">
                    Configura al menos un miembro del equipo activo para calcular el costo hora real.
                </p>
            </div>
        );
    }

    return (
        <div className="rounded-2xl border border-gray-200 bg-white shadow-sm overflow-hidden">
            {/* Hero BCR */}
            <div className="px-4 pt-4 pb-3 border-b border-gray-100">
                <div className="flex items-center justify-between mb-2">
                    <span className="text-[10px] font-semibold uppercase tracking-[0.5px] text-gray-400">BCR · Costo hora real</span>
                    <TrendingUp size={12} className="text-gray-300" />
                </div>
                <div className="flex items-baseline gap-1.5">
                    <span className="text-[30px] font-bold text-gray-900 tabular-nums leading-none">
                        {formatCurrency(summary.blended_cost_rate, summaryCurrency)}
                    </span>
                    <span className="text-[12px] text-gray-400 font-medium">/ hora</span>
                </div>
                <p className="mt-1 text-[10.5px] text-gray-400">
                    {summary.active_team_members} miembro{summary.active_team_members !== 1 ? 's' : ''} activo{summary.active_team_members !== 1 ? 's' : ''}
                </p>
            </div>

            {/* Stats */}
            <div className="px-4 py-3 space-y-2">
                <Row label="Costo mensual total" value={formatCurrency(summary.total_monthly_costs, summaryCurrency)} />
                <Row
                    label="Horas facturables/mes"
                    value={`${formatDisplayNumber(summary.total_monthly_hours, { minimumFractionDigits: 1, maximumFractionDigits: 1 })} hrs`}
                />
            </div>

            {/* Expanded breakdown */}
            {isExpanded && (
                <div className="px-4 pb-3 pt-0 space-y-2 border-t border-dashed border-gray-100 animate-in slide-in-from-top-1">
                    <p className="text-[9.5px] font-semibold uppercase tracking-[0.5px] text-gray-400 pt-2">Desglose mensual</p>
                    <Row label="Salarios (con cargas)" value={formatCurrency(summary.total_salaries, summaryCurrency)} />
                    <Row label="Gastos fijos" value={formatCurrency(summary.total_fixed_overhead, summaryCurrency)} />
                    <Row label="Herramientas / SaaS" value={formatCurrency(summary.total_tools_costs, summaryCurrency)} />
                </div>
            )}

            {/* Toggle */}
            <button
                onClick={() => setIsExpanded(v => !v)}
                className="flex w-full items-center justify-center gap-1 border-t border-gray-100 py-2.5 text-[11px] font-medium text-gray-400 hover:text-gray-600 hover:bg-surface-2 transition-colors"
            >
                {isExpanded ? <><ChevronUp size={11} /> Ocultar detalles</> : <><ChevronDown size={11} /> Ver desglose</>}
            </button>
        </div>
    );
}
