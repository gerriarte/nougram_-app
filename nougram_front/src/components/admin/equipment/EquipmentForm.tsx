
'use client';

import React, { useState, useEffect } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Equipment, EquipmentCategory, DepreciationMethod, Currency } from '@/types/equipment';
import { calculateDepreciation } from '@/lib/depreciation';
import { useEquipment } from '@/hooks/useEquipment';

interface EquipmentFormProps {
    onClose: () => void;
    initialData?: Equipment;
}

export function EquipmentForm({ onClose, initialData }: EquipmentFormProps) {
    const { addEquipment, updateEquipment } = useEquipment();
    const [formData, setFormData] = useState<Partial<Equipment>>({
        category: 'Hardware',
        currency: 'COP',
        depreciationMethod: 'straight_line',
        usefulLifeMonths: 36,
        salvageValue: 0,
        purchaseDate: new Date().toISOString().split('T')[0],
        purchasePrice: 0,
        isActive: true,
        ...initialData
    });

    const [preview, setPreview] = useState<any>(null);

    // Calculate Preview on changes
    useEffect(() => {
        if (formData.purchasePrice && formData.usefulLifeMonths) {
            const mock = {
                ...formData,
                id: 'preview',
                name: 'preview'
            } as Equipment;

            setPreview(calculateDepreciation(mock));
        }
    }, [formData.purchasePrice, formData.salvageValue, formData.usefulLifeMonths, formData.currency]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        // Validation Logic (Section 7)
        if (formData.salvageValue! >= formData.purchasePrice!) {
            alert('El valor de salvamento debe ser MENOR al precio de compra.');
            return;
        }

        try {
            if (initialData) {
                await updateEquipment(initialData.id, formData);
            } else {
                await addEquipment(formData as any);
            }
            onClose();
        } catch (error) {
            console.error(error);
            alert('Error al guardar el equipo.');
        }
    };

    const handleChange = (field: keyof Equipment, value: any) => {
        setFormData(prev => ({ ...prev, [field]: value }));
    };

    return (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <Card className="w-full max-w-2xl bg-white shadow-2xl max-h-[90vh] overflow-y-auto">
                <form onSubmit={handleSubmit} className="p-6 space-y-6">
                    <div className="flex justify-between items-center border-b pb-4">
                        <h2 className="text-xl font-bold">{initialData ? 'Editar Equipo' : 'Registrar Nuevo Equipo'}</h2>
                        <button type="button" onClick={onClose} className="text-gray-400 hover:text-gray-600">✕</button>
                    </div>

                    {/* Basic Info */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="space-y-1">
                            <label className="text-sm font-medium">Nombre del Equipo</label>
                            <Input
                                required
                                value={formData.name || ''}
                                onChange={e => handleChange('name', e.target.value)}
                                placeholder="Ej: MacBook Pro 16 M2"
                            />
                        </div>
                        <div className="space-y-1">
                            <label className="text-sm font-medium">Categoría</label>
                            <select
                                className="w-full p-2 border rounded-md"
                                value={formData.category}
                                onChange={e => handleChange('category', e.target.value)}
                            >
                                <option value="Hardware">Hardware</option>
                                <option value="Software">Software (Licencias)</option>
                                <option value="Vehicles">Vehículos</option>
                                <option value="Office Equipment">Mobiliario / Oficina</option>
                            </select>
                        </div>
                    </div>

                    {/* Purchase Info */}
                    <div className="space-y-4 border rounded-lg p-4 bg-gray-50">
                        <h3 className="text-sm font-bold text-gray-700 uppercase">Información de Compra</h3>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <div className="space-y-1">
                                <label className="text-sm font-medium">Precio Compra</label>
                                <Input
                                    type="number" required min="1"
                                    value={formData.purchasePrice || ''}
                                    onChange={e => handleChange('purchasePrice', parseFloat(e.target.value))}
                                />
                            </div>
                            <div className="space-y-1">
                                <label className="text-sm font-medium">Moneda</label>
                                <select
                                    className="w-full p-2 border rounded-md"
                                    value={formData.currency}
                                    onChange={e => handleChange('currency', e.target.value)}
                                >
                                    <option value="COP">COP</option>
                                    <option value="USD">USD</option>
                                </select>
                            </div>
                            <div className="space-y-1">
                                <label className="text-sm font-medium">Fecha Compra</label>
                                <Input
                                    type="date" required
                                    value={formData.purchaseDate}
                                    onChange={e => handleChange('purchaseDate', e.target.value)}
                                />
                            </div>
                        </div>

                        {formData.currency !== 'COP' && (
                            <div className="space-y-1 animate-in fade-in">
                                <label className="text-sm font-medium text-blue-700">TRM del Día de Compra (USD → COP)</label>
                                <Input
                                    type="number" required placeholder="Ej: 4200"
                                    className="border-blue-300 bg-blue-50"
                                    value={formData.exchangeRateAtPurchase || ''}
                                    onChange={e => handleChange('exchangeRateAtPurchase', parseFloat(e.target.value))}
                                />
                                <p className="text-xs text-blue-600">
                                    💡 Usamos la TRM histórica para fijar el costo y evitar fluctuaciones mensuales.
                                </p>
                            </div>
                        )}
                    </div>

                    {/* Depreciation Params */}
                    <div className="space-y-4 pt-2">
                        <h3 className="text-sm font-bold text-gray-700 uppercase">Parámetros de Depreciación</h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="space-y-1">
                                <label className="text-sm font-medium">Vida Útil (Meses)</label>
                                <Input
                                    type="number" required min="1"
                                    value={formData.usefulLifeMonths}
                                    onChange={e => handleChange('usefulLifeMonths', parseFloat(e.target.value))}
                                />
                                <p className="text-xs text-gray-400">Estándar: PC (36), Muebles (120)</p>
                            </div>
                            <div className="space-y-1">
                                <label className="text-sm font-medium">Valor de Salvamento</label>
                                <Input
                                    type="number" required min="0"
                                    value={formData.salvageValue}
                                    onChange={e => handleChange('salvageValue', parseFloat(e.target.value))}
                                />
                                <p className="text-xs text-gray-400">Valor de reventa esperado al final.</p>
                            </div>
                        </div>
                    </div>

                    {/* Preview */}
                    {preview && (
                        <div className="bg-blue-50 border border-blue-100 p-4 rounded-lg flex justify-between items-center">
                            <div>
                                <p className="text-xs font-bold text-blue-800 uppercase">Impacto en Costos</p>
                                <p className="text-sm text-blue-600">Base Depreciable: ${(preview.currentBookValue + preview.totalDepreciated).toLocaleString()}</p>
                            </div>
                            <div className="text-right">
                                <p className="text-2xl font-bold text-blue-900">
                                    ${preview.monthlyDepreciation.toLocaleString()}
                                    <span className="text-xs font-normal text-blue-600"> / mes</span>
                                </p>
                            </div>
                        </div>
                    )}

                    <div className="flex justify-end gap-3 pt-4 border-t">
                        <Button type="button" variant="ghost" onClick={onClose}>Cancelar</Button>
                        <Button type="submit">Guardar Equipo</Button>
                    </div>
                </form>
            </Card>
        </div>
    );
}
