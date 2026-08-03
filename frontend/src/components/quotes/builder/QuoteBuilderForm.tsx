
'use client';

import React from 'react';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { useQuoteBuilder, PRICE_BELOW_COST_ERROR } from '@/context/QuoteBuilderContext';
import { QuoteItemRow } from './QuoteItemRow';
import { ContingencySection } from './ContingencySection';
import { ClientSelector } from './ClientSelector';
import { AddItemMenu, ItemType } from './AddItemMenu';
import { VendorItemRow } from './VendorItemRow';
import { useRouter } from 'next/navigation';
import { PaywallModal } from '@/components/billing/PaywallModal';
import { Check, AlertTriangle } from 'lucide-react';
import { cn } from '@/lib/utils';

interface SectionHeaderProps {
    step: number;
    title: string;
    subtitle: string;
    complete: boolean;
    current: boolean;
}

function SectionHeader({ step, title, subtitle, complete, current }: SectionHeaderProps) {
    return (
        <div className="mb-5 flex items-start gap-3.5">
            <div className={cn(
                'mt-0.5 flex h-[26px] w-[26px] shrink-0 items-center justify-center rounded-full border-[1.5px] text-[11px] font-semibold',
                complete
                    ? 'border-success bg-success text-white'
                    : current
                    ? 'border-primary bg-primary/10 text-primary'
                    : 'border-gray-300 bg-white text-gray-400'
            )}>
                {complete ? <Check size={13} strokeWidth={2.5} /> : step}
            </div>
            <div>
                <h2 className="text-[19px] font-semibold leading-tight tracking-tight text-gray-900">{title}</h2>
                <p className="mt-0.5 text-[13px] text-gray-500">{subtitle}</p>
            </div>
        </div>
    );
}

