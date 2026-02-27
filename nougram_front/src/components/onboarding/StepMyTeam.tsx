
import React, { useMemo, useState } from 'react';
import { Card, CardContent } from '../ui/Card';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { Label } from '../ui/Label';
import { Alert } from '../ui/Alert';
import { onboardingService } from '@/services/onboardingService';
import { Step3MyTeamData } from '@/types/onboarding';

interface StepMyTeamProps {
    onNext: (data: Step3MyTeamData[]) => void;
    onBack: () => void;
    initialData?: Step3MyTeamData[];
    currency: string;
    country?: string;
}


const ROLES = [
    'Diseñador UI/UX',
    'Desarrollador Frontend',
    'Desarrollador Backend',
    'Product Manager',
    'CEO/Founder',
    'Otro'
];

const LEVELS: Step3MyTeamData['level'][] = ['Junior', 'Mid', 'Senior'];
const SOCIAL_CHARGES_RATE = 0.52852;

const emptyDraft = (isColombia: boolean): Omit<Step3MyTeamData, 'id' | 'yearlyBillableHours' | 'hourlyCost'> => ({
    name: '',
    role: '',
    level: '',
    salary: 0,
    totalHours: 40,
    billableHours: 28,
    vacationDays: 20,
    applySocialCharges: isColombia
});

