
'use client';

import React from 'react';
import { useQuoteBuilder } from '@/context/QuoteBuilderContext';
import { Card, CardContent } from '@/components/ui/Card';
import { User, Activity, AlertCircle, CheckCircle2, TrendingUp } from 'lucide-react';

interface TeamAvailabilityDashboardProps {
    membersOverride?: import('@/types/quote-builder').TeamMemberMock[];
    utilizationCalcOverride?: (memberId: number) => { capacity: number, used: number, percentage: number };
}

export function TeamAvailabilityDashboard({ membersOverride, utilizationCalcOverride }: TeamAvailabilityDashboardProps) {
    const context = useQuoteBuilder();

    const teamMembers = membersOverride || context.teamMembers;
    const getMemberUtilization = utilizationCalcOverride || context.getMemberUtilization;

    if (!teamMembers || teamMembers.length === 0) return null;

    return (
        <Card className="bg-gradient-to-br from-gray-50 to-white border border-gray-100 shadow-sm overflow-hidden">
            <CardContent className="p-5">
                <div className="flex items-center justify-between mb-6">
                    <div className="flex items-center gap-2.5">
                        <div className="p-2 bg-purple-100 rounded-xl text-purple-600">
                            <Activity size={18} />
                        </div>
                        <div>
                            <h3 className="text-sm font-extrabold text-gray-800 tracking-tight">Disponibilidad del Equipo</h3>
                            <p className="text-[10px] text-gray-400 font-medium">Capacidad operativa tiempo real</p>
                        </div>
                    </div>
                    <div className="flex items-center gap-4">
                        <div className="flex items-center gap-1.5 text-[10px] font-bold text-gray-500 uppercase tracking-wider">
                            <span className="w-2 h-2 rounded-full bg-green-500" /> Normal
                        </div>
                        <div className="flex items-center gap-1.5 text-[10px] font-bold text-gray-500 uppercase tracking-wider">
                            <span className="w-2 h-2 rounded-full bg-yellow-500" /> Alta
                        </div>
                        <div className="flex items-center gap-1.5 text-[10px] font-bold text-gray-500 uppercase tracking-wider">
                            <span className="w-2 h-2 rounded-full bg-red-500" /> Crítica
                        </div>
                    </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                    {teamMembers.map(member => {
                        const { used, capacity, percentage } = getMemberUtilization(member.id);
                        const isOver = percentage > 100;
                        const isHigh = percentage > 90 && percentage <= 100;

                        let statusColor = 'bg-green-500';
                        let statusText = 'text-green-600';
                        let statusBg = 'bg-green-50';
                        let Icon = CheckCircle2;

                        if (isOver) {
                            statusColor = 'bg-red-500';
                            statusText = 'text-red-600';
                            statusBg = 'bg-red-50';
                            Icon = AlertCircle;
                        } else if (isHigh) {
                            statusColor = 'bg-yellow-500';
                            statusText = 'text-yellow-600';
                            statusBg = 'bg-yellow-50';
                            Icon = TrendingUp;
                        }

                        return (
                            <div
                                key={member.id}
                                className="group relative bg-white p-4 rounded-xl border border-gray-100 shadow-sm transition-all duration-300 hover:shadow-md hover:border-purple-100"
                            >
                                <div className="flex justify-between items-start mb-4">
                                    <div className="flex items-center gap-3">
                                        <div className={`w-10 h-10 rounded-full ${statusBg} flex items-center justify-center text-gray-700 font-bold border-2 border-white shadow-sm ring-1 ring-gray-100`}>
                                            <span className="text-xs">{member.name.split(' ').map(n => n[0]).join('')}</span>
                                        </div>
                                        <div>
                                            <p className="text-sm font-bold text-gray-900 leading-none group-hover:text-purple-700 transition-colors">{member.name}</p>
                                            <p className="text-[10px] text-gray-400 font-medium uppercase tracking-tighter mt-1">{member.role}</p>
                                        </div>
                                    </div>
                                    <Icon size={16} className={statusText} />
                                </div>

                                <div className="space-y-3">
                                    <div className="flex justify-between items-end">
                                        <div className="flex flex-col">
                                            <span className="text-[9px] text-gray-400 font-bold uppercase mb-0.5">Uso de Capacidad</span>
                                            <span className={`text-lg font-black leading-none ${statusText}`}>
                                                {percentage.toFixed(0)}%
                                            </span>
                                        </div>
                                        <div className="text-right">
                                            <span className="text-[10px] text-gray-500 font-bold">{used}h</span>
                                            <span className="text-[10px] text-gray-300 mx-1">/</span>
                                            <span className="text-[10px] text-gray-400 font-medium">{capacity}h</span>
                                        </div>
                                    </div>

                                    <div className="relative h-2 w-full bg-gray-100 rounded-full overflow-hidden">
                                        <div
                                            className={`absolute h-full rounded-full transition-all duration-1000 ease-out shadow-sm ${statusColor}`}
                                            style={{ width: `${Math.min(percentage, 100)}%` }}
                                        />
                                        {isOver && (
                                            <div className="absolute inset-0 bg-red-500/20 animate-pulse" />
                                        )}
                                    </div>
                                </div>

                                {isOver && (
                                    <div className="mt-3 py-1.5 px-2 bg-red-50 rounded text-[9px] text-red-600 font-bold flex items-center gap-1.5 border border-red-100">
                                        <AlertCircle size={10} />
                                        <span>REQUERIDO: {used - capacity}h EXCEDIDAS</span>
                                    </div>
                                )}
                            </div>
                        );
                    })}
                </div>
            </CardContent>
        </Card>
    );
}
