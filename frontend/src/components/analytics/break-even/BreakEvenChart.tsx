import React from 'react';
import { BreakEvenAnalysisResponse } from '@/types/break-even';

interface BreakEvenChartProps {
    data: BreakEvenAnalysisResponse;
}

export function BreakEvenChart({ data }: BreakEvenChartProps) {
    // Simple logic to set max scale
    const maxScale = Math.max(data.break_even_hours, data.current_allocated_hours, 500) * 1.2;

    // Percentages
    const breakEvenPercent = (data.break_even_hours / maxScale) * 100;
    const allocatedPercent = (data.current_allocated_hours / maxScale) * 100;

    return (
        <div className="bg-white rounded-[24px] p-8 shadow-sm border border-gray-100">
            <h3 className="text-lg font-semibold text-gray-800 mb-8">Visualización de Equilibrio</h3>

            <div className="relative h-64 border-l border-b border-gray-300">
                {/* Break Even Line */}
                <div
                    className="absolute left-0 w-full border-t-2 border-dashed border-gray-800 z-10 flex items-center"
                    style={{ bottom: `${breakEvenPercent}%` }}
                >
                    <span className="absolute right-0 -top-8 bg-gray-900 text-white text-xs px-2 py-1 rounded">
                        🎯 Equilibrio: {data.break_even_hours}h
                    </span>
                </div>

                {/* Bars Area */}
                <div className="absolute bottom-0 left-10 w-24 bg-blue-500/10 h-full flex items-end justify-center transition-all duration-500">
                    <div
                        className="w-16 bg-gradient-to-t from-blue-600 to-blue-400 rounded-t-lg shadow-lg relative group"
                        style={{ height: `${allocatedPercent}%` }}
                    >
                        <div className="absolute -top-8 left-1/2 -translate-x-1/2 bg-blue-100 text-blue-800 text-xs font-bold px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
                            Asignadas: {data.current_allocated_hours}h
                        </div>
                    </div>
                </div>
            </div>

            <div className="mt-4 flex gap-6 justify-center">
                <div className="flex items-center gap-2">
                    <div className="w-3 h-3 bg-blue-500 rounded-sm"></div>
                    <span className="text-sm text-gray-600">Horas Asignadas</span>
                </div>
                <div className="flex items-center gap-2">
                    <div className="w-3 h-3 border-t-2 border-dashed border-gray-800 h-0"></div>
                    <span className="text-sm text-gray-600">Meta de Equilibrio</span>
                </div>
            </div>
        </div>
    );
}