export function StepMyTeam({ onNext, onBack, initialData, currency, country }: StepMyTeamProps) {
    const isColombia = country === 'COL';
    const [roles, setRoles] = useState<string[]>(ROLES);
    const [newRole, setNewRole] = useState('');
    const [members, setMembers] = useState<Step3MyTeamData[]>(initialData || []);
    const [editingId, setEditingId] = useState<string | null>(null);
    const [draft, setDraft] = useState<Omit<Step3MyTeamData, 'id' | 'yearlyBillableHours' | 'hourlyCost'>>(
        emptyDraft(isColombia)
    );

    const buildMember = (base: Omit<Step3MyTeamData, 'id' | 'yearlyBillableHours' | 'hourlyCost'>, id: string): Step3MyTeamData => {
        const salaryWithCharges = base.applySocialCharges && isColombia
            ? base.salary * (1 + SOCIAL_CHARGES_RATE)
            : base.salary;
        const trueCost = onboardingService.calculateTrueHourlyCost(salaryWithCharges, base.billableHours, base.vacationDays);
        return {
            ...base,
            id,
            applySocialCharges: isColombia ? base.applySocialCharges : false,
            yearlyBillableHours: trueCost.annualBillableHours,
            hourlyCost: trueCost.hourlyCost
        };
    };

    const handleAddRole = () => {
        const trimmed = newRole.trim();
        if (!trimmed || roles.includes(trimmed)) return;
        setRoles((prev) => [...prev, trimmed]);
        setNewRole('');
        if (!draft.role) {
            setDraft((prev) => ({ ...prev, role: trimmed }));
        }
    };

    const handleRemoveRole = (roleToRemove: string) => {
        if (ROLES.includes(roleToRemove)) return;
        setRoles((prev) => prev.filter((role) => role !== roleToRemove));
        if (draft.role === roleToRemove) {
            setDraft((prev) => ({ ...prev, role: '' }));
        }
    };

    const clearDraft = () => {
        setEditingId(null);
        setDraft(emptyDraft(isColombia));
    };

    const saveDraftMember = () => {
        if (!draft.name.trim() || !draft.role || !draft.level || draft.salary <= 0) return;
        if (editingId) {
            setMembers((prev) => prev.map((member) => member.id === editingId ? buildMember(draft, editingId) : member));
            clearDraft();
            return;
        }
        const id = `member-${Date.now()}`;
        setMembers((prev) => [...prev, buildMember(draft, id)]);
        clearDraft();
    };

    const editMember = (member: Step3MyTeamData) => {
        setEditingId(member.id);
        setDraft({
            name: member.name,
            role: member.role,
            level: member.level,
            salary: member.salary,
            totalHours: member.totalHours,
            billableHours: member.billableHours,
            vacationDays: member.vacationDays,
            applySocialCharges: isColombia ? member.applySocialCharges : false
        });
    };

    const deleteMember = (id: string) => {
        setMembers((prev) => prev.filter((member) => member.id !== id));
    };

    const totals = useMemo(() => {
        const totalMonthlyCost = members.reduce((acc, member) => {
            const salaryWithCharges = member.applySocialCharges && isColombia
                ? member.salary * (1 + SOCIAL_CHARGES_RATE)
                : member.salary;
            return acc + salaryWithCharges;
        }, 0);
        const totalHourly = members.reduce((acc, member) => acc + member.hourlyCost, 0);
        const avgHourly = members.length > 0 ? totalHourly / members.length : 0;
        return {
            membersCount: members.length,
            totalMonthlyCost,
            avgHourly
        };
    }, [members, isColombia]);

    const handleNext = () => {
        if (members.length === 0) return;
        onNext(members);
    };

    return (
        <div className="space-y-6 max-w-3xl mx-auto">
            <div className="text-center space-y-2">
                <h1 className="text-2xl font-bold text-gray-900">Configura costos de equipo</h1>
                <p className="text-gray-600">Agrega uno o varios recursos y calcula su costo real por hora.</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <Card className="md:col-span-2">
                    <CardContent className="space-y-4 pt-6">
                        <h3 className="font-semibold text-gray-900">{editingId ? 'Editar recurso' : 'Nuevo recurso'}</h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label>Nombre *</Label>
                                <Input
                                    value={draft.name}
                                    onChange={e => setDraft((prev) => ({ ...prev, name: e.target.value }))}
                                    placeholder="Ej: Juan Perez"
                                />
                            </div>
                            <div className="space-y-2">
                                <Label>Rol / Cargo *</Label>
                                <select
                                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                                    value={draft.role}
                                    onChange={e => setDraft((prev) => ({ ...prev, role: e.target.value }))}
                                >
                                    <option value="">Seleccionar...</option>
                                    {roles.map(r => <option key={r} value={r}>{r}</option>)}
                                </select>
                            </div>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label>Crear nuevo cargo</Label>
                                <div className="flex gap-2">
                                    <Input value={newRole} onChange={e => setNewRole(e.target.value)} placeholder="Ej: Analista SEO" />
                                    <Button type="button" variant="secondary" onClick={handleAddRole}>Agregar</Button>
                                </div>
                            </div>
                            <div className="space-y-2">
                                <Label>Cargos personalizados</Label>
                                <div className="flex flex-wrap gap-2">
                                    {roles.filter((role) => !ROLES.includes(role)).map((role) => (
                                        <button
                                            key={role}
                                            type="button"
                                            onClick={() => handleRemoveRole(role)}
                                            className="text-xs px-2 py-1 rounded bg-gray-100 text-gray-700 hover:bg-gray-200"
                                        >
                                            {role} x
                                        </button>
                                    ))}
                                    {roles.filter((role) => !ROLES.includes(role)).length === 0 && (
                                        <span className="text-xs text-gray-500">Sin cargos personalizados</span>
                                    )}
                                </div>
                            </div>
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label>Nivel *</Label>
                                <select
                                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                                    value={draft.level}
                                    onChange={e => setDraft((prev) => ({ ...prev, level: e.target.value as Step3MyTeamData['level'] }))}
                                >
                                    <option value="">Seleccionar...</option>
                                    {LEVELS.map(l => <option key={l} value={l}>{l}</option>)}
                                </select>
                            </div>
                            <div className="space-y-2">
                                <Label>Salario mensual bruto ({currency}) *</Label>
                                <Input
                                    type="number"
                                    value={draft.salary}
                                    onChange={e => setDraft((prev) => ({ ...prev, salary: Number(e.target.value || 0) }))}
                                    placeholder="0"
                                />
                            </div>
                        </div>

                        <div className="grid grid-cols-3 gap-4">
                            <div className="space-y-2">
                                <Label>Horas totales/semana</Label>
                                <Input
                                    type="number"
                                    value={draft.totalHours}
                                    onChange={e => {
                                        const total = Number(e.target.value || 0);
                                        setDraft((prev) => ({ ...prev, totalHours: total, billableHours: Math.min(prev.billableHours, total) }));
                                    }}
                                />
                            </div>
                            <div className="space-y-2">
                                <Label>Horas facturables/semana</Label>
                                <Input
                                    type="number"
                                    value={draft.billableHours}
                                    onChange={e => setDraft((prev) => ({ ...prev, billableHours: Number(e.target.value || 0) }))}
                                />
                            </div>
                            <div className="space-y-2">
                                <Label>Dias no productivos/anio</Label>
                                <Input
                                    type="number"
                                    value={draft.vacationDays}
                                    onChange={e => setDraft((prev) => ({ ...prev, vacationDays: Number(e.target.value || 0) }))}
                                />
                            </div>
                        </div>

                        <div className="flex gap-2 justify-end">
                            {editingId && (
                                <Button variant="secondary" onClick={clearDraft}>Cancelar edicion</Button>
                            )}
                            <Button onClick={saveDraftMember}>{editingId ? 'Guardar recurso' : 'Agregar recurso'}</Button>
                        </div>
                    </CardContent>
                </Card>

                <Card className="md:col-span-2">
                    <CardContent className="space-y-4 pt-6">
                        <h3 className="font-semibold text-gray-900">Recursos agregados ({members.length})</h3>
                        {members.length === 0 ? (
                            <p className="text-sm text-gray-500">Aun no agregas recursos.</p>
                        ) : (
                            <div className="space-y-3">
                                {members.map((member) => (
                                    <div key={member.id} className="p-3 border rounded-lg bg-white flex items-center justify-between">
                                        <div>
                                            <p className="font-medium text-gray-900">{member.name} · {member.role} ({member.level})</p>
                                            <p className="text-sm text-gray-600">
                                                {currency} {member.salary.toLocaleString()} / mes · {Math.round(member.hourlyCost).toLocaleString()} {currency}/h
                                            </p>
                                        </div>
                                        <div className="flex gap-2">
                                            <Button variant="secondary" onClick={() => editMember(member)}>Editar</Button>
                                            <Button variant="secondary" onClick={() => deleteMember(member.id)}>Eliminar</Button>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </CardContent>
                </Card>

                <Card className="md:col-span-2">
                    <CardContent className="space-y-4 pt-6">
                        <div className="flex items-center justify-between">
                            <h3 className="font-semibold text-gray-900">Costos fiscales de contratacion</h3>
                            <span className={`text-xs px-2 py-1 rounded ${isColombia ? 'bg-emerald-100 text-emerald-700' : 'bg-gray-100 text-gray-600'}`}>
                                {isColombia ? 'Activo para Colombia' : 'Desactivado para este pais'}
                            </span>
                        </div>
                        {!isColombia ? (
                            <Alert variant="warning" className="bg-amber-50 border-amber-200">
                                <p className="text-sm text-amber-800">
                                    El modulo fiscal de contratacion solo aplica para Colombia. Para otras monedas/paises se mantiene desactivado.
                                </p>
                            </Alert>
                        ) : (
                            <div className="space-y-3 text-sm">
                                <p className="text-gray-600">Config actual (Colombia): Salud 8.5%, Pension 12%, Prestaciones 21.85%, total aproximado 52.852%.</p>
                                <div className="space-y-2">
                                    <label className="inline-flex items-center gap-2 text-gray-700">
                                        <input
                                            type="checkbox"
                                            checked={draft.applySocialCharges}
                                            onChange={e => setDraft((prev) => ({ ...prev, applySocialCharges: e.target.checked }))}
                                            className="h-4 w-4"
                                        />
                                        Aplicar costos fiscales a este recurso
                                    </label>
                                </div>
                            </div>
                        )}
                    </CardContent>
                </Card>

                <Card className="md:col-span-2 bg-slate-900 text-white border-slate-800">
                    <CardContent className="space-y-4 pt-6">
                        <div className="flex items-center gap-2 text-blue-400">
                            <span className="text-xl">💎</span>
                            <h3 className="font-semibold">Resumen de equipo</h3>
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                            <div>
                                <p className="text-slate-400">Recursos activos</p>
                                <p className="text-xl font-bold">{totals.membersCount}</p>
                            </div>
                            <div>
                                <p className="text-slate-400">Costo mensual equipo</p>
                                <p className="text-xl font-bold">{currency} {Math.round(totals.totalMonthlyCost).toLocaleString()}</p>
                            </div>
                            <div>
                                <p className="text-slate-400">Costo hora promedio</p>
                                <p className="text-xl font-bold">{currency} {Math.round(totals.avgHourly).toLocaleString()}</p>
                            </div>
                        </div>
                    </CardContent>
                </Card>

            </div>

            <div className="flex justify-between mt-6">
                <Button variant="secondary" onClick={onBack}>← Atrás</Button>
                <Button onClick={handleNext} disabled={members.length === 0}>Siguiente →</Button>
            </div>
        </div>
    );
}
