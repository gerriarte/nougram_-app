import React from 'react';
import { MonthProjection } from '@/types/break-even';

interface ProjectionTableProps {
    projection: MonthProjection[];
}

export function ProjectionTable({ projection }: ProjectionTableProps) {
    return (
        <div className="bg-white rounded-[24px] overflow-hidden border border-gray-100 shadow-sm">
            <div className="overflow-x-auto">
                <table className="w-full text-sm text-left">
                    <thead className="bg-gray-50 text-gray-500 border-b border-gray-100">
                        <tr>
                            <th className="px-6 py-4 font-medium">Mes</th>
                            <th className="px-6 py-4 font-medium">Horas Asignadas</th>
                            <th className="px-6 py-4 font-medium">Equilibrio</th>
                            <th className="px-6 py-4 font-medium">Estado</th>
                            <th className="px-6 py-4 font-medium">Profit (Horas)</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-50">
                        {projection.map((row) => {
                            const isBelow = row.status === 'below_break_even';
                            const isAbove = row.status === 'above_break_even';

                            return (
                                <tr key={row.month} className="hover:bg-gray-50/50 transition-colors">
                                    <td className="px-6 py-4 font-medium text-gray-900">{row.month}</td>
                                    <td className="px-6 py-4 text-gray-700">{row.allocated_hours.toFixed(1)}h</td>
                                    <td className="px-6 py-4 text-gray-500">{row.break_even_hours}h</td>
                                    <td className="px-6 py-4">
                                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${isBelow ? 'bg-yellow-100 text-yellow-800' :
                                                isAbove ? 'bg-green-100 text-green-800' :
                                                    'bg-blue-100 text-blue-800'
                                            }`}>
                                            {isBelow ? 'Abajo' : isAbove ? 'Arriba' : 'Equilibrio'}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 font-medium text-green-600">
                                        {row.profit_hours ? `+${row.profit_hours.toFixed(1)}h` : '-'}
                                    </td>
                                </tr>
                            );
                        })}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
