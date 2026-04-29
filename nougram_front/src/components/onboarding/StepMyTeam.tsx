
import React, { useState } from 'react';
import { Card, CardContent } from '../ui/Card';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { Label } from '../ui/Label';
import { Alert } from '../ui/Alert';
import { OnboardingStepHero } from '@/components/onboarding/OnboardingStepHero';
import { Step3MyTeamData } from '@/types/onboarding';
import { formatCurrency, formatLocalizedNumberInput, parseLocalizedNumberInput } from '@/lib/utils';
import { cn } from '@/lib/utils';

interface StepMyTeamProps {
    onNext: (data: Step3MyTeamData) => void;
    onBack: () => void;
    initialData?: Step3MyTeamData;
    currency: string;
    backendBcr?: number | null;
    backendBcrLoading?: boolean;
    onOpenImport?: () => void;
}


const ROLES = [
    'Project Manager',
    'Diseñador UI/UX',
    'Desarrollador Frontend',
    'Desarrollador Backend',
    'QA',
    'UX Researcher',
    'Director/a Creativa',
    'Product Manager',
    'CEO/Founder',
    'Otro'
];

const LEVELS = ['Junior', 'Mid', 'Senior', 'Lead'];

type TeamMemberDraft = {
    id: string;
    name: string;
    role: string;
    level: 'Junior' | 'Mid' | 'Senior' | '';
    salary: string;
    totalHours: number;
    billableHours: number;
    vacationDays: number;
    applySocialCharges: boolean;
};

type ModeledMember = {
    id: string;
    name: string;
    role: string;
    level: Step3MyTeamData['level'];
    salary: number;
    totalHours: number;
    billableHours: number;
    vacationDays: number;
    applySocialCharges: boolean;
    isMain?: boolean;
};

