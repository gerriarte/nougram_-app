import React from 'react';
import { ScenarioResult } from '@/types/break-even';

interface ScenarioComparisonChartProps {
    baseBreakEven: number;
    scenarios: ScenarioResult[];
}

export function ScenarioComparisonChart({ baseBreakEven, scenarios }: ScenarioComparisonChartProps) {
    // Find max value for scale
    const maxVal = Math.max(
        baseBreakEven,
        ...scenarios.map(s => s.break_even_hours)
    ) * 1.2;

    const getWidth = (val: number) => `${(val / maxVal) * 100}%`;

    return (
        <div className="bg-white rounded-[24px] p-8 shadow-sm border border-gray-100">
            <h3 className="text-lg font-semibold text-gray-900 mb-8">Comparación Visual</h3>

            <div className="space-y-6">
                {/* Base Scenario */}
                <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                        <span className="font-medium text-gray-900">Escenario Base</span>
                        <span className="font-bold text-gray-900">{baseBreakEven}h</span>
                    </div>
                    <div className="h-8 bg-gray-100 rounded-lg overflow-hidden relative">
                        <div
                            className="h-full bg-gray-300 rounded-lg flex items-center justify-end px-2 text-xs font-bold text-gray-700 transition-all duration-500"
                            style={{ width: getWidth(baseBreakEven) }}
                        >
                            Base
                        </div>
                    </div>
                </div>

                {/* Scenarios */}
                {scenarios.map(scenario => {
                    const isBetter = scenario.break_even_hours < baseBreakEven;
                    const colorClass = isBetter ? 'bg-green-500' : 'bg-red-500';

                    return (
                        <div key={scenario.id} className="space-y-2">
                            <div className="flex justify-between text-sm">
                                <span className="font-medium text-gray-700">{scenario.name}</span>
                                <span className={`font-bold ${isBetter ? 'text-green-600' : 'text-red-600'}`}>
                                    {scenario.break_even_hours}h
                                </span>
                            </div>
                            <div className="h-8 bg-gray-100 rounded-lg overflow-hidden relative">
                                <div
                                    className={`h-full ${colorClass} rounded-lg flex items-center justify-end px-2 text-xs font-bold text-white transition-all duration-500 opacity-90`}
                                    style={{ width: getWidth(scenario.break_even_hours) }}
                                >
                                    {scenario.impact.hours_change > 0 ? '+' : ''}{scenario.impact.hours_change}h
                                </div>

                                {/* Reference Line for Base */}
                                <div
                                    className="absolute top-0 bottom-0 border-l-2 border-dashed border-black/20 z-10"
                                    style={{ left: getWidth(baseBreakEven) }}
                                ></div>
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}
