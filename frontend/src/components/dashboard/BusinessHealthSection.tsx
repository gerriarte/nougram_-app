'use client';

import React, { useEffect, useState } from 'react';
import { insightsService, BreakEven, ResourceUtilization } from '@/services/insightsService';

function formatMoney(value: number, currency: string): string {
    try {
        return new Intl.NumberFormat('es-CO', {
            style: 'currency', currency, maximumFractionDigits: 0,
        }).format(value || 0);
    } catch {
        return `${currency} ${Math.round(value || 0).toLocaleString()}`;
    }
}

const STATUS_STYLE: Record<BreakEven['status'], { label: string; color: string }> = {
    profit: { label: 'Rentable', color: 'text-green-600' },
    break_even: { label: 'En equilibrio', color: 'text-amber-600' },
    deficit: { label: 'En déficit', color: 'text-red-600' },
};

export function BusinessHealthSection() {
    const [breakEven, setBreakEven] = useState<BreakEven | null>(null);
    const [utilization, setUtilization] = useState<ResourceUtilization | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        let active = true;
        Promise.all([
            insightsService.getBreakEven(),
            insightsService.getResourceUtilization(),
        ]).then(([be, util]) => {
            if (!active) return;
            setBreakEven(be);
            setUtilization(util);
            setLoading(false);
        });
        return () => { active = false; };
    }, []);

    if (loading) {
        return <div className="text-system-gray">Cargando salud del negocio…</div>;
    }

    return (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {breakEven && (
                <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
                    <div className="flex items-center justify-between">
                        <h2 className="text-lg font-bold text-gray-900">Punto de equilibrio mensual</h2>
                        <span className={`text-sm font-bold ${STATUS_STYLE[breakEven.status].color}`}>
                            {STATUS_STYLE[breakEven.status].label}
                        </span>
                    </div>
                    <div className="mt-4 grid grid-cols-2 gap-4">
                        <Metric label="Costo a cubrir" value={formatMoney(breakEven.break_even_cost, breakEven.currency)} />
                        <Metric label="Ingreso comprometido" value={formatMoney(breakEven.committed_revenue, breakEven.currency)} />
                        <Metric label="MRR (recurrente)" value={formatMoney(breakEven.mrr, breakEven.currency)} />
                        <Metric label="One-time mensual" value={formatMoney(breakEven.one_time_monthly, breakEven.currency)} />
                    </div>
                    <div className="mt-4">
                        <div className="flex justify-between text-sm font-medium text-gray-600">
                            <span>Cobertura de costos</span>
                            <span>{Math.round((breakEven.coverage_percentage || 0) * 100)}%</span>
                        </div>
                        <div className="mt-1 h-3 w-full rounded-full bg-gray-100 overflow-hidden">
                            <div
                                className={breakEven.surplus_or_deficit >= 0 ? 'h-3 bg-green-500' : 'h-3 bg-red-500'}
                                style={{ width: `${Math.min(100, Math.round((breakEven.coverage_percentage || 0) * 100))}%` }}
                            />
                        </div>
                        <p className="mt-2 text-sm text-gray-600">
                            {breakEven.surplus_or_deficit >= 0 ? 'Superávit' : 'Déficit'}:{' '}
                            <span className="font-bold">{formatMoney(Math.abs(breakEven.surplus_or_deficit), breakEven.currency)}</span>
                        </p>
                    </div>
                </div>
            )}

            {utilization && (
                <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
                    <div className="flex items-center justify-between">
                        <h2 className="text-lg font-bold text-gray-900">Recursos asignados (proyectos ganados)</h2>
                        <span className="text-sm font-bold text-gray-700">
                            {Math.round(utilization.overall_utilization_percentage)}%
                        </span>
                    </div>
                    <div className="mt-4 space-y-3">
                        {utilization.members.length === 0 && (
                            <p className="text-system-gray text-sm">Aún no hay recursos asignados en proyectos aprobados.</p>
                        )}
                        {utilization.members.map((m) => (
                            <div key={m.team_member_id}>
                                <div className="flex justify-between text-sm">
                                    <span className="font-medium text-gray-800">{m.name}</span>
                                    <span className={m.over_allocated ? 'text-red-600 font-bold' : 'text-gray-600'}>
                                        {Math.round(m.allocated_hours)}h / {Math.round(m.capacity_hours)}h
                                        ({Math.round(m.utilization_percentage)}%)
                                    </span>
                                </div>
                                <div className="mt-1 h-2 w-full rounded-full bg-gray-100 overflow-hidden">
                                    <div
                                        className={m.over_allocated ? 'h-2 bg-red-500' : 'h-2 bg-blue-500'}
                                        style={{ width: `${Math.min(100, Math.round(m.utilization_percentage))}%` }}
                                    />
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}

function Metric({ label, value }: { label: string; value: string }) {
    return (
        <div>
            <p className="text-xs font-medium text-system-gray uppercase tracking-wide">{label}</p>
            <p className="text-xl font-bold text-gray-900 mt-1">{value}</p>
        </div>
    );
}
