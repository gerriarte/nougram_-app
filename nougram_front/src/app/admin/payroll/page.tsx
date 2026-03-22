
import React from 'react';
import { TeamMemberList } from '@/components/admin/payroll/TeamMemberList';

export default function PayrollPage() {
    return (
        <div className="space-y-8">
            <div>
                <h1 className="text-2xl font-bold text-gray-900">Módulo de Nómina</h1>
                <p className="text-gray-500">Gestiona tu equipo humano. La configuracion de cargas prestacionales se configura en Impuestos.</p>
            </div>

            <TeamMemberList />
        </div>
    );
}
