
'use client';

import React, { useState, useMemo } from 'react';
import { Equipment } from '@/types/equipment';
import { equipmentService } from '@/services/equipmentService';
import { Button } from '@/components/ui/Button';
import { ChevronLeft, ChevronRight, Download } from 'lucide-react';

interface DepreciationScheduleTableProps {
    equipment: Equipment;
}

export function DepreciationScheduleTable({ equipment }: DepreciationScheduleTableProps) {
    const [page, setPage] = useState(1);
    const itemsPerPage = 12;

    // Generate full schedule
    const schedule = useMemo(() => {
        // We need a helper in service to generate array
        // For now, we'll generate it here based on service logic or call a (mocked) service method
        // In real app, service.getDepreciationSchedule(eq) returns array

        // Simulating generation matching the Requirements 4.1 & 4.2
        const rows = [];
        const { purchasePrice, salvageValue, usefulLifeMonths, purchaseDate, depreciationMethod, currency, exchangeRateAtPurchase } = equipment;

        let cost = purchasePrice;
        let salvage = salvageValue;

        if (currency !== 'COP' && exchangeRateAtPurchase) {
            cost = purchasePrice * exchangeRateAtPurchase;
            salvage = salvageValue * exchangeRateAtPurchase;
        }

        const depreciableBase = cost - salvage;
        const start = new Date(purchaseDate);

        let accumulated = 0;
        let currentBook = cost;

        for (let i = 1; i <= usefulLifeMonths; i++) {
            const date = new Date(start);
            date.setMonth(start.getMonth() + i);

            let monthlyDep = 0;

            if (depreciationMethod === 'straight_line') {
                monthlyDep = depreciableBase / usefulLifeMonths;
            } else {
                // Declining balance simplified for loop
                // In real app this comes from robust library
                const rate = (2 / usefulLifeMonths);
                monthlyDep = currentBook * rate;
                if (currentBook - monthlyDep < salvage) monthlyDep = currentBook - salvage;
            }

            // Cap final
            if (accumulated + monthlyDep > depreciableBase) monthlyDep = depreciableBase - accumulated;

            accumulated += monthlyDep;
            currentBook -= monthlyDep;

            rows.push({
                month: i,
                date: date.toISOString().split('T')[0],
                depreciation: monthlyDep,
                accumulated: accumulated,
                bookValue: currentBook,
                percentage: (accumulated / depreciableBase) * 100
            });

            if (currentBook <= salvage) break;
        }
        return rows;
    }, [equipment]);

    const totalPages = Math.ceil(schedule.length / itemsPerPage);
    const paginatedData = schedule.slice((page - 1) * itemsPerPage, page * itemsPerPage);

    return (
        <div className="space-y-4">
            <div className="flex justify-between items-center">
                <h4 className="text-sm font-bold text-gray-700 uppercase">Cronograma de Depreciación</h4>
                <div className="flex gap-2">
                    <Button variant="secondary" size="sm">
                        <Download size={14} className="mr-2" /> Exportar CSV
                    </Button>
                </div>
            </div>

            <div className="border rounded-lg overflow-hidden text-sm">
                <div className="overflow-x-auto">
                    <table className="w-full text-left">
                        <thead className="bg-gray-50 border-b">
                            <tr>
                                <th className="px-4 py-2 font-medium text-gray-600">Mes</th>
                                <th className="px-4 py-2 font-medium text-gray-600">Fecha</th>
                                <th className="px-4 py-2 font-medium text-gray-600 text-right">Depreciación</th>
                                <th className="px-4 py-2 font-medium text-gray-600 text-right">Acumulada</th>
                                <th className="px-4 py-2 font-medium text-gray-600 text-right">Valor en Libros</th>
                                <th className="px-4 py-2 font-medium text-gray-600 w-24">Progreso</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y">
                            {paginatedData.map((row) => (
                                <tr key={row.month} className="hover:bg-gray-50/50">
                                    <td className="px-4 py-2 text-gray-900">{row.month}</td>
                                    <td className="px-4 py-2 text-gray-500">{row.date}</td>
                                    <td className="px-4 py-2 text-right font-medium">${row.depreciation.toLocaleString(undefined, { maximumFractionDigits: 0 })}</td>
                                    <td className="px-4 py-2 text-right text-gray-500">${row.accumulated.toLocaleString(undefined, { maximumFractionDigits: 0 })}</td>
                                    <td className="px-4 py-2 text-right font-bold text-gray-900">${row.bookValue.toLocaleString(undefined, { maximumFractionDigits: 0 })}</td>
                                    <td className="px-4 py-2">
                                        <div className="h-1.5 w-full bg-gray-100 rounded-full overflow-hidden">
                                            <div
                                                className={`h-full ${row.percentage >= 100 ? 'bg-green-500' : 'bg-blue-500'}`}
                                                style={{ width: `${Math.min(row.percentage, 100)}%` }}
                                            />
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>

                {/* Pagination */}
                {totalPages > 1 && (
                    <div className="flex justify-between items-center p-2 bg-gray-50 border-t">
                        <span className="text-xs text-gray-500">Página {page} de {totalPages}</span>
                        <div className="flex gap-1">
                            <Button
                                variant="ghost" size="sm"
                                disabled={page === 1}
                                onClick={() => setPage(p => p - 1)}
                            >
                                <ChevronLeft size={16} />
                            </Button>
                            <Button
                                variant="ghost" size="sm"
                                disabled={page === totalPages}
                                onClick={() => setPage(p => p + 1)}
                            >
                                <ChevronRight size={16} />
                            </Button>
                        </div>
                    </div>
                )}
            </div>

            <div className="flex gap-4 p-4 bg-blue-50 rounded-lg text-xs text-blue-800">
                <div>
                    <span className="font-bold block">Base Depreciable</span>
                    ${(equipment.purchasePrice - equipment.salvageValue).toLocaleString()}
                </div>
                <div>
                    <span className="font-bold block">Depreciación Mensual Promedio</span>
                    ${(schedule.length > 0 ? schedule[0].depreciation : 0).toLocaleString(undefined, { maximumFractionDigits: 0 })} / mes
                </div>
            </div>
        </div>
    );
}
