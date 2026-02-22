import * as React from "react";
import { FixedCostDisplay } from "@/types/admin";
import { Button } from "@/components/ui/Button";
import { formatCurrency } from "@/lib/utils";
import { Edit2, Trash2, PlusCircle } from "lucide-react";

interface FixedCostListProps {
    costs: FixedCostDisplay[];
    onAdd: () => void;
    onEdit: (cost: FixedCostDisplay) => void;
    onDelete: (id: number) => void;
}

export function FixedCostList({ costs, onAdd, onEdit, onDelete }: FixedCostListProps) {

    if (costs.length === 0) {
        return (
            <div className="text-center py-12 bg-white rounded-lg border border-dashed border-gray-300">
                <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-orange-100">
                    <PlusCircle className="h-6 w-6 text-orange-600" />
                </div>
                <h3 className="mt-2 text-sm font-semibold text-gray-900">No hay gastos fijos configurados</h3>
                <p className="mt-1 text-sm text-gray-500">Agrega gastos como alquiler, software y servicios para completar el BCR.</p>
                <div className="mt-6">
                    <Button onClick={onAdd} variant="secondary">Agregar Gasto Fijo</Button>
                </div>
            </div>
        );
    }

    return (
        <div className="space-y-4">
            <div className="flex justify-between items-center">
                <h2 className="text-lg font-semibold text-gray-900">Gastos Fijos & Tools</h2>
                <Button onClick={onAdd} size="sm" className="gap-2">
                    <PlusCircle className="h-4 w-4" /> Agregar Gasto
                </Button>
            </div>

            <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
                <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                        <tr>
                            <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Nombre</th>
                            <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Categoría</th>
                            <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Monto Mensual</th>
                            <th scope="col" className="relative px-6 py-3"><span className="sr-only">Acciones</span></th>
                        </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                        {costs.map((cost) => (
                            <tr key={cost.id} className="hover:bg-gray-50 transition-colors">
                                <td className="px-6 py-4 whitespace-nowrap">
                                    <div className="text-sm font-medium text-gray-900">{cost.name}</div>
                                    {cost.description && <div className="text-xs text-gray-500">{cost.description}</div>}
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap">
                                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                                        {cost.category}
                                    </span>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-900">
                                    {formatCurrency(cost.amount_monthly_normalized)}
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                    <div className="flex justify-end gap-2">
                                        <button onClick={() => onEdit(cost)} className="text-blue-600 hover:text-blue-900 p-1">
                                            <Edit2 className="h-4 w-4" />
                                        </button>
                                        <button onClick={() => onDelete(cost.id)} className="text-red-400 hover:text-red-600 p-1">
                                            <Trash2 className="h-4 w-4" />
                                        </button>
                                    </div>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
