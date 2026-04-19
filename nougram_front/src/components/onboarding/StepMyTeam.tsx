
import React, { useState } from 'react';
import { Card, CardContent } from '../ui/Card';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { Label } from '../ui/Label';
import { Alert } from '../ui/Alert';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '../ui/Dialog';
import { Step3MyTeamData } from '@/types/onboarding';
import { formatCurrency, formatLocalizedNumberInput, parseLocalizedNumberInput } from '@/lib/utils';

interface StepMyTeamProps {
    onNext: (data: Step3MyTeamData) => void;
    onBack: () => void;
    initialData?: Step3MyTeamData;
    currency: string;
    backendBcr?: number | null;
    backendBcrLoading?: boolean;
}


const ROLES = [
    'Diseñador UI/UX',
    'Desarrollador Frontend',
    'Desarrollador Backend',
    'Product Manager',
    'CEO/Founder'
];

const LEVELS = ['Junior', 'Mid', 'Senior'];

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

export function StepMyTeam({
    onNext,
    onBack,
    initialData,
    currency,
    backendBcr,
    backendBcrLoading
}: StepMyTeamProps) {
    const isCopCurrency = String(currency || '').toUpperCase() === 'COP';
    const moneyInputMode: 'numeric' | 'decimal' = isCopCurrency ? 'numeric' : 'decimal';
    const parseMoneyInput = (raw: string) => parseLocalizedNumberInput(raw, { allowDecimal: !isCopCurrency });
    const formatMoneyInput = (value: number | string | null | undefined) =>
        formatLocalizedNumberInput(value, { currencyCode: currency, maximumFractionDigits: isCopCurrency ? 0 : 2 });

    const [isTeamModalOpen, setIsTeamModalOpen] = useState(false);
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
            id: `member-${index + 1}`,
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

    // Calculations
    const salaryNum = parseMoneyInput(salary);

    // Social Charges Math (Colombia Defaults)
    const SOCIAL_CHARGES_RATE = 0.52852; // ~52.8%
    const selectedRole = isCustomRole ? customRole : role;

    const modeledMembers = [
        {
            name,
            role: selectedRole,
            level,
            salary: salaryNum,
            totalHours,
            billableHours,
            vacationDays,
            applySocialCharges,
        },
        ...additionalMembers.map((member) => ({
            name: member.name,
            role: member.role,
            level: member.level,
            salary: parseMoneyInput(member.salary),
            totalHours: member.totalHours,
            billableHours: member.billableHours,
            vacationDays: member.vacationDays,
            applySocialCharges: member.applySocialCharges,
        })),
    ].filter((member) => member.name && member.role && member.salary > 0 && member.billableHours > 0);

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
        setAdditionalMembers((prev) => [
            ...prev,
            {
                id: `member-${Date.now()}`,
                name: '',
                role: '',
                level: '',
                salary: '',
                totalHours: 40,
                billableHours: 28,
                vacationDays: 20,
                applySocialCharges: true,
            },
        ]);
    };

    const openTeamManager = (createDraft: boolean) => {
        if (createDraft) {
            addAdditionalMember();
        }
        setIsTeamModalOpen(true);
    };

    const updateAdditionalMember = (id: string, updates: Partial<TeamMemberDraft>) => {
        setAdditionalMembers((prev) => prev.map((member) => (member.id === id ? { ...member, ...updates } : member)));
    };

    const removeAdditionalMember = (id: string) => {
        setAdditionalMembers((prev) => prev.filter((member) => member.id !== id));
    };

    const validAdditionalMembers = additionalMembers.filter(
        (member) =>
            member.name.trim() &&
            member.role.trim() &&
            parseMoneyInput(member.salary) > 0 &&
            member.billableHours > 0
    );

    return (
        <div className="space-y-6 max-w-3xl mx-auto px-1">
            <div className="text-center space-y-2">
                <h1 className="text-xl sm:text-2xl font-bold text-gray-900">Configura tu propio costo</h1>
                <p className="text-sm sm:text-base text-gray-600">Gestiona toda la nómina desde un solo modal y calcula el BCR en tiempo real.</p>
            </div>

            <Card className="bg-amber-50 border-amber-200">
                <CardContent className="space-y-4 pt-6">
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                        <div>
                            <p className="text-sm font-semibold text-amber-900">Registro de equipo en nómina</p>
                            <p className="text-xs text-amber-800">
                                Todo el flujo de carga y edición de miembros está centralizado en el modal.
                            </p>
                        </div>
                        <div className="flex gap-2">
                            <Button type="button" variant="secondary" onClick={() => openTeamManager(false)} className="whitespace-nowrap">
                                Ver miembros
                            </Button>
                            <Button type="button" onClick={() => openTeamManager(true)} className="whitespace-nowrap">
                                + Agregar recurso
                            </Button>
                        </div>
                    </div>

                    <div className="space-y-2 max-w-xs">
                        <Label>Cantidad de personas en nómina</Label>
                        <Input
                            type="number"
                            min={1}
                            value={payrollHeadcount}
                            onChange={(e) => setPayrollHeadcount(Math.max(1, parseInt(e.target.value || '1', 10)))}
                        />
                    </div>

                    <Alert variant="warning" className="bg-amber-100 border-amber-200">
                        <p className="text-sm text-amber-900">
                            Para un BCR preciso, registra todos los miembros del equipo en nómina.
                            {payrollHeadcount > 1
                                ? ` Actualmente estas modelando ${modeledMembers.length} de ${payrollHeadcount}.`
                                : ' Actualmente estas modelando 1 persona.'}
                        </p>
                    </Alert>
                </CardContent>
            </Card>

            <Card>
                <CardContent className="space-y-3 pt-6">
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-sm">
                        <div>
                            <p className="text-xs uppercase tracking-wide text-gray-500">Modelados</p>
                            <p className="font-semibold text-gray-900">{modeledMembers.length}</p>
                        </div>
                        <div>
                            <p className="text-xs uppercase tracking-wide text-gray-500">Adicionales válidos</p>
                            <p className="font-semibold text-gray-900">{validAdditionalMembers.length}</p>
                        </div>
                        <div>
                            <p className="text-xs uppercase tracking-wide text-gray-500">Pendientes por registrar</p>
                            <p className="font-semibold text-gray-900">
                                {Math.max(payrollHeadcount - modeledMembers.length, 0)}
                            </p>
                        </div>
                    </div>

                    <div className="rounded-lg border border-blue-100 bg-primary-soft p-4">
                        <div className="flex items-center justify-between gap-3">
                            <p className="text-sm font-semibold text-blue-900">Miembros que se guardarán</p>
                            <span className="text-xs font-bold text-primary bg-white border border-primary-soft rounded-full px-2 py-0.5">
                                {modeledMembers.length} miembro(s)
                            </span>
                        </div>
                        {modeledMembers.length === 0 ? (
                            <p className="text-sm text-primary mt-2">
                                Agrega al menos un miembro válido (nombre, rol, salario y horas facturables) para continuar.
                            </p>
                        ) : (
                            <div className="mt-3 flex flex-wrap gap-2">
                                {modeledMembers.map((member, index) => (
                                    <span
                                        key={`${member.name}-${index}`}
                                        className="text-xs font-medium text-blue-800 bg-white border border-primary-soft rounded-full px-3 py-1"
                                    >
                                        {member.name} - {member.role}
                                    </span>
                                ))}
                            </div>
                        )}
                    </div>
                </CardContent>
            </Card>

            <Card className="bg-slate-900 text-white border-slate-800">
                <CardContent className="space-y-4 pt-6">
                    <div className="flex items-center gap-2 text-blue-400">
                        <span className="text-xl">💎</span>
                        <h3 className="font-semibold">Costo real por hora (BCR)</h3>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-sm">
                        <div className="space-y-1">
                            <p className="text-slate-400">Costo Total Anual</p>
                            <p className="text-xl font-bold">{formatCurrency(trueCostAnalysis.annualCost, currency)}</p>
                            <p className="text-xs text-slate-500">Incluye miembros modelados y cargas sociales</p>
                        </div>

                        <div className="space-y-1">
                            <p className="text-slate-400">Horas Facturables/Año</p>
                            <p className="text-xl font-bold">{trueCostAnalysis.annualBillableHours.toLocaleString()} h</p>
                            <p className="text-xs text-slate-500">Basado en horas facturables y días no productivos</p>
                        </div>

                        <div className="space-y-1 bg-white/10 p-3 rounded-lg border border-white/20">
                            <p className="text-blue-200 font-medium">Costo por Hora (BCR)</p>
                            <p className="text-2xl font-bold text-white">{formatCurrency(Math.round(displayedBcr), currency)}</p>
                            <p className="text-xs text-slate-300">
                                {backendBcrLoading ? 'Sincronizando con motor central...' : 'Base mínima para no perder dinero'}
                            </p>
                        </div>
                    </div>
                </CardContent>
            </Card>

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

            <Dialog open={isTeamModalOpen} onOpenChange={setIsTeamModalOpen}>
                <DialogContent className="max-w-4xl w-[95vw] h-[90vh] p-0 flex flex-col">
                    <div className="p-6 border-b border-gray-100">
                        <DialogHeader>
                            <DialogTitle>Miembros adicionales del equipo</DialogTitle>
                            <DialogDescription>
                                Agrega y edita aquí todos los miembros de nómina para mejorar la precisión del BCR.
                            </DialogDescription>
                        </DialogHeader>
                    </div>

                    <div className="p-6 min-h-0 flex-1 overflow-y-auto space-y-4">
                        <div className="rounded-lg border border-primary-soft bg-primary-soft p-4 space-y-3">
                            <div className="flex items-center justify-between">
                                <p className="text-sm font-semibold text-blue-900">Miembro principal (tú)</p>
                                <span className="text-xs font-medium text-primary bg-white border border-primary-soft rounded-full px-2 py-0.5">
                                    Obligatorio
                                </span>
                            </div>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                <div className="space-y-1">
                                    <Label className="text-xs font-semibold text-blue-900">Nombre</Label>
                                    <Input
                                        placeholder="Ej: Juan Pérez"
                                        value={name}
                                        onChange={(e) => setName(e.target.value)}
                                    />
                                    <p className="text-[11px] text-blue-800">Nombre completo del miembro de nómina.</p>
                                </div>
                                <div className="space-y-1">
                                    <Label className="text-xs font-semibold text-blue-900">Rol / Cargo</Label>
                                    <select
                                        className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                                        value={isCustomRole ? '__custom__' : role}
                                        onChange={(e) => {
                                            if (e.target.value === '__custom__') {
                                                setIsCustomRole(true);
                                                setRole('');
                                            } else {
                                                setIsCustomRole(false);
                                                setRole(e.target.value);
                                            }
                                        }}
                                    >
                                        <option value="">Rol/Cargo</option>
                                        {ROLES.map((r) => <option key={r} value={r}>{r}</option>)}
                                        <option value="__custom__">+ Crear nuevo rol/cargo</option>
                                    </select>
                                    {isCustomRole && (
                                        <Input
                                            value={customRole}
                                            onChange={(e) => setCustomRole(e.target.value)}
                                            placeholder="Rol personalizado"
                                        />
                                    )}
                                    <p className="text-[11px] text-blue-800">Función principal en el equipo (ej. PM, diseñador, dev).</p>
                                </div>
                                <div className="space-y-1">
                                    <Label className="text-xs font-semibold text-blue-900">Nivel</Label>
                                    <select
                                        className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                                        value={level}
                                        onChange={(e) => setLevel(e.target.value as Step3MyTeamData['level'])}
                                    >
                                        <option value="">Nivel</option>
                                        {LEVELS.map((lvl) => <option key={lvl} value={lvl}>{lvl}</option>)}
                                    </select>
                                    <p className="text-[11px] text-blue-800">Senioridad para contextualizar capacidades del perfil.</p>
                                </div>
                                <div className="space-y-1">
                                    <Label className="text-xs font-semibold text-blue-900">Salario mensual ({currency})</Label>
                                    <Input
                                        type="text"
                                        inputMode={moneyInputMode}
                                        placeholder={`Salario mensual (${currency})`}
                                        value={salary}
                                        onChange={(e) => {
                                            const next = e.target.value;
                                            if (!next.trim()) {
                                                setSalary('');
                                                return;
                                            }
                                            const parsed = parseMoneyInput(next);
                                            setSalary(formatMoneyInput(parsed));
                                        }}
                                    />
                                    <p className="text-[11px] text-blue-800">Costo mensual bruto antes de dividir por horas productivas.</p>
                                </div>
                                <div className="space-y-1">
                                    <Label className="text-xs font-semibold text-blue-900">Horas totales por semana</Label>
                                    <Input
                                        type="number"
                                        min={1}
                                        placeholder="Horas totales/semana"
                                        value={totalHours}
                                        onChange={(e) => handleTotalHoursChange(e.target.value)}
                                    />
                                    <p className="text-[11px] text-blue-800">Horas laborales semanales (facturables + no facturables).</p>
                                </div>
                                <div className="space-y-1">
                                    <Label className="text-xs font-semibold text-blue-900">Horas facturables por semana</Label>
                                    <Input
                                        type="number"
                                        min={1}
                                        placeholder="Horas facturables/semana"
                                        value={billableHours}
                                        onChange={(e) => setBillableHours(Math.max(1, parseInt(e.target.value || '1', 10)))}
                                    />
                                    <p className="text-[11px] text-blue-800">Horas que realmente se pueden cobrar a clientes.</p>
                                </div>
                                <div className="space-y-1">
                                    <Label className="text-xs font-semibold text-blue-900">Días no productivos al año</Label>
                                    <Input
                                        type="number"
                                        min={0}
                                        placeholder="Días no productivos/año"
                                        value={vacationDays}
                                        onChange={(e) => setVacationDays(Math.max(0, parseInt(e.target.value || '0', 10)))}
                                    />
                                    <p className="text-[11px] text-blue-800">Vacaciones, festivos, incapacidad u otros días sin facturación.</p>
                                </div>
                                <div className="space-y-1">
                                    <Label className="text-xs font-semibold text-blue-900">Cargas sociales</Label>
                                    <label className="flex items-center gap-2 text-sm text-gray-700">
                                        <input
                                            type="checkbox"
                                            checked={applySocialCharges}
                                            onChange={(e) => setApplySocialCharges(e.target.checked)}
                                            className="h-4 w-4 rounded"
                                        />
                                        Aplicar cargas sociales
                                    </label>
                                    <p className="text-[11px] text-blue-800">Suma parafiscales y prestaciones para un costo real más preciso.</p>
                                </div>
                            </div>
                        </div>

                        <div className="flex items-center justify-between">
                            <p className="text-sm text-gray-600">
                                Registrados: <strong>{validAdditionalMembers.length}</strong> de <strong>{Math.max(payrollHeadcount - 1, 0)}</strong> adicionales esperados.
                            </p>
                            <Button type="button" variant="secondary" onClick={addAdditionalMember}>
                                + Agregar miembro
                            </Button>
                        </div>

                        {additionalMembers.length === 0 && (
                            <div className="rounded-lg border border-dashed border-gray-300 bg-gray-50 p-6 text-center">
                                <p className="text-sm text-gray-600">No hay miembros adicionales todavía.</p>
                                <p className="text-xs text-gray-500 mt-1">Empieza agregando el siguiente miembro de nómina.</p>
                            </div>
                        )}

                        <div className="space-y-3">
                            {additionalMembers.map((member, idx) => (
                                <div key={member.id} className="rounded-lg border border-gray-200 p-4 space-y-3 bg-white">
                                    <div className="flex items-center justify-between">
                                        <p className="text-sm font-semibold text-gray-700">Miembro {idx + 2}</p>
                                        <Button
                                            type="button"
                                            variant="destructive"
                                            size="sm"
                                            onClick={() => removeAdditionalMember(member.id)}
                                        >
                                            Eliminar
                                        </Button>
                                    </div>
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                        <div className="space-y-1">
                                            <Label className="text-xs">Nombre</Label>
                                            <Input
                                                placeholder="Ej: Ana Torres"
                                                value={member.name}
                                                onChange={(e) => updateAdditionalMember(member.id, { name: e.target.value })}
                                            />
                                            <p className="text-[11px] text-gray-500">Nombre completo del miembro.</p>
                                        </div>
                                        <div className="space-y-1">
                                            <Label className="text-xs">Rol / Cargo</Label>
                                            <Input
                                                placeholder="Ej: Diseñador UI/UX"
                                                value={member.role}
                                                onChange={(e) => updateAdditionalMember(member.id, { role: e.target.value })}
                                            />
                                            <p className="text-[11px] text-gray-500">Responsabilidad principal del perfil.</p>
                                        </div>
                                        <div className="space-y-1">
                                            <Label className="text-xs">Nivel</Label>
                                            <select
                                                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                                                value={member.level}
                                                onChange={(e) => updateAdditionalMember(member.id, { level: e.target.value as TeamMemberDraft['level'] })}
                                            >
                                                <option value="">Nivel</option>
                                                {LEVELS.map((lvl) => (
                                                    <option key={lvl} value={lvl}>{lvl}</option>
                                                ))}
                                            </select>
                                            <p className="text-[11px] text-gray-500">Senioridad del miembro.</p>
                                        </div>
                                        <div className="space-y-1">
                                            <Label className="text-xs">Salario mensual ({currency})</Label>
                                            <Input
                                                type="text"
                                                inputMode={moneyInputMode}
                                                placeholder={`Salario mensual (${currency})`}
                                                value={member.salary}
                                                onChange={(e) => {
                                                    const next = e.target.value;
                                                    if (!next.trim()) {
                                                        updateAdditionalMember(member.id, { salary: '' });
                                                        return;
                                                    }
                                                    const parsed = parseMoneyInput(next);
                                                    updateAdditionalMember(member.id, {
                                                        salary: formatMoneyInput(parsed),
                                                    });
                                                }}
                                            />
                                            <p className="text-[11px] text-gray-500">Costo mensual bruto del perfil.</p>
                                        </div>
                                        <div className="space-y-1">
                                            <Label className="text-xs">Horas totales por semana</Label>
                                            <Input
                                                type="number"
                                                min={1}
                                                placeholder="Horas totales/semana"
                                                value={member.totalHours}
                                                onChange={(e) =>
                                                    updateAdditionalMember(member.id, {
                                                        totalHours: Math.max(1, parseInt(e.target.value || '1', 10)),
                                                    })
                                                }
                                            />
                                            <p className="text-[11px] text-gray-500">Horas laborales semanales totales.</p>
                                        </div>
                                        <div className="space-y-1">
                                            <Label className="text-xs">Horas facturables por semana</Label>
                                            <Input
                                                type="number"
                                                min={1}
                                                placeholder="Horas facturables/semana"
                                                value={member.billableHours}
                                                onChange={(e) =>
                                                    updateAdditionalMember(member.id, {
                                                        billableHours: Math.max(1, parseInt(e.target.value || '1', 10)),
                                                    })
                                                }
                                            />
                                            <p className="text-[11px] text-gray-500">Horas que sí se cobran a cliente.</p>
                                        </div>
                                        <div className="space-y-1">
                                            <Label className="text-xs">Días no productivos al año</Label>
                                            <Input
                                                type="number"
                                                min={0}
                                                placeholder="Días no productivos/año"
                                                value={member.vacationDays}
                                                onChange={(e) =>
                                                    updateAdditionalMember(member.id, {
                                                        vacationDays: Math.max(0, parseInt(e.target.value || '0', 10)),
                                                    })
                                                }
                                            />
                                            <p className="text-[11px] text-gray-500">Vacaciones/festivos/ausencias sin facturar.</p>
                                        </div>
                                        <div className="space-y-1">
                                            <Label className="text-xs">Cargas sociales</Label>
                                            <label className="flex items-center gap-2 text-sm text-gray-700">
                                                <input
                                                    type="checkbox"
                                                    checked={member.applySocialCharges}
                                                    onChange={(e) =>
                                                        updateAdditionalMember(member.id, {
                                                            applySocialCharges: e.target.checked,
                                                        })
                                                    }
                                                    className="h-4 w-4 rounded"
                                                />
                                                Aplicar cargas sociales
                                            </label>
                                            <p className="text-[11px] text-gray-500">Incluye prestaciones y parafiscales en el costo.</p>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    <DialogFooter className="p-4 border-t border-gray-100 bg-gray-50">
                        <Button type="button" variant="secondary" onClick={() => setIsTeamModalOpen(false)}>
                            Cerrar
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </div>
    );
}
