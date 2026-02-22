
'use client';

import React, { useState, useMemo } from 'react';
// import dynamic from 'next/dynamic';
import { FixedCostList } from '@/components/admin/overhead/FixedCostList';
import { OverheadSummary } from '@/components/admin/overhead/OverheadSummary';
// import { EquipmentList } from '@/components/admin/equipment/EquipmentList';
import { useNougram } from '@/context/NougramCoreContext';
import { useEquipment } from '@/hooks/useEquipment';
import { calculateDepreciation } from '@/lib/depreciation';

import EquipmentList from '@/components/admin/equipment/EquipmentList';

export default function OverheadPage() {
    const { state } = useNougram();
    const { equipment } = useEquipment();
    const [activeTab, setActiveTab] = useState<'fixed' | 'equipment'>('fixed');

    const equipmentStats = useMemo(() => {
        const totalAmortization = equipment.reduce((sum, eq) => {
            const dep = calculateDepreciation(eq);
            return sum + dep.monthlyDepreciation;
        }, 0);
        return { totalAmortization, count: equipment.length };
    }, [equipment]);

    return (
        <div className="space-y-8">
            <div>
                <h1 className="text-2xl font-bold text-gray-900">Overhead & Activos</h1>
                <p className="text-gray-500">Gestiona tus costos fijos, licencias y la amortización de equipos.</p>
            </div>

            {/* Quick Stats / Summary (Global) */}
            <OverheadSummary />

            {/* Tabs Navigation */}
            <div className="border-b border-gray-200">
                <nav className="-mb-px flex space-x-8" aria-label="Tabs">
                    <button
                        onClick={() => setActiveTab('fixed')}
                        className={`
                            whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm
                            ${activeTab === 'fixed'
                                ? 'border-blue-500 text-blue-600'
                                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}
                        `}
                    >
                        Gastos Fijos (Arriendo/Software)
                    </button>
                    <button
                        onClick={() => setActiveTab('equipment')}
                        className={`
                            whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm
                            ${activeTab === 'equipment'
                                ? 'border-blue-500 text-blue-600'
                                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}
                        `}
                    >
                        Amortización de Equipos
                    </button>
                </nav>
            </div>

            {/* Content */}
            <div className="min-h-[400px]">
                {activeTab === 'fixed' ? (
                    <FixedCostList />
                ) : (
                    <div className="space-y-6 animate-in fade-in slide-in-from-left-4 duration-300">
                        {/* Equipment KPI */}
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <div className="bg-blue-50 p-4 rounded-lg border border-blue-100">
                                <p className="text-xs font-bold text-blue-800 uppercase">Impacto Total BCR</p>
                                <div className="flex items-baseline gap-2">
                                    <p className="text-2xl font-bold text-blue-900">
                                        +${(equipmentStats.totalAmortization / (state.financials.billableHours || 1)).toLocaleString(undefined, { maximumFractionDigits: 0 })}
                                    </p>
                                    <span className="text-xs text-blue-600">/ hora</span>
                                </div>
                            </div>
                            <div className="bg-white p-4 rounded-lg border shadow-sm">
                                <p className="text-xs font-bold text-gray-400 uppercase">Amortización Mensual</p>
                                <p className="text-2xl font-bold text-gray-900">
                                    ${equipmentStats.totalAmortization.toLocaleString()}
                                </p>
                            </div>
                            <div className="bg-white p-4 rounded-lg border shadow-sm">
                                <p className="text-xs font-bold text-gray-400 uppercase">Activos Registrados</p>
                                <p className="text-2xl font-bold text-gray-900">
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
