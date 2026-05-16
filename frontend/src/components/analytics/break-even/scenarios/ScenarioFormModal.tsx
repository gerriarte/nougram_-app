import React, { useState, useEffect } from 'react';
import { ScenarioConfig } from '@/types/break-even';
import { X } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';

interface ScenarioFormModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSave: (config: Omit<ScenarioConfig, 'id'>) => void;
    initialData?: ScenarioConfig;
    isLoading?: boolean;
}

export function ScenarioFormModal({ isOpen, onClose, onSave, initialData, isLoading = false }: ScenarioFormModalProps) {
    const [formData, setFormData] = useState({
        name: '',
        bcr_multiplier: '1.0',
        fixed_costs_adjustment: '0',
        average_margin_adjustment: '0'
    });

    useEffect(() => {
        if (initialData) {
            setFormData({
                name: initialData.name,
                bcr_multiplier: initialData.bcr_multiplier.toString(),
                fixed_costs_adjustment: initialData.fixed_costs_adjustment.toString(),
                average_margin_adjustment: initialData.average_margin_adjustment.toString()
            });
        } else {
            setFormData({
                name: '',
                bcr_multiplier: '1.0',
                fixed_costs_adjustment: '0',
                average_margin_adjustment: '0'
            });
        }
    }, [initialData, isOpen]);

    if (!isOpen) return null;

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        onSave({
            name: formData.name,
            bcr_multiplier: parseFloat(formData.bcr_multiplier),
            fixed_costs_adjustment: parseFloat(formData.fixed_costs_adjustment),
            average_margin_adjustment: parseFloat(formData.average_margin_adjustment)
        });
        // onClose(); // Handled by parent on success
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
            <div className="bg-white rounded-[24px] w-full max-w-lg shadow-2xl animate-in zoom-in-95 duration-200">
                <div className="flex justify-between items-center p-6 border-b border-gray-100">
                    <h2 className="text-xl font-bold text-gray-900">{initialData ? 'Editar Escenario' : 'Nuevo Escenario'}</h2>
                    <button onClick={onClose} className="text-gray-400 hover:text-gray-900 transition-colors">
                        <X size={24} />
                    </button>
                </div>

                <form onSubmit={handleSubmit} className="p-6 space-y-6">
                    {/* Name */}
                    <div className="space-y-2">
                        <label className="text-sm font-medium text-gray-700">Nombre del Escenario</label>
                        <Input
                            required
                            placeholder="Ej: Contratar Dev Senior"
                            value={formData.name}
                            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                            disabled={isLoading}
                        />
                    </div>

                    {/* BCR Multiplier */}
                    <div className="space-y-2">
                        <label className="text-sm font-medium text-gray-700">Multiplicador de BCR</label>
                        <div className="flex gap-4 items-center">
                            <Input
                                type="number" step="0.05"
                                value={formData.bcr_multiplier}
                                onChange={(e) => setFormData({ ...formData, bcr_multiplier: e.target.value })}
                                disabled={isLoading}
                            />
                            <span className="text-xs text-gray-500 w-full">1.0 = Sin cambio. Un valor mayor mejora el margen.</span>
                        </div>
                    </div>

                    {/* Fixed Costs */}
                    <div className="space-y-2">
                        <label className="text-sm font-medium text-gray-700">Ajuste Costos Fijos</label>
                        <div className="flex gap-4 items-center">
                            <Input
                                type="number" step="1000"
                                value={formData.fixed_costs_adjustment}
                                onChange={(e) => setFormData({ ...formData, fixed_costs_adjustment: e.target.value })}
                                disabled={isLoading}
                            />
                            <span className="text-xs text-gray-500 w-full">+ aumenta costos, - reduce costos.</span>
                        </div>
                    </div>

                    {/* Margin Adjustment */}
                    <div className="space-y-2">
                        <label className="text-sm font-medium text-gray-700">Ajuste Margen Promedio</label>
                        <div className="flex gap-4 items-center">
                            <Input
                                type="number" step="0.01"
                                value={formData.average_margin_adjustment}
                                onChange={(e) => setFormData({ ...formData, average_margin_adjustment: e.target.value })}
                                disabled={isLoading}
                            />
                            <span className="text-xs text-gray-500 w-full">0.15 = +15%.</span>
                        </div>
                    </div>

                    <div className="pt-4 flex gap-3">
                        <Button type="button" variant="secondary" className="flex-1" onClick={onClose} disabled={isLoading}>Cancelar</Button>
                        <Button type="submit" className="flex-1 bg-black text-white hover:bg-gray-800" disabled={isLoading}>
                            {isLoading ? 'Calculando...' : (initialData ? 'Guardar Cambios' : 'Simular')}
                        </Button>
                    </div>
                </form>
            </div>
        </div>
    );
}
