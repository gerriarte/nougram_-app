
import React, { useState } from 'react';
import { Card, CardContent } from '../ui/Card';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { toast } from 'sonner';

interface StepReadyProps {
    data: any;
    onPersistOnboarding: () => Promise<void>;
    onGoToDashboard: () => void;
    onCreateQuote: () => void;
}

export function StepReady({ data, onPersistOnboarding, onGoToDashboard, onCreateQuote }: StepReadyProps) {
    // Extract data
    const teamMembers = Array.isArray(data.team) ? data.team : [];
    const currency = data.identity.primaryCurrency;
    const monthlyFixedCosts = data.fixedCosts.totalMonthly;
    const monthlyPayroll = teamMembers.reduce((acc: number, member: any) => {
        const baseSalary = Number(member.salary || 0);
        const withCharges = member.applySocialCharges ? baseSalary * 1.52852 : baseSalary;
        return acc + withCharges;
    }, 0);
    const [isSaving, setIsSaving] = useState(false);
    const [isSaved, setIsSaved] = useState(false);
    const [saveError, setSaveError] = useState<string | null>(null);

    // Interactive State for "What-if" scenario
    const initialBillableHours = teamMembers.reduce((acc: number, member: any) => acc + Number(member.billableHours || 0), 0);
    const [billableHoursPerWeek, setBillableHoursPerWeek] = useState<number>(Math.max(1, initialBillableHours));

    // Initial constants
    const averageVacationDays = teamMembers.length > 0
        ? teamMembers.reduce((acc: number, member: any) => acc + Number(member.vacationDays || 0), 0) / teamMembers.length
        : 20;
    const vacationDays = averageVacationDays;
    const weeksPerYear = 52;
    const productiveWeeks = weeksPerYear - (vacationDays / 5);

    // Dynamic Calculation
    const annualPayroll = monthlyPayroll * 12;
    const annualFixedCosts = monthlyFixedCosts * 12;
    const totalAnnualCosts = annualPayroll + annualFixedCosts;

    const annualBillableHours = billableHoursPerWeek * productiveWeeks;

    const bcr = annualBillableHours > 0 ? (totalAnnualCosts / annualBillableHours) : 0;

    // Monthly Calculation (for comparison "The Wrong Way")
    const monthlyBillableHours = billableHoursPerWeek * 4.33;
    const totalMonthlyCosts = monthlyPayroll + monthlyFixedCosts;
    const bcrMonthlyWrong = monthlyBillableHours > 0 ? (totalMonthlyCosts / monthlyBillableHours) : 0;

    // Determine color based on hours (just for visual flair)
    const bcrColor = billableHoursPerWeek < 20 ? 'text-orange-600' : 'text-blue-700';

    const handleComplete = async (action: 'dashboard' | 'quote') => {
        if (isSaving || isSaved) return;
        setSaveError(null);
        setIsSaving(true);
        try {
            await onPersistOnboarding();
            setIsSaved(true);
            toast.success('Configuración inicial guardada');
            setIsSaving(false);
            await new Promise((resolve) => setTimeout(resolve, 1500));
            if (action === 'dashboard') {
                onGoToDashboard();
            } else {
                onCreateQuote();
            }
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'No fue posible guardar tu onboarding';
            setSaveError(errorMessage);
            toast.error(errorMessage);
            setIsSaving(false);
        }
    };

    return (
        <div className="space-y-8 max-w-3xl mx-auto text-center">

            <div className="space-y-2">
                <span className="text-4xl">🎉</span>
                <h1 className="text-3xl font-bold text-gray-900">¡Listo! Tu estructura de costos está configurada</h1>
                <p className="text-gray-600">
                    Este es tu BCR inicial: el costo mínimo por hora que debes cobrar para no perder dinero.
                </p>
            </div>

            {/* Main BCR Result */}
            <Card className="bg-blue-50 border-blue-200 shadow-md transform hover:scale-105 transition-transform duration-300">
                <CardContent className="py-10">
                    <p className="text-sm font-semibold text-blue-800 uppercase tracking-widest mb-2">Tu Costo por Hora Real (BCR)</p>
                    <h2 className={`text-6xl font-extrabold ${bcrColor} mb-2`}>
                        ${Math.round(bcr).toLocaleString()} <span className="text-2xl font-normal text-gray-500">{currency}</span>
                    </h2>
                    <p className="text-xs text-blue-600/80 font-medium">(Cálculo anual preciso)</p>
                </CardContent>
            </Card>

            {/* Interactive Slider Section */}
            <div className="bg-gray-50 p-6 rounded-xl border border-gray-200 text-left space-y-4">
                <div className="flex justify-between items-center mb-2">
                    <h3 className="font-semibold text-gray-900">⚡ Simulación en Tiempo Real</h3>
                    <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">Interactivo</span>
                </div>

                <p className="text-sm text-gray-600">
                    Ajusta tus horas facturables semanales y mira cómo cambia tu costo mínimo.
                    <br />
                    <span className="text-xs text-gray-500 italic">Si trabajas menos horas, tu costo por hora sube porque tienes menos tiempo para cubrir tus costos fijos.</span>
                </p>

                <div className="space-y-2 pt-2">
                    <div className="flex justify-between text-sm font-medium">
                        <span>15h</span>
                        <span className="text-blue-600 text-lg">{billableHoursPerWeek} horas / semana</span>
                        <span>40h</span>
                    </div>
                    <Input
                        type="range"
                        min="15"
                        max={Math.max(60, initialBillableHours + 20)}
                        step="1"
                        value={billableHoursPerWeek}
                        onChange={(e) => setBillableHoursPerWeek(parseInt(e.target.value))}
                        className="w-full accent-blue-600 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                    />
                </div>
            </div>

            {/* Breakdown & Education */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-left">
                <Card>
                    <CardContent className="pt-6 space-y-3">
                        <h4 className="font-semibold text-gray-900 border-b pb-2">📊 Desglose de Costos Anuales</h4>
                        <div className="flex justify-between text-sm">
                            <span className="text-gray-600">Nómina (+cargas):</span>
                            <span>${(annualPayroll).toLocaleString()}</span>
                        </div>
                        <div className="flex justify-between text-sm">
                            <span className="text-gray-600">Costos Fijos:</span>
                            <span>${(annualFixedCosts).toLocaleString()}</span>
                        </div>
                        <div className="flex justify-between text-sm font-bold pt-2 border-t text-gray-900">
                            <span>Total Anual:</span>
                            <span>${(totalAnnualCosts).toLocaleString()}</span>
                        </div>
                    </CardContent>
                </Card>

                <Card>
                    <CardContent className="pt-6 space-y-3">
                        <h4 className="font-semibold text-gray-900 border-b pb-2">💡 ¿Qué es el BCR?</h4>
                        <p className="text-sm text-gray-600">
                            El BCR (Blended Cost Rate) es tu costo por hora considerando salarios, cargas y costos fijos.
                            Te sirve como base para definir precios rentables en cada cotización.
                        </p>
                        <div className="bg-amber-50 p-2 rounded text-xs text-amber-800 border border-amber-100 mt-2">
                            Siguiente paso recomendado: completa y revisa todos tus costos operacionales en Admin
                            antes de emitir cotizaciones al cliente final.
                        </div>
                    </CardContent>
                </Card>
            </div>

            <Card className="border-indigo-200 bg-indigo-50">
                <CardContent className="pt-6 text-left space-y-2">
                    <h4 className="font-semibold text-indigo-900">Antes de crear una cotización</h4>
                    <p className="text-sm text-indigo-900">
                        1) Verifica que tu equipo esté completo.
                        <br />
                        2) Agrega todos los costos operacionales pendientes (software, servicios, overhead).
                        <br />
                        3) Usa este BCR como base para fijar precios y márgenes.
                    </p>
                </CardContent>
            </Card>

            {/* Final Actions */}
            <div className="flex flex-col sm:flex-row gap-4 pt-4 justify-center">
                <Button variant="secondary" onClick={() => void handleComplete('dashboard')} className="w-full sm:w-auto" disabled={isSaving || isSaved}>
                    Ir al Dashboard
                </Button>
                <Button size="lg" className="w-full sm:w-auto bg-blue-600 hover:bg-blue-700 shadow-lg" onClick={() => void handleComplete('quote')} disabled={isSaving || isSaved}>
                    Crear mi Primera Cotización →
                </Button>
            </div>
            {isSaving && (
                <p className="text-sm text-gray-500">Guardando configuración inicial...</p>
            )}
            {isSaved && (
                <p className="text-sm text-green-700">Configuración guardada con éxito. Redirigiendo...</p>
            )}
            {saveError && (
                <p className="text-sm text-red-600">{saveError}</p>
            )}
        </div>
    );
}
