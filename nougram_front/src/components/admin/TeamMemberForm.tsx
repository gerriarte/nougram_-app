import * as React from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/Dialog"; // We need to create Dialog or use a simple modal
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Label } from "@/components/ui/Label";
import { TeamMemberInput } from "@/types/admin";

interface TeamMemberFormProps {
    initialData?: TeamMemberInput;
    onSubmit: (data: TeamMemberInput) => void;
    onCancel: () => void;
}

const DEFAULT_MEMBER: TeamMemberInput = {
    name: "",
    role: "",
    is_active: true,
    salary_monthly_brute: "",
    currency: "COP",
    billable_hours_per_week: 32,
    non_billable_hours_percentage: "0.0"
};

export function TeamMemberForm({ initialData, onSubmit, onCancel }: TeamMemberFormProps) {
    const [formData, setFormData] = React.useState<TeamMemberInput>(initialData || DEFAULT_MEMBER);

    const handleChange = (field: keyof TeamMemberInput, value: TeamMemberInput[keyof TeamMemberInput]) => {
        setFormData(prev => ({ ...prev, [field]: value }));
    };

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        onSubmit(formData);
    };

    return (
        <Dialog open={true} onOpenChange={(open) => { if (!open) onCancel(); }}>
            <DialogContent className="max-w-lg p-0 overflow-hidden">
                <DialogHeader className="px-6 py-4 border-b border-gray-100">
                    <DialogTitle>
                        {initialData ? "Editar Miembro" : "Agregar Nuevo Miembro"}
                    </DialogTitle>
                </DialogHeader>
                <form onSubmit={handleSubmit} className="p-6 space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                            <Label htmlFor="name">Nombre</Label>
                            <Input
                                id="name"
                                required
                                value={formData.name}
                                onChange={e => handleChange("name", e.target.value)}
                                placeholder="Ej: Juan Pérez"
                            />
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="role">Rol</Label>
                            <Input
                                id="role"
                                required
                                value={formData.role}
                                onChange={e => handleChange("role", e.target.value)}
                                placeholder="Ej: Senior Dev"
                            />
                        </div>
                    </div>

                    <div className="space-y-2">
                        <Label htmlFor="salary">Salario Mensual Bruto</Label>
                        <div className="flex gap-2">
                            <Input
                                id="salary"
                                required
                                isCurrency
                                value={formData.salary_monthly_brute}
                                onChange={e => handleChange("salary_monthly_brute", e.target.value)}
                                className="flex-1"
                            />
                            <select
                                className="w-24 rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                                value={formData.currency}
                                onChange={e => handleChange("currency", e.target.value)}
                            >
                                <option value="COP">COP</option>
                                <option value="USD">USD</option>
                            </select>
                        </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                            <Label htmlFor="hours">Horas Facturables/Sem</Label>
                            <Input
                                id="hours"
                                type="number"
                                min="0"
                                max="80"
                                value={formData.billable_hours_per_week}
                                onChange={e => handleChange("billable_hours_per_week", parseFloat(e.target.value))}
                            />
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="nonBillable">% No Facturable (0-1)</Label>
                            <Input
                                id="nonBillable"
                                type="number"
                                step="0.01"
                                min="0"
                                max="1"
                                value={formData.non_billable_hours_percentage}
                                onChange={e => handleChange("non_billable_hours_percentage", e.target.value)}
                            />
                        </div>
                    </div>

                    <DialogFooter className="pt-4">
                        <Button type="button" variant="secondary" onClick={onCancel}>Cancelar</Button>
                        <Button type="submit">Guardar Miembro</Button>
                    </DialogFooter>
                </form>
            </DialogContent>
        </Dialog>
    );
}
