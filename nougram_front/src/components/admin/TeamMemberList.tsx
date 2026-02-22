import * as React from "react";
import { TeamMemberDisplay } from "@/types/admin";
import { Button } from "@/components/ui/Button";
import { formatCurrency } from "@/lib/utils";
import { Edit2, Trash2, UserPlus, AlertTriangle } from "lucide-react";
import { Badge } from "@/components/ui/Badge";

interface TeamMemberListProps {
    members: TeamMemberDisplay[];
    onAdd: () => void;
    onEdit: (member: TeamMemberDisplay) => void;
    onDelete: (id: number) => void;
}

export function TeamMemberList({ members, onAdd, onEdit, onDelete }: TeamMemberListProps) {

    if (members.length === 0) {
        return (
            <div className="text-center py-12 bg-white rounded-lg border border-dashed border-gray-300">
                <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-blue-100">
                    <UserPlus className="h-6 w-6 text-blue-600" />
                </div>
                <h3 className="mt-2 text-sm font-semibold text-gray-900">No hay miembros del equipo</h3>
                <p className="mt-1 text-sm text-gray-500">Comienza agregando los miembros de tu equipo para calcular costos.</p>
                <div className="mt-6">
                    <Button onClick={onAdd}>Agregar Primer Miembro</Button>
                </div>
            </div>
        );
    }

    return (
        <div className="space-y-4">
            <div className="flex justify-between items-center">
                <h2 className="text-lg font-semibold text-gray-900">Miembros del Equipo</h2>
                <Button onClick={onAdd} size="sm" className="gap-2">
                    <UserPlus className="h-4 w-4" /> Agregar Miembro
                </Button>
            </div>

            <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
                <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                        <tr>
                            <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Nombre / Rol</th>
                            <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Salario (Con Cargas)</th>
                            <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Horas/Mes</th>
                            <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Costo Hora</th>
                            <th scope="col" className="relative px-6 py-3"><span className="sr-only">Acciones</span></th>
                        </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                        {members.map((member) => (
                            <tr key={member.id} className="hover:bg-gray-50 transition-colors">
                                <td className="px-6 py-4 whitespace-nowrap">
                                    <div className="flex items-center">
                                        <div className="flex-shrink-0 h-10 w-10 bg-gray-100 rounded-full flex items-center justify-center text-gray-500 font-bold">
                                            {member.name.charAt(0)}
                                        </div>
                                        <div className="ml-4">
                                            <div className="text-sm font-medium text-gray-900">{member.name}</div>
                                            <div className="text-sm text-gray-500">{member.role}</div>
                                        </div>
                                    </div>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-right">
                                    <div className="text-sm font-medium text-gray-900">{formatCurrency(member.salary_with_charges)}</div>
                                    <div className="text-xs text-gray-500">Base: {formatCurrency(member.salary_monthly_brute)}</div>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-right">
                                    <div className="text-sm text-gray-900">{member.billable_hours_per_month.toFixed(1)}</div>
                                    <div className="text-xs text-gray-400">Facturables</div>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-right">
                                    <div className="inline-flex items-center px-2.5 py-0.5 rounded-full text-sm font-medium bg-blue-50 text-blue-700">
                                        {formatCurrency(member.cost_per_hour)}
                                    </div>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                    <div className="flex justify-end gap-2">
                                        <button onClick={() => onEdit(member)} className="text-blue-600 hover:text-blue-900 p-1">
                                            <Edit2 className="h-4 w-4" />
                                        </button>
                                        <button onClick={() => onDelete(member.id)} className="text-red-400 hover:text-red-600 p-1">
                                            <Trash2 className="h-4 w-4" />
                                        </button>
                                    </div>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            <div className="flex items-center gap-2 p-4 bg-blue-50 text-blue-800 rounded-lg text-sm border border-blue-100">
                <AlertTriangle className="h-5 w-5 flex-shrink-0" />
                <p>
                    Recuerda: El costo por hora incluye el impacto de las cargas sociales configuradas.
                    Asegúrate de mantener actualizados los salarios.
                </p>
            </div>
        </div>
    );
}
