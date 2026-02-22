
'use client';

import React from 'react';
import { Card } from '@/components/ui/Card';
import { TrendingUp, TrendingDown, DollarSign, PieChart, Activity, AlertCircle, ChevronRight } from 'lucide-react';
import { motion } from 'framer-motion';
import type { PipelineMetrics } from '@/hooks/useQuotePipeline';
import type { Quote } from '@/components/dashboard/QuoteCard';

interface KPIWidgetsProps {
    metrics: PipelineMetrics;
}

export function KPIWidgets({ metrics }: KPIWidgetsProps) {
    type KpiCard = {
        title: string;
        value: string;
        icon: React.ComponentType<{ size?: number; strokeWidth?: number }>;
        color: string;
        bg: string;
        trend?: 'up' | 'down';
        change?: string;
        subtitle?: string;
        status?: string;
    };

    const cards: KpiCard[] = [
        {
            title: 'Total Cotizado',
            value: `$${Math.round(metrics.totalQuoted).toLocaleString()}`,
            trend: 'up',
            icon: DollarSign,
            color: 'text-blue-500',
            bg: 'bg-blue-50/50'
        },
        {
            title: 'Pipeline Value',
            value: `$${Math.round(metrics.pipelineValue).toLocaleString()}`,
            subtitle: `${metrics.sentCount} activas`,
            icon: Activity,
            color: 'text-purple-500',
            bg: 'bg-purple-50/50'
        },
        {
            title: 'Win Rate',
            value: `${metrics.winRate.toFixed(1)}%`,
            trend: 'up',
            icon: PieChart,
            color: 'text-green-500',
            bg: 'bg-green-50/50'
        },
        {
            title: 'Margen Promedio',
            value: `${metrics.avgMargin.toFixed(1)}%`,
            status: metrics.avgMargin >= 20 ? 'Saludable' : 'Revisar',
            icon: TrendingUp,
            color: 'text-orange-500',
            bg: 'bg-orange-50/50'
        }
    ];

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {cards.map((metric, index) => (
                <motion.div
                    key={index}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.1 }}
                >
                    <Card className="p-5 hover:shadow-[0_20px_40px_rgba(0,0,0,0.08)] transition-all duration-500 group h-full">
                        <div className="flex justify-between items-start mb-4">
                            <div className={`w-10 h-10 rounded-[14px] flex items-center justify-center ${metric.bg} ${metric.color} group-hover:scale-110 transition-transform duration-500`}>
                                <metric.icon size={20} strokeWidth={1.5} />
                            </div>
                            {metric.change && (
                                <span className={`text-[10px] font-black px-3 py-1.5 rounded-full uppercase tracking-wider ${metric.trend === 'up' ? 'bg-green-50 text-green-600 border border-green-100/50' : 'bg-red-50 text-red-600 border border-red-100/50'}`}>
                                    {metric.change}
                                </span>
                            )}
                            {metric.status && (
                                <span className="text-[10px] font-black px-3 py-1.5 rounded-full bg-green-50 text-green-600 border border-green-100/50 uppercase tracking-wider">
                                    {metric.status}
                                </span>
                            )}
                        </div>

                        <div>
                            <p className="text-[10px] font-black text-system-gray uppercase tracking-[0.2em] mb-2">{metric.title}</p>
                            <h3 className="text-3xl font-bold text-gray-900 tracking-tight">{metric.value}</h3>
                            {metric.subtitle && (
                                <p className="text-sm text-system-gray mt-2 font-medium flex items-center gap-1.5">
                                    <span className="w-1.5 h-1.5 rounded-full bg-purple-400" />
                                    {metric.subtitle}
                                </p>
                            )}
                        </div>
                    </Card>
                </motion.div>
            ))}
        </div>
    );
}

type AlertType = 'critical' | 'warning' | 'info';
type PipelineAlert = {
    id: string;
    type: AlertType;
    text: string;
    action: string;
};

interface AlertsWidgetProps {
    quotes: Quote[];
}

export function AlertsWidget({ quotes }: AlertsWidgetProps) {
    const criticalMarginCount = quotes.filter((q) => q.margin < 15 && q.status !== 'accepted').length;
    const viewedNoDecisionCount = quotes.filter((q) => q.status === 'viewed').length;
    const draftCount = quotes.filter((q) => q.status === 'draft').length;

    const alerts: PipelineAlert[] = [];
    if (criticalMarginCount > 0) {
        alerts.push({
            id: 'critical-margin',
            type: 'critical',
            text: `${criticalMarginCount} cotización${criticalMarginCount === 1 ? '' : 'es'} con rentabilidad crítica (<15%)`,
            action: 'Revisar'
        });
    }
    if (viewedNoDecisionCount > 0) {
        alerts.push({
            id: 'viewed-followup',
            type: 'warning',
            text: `${viewedNoDecisionCount} cotización${viewedNoDecisionCount === 1 ? '' : 'es'} vistas sin cierre`,
            action: 'Seguir'
        });
    }
    if (draftCount > 0) {
        alerts.push({
            id: 'draft-pending',
            type: 'info',
            text: `${draftCount} borrador${draftCount === 1 ? '' : 'es'} pendiente${draftCount === 1 ? '' : 's'} de envío`,
            action: 'Ver'
        });
    }

    return (
        <Card className="p-5 h-full">
            <div className="flex items-center justify-between mb-4">
                <div>
                    <h3 className="text-lg font-bold text-gray-900 tracking-tight">Atención Requerida</h3>
                    <p className="text-[10px] font-black text-system-gray uppercase tracking-widest mt-1">Acciones pendientes</p>
                </div>
                <span className="w-8 h-8 bg-red-50 text-red-600 text-xs font-black flex items-center justify-center rounded-xl border border-red-100/50">
                    {alerts.length}
                </span>
            </div>

            {alerts.length === 0 ? (
                <div className="text-sm text-gray-500 font-medium py-8 text-center">
                    Sin alertas por ahora. El pipeline se ve saludable.
                </div>
            ) : (
                <div className="space-y-4">
                    {alerts.map((alert) => (
                        <motion.div
                            whileHover={{ x: 4 }}
                            key={alert.id}
                            className="flex items-start gap-4 p-4 rounded-2xl hover:bg-gray-50/50 transition-all group cursor-pointer border border-transparent hover:border-gray-100/50"
                        >
                            <div className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 ${alert.type === 'critical' ? 'bg-red-50 text-red-500' :
                                alert.type === 'warning' ? 'bg-orange-50 text-orange-600' :
                                    'bg-blue-50 text-blue-500'
                                }`}>
                                <AlertCircle size={20} strokeWidth={1.5} />
                            </div>
                            <div className="flex-1 pt-0.5">
                                <p className="text-sm text-gray-700 font-bold leading-snug tracking-tight mb-1">{alert.text}</p>
                                <span className="text-[11px] font-black text-blue-600 uppercase tracking-widest flex items-center gap-1">
                                    {alert.action} <ChevronRight size={10} strokeWidth={3} />
                                </span>
                            </div>
                        </motion.div>
                    ))}
                </div>
            )}
        </Card>
    );
}
