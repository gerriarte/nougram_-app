'use client';

import React, { useMemo } from 'react';
// import dynamic from 'next/dynamic';
import { useNougram } from '@/context/NougramCoreContext';
import { useEquipment } from '@/hooks/useEquipment';
import { calculateDepreciation } from '@/lib/depreciation';

import EquipmentList from '@/components/admin/equipment/EquipmentList';

export default function EquipmentPage() {
    const { state } = useNougram();
    const { equipment } = useEquipment();

    const stats = useMemo(() => {
        const totalAmortization = equipment.reduce((sum, eq) => {
            const dep = calculateDepreciation(eq);
            return sum + dep.monthlyDepreciation;
        }, 0);
        return { totalAmortization, count: equipment.length };
    }, [equipment]);

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-2xl font-bold text-gray-900">Amortización de Equipos</h1>
                <p className="text-gray-500">
                    Gestiona tus activos y visualiza cómo su depreciación impacta tu Costo Hora Real (BCR).
                </p>
            </div>

            {/* KPI Summary */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-white p-4 rounded-lg border shadow-sm">
                    <p className="text-xs font-bold text-gray-400 uppercase">Impacto Total BCR</p>
                    <div className="flex items-baseline gap-2">
                        <p className="text-2xl font-bold text-gray-900">
                            +${(stats.totalAmortization / (state.financials.billableHours || 1)).toLocaleString(undefined, { maximumFractionDigits: 0 })}
                        </p>
                        <span className="text-xs text-gray-500">/ hora</span>
                    </div>
                </div>
                <div className="bg-white p-4 rounded-lg border shadow-sm">
                    <p className="text-xs font-bold text-gray-400 uppercase">Amortización Mensual</p>
                    <p className="text-2xl font-bold text-gray-900">
                        ${stats.totalAmortization.toLocaleString()}
                    </p>
                </div>
                <div className="bg-white p-4 rounded-lg border shadow-sm">
                    <p className="text-xs font-bold text-gray-400 uppercase">Activos Registrados</p>
                    <p className="text-2xl font-bold text-gray-900">
                        {stats.count}
                    </p>
                </div>
            </div>

            <EquipmentList />
        </div>
    );
}
