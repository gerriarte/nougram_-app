'use client';

import React from 'react';
import { useQuoteBuilder } from '@/context/QuoteBuilderContext';
import { formatMoneyAmount } from '@/lib/utils';
import { AlertCircle, AlertTriangle, ArrowUpRight } from 'lucide-react';
import Link from 'next/link';
import { cn } from '@/lib/utils';

// ── Tone helpers ───────────────────────────────────────────────────
function marginTone(pct: number) {
    if (pct < 15) return 'danger';
    if (pct < 25) return 'warn';
    return 'good';
}
const TONE_CLASSES = {
    danger: { text: 'text-critical', bg: 'bg-critical-soft', badge: 'bg-critical text-white', bar: 'bg-critical' },
    warn:   { text: 'text-warning',  bg: 'bg-warning-soft',  badge: 'bg-warning text-white',  bar: 'bg-warning' },
    good:   { text: 'text-success',  bg: 'bg-success-soft',  badge: 'bg-success text-white',  bar: 'bg-success' },
};
const TONE_LABELS = { danger: 'BAJO', warn: 'ATENCIÓN', good: 'SALUDABLE' };

// ── StatRow ────────────────────────────────────────────────────────
function StatRow({
    label, hint, value, muted,
}: {
    label: string;
    hint?: string;
    value: string;
    muted?: boolean;
}) {
    return (
        <div className="flex items-baseline justify-between gap-3">
            <div className="min-w-0 pr-2">
                <span className={cn('text-[11.5px] font-medium', muted ? 'text-gray-400' : 'text-gray-600')}>
                    {label}
                </span>
                {hint && <span className="block text-[10.5px] text-gray-400">{hint}</span>}
            </div>
            <span className={cn(
                'shrink-0 tabular-nums text-right text-[14px] font-semibold',
                muted ? 'text-gray-400' : 'text-gray-900'
            )}>
                {value}
            </span>
        </div>
    );
}

// ── MarginSlider ───────────────────────────────────────────────────
function MarginSlider({
    mode, setMode, marginValue, onChangeMargin,
}: {
    mode: 'margin' | 'markup';
    setMode: (m: 'margin' | 'markup') => void;
    marginValue: number;
    onChangeMargin: (v: number) => void;
}) {
    const isMargin = mode === 'margin';
    const displayPct = isMargin ? marginValue * 100 : (marginValue / (1 - marginValue)) * 100;
    const max = isMargin ? 80 : 300;
    const sliderPct = isMargin ? (marginValue * 100) / max : displayPct / max;
    const tone = marginTone(marginValue * 100);
    const barClass = TONE_CLASSES[tone].bar;
    const textClass = TONE_CLASSES[tone].text;
    const thumbBorderClass = tone === 'danger' ? 'border-critical' : tone === 'warn' ? 'border-warning' : 'border-success';

    const handleSliderChange = (raw: number) => {
        if (isMargin) {
            onChangeMargin(Math.min(raw / 100, 0.95));
        } else {
            const markupRatio = raw / 100;
            onChangeMargin(Math.min(markupRatio / (1 + markupRatio), 0.95));
        }
    };

    return (
        <div>
            <div className="mb-3.5 flex gap-1 rounded-lg bg-surface-2 p-1">
                {(['margin', 'markup'] as const).map(m => (
                    <button
                        key={m}
                        type="button"
                        onClick={() => setMode(m)}
                        className={cn(
                            'flex-1 h-7 rounded-md text-[12px] font-semibold transition-colors',
                            mode === m ? 'bg-white shadow-sm text-gray-800' : 'text-gray-400 hover:text-gray-600'
                        )}
                    >
                        {m === 'margin' ? 'Margen' : 'Markup'}
                    </button>
                ))}
            </div>

            <div className="mb-2.5 flex items-baseline justify-between">
                <span className="text-[11.5px] font-medium text-gray-500">
                    {isMargin ? 'Margen sobre venta' : 'Markup sobre costo'}
                </span>
                <span className={cn('text-[22px] font-bold tabular-nums leading-none', textClass)}>
                    {displayPct.toFixed(0)}%
                </span>
            </div>

            <div className="relative flex h-6 items-center">
                <div className="absolute inset-x-0 h-[5px] rounded-full bg-gray-100" />
                <div
                    className={cn('absolute left-0 h-[5px] rounded-full transition-colors', barClass)}
                    style={{ width: `${Math.min(sliderPct * 100, 100)}%` }}
                />
                {isMargin && [15, 25].map(m => (
                    <div
                        key={m}
                        className="absolute h-3 w-px bg-gray-300 opacity-60"
                        style={{ left: `${(m / max) * 100}%`, top: '50%', transform: 'translate(-50%, -50%)' }}
                    />
                ))}
                <input
                    type="range"
                    min={0}
                    max={max}
                    step={1}
                    value={Math.round(displayPct)}
                    onChange={e => handleSliderChange(Number(e.target.value))}
                    className="absolute inset-0 h-full w-full cursor-pointer opacity-0"
                />
                <div
                    className={cn('pointer-events-none absolute h-4 w-4 rounded-full border-2 bg-white shadow-sm transition-colors', thumbBorderClass)}
                    style={{ left: `${Math.min(sliderPct * 100, 100)}%`, transform: 'translate(-50%, 0)' }}
                />
            </div>
            <div className="mt-2 flex justify-between text-[10px] text-gray-400">
                <span>0%</span>
                {isMargin && <><span className="text-warning">15%</span><span>25% obj.</span></>}
                <span>{max}%</span>
            </div>
        </div>
    );
}