export function StepMyTeam({
    onNext,
    onBack,
    initialData,
    currency,
    backendBcr,
    backendBcrLoading,
    onOpenImport
}: StepMyTeamProps) {
    const isCopCurrency = String(currency || '').toUpperCase() === 'COP';
    const moneyInputMode: 'numeric' | 'decimal' = isCopCurrency ? 'numeric' : 'decimal';
    const parseMoneyInput = (raw: string) => parseLocalizedNumberInput(raw, { allowDecimal: !isCopCurrency });
    const formatMoneyInput = (value: number | string | null | undefined) =>
        formatLocalizedNumberInput(value, { currencyCode: currency, maximumFractionDigits: isCopCurrency ? 0 : 2 });

    const [payrollHeadcount, setPayrollHeadcount] = useState<number>(initialData?.payrollHeadcount || 1);
    // Member Info
    const [name, setName] = useState(initialData?.name || '');
    const [role, setRole] = useState(initialData?.role || '');
    const [customRole, setCustomRole] = useState(
        initialData?.role && !ROLES.includes(initialData.role) ? initialData.role : ''
    );
    const [isCustomRole, setIsCustomRole] = useState(
        Boolean(initialData?.role && !ROLES.includes(initialData.role))
    );
    const [level, setLevel] = useState<Step3MyTeamData['level']>(initialData?.level || '');
    const [salary, setSalary] = useState<string>(() =>
        initialData?.salary != null ? formatMoneyInput(initialData.salary) : ''
    );

    // Reality Calculator
    const [totalHours, setTotalHours] = useState<number>(initialData?.totalHours || 40);
    const [billableHours, setBillableHours] = useState<number>(initialData?.billableHours || 28);

    // Annual Calculation Defaults
    const [vacationDays, setVacationDays] = useState<number>(initialData?.vacationDays || 20);

    // Social Charges
    const [applySocialCharges, setApplySocialCharges] = useState<boolean>(initialData?.applySocialCharges ?? true);
    const [additionalMembers, setAdditionalMembers] = useState<TeamMemberDraft[]>(
        (initialData?.teamMembers || []).slice(1).map((member, index) => ({
            id: member.id || `member-${index + 1}`,
            name: member.name,
            role: member.role,
            level: member.level,
            salary: member.salary != null ? formatMoneyInput(member.salary) : '',
            totalHours: member.totalHours || 40,
            billableHours: member.billableHours || 28,
            vacationDays: member.vacationDays || 20,
            applySocialCharges: member.applySocialCharges ?? true,
        }))
    );
    const [activeMemberId, setActiveMemberId] = useState<string>('main');

    // Calculations
    const salaryNum = parseMoneyInput(salary);

    // Social Charges Math (Colombia Defaults)
    const SOCIAL_CHARGES_RATE = 0.52852; // ~52.8%
    const selectedRole = isCustomRole ? customRole : role;

    const memberRows: ModeledMember[] = [
        {
            id: 'main',
            name,
            role: selectedRole,
            level,
            salary: salaryNum,
            totalHours,
            billableHours,
            vacationDays,
            applySocialCharges,
            isMain: true,
        },
        ...additionalMembers.map((member) => ({
            id: member.id,
            name: member.name,
            role: member.role,
            level: member.level,
            salary: parseMoneyInput(member.salary),
            totalHours: member.totalHours,
            billableHours: member.billableHours,
            vacationDays: member.vacationDays,
            applySocialCharges: member.applySocialCharges,
        })),
    ];
    const modeledMembers = memberRows.filter((member) => member.name && member.role && member.salary > 0 && member.billableHours > 0);
    const activeMember = memberRows.find((member) => member.id === activeMemberId) || memberRows[0];
    const activeAdditionalMember = additionalMembers.find((member) => member.id === activeMemberId);

    // True Cost Calculation (Live) with all modeled members
    const aggregateAnnualCost = modeledMembers.reduce((sum, member) => {
        const monthly = member.applySocialCharges ? member.salary * (1 + SOCIAL_CHARGES_RATE) : member.salary;
        return sum + (monthly * 12);
    }, 0);
    const aggregateAnnualHours = modeledMembers.reduce((sum, member) => {
        const productiveWeeks = 52 - (member.vacationDays / 5);
        return sum + (member.billableHours * productiveWeeks);
    }, 0);
    const trueCostAnalysis = {
        annualCost: aggregateAnnualCost,
        annualBillableHours: aggregateAnnualHours,
        hourlyCost: aggregateAnnualHours > 0 ? aggregateAnnualCost / aggregateAnnualHours : 0,
    };
    const displayedBcr = backendBcr ?? trueCostAnalysis.hourlyCost;

    const handleTotalHoursChange = (val: string) => {
        const hours = parseInt(val) || 0;
        setTotalHours(hours);
        // Default logic: ~70% billable
        setBillableHours(Math.floor(hours * 0.7));
    };

    const handleNext = () => {
        if (modeledMembers.length === 0) return;
        const fallbackMember = modeledMembers[0];

        onNext({
            payrollHeadcount,
            name: name || fallbackMember?.name || '',
            role: selectedRole || fallbackMember?.role || '',
            level: (level || fallbackMember?.level || '') as Step3MyTeamData['level'],
            salary: salaryNum || fallbackMember?.salary || 0,
            totalHours: totalHours || fallbackMember?.totalHours || 40,
            billableHours: billableHours || fallbackMember?.billableHours || 28,
            vacationDays: vacationDays || fallbackMember?.vacationDays || 20,
            applySocialCharges: applySocialCharges ?? fallbackMember?.applySocialCharges ?? true,
            yearlyBillableHours: trueCostAnalysis.annualBillableHours,
            hourlyCost: trueCostAnalysis.hourlyCost,
            teamMembers: modeledMembers
        });
    };

    const addAdditionalMember = () => {
        const id = `member-${Date.now()}`;
        setAdditionalMembers((prev) => [
            ...prev,
            {
                id,
                name: '',
                role: '',
                level: 'Mid',
                salary: '',
                totalHours: 40,
                billableHours: 28,
                vacationDays: 20,
                applySocialCharges: true,
            },
        ]);
        setActiveMemberId(id);
    };

    const updateAdditionalMember = (id: string, updates: Partial<TeamMemberDraft>) => {
        setAdditionalMembers((prev) => prev.map((member) => (member.id === id ? { ...member, ...updates } : member)));
    };

    const removeAdditionalMember = (id: string) => {
        setAdditionalMembers((prev) => prev.filter((member) => member.id !== id));
        if (activeMemberId === id) setActiveMemberId('main');
    };

    return (
        <div className="space-y-6 max-w-3xl mx-auto px-1">
            <OnboardingStepHero
                eyebrow="Paso 3 de 4"
                title="Modela tu equipo y horas facturables"
                description="Carga nómina, rol y disponibilidad real. Con esto calculamos el BCR usando horas productivas, vacaciones y cargas sociales."
                callout="Puedes empezar con una persona y agregar el resto del equipo ahora o más adelante desde Nómina."
            />

            <div className="grid grid-cols-1 gap-4 lg:grid-cols-[280px_1fr] lg:items-start">
                <Card className="overflow-hidden border-gray-200 shadow-sm lg:sticky lg:top-24">
                    <div className="flex items-center justify-between border-b border-gray-100 px-4 py-3">
                        <div>
                            <p className="text-sm font-bold text-gray-900">Miembros del equipo</p>
                            <p className="mt-0.5 text-[11px] text-gray-400">
                                {modeledMembers.length} válidos · {memberRows.length} total
                            </p>
                        </div>
                        {onOpenImport && (
                            <Button type="button" variant="secondary" size="sm" onClick={onOpenImport}>
                                Excel
                            </Button>
                        )}
                    </div>
                    <div className="max-h-[420px] overflow-y-auto">
                        {memberRows.map((member, index) => {
                            const selected = member.id === activeMemberId;
                            const valid = Boolean(member.name && member.role && member.salary > 0);
                            const initials = member.name
                                ? member.name.split(' ').map(part => part[0]).slice(0, 2).join('').toUpperCase()
                                : String(index + 1);
                            return (
                                <button
                                    key={member.id}
                                    type="button"
                                    onClick={() => setActiveMemberId(member.id)}
                                    className={cn(
                                        'flex w-full items-center gap-3 border-b border-gray-100 px-4 py-3 text-left transition-colors',
                                        selected ? 'border-l-4 border-l-primary bg-primary-soft' : 'border-l-4 border-l-transparent hover:bg-gray-50'
                                    )}
                                >
                                    <div className={cn(
                                        'flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-xs font-black',
                                        valid ? 'bg-primary text-white' : 'bg-gray-100 text-gray-400'
                                    )}>
                                        {initials}
                                    </div>
                                    <div className="min-w-0 flex-1">
                                        <p className="truncate text-[13px] font-bold text-gray-900">
                                            {member.name || (member.isMain ? 'Tú (miembro principal)' : `Miembro ${index + 1}`)}
                                        </p>
                                        <p className="mt-0.5 truncate text-[11px] text-gray-400">{member.role || 'Sin completar'}</p>
                                    </div>
                                    <span className={cn(
                                        'flex h-5 w-5 items-center justify-center rounded-full text-[10px] font-black',
                                        valid ? 'bg-success text-white' : 'bg-warning-soft text-warning'
                                    )}>
                                        {valid ? '✓' : '!'}
                                    </span>
                                </button>
                            );
                        })}
                    </div>
                    <button
                        type="button"
                        onClick={addAdditionalMember}
                        className="flex w-full items-center justify-center gap-1.5 border-t border-gray-100 bg-surface-2 px-4 py-3 text-[12px] font-bold text-primary hover:bg-primary-soft"
                    >
                        + Agregar miembro
                    </button>
                </Card>

                <div className="space-y-4">
                    <Card className="border-gray-200 shadow-sm">
                        <CardContent className="space-y-5 pt-6">
                            <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                                <div>
                                    <h3 className="text-lg font-black tracking-tight text-gray-900">
                                        {activeMember.isMain ? 'Tú (miembro principal)' : (activeMember.name || 'Nuevo miembro')}
                                    </h3>
                                    <p className="mt-1 text-sm text-gray-500">Quick-add: nombre, rol y salario son lo mínimo para continuar.</p>
                                </div>
                                {!activeMember.isMain && activeAdditionalMember && (
                                    <Button type="button" variant="destructive" size="sm" onClick={() => removeAdditionalMember(activeAdditionalMember.id)}>
                                        Eliminar
                                    </Button>
                                )}
                            </div>

                            <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
                                <div>
                                    <Label>Nombre completo *</Label>
                                    <Input
                                        value={activeMember.isMain ? name : activeAdditionalMember?.name || ''}
                                        onChange={(event) => activeMember.isMain
                                            ? setName(event.target.value)
                                            : activeAdditionalMember && updateAdditionalMember(activeAdditionalMember.id, { name: event.target.value })}
                                        placeholder="Ej. Juan Pérez"
                                    />
                                </div>
                                <div>
                                    <Label>Rol *</Label>
                                    <select
                                        value={activeMember.isMain ? (isCustomRole ? 'Otro' : role) : activeAdditionalMember?.role || ''}
                                        onChange={(event) => {
                                            if (activeMember.isMain) {
                                                const nextRole = event.target.value;
                                                setIsCustomRole(nextRole === 'Otro');
                                                setRole(nextRole === 'Otro' ? '' : nextRole);
                                            } else if (activeAdditionalMember) {
                                                updateAdditionalMember(activeAdditionalMember.id, { role: event.target.value });
                                            }
                                        }}
                                        className="h-10 w-full rounded-md border border-gray-300 bg-white px-3 text-sm"
                                    >
                                        <option value="">Seleccionar rol</option>
                                        {ROLES.map((roleOption) => (
                                            <option key={roleOption} value={roleOption}>{roleOption}</option>
                                        ))}
                                    </select>
                                    {activeMember.isMain && isCustomRole && (
                                        <Input
                                            className="mt-2"
                                            value={customRole}
                                            onChange={(event) => setCustomRole(event.target.value)}
                                            placeholder="Escribe el rol"
                                        />
                                    )}
                                </div>
                                <div>
                                    <Label>Salario mensual *</Label>
                                    <Input
                                        type="text"
                                        inputMode={moneyInputMode}
                                        value={activeMember.isMain ? salary : activeAdditionalMember?.salary || ''}
                                        onChange={(event) => activeMember.isMain
                                            ? setSalary(event.target.value)
                                            : activeAdditionalMember && updateAdditionalMember(activeAdditionalMember.id, { salary: event.target.value })}
                                        placeholder={`${currency} 0`}
                                    />
                                </div>
                            </div>

                            <div className="grid grid-cols-1 gap-3 md:grid-cols-4">
                                <div>
                                    <Label>Nivel</Label>
                                    <select
                                        value={activeMember.isMain ? level : activeAdditionalMember?.level || 'Mid'}
                                        onChange={(event) => activeMember.isMain
                                            ? setLevel(event.target.value as Step3MyTeamData['level'])
                                            : activeAdditionalMember && updateAdditionalMember(activeAdditionalMember.id, { level: event.target.value as TeamMemberDraft['level'] })}
                                        className="h-10 w-full rounded-md border border-gray-300 bg-white px-3 text-sm"
                                    >
                                        {LEVELS.map((levelOption) => (
                                            <option key={levelOption} value={levelOption}>{levelOption}</option>
                                        ))}
                                    </select>
                                </div>
                                <div>
                                    <Label>Horas/semana</Label>
                                    <Input
                                        type="number"
                                        min={1}
                                        value={activeMember.isMain ? totalHours : activeAdditionalMember?.totalHours || 40}
                                        onChange={(event) => activeMember.isMain
                                            ? handleTotalHoursChange(event.target.value)
                                            : activeAdditionalMember && updateAdditionalMember(activeAdditionalMember.id, { totalHours: Math.max(1, Number(event.target.value) || 40) })}
                                    />
                                </div>
                                <div>
                                    <Label>Facturables/semana</Label>
                                    <Input
                                        type="number"
                                        min={1}
                                        value={activeMember.isMain ? billableHours : activeAdditionalMember?.billableHours || 28}
                                        onChange={(event) => activeMember.isMain
                                            ? setBillableHours(Math.max(1, Number(event.target.value) || 1))
                                            : activeAdditionalMember && updateAdditionalMember(activeAdditionalMember.id, { billableHours: Math.max(1, Number(event.target.value) || 1) })}
                                    />
                                </div>
                                <div>
                                    <Label>Días no productivos</Label>
                                    <Input
                                        type="number"
                                        min={0}
                                        value={activeMember.isMain ? vacationDays : activeAdditionalMember?.vacationDays || 20}
                                        onChange={(event) => activeMember.isMain
                                            ? setVacationDays(Math.max(0, Number(event.target.value) || 0))
                                            : activeAdditionalMember && updateAdditionalMember(activeAdditionalMember.id, { vacationDays: Math.max(0, Number(event.target.value) || 0) })}
                                    />
                                </div>
                            </div>

                            <label className="flex cursor-pointer items-center gap-2 rounded-xl border border-gray-200 bg-surface-2 px-3 py-2 text-sm text-gray-600">
                                <input
                                    type="checkbox"
                                    checked={activeMember.isMain ? applySocialCharges : activeAdditionalMember?.applySocialCharges ?? true}
                                    onChange={(event) => activeMember.isMain
                                        ? setApplySocialCharges(event.target.checked)
                                        : activeAdditionalMember && updateAdditionalMember(activeAdditionalMember.id, { applySocialCharges: event.target.checked })}
                                    className="h-4 w-4 rounded border-gray-300 text-primary"
                                />
                                Aplicar cargas sociales
                            </label>
                        </CardContent>
                    </Card>

                    <Card className="overflow-hidden border-slate-800 bg-slate-900 text-white">
                        <CardContent className="space-y-4 pt-6">
                            <div className="flex items-center gap-2 text-blue-300">
                                <span className="text-xl">✦</span>
                                <h3 className="font-semibold">Costo real por hora — vista previa</h3>
                            </div>

                            <div className="grid grid-cols-1 gap-4 text-sm md:grid-cols-3">
                                <div>
                                    <p className="text-slate-400">Costo Total Anual</p>
                                    <p className="mt-1 text-xl font-bold">{formatCurrency(trueCostAnalysis.annualCost, currency)}</p>
                                    <p className="mt-1 text-xs text-slate-500">Nómina + cargas sociales</p>
                                </div>
                                <div>
                                    <p className="text-slate-400">Horas Facturables/Año</p>
                                    <p className="mt-1 text-xl font-bold">{trueCostAnalysis.annualBillableHours.toLocaleString()} h</p>
                                    <p className="mt-1 text-xs text-slate-500">Después de días no productivos</p>
                                </div>
                                <div className="rounded-xl border border-white/10 bg-white/10 p-4">
                                    <p className="text-xs font-bold uppercase tracking-wide text-blue-200">Costo por Hora (BCR)</p>
                                    <p className="mt-1 text-3xl font-black text-white">{formatCurrency(Math.round(displayedBcr), currency)}</p>
                                    <p className="mt-1 text-xs text-slate-300">
                                        {backendBcrLoading ? 'Sincronizando con motor central...' : 'Mínimo para no perder dinero'}
                                    </p>
                                </div>
                            </div>
                        </CardContent>
                    </Card>

                    <Alert variant="warning" className="bg-amber-50 border-amber-200">
                        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                            <p className="text-sm text-amber-900">
                                Para un BCR preciso, registra todos los miembros del equipo en nómina.
                                {payrollHeadcount > 1
                                    ? ` Actualmente estás modelando ${modeledMembers.length} de ${payrollHeadcount}.`
                                    : ' Actualmente estás modelando 1 persona.'}
                            </p>
                            <label className="flex shrink-0 items-center gap-2 text-xs font-semibold text-amber-900">
                                Personas esperadas
                                <Input
                                    type="number"
                                    min={1}
                                    value={payrollHeadcount}
                                    onChange={(event) => setPayrollHeadcount(Math.max(1, Number(event.target.value) || 1))}
                                    className="h-8 w-20 bg-white"
                                />
                            </label>
                        </div>
                    </Alert>
                </div>
            </div>

            <div className="pb-24 md:pb-0">
                <div className="fixed inset-x-0 bottom-0 z-40 md:static md:z-auto border-t border-gray-200 bg-white/95 backdrop-blur-md px-4 pt-3 pb-[max(0.75rem,env(safe-area-inset-bottom))] md:border-0 md:bg-transparent md:backdrop-blur-none md:p-0 shadow-[0_-6px_24px_rgba(15,23,42,0.06)] md:shadow-none">
                    <div className="max-w-5xl mx-auto flex gap-3 justify-between mt-0 md:mt-6">
                        <Button variant="secondary" onClick={onBack} className="flex-1 sm:flex-none h-12 rounded-2xl font-bold md:h-10 md:rounded-md">
                            ← Atrás
                        </Button>
                        <Button onClick={handleNext} className="flex-1 sm:flex-none h-12 rounded-2xl font-bold md:h-10 md:rounded-md">
                            Siguiente →
                        </Button>
                    </div>
                </div>
            </div>

        </div>
    );
}
