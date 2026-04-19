'use client';

import React from 'react';
import { Truck, Trash2 } from 'lucide-react';
import { NumInput } from '@/components/ui/NumInput';
import { Input } from '@/components/ui/Input';
import { useQuoteBuilder } from '@/context/QuoteBuilderContext';
import { useNougram } from '@/context/NougramCoreContext';
import { QuoteExpense } from '@/types/quote-builder';
import { formatCurrency } from '@/lib/utils';
import { cn } from '@/lib/utils';

interface VendorItemRowProps {
    expense: QuoteExpense;
}

export function VendorItemRow({ expense }: VendorItemRowProps) {
    const { updateExpense, removeExpense } = useQuoteBuilder();
    const { state: coreState } = useNougram();
    const currency = coreState.identity.primaryCurrency || 'COP';

    const clientPrice = expense.cost * expense.quantity * (1 + expense.markupPercentage);

    return (
        <div className="group relative rounded-xl border border-gray-200 bg-white shadow-sm overflow-hidden">
            {/* Type badge strip */}
            <div className="flex items-center gap-2.5 border-b border-gray-100 px-4 py-2.5">
                <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-warning-soft text-amber-700">
                    <Truck size={13} strokeWidth={2} />
                </div>
                <span className="text-[11px] font-semibold uppercase tracking-wide text-amber-700">Proveedor</span>
                <button
                    type="button"
                    onClick={() => removeExpense(expense.id)}
                    className={cn(
                        'ml-auto flex h-7 w-7 items-center justify-center rounded-full text-gray-300 transition-colors',
                        'opacity-0 group-hover:opacity-100 hover:bg-red-50 hover:text-red-500'
                    )}
                >
                    <Trash2 size={13} />
                </button>
            </div>

            <div className="p-4 space-y-4">
                {/* Name + vendor */}
                <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                    <div className="space-y-1">
                        <label className="text-[11px] font-semibold text-gray-500">Nombre del ítem</label>
                        <Input
                            value={expense.name}
                            onChange={e => updateExpense(expense.id, { name: e.target.value })}
                            placeholder="Ej: Hosting anual"
                            className="h-9 bg-white"
                        />
                    </div>
                    <div className="space-y-1">
                        <label className="text-[11px] font-semibold text-gray-500">Proveedor</label>
                        <Input
                            value={expense.vendorName || ''}
                            onChange={e => updateExpense(expense.id, { vendorName: e.target.value })}
                            placeholder="Ej: AWS, Google, etc."
                            className="h-9 bg-white"
                        />
                    </div>
                </div>

                {/* Numeric fields + subtotal */}
                <div className="grid grid-cols-3 gap-3 sm:grid-cols-4">
                    <div className="space-y-1">
                        <label className="text-[11px] font-semibold text-gray-500">Costo unitario</label>
                        <NumInput
                            value={expense.cost}
                            onChange={v => updateExpense(expense.id, { cost: v === '' ? 0 : v })}
                            prefix={currency === 'USD' ? '$' : '$'}
                            placeholder="0"
                        />
                    </div>
                    <div className="space-y-1">
                        <label className="text-[11px] font-semibold text-gray-500">Cantidad</label>
                        <NumInput
                            value={expense.quantity}
                            onChange={v => updateExpense(expense.id, { quantity: v === '' ? 1 : Math.max(1, v) })}
                            placeholder="1"
                        />
                    </div>
                    <div className="space-y-1">
                        <label className="text-[11px] font-semibold text-gray-500">Margen (%)</label>
                        <NumInput
                            value={Math.round(expense.markupPercentage * 100)}
                            onChange={v => updateExpense(expense.id, { markupPercentage: v === '' ? 0 : v / 100 })}
                            suffix="%"
                            placeholder="10"
                        />
                    </div>
                    <div className="space-y-1 hidden sm:block">
                        <label className="text-[11px] font-semibold text-gray-500">Subtotal cliente</label>
                        <div className="flex h-9 items-center rounded-lg border border-gray-100 bg-surface-2 px-3 text-[13px] font-semibold tabular-nums text-gray-800">
                            {formatCurrency(clientPrice, currency)}
                        </div>
                    </div>
                </div>

                {/* Mobile subtotal */}
                <div className="flex items-center justify-between rounded-lg border border-gray-100 bg-surface-2 px-3 py-2 sm:hidden">
                    <span className="text-[11px] text-gray-500">Subtotal cliente</span>
                    <span className="text-[13px] font-semibold tabular-nums text-gray-800">
                        {formatCurrency(clientPrice, currency)}
                    </span>
                </div>
            </div>
        </div>
    );
}
