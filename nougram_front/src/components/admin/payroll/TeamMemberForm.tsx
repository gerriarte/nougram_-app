
import React, { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/Dialog';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Label } from '@/components/ui/Label';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/Alert';
import { TeamMember } from '@/types/admin';
import { useNougram } from '@/context/NougramCoreContext';

export type TeamMemberFormSavePayload = Omit<TeamMember, 'id' | 'salaryWithCharges'>;

interface TeamMemberFormProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    initialData?: TeamMember;
    onSave: (data: TeamMemberFormSavePayload) => Promise<{ success: boolean; error?: string }>;
}

const DEFAULT_FORM: TeamMemberFormSavePayload = {
    name: '',
    role: '',
    salaryMonthlyBrute: 0,
    currency: 'COP',
    applySocialCharges: true,
    billableHoursPerWeek: 32,
    nonBillablePercentage: 0.2,
    vacationDaysPerYear: 15,
    isActive: true,
};

export function TeamMemberForm({ open, onOpenChange, initialData, onSave }: TeamMemberFormProps) {
    const { state } = useNougram();
    const primaryCurrency = state.identity.primaryCurrency || 'COP';
    const [formData, setFormData] = useState<TeamMemberFormSavePayload>(DEFAULT_FORM);
    const [saveError, setSaveError] = useState<string | null>(null);
    const [isSaving, setIsSaving] = useState(false);

    useEffect(() => {
        if (!open) return;
        setSaveError(null);
        if (initialData) {
            const { id: _id, salaryWithCharges: _salaryWithCharges, ...rest } = initialData;
            void _id;
            void _salaryWithCharges;
            setFormData({ ...rest, currency: primaryCurrency as TeamMemberFormSavePayload['currency'] });
        } else {
            setFormData({ ...DEFAULT_FORM, currency: primaryCurrency as TeamMemberFormSavePayload['currency'] });
        }
    }, [initialData, open, primaryCurrency]);

    const handleSave = async () => {
        if (!formData.name || !formData.role || formData.salaryMonthlyBrute <= 0) {
            alert('Por favor completa los campos requeridos correctamente.');
            return;
        }
        if (formData.billableHoursPerWeek < 0 || formData.billableHoursPerWeek > 80) {
            alert('Las horas facturables deben estar entre 0 y 80.');
            return;
        }
        setSaveError(null);
        setIsSaving(true);
        try {
            const payload: TeamMemberFormSavePayload = {
                ...formData,
                currency: primaryCurrency as TeamMemberFormSavePayload['currency'],
            };
            const result = await onSave(payload);
            if (!result.success) {
                setSaveError(result.error ?? 'No se pudo guardar el miembro.');
                return;
            }
            onOpenChange(false);
        } finally {
            setIsSaving(false);
        }
    };

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="max-w-xl">
                <DialogHeader>
                    <DialogTitle>
                        {initialData ? 'Editar Miembro del Equipo' : 'Agregar Nuevo Miembro'}
                    </DialogTitle>
                </DialogHeader>

                <div className="space-y-4 py-4">
                    {saveError && (
                        <Alert variant="critical">
                            <AlertTitle>Error al guardar</AlertTitle>
                            <AlertDescription>{saveError}</AlertDescription>
                        </Alert>
                    )}
                    <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                            <Label>Nombre Completo *</Label>
                            <Input
                                value={formData.name}
                                onChange={e => setFormData({ ...formData, name: e.target.value })}
                                placeholder="Ej: Diana Prince"
                            />
                        </div>
                        <div className="space-y-2">
                            <Label>Rol / Cargo *</Label>
                            <Input
                                value={formData.role}
                                onChange={e => setFormData({ ...formData, role: e.target.value })}
                                placeholder="Ej: Senior Designer"
                            />
                        </div>
                    </div>

                    <div className="flex items-center gap-2 rounded-lg border border-gray-200 bg-white px-3 py-2">
                        <input
                            type="checkbox"
                            id="member-active"
                            checked={formData.isActive}
                            onChange={e => setFormData({ ...formData, isActive: e.target.checked })}
                            className="h-4 w-4 rounded text-blue-600"
                        />
                        <Label htmlFor="member-active" className="font-normal cursor-pointer">Miembro activo</Label>
                    </div>

                    <div className="space-y-2 p-4 bg-gray-50 rounded-lg border">
                        <h4 className="font-medium text-sm text-gray-900 mb-3">Compensación</h4>
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label>Salario Mensual Bruto *</Label>
                                <Input
                                    type="number"
                                    value={formData.salaryMonthlyBrute || ''}
                                    onChange={e => setFormData({ ...formData, salaryMonthlyBrute: parseFloat(e.target.value) || 0 })}
                                />
                            </div>
                            <div className="space-y-2">
                                <Label>Moneda de operación</Label>
                                <Input value={primaryCurrency} disabled />
                                <p className="text-xs text-gray-500">
                                    Coincide con la moneda principal de la organización; el servidor la valida al guardar.
                                </p>
                            </div>
                        </div>
                        <div className="flex items-center gap-2 mt-3">
                            <input
                                type="checkbox"
                                id="charges"
                                checked={formData.applySocialCharges}
                                onChange={e => setFormData({ ...formData, applySocialCharges: e.target.checked })}
                                className="h-4 w-4 text-blue-600 rounded"
                            />
                            <Label htmlFor="charges" className="font-normal cursor-pointer">Aplicar cargas sociales automáticas</Label>
                        </div>
                    </div>

                    <div className="space-y-2">
                        <h4 className="font-medium text-sm text-gray-900 mb-3">Capacidad</h4>
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label>Horas Facturables / Semana</Label>
                                <Input
                                    type="number"
                                    value={formData.billableHoursPerWeek}
                                    onChange={e => setFormData({ ...formData, billableHoursPerWeek: parseFloat(e.target.value) || 0 })}
                                />
                                <p className="text-xs text-gray-500">Max 80 hrs</p>
                            </div>
                            <div className="space-y-2">
                                <Label>% No Facturable</Label>
                                <Input
                                    type="number"
                                    step="0.1"
                                    max="1.0"
                                    min="0"
                                    value={formData.nonBillablePercentage}
                                    onChange={e => setFormData({ ...formData, nonBillablePercentage: parseFloat(e.target.value) || 0 })}
                                />
                                <p className="text-xs text-gray-500">0.2 = 20% Admin</p>
                            </div>
                        </div>
                    </div>
                </div>

                <DialogFooter>
                    <Button variant="secondary" onClick={() => onOpenChange(false)} disabled={isSaving}>Cancelar</Button>
                    <Button onClick={() => void handleSave()} disabled={isSaving}>
                        {isSaving ? 'Guardando...' : 'Guardar Miembro'}
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}
