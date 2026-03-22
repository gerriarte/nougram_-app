
'use client';

import React from 'react';
import { TeamMemberList } from '@/components/admin/payroll/TeamMemberList';
import { TeamCellsManager } from '@/components/admin/payroll/TeamCellsManager';
import { Button } from '@/components/ui/Button';

export default function PayrollPage() {
    const [activeTab, setActiveTab] = React.useState<'members' | 'teams'>('members');

    return (
        <div className="space-y-8">
            <div>
                <h1 className="text-2xl font-bold text-gray-900">Módulo de Nómina</h1>
                <p className="text-gray-500">Gestiona tu equipo humano y la configuración de equipos de trabajo. Las cargas prestacionales se configuran en Impuestos.</p>
            </div>

            <div className="flex items-center gap-2">
                <Button
                    variant={activeTab === 'members' ? 'primary' : 'secondary'}
                    onClick={() => setActiveTab('members')}
                >
                    Miembros
                </Button>
                <Button
                    variant={activeTab === 'teams' ? 'primary' : 'secondary'}
                    onClick={() => setActiveTab('teams')}
                >
                    Equipos
                </Button>
            </div>

            {activeTab === 'members' ? <TeamMemberList /> : <TeamCellsManager />}
        </div>
    );
}
