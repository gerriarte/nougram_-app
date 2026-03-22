
'use client';

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { useQuoteBuilder } from '@/context/QuoteBuilderContext';
import { QuoteItemRow } from './QuoteItemRow';
import { ContingencySection } from './ContingencySection';
import { ClientSelector } from './ClientSelector';
import { useRouter } from 'next/navigation';
import { PaywallModal } from '@/components/billing/PaywallModal';
import { QuoteFlowStepper } from '@/components/quotes/QuoteFlowStepper';

const QUOTE_FLOW_STEPS = [
    { id: 1, title: 'Información general' },
    { id: 2, title: 'Tipo de cotización y costos' },
    { id: 3, title: 'Validación y propuesta' },
];

export function QuoteBuilderForm() {
    const { state, services, updateProjectInfo, addItem, isValid, errors, saveQuote, paywall, clearPaywall } = useQuoteBuilder();
    const router = useRouter();
    const [selectedBillingType, setSelectedBillingType] = React.useState<'' | 'hourly' | 'fixed' | 'recurring'>('');

    const handleSave = async (options?: { goToProposal?: boolean; goToDashboard?: boolean }) => {
        try {
            const projectId = await saveQuote();
            if (options?.goToProposal && projectId) {
                router.push(`/dashboard/quotes/${projectId}/proposal`);
            } else if (options?.goToDashboard) {
                router.push('/dashboard');
            }
        } catch (e) {
            const message = e instanceof Error ? e.message : 'Error guardando cotización';
            alert(message);
        }
    };

    const activeServices = React.useMemo(
        () => services.filter((service) => service.isActive),
        [services]
    );

    const normalizeOptionalText = (value: unknown): string => {
        if (typeof value !== 'string') return '';
        const trimmed = value.trim();
        if (!trimmed) return '';
        if (trimmed.toLowerCase() === 'undefined' || trimmed.toLowerCase() === 'null') return '';
        return trimmed;
    };

    const getBillingLabel = (pricingType: string) => {
        switch (pricingType) {
            case 'hourly':
                return 'Por hora';
            case 'recurring':
                return 'Fee mensual';
            case 'fixed':
            case 'project_value':
            default:
                return 'Precio fijo';
        }
    };

    const selectedBillingModes = Array.from(
        new Set(state.items.map((item) => getBillingLabel(item.pricingType)))
    );
    const servicesByBilling = React.useMemo(
        () => activeServices.filter((service) => {
            if (!selectedBillingType) return false;
            if (selectedBillingType === 'fixed') {
                return service.pricingType === 'fixed' || service.pricingType === 'project_value';
            }
            return service.pricingType === selectedBillingType;
        }),
        [activeServices, selectedBillingType]
    );
    const canAddByBillingType = selectedBillingType !== '' && servicesByBilling.length > 0;

    const addItemForBillingType = () => {
        if (!canAddByBillingType) return;
        const [candidateService] = servicesByBilling;
        if (!candidateService) return;
        addItem(candidateService.id);
    };

    const hasProjectName = typeof state.projectName === 'string' && state.projectName.trim().length > 0;
    const hasClient = Boolean(
        state.clientId ||
        (typeof state.clientCompany === 'string' && state.clientCompany.trim().length > 0) ||
        (typeof state.clientName === 'string' && state.clientName.trim().length > 0)
    );
    const hasItems = state.items.length > 0;
    const currentFlowStepId = !hasProjectName || !hasClient ? 1 : !hasItems ? 2 : 3;

    const stepSectionById: Record<number, string> = {
        1: 'quote-step-project-info',
        2: 'quote-step-estimation',
        3: 'quote-final-proposal-section',
    };

    const handleStepNavigation = (stepId: number) => {
        const targetId = stepSectionById[stepId];
        if (!targetId) return;
        const el = document.getElementById(targetId);
        if (!el) return;
        el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    };

    return (
        <>
        <div className="space-y-8 pb-12 max-w-5xl mx-auto">
            <QuoteFlowStepper
                className="sticky top-2 z-20 rounded-2xl border border-gray-200 bg-white/90 backdrop-blur p-3 shadow-sm"
                label="Flujo de cotización"
                steps={QUOTE_FLOW_STEPS}
                currentStepId={currentFlowStepId}
                onStepClick={handleStepNavigation}
            />
            {/* 1. Project Info */}
            <Card id="quote-step-project-info" className="overflow-hidden border-none shadow-xl bg-white/80 backdrop-blur-2xl">
                <CardHeader className="bg-gray-50/50 border-b border-gray-100 flex flex-row justify-between items-start">
                    <div>
                        <CardTitle className="text-xl">Información General</CardTitle>
                        <CardDescription>Define los detalles clave del proyecto y el cliente.</CardDescription>
                    </div>
                    {state.version && (
                        <div className="bg-blue-100 text-blue-700 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider">
                            Versión {state.version}
                        </div>
                    )}
                </CardHeader>
                <CardContent className="p-8 space-y-8">
                    {/* Top Row: Project Name & Client */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                        <div className="space-y-3">
                            <label className="text-sm font-semibold text-gray-700">Nombre del Proyecto</label>
                            <Input
                                placeholder="Ej: Rediseño Ecommerce 2026"
                                value={state.projectName || ''}
                                onChange={e => updateProjectInfo({ projectName: e.target.value })}
                                className="bg-white"
                            />
                        </div>
                        <div className="space-y-3">
                            <label className="text-sm font-semibold text-gray-700">Cliente</label>
                            <ClientSelector
                                value={normalizeOptionalText(state.clientCompany) || normalizeOptionalText(state.clientName)}
                                clientId={state.clientId ?? undefined}
                                onChange={(clientId, name, email, company, requester) => updateProjectInfo({
                                    clientId: clientId ?? undefined,
                                    clientName: normalizeOptionalText(name),
                                    clientEmail: normalizeOptionalText(email),
                                    clientCompany: normalizeOptionalText(company) || normalizeOptionalText(name),
                                    clientRequester: normalizeOptionalText(requester)
                                })}
                            />
                        </div>
                    </div>

                    {/* Project Brief for AI */}
                    <div className="space-y-3">
                        <label className="text-sm font-semibold text-gray-700">
                            Descripción de la Solicitud
                            <span className="ml-2 text-xs font-normal text-gray-400 bg-gray-100 px-2 py-0.5 rounded-full">Para IA</span>
                        </label>
                        <textarea
                            className="flex min-h-[120px] w-full rounded-xl border border-transparent bg-gray-100/50 px-4 py-3 text-sm text-gray-900 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:bg-white transition-all resize-y"
                            placeholder="Describe el alcance, objetivos y requerimientos específicos del proyecto. Esta información ayudará a la IA a generar una propuesta más precisa."
                            value={state.projectDescription}
                            onChange={e => updateProjectInfo({ projectDescription: e.target.value })}
                        />
                        <p className="text-xs text-gray-500">
                            Este brief alimenta la generación de la propuesta comercial en el siguiente paso luego de cotizar.
                        </p>
                    </div>
                </CardContent>
            </Card>

            {/* 2. Billing Type Manager */}
            <div id="quote-step-estimation" className="space-y-6">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div>
                        <h2 className="text-2xl font-bold text-gray-900 tracking-tight">Tipo de cotización</h2>
                        <p className="text-gray-500 text-sm">Selecciona la modalidad de cobro y agrega los servicios correspondientes.</p>
                        {selectedBillingModes.length > 0 && (
                            <div className="mt-2 flex flex-wrap gap-2">
                                {selectedBillingModes.map((mode) => (
                                    <span key={mode} className="rounded-full border border-gray-200 bg-white px-2.5 py-1 text-[11px] font-semibold text-gray-600">
                                        {mode}
                                    </span>
                                ))}
                            </div>
                        )}
                    </div>

                    {/* Quick Add Selector */}
                    <div className="flex w-full md:w-auto gap-2">
                        <select
                            className="h-9 min-w-[190px] rounded-md border border-gray-200 bg-white px-3 text-sm text-gray-700"
                            value={selectedBillingType}
                            onChange={(e) => {
                                const nextType = e.target.value as '' | 'hourly' | 'fixed' | 'recurring';
                                setSelectedBillingType(nextType);
                            }}
                        >
                            <option value="">Tipo de cotización</option>
                            <option value="hourly">Por hora</option>
                            <option value="fixed">Precio fijo</option>
                            <option value="recurring">Fee mensual</option>
                        </select>
                    </div>
                </div>
                <div className="rounded-xl border border-dashed border-gray-200 bg-white/70 p-3">
                    {!selectedBillingType ? (
                        <p className="text-xs text-gray-500">Primero elige el tipo de cotización para habilitar la creación del ítem.</p>
                    ) : servicesByBilling.length === 0 ? (
                        <p className="text-xs text-gray-500">No hay servicios configurados para este tipo de cotización.</p>
                    ) : (
                        <div className="flex items-center justify-between gap-3">
                            <p className="text-xs text-gray-500">
                                Tipo seleccionado: <span className="font-semibold text-gray-700">{getBillingLabel(selectedBillingType)}</span>.
                                El ítem se crea directamente sin elegir servicio.
                            </p>
                            <Button
                                size="sm"
                                type="button"
                                variant="secondary"
                                disabled={!canAddByBillingType}
                                onClick={addItemForBillingType}
                                className="bg-white shadow-sm border-gray-200 hover:bg-gray-50 whitespace-nowrap"
                            >
                                + Agregar ítem
                            </Button>
                        </div>
                    )}
                </div>

                {state.items.length === 0 ? (
                    <div className="border border-dashed border-gray-300 rounded-2xl p-12 text-center bg-gray-50/50">
                        <div className="mx-auto w-12 h-12 bg-white rounded-full flex items-center justify-center shadow-sm mb-4">
                            <PlusIcon className="text-gray-400" />
                        </div>
                        <h3 className="text-lg font-medium text-gray-900">No has agregado ítems de cotización</h3>
                        <p className="text-sm text-gray-500 mt-1">Selecciona el tipo de cotización y agrega servicios para comenzar la estimación.</p>
                    </div>
                ) : (
                    <div className="space-y-4">
                        {state.items.map(item => {
                            return <QuoteItemRow key={item.id} item={item} />;
                        })}
                    </div>
                )}
            </div>

            {/* 3. Contingency Module */}
            <ContingencySection />

            {/* 4. Validation Errors */}
            {errors.length > 0 && (
                <div className="bg-red-50/50 backdrop-blur-sm border border-red-100 p-6 rounded-2xl text-red-800 text-sm shadow-sm space-y-2">
                    <div className="flex items-center gap-2 font-bold text-red-900">
                        <AlertCircle className="w-5 h-5" />
                        No se puede guardar:
                    </div>
                    <ul className="list-disc list-inside space-y-1 ml-1 text-red-700/80">
                        {errors.map((err, i) => <li key={i}>{err}</li>)}
                    </ul>
                </div>
            )}

            {/* 4. Actions */}
            <div className="sticky bottom-4 z-30" id="quote-final-proposal-section">
                <div className="max-w-5xl mx-auto flex gap-3 justify-end rounded-2xl border border-gray-200 bg-white/95 backdrop-blur-xl shadow-lg p-3">
                    <Button variant="secondary" onClick={() => handleSave({ goToDashboard: true })} className="w-full sm:w-auto">
                        Guardar
                    </Button>
                    <Button
                        variant="ghost"
                        onClick={() => (state.id ? router.push('/dashboard') : router.back())}
                        className="w-full sm:w-auto"
                    >
                        Cancelar
                    </Button>
                    <Button
                        className={`w-full sm:w-auto ${isValid ? 'bg-blue-600 hover:bg-blue-700 text-white shadow-lg shadow-blue-500/20' : 'bg-gray-100 text-gray-400 cursor-not-allowed'}`}
                        disabled={!isValid}
                        onClick={() => handleSave({ goToProposal: true })}
                    >
                        Crear propuesta
                    </Button>
                </div>
            </div>
        </div>

        <PaywallModal
            isOpen={paywall.open}
            onClose={clearPaywall}
            reason={paywall.reason}
            data={paywall.reason === 'credits_insufficient' ? {
                availableCredits: paywall.data?.availableCredits,
                requiredCredits: paywall.data?.requiredCredits,
            } : undefined}
            onUpgrade={() => {
                clearPaywall();
                router.push('/billing');
            }}
        />
        </>
    );
}

function PlusIcon({ className }: { className?: string }) {
    return (
        <svg className={className} width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 5V19M5 12H19" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
    )
}

function AlertCircle({ className }: { className?: string }) {
    return (
        <svg className={className} width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
        </svg>
    )
}
