
'use client';

import React, { useEffect, useRef, useState } from 'react';
import { useAdmin } from '@/context/AdminContext';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Input } from '@/components/ui/Input';
import { TeamMemberForm } from './TeamMemberForm';
import { TeamMember } from '@/types/admin';
import { formatCurrency } from '@/lib/utils';
import { TeamSummary, TeamVersion, workTeamsService } from '@/services/workTeamsService';

type TeamMemberInput = Omit<TeamMember, 'id' | 'salaryWithCharges' | 'isActive'>;
type MemberTeamAssignment = { teamName: string; percentage: number };

export function TeamMemberList() {
    const { teamMembers, deleteTeamMember, updateTeamMember, addTeamMember } = useAdmin();
    const loadSequenceRef = useRef(0);
    const [isFormOpen, setIsFormOpen] = useState(false);
    const [editingMember, setEditingMember] = useState<TeamMember | undefined>(undefined);
    const [memberTeamsMap, setMemberTeamsMap] = useState<Record<string, MemberTeamAssignment[]>>({});
    const [teams, setTeams] = useState<TeamSummary[]>([]);
    const [latestVersionByTeam, setLatestVersionByTeam] = useState<Record<number, TeamVersion | null>>({});
    const [assignTeamByMember, setAssignTeamByMember] = useState<Record<string, number>>({});
    const [assignPercentageByMember, setAssignPercentageByMember] = useState<Record<string, string>>({});
    const [assigningMemberId, setAssigningMemberId] = useState<string | null>(null);
    const [assignError, setAssignError] = useState<string | null>(null);
    const [assignSuccess, setAssignSuccess] = useState<string | null>(null);

    const loadMemberTeams = React.useCallback(async () => {
        const currentSequence = ++loadSequenceRef.current;
        try {
            const teams = await workTeamsService.listTeams(true);
            if (currentSequence !== loadSequenceRef.current) return;
            setTeams(teams);
            if (!teams.length) {
                setMemberTeamsMap({});
                setLatestVersionByTeam({});
                return;
            }

            const versionsByTeam = await Promise.all(
                teams.map(async (team) => {
                    const versions = await workTeamsService.listTeamVersions(team.id, true);
                    const latest = versions.sort((a, b) => (b.version_number || 0) - (a.version_number || 0))[0];
                    return { teamId: team.id, teamName: team.name, latest };
                })
            );

            const nextMap: Record<string, MemberTeamAssignment[]> = {};
            const nextLatestByTeam: Record<number, TeamVersion | null> = {};
            versionsByTeam.forEach(({ teamId, teamName, latest }) => {
                nextLatestByTeam[teamId] = latest || null;
                if (!latest) return;
                (latest.members || [])
                    .filter((member) => member.is_active !== false)
                    .forEach((member) => {
                        const key = String(member.team_member_id);
                        const percentage = Number(member.weight || 0) * 100;
                        nextMap[key] = [
                            ...(nextMap[key] || []),
                            { teamName, percentage },
                        ];
                    });
            });
            if (currentSequence !== loadSequenceRef.current) return;
            setMemberTeamsMap(nextMap);
            setLatestVersionByTeam(nextLatestByTeam);
        } catch {
            if (currentSequence !== loadSequenceRef.current) return;
            setTeams([]);
            setMemberTeamsMap({});
            setLatestVersionByTeam({});
        }
    }, []);

    useEffect(() => {
        void loadMemberTeams();
    }, [loadMemberTeams]);

    const handleAssignToTeam = async (memberId: string) => {
        setAssignError(null);
        setAssignSuccess(null);
        const teamId = Number(assignTeamByMember[memberId] || 0);
        const percentage = Number(assignPercentageByMember[memberId] || 0);
        if (!teamId) {
            setAssignError('Selecciona un equipo para asignar el miembro.');
            return;
        }
        if (percentage <= 0 || percentage > 100) {
            setAssignError('Ingresa un porcentaje válido entre 0.01 y 100.');
            return;
        }

        const latest = latestVersionByTeam[teamId];
        const existingMembers = (latest?.members || [])
            .filter((m) => m.is_active !== false && String(m.team_member_id) !== memberId)
            .map((m) => ({
                team_member_id: Number(m.team_member_id),
                allocation_percentage: Number(m.weight || 0) * 100,
                role_override: m.role_override || null,
                is_active: true,
            }));

        const currentMember = teamMembers.find((m) => m.id === memberId);
        const mergedMembers = [
            ...existingMembers,
            {
                team_member_id: Number(memberId),
                allocation_percentage: percentage,
                role_override: currentMember?.role || null,
                is_active: true,
            },
        ];

        const total = mergedMembers.reduce((acc, item) => acc + item.allocation_percentage, 0);
        if (Math.abs(total - 100) > 0.05) {
            setAssignError(`La suma de porcentajes del equipo debe ser 100%. Actual: ${total.toFixed(2)}%.`);
            return;
        }

        setAssigningMemberId(memberId);
        try {
            await workTeamsService.publishVersion(teamId, {
                members: mergedMembers.map((m) => ({
                    team_member_id: m.team_member_id,
                    weight: (m.allocation_percentage / 100).toFixed(6),
                    role_override: m.role_override,
                    is_active: m.is_active,
                })),
                notes: 'Asignación desde vista de miembros',
            });
            setAssignSuccess('Miembro asignado al equipo correctamente.');
            await loadMemberTeams();
        } catch (e) {
            setAssignError(e instanceof Error ? e.message : 'No se pudo asignar el miembro al equipo.');
        } finally {
            setAssigningMemberId(null);
        }
    };

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
                {assignError && (
                    <div className="mb-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                        {assignError}
                    </div>
                )}
                {assignSuccess && (
                    <div className="mb-4 rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
                        {assignSuccess}
                    </div>
                )}
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
                                                {memberTeamsMap[member.id].map((assignment) => (
                                                    <span
                                                        key={`${member.id}-${assignment.teamName}`}
                                                        className="inline-flex items-center rounded-full bg-blue-50 px-2 py-0.5 text-[10px] font-semibold text-blue-700"
                                                    >
                                                        {assignment.teamName} ({assignment.percentage.toFixed(1)}%)
                                                    </span>
                                                ))}
                                            </div>
                                        ) : (
                                            <span className="text-xs text-gray-400">Sin equipo</span>
                                        )}
                                        <div className="mt-2 flex flex-wrap items-center gap-2">
                                            <select
                                                className="h-8 rounded-md border border-gray-200 bg-white px-2 text-xs min-w-[140px]"
                                                value={assignTeamByMember[member.id] || ''}
                                                onChange={(e) => setAssignTeamByMember((prev) => ({
                                                    ...prev,
                                                    [member.id]: Number(e.target.value) || 0,
                                                }))}
                                            >
                                                <option value="">Asignar a equipo...</option>
                                                {teams.map((team) => (
                                                    <option key={team.id} value={team.id}>
                                                        {team.name}
                                                    </option>
                                                ))}
                                            </select>
                                            <Input
                                                type="number"
                                                min={0.01}
                                                max={100}
                                                step={0.01}
                                                className="h-8 w-24 bg-white border-gray-200 text-xs"
                                                placeholder="% recurso"
                                                value={assignPercentageByMember[member.id] || ''}
                                                onChange={(e) => setAssignPercentageByMember((prev) => ({
                                                    ...prev,
                                                    [member.id]: e.target.value,
                                                }))}
                                            />
                                            <Button
                                                size="sm"
                                                className="h-8 text-xs"
                                                onClick={() => void handleAssignToTeam(member.id)}
                                                disabled={assigningMemberId === member.id}
                                            >
                                                {assigningMemberId === member.id ? 'Asignando...' : 'Asignar'}
                                            </Button>
                                        </div>
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
