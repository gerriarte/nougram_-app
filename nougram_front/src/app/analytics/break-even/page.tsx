'use client';

import React from 'react';
import { AdminLayout } from '@/components/admin/layout/AdminLayout';
import { useBreakEven } from '@/hooks/useBreakEven';
import { BreakEvenStateCard } from '@/components/analytics/break-even/BreakEvenStateCard';
import { BreakEvenMetrics } from '@/components/analytics/break-even/BreakEvenMetrics';
import { BreakEvenChart } from '@/components/analytics/break-even/BreakEvenChart';
import { BreakEvenCostBreakdown } from '@/components/analytics/break-even/BreakEvenCostBreakdown';
import { Filter, Settings } from 'lucide-react';
import { Button } from '@/components/ui/Button';

import { BreakEvenNav } from '@/components/analytics/break-even/BreakEvenNav';

export default function BreakEvenDashboardPage() {
    const { data, isLoading, error } = useBreakEven();

    if (isLoading) {
        return (
            <AdminLayout>
                <div className="flex items-center justify-center h-64">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
                </div>
            </AdminLayout>
        );
    }

    if (error || !data) {
        return (
            <AdminLayout>
                <div className="p-8 text-center text-red-600">
                    <p>Error: {error || 'No se pudieron cargar los datos.'}</p>
                </div>
            </AdminLayout>
        );
    }

    return (
        <AdminLayout>
            <div className="space-y-8 pb-20">
                <BreakEvenNav />

                {/* Header */}
                <div className="flex justify-between items-center">
                    <div>
                        <h1 className="text-2xl font-bold text-gray-900">Punto de Equilibrio</h1>
                        <p className="text-gray-500">Analiza y proyecta la viabilidad financiera de tu operación.</p>
                    </div>
                    <div className="flex gap-3">
                        <Button variant="secondary" className="h-9">
                            <Filter size={16} className="mr-2" /> Filtros
                        </Button>
                        <Button variant="secondary" className="h-9 w-9 p-0">
                            <Settings size={18} />
                        </Button>
                    </div>
                </div>

                {/* 1. State Card (Main Status) */}
                <BreakEvenStateCard data={data} />

                {/* 2. Key Metrics */}
                <BreakEvenMetrics data={data} />

                {/* 3. Visualization & Cost Breakdown */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <BreakEvenChart data={data} />
                    <BreakEvenCostBreakdown data={data} />
                </div>
            </div>
        </AdminLayout>
    );
}
