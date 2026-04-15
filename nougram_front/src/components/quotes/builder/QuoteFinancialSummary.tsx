
'use client';

import React from 'react';
import { Card, CardContent } from '@/components/ui/Card';
import { useQuoteBuilder } from '@/context/QuoteBuilderContext';
import { Info, ArrowUpRight, Percent, Users, Receipt } from 'lucide-react';
import Link from 'next/link';
import { formatDisplayNumber, formatMoneyAmount } from '@/lib/utils';

export function QuoteFinancialSummary() {
    const { summary, state, toggleTax, taxes, setTargetMargin, teamMembers } = useQuoteBuilder();
    const [objectiveMode, setObjectiveMode] = React.useState<'margin' | 'markup'>('margin');

    const markupRatioFromMargin = React.useMemo(() => {
        const margin = Number(state.targetMargin || 0);
        if (!Number.isFinite(margin) || margin <= 0) return 0;
        if (margin >= 1) return 0;
        return margin / (1 - margin);
    }, [state.targetMargin]);

    const objectiveDisplay = React.useMemo(() => {
        if (objectiveMode === 'markup') {
            return `${formatDisplayNumber(markupRatioFromMargin * 100, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}%`;
        }
        return `${formatDisplayNumber(state.targetMargin * 100, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}%`;
    }, [objectiveMode, markupRatioFromMargin, state.targetMargin]);

    const updateFromMarkupPercent = (markupPercent: number) => {
        const safePercent = Math.max(0, Math.min(markupPercent, 300));
        const markupRatio = safePercent / 100; // 150% => 1.5
        const marginRatio = markupRatio / (1 + markupRatio); // m = markup/(1+markup)
        setTargetMargin(Number.isFinite(marginRatio) ? marginRatio : 0);
    };

    // Margin Color Logic
    let marginColor = 'text-red-500';
    let marginBg = 'bg-red-50 border-red-100';
    let marginLabel = 'Bajo';

    if (summary.netMarginPercent >= 30) {
        marginColor = 'text-green-600';
        marginBg = 'bg-green-50 border-green-100';
        marginLabel = 'Excelente';
    } else if (summary.netMarginPercent >= 20) {
        marginColor = 'text-yellow-600';
        marginBg = 'bg-yellow-50 border-yellow-100';
        marginLabel = 'Aceptable';
    }

    return (
        <Card className="h-full bg-white shadow-[0_20px_50px_rgba(0,0,0,0.05)] border-0 ring-1 ring-gray-100 sticky top-4 overflow-hidden">
            <div className="absolute top-0 right-0 w-32 h-32 bg-blue-50 rounded-full blur-3xl -mr-16 -mt-16 opacity-50" />

            <CardContent className="p-6 space-y-5 relative">
                {/* 0. Critical Alerts */}
                {summary.totalClientPrice < summary.totalInternalCost && (
                    <div className="bg-red-50 border-l-4 border-red-500 p-4 rounded-r-md flex items-start gap-3">
                        <div className="text-red-500 mt-0.5"><Info size={16} /></div>
                        <div>
                            <h4 className="text-xs font-black text-red-700 uppercase tracking-wide">Pérdida Crítica</h4>
                            <p className="text-xs text-red-600 font-medium">El precio es menor que el costo operativo.</p>
                        </div>
                    </div>
                )}
                {summary.totalClientPrice >= summary.totalInternalCost && summary.netMarginPercent < 20 && (
                    <div className="bg-yellow-50 border-l-4 border-yellow-500 p-4 rounded-r-md flex items-start gap-3">
                        <div className="text-yellow-600 mt-0.5"><Info size={16} /></div>
                        <div>
                            <h4 className="text-xs font-black text-yellow-700 uppercase tracking-wide">Margen Bajo</h4>
                            <p className="text-xs text-yellow-600 font-medium">El margen es inferior al objetivo del 20%.</p>
                        </div>
                    </div>
                )}

                {/* 1. Header: Primary Metric */}
                <div>
                    <div className="flex items-center justify-between mb-2">
                        <p className="text-[10px] font-black text-gray-400 uppercase tracking-[0.2em]">Presupuesto para Cliente</p>
                        <Receipt size={14} className="text-gray-300" />
                    </div>
                    <div className="flex items-baseline gap-1">
                        <span className="text-sm font-bold text-gray-400">$</span>
                        <p className="text-5xl font-black text-gray-900 tracking-tighter">
                            {formatMoneyAmount(summary.totalClientPrice)}
                        </p>
                    </div>
                </div>

                {/* 2. Interactive Controls Section */}
                <div className="space-y-6">
                    {/* Taxes */}
                    <div className="bg-gray-50/50 p-4 rounded-2xl border border-gray-100 space-y-3">
                        <div className="flex items-center justify-between">
                            <h4 className="text-[10px] font-black text-gray-500 uppercase tracking-widest">Impuestos</h4>
                            <span className="text-[10px] bg-white px-2 py-0.5 rounded-full border border-gray-100 font-bold text-gray-400">
                                {state.selectedTaxIds.length} Activos
                            </span>
                        </div>

                        <div className="space-y-2.5">
                            {taxes.length === 0 && (
                                <div className="rounded-xl border border-dashed border-gray-200 bg-white p-3 text-xs text-gray-600">
                                    No tienes impuestos activos configurados para esta organización.
                                    <Link href="/admin/taxes" className="ml-1 font-semibold text-blue-600 hover:text-blue-700">
                                        Configurar impuestos
                                    </Link>
                                </div>
                            )}
                            {taxes.map(tax => {
                                const isSelected = state.selectedTaxIds.includes(tax.id);
                                const amount = isSelected ? summary.totalClientPrice * (tax.percentage / 100) : 0;

                                return (
                                    <div
                                        key={tax.id}
                                        className={`flex items-center justify-between p-2 rounded-xl transition-all ${isSelected ? 'bg-white shadow-sm ring-1 ring-gray-100' : 'opacity-60'}`}
                                    >
                                        <label className="flex items-center gap-3 cursor-pointer text-xs font-bold text-gray-600">
                                            <input
                                                type="checkbox"
                                                checked={isSelected}
                                                onChange={() => toggleTax(tax.id)}
                                                className="w-4 h-4 rounded-lg border-gray-200 text-blue-600 focus:ring-blue-500/20"
                                            />
                                            {tax.name} <span className="text-[10px] text-gray-400">({tax.percentage}%)</span>
                                        </label>
                                        <span className={`text-xs font-black ${isSelected ? 'text-gray-900' : 'text-gray-400'}`}>
                                            ${formatMoneyAmount(amount)}
                                        </span>
                                    </div>
                                );
                            })}
                        </div>
                    </div>

                    {/* Margin Control */}
                    <div className="space-y-3">
                        <div className="flex justify-between items-center">
                            <label className="text-[10px] font-black text-gray-500 uppercase tracking-widest">
                                {objectiveMode === 'markup' ? 'Objetivo (Markup)' : 'Margen de Ganancia'}
                            </label>
                            <div className="flex items-center gap-1 bg-blue-50 text-blue-700 px-2 py-0.5 rounded-full text-[10px] font-black">
                                <Percent size={10} />
                                {objectiveDisplay}
                            </div>
                        </div>
                        <div className="flex items-center gap-2">
                            <button
                                type="button"
                                onClick={() => setObjectiveMode('margin')}
                                className={`text-[10px] px-2 py-1 rounded-full font-black transition-colors ${
                                    objectiveMode === 'margin'
                                        ? 'bg-blue-600 text-white'
                                        : 'bg-gray-100 text-gray-500 hover:bg-gray-200'
                                }`}
                            >
                                Margen
                            </button>
                            <button
                                type="button"
                                onClick={() => setObjectiveMode('markup')}
                                className={`text-[10px] px-2 py-1 rounded-full font-black transition-colors ${
                                    objectiveMode === 'markup'
                                        ? 'bg-blue-600 text-white'
                                        : 'bg-gray-100 text-gray-500 hover:bg-gray-200'
                                }`}
                            >
                                Markup
                            </button>
                        </div>
                        <div className="relative pt-1 px-1">
                            {objectiveMode === 'margin' ? (
                                <input
                                    type="range"
                                    min="0"
                                    max="0.95"
                                    step="0.01"
                                    value={state.targetMargin}
                                    onChange={(e) => setTargetMargin(parseFloat(e.target.value))}
                                    className="w-full h-1.5 bg-gray-100 rounded-lg appearance-none cursor-pointer accent-blue-600 hover:accent-blue-700 transition-all"
                                />
                            ) : (
                                <div className="flex items-center gap-2">
                                    <input
                                        type="range"
                                        min="0"
                                        max="300"
                                        step="5"
                                        value={Math.round(markupRatioFromMargin * 100)}
                                        onChange={(e) => updateFromMarkupPercent(parseFloat(e.target.value))}
                                        className="w-full h-1.5 bg-gray-100 rounded-lg appearance-none cursor-pointer accent-blue-600 hover:accent-blue-700 transition-all"
                                    />
                                    <input
                                        type="number"
                                        min={0}
                                        max={300}
                                        step={5}
                                        value={Math.round(markupRatioFromMargin * 100)}
                                        onChange={(e) => updateFromMarkupPercent(parseFloat(e.target.value || '0'))}
                                        className="w-20 rounded-lg border border-gray-200 px-2 py-1 text-xs font-bold text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-200"
                                    />
                                    <span className="text-xs font-bold text-gray-500">%</span>
                                </div>
                            )}
                            <div className="flex justify-between text-[8px] font-bold text-gray-300 mt-2 uppercase tracking-tighter">
                                <span>Volumen</span>
                                <span>Equilibrio</span>
                                <span>Alta Rentabilidad</span>
                            </div>
                            {objectiveMode === 'markup' && (
                                <p className="mt-2 text-[10px] text-gray-500 font-medium">
                                    150% de markup equivale aproximadamente a {formatDisplayNumber(state.targetMargin * 100, { minimumFractionDigits: 1, maximumFractionDigits: 1 })}% de margen.
                                </p>
                            )}
                        </div>
                    </div>
                </div>

                {/* 3. Final Total */}
                <div className="flex justify-between items-center p-5 bg-blue-900 rounded-[1.5rem] text-white shadow-xl shadow-blue-100 ring-4 ring-blue-50">
                    <div className="space-y-0.5">
                        <p className="text-[9px] font-black text-blue-300 uppercase tracking-widest">Total Factura</p>
                        <p className="text-xs text-blue-100 font-medium">Incluye impuestos</p>
                    </div>
                        <p className="text-2xl font-black tracking-tighter">
                        ${formatMoneyAmount(summary.totalWithTaxes)}
                    </p>
                </div>

                {/* 4. Business Reality Section */}
                <div className="pt-2">
                    <div className="flex items-center gap-2 mb-6">
                        <div className="h-0.5 w-6 bg-blue-500 rounded-full" />
                        <h3 className="text-[10px] font-black text-gray-400 uppercase tracking-[0.2em]">Realidad Financiera</h3>
                    </div>

                    <div className="space-y-3">
                        <div className="flex justify-between items-center px-1">
                            <span className="text-xs font-bold text-gray-500">Ingreso Neto (Excl. Impuestos)</span>
                            <span className="text-sm font-black text-gray-900">${formatMoneyAmount(summary.realIncome)}</span>
                        </div>

                        <div className="flex justify-between items-center px-1">
                            <span className="text-xs font-bold text-gray-500">Costo Operativo (Total BCR)</span>
                            <span className="text-sm font-black text-red-500">-${formatMoneyAmount(summary.totalInternalCost)}</span>
                        </div>

                        {/* Resulting Benefit */}
                        <div className={`relative p-4 rounded-2xl border ${marginBg} transition-all duration-500`}>
                            <div className="flex justify-between items-start mb-1">
                                <div className="space-y-1">
                                    <p className={`text-[10px] font-black uppercase tracking-widest ${marginColor}`}>Utilidad Neta ({marginLabel})</p>
                                    <p className={`text-3xl font-black ${marginColor} tracking-tighter`}>
                                        {formatDisplayNumber(summary.netMarginPercent, { minimumFractionDigits: 1, maximumFractionDigits: 1 })}%
                                    </p>
                                </div>
                                <div className={`p-2 rounded-xl bg-white shadow-sm border border-gray-100 ${marginColor}`}>
                                    <ArrowUpRight size={20} />
                                </div>
                            </div>
                            <p className={`text-xl font-black ${marginColor} mt-2 opacity-80`}>
                                ${formatMoneyAmount(summary.netMarginAmount)}
                            </p>
                        </div>
                    </div>
                </div>

                {/* 5. Resource Quickview */}
                {state.showResourceAllocation && state.resourceAllocations.length > 0 && (
                    <div className="pt-6 border-t border-gray-100">
                        <div className="flex items-center justify-between mb-4">
                            <div className="flex flex-col">
                                <span className="text-[9px] font-black text-gray-400 uppercase tracking-widest">Capacidad Asignada</span>
                                <span className="text-xs font-black text-blue-600">
                                    {state.resourceAllocations.reduce((sum, a) => sum + a.hours, 0)} Horas Totales
                                </span>
                            </div>
                            <Users size={16} className="text-gray-200" />
                        </div>

                        <div className="flex -space-x-3 overflow-hidden p-1">
                            {state.resourceAllocations.slice(0, 5).map((alloc, idx) => {
                                const member = teamMembers.find(m => m.id === alloc.teamMemberId);
                                if (!member) return null;
                                return (
                                    <div
                                        key={idx}
                                        className="inline-flex h-9 w-9 rounded-full ring-4 ring-white bg-gradient-to-br from-blue-50 to-blue-100 items-center justify-center text-[10px] font-black text-blue-700 border border-blue-50 shadow-sm transition-transform hover:scale-110 active:scale-95 cursor-pointer"
                                        title={`${member.name} (${alloc.hours}h)`}
                                    >
                                        {member.name[0]}
                                    </div>
                                );
                            })}
                            {state.resourceAllocations.length > 5 && (
                                <div className="inline-flex h-9 w-9 rounded-full ring-4 ring-white bg-gray-50 items-center justify-center text-[10px] font-black text-gray-400 border border-gray-100 shadow-sm">
                                    +{state.resourceAllocations.length - 5}
                                </div>
                            )}
                        </div>
                    </div>
                )}
            </CardContent>
        </Card>
    );
}
