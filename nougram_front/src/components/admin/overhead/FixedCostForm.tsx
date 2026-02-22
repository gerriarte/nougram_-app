
import React, { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/Dialog';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Label } from '@/components/ui/Label';
import { FixedCost, CostCategory } from '@/types/admin';

type FixedCostInput = Omit<FixedCost, 'id' | 'isActive'>;

interface FixedCostFormProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    initialData?: FixedCost;
    onSave: (data: FixedCostInput) => void;
}

const DEFAULT_FORM: FixedCostInput = {
    name: '',
    description: '',
    category: 'Overhead',
    amountMonthly: 0,
    currency: 'COP'
};

const CATEGORIES: CostCategory[] = [
    'Software', 'Overhead', 'Tools', 'Infrastructure', 'Office', 'Utilities', 'Rent', 'Other'
];

export function FixedCostForm({ open, onOpenChange, initialData, onSave }: FixedCostFormProps) {
    const [formData, setFormData] = useState<FixedCostInput>(DEFAULT_FORM);

    useEffect(() => {
        if (initialData) {
            const { id, isActive, ...rest } = initialData;
            setFormData(rest);
        } else {
            setFormData(DEFAULT_FORM);
        }
    }, [initialData, open]);

    const handleSave = () => {
        if (!formData.name || formData.amountMonthly <= 0) {
            alert('Por favor completa los campos requeridos.');
            return;
        }
        onSave(formData);
        onOpenChange(false);
    };

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="max-w-md">
                <DialogHeader>
                    <DialogTitle>
                        {initialData ? 'Editar Gasto Fijo' : 'Agregar Nuevo Gasto'}
                    </DialogTitle>
                </DialogHeader>

                <div className="space-y-4 py-4">
                    <div className="space-y-2">
                        <Label>Nombre del Gasto *</Label>
                        <Input
                            value={formData.name}
                            onChange={e => setFormData({ ...formData, name: e.target.value })}
                            placeholder="Ej: Internet Fibra Óptica"
                        />
                    </div>

                    <div className="space-y-2">
                        <Label>Categoría</Label>
                        <select
                            className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                            value={formData.category}
                            onChange={e => setFormData({ ...formData, category: e.target.value as CostCategory })}
                        >
                            {CATEGORIES.map(cat => (
                                <option key={cat} value={cat}>{cat}</option>
                            ))}
                        </select>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                            <Label>Costo Mensual *</Label>
                            <Input
                                type="number"
                                value={formData.amountMonthly || ''}
                                onChange={e => setFormData({ ...formData, amountMonthly: parseFloat(e.target.value) || 0 })}
                            />
                        </div>
                        <div className="space-y-2">
                            <Label>Moneda</Label>
                            <select
                                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                                value={formData.currency}
                                onChange={e => setFormData({ ...formData, currency: e.target.value as any })}
                            >
                                <option value="COP">COP</option>
                                <option value="USD">USD</option>
                            </select>
                        </div>
                    </div>

                    <div className="space-y-2">
                        <Label>Descripción (Opcional)</Label>
                        <Input
                            value={formData.description || ''}
                            onChange={e => setFormData({ ...formData, description: e.target.value })}
                            placeholder="Detalles adicionales..."
                        />
                    </div>
                </div>

                <DialogFooter>
                    <Button variant="secondary" onClick={() => onOpenChange(false)}>Cancelar</Button>
                    <Button onClick={handleSave}>Guardar Gasto</Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}
