
'use client';

import React, { useState, useMemo } from 'react';
import { cn } from '@/lib/utils';
// import dynamic from 'next/dynamic';
import { FixedCostList } from '@/components/admin/overhead/FixedCostList';
import { OverheadSummary } from '@/components/admin/overhead/OverheadSummary';
// import { EquipmentList } from '@/components/admin/equipment/EquipmentList';
import { useNougram } from '@/context/NougramCoreContext';
import { useEquipment } from '@/hooks/useEquipment';
import { calculateDepreciation } from '@/lib/depreciation';

import EquipmentList from '@/components/admin/equipment/EquipmentList';
import { formatCurrency } from '@/lib/utils';

export default function OverheadPage() {
    const { state } = useNougram();
    const { equipment } = useEquipment();
    const currency = state.identity.primaryCurrency || 'COP';
    const [activeTab, setActiveTab] = useState<'fixed' | 'equipment'>('fixed');

    const equipmentStats = useMemo(() => {
        const totalAmortization = equipment.reduce((sum, eq) => {
            const dep = calculateDepreciation(eq);
            return sum + dep.monthlyDepreciation;
        }, 0);
        return { totalAmortization, count: equipment.length };
    }, [equipment]);

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-[20px] font-bold text-gray-900">Inventario de gastos & activos</h1>
                <p className="text-[13px] text-gray-500 mt-0.5">Gestiona costos fijos, licencias y amortización de equipos.</p>
            </div>

            <OverheadSummary />

            {/* Pill tabs */}
            <div className="flex items-center gap-1 rounded-lg bg-surface-2 border border-gray-200 p-1 w-fit">
                {(['fixed', 'equipment'] as const).map((tab) => (
                    <button
                        key={tab}
                        type="button"
                        onClick={() => setActiveTab(tab)}
                        className={cn(
                            'px-4 py-1.5 rounded-md text-[12.5px] font-semibold transition-colors',
                            activeTab === tab ? 'bg-white shadow-sm text-gray-900' : 'text-gray-500 hover:text-gray-700'
                        )}
                    >
                        {tab === 'fixed' ? 'Gastos fijos' : 'Equipos'}
                    </button>
                ))}
            </div>

            <div className="min-h-[400px]">
                {activeTab === 'fixed' ? (
                    <FixedCostList />
                ) : (
                    <div className="space-y-5 animate-in fade-in slide-in-from-left-2 duration-200">
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
                                <p className="text-[10px] font-semibold uppercase tracking-wider text-gray-400">Impacto total BCR</p>
                                <div className="flex items-baseline gap-1.5 mt-1">
                                    <p className="text-[22px] font-bold text-gray-900">
                                        +{formatCurrency((equipmentStats.totalAmortization / (state.financials.billableHours || 1)), currency)}
                                    </p>
                                    <span className="text-[11px] text-gray-400">/ hora</span>
                                </div>
                            </div>
                            <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
                                <p className="text-[10px] font-semibold uppercase tracking-wider text-gray-400">Amortización mensual</p>
                                <p className="text-[22px] font-bold text-gray-900 mt-1">
                                    {formatCurrency(equipmentStats.totalAmortization, currency)}
                                </p>
                            </div>
                            <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
                                <p className="text-[10px] font-semibold uppercase tracking-wider text-gray-400">Activos registrados</p>
                                <p className="text-[22px] font-bold text-gray-900 mt-1">
                                    {equipmentStats.count}
                                </p>
                            </div>
                        </div>
                        <EquipmentList />
                    </div>
                )}
            </div>
        </div>
    );
}
