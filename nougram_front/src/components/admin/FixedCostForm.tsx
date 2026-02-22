import * as React from "react";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Label } from "@/components/ui/Label";
import { FixedCostInput } from "@/types/admin";

interface FixedCostFormProps {
    initialData?: FixedCostInput;
    onSubmit: (data: FixedCostInput) => void;
    onCancel: () => void;
}

const DEFAULT_COST: FixedCostInput = {
    name: "",
    category: "Overhead",
    amount_monthly: "",
    currency: "COP",
    description: ""
};

export function FixedCostForm({ initialData, onSubmit, onCancel }: FixedCostFormProps) {
    const [formData, setFormData] = React.useState<FixedCostInput>(initialData || DEFAULT_COST);

    const handleChange = (field: keyof FixedCostInput, value: any) => {
        setFormData(prev => ({ ...prev, [field]: value }));
    };

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        onSubmit(formData);
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
            <div className="bg-white rounded-lg shadow-xl w-full max-w-lg overflow-hidden animate-in fade-in zoom-in-95 duration-200">
                <div className="px-6 py-4 border-b border-gray-100 flex justify-between items-center">
                    <h2 className="text-lg font-semibold text-gray-900">
                        {initialData ? "Editar Gasto" : "Agregar Nuevo Gasto"}
                    </h2>
                    <button onClick={onCancel} className="text-gray-400 hover:text-gray-600">×</button>
                </div>

                <form onSubmit={handleSubmit} className="p-6 space-y-4">
                    <div className="space-y-2">
                        <Label htmlFor="name">Nombre del Gasto</Label>
                        <Input
                            id="name"
                            required
                            value={formData.name}
                            onChange={e => handleChange("name", e.target.value)}
                            placeholder="Ej: Alquiler Oficina"
                        />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                            <Label htmlFor="category">Categoría</Label>
                            <Input
                                id="category"
                                required
                                value={formData.category}
                                onChange={e => handleChange("category", e.target.value)}
                                placeholder="Overhead, Software, etc."
                            />
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="currency">Moneda</Label>
                            <select
                                id="currency"
                                className="flex h-10 w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                                value={formData.currency}
                                onChange={e => handleChange("currency", e.target.value)}
                            >
                                <option value="COP">COP</option>
                                <option value="USD">USD</option>
                            </select>
                        </div>
                    </div>

                    <div className="space-y-2">
                        <Label htmlFor="amount">Costo Mensual</Label>
                        <Input
                            id="amount"
                            required
                            isCurrency
                            value={formData.amount_monthly}
                            onChange={e => handleChange("amount_monthly", e.target.value)}
                        />
                    </div>

                    <div className="space-y-2">
                        <Label htmlFor="description">Descripción (Opcional)</Label>
                        <Input
                            id="description"
                            value={formData.description || ""}
                            onChange={e => handleChange("description", e.target.value)}
                        />
                    </div>

                    <div className="pt-4 flex justify-end gap-2">
                        <Button type="button" variant="secondary" onClick={onCancel}>Cancelar</Button>
                        <Button type="submit">Guardar Gasto</Button>
                    </div>
                </form>
            </div>
        </div>
    );
}
