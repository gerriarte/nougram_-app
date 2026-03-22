
'use client';

import React, { useEffect, useState } from 'react';
import { useAdmin } from '@/context/AdminContext';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { TeamMemberForm } from './TeamMemberForm';
import { TeamMember } from '@/types/admin';
import { formatCurrency } from '@/lib/utils';
import { workTeamsService } from '@/services/workTeamsService';

type TeamMemberInput = Omit<TeamMember, 'id' | 'salaryWithCharges' | 'isActive'>;

export function TeamMemberList() {
    const { teamMembers, deleteTeamMember, updateTeamMember, addTeamMember } = useAdmin();
    const [isFormOpen, setIsFormOpen] = useState(false);
    const [editingMember, setEditingMember] = useState<TeamMember | undefined>(undefined);
    const [memberTeamsMap, setMemberTeamsMap] = useState<Record<string, string[]>>({});

    useEffect(() => {
        let mounted = true;
        const loadMemberTeams = async () => {
            const teams = await workTeamsService.listTeams(true);
            if (!teams.length) {
                if (mounted) setMemberTeamsMap({});
                return;
            }

            const versionsByTeam = await Promise.all(
                teams.map(async (team) => {
                    const versions = await workTeamsService.listTeamVersions(team.id, true);
                    const latest = versions.sort((a, b) => (b.version_number || 0) - (a.version_number || 0))[0];
                    return { teamName: team.name, latest };
                })
            );

            const nextMap: Record<string, string[]> = {};
            versionsByTeam.forEach(({ teamName, latest }) => {
                if (!latest) return;
                (latest.members || [])
                    .filter((member) => member.is_active !== false)
                    .forEach((member) => {
                        const key = String(member.team_member_id);
                        nextMap[key] = [...(nextMap[key] || []), teamName];
                    });
            });
            if (mounted) setMemberTeamsMap(nextMap);
        };

        void loadMemberTeams();
        return () => {
            mounted = false;
        };
    }, [teamMembers]);

    const handleCreate = () => {
        setEditingMember(undefined);
        setIsFormOpen(true);
    };

    const handleEdit = (member: TeamMember) => {
        setEditingMember(member);
        setIsFormOpen(true);
    };

    const handleSave = (data: TeamMemberInput) => {
        if (editingMember) {
            updateTeamMember(editingMember.id, data);
        } else {
            addTeamMember({
                ...data,
                id: crypto.randomUUID(), // In real app, backend generates ID
                salaryWithCharges: 0, // Context will recalc this
                isActive: true
            });
        }
    };

    const handleDelete = (id: string) => {
        if (confirm('¿Estás seguro de eliminar este miembro?')) {
            deleteTeamMember(id);
        }
    };

    return (
        <Card>
            <CardHeader className="flex flex-row items-center justify-between">
                <div>
                    <CardTitle>Miembros del Equipo</CardTitle>
                    <p className="text-sm text-gray-500">Gestiona tu nómina y capacidad operativa.</p>
                </div>
                <Button onClick={handleCreate}>+ Agregar Miembro</Button>
            </CardHeader>
            <CardContent>
                <div className="overflow-x-auto">
                    <table className="w-full text-sm text-left">
                        <thead className="bg-gray-50 text-gray-700 uppercase text-xs">
                            <tr>
                                <th className="px-4 py-3">Nombre / Rol</th>
                                <th className="px-4 py-3">Equipos</th>
                                <th className="px-4 py-3">Salario Base</th>
                                <th className="px-4 py-3">Con Cargas</th>
                                <th className="px-4 py-3">Horas/Sem</th>
                                <th className="px-4 py-3">Estado</th>
                                <th className="px-4 py-3 text-right">Acciones</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-200">
                            {teamMembers.map(member => (
                                <tr key={member.id} className="hover:bg-gray-50">
                                    <td className="px-4 py-3">
                                        <div className="font-medium text-gray-900">{member.name}</div>
                                        <div className="text-xs text-gray-500">{member.role}</div>
                                    </td>
                                    <td className="px-4 py-3">
                                        {memberTeamsMap[member.id]?.length ? (
                                            <div className="flex flex-wrap gap-1">
                                                {memberTeamsMap[member.id].map((teamName) => (
                                                    <span
                                                        key={`${member.id}-${teamName}`}
                                                        className="inline-flex items-center rounded-full bg-blue-50 px-2 py-0.5 text-[10px] font-semibold text-blue-700"
                                                    >
                                                        {teamName}
                                                    </span>
                                                ))}
                                            </div>
                                        ) : (
                                            <span className="text-xs text-gray-400">Sin equipo</span>
                                        )}
                                    </td>
                                    <td className="px-4 py-3">
                                        {formatCurrency(member.salaryMonthlyBrute, member.currency)}
                                    </td>
                                    <td className="px-4 py-3 font-medium text-blue-600">
                                        {/* Simple display logic, precise calculation is in context */}
                                        {formatCurrency((member.salaryWithCharges || member.salaryMonthlyBrute), member.currency)}
                                    </td>
                                    <td className="px-4 py-3">
                                        {member.billableHoursPerWeek} hrs
                                        <div className="text-xs text-gray-500">{(member.nonBillablePercentage * 100).toFixed(0)}% Admin</div>
                                    </td>
                                    <td className="px-4 py-3">
                                        <Badge variant={member.isActive ? 'success' : 'default'}>
                                            {member.isActive ? 'Activo' : 'Inactivo'}
                                        </Badge>
                                    </td>
                                    <td className="px-4 py-3 text-right space-x-2">
                                        <Button variant="secondary" size="sm" onClick={() => handleEdit(member)}>Editar</Button>
                                        <Button
                                            variant="destructive"
                                            size="sm"
                                            onClick={() => handleDelete(member.id)}
                                        >
                                            🗑️
                                        </Button>
                                    </td>
                                </tr>
                            ))}
                            {teamMembers.length === 0 && (
                                <tr>
                                    <td colSpan={7} className="px-4 py-8 text-center text-gray-500 italic">
                                        No hay miembros configurados. Agrega uno para empezar.
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </CardContent>

            <TeamMemberForm
                open={isFormOpen}
                onOpenChange={setIsFormOpen}
                initialData={editingMember}
                onSave={handleSave}
            />
        </Card>
    );
}
