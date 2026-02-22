import React from 'react';
import { BreakEvenAnalysisResponse } from '@/types/break-even';

interface BreakEvenMetricsProps {
    data: BreakEvenAnalysisResponse;
}

export function BreakEvenMetrics({ data }: BreakEvenMetricsProps) {

    // Format Currency
    const formatCurrency = (amount: number) => {
        return new Intl.NumberFormat('en-US', { style: 'currency', currency: data.currency, maximumFractionDigits: 0 }).format(amount);
    };

    return (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* 1. Hours Card */}
            <div className="bg-white rounded-[24px] p-6 shadow-sm border border-gray-100 flex flex-col justify-between">
                <div>
                    <h3 className="text-gray-500 text-sm font-medium mb-4">Horas</h3>

                    <div className="space-y-4">
                        <div>
                            <span className="text-xs text-gray-400 uppercase tracking-wide">Punto de Equilibrio</span>
                            <div className="text-2xl font-semibold text-gray-900">{data.break_even_hours}h</div>
                        </div>
                        <div>
                            <span className="text-xs text-gray-400 uppercase tracking-wide">Asignadas Actuales</span>
                            <div className="text-xl font-medium text-gray-700">{data.current_allocated_hours}h</div>
                        </div>
                    </div>
                </div>

                <div className="mt-6 pt-4 border-t border-gray-50">
                    <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-500">Faltan</span>
                        <span className={`text-sm font-bold px-2 py-1 rounded-full ${data.hours_to_break_even > 0 ? 'bg-yellow-100 text-yellow-700' : 'bg-green-100 text-green-700'
                            }`}>
                            {data.hours_to_break_even > 0 ? `${data.hours_to_break_even.toFixed(1)}h` : 'Meta Alcanzada'}
                        </span>
                    </div>
                </div>
            </div>

            {/* 2. Revenue Card */}
            <div className="bg-white rounded-[24px] p-6 shadow-sm border border-gray-100 flex flex-col justify-between">
                <div>
                    <h3 className="text-gray-500 text-sm font-medium mb-4">Ingresos</h3>

                    <div className="space-y-4">
                        <div>
                            <span className="text-xs text-gray-400 uppercase tracking-wide">Punto de Equilibrio</span>
                            <div className="text-2xl font-semibold text-gray-900">{formatCurrency(data.break_even_revenue)}</div>
                        </div>
                        <div>
                            <span className="text-xs text-gray-400 uppercase tracking-wide">Proyectados</span>
                            <div className="text-xl font-medium text-gray-700">{formatCurrency(data.current_projected_revenue)}</div>
                        </div>
                    </div>
                </div>

                <div className="mt-6 pt-4 border-t border-gray-50">
                    <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-500">Faltan</span>
                        <span className={`text-sm font-bold px-2 py-1 rounded-full ${data.revenue_to_break_even > 0 ? 'bg-yellow-100 text-yellow-700' : 'bg-green-100 text-green-700'
                            }`}>
                            {data.revenue_to_break_even > 0 ? formatCurrency(data.revenue_to_break_even) : 'Meta Alcanzada'}
                        </span>
                    </div>
                </div>
            </div>

            {/* 3. Utilization Card */}
            <div className="bg-white rounded-[24px] p-6 shadow-sm border border-gray-100 flex flex-col justify-between">
                <div>
                    <h3 className="text-gray-500 text-sm font-medium mb-4">Utilización</h3>

                    <div className="space-y-4">
                        <div>
                            <span className="text-xs text-gray-400 uppercase tracking-wide">Actual</span>
                            <div className="text-2xl font-semibold text-gray-900">{data.current_utilization_rate}%</div>
                        </div>
                        <div>
                            <span className="text-xs text-gray-400 uppercase tracking-wide">Necesaria para Equilibrio</span>
                            <div className="text-xl font-medium text-gray-700">{data.break_even_utilization_rate}%</div>
                        </div>
                    </div>
                </div>

                <div className="mt-6 pt-4 border-t border-gray-50">
                    <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-500">Diferencia</span>
                        <span className={`text-sm font-bold px-2 py-1 rounded-full ${data.current_utilization_rate < data.break_even_utilization_rate ? 'bg-yellow-100 text-yellow-700' : 'bg-green-100 text-green-700'
                            }`}>
                            {(data.current_utilization_rate - data.break_even_utilization_rate).toFixed(1)}%
                        </span>
                    </div>
                </div>
            </div>
        </div>
    );
}
