'use client';

import React, { useState, useMemo } from 'react';
import { AdminLayout } from '@/components/admin/layout/AdminLayout';
import { useBreakEven } from '@/hooks/useBreakEven';
import { BreakEvenProjectionResponse } from '@/types/break-even';
import { ProjectionConfig } from '@/components/analytics/break-even/projection/ProjectionConfig';
import { ProjectionChart } from '@/components/analytics/break-even/projection/ProjectionChart';
import { ProjectionTable } from '@/components/analytics/break-even/projection/ProjectionTable';
import { BreakEvenNav } from '@/components/analytics/break-even/BreakEvenNav';
import { ArrowLeft } from 'lucide-react';
import Link from 'next/link';

export default function BreakEvenProjectionPage() {
    const { data: baseData, isLoading, error, generateProjection } = useBreakEven();

    const [months, setMonths] = useState(12);
    const [growthRate, setGrowthRate] = useState(0);
    const [projectionData, setProjectionData] = useState<BreakEvenProjectionResponse | null>(null);
    const [isProjecting, setIsProjecting] = useState(false);

    React.useEffect(() => {
        const updateProjection = async () => {
            if (baseData) {
                setIsProjecting(true);
                const result = await generateProjection(months, growthRate);
                setProjectionData(result);
                setIsProjecting(false);
            }
        };
        updateProjection();
    }, [baseData, months, growthRate, generateProjection]); // Add dependencies

    if (isLoading) {
        return (
            <AdminLayout>
                <div className="flex items-center justify-center h-64">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
                </div>
            </AdminLayout>
        );
    }

    if (error || !baseData) {
        return (
            <AdminLayout>
                <div className="p-8 text-center text-red-600">
                    <p>Error: {error || 'No se pudieron cargar los datos base.'}</p>
                </div>
            </AdminLayout>
        );
    }

    return (
        <AdminLayout>
            <div className="space-y-8 pb-20">
                {/* Header */}
                <BreakEvenNav />

                {/* Header */}
                <div className="flex flex-col gap-4">
                    <div className="flex justify-between items-end">
                        <div className="max-w-2xl">
                            <h1 className="text-2xl font-bold text-gray-900 mb-2">Proyección Temporal</h1>
                            <p className="text-gray-500">Proyecta cuándo alcanzarás el punto de equilibrio basado en tu ritmo actual y crecimiento estimado.</p>
                        </div>
                    </div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Config Side */}
                    <div className="lg:col-span-1">
                        <ProjectionConfig
                            months={months}
                            setMonths={setMonths}
                            growthRate={growthRate}
                            setGrowthRate={setGrowthRate}
                        />
                    </div>

                    {/* Chart Main */}
                    <div className="lg:col-span-2">
                        {isProjecting || !projectionData ? (
                            <div className="h-64 flex items-center justify-center border rounded-[24px]">
                                <span className="text-gray-400">Calculando proyección...</span>
                            </div>
                        ) : (
                            <ProjectionChart
                                projection={projectionData.projection}
                                target={baseData.break_even_hours}
                            />
                        )}
                    </div>
                </div>

                {/* Summary Box */}
                {projectionData && (
                    <div className="bg-blue-50/50 border border-blue-100 rounded-[24px] p-6 flex flex-col md:flex-row items-center justify-between gap-6">
                        <div>
                            <h3 className="text-blue-900 font-semibold text-lg mb-1">Resultados de Proyección</h3>
                            {projectionData.break_even_date ? (
                                <p className="text-blue-800">
                                    Alcanzarás el equilibrio el <span className="font-bold">{projectionData.break_even_date}</span>.
                                </p>
                            ) : (
                                <p className="text-yellow-700 font-medium">
                                    No se alcanza el equilibrio en el periodo seleccionado.
                                </p>
                            )}
                        </div>
                        <div className="flex gap-8 text-sm">
                            <div>
                                <span className="text-gray-500 block">Velocidad Actual</span>
                                <span className="font-semibold text-gray-900">{baseData.current_allocated_hours}h/mes</span>
                            </div>
                            <div>
                                <span className="text-gray-500 block">Crecimiento Simulado</span>
                                <span className="font-semibold text-gray-900">{growthRate}%/mes</span>
                            </div>
                        </div>
                    </div>
                )}

                {/* Table */}
                <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Detalle Mes a Mes</h3>
                    {projectionData && <ProjectionTable projection={projectionData.projection} />}
                </div>
            </div>
        </AdminLayout>
    );
}
