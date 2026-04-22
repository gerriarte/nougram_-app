'use client';

import React from 'react';
import { Input } from '@/components/ui/Input';
import { Toggle } from '@/components/ui/Toggle';
import { NumInput } from '@/components/ui/NumInput';
import { Shield } from 'lucide-react';
import { useQuoteBuilder } from '@/context/QuoteBuilderContext';
import { formatCurrency } from '@/lib/utils';
import { cn } from '@/lib/utils';

export function ContingencySection() {
    const { state, setContingency, summary } = useQuoteBuilder();

    const contingency = state.contingency || { description: '', type: 'percentage', value: 0 };
    const isActive = !!state.contingency;

    const handleToggle = () => {
        if (isActive) {
            setContingency(undefined);
        } else {
            setContingency({ description: 'Imprevistos generales', type: 'percentage', value: 5 });
        }
    };

    const update = (updates: Partial<typeof contingency>) =>
        setContingency({ ...contingency, ...updates });

    return (
        <div className={cn(
            'rounded-xl border bg-white shadow-sm overflow-hidden transition-colors',
            isActive ? 'border-amber-200' : 'border-gray-200'
        )}>
            {/* Header */}
            <div className="flex items-center gap-3 px-4 py-3.5">
                <div className={cn(
                    'flex h-8 w-8 shrink-0 items-center justify-center rounded-lg transition-colors',
                    isActive ? 'bg-warning-soft text-amber-700' : 'bg-surface-2 text-gray-400'
                )}>
                    <Shield size={15} strokeWidth={2} />
                </div>
                <div className="flex-1 min-w-0">
                    <p className="text-[13px] font-semibold text-gray-800">Imprevistos</p>
                    <p className="text-[11.5px] text-gray-400">Reserva para riesgos o costos no planeados</p>
                </div>
                <Toggle checked={isActive} onChange={handleToggle} />
            </div>

            {/* Expanded content */}
            {isActive && (
                <div className="border-t border-dashed border-amber-100 px-4 pb-4 pt-3 space-y-3 animate-in fade-in slide-in-from-top-1">
                    <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
                        {/* Description */}
                        <div className="sm:col-span-1 space-y-1">
                            <label className="text-[10px] font-semibold uppercase tracking-wide text-gray-400">Descripción</label>
                            <Input
                                value={contingency.description}
                                onChange={e => update({ description: e.target.value })}
                                placeholder="Ej: Variación en tasa de cambio…"
                                className="h-9 bg-white border-amber-200 focus:border-amber-400"
                            />
                        </div>

                        {/* Type toggle */}
                        <div className="space-y-1">
                            <label className="text-[10px] font-semibold uppercase tracking-wide text-gray-400">Tipo</label>
                            <div className="flex h-9 rounded-lg border border-amber-200 bg-white p-1">
                                {(['percentage', 'fixed'] as const).map(t => (
                                    <button
                                        key={t}
                                        type="button"
                                        onClick={() => update({ type: t })}
                                        className={cn(
                                            'flex-1 rounded-md text-[11px] font-semibold transition-colors',
                                            contingency.type === t
                                                ? 'bg-warning-soft text-amber-700'
                                                : 'text-gray-400 hover:bg-surface-2'
                                        )}
                                    >
                                        {t === 'percentage' ? 'Porcentaje' : 'Valor fijo'}
                                    </button>
                                ))}
                            </div>
                        </div>

                        {/* Value */}
                        <div className="space-y-1">
                            <label className="text-[10px] font-semibold uppercase tracking-wide text-gray-400">
                                {contingency.type === 'percentage' ? 'Porcentaje' : 'Valor'}
                            </label>
                            <NumInput
                                value={contingency.value}
                                onChange={v => update({ value: v === '' ? 0 : v })}
                                suffix={contingency.type === 'percentage' ? '%' : undefined}
                                className="border-amber-200 focus-within:border-amber-400"
                                placeholder="0"
                            />
                        </div>
                    </div>

                    {/* Impact summary */}
                    <div className="flex items-center justify-between rounded-lg border border-amber-100 bg-warning-soft px-3 py-2.5">
                        <span className="text-[12px] text-amber-700">Impacto en cotización</span>
                        <div className="flex items-center gap-5">
                            <div className="text-right">
                                <span className="block text-[10px] text-amber-600/70">Costo adicional</span>
                                <span className="text-[13px] font-semibold text-amber-900">
                                    +{formatCurrency(summary.contingencyAmount || 0, state.currency)}
                                </span>
                            </div>
                            <div className="text-right">
                                <span className="block text-[10px] text-amber-600/70">Total con imprevistos</span>
                                <span className="text-[13px] font-semibold text-amber-900">
                                    {formatCurrency(summary.contingencyTotal || 0, state.currency)}
                                </span>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
