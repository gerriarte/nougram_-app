
'use client';

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { useQuoteBuilder } from '@/context/QuoteBuilderContext';
import { QuoteItemRow } from './QuoteItemRow';
import { ContingencySection } from './ContingencySection';
import { ClientSelector } from './ClientSelector';
import { Briefcase, FileText, Globe, Lightbulb, Megaphone, Monitor, Palette, Repeat, Calculator } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { PaywallModal } from '@/components/billing/PaywallModal';

export function QuoteBuilderForm() {
    const { state, services, updateProjectInfo, addItem, summary, isValid, errors, saveQuote, paywall, clearPaywall } = useQuoteBuilder();
    const router = useRouter();
    const hourlyService = services.find((s) => s.pricingType === 'hourly');
    const fixedService = services.find((s) => s.pricingType === 'fixed');
    const recurringService = services.find((s) => s.pricingType === 'recurring');

    const handleSave = async (status: 'Draft' | 'Sent', continueToNextStep: boolean = false) => {
        if (!isValid && status === 'Sent') return;

        try {
            const projectId = await saveQuote(status);
            if (continueToNextStep && projectId) {
                router.push(`/dashboard/quotes/${projectId}/next-step`);
            } else {
                router.push('/dashboard');
            }
        } catch (e) {
            const message = e instanceof Error ? e.message : 'Error guardando cotización';
            alert(message);
        }
    };

    const inferProjectTypeIcon = (serviceName: string, pricingType?: string) => {
        const name = serviceName.toLowerCase();

        if (name.includes('marketing') || name.includes('ads') || name.includes('campa')) return Megaphone;
        if (name.includes('ux') || name.includes('ui') || name.includes('dise')) return Palette;
        if (name.includes('web')) return Globe;
        if (name.includes('software') || name.includes('app') || name.includes('sistema')) return Monitor;
        if (name.includes('brand') || name.includes('marca')) return Lightbulb;
        if (name.includes('consult')) return Briefcase;
        if (pricingType === 'recurring') return Repeat;
        if (pricingType === 'project_value' || pricingType === 'fixed') return Calculator;
        return FileText;
    };

    const projectTypeOptions = Array.from(
        services
            .filter((service) => service.isActive)
            .reduce((acc, service) => {
                if (!acc.has(service.name)) {
                    acc.set(service.name, {
                        value: service.name,
                        label: service.name,
                        icon: inferProjectTypeIcon(service.name, service.pricingType),
                    });
                }
                return acc;
            }, new Map<string, { value: string; label: string; icon: React.ComponentType<{ size?: number; className?: string }> }>())
            .values()
    );

    const normalizeOptionalText = (value: unknown): string => {
        if (typeof value !== 'string') return '';
        const trimmed = value.trim();
        if (!trimmed) return '';
        if (trimmed.toLowerCase() === 'undefined' || trimmed.toLowerCase() === 'null') return '';
        return trimmed;
    };

    const jumpToSection = (id: string) => {
        if (typeof window === 'undefined') return;
        const target = document.getElementById(id);
        if (target) target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    };

    return (
        <>
        <div className="space-y-8 pb-12 max-w-5xl mx-auto">
            <div className="sticky top-2 z-20 rounded-2xl border border-gray-200 bg-white/90 backdrop-blur p-3 shadow-sm">
                <p className="text-[10px] font-black text-gray-400 uppercase tracking-[0.2em] mb-2">Flujo de cotización</p>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                    <Button type="button" variant="secondary" className="justify-start" onClick={() => jumpToSection('quote-client-section')}>
                        1. Cliente
                    </Button>
                    <Button type="button" variant="secondary" className="justify-start" onClick={() => jumpToSection('quote-proposal-type-section')}>
                        2. Tipo de propuesta
                    </Button>
                    <Button type="button" variant="secondary" className="justify-start" onClick={() => jumpToSection('quote-final-proposal-summary')}>
                        3. Propuesta final
                    </Button>
                </div>
            </div>
            {/* 1. Project Info */}
            <Card className="overflow-hidden border-none shadow-xl bg-white/80 backdrop-blur-2xl">
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
                        <div className="space-y-3" id="quote-client-section">
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

                    {/* Middle Row: Project Type */}
                    <div className="space-y-3" id="quote-proposal-type-section">
                        <label className="text-sm font-semibold text-gray-700">Tipo de Proyecto</label>
                        <Input
                            placeholder="Escribe o ajusta el nombre del tipo de proyecto"
                            value={state.projectType || ''}
                            onChange={(e) => updateProjectInfo({ projectType: e.target.value })}
                            className="bg-white"
                        />
                        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
                            {projectTypeOptions.map((type) => {
                                const Icon = type.icon;
                                const isSelected = state.projectType === type.value;
                                return (
                                    <button
                                        key={type.value}
                                        onClick={() => updateProjectInfo({ projectType: type.value })}
                                        className={`
                                            flex flex-col items-center justify-center p-3 rounded-xl border transition-all duration-200
                                            ${isSelected
                                                ? 'bg-blue-50 border-blue-200 text-blue-700 shadow-sm ring-1 ring-blue-200'
                                                : 'bg-white border-gray-100 text-gray-500 hover:border-gray-200 hover:bg-gray-50'
                                            }
                                        `}
                                    >
                                        <Icon size={20} className={`mb-2 ${isSelected ? 'text-blue-600' : 'text-gray-400'}`} />
                                        <span className="text-xs font-medium text-center leading-tight">{type.label}</span>
                                    </button>
                                )
                            })}
                            {projectTypeOptions.length === 0 && (
                                <div className="col-span-full rounded-xl border border-dashed border-gray-200 p-4 text-xs text-gray-500">
                                    No hay servicios activos para sugerir tipos. Puedes escribir un tipo personalizado.
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Bottom Row: Description */}
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
                    </div>
                </CardContent>
            </Card>

            {/* 2. Items Manager */}
            <div className="space-y-6">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div>
                        <h2 className="text-2xl font-bold text-gray-900 tracking-tight">Servicios Incluidos</h2>
                        <p className="text-gray-500 text-sm">Define el alcance y costos del proyecto.</p>
                    </div>

                    {/* Quick Add Selector */}
                    <div className="flex flex-wrap gap-2">
                        <Button size="sm" variant="secondary" onClick={() => hourlyService && addItem(hourlyService.id)} disabled={!hourlyService} className="bg-white shadow-sm border-gray-200 hover:bg-gray-50">+ Horas</Button>
                        <Button size="sm" variant="secondary" onClick={() => fixedService && addItem(fixedService.id)} disabled={!fixedService} className="bg-white shadow-sm border-gray-200 hover:bg-gray-50">+ Fijo</Button>
                        <Button size="sm" variant="secondary" onClick={() => recurringService && addItem(recurringService.id)} disabled={!recurringService} className="bg-white shadow-sm border-gray-200 hover:bg-gray-50">+ Recurrente</Button>
                    </div>
                </div>

                {state.items.length === 0 ? (
                    <div className="border border-dashed border-gray-300 rounded-2xl p-12 text-center bg-gray-50/50">
                        <div className="mx-auto w-12 h-12 bg-white rounded-full flex items-center justify-center shadow-sm mb-4">
                            <PlusIcon className="text-gray-400" />
                        </div>
                        <h3 className="text-lg font-medium text-gray-900">No has agregado servicios</h3>
                        <p className="text-sm text-gray-500 mt-1">Selecciona una opción arriba para comenzar a construir la cotización.</p>
                    </div>
                ) : (
                    <div className="space-y-4">
                        {state.items.map(item => {
                            const service = services.find(s => s.id === item.serviceId) || {
                                id: item.serviceId,
                                name: item.serviceName || `Servicio ${item.serviceId}`,
                                pricingType: item.pricingType,
                                defaultMarginTarget: state.targetMargin || 0.35,
                                isActive: false,
                            };
                            return <QuoteItemRow key={item.id} item={item} service={service} />;
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
                    <Button
                        variant="ghost"
                        onClick={() => (state.id ? router.push('/dashboard') : router.back())}
                        className="w-full sm:w-auto"
                    >
                        {state.id ? 'Cancelar Edición' : 'Cancelar'}
                    </Button>
                    <Button variant="secondary" onClick={() => handleSave('Draft')} className="w-full sm:w-auto">
                        Guardar Borrador
                    </Button>
                    <Button
                        className={`w-full sm:w-auto ${isValid ? 'bg-blue-600 hover:bg-blue-700 text-white shadow-lg shadow-blue-500/20' : 'bg-gray-100 text-gray-400 cursor-not-allowed'}`}
                        disabled={!isValid}
                        onClick={() => handleSave('Draft', true)}
                    >
                        Guardar y Continuar
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
