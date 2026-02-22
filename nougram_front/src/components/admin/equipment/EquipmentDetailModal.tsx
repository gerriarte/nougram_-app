
'use client';

import React from 'react';
import { Equipment } from '@/types/equipment';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/Dialog';
import { DepreciationScheduleTable } from './DepreciationScheduleTable';
import { AssetValueChart } from './AssetValueChart';
import { LifeProgressBar } from './LifeProgressBar';
import { calculateDepreciation } from '@/lib/depreciation';

interface EquipmentDetailModalProps {
    equipment: Equipment | null;
    onClose: () => void;
}

export function EquipmentDetailModal({ equipment, onClose }: EquipmentDetailModalProps) {
    if (!equipment) return null;

    const stats = calculateDepreciation(equipment);

    return (
        <Dialog open={!!equipment} onOpenChange={(open) => !open && onClose()}>
            <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
                <DialogHeader>
                    <DialogTitle className="flex justify-between items-center pr-8">
                        <span>{equipment.name}</span>
                        <span className="text-xs font-normal text-gray-500 bg-gray-100 px-2 py-1 rounded">
                            {equipment.category}
                        </span>
                    </DialogTitle>
                </DialogHeader>

                <div className="space-y-8">
                    {/* 1. Key Metrics */}
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                        <div className="p-4 bg-blue-50 rounded-lg border border-blue-100">
                            <p className="text-xs text-blue-600 uppercase font-black">Depreciación Mensual</p>
                            <p className="text-2xl font-bold text-blue-900">${stats.monthlyDepreciation.toLocaleString(undefined, { maximumFractionDigits: 0 })}</p>
                        </div>
                        <div className="p-4 bg-gray-50 rounded-lg border border-gray-100">
                            <p className="text-xs text-gray-500 uppercase font-black">Valor en Libros</p>
                            <p className="text-xl font-bold text-gray-900">${stats.currentBookValue.toLocaleString(undefined, { maximumFractionDigits: 0 })}</p>
                        </div>
                        <div className="p-4 bg-gray-50 rounded-lg border border-gray-100">
                            <p className="text-xs text-gray-500 uppercase font-black">Vida Útil Restante</p>
                            <p className="text-xl font-bold text-gray-900">{stats.monthsRemaining} Meses</p>
                        </div>
                        <div className="p-4 bg-gray-50 rounded-lg border border-gray-100">
                            <p className="text-xs text-gray-500 uppercase font-black">Progreso</p>
                            <div className="mt-2">
                                <LifeProgressBar percentage={stats.percentageDepreciated} />
                            </div>
                            <p className="text-[10px] text-right mt-1 text-gray-400">{stats.percentageDepreciated.toFixed(1)}%</p>
                        </div>
                    </div>

                    {/* 2. Chart */}
                    <AssetValueChart equipment={equipment} />

                    {/* 3. Schedule Table */}
                    <DepreciationScheduleTable equipment={equipment} />
                </div>
            </DialogContent>
        </Dialog>
    );
}
