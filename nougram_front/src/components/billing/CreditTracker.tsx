
import React from 'react';
import { CreditUsage, CreditTransaction } from '@/types/billing';
import { Card, CardContent } from '@/components/ui/Card';
import { Zap, ArrowRight, BatteryCharging, TrendingUp } from 'lucide-react';
import { Button } from '@/components/ui/Button';

// Mock Recent Activity
const DEFAULT_ACTIVITY: CreditTransaction[] = [
    { id: '1', action: 'Generación de propuesta estratégica', credits: -5, timestamp: 'Hace 2 horas' },
    { id: '2', action: 'Análisis financiero con IA', credits: -3, timestamp: 'Ayer' },
    { id: '3', action: 'Sugerencias de onboarding', credits: -2, timestamp: 'Hace 3 días' },
];

interface CreditTrackerProps {
    usage: CreditUsage;
    recentActivity?: CreditTransaction[];
    onUpgrade?: () => void;
    onTopUp?: () => void;
}

export function CreditTracker({
    usage,
    recentActivity = DEFAULT_ACTIVITY,
    onUpgrade,
    onTopUp
}: CreditTrackerProps) {
    // Percentage Calculation
    const limit = usage.limitMonthly || 100;
    const percentage = Math.min((usage.usedThisMonth / limit) * 100, 100);
    const isUnlimited = usage.limitMonthly === null;

    // Apple Style Colors
    let color = 'text-[#34C759]'; // Apple Green
    let pathColor = 'stroke-[#34C759]';
    let bgColor = 'bg-[#34C759]';
    let gradientStart = '#34C759';
    let gradientEnd = '#30B34E';

    if (percentage > 90) {
        color = 'text-[#FF3B30]'; // Apple Red
        pathColor = 'stroke-[#FF3B30]';
        bgColor = 'bg-[#FF3B30]';
        gradientStart = '#FF3B30';
        gradientEnd = '#E02B1F';
    } else if (percentage > 70) {
        color = 'text-[#FF9500]'; // Apple Orange
        pathColor = 'stroke-[#FF9500]';
        bgColor = 'bg-[#FF9500]';
        gradientStart = '#FF9500';
        gradientEnd = '#DD8200';
    }

    // Circular Progress SVG Props - Thinner Stroke for Apple look
    const radius = 58;
    const circumference = 2 * Math.PI * radius;
    const offset = circumference - (percentage / 100) * circumference;

    return (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* 1. Main Usage Meter Card */}
            <div className="lg:col-span-1 rounded-[28px] bg-white shadow-[0_8px_30px_rgba(0,0,0,0.04)] border border-gray-100 p-8 flex flex-col justify-between relative overflow-hidden group hover:shadow-[0_20px_40px_rgba(0,0,0,0.06)] transition-all duration-500">
                {/* Background Blur Effect */}
                <div className="absolute -top-20 -right-20 w-64 h-64 bg-gray-50 rounded-full blur-3xl opacity-50 group-hover:opacity-80 transition-opacity" />

                <div className="flex items-center gap-3 relative z-10">
                    <div className={`p-2 rounded-full ${percentage > 90 ? 'bg-red-50 text-[#FF3B30]' : 'bg-blue-50 text-[#2997FF]'}`}>
                        <Zap size={20} strokeWidth={2.5} />
                    </div>
                    <div>
                        <h3 className="text-base font-semibold text-[#1D1D1F]">Créditos de IA</h3>
                        <p className="text-xs text-[#86868B] font-medium">Ciclo mensual</p>
                    </div>
                </div>

                <div className="flex flex-col items-center justify-center py-8 relative z-10">
                    {isUnlimited ? (
                        <div className="flex flex-col items-center gap-4">
                            <span className="text-6xl font-thin text-[#2997FF]">∞</span>
                            <p className="text-sm font-medium text-[#86868B]">Plan Ilimitado</p>
                        </div>
                    ) : (
                        <div className="relative h-60 w-60 flex items-center justify-center">
                            {/* SVG Circle */}
                            <svg className="h-full w-full transform -rotate-90 drop-shadow-sm" viewBox="0 0 140 140">
                                <circle
                                    className="text-gray-100 stroke-current"
                                    strokeWidth="6"
                                    fill="transparent"
                                    strokeLinecap="round"
                                    r={radius}
                                    cx="70"
                                    cy="70"
                                />
                                <circle
                                    className={`${pathColor} transition-all duration-1000 ease-[cubic-bezier(0.25,0.1,0.25,1.0)]`}
                                    strokeWidth="6"
                                    strokeDasharray={circumference}
                                    strokeDashoffset={offset}
                                    strokeLinecap="round"
                                    fill="transparent"
                                    r={radius}
                                    cx="70"
                                    cy="70"
                                />
                            </svg>

                            {/* Centered Text */}
                            <div className="absolute flex flex-col items-center scale-up-center animate-in zoom-in duration-500">
                                <span className="text-5xl font-semibold tracking-tighter text-[#1D1D1F]">
                                    {usage.usedThisMonth}
                                </span>
                                <span className="text-sm font-medium text-[#86868B] mt-1">de {limit}</span>
                            </div>
                        </div>
                    )}
                </div>

                {!isUnlimited && (
                    <div className="relative z-10">
                        <div className="flex justify-between items-center mb-2">
                            <span className="text-[13px] font-medium text-[#86868B]">{percentage.toFixed(0)}% Utilizado</span>
                            <span className="text-[13px] font-semibold text-[#1D1D1F]">{usage.available} disponibles</span>
                        </div>
                        <div className="w-full bg-gray-100 rounded-full h-1.5 overflow-hidden">
                            <div
                                className={`h-full rounded-full transition-all duration-1000 ${bgColor}`}
                                style={{ width: `${percentage}%` }}
                            />
                        </div>
                    </div>
                )}
            </div>

            {/* 2. Detailed Summary & Activity */}
            <div className="lg:col-span-2 flex flex-col gap-8">

                {/* Stats Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="rounded-[24px] bg-white p-6 shadow-[0_4px_20px_rgba(0,0,0,0.03)] border border-gray-100 flex items-start justify-between">
                        <div>
                            <p className="text-[13px] font-semibold text-[#86868B] uppercase tracking-wide">Recarga Automática</p>
                            <h4 className="text-2xl font-semibold text-[#1D1D1F] mt-2">{new Date(usage.nextResetDate).toLocaleDateString()}</h4>
                            <p className="text-xs text-[#86868B] mt-1">Tu cuota se reinicia este día</p>
                        </div>
                        <div className="p-3 bg-gray-50 rounded-full text-[#86868B]">
                            <BatteryCharging size={24} strokeWidth={1.5} />
                        </div>
                    </div>

                    <div className="rounded-[24px] bg-white p-6 shadow-[0_4px_20px_rgba(0,0,0,0.03)] border border-gray-100 flex items-start justify-between">
                        <div>
                            <p className="text-[13px] font-semibold text-[#86868B] uppercase tracking-wide">Consumo Total</p>
                            <h4 className="text-2xl font-semibold text-[#1D1D1F] mt-2">{usage.usedTotal}</h4>
                            <p className="text-xs text-[#86868B] mt-1">Créditos usados históricamente</p>
                        </div>
                        <div className="p-3 bg-gray-50 rounded-full text-[#86868B]">
                            <TrendingUp size={24} strokeWidth={1.5} />
                        </div>
                    </div>
                </div>

                {/* Activity List */}
                <div className="rounded-[28px] bg-white shadow-[0_8px_30px_rgba(0,0,0,0.04)] border border-gray-100 overflow-hidden flex-1">
                    <div className="p-6 border-b border-gray-50 flex items-center justify-between">
                        <h3 className="text-lg font-semibold text-[#1D1D1F]">Actividad Reciente</h3>
                        <Button variant="ghost" size="sm" className="text-[#0071E3] hover:bg-blue-50 hover:text-[#0077ED] text-[13px] font-medium px-4 rounded-full h-8">
                            Ver todo
                        </Button>
                    </div>

                    <div className="p-2">
                        {recentActivity.map((activity) => (
                            <div key={activity.id} className="p-4 rounded-2xl hover:bg-[#F5F5F7] transition-colors flex items-center justify-between group">
                                <div className="flex items-center gap-4">
                                    <div className="h-10 w-10 rounded-full bg-blue-50 text-[#0071E3] flex items-center justify-center group-hover:bg-white group-hover:shadow-sm transition-all">
                                        <Zap size={18} fill="currentColor" className="opacity-80" />
                                    </div>
                                    <div>
                                        <p className="text-[15px] font-medium text-[#1D1D1F]">{activity.action}</p>
                                        <p className="text-[13px] text-[#86868B] mt-0.5">{activity.timestamp}</p>
                                    </div>
                                </div>
                                <span className={`text-[14px] font-semibold px-3 py-1 rounded-full ${activity.credits < 0 ? 'bg-gray-100 text-[#1D1D1F]' : 'bg-green-100 text-[#34C759]'}`}>
                                    {activity.credits}
                                </span>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Alert/Upgrade CTA */}
                {!isUnlimited && percentage > 70 && (
                    <div className="rounded-[24px] bg-[#F5F5F7] p-6 flex flex-col sm:flex-row items-center justify-between gap-6 border border-gray-200">
                        <div className="flex items-center gap-4">
                            <div className={`p-3 rounded-full ${color === 'text-[#FF3B30]' ? 'bg-[#FF3B30] text-white' : 'bg-[#FF9500] text-white'}`}>
                                <Zap size={20} fill="currentColor" />
                            </div>
                            <div>
                                <h4 className="text-[15px] font-semibold text-[#1D1D1F]">Considera actualizar tu plan</h4>
                                <p className="text-[13px] text-[#86868B] max-w-sm">Te quedan pocos créditos. Evita interrupciones actualizando a un plan superior.</p>
                            </div>
                        </div>
                        <Button onClick={onUpgrade} className="bg-[#1D1D1F] hover:bg-black text-white rounded-full px-6 h-10 text-[13px] font-medium whitespace-nowrap shadow-lg shadow-gray-200">
                            Ver Planes
                        </Button>
                    </div>
                )}
            </div>
        </div>
    );
}
