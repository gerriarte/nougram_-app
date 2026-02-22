
'use client';

import React from 'react';
import { AdminLayout } from '@/components/admin/layout/AdminLayout';
import { TeamAvailabilityDashboard } from '@/components/quotes/builder/TeamAvailabilityDashboard';
import { AllocationTimeline } from '@/components/quotes/builder/AllocationTimeline';
import { useResourceAllocation } from '@/hooks/useResourceAllocation';
import { Users, Filter, Calendar } from 'lucide-react';
import { Button } from '@/components/ui/Button';

export default function AvailabilityPage() {
    const { teamMembers, loading, getUtilization } = useResourceAllocation();

    // In a real app, this would fetch ALL allocations from all projects.
    // For this mock implementation, we assume the service provides global data
    // or we use dummy data for the dashboard.
    const mockGlobalAllocations = [
        { id: '1', teamMemberId: 1, hours: 40, role: 'Lead Dev', startDate: '2026-02-01', endDate: '2026-02-28' },
        { id: '2', teamMemberId: 2, hours: 20, role: 'Designer', startDate: '2026-02-05', endDate: '2026-02-15' },
    ];

    if (loading) {
        return (
            <AdminLayout>
                <div className="flex h-screen items-center justify-center">
                    Cargando disponibilidad del equipo...
                </div>
            </AdminLayout>
        );
    }

    return (
        <AdminLayout>
            <div className="space-y-8 pb-20">
                {/* Header */}
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div>
                        <h1 className="text-2xl font-black text-gray-900 tracking-tight">Capacidad del Equipo</h1>
                        <p className="text-gray-500 font-medium">Visualización global de carga de trabajo y disponibilidad.</p>
                    </div>
                    <div className="flex items-center gap-3">
                        <Button variant="secondary" className="flex items-center gap-2">
                            <Filter size={16} />
                            Filtros
                        </Button>
                        <Button className="bg-blue-600 hover:bg-blue-700 text-white flex items-center gap-2 shadow-lg shadow-blue-100">
                            <Calendar size={16} />
                            Planificar Mes
                        </Button>
                    </div>
                </div>

                {/* Main Content */}
                <div className="grid grid-cols-1 gap-8">
                    {/* Summary Widgets could go here */}

                    <TeamAvailabilityDashboard
                        membersOverride={teamMembers}
                        utilizationCalcOverride={(id) => {
                            const member = teamMembers.find(m => m.id === id);
                            if (!member) return { capacity: 0, used: 0, percentage: 0 };
                            // Using local mockGlobalAllocations for this view
                            const used = mockGlobalAllocations
                                .filter(a => a.teamMemberId === id)
                                .reduce((sum, a) => sum + a.hours, 0);
                            return {
                                capacity: member.availableHours,
                                used,
                                percentage: (used / member.availableHours) * 100
                            };
                        }}
                    />

                    <div className="space-y-4">
                        <div className="flex items-center gap-2 px-1">
                            <Users size={18} className="text-gray-400" />
                            <h2 className="text-sm font-black text-gray-400 uppercase tracking-widest">Cronograma Global</h2>
                        </div>
                        <AllocationTimeline
                            allocationsOverride={mockGlobalAllocations as any}
                            membersOverride={teamMembers}
                        />
                    </div>
                </div>
            </div>
        </AdminLayout>
    );
}
