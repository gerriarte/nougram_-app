
'use client';

import React from 'react';
import { useAdmin } from '@/context/AdminContext';
import { Card, CardContent } from '@/components/ui/Card';

export function OverheadSummary() {
    const { bcr, fixedCosts } = useAdmin();

    // Group costs by type (Software vs Overhead/Other)
    const softwareCosts = fixedCosts
        .filter(c => c.isActive && (c.category === 'Software' || c.category === 'Tools'))
        .reduce((sum, c) => sum + c.amountMonthly, 0);

    const overheadCosts = fixedCosts
        .filter(c => c.isActive && c.category !== 'Software' && c.category !== 'Tools')
        .reduce((sum, c) => sum + c.amountMonthly, 0);

    return (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
            <Card className="bg-white border-blue-100 shadow-sm">
                <CardContent className="p-6">
                    <p className="text-sm font-medium text-gray-500 uppercase">Total Gastos Fijos</p>
                    <p className="text-3xl font-bold text-gray-900 mt-2">
                        ${bcr.totalFixedCosts.toLocaleString()}
                    </p>
                    <p className="text-xs text-gray-400 mt-1">Mensual</p>
                </CardContent>
            </Card>

            <Card className="bg-white border-gray-100 shadow-sm">
                <CardContent className="p-6">
                    <p className="text-sm font-medium text-gray-500 uppercase">Overhead Operacional</p>
                    <p className="text-2xl font-bold text-gray-700 mt-2">
                        ${overheadCosts.toLocaleString()}
                    </p>
                    <p className="text-xs text-gray-400 mt-1">Oficina, Arriendo, Servicios</p>
                </CardContent>
            </Card>

            <Card className="bg-white border-gray-100 shadow-sm">
                <CardContent className="p-6">
                    <p className="text-sm font-medium text-gray-500 uppercase">Herramientas & Software</p>
                    <p className="text-2xl font-bold text-gray-700 mt-2">
                        ${softwareCosts.toLocaleString()}
                    </p>
                    <p className="text-xs text-gray-400 mt-1">Licencias, SaaS</p>
                </CardContent>
            </Card>
        </div>
    );
}
