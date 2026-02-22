
'use client';

import React, { useState } from 'react';
import { useAdmin } from '@/context/AdminContext';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { FixedCostForm } from './FixedCostForm';
import { FixedCost } from '@/types/admin';

export function FixedCostList() {
    const { fixedCosts, deleteFixedCost, updateFixedCost, addFixedCost } = useAdmin();
    const [isFormOpen, setIsFormOpen] = useState(false);
    const [editingCost, setEditingCost] = useState<FixedCost | undefined>(undefined);

    const handleCreate = () => {
        setEditingCost(undefined);
        setIsFormOpen(true);
    };

    const handleEdit = (cost: FixedCost) => {
        setEditingCost(cost);
        setIsFormOpen(true);
    };

    const handleSave = (data: any) => {
        if (editingCost) {
            updateFixedCost(editingCost.id, data);
        } else {
            addFixedCost({
                ...data,
                id: crypto.randomUUID(),
                isActive: true
            });
        }
    };

    const handleDelete = (id: string) => {
        if (confirm('¿Estás seguro de eliminar este gasto?')) {
            deleteFixedCost(id);
        }
    };

    return (
        <Card>
            <CardHeader className="flex flex-row items-center justify-between">
                <div>
                    <CardTitle>Gastos Fijos</CardTitle>
                    <p className="text-sm text-gray-500">Costos recurrentes de operación.</p>
                </div>
                <Button onClick={handleCreate}>+ Agregar Gasto</Button>
            </CardHeader>
            <CardContent>
                <div className="overflow-x-auto">
                    <table className="w-full text-sm text-left">
                        <thead className="bg-gray-50 text-gray-700 uppercase text-xs">
                            <tr>
                                <th className="px-4 py-3">Nombre</th>
                                <th className="px-4 py-3">Categoría</th>
                                <th className="px-4 py-3">Costo Mensual</th>
                                <th className="px-4 py-3">Estado</th>
                                <th className="px-4 py-3 text-right">Acciones</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-200">
                            {fixedCosts.map(cost => (
                                <tr key={cost.id} className="hover:bg-gray-50">
                                    <td className="px-4 py-3 font-medium text-gray-900">
                                        {cost.name}
                                        {cost.description && <p className="text-xs text-gray-500 font-normal">{cost.description}</p>}
                                    </td>
                                    <td className="px-4 py-3">
                                        <Badge variant="default">{cost.category}</Badge>
                                    </td>
                                    <td className="px-4 py-3 font-semibold">
                                        ${cost.amountMonthly.toLocaleString()} {cost.currency}
                                    </td>
                                    <td className="px-4 py-3">
                                        <Badge variant={cost.isActive ? 'success' : 'default'} className="cursor-pointer" onClick={() => updateFixedCost(cost.id, { isActive: !cost.isActive })}>
                                            {cost.isActive ? 'Activo' : 'Inactivo'}
                                        </Badge>
                                    </td>
                                    <td className="px-4 py-3 text-right space-x-2">
                                        <Button variant="secondary" size="sm" onClick={() => handleEdit(cost)}>Editar</Button>
                                        <Button
                                            variant="destructive"
                                            size="sm"
                                            onClick={() => handleDelete(cost.id)}
                                        >
                                            🗑️
                                        </Button>
                                    </td>
                                </tr>
                            ))}
                            {fixedCosts.length === 0 && (
                                <tr>
                                    <td colSpan={5} className="px-4 py-8 text-center text-gray-500 italic">
                                        No hay gastos configurados.
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </CardContent>

            <FixedCostForm
                open={isFormOpen}
                onOpenChange={setIsFormOpen}
                initialData={editingCost}
                onSave={handleSave}
            />
        </Card>
    );
}