// ── Main ───────────────────────────────────────────────────────────
export function QuoteFinancialSummary() {
    const { summary, state, toggleTax, taxes, setTargetMargin } = useQuoteBuilder();
    const [sliderMode, setSliderMode] = React.useState<'margin' | 'markup'>('margin');

    const netMarginPct = summary.netMarginPercent || 0;
    const tone = marginTone(netMarginPct);
    const tc = TONE_CLASSES[tone];
    const fmt = (n: number) => `$${formatMoneyAmount(n)}`;

    const itemsWithUnknownCost = state.items.filter(
        item => (item.clientPrice || 0) > 0 && (item.internalCost || 0) === 0
    ).length;

    const hasTaxes = summary.totalTaxes > 0;

    return (
        <aside className="sticky top-4 flex flex-col gap-3 self-start max-h-[calc(100vh-6rem)] overflow-y-auto pb-4">

            {/* ── Card 1: Monto propuesta + Rentabilidad ── */}
            <div className="rounded-2xl border border-gray-200 bg-white shadow-sm overflow-hidden">

                {/* Header */}
                <div className="flex items-center justify-between px-4 pt-4 pb-0">
                    <span className="text-[10px] font-semibold uppercase tracking-[0.55px] text-gray-400">
                        Propuesta al cliente
                    </span>
                    <ArrowUpRight size={13} className="text-gray-300" />
                </div>

                {/* Hero 1 — Monto de la propuesta */}
                <div className="px-4 pt-3 pb-4 border-b border-gray-100">
                    <div className="text-[44px] font-bold tabular-nums leading-none tracking-tight text-gray-900">
                        {fmt(summary.totalClientPrice)}
                    </div>
                    <div className="mt-1.5 text-[11px] text-gray-400">
                        Precio base · sin impuestos
                    </div>
                    {hasTaxes && (
                        <div className="mt-2.5 flex items-center gap-2">
                            <span className="text-[10.5px] text-gray-400">Total a facturar</span>
                            <span className="text-[15px] font-bold tabular-nums text-gray-700">
                                {fmt(summary.totalWithTaxes)}
                            </span>
                        </div>
                    )}
                </div>

                {/* Hero 2 — Rentabilidad neta */}
                <div className={cn('px-4 py-3.5 border-b border-gray-100', tc.bg)}>
                    <div className="mb-2 flex items-center justify-between">
                        <span className="text-[10px] font-semibold uppercase tracking-[0.5px] text-gray-500">
                            Rentabilidad neta
                        </span>
                        <span className={cn('rounded-full px-2 py-px text-[9.5px] font-bold tracking-wide', tc.badge)}>
                            {TONE_LABELS[tone]}
                        </span>
                    </div>
                    <div className="flex flex-wrap items-end gap-x-3 gap-y-1">
                        <span className={cn('text-[32px] font-bold tabular-nums leading-none tracking-tight', tc.text)}>
                            {netMarginPct.toFixed(1)}%
                        </span>
                        <div className="min-w-0 pb-0.5">
                            <div className="text-[15px] font-semibold tabular-nums text-gray-900">
                                {fmt(summary.netMarginAmount || 0)}
                            </div>
                            <div className="text-[10.5px] text-gray-400">
                                {tone === 'danger' ? 'Bajo mínimo recomendado'
                                    : tone === 'warn' ? 'Bajo objetivo del 25%'
                                    : 'Por encima del objetivo'}
                            </div>
                        </div>
                    </div>
                </div>

                {/* Alerts */}
                {(itemsWithUnknownCost > 0 || (summary.totalClientPrice < summary.totalInternalCost && summary.totalInternalCost > 0)) && (
                    <div className="px-3 pb-3 pt-2.5 space-y-2">
                        {itemsWithUnknownCost > 0 && (
                            <div className="flex items-start gap-2.5 rounded-lg border border-amber-100 bg-amber-50/80 px-3 py-2.5">
                                <AlertCircle size={13} className="mt-0.5 shrink-0 text-amber-600" />
                                <div>
                                    <p className="text-[11.5px] font-semibold text-amber-800">
                                        {itemsWithUnknownCost} ítem{itemsWithUnknownCost > 1 ? 's' : ''} sin horas estimadas
                                    </p>
                                    <p className="text-[10.5px] text-amber-700/90">
                                        El margen está sobreestimado. Asigna horas o recursos.
                                    </p>
                                </div>
                            </div>
                        )}
                        {summary.totalClientPrice < summary.totalInternalCost && summary.totalInternalCost > 0 && (
                            <div className="flex items-start gap-2.5 rounded-lg border border-red-100 bg-critical-soft px-3 py-2.5">
                                <AlertTriangle size={13} className="mt-0.5 shrink-0 text-critical" />
                                <p className="text-[11.5px] font-medium text-red-700">
                                    El precio es menor que el costo operativo.
                                </p>
                            </div>
                        )}
                    </div>
                )}
            </div>

            {/* ── Card 2: Margen / Markup slider ── */}
            <div className="rounded-2xl border border-gray-200 bg-white p-4 shadow-sm">
                <div className="mb-3 text-[10px] font-semibold uppercase tracking-[0.5px] text-gray-400">
                    Objetivo de margen
                </div>
                <MarginSlider
                    mode={sliderMode}
                    setMode={setSliderMode}
                    marginValue={state.targetMargin}
                    onChangeMargin={setTargetMargin}
                />
            </div>

            {/* ── Card 3: Impuestos ── */}
            <div className="rounded-2xl border border-gray-200 bg-white p-4 shadow-sm">
                <div className="mb-3 flex items-center justify-between">
                    <span className="text-[10px] font-semibold uppercase tracking-[0.5px] text-gray-400">
                        Impuestos
                    </span>
                    <span className="text-[10.5px] text-gray-400">{state.selectedTaxIds.length} activos</span>
                </div>
                {taxes.length === 0 ? (
                    <div className="rounded-lg border border-dashed border-gray-200 p-3 text-[11.5px] text-gray-500">
                        Sin impuestos configurados.{' '}
                        <Link href="/admin/taxes" className="font-semibold text-primary hover:underline">
                            Configurar
                        </Link>
                    </div>
                ) : (
                    <div className="space-y-1.5">
                        {taxes.map(tax => {
                            const isSelected = state.selectedTaxIds.includes(tax.id);
                            const amount = isSelected ? summary.totalClientPrice * (tax.percentage / 100) : 0;
                            return (
                                <label
                                    key={tax.id}
                                    className={cn(
                                        'flex cursor-pointer items-center gap-3 rounded-lg border px-3 py-2.5 transition-colors',
                                        isSelected
                                            ? 'border-gray-200 bg-white shadow-sm'
                                            : 'border-transparent bg-surface-2 opacity-60'
                                    )}
                                >
                                    <input
                                        type="checkbox"
                                        checked={isSelected}
                                        onChange={() => toggleTax(tax.id)}
                                        className="h-3.5 w-3.5 rounded border-gray-300 text-primary focus:ring-primary/20"
                                    />
                                    <div className="flex-1 min-w-0">
                                        <span className="text-[12.5px] font-semibold text-gray-700">{tax.name}</span>
                                        <span className="ml-1.5 text-[10.5px] text-gray-400">{tax.percentage}%</span>
                                    </div>
                                    <span className={cn('tabular-nums text-[12.5px] font-semibold', isSelected ? 'text-gray-800' : 'text-gray-400')}>
                                        {fmt(amount)}
                                    </span>
                                </label>
                            );
                        })}
                    </div>
                )}
            </div>

            {/* ── Card 4: Resumen completo ── */}
            <div className="rounded-2xl border border-gray-200 bg-white p-4 shadow-sm">
                <div className="mb-3 text-[10px] font-semibold uppercase tracking-[0.5px] text-gray-400">
                    Resumen
                </div>
                <div className="space-y-2.5">
                    <StatRow
                        label="Total a cobrar"
                        hint="Precio base al cliente"
                        value={fmt(summary.totalClientPrice)}
                    />
                    {summary.expensesInternalCost > 0 ? (
                        <>
                            <StatRow
                                label="Servicios internos"
                                hint="Horas × BCR"
                                value={`–${fmt(summary.totalInternalCost - summary.expensesInternalCost)}`}
                                muted
                            />
                            <StatRow
                                label="Proveedores"
                                hint={`costo ${fmt(summary.expensesInternalCost)} → cliente ${fmt(summary.expensesClientPrice)}`}
                                value={`–${fmt(summary.expensesInternalCost)}`}
                                muted
                            />
                        </>
                    ) : (
                        <StatRow
                            label="Costo de ejecución"
                            hint="Recursos + gastos directos"
                            value={`–${fmt(summary.totalInternalCost)}`}
                            muted
                        />
                    )}
                    {hasTaxes && (
                        <StatRow
                            label="Impuestos"
                            value={fmt(summary.totalTaxes)}
                            muted
                        />
                    )}
                </div>

                <div className="my-3 h-px bg-gray-100" />

                {/* Ganancia neta — highlighted */}
                <div className={cn('flex items-center justify-between rounded-xl px-3 py-3', tc.bg)}>
                    <div>
                        <div className={cn('text-[10px] font-bold uppercase tracking-wide mb-0.5', tc.text)}>
                            Ganancia neta
                        </div>
                        <div className={cn('text-[26px] font-bold tabular-nums leading-none tracking-tight', tc.text)}>
                            {netMarginPct.toFixed(1)}%
                        </div>
                    </div>
                    <div className="text-right">
                        <div className={cn('text-[19px] font-bold tabular-nums', tc.text)}>
                            {fmt(summary.netMarginAmount || 0)}
                        </div>
                        {hasTaxes && (
                            <div className="text-[10px] text-gray-400 mt-0.5">
                                Total factura {fmt(summary.totalWithTaxes)}
                            </div>
                        )}
                    </div>
                </div>
            </div>

        </aside>
    );
}
