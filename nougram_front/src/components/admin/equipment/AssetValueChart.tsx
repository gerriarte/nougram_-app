
'use client';

import React, { useMemo } from 'react';
import { Equipment } from '@/types/equipment';

interface AssetValueChartProps {
    equipment: Equipment;
}

export function AssetValueChart({ equipment }: AssetValueChartProps) {
    // Generate data points for the chart
    // We reuse logic or duplicate for "Visual" purpose vs "Tabular" purpose
    const dataPoints = useMemo(() => {
        const points = [];
        const { purchasePrice, salvageValue, usefulLifeMonths, currency, exchangeRateAtPurchase } = equipment;

        let cost = purchasePrice;
        let salvage = salvageValue;
        if (currency !== 'COP' && exchangeRateAtPurchase) {
            cost *= exchangeRateAtPurchase;
            salvage *= exchangeRateAtPurchase;
        }

        // Just 2 points for Straight Line (Start, End) + maybe current?
        // Actually for a nice chart we want a few points.
        points.push({ month: 0, value: cost });
        points.push({ month: usefulLifeMonths, value: salvage });

        return { points, cost, salvage, maxMonth: usefulLifeMonths };
    }, [equipment]);

    const height = 200;
    const width = 500;
    const padding = 30;

    // Scales
    const maxY = dataPoints.cost;
    const maxX = dataPoints.maxMonth;

    const getY = (val: number) => height - padding - ((val / maxY) * (height - 2 * padding));
    const getX = (month: number) => padding + ((month / maxX) * (width - 2 * padding));

    return (
        <div className="bg-white p-4 rounded-lg border border-gray-100 shadow-sm">
            <h4 className="text-sm font-bold text-gray-700 uppercase mb-4">Evolución del Valor del Activo</h4>

            <div className="relative w-full aspect-[5/2]">
                <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-full overflow-visible">
                    {/* Grid Lines */}
                    <line x1={padding} y1={height - padding} x2={width - padding} y2={height - padding} stroke="#e5e7eb" strokeWidth="1" />
                    <line x1={padding} y1={padding} x2={padding} y2={height - padding} stroke="#e5e7eb" strokeWidth="1" />

                    {/* Salvage Value Line (Dashed) */}
                    <line
                        x1={padding}
                        y1={getY(dataPoints.salvage)}
                        x2={width - padding}
                        y2={getY(dataPoints.salvage)}
                        stroke="#ef4444"
                        strokeWidth="1"
                        strokeDasharray="4 4"
                    />
                    <text x={width - padding + 5} y={getY(dataPoints.salvage)} className="text-[8px] fill-red-500" dominantBaseline="middle">
                        Salvamento (${dataPoints.salvage.toLocaleString()})
                    </text>

                    {/* Value Line */}
                    <path
                        d={`M ${getX(0)} ${getY(dataPoints.cost)} L ${getX(dataPoints.maxMonth)} ${getY(dataPoints.salvage)}`}
                        fill="none"
                        stroke="#3b82f6"
                        strokeWidth="2"
                    />

                    {/* Area under curve */}
                    <path
                        d={`M ${getX(0)} ${getY(dataPoints.cost)} L ${getX(dataPoints.maxMonth)} ${getY(dataPoints.salvage)} L ${getX(dataPoints.maxMonth)} ${height - padding} L ${getX(0)} ${height - padding} Z`}
                        fill="url(#blueGradient)"
                        opacity="0.2"
                    />

                    {/* Gradient Def */}
                    <defs>
                        <linearGradient id="blueGradient" x1="0" x2="0" y1="0" y2="1">
                            <stop offset="0%" stopColor="#3b82f6" />
                            <stop offset="100%" stopColor="#eff6ff" />
                        </linearGradient>
                    </defs>

                    {/* Start Point */}
                    <circle cx={getX(0)} cy={getY(dataPoints.cost)} r="4" fill="#3b82f6" />
                    <text x={getX(0)} y={getY(dataPoints.cost) - 10} className="text-[10px] font-bold fill-gray-500" textAnchor="start">
                        ${dataPoints.cost.toLocaleString()}
                    </text>

                    {/* End Point */}
                    <circle cx={getX(dataPoints.maxMonth)} cy={getY(dataPoints.salvage)} r="4" fill="#3b82f6" />
                </svg>
            </div>

            <div className="flex justify-between mt-2 text-xs text-gray-400">
                <span>Compra</span>
                <span>Fin Vida Útil ({dataPoints.maxMonth} meses)</span>
            </div>
        </div>
    );
}