export function QuoteBuilderForm() {
    const {
        state, services, updateProjectInfo, addItem, addExpense,
        errors, paywall, clearPaywall,
    } = useQuoteBuilder();
    const router = useRouter();

    const normalizeOptionalText = (value: unknown): string => {
        if (typeof value !== 'string') return '';
        const trimmed = value.trim();
        if (!trimmed || trimmed.toLowerCase() === 'undefined' || trimmed.toLowerCase() === 'null') return '';
        return trimmed;
    };

    const handleAddItem = (type: ItemType) => {
        if (type === 'vendor') {
            addExpense({
                name: `Proveedor ${state.expenses.length + 1}`,
                vendorName: '',
                cost: 0,
                markupPercentage: 0.10,
                quantity: 1,
                category: 'vendor',
            });
            return;
        }
        const pricingTypeMap: Record<Exclude<ItemType, 'vendor'>, 'hourly' | 'fixed' | 'recurring'> = {
            hourly: 'hourly',
            fixed: 'fixed',
            recurring: 'recurring',
        };
        const targetPricingType = pricingTypeMap[type];
        const candidateService =
            services.find(s => s.pricingType === targetPricingType && s.isActive) ||
            services.find(s => s.isActive);
        if (!candidateService) return;
        // Título vacío a propósito: antes se autocompletaba con etiquetas genéricas
        // ("Por horas 1") que quedaban guardadas tal cual en la cotización.
        addItem(candidateService.id, '', targetPricingType);
    };

    const hasProjectName = typeof state.projectName === 'string' && state.projectName.trim().length > 0;
    const hasClient = Boolean(
        state.clientId ||
        (typeof state.clientCompany === 'string' && state.clientCompany.trim().length > 0) ||
        (typeof state.clientName === 'string' && state.clientName.trim().length > 0)
    );
    const hasItems = state.items.length > 0 || state.expenses.length > 0;
    const currentFlowStepId = !hasProjectName || !hasClient ? 1 : !hasItems ? 2 : 3;

    const step1Done = hasProjectName && hasClient;
    const step2Done = hasItems;

    return (
        <>
        <div className="space-y-8 pb-6 lg:pb-12">

            {/* ── Step 1: Project Info ── */}
            <section id="quote-step-project-info">
                <SectionHeader
                    step={1}
                    title="Información general"
                    subtitle="Define los detalles clave del proyecto y el cliente."
                    complete={step1Done}
                    current={currentFlowStepId === 1}
                />
                <div className="rounded-xl border border-gray-200 bg-white shadow-sm overflow-hidden">
                    <div className="p-6 space-y-5">
                        <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
                            <div className="space-y-1.5">
                                <label className="text-[12px] font-semibold text-gray-600">
                                    Nombre del proyecto <span className="text-primary">*</span>
                                </label>
                                <Input
                                    placeholder="Ej: Rediseño Ecommerce 2026"
                                    value={state.projectName || ''}
                                    onChange={e => updateProjectInfo({ projectName: e.target.value })}
                                    className="h-9 bg-white"
                                />
                            </div>
                            <div className="space-y-1.5">
                                <label className="text-[12px] font-semibold text-gray-600">
                                    Cliente <span className="text-primary">*</span>
                                </label>
                                <ClientSelector
                                    value={normalizeOptionalText(state.clientCompany) || normalizeOptionalText(state.clientName)}
                                    clientId={state.clientId ?? undefined}
                                    onChange={(clientId, name, email, company, requester) =>
                                        updateProjectInfo({
                                            clientId: clientId ?? undefined,
                                            clientName: normalizeOptionalText(name),
                                            clientEmail: normalizeOptionalText(email),
                                            clientCompany: normalizeOptionalText(company) || normalizeOptionalText(name),
                                            clientRequester: normalizeOptionalText(requester),
                                        })
                                    }
                                />
                            </div>
                        </div>

                        <div className="space-y-1.5">
                            <label className="text-[12px] font-semibold text-gray-600">
                                Descripción de la solicitud
                                <span className="ml-2 text-[11px] font-normal text-gray-400">· Contexto y objetivos</span>
                            </label>
                            <textarea
                                className="flex min-h-[80px] w-full rounded-lg border border-gray-200 bg-white px-3 py-2.5 text-sm text-gray-900 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all resize-y"
                                placeholder="Describe el alcance, objetivos y requerimientos específicos del proyecto."
                                rows={3}
                                value={state.projectDescription || ''}
                                onChange={e => updateProjectInfo({ projectDescription: e.target.value })}
                            />
                        </div>
                    </div>
                </div>
            </section>

            {/* ── Step 2: Items ── */}
            <section id="quote-step-estimation">
                <SectionHeader
                    step={2}
                    title="Ítems de cotización"
                    subtitle="Elige una modalidad y agrega los servicios del proyecto."
                    complete={step2Done}
                    current={currentFlowStepId === 2}
                />

                {state.items.length === 0 && state.expenses.length === 0 ? (
                    <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
                        <p className="mb-4 text-[13px] font-semibold text-gray-700">Agregar primer ítem</p>
                        <p className="mb-4 text-[12px] text-gray-400">Selecciona la modalidad de cobro para empezar.</p>
                        {services.length === 0 && (
                            <p className="mb-4 text-xs text-amber-600 bg-warning-soft border border-yellow-200 rounded-lg px-3 py-2">
                                No hay servicios activos configurados. Ve a{' '}
                                <a href="/admin/taxes" className="font-semibold underline">Configuración</a>{' '}
                                para agregar servicios.
                            </p>
                        )}
                        <AddItemMenu onAdd={handleAddItem} />
                    </div>
                ) : (
                    <div className="space-y-3">
                        {state.items.map((item, idx) => (
                            <QuoteItemRow key={item.id} item={item} index={idx} />
                        ))}
                        {state.expenses.map(expense => (
                            <VendorItemRow key={expense.id} expense={expense} />
                        ))}

                        {/* Agregar otro */}
                        <div className="rounded-xl border border-dashed border-gray-200 bg-white p-4">
                            <p className="mb-3 text-[11.5px] font-semibold uppercase tracking-wide text-gray-400">
                                Agregar otro ítem
                            </p>
                            <AddItemMenu onAdd={handleAddItem} />
                        </div>
                    </div>
                )}
            </section>

            {/* ── Contingency ── */}
            <ContingencySection />

            {/* ── Validation Errors ── */}
            {errors.length > 0 && (hasProjectName || hasItems) && (
                <div className="flex items-start gap-3 rounded-xl border border-yellow-200 bg-warning-soft px-4 py-3.5">
                    <AlertTriangle size={15} className="mt-0.5 shrink-0 text-warning" />
                    <div>
                        {/* No todos los errores son campos vacíos (el precio bajo costo no lo es),
                            así que el título no puede prometer que se resuelven completando datos. */}
                        <p className="text-[12.5px] font-semibold text-amber-700">
                            {errors.length === 1
                                ? 'Queda algo por resolver antes de crear la propuesta'
                                : `Quedan ${errors.length} cosas por resolver antes de crear la propuesta`}
                        </p>
                        <p className="mt-1 text-[12px] text-gray-600">{errors.join(' · ')}</p>
                        {errors.includes(PRICE_BELOW_COST_ERROR) && (
                            <label className="mt-2.5 flex items-start gap-2 text-[12px] text-gray-700">
                                <input
                                    type="checkbox"
                                    className="mt-0.5 h-3.5 w-3.5 shrink-0 accent-amber-600"
                                    checked={state.allowLowMargin}
                                    onChange={e => updateProjectInfo({ allowLowMargin: e.target.checked })}
                                />
                                <span>
                                    Vender por debajo del costo a propósito.
                                    <span className="text-gray-500"> Marcá esto si la decisión es intencional
                                    (piloto, cliente estratégico) y querés crear la propuesta igual.</span>
                                </span>
                            </label>
                        )}
                    </div>
                </div>
            )}
        </div>

        <PaywallModal
            isOpen={paywall.open}
            onClose={clearPaywall}
            reason={paywall.reason}
            data={paywall.reason === 'credits_insufficient' ? {
                availableCredits: paywall.data?.availableCredits,
                requiredCredits: paywall.data?.requiredCredits,
            } : undefined}
            onUpgrade={() => { clearPaywall(); router.push('/billing'); }}
        />
        </>
    );
}
