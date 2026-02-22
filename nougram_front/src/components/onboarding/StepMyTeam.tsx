
import React, { useState, useEffect } from 'react';
import { Card, CardContent } from '../ui/Card';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { Label } from '../ui/Label';
import { Badge } from '../ui/Badge';
import { Alert } from '../ui/Alert';
import { onboardingService } from '@/services/onboardingService';
import { Step3MyTeamData } from '@/types/onboarding';

interface StepMyTeamProps {
    onNext: (data: Step3MyTeamData) => void;
    onBack: () => void;
    initialData?: Step3MyTeamData;
    currency: string;
}


const ROLES = [
    'Diseñador UI/UX',
    'Desarrollador Frontend',
    'Desarrollador Backend',
    'Product Manager',
    'CEO/Founder',
    'Otro'
];

const LEVELS = ['Junior', 'Mid', 'Senior'];

export function StepMyTeam({ onNext, onBack, initialData, currency }: StepMyTeamProps) {
    // Member Info
    const [name, setName] = useState(initialData?.name || '');
    const [role, setRole] = useState(initialData?.role || '');
    const [level, setLevel] = useState<Step3MyTeamData['level']>(initialData?.level || '');
    const [salary, setSalary] = useState<string>(initialData?.salary?.toString() || '');

    // Reality Calculator
    const [totalHours, setTotalHours] = useState<number>(initialData?.totalHours || 40);
    const [billableHours, setBillableHours] = useState<number>(initialData?.billableHours || 28);

    // Annual Calculation Defaults
    const [vacationDays, setVacationDays] = useState<number>(initialData?.vacationDays || 20);

    // Social Charges
    const [applySocialCharges, setApplySocialCharges] = useState<boolean>(initialData?.applySocialCharges ?? true);

    // Calculations
    const nonBillableHours = totalHours - billableHours;
    const salaryNum = parseFloat(salary) || 0;

    // Social Charges Math (Colombia Defaults)
    const SOCIAL_CHARGES_RATE = 0.52852; // ~52.8%
    const salaryWithCharges = applySocialCharges ? salaryNum * (1 + SOCIAL_CHARGES_RATE) : salaryNum;

    // True Cost Calculation (Live)
    const trueCostAnalysis = onboardingService.calculateTrueHourlyCost(
        salaryWithCharges,
        billableHours,
        vacationDays
    );

    // Validation Status
    const minSalary = onboardingService.getMarketSalaryThreshold(role, level, currency);
    const isSalaryLow = minSalary && salaryNum < minSalary;

    const handleTotalHoursChange = (val: string) => {
        const hours = parseInt(val) || 0;
        setTotalHours(hours);
        // Default logic: ~70% billable
        setBillableHours(Math.floor(hours * 0.7));
    };

    const handleNext = () => {
        if (!name || !role || !level || !salary) return; // Basic validation

        onNext({
            name,
            role,
            level,
            salary: salaryNum,
            totalHours,
            billableHours,
            vacationDays,
            applySocialCharges,
            yearlyBillableHours: trueCostAnalysis.annualBillableHours,
            hourlyCost: trueCostAnalysis.hourlyCost
        });
    };

    return (
        <div className="space-y-6 max-w-3xl mx-auto">
            <div className="text-center space-y-2">
                <h1 className="text-2xl font-bold text-gray-900">Configura tu propio costo</h1>
                <p className="text-gray-600">Calcula cuánto te cuesta realmente tu hora de trabajo.</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

                {/* 1. Personal Details */}
                <Card className="md:col-span-2">
                    <CardContent className="space-y-4 pt-6">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label>Tu Nombre *</Label>
                                <Input value={name} onChange={e => setName(e.target.value)} placeholder="Ej: Juan Pérez" />
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-2">
                                    <Label>Tu Rol *</Label>
                                    <select
                                        className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                                        value={role}
                                        onChange={e => setRole(e.target.value)}
                                    >
                                        <option value="">Seleccionar...</option>
                                        {ROLES.map(r => <option key={r} value={r}>{r}</option>)}
                                    </select>
                                </div>
                                <div className="space-y-2">
                                    <Label>Nivel *</Label>
                                    <select
                                        className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                                        value={level}
                                        onChange={e => setLevel(e.target.value as any)}
                                    >
                                        <option value="">Seleccionar...</option>
                                        {LEVELS.map(l => <option key={l} value={l}>{l}</option>)}
                                    </select>
                                </div>
                            </div>
                        </div>

                        <div className="space-y-2">
                            <Label>Salario Mensual Bruto ({currency}) *</Label>
                            <Input
                                type="number"
                                value={salary}
                                onChange={e => setSalary(e.target.value)}
                                placeholder="0"
                            />
                            {isSalaryLow && (
                                <Alert variant="warning" className="bg-amber-50 border-amber-200">
                                    <p className="text-sm text-amber-800">
                                        ⚠️ <strong>Validación de Mercado:</strong> Tu salario parece bajo para un {role} {level}.
                                        El promedio es ~${minSalary?.toLocaleString()} {currency}.
                                    </p>
                                </Alert>
                            )}
                        </div>
                    </CardContent>
                </Card>

                {/* 2. Reality Calculator */}
                <Card className="bg-blue-50/30 border-blue-100">
                    <CardContent className="space-y-4 pt-6">
                        <div className="flex items-center gap-2">
                            <span className="text-xl">📊</span>
                            <h3 className="font-semibold text-gray-900">Calculadora de Realidad</h3>
                        </div>

                        <div className="space-y-2">
                            <Label>Horas Totales / Semana</Label>
                            <Input type="number" value={totalHours} onChange={e => handleTotalHoursChange(e.target.value)} />
                        </div>

                        <div className="p-3 bg-white rounded border border-blue-200 space-y-2">
                            <div className="flex justify-between items-center">
                                <span className="text-sm font-medium text-gray-700">Horas Facturables</span>
                                <span className="text-lg font-bold text-blue-600">{billableHours}h</span>
                            </div>
                            <Input
                                type="range"
                                min="0"
                                max={totalHours}
                                value={billableHours}
                                onChange={e => setBillableHours(parseInt(e.target.value))}
                                className="w-full"
                            />
                            <p className="text-xs text-gray-500">
                                Las {nonBillableHours} horas restantes de la semana se usan en reuniones, admin y capacitación.
                            </p>
                        </div>

                        <div className="space-y-2 pt-2">
                            <Label>Días No Productivos / Año</Label>
                            <Input
                                type="number"
                                value={vacationDays}
                                onChange={e => setVacationDays(parseInt(e.target.value))}
                            />
                            <p className="text-xs text-gray-500">Vacaciones, enfermedad, festivos (Default: 20 días)</p>
                        </div>
                    </CardContent>
                </Card>

                {/* 3. Social Charges */}
                <Card>
                    <CardContent className="space-y-4 pt-6">
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                                <span className="text-xl">🔧</span>
                                <h3 className="font-semibold text-gray-900">Cargas Sociales</h3>
                            </div>
                            <input
                                type="checkbox"
                                checked={applySocialCharges}
                                onChange={e => setApplySocialCharges(e.target.checked)}
                                className="h-5 w-5 text-blue-600 rounded"
                            />
                        </div>

                        {applySocialCharges ? (
                            <div className="space-y-3 text-sm">
                                <div className="flex justify-between">
                                    <span className="text-gray-600">Salario Base:</span>
                                    <span>${salaryNum.toLocaleString()}</span>
                                </div>
                                <div className="border-t border-dashed my-2"></div>
                                <div className="space-y-1 text-gray-500 text-xs">
                                    <div className="flex justify-between"><span>Salud (8.5%)</span><span>+${(salaryNum * 0.085).toLocaleString()}</span></div>
                                    <div className="flex justify-between"><span>Pensión (12%)</span><span>+${(salaryNum * 0.12).toLocaleString()}</span></div>
                                    <div className="flex justify-between"><span>Prestaciones (~21%)</span><span>+${(salaryNum * 0.2185).toLocaleString()}</span></div>
                                </div>
                                <div className="border-t border-gray-200 pt-2 flex justify-between font-bold text-gray-900">
                                    <span>Total con Cargas:</span>
                                    <span>${salaryWithCharges.toLocaleString()}</span>
                                </div>
                                <Badge variant="info" className="w-full justify-center">Multiplicador: ~1.53x</Badge>
                            </div>
                        ) : (
                            <p className="text-sm text-gray-500 italic">
                                Habilita esta opción si estás en Colombia para calcular parafiscales y prestaciones de ley automáticamente.
                            </p>
                        )}
                    </CardContent>
                </Card>

                {/* 4. True Hourly Cost Summary (NEW) */}
                <Card className="md:col-span-2 bg-slate-900 text-white border-slate-800">
                    <CardContent className="space-y-4 pt-6">
                        <div className="flex items-center gap-2 text-blue-400">
                            <span className="text-xl">💎</span>
                            <h3 className="font-semibold">Tu Costo Real por Hora (Calculado Anualmente)</h3>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-sm">
                            <div className="space-y-1">
                                <p className="text-slate-400">Costo Total Anual</p>
                                <p className="text-xl font-bold">${trueCostAnalysis.annualCost.toLocaleString()}</p>
                                <p className="text-xs text-slate-500">12 meses x ${salaryWithCharges.toLocaleString()}</p>
                            </div>

                            <div className="space-y-1">
                                <p className="text-slate-400">Horas Facturables/Año</p>
                                <p className="text-xl font-bold">{trueCostAnalysis.annualBillableHours.toLocaleString()} h</p>
                                <p className="text-xs text-slate-500">{billableHours}h/sem x {(52 - vacationDays / 5).toFixed(1)} sem. productivas</p>
                            </div>

                            <div className="space-y-1 bg-white/10 p-3 rounded-lg border border-white/20">
                                <p className="text-blue-200 font-medium">Costo por Hora (BCR)</p>
                                <p className="text-2xl font-bold text-white">${Math.round(trueCostAnalysis.hourlyCost).toLocaleString()}</p>
                                <p className="text-xs text-slate-300">Base mínima para no perder dinero</p>
                            </div>
                        </div>

                        <div className="mt-2 p-2 bg-yellow-500/10 border border-yellow-500/20 rounded text-xs text-yellow-200">
                            ⚠️ Si solo calculáramos mensual ({salaryWithCharges.toLocaleString()} / {billableHours * 4.33}h),
                            tu BCR sería incorrecto (~${Math.round(salaryWithCharges / (billableHours * 4.33)).toLocaleString()}).
                            El cálculo anual es más preciso.
                        </div>
                    </CardContent>
                </Card>

            </div>

            <div className="flex justify-between mt-6">
                <Button variant="secondary" onClick={onBack}>← Atrás</Button>
                <Button onClick={handleNext}>Siguiente →</Button>
            </div>
        </div>
    );
}
