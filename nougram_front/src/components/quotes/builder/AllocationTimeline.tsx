
'use client';

import React from 'react';
import { useQuoteBuilder } from '@/context/QuoteBuilderContext';
import { Card, CardContent } from '@/components/ui/Card';
import { Calendar, Clock } from 'lucide-react';

interface AllocationTimelineProps {
    allocationsOverride?: import('@/types/quote-builder').ResourceAllocation[];
    membersOverride?: import('@/types/quote-builder').TeamMemberMock[];
}

export function AllocationTimeline({ allocationsOverride, membersOverride }: AllocationTimelineProps) {
    const context = useQuoteBuilder();

    const allocations = allocationsOverride || context.state.resourceAllocations;
    const teamMembers = membersOverride || context.teamMembers;

    // Only show if there are allocations with dates
    const allocationsWithDates = allocations.filter(a => a.startDate || a.endDate);
    if (allocationsWithDates.length === 0) return null;

    // Find min and max dates to define the range
    const dates = allocationsWithDates.flatMap(a => [
        a.startDate ? new Date(a.startDate).getTime() : Infinity,
        a.endDate ? new Date(a.endDate).getTime() : -Infinity
    ]).filter(d => d !== Infinity && d !== -Infinity);

    if (dates.length === 0) return null;

    const minDate = new Date(Math.min(...dates));
    const maxDate = new Date(Math.max(...dates));

    // Add some padding to the range (e.g., 2 days)
    minDate.setDate(minDate.getDate() - 2);
    maxDate.setDate(maxDate.getDate() + 2);

    const totalTime = maxDate.getTime() - minDate.getTime();
    const totalDays = Math.ceil(totalTime / (1000 * 60 * 60 * 24));

    // Helper to format date for display
    const formatDate = (date: Date) => {
        return date.toLocaleDateString('es-ES', { day: '2-digit', month: 'short' });
    };

    return (
        <Card className="overflow-hidden border border-gray-100 shadow-sm bg-white/50 backdrop-blur-sm">
            <CardContent className="p-5">
                <div className="flex items-center justify-between mb-6">
                    <div className="flex items-center gap-2">
                        <div className="p-1.5 bg-blue-50 rounded-lg">
                            <Calendar size={18} className="text-blue-600" />
                        </div>
                        <h3 className="text-sm font-bold text-gray-800 tracking-tight">Cronograma de Asignación</h3>
                    </div>
                    <div className="flex items-center gap-1.5 px-2 py-1 bg-gray-50 rounded text-[10px] text-gray-500 font-medium border border-gray-100">
                        <Clock size={12} />
                        <span>{totalDays} días de proyecto</span>
                    </div>
                </div>

                <div className="relative">
                    {/* Header Dates / Grid Markers */}
                    <div className="flex justify-between text-[10px] text-gray-400 font-bold mb-4 uppercase tracking-tighter px-1">
                        <span className="flex flex-col items-center">
                            <span className="w-px h-2 bg-gray-200 mb-1" />
                            {formatDate(minDate)}
                        </span>
                        <span className="flex flex-col items-center">
                            <span className="w-px h-2 bg-gray-200 mb-1" />
                            {formatDate(maxDate)}
                        </span>
                    </div>

                    {/* Timeline Rows */}
                    <div className="space-y-4 relative">
                        {/* Grid Background Lines (Optional) */}
                        <div className="absolute inset-0 flex justify-between pointer-events-none opacity-20">
                            <div className="w-px h-full bg-gray-300" />
                            <div className="w-px h-full bg-gray-300" />
                            <div className="w-px h-full bg-gray-300" />
                            <div className="w-px h-full bg-gray-300" />
                            <div className="w-px h-full bg-gray-300" />
                        </div>

                        {allocations.map(alloc => {
                            const member = teamMembers.find(m => m.id === alloc.teamMemberId);
                            if (!member || !alloc.startDate) return null;

                            const start = new Date(alloc.startDate);
                            // If no end date, assume 1 day or end of project for visualization
                            const end = alloc.endDate ? new Date(alloc.endDate) : new Date(alloc.startDate);

                            const offsetDays = (start.getTime() - minDate.getTime());
                            const durationDays = Math.max(1000 * 60 * 60 * 24, (end.getTime() - start.getTime()));

                            const left = (offsetDays / totalTime) * 100;
                            const width = (durationDays / totalTime) * 100;

                            return (
                                <div key={alloc.id} className="relative group pt-4">
                                    <div className="flex items-center justify-between mb-1.5">
                                        <span className="text-[11px] font-bold text-gray-700 flex items-center gap-1.5">
                                            <span className="w-1.5 h-1.5 rounded-full bg-purple-500" />
                                            {member.name}
                                        </span>
                                        <span className="text-[10px] text-gray-500 font-medium group-hover:text-purple-600 transition-colors">
                                            {alloc.hours}h ({alloc.role || member.role})
                                        </span>
                                    </div>

                                    <div className="relative h-2.5 w-full bg-gray-100/50 rounded-full overflow-hidden border border-gray-50">
                                        <div
                                            className="absolute h-full rounded-full bg-gradient-to-r from-purple-500 to-blue-500 shadow-[0_0_10px_rgba(168,85,247,0.3)] transition-all duration-500 ease-out group-hover:from-purple-600 group-hover:to-blue-600"
                                            style={{
                                                left: `${Math.max(0, Math.min(left, 95))}%`,
                                                width: `${Math.max(2, Math.min(width, 100))}%`
                                            }}
                                        />
                                    </div>

                                    {/* Tooltip on hover */}
                                    <div className="absolute opacity-0 group-hover:opacity-100 transition-all duration-200 pointer-events-none -top-8 left-1/2 -translate-x-1/2 bg-gray-900 text-white text-[10px] py-1 px-2 rounded z-10 whitespace-nowrap shadow-lg">
                                        {formatDate(start)} - {alloc.endDate ? formatDate(end) : 'S/F'}
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>
            </CardContent>
        </Card>
    );
}
