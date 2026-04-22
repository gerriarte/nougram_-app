
'use client';

import React from 'react';
import { useAdmin } from '@/context/AdminContext';
import { useNougram } from '@/context/NougramCoreContext';
import { formatCurrency } from '@/lib/utils';

function KpiCard({ label, value, sub }: { label: string; value: string; sub: string }) {
    return (
        <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
            <p className="text-[10px] font-semibold uppercase tracking-wider text-gray-400">{label}</p>
            <p className="text-[22px] font-bold text-gray-900 mt-1 tabular-nums">{value}</p>
            <p className="text-[11px] text-gray-400 mt-0.5">{sub}</p>
        </div>
    );
}

export function OverheadSummary() {
    const { bcr, fixedCosts } = useAdmin();
    const { state } = useNougram();
    const currency = state.identity.primaryCurrency || 'COP';

    const softwareCosts = fixedCosts
        .filter(c => c.isActive && (c.category === 'Software' || c.category === 'Tools'))
        .reduce((sum, c) => sum + c.amountMonthly, 0);

    const overheadCosts = fixedCosts
        .filter(c => c.isActive && c.category !== 'Software' && c.category !== 'Tools')
        .reduce((sum, c) => sum + c.amountMonthly, 0);

    return (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <KpiCard
                label="Total gastos fijos"
                value={formatCurrency(bcr.totalFixedCosts, currency)}
                sub="Mensual"
            />
            <KpiCard
                label="Gastos operacionales"
                value={formatCurrency(overheadCosts, currency)}
                sub="Oficina, arriendo, servicios"
            />
            <KpiCard
                label="Herramientas & software"
                value={formatCurrency(softwareCosts, currency)}
                sub="Licencias, SaaS"
            />
        </div>
    );
}
