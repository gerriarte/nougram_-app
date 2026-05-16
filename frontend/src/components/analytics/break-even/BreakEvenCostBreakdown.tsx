import React from 'react';
import { BreakEvenAnalysisResponse } from '@/types/break-even';

interface BreakEvenCostBreakdownProps {
    data: BreakEvenAnalysisResponse;
}

export function BreakEvenCostBreakdown({ data }: BreakEvenCostBreakdownProps) {
    const formatCurrency = (amount: number) => {
        return new Intl.NumberFormat('en-US', { style: 'currency', currency: data.currency, maximumFractionDigits: 0 }).format(amount);
    };

    return (
        <div className="bg-white rounded-[24px] p-6 shadow-sm border border-gray-100">
            <div className="flex justify-between items-center mb-6">
                <h3 className="text-lg font-semibold text-gray-800">Desglose de Costos</h3>
                <span className="text-sm text-gray-500 font-medium bg-gray-100 px-3 py-1 rounded-full">
                    Total: {formatCurrency(data.total_fixed_costs)}/mes
                </span>
            </div>

            <div className="space-y-6">
                {data.cost_breakdown.map((item, index) => (
                    <div key={index}>
                        <div className="flex justify-between text-sm mb-1">
                            <span className="font-medium text-gray-700">{item.category}</span>
                            <span className="text-gray-500">{formatCurrency(item.amount)} ({item.percentage}%)</span>
                        </div>
                        <div className="h-2 w-full bg-gray-100 rounded-full overflow-hidden">
                            <div
                                className={`h-full rounded-full ${item.color || 'bg-blue-500'}`}
                                style={{ width: `${item.percentage}%` }}
                            ></div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
