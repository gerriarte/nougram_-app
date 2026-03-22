'use client';

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { teamService } from '@/services/teamService';
import {
    TeamPublishMemberInput,
    TeamSummary,
    TeamVersion,
    TeamGroup,
    workTeamsService
} from '@/services/workTeamsService';

type VersionMemberDraft = {
    team_member_id: number;
    allocation_percentage: string;
    role_override: string;
    is_active: boolean;
};

const DEFAULT_GROUP_NAME = 'Equipos de Trabajo';
const DEFAULT_MEMBER: VersionMemberDraft = {
    team_member_id: 0,
    allocation_percentage: '0',
    role_override: '',
    is_active: true,
};

export function TeamCellsManager() {
    const [loading, setLoading] = React.useState(true);
    const [submitting, setSubmitting] = React.useState(false);
    const [error, setError] = React.useState<string | null>(null);
    const [success, setSuccess] = React.useState<string | null>(null);

    const [groups, setGroups] = React.useState<TeamGroup[]>([]);
    const [teams, setTeams] = React.useState<TeamSummary[]>([]);
    const [versions, setVersions] = React.useState<TeamVersion[]>([]);
    const [members, setMembers] = React.useState<Array<{ id: number; name: string; role: string; isActive: boolean }>>([]);

    const [newTeamName, setNewTeamName] = React.useState('');
    const [newTeamDescription, setNewTeamDescription] = React.useState('');
    const [selectedTeamId, setSelectedTeamId] = React.useState<number>(0);
    const [versionMembers, setVersionMembers] = React.useState<VersionMemberDraft[]>([{ ...DEFAULT_MEMBER }]);
    const [versionNotes, setVersionNotes] = React.useState('');

    const activeMembers = React.useMemo(() => members.filter((m) => m.isActive), [members]);
    const totalPercentage = React.useMemo(
        () => versionMembers.reduce((acc, item) => acc + (Number(item.allocation_percentage) || 0), 0),
        [versionMembers]
    );

    const ensureDefaultGroup = React.useCallback(async (currentGroups: TeamGroup[]): Promise<number | null> => {
        if (currentGroups.length > 0) {
            return currentGroups[0].id;
        }
        const created = await workTeamsService.createGroup({
            name: DEFAULT_GROUP_NAME,
            description: 'Grupo base autogenerado para operación por equipos.',
        });
        return created?.id ?? null;
    }, []);

    const loadCatalog = React.useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const [loadedGroups, loadedTeams, loadedMembers] = await Promise.all([
                workTeamsService.listGroups(true),
                workTeamsService.listTeams(true),
                teamService.getAll(),
            ]);
            setGroups(loadedGroups);
            setTeams(loadedTeams);
            setMembers(
                loadedMembers.map((m) => ({
                    id: Number(m.id),
                    name: m.name,
                    role: m.role,
                    isActive: m.isActive,
                })).filter((m) => Number.isFinite(m.id))
            );
            if (!selectedTeamId && loadedTeams.length > 0) setSelectedTeamId(loadedTeams[0].id);
        } catch (e) {
            setError(e instanceof Error ? e.message : 'No se pudo cargar la configuración de equipos.');
        } finally {
            setLoading(false);
        }
    }, [selectedTeamId]);

    const loadVersions = React.useCallback(async (teamId: number) => {
        if (!teamId) {
            setVersions([]);
            return;
        }
        const loaded = await workTeamsService.listTeamVersions(teamId, true);
        setVersions(loaded);
    }, []);

    React.useEffect(() => {
        void loadCatalog();
    }, [loadCatalog]);

    React.useEffect(() => {
        void loadVersions(selectedTeamId);
    }, [selectedTeamId, loadVersions]);

    const clearMessages = () => {
        setError(null);
        setSuccess(null);
    };

    const handleCreateTeam = async () => {
        clearMessages();
        if (!newTeamName.trim()) {
            setError('El nombre del equipo es obligatorio.');
            return;
        }
        setSubmitting(true);
        try {
            const groupId = await ensureDefaultGroup(groups);
            if (!groupId) {
                setError('No se pudo preparar el grupo base para crear el equipo.');
                return;
            }
            const created = await workTeamsService.createTeam({
                group_id: groupId,
                name: newTeamName.trim(),
                description: newTeamDescription.trim() || undefined,
            });
            if (!created) {
                setError('No se pudo crear el equipo.');
                return;
            }
            setSuccess('Equipo creado correctamente.');
            setNewTeamName('');
            setNewTeamDescription('');
            setSelectedTeamId(created.id);
            await loadCatalog();
        } finally {
            setSubmitting(false);
        }
    };

    const updateVersionMember = (index: number, patch: Partial<VersionMemberDraft>) => {
        setVersionMembers((prev) => prev.map((item, i) => (i === index ? { ...item, ...patch } : item)));
    };

    const addVersionMember = () => {
        setVersionMembers((prev) => [...prev, { ...DEFAULT_MEMBER }]);
    };

    const removeVersionMember = (index: number) => {
        setVersionMembers((prev) => (prev.length <= 1 ? prev : prev.filter((_, i) => i !== index)));
    };

    const handlePublishVersion = async () => {
        clearMessages();
        if (!selectedTeamId) {
            setError('Selecciona un equipo para publicar una versión.');
            return;
        }

        const normalizedMembers = versionMembers.map((item) => ({
            team_member_id: Number(item.team_member_id),
            allocation_percentage: Number(item.allocation_percentage || 0),
            role_override: item.role_override.trim() || null,
            is_active: item.is_active,
        }));

        const invalidMember = normalizedMembers.some(
            (m) => !m.team_member_id || m.allocation_percentage <= 0 || m.allocation_percentage > 100
        );
        if (invalidMember) {
            setError('Cada integrante requiere miembro y porcentaje entre 0.01 y 100.');
            return;
        }

        const uniqueMemberIds = new Set(normalizedMembers.map((m) => m.team_member_id));
        if (uniqueMemberIds.size !== normalizedMembers.length) {
            setError('No repitas el mismo miembro en la versión.');
            return;
        }

        const percentageTotal = normalizedMembers.reduce((acc, item) => acc + item.allocation_percentage, 0);
        if (Math.abs(percentageTotal - 100) > 0.05) {
            setError(`El total de porcentajes debe sumar 100%. Actualmente: ${percentageTotal.toFixed(2)}%.`);
            return;
        }

        const payloadMembers: TeamPublishMemberInput[] = normalizedMembers.map((item) => ({
            team_member_id: item.team_member_id,
            weight: (item.allocation_percentage / 100).toFixed(6),
            role_override: item.role_override,
            is_active: item.is_active,
        }));

        setSubmitting(true);
        try {
            const published = await workTeamsService.publishVersion(selectedTeamId, {
                members: payloadMembers,
                notes: versionNotes.trim() || undefined,
            });
            if (!published) {
                setError('No se pudo publicar la versión del equipo.');
                return;
            }
            setSuccess(`Versión V${published.version_number} publicada correctamente.`);
            setVersionNotes('');
            setVersionMembers([{ ...DEFAULT_MEMBER }]);
            await loadVersions(selectedTeamId);
        } finally {
            setSubmitting(false);
        }
    };

    return (
        <Card>
            <CardHeader className="space-y-2">
                <CardTitle>Equipos de Trabajo</CardTitle>
                <p className="text-sm text-gray-500">
                    Crea y versiona equipos reutilizables para cotizar por porcentaje de ocupación sin editar manualmente integrante por integrante.
                </p>
            </CardHeader>
            <CardContent className="space-y-6">
                {loading && (
                    <div className="rounded-lg border border-gray-200 bg-gray-50 px-4 py-3 text-sm text-gray-500">
                        Cargando configuración de equipos...
                    </div>
                )}

                {error && (
                    <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                        {error}
                    </div>
                )}

                {success && (
                    <div className="rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
                        {success}
                    </div>
                )}

                <div className="rounded-xl border border-blue-200 bg-blue-50/60 p-4">
                    <h3 className="text-sm font-bold uppercase tracking-wide text-blue-700 mb-2">Paso a paso de equipos</h3>
                    <ol className="list-decimal ml-5 space-y-1 text-sm text-blue-900">
                        <li>Crea el equipo (nombre y descripción).</li>
                        <li>Selecciona el equipo y agrega integrantes con porcentaje de participación.</li>
                        <li>Publica la versión para usarla en cotizaciones por ocupación.</li>
                    </ol>
                    <p className="text-xs text-blue-800 mt-3">
                        El porcentaje define cómo se reparte la carga del equipo. La suma de todos los integrantes debe ser 100%.
                    </p>
                </div>

                <div className="grid grid-cols-1 gap-6">
                    <div className="rounded-xl border border-gray-200 p-4 space-y-3">
                        <h3 className="text-sm font-bold uppercase tracking-wide text-gray-600">Paso 1: Crear Equipo</h3>
                        <Input
                            value={newTeamName}
                            onChange={(e) => setNewTeamName(e.target.value)}
                            placeholder="Ej. Equipo Comercial Senior"
                            className="h-10 bg-white border-gray-200"
                        />
                        <Input
                            value={newTeamDescription}
                            onChange={(e) => setNewTeamDescription(e.target.value)}
                            placeholder="Descripción (opcional)"
                            className="h-10 bg-white border-gray-200"
                        />
                        <Button onClick={() => void handleCreateTeam()} disabled={submitting || loading}>
                            Crear equipo
                        </Button>
                    </div>
                </div>

                <div className="rounded-xl border border-gray-200 overflow-hidden">
                    <div className="bg-gray-50 px-4 py-3 border-b border-gray-200">
                        <h3 className="text-sm font-bold uppercase tracking-wide text-gray-600">Equipos Activos</h3>
                    </div>
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                            <thead className="bg-white text-gray-600">
                                <tr>
                                    <th className="px-4 py-3 text-left font-semibold">Equipo</th>
                                    <th className="px-4 py-3 text-left font-semibold">Descripción</th>
                                </tr>
                            </thead>
                            <tbody>
                                {teams.length === 0 ? (
                                    <tr>
                                        <td colSpan={2} className="px-4 py-6 text-center text-gray-400">
                                            Aún no hay equipos configurados.
                                        </td>
                                    </tr>
                                ) : (
                                    teams.map((team) => (
                                        <tr key={team.id} className="border-t border-gray-100">
                                            <td className="px-4 py-3 font-medium text-gray-900">{team.name}</td>
                                            <td className="px-4 py-3 text-gray-600">{team.description || '-'}</td>
                                        </tr>
                                    ))
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>

                <div className="rounded-xl border border-gray-200 p-4 space-y-4">
                    <div className="flex flex-col md:flex-row md:items-center gap-3">
                        <h3 className="text-sm font-bold uppercase tracking-wide text-gray-600">Paso 2: Publicar Versión de Equipo</h3>
                        <select
                            value={selectedTeamId || ''}
                            onChange={(e) => setSelectedTeamId(Number(e.target.value) || 0)}
                            className="h-9 rounded-lg border border-gray-200 bg-white px-3 text-sm md:min-w-[280px]"
                        >
                            <option value="">Selecciona equipo...</option>
                            {teams.map((team) => (
                                <option key={team.id} value={team.id}>
                                    {team.name}
                                </option>
                            ))}
                        </select>
                    </div>

                    <div className="rounded-lg border border-gray-100 bg-gray-50 p-3">
                        <p className="text-xs font-semibold text-gray-500 uppercase mb-2">Versiones existentes</p>
                        <div className="flex flex-wrap gap-2">
                            {versions.length === 0 ? (
                                <span className="text-xs text-gray-400">Sin versiones publicadas.</span>
                            ) : (
                                versions.map((version) => (
                                    <span key={version.id} className="inline-flex rounded-full bg-white border border-gray-200 px-3 py-1 text-xs text-gray-600">
                                        V{version.version_number} - {version.status}
                                    </span>
                                ))
                            )}
                        </div>
                    </div>

                    <div className={`rounded-lg border px-3 py-2 text-xs font-semibold ${
                        Math.abs(totalPercentage - 100) <= 0.05
                            ? 'border-emerald-200 bg-emerald-50 text-emerald-700'
                            : 'border-amber-200 bg-amber-50 text-amber-700'
                    }`}>
                        Total participación: {totalPercentage.toFixed(2)}% {Math.abs(totalPercentage - 100) <= 0.05 ? '(OK)' : '(debe ser 100%)'}
                    </div>

                    <div className="space-y-2">
                        {versionMembers.map((member, index) => (
                            <div key={`${index}-${member.team_member_id}`} className="grid grid-cols-1 md:grid-cols-12 gap-2">
                                <select
                                    value={member.team_member_id || ''}
                                    onChange={(e) => updateVersionMember(index, { team_member_id: Number(e.target.value) || 0 })}
                                    className="md:col-span-5 h-10 rounded-lg border border-gray-200 bg-white px-3 text-sm"
                                >
                                    <option value="">Selecciona integrante...</option>
                                    {activeMembers.map((teamMember) => (
                                        <option key={teamMember.id} value={teamMember.id}>
                                            {teamMember.name} - {teamMember.role}
                                        </option>
                                    ))}
                                </select>
                                <Input
                                    type="number"
                                    min={0.01}
                                    max={100}
                                    step={0.01}
                                    value={member.allocation_percentage}
                                    onChange={(e) => updateVersionMember(index, { allocation_percentage: e.target.value || '0' })}
                                    className="md:col-span-2 h-10 bg-white border-gray-200"
                                    placeholder="%"
                                />
                                <Input
                                    value={member.role_override}
                                    onChange={(e) => updateVersionMember(index, { role_override: e.target.value })}
                                    className="md:col-span-4 h-10 bg-white border-gray-200"
                                    placeholder="Rol override (opcional)"
                                />
                                <Button
                                    type="button"
                                    variant="destructive"
                                    size="sm"
                                    className="md:col-span-1 h-10"
                                    onClick={() => removeVersionMember(index)}
                                    disabled={versionMembers.length <= 1}
                                >
                                    X
                                </Button>
                            </div>
                        ))}
                    </div>

                    <div className="flex flex-wrap items-center gap-2">
                        <Button type="button" variant="secondary" onClick={addVersionMember}>
                            + Agregar integrante
                        </Button>
                        <Input
                            value={versionNotes}
                            onChange={(e) => setVersionNotes(e.target.value)}
                            className="h-10 bg-white border-gray-200 md:min-w-[320px]"
                            placeholder="Notas de versión (opcional)"
                        />
                        <Button
                            type="button"
                            onClick={() => void handlePublishVersion()}
                            disabled={submitting || loading || !selectedTeamId}
                        >
                            Publicar versión
                        </Button>
                    </div>
                </div>
            </CardContent>
        </Card>
    );
}

