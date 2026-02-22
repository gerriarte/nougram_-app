import React from 'react';
import { MonthProjection } from '@/types/break-even';

interface ProjectionChartProps {
    projection: MonthProjection[];
    target: number;
}

export function ProjectionChart({ projection, target }: ProjectionChartProps) {
    const maxVal = Math.max(target, ...projection.map(p => p.allocated_hours)) * 1.2;

    return (
        <div className="bg-white rounded-[24px] p-6 shadow-sm border border-gray-100 h-96 flex flex-col justify-end relative">
            <h3 className="absolute top-6 left-6 font-semibold text-gray-900">Trayectoria de Crecimiento</h3>

            <div className="flex h-64 items-end gap-2 w-full px-4 pb-4 border-b border-l border-gray-200 relative">

                {/* Break Even Line */}
                <div
                    className="absolute left-0 w-full border-t-2 border-dashed border-gray-400 z-10 flex items-center pointer-events-none"
                    style={{ bottom: `${(target / maxVal) * 100}%` }}
                >
                    <span className="bg-gray-100 text-gray-600 text-xs px-2 rounded ml-2">Meta: {target}h</span>
                </div>

                {projection.map((col, i) => {
                    const height = (col.allocated_hours / maxVal) * 100;
                    const isAbove = col.status === 'above_break_even';

                    return (
                        <div key={col.month} className="flex-1 flex flex-col justify-end group relative">
                            <div
                                className={`w-full rounded-t-sm transition-all duration-300 ${isAbove ? 'bg-green-400' : 'bg-blue-400'
                                    } opacity-80 group-hover:opacity-100`}
                                style={{ height: `${height}%` }}
                            ></div>

                            {/* Tooltip */}
                            <div className="absolute bottom-full mb-2 left-1/2 -translate-x-1/2 hidden group-hover:block bg-black text-white text-xs p-2 rounded z-20 whitespace-nowrap shadow-lg">
                                <div className="capitalize">{col.month}</div>
                                <div className="font-bold">{col.allocated_hours.toLocaleString('es-US', { minimumFractionDigits: 1, maximumFractionDigits: 1 })}h</div>
                            </div>
                        </div>
                    );
                })}
            </div>
            <div className="flex justify-between px-4 mt-2 text-xs text-gray-400">
                <span>{projection[0]?.month}</span>
                <span>{projection[projection.length - 1]?.month}</span>
            </div>
        </div>
    );
}
