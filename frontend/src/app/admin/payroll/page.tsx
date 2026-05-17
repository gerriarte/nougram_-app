
'use client';

import React from 'react';
import { TeamMemberList } from '@/components/admin/payroll/TeamMemberList';
import { TeamCellsManager } from '@/components/admin/payroll/TeamCellsManager';
import { cn } from '@/lib/utils';

export default function PayrollPage() {
    const [activeTab, setActiveTab] = React.useState<'members' | 'teams'>('members');

    return (
        <div className="space-y-8">
            <div>
                <h1 className="text-[20px] font-bold text-gray-900">Nómina</h1>
                <p className="text-[13px] text-gray-500 mt-0.5">Gestiona tu equipo humano y equipos de trabajo. Las cargas prestacionales se configuran en Impuestos.</p>
            </div>

            <div className="flex items-center gap-1 rounded-lg bg-surface-2 border border-gray-200 p-1 w-fit">
                {(['members', 'teams'] as const).map((tab) => (
                    <button
                        key={tab}
                        type="button"
                        onClick={() => setActiveTab(tab)}
                        className={cn(
                            'px-4 py-1.5 rounded-md text-[12.5px] font-semibold transition-colors',
                            activeTab === tab ? 'bg-white shadow-sm text-gray-900' : 'text-gray-500 hover:text-gray-700'
                        )}
                    >
                        {tab === 'members' ? 'Miembros' : 'Equipos'}
                    </button>
                ))}
            </div>

            {activeTab === 'members' ? <TeamMemberList /> : <TeamCellsManager />}
        </div>
    );
}
