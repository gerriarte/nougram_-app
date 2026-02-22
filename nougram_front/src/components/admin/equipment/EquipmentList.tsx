
'use client';

import React, { useState } from 'react';
import { useEquipment } from '@/hooks/useEquipment';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Equipment } from '@/types/equipment';
// calculateDepreciation is handled by hook now, but detail modal needs it imported or passed
import { LifeProgressBar } from './LifeProgressBar';
import { EquipmentForm } from './EquipmentForm';
import { EquipmentDetailModal } from './EquipmentDetailModal';

export function EquipmentList() {
    const { equipment, removeEquipment, getStats } = useEquipment();
    const [editingId, setEditingId] = useState<string | null>(null);
    const [detailId, setDetailId] = useState<string | null>(null);
    const [isFormOpen, setIsFormOpen] = useState(false);

    // Filter Detail Data
    const detailEquipment = detailId ? equipment.find(e => e.id === detailId) || null : null;

    const handleEdit = (id: string) => {
        setEditingId(id);
        setIsFormOpen(true);
    };

    const handleCreate = () => {
        setEditingId(null);
        setIsFormOpen(true);
    };

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <h3 className="text-lg font-semibold text-gray-800">Inventario de Activos</h3>
                <Button onClick={handleCreate}>+ Registrar Equipo</Button>
            </div>

            {equipment.length === 0 ? (
                <div className="text-center py-12 bg-gray-50 border border-dashed rounded-lg">
                    <p className="text-gray-500">No hay equipos registrados.</p>
                    <p className="text-sm text-gray-400">Registra tus activos para calcular la depreciación real.</p>
                </div>
            ) : (
                <div className="grid grid-cols-1 gap-4">
                    {equipment.map(eq => {
                        const stats = getStats(eq);

                        return (
                            <Card key={eq.id} className="p-4 hover:shadow-md transition-shadow">
                                <div className="flex flex-col md:flex-row justify-between gap-4">
                                    {/* Left: Info */}
                                    <div className="flex-1">
                                        <div className="flex items-center gap-2 mb-1">
                                            <span className="px-2 py-0.5 rounded text-xs font-bold bg-gray-100 text-gray-600 uppercase">
                                                {eq.category}
                                            </span>
                                            <h4 className="font-bold text-gray-900">{eq.name}</h4>
                                        </div>
                                        <p className="text-xs text-gray-500 mb-3">
                                            Comprado: {eq.purchaseDate} • Precio: ${eq.purchasePrice.toLocaleString()} {eq.currency}
                                        </p>

                                        {/* Progress Bar */}
                                        <div className="max-w-md space-y-1">
                                            <div className="flex justify-between text-xs font-medium text-gray-600">
                                                <span>Vida Útil: {stats.percentageDepreciated.toFixed(0)}% Consumida</span>
                                                <span>{stats.monthsRemaining} meses restantes</span>
                                            </div>
                                            <LifeProgressBar percentage={stats.percentageDepreciated} />
                                        </div>
                                    </div>

                                    {/* Right: Financials */}
                                    <div className="text-right flex flex-col justify-center min-w-[150px]">
                                        <p className="text-xs text-gray-400 uppercase">Depreciación Mensual</p>
                                        <p className="text-xl font-bold text-gray-900">
                                            ${stats.monthlyDepreciation.toLocaleString()}
                                        </p>
                                        <p className="text-xs text-gray-500 mt-1">
                                            Valor en Libros: ${stats.currentBookValue.toLocaleString()}
                                        </p>

                                        <div className="mt-2 flex justify-end gap-2 text-xs">
                                            <button onClick={() => setDetailId(eq.id)} className="text-blue-600 hover:underline font-bold">Ver Detalle</button>
                                            <button onClick={() => handleEdit(eq.id)} className="text-gray-500 hover:underline">Editar</button>
                                            <button onClick={() => removeEquipment(eq.id)} className="text-red-500 hover:underline">Eliminar</button>
                                        </div>
                                    </div>
                                </div>
                            </Card>
                        );
                    })}
                </div>
            )}

            {isFormOpen && (
                <EquipmentForm
                    onClose={() => setIsFormOpen(false)}
                    initialData={editingId ? equipment.find(e => e.id === editingId) : undefined}
                />
            )}

            <EquipmentDetailModal
                equipment={detailEquipment}
                onClose={() => setDetailId(null)}
            />
        </div>
    );
}

export default EquipmentList;
