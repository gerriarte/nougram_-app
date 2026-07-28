
'use client';

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { useNougram } from '@/context/NougramCoreContext';
import {
    QuoteBuilderState, QuoteItem, QuoteExpense, TaxConfig, CalculationSummary,
    PricingType, Service, Contingency, TeamMemberMock, ResourceAllocation
} from '@/types/quote-builder';
import { taxService } from '@/services/taxService';

import { resourceService } from '@/services/resourceService';
import { CreditsRequiredError } from '@/lib/errors';
import type { PaywallReason } from '@/components/billing/PaywallModal';
import { getQuoteEditorMeta, saveQuoteEditorMeta } from '@/lib/quote-editor-meta';
import { trackQuoteCreated, trackQuoteSaved } from '@/lib/analytics';
import { formatDisplayNumber } from '@/lib/utils';

// --- INITIAL STATE ---
const INITIAL_STATE: QuoteBuilderState = {
    step: 'editor',
    projectName: '',
    clientName: '',
    clientCompany: '',
    clientRequester: '',
    clientEmail: '',
    projectType: '',
    projectDescription: '',
    currency: 'COP',
    items: [],
    expenses: [],
    selectedTaxIds: [],
    targetMargin: 0.35, // Default margin
    allowLowMargin: false,
    showResourceAllocation: false,
    resourceAllocations: []
};

const PROJECT_TYPES = [
    'Desarrollo Web',
    'Diseño UI/UX',
    'Marketing Digital',
    'Consultoría',
    'Desarrollo de Software',
    'Branding',
    'Otro',
];

function normalizeOptionalText(value: unknown): string {
    if (typeof value !== 'string') return '';
    const trimmed = value.trim();
    if (!trimmed) return '';
    if (trimmed.toLowerCase() === 'undefined' || trimmed.toLowerCase() === 'null') return '';
    return trimmed;
}

/**
 * Marca interna del builder: el ítem fue creado en ESTA sesión de edición (addItem).
 *
 * Es una marca explícita puesta al crear el ítem, no una inferencia sobre la forma
 * del id: los ítems que vuelven de `loadQuote` nunca la traen, así que quedan
 * exentos de las validaciones que solo aplican a lo nuevo (ver H14). Vive fuera de
 * `QuoteItem` a propósito — es estado de UI, no parte del contrato con el backend,
 * y `mapQuoteItemToApi` copia campo por campo, así que nunca se envía.
 */
type BuilderQuoteItem = QuoteItem & { __createdInSession?: true };

export function markItemAsCreatedInSession(item: QuoteItem): QuoteItem {
    const marked: BuilderQuoteItem = { ...item, __createdInSession: true };
    return marked;
}

export function isItemCreatedInSession(item: QuoteItem): boolean {
    return (item as BuilderQuoteItem).__createdInSession === true;
}

/**
 * Utilización de un miembro dentro de esta cotización (función pura).
 *
 * Las asignaciones viven en `item.allocations` (una por ítem). El array legacy
 * `state.resourceAllocations` quedó sin UI que lo alimente, así que se suma
 * también para no romper flujos viejos, pero la fuente real son los ítems.
 *
 * `member.availableHours` es capacidad MENSUAL (billable_hours_per_week × 4.33).
 * En los ítems recurrentes las horas ya son por mes, pero en los one-off son el
 * TOTAL del ítem y no hay dato de en cuántos meses se ejecuta (`durationMonths`
 * solo se setea en recurring). Por eso el porcentaje resultante es orientativo:
 * se lee como "qué porcentaje de un mes de capacidad consume si todo cayera en
 * el mismo mes", y por eso mismo no puede bloquear el guardado (ver H13).
 */
export function computeMemberUtilization(
    memberId: number,
    state: Pick<QuoteBuilderState, 'items' | 'resourceAllocations'>,
    teamMembers: TeamMemberMock[]
): { capacity: number; used: number; percentage: number; remaining: number } {
    const member = teamMembers.find(m => m.id === memberId);
    if (!member) return { capacity: 0, used: 0, percentage: 0, remaining: 0 };

    const itemAllocations: ResourceAllocation[] = (state.items || []).flatMap(item =>
        (item.allocations || []).filter(a => a.teamMemberId === memberId)
    );

    return resourceService.calculateUtilization(member, [
        ...(state.resourceAllocations || []).filter(a => a.teamMemberId === memberId),
        ...itemAllocations,
    ]);
}

export interface QuoteBuilderValidation {
    /** Bloquean el guardado (apagan `isValid`). */
    errors: string[];
    /** Informativas: se muestran, pero NO bloquean el guardado. */
    warnings: string[];
}

/**
 * Validación del builder, pura y testeable.
 *
 * Regla de alcance (H14): la descripción del ítem es obligatoria SOLO para los
 * ítems creados en esta sesión. Una cotización vieja — cuyos ítems nunca tuvieron
 * `description` porque la columna es nueva — se tiene que poder re-guardar (p. ej.
 * para cambiar el estado a 'Won') sin tipear a mano el alcance de cada ítem viejo.
 * El aviso visual por ítem (QuoteItemRow) se sigue mostrando igual.
 *
 * Sobreasignación de recursos (H13): es una ADVERTENCIA, no un error. Compara
 * horas totales del ítem contra capacidad mensual (ver computeMemberUtilization),
 * así que un ítem one-off repartido en varios meses da falso positivo; bloquear el
 * guardado con eso dejaba al usuario sin ninguna vía de escape.
 */
export function computeQuoteBuilderValidation(input: {
    state: QuoteBuilderState;
    summary: Pick<CalculationSummary, 'totalClientPrice' | 'totalInternalCost'>;
    teamMembers: TeamMemberMock[];
}): QuoteBuilderValidation {
    const { state, summary, teamMembers } = input;
    const errors: string[] = [];
    const warnings: string[] = [];

    if (!normalizeOptionalText(state.projectName)) errors.push('Nombre del proyecto requerido');
    const hasClientForSave =
        Boolean(normalizeOptionalText(state.clientName)) ||
        Boolean(normalizeOptionalText(state.clientCompany));
    if (!hasClientForSave) errors.push('Cliente requerido');
    if (state.items.length === 0) errors.push('Al menos un ítem de servicio requerido (gastos de proveedor no bastan)');

    // Título y alcance por ítem: sin esto la cotización no se entiende al revisarla.
    const itemsMissingTitle = state.items.filter(i => !normalizeOptionalText(i.serviceName)).length;
    if (itemsMissingTitle > 0) {
        errors.push(
            itemsMissingTitle === 1
                ? 'Un ítem sin título'
                : `${itemsMissingTitle} ítems sin título`
        );
    }
    const itemsMissingDescription = state.items.filter(
        i => isItemCreatedInSession(i) && !normalizeOptionalText(i.description)
    ).length;
    if (itemsMissingDescription > 0) {
        errors.push(
            itemsMissingDescription === 1
                ? 'Un ítem nuevo sin descripción del alcance'
                : `${itemsMissingDescription} ítems nuevos sin descripción del alcance`
        );
    }
    if (summary.totalClientPrice < summary.totalInternalCost && !state.allowLowMargin) {
        errors.push('CRITICAL: Price below Cost');
    }

    const allocatedMemberIds = Array.from(new Set([
        ...(state.resourceAllocations || []).map(a => a.teamMemberId),
        ...state.items.flatMap(item => (item.allocations || []).map(a => a.teamMemberId)),
    ]));
    allocatedMemberIds.forEach(memberId => {
        const member = teamMembers.find(m => m.id === memberId);
        if (!member) return;
        const util = computeMemberUtilization(memberId, state, teamMembers);
        // Sin capacidad conocida no se puede afirmar que haya sobreasignación.
        if (util.capacity <= 0 || util.percentage <= 100) return;
        const pct = formatDisplayNumber(util.percentage, { minimumFractionDigits: 1, maximumFractionDigits: 1 });
        const used = formatDisplayNumber(util.used, { maximumFractionDigits: 1 });
        const capacity = formatDisplayNumber(util.capacity, { maximumFractionDigits: 1 });
        warnings.push(
            `${member.name} quedaría al ${pct}% de un mes de capacidad: ${used} h sobre ${capacity} h disponibles por mes. ` +
            `Si el trabajo se reparte en varios meses puede estar bien; si no, reducí sus horas o repartí el trabajo entre otros recursos.`
        );
    });

    return { errors, warnings };
}

interface QuoteBuilderContextType {
    state: QuoteBuilderState;
    services: Service[];
    taxes: TaxConfig[];
    teamMembers: import('@/types/quote-builder').TeamMemberMock[];

    // Actions
    updateProjectInfo: (info: Partial<QuoteBuilderState>) => void;

    addItem: (serviceId: number, serviceNameOverride?: string, pricingTypeOverride?: PricingType) => void;
    updateItem: (itemId: string, updates: Partial<QuoteItem>) => void;
    removeItem: (itemId: string) => void;

    addExpense: (expense: Omit<QuoteExpense, 'id' | 'clientPrice'>) => void;
    updateExpense: (expenseId: string, updates: Partial<QuoteExpense>) => void;
    removeExpense: (expenseId: string) => void;

    toggleTax: (taxId: number) => void;
    setTargetMargin: (margin: number) => void;
    setContingency: (contingency: Contingency | undefined) => void;

    // Resource Allocation Actions
    toggleResourceAllocation: () => void;
    addResourceAllocation: (allocation: import('@/types/quote-builder').ResourceAllocation) => void;
    updateResourceAllocation: (id: string, updates: Partial<import('@/types/quote-builder').ResourceAllocation>) => void;
    removeResourceAllocation: (id: string) => void;
    getMemberUtilization: (memberId: number) => { capacity: number, used: number, percentage: number, remaining: number };

    // Outputs
    summary: CalculationSummary;
    isValid: boolean;
    errors: string[];
    /** Avisos que NO bloquean el guardado (p. ej. sobreasignación de recursos). */
    warnings: string[];

    /** `null` = paywall de créditos abierto (no navegar). `undefined` = salida temprana sin guardar. */
    saveQuote: (status?: 'Draft' | 'Sent' | 'Won' | 'Lost') => Promise<string | null | undefined>;
    loadQuote: (id: string) => Promise<void>;

    /** 402 / credits paywall: show PaywallModal when reason is set */
    paywall: { open: boolean; reason: PaywallReason; data?: { availableCredits?: number; requiredCredits?: number } };
    clearPaywall: () => void;
}

const QuoteBuilderContext = createContext<QuoteBuilderContextType | undefined>(undefined);

export function QuoteBuilderProvider({ children }: { children: React.ReactNode }) {
    const { state: coreState } = useNougram();
    const [state, setState] = useState<QuoteBuilderState>(INITIAL_STATE);
    const [services, setServices] = useState<Service[]>([]);
    const [taxes, setTaxes] = useState<TaxConfig[]>([]);
    const [teamMembers, setTeamMembers] = useState<import('@/types/quote-builder').TeamMemberMock[]>([]); // Load from service
    const [summary, setSummary] = useState<CalculationSummary>({
        totalInternalCost: 0, totalClientPrice: 0, totalTaxes: 0, totalWithTaxes: 0, netMarginAmount: 0, netMarginPercent: 0, realIncome: 0,
        contingencyAmount: 0, contingencyTotal: 0,
        expensesInternalCost: 0, expensesClientPrice: 0,
    });
    const [paywall, setPaywall] = useState<{
        open: boolean;
        reason: PaywallReason;
        data?: { availableCredits?: number; requiredCredits?: number };
    }>({ open: false, reason: 'credits_insufficient' });
    const clearPaywall = useCallback(() => setPaywall((p) => ({ ...p, open: false })), []);

    // --- LOAD RESOURCES ---
    useEffect(() => {
        resourceService.getAllMembers().then(setTeamMembers);
        const loadTaxes = async () => {
            try {
                const country = coreState.identity.country;
                const byCountry = await taxService.getAll({ activeOnly: true, country });
                if (byCountry.length > 0) {
                    setTaxes(byCountry);
                    return;
                }
                const globalTaxes = await taxService.getAll(true);
                setTaxes(globalTaxes);
            } catch {
                setTaxes([]);
            }
        };
        void loadTaxes();
        import('@/services/quoteService').then(({ quoteService }) => {
            quoteService.getAvailableServices().then((available) => {
                if (available.length > 0) setServices(available);
            }).catch(() => {
                setServices([]);
            });
        });
    }, [coreState.identity.country]);

    // Keep new quotes aligned with organization primary currency.
    useEffect(() => {
        const orgCurrency = (coreState.identity.primaryCurrency || 'COP') as QuoteBuilderState['currency'];
        setState((prev) => {
            if (prev.id) return prev;
            if (prev.currency === orgCurrency) return prev;
            return { ...prev, currency: orgCurrency };
        });
    }, [coreState.identity.primaryCurrency]);

    // --- CALCULATION ENGINE ---
    // Fuente de verdad: el BACKEND. El frontend NO calcula precios; envía los inputs
    // a POST /quotes/calculate (con debounce) y renderiza lo que devuelve.

    // Normalize selected taxes against the loaded (real) taxes.
    useEffect(() => {
        if (!state.selectedTaxIds.length) return;
        const activeTaxIds = new Set(
            (taxes || [])
                .filter((tax) => tax.isActive !== false)
                .map((tax) => tax.id)
        );
        const normalizedTaxIds = state.selectedTaxIds.filter((taxId) => activeTaxIds.has(taxId));
        if (normalizedTaxIds.length !== state.selectedTaxIds.length) {
            setState((prev) => ({ ...prev, selectedTaxIds: normalizedTaxIds }));
        }
    }, [taxes, state.selectedTaxIds]);

    // Signature of the pricing INPUTS only, so writing the backend results back to
    // the items does not retrigger the effect (avoids an infinite recompute loop).
    const itemsInputSignature = JSON.stringify(
        state.items.map(i => ({
            id: i.id, s: i.serviceId, p: i.pricingType, f: i.fixedPrice, q: i.quantity,
            r: i.recurringPrice, b: i.billingFrequency, v: i.projectValue,
            d: i.durationMonths, e: i.estimatedHours,
            // manualPrice es un INPUT: sin él acá, editar "Precio cliente" no
            // retriggerea el recálculo y el subtotal queda congelado.
            m: i.manualPrice,
            a: (i.allocations || []).map(x => [x.teamMemberId, x.hours]),
        }))
    );
    const expensesSignature = JSON.stringify(
        (state.expenses || []).map(e => [e.cost, e.markupPercentage, e.quantity])
    );
    const contingencySignature = state.contingency ? `${state.contingency.type}:${state.contingency.value}` : '';
    const taxSignature = (state.selectedTaxIds || []).join(',');

    useEffect(() => {
        if (state.items.length === 0 && (state.expenses || []).length === 0) {
            setSummary({
                totalInternalCost: 0, totalClientPrice: 0, totalTaxes: 0, totalWithTaxes: 0,
                netMarginAmount: 0, netMarginPercent: 0, realIncome: 0,
                contingencyAmount: 0, contingencyTotal: 0,
                expensesInternalCost: 0, expensesClientPrice: 0,
            });
            return;
        }
        let cancelled = false;
        const handle = setTimeout(async () => {
            try {
                const { quoteService } = await import('@/services/quoteService');
                const { summary: backendSummary, itemsById } = await quoteService.calculate({
                    items: state.items,
                    expenses: state.expenses,
                    selectedTaxIds: state.selectedTaxIds,
                    targetMargin: state.targetMargin,
                    contingency: state.contingency,
                });
                if (cancelled) return;
                setSummary(backendSummary);
                setState(prev => ({
                    ...prev,
                    items: prev.items.map(item => {
                        const calc = itemsById[item.id];
                        return calc
                            ? { ...item, internalCost: calc.internalCost, clientPrice: calc.clientPrice, marginPercentage: calc.marginPercentage }
                            : item;
                    }),
                }));
            } catch (err) {
                if (!cancelled) console.error('Error calculando cotización en backend', err);
            }
        }, 350);
        return () => { cancelled = true; clearTimeout(handle); };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [itemsInputSignature, expensesSignature, taxSignature, state.targetMargin, contingencySignature]);

    // --- RESOURCE ALLOCATION HELPERS ---
    /** Ver computeMemberUtilization: misma lógica, atada al estado del builder. */
    const getMemberUtilization = (memberId: number) =>
        computeMemberUtilization(memberId, state, teamMembers);

    // --- ACTIONS ---
    const updateProjectInfo = (info: Partial<QuoteBuilderState>) =>
        setState((prev) => ({
            ...prev,
            ...info,
            currency: (coreState.identity.primaryCurrency || prev.currency) as QuoteBuilderState['currency'],
        }));

    const addItem = (serviceId: number, serviceNameOverride?: string, pricingTypeOverride?: PricingType) => {
        const service = services.find(s => s.id === serviceId);
        if (!service) return;
        // Un override explícito manda, incluso vacío: el builder crea el ítem sin
        // título para forzar que el usuario escriba uno propio en vez de heredar
        // una etiqueta genérica. Sin override se usa el nombre del catálogo.
        const normalizedServiceName =
            serviceNameOverride !== undefined
                ? normalizeOptionalText(serviceNameOverride)
                : service.name;
        const effectivePricingType: PricingType = pricingTypeOverride || service.pricingType;

        const newItem: QuoteItem = {
            id: crypto.randomUUID(),
            serviceId: service.id,
            serviceName: normalizedServiceName,
            pricingType: effectivePricingType,
            quantity: 1,
            estimatedHours: effectivePricingType === 'hourly' ? 10 : undefined,
            fixedPrice: effectivePricingType === 'fixed' ? 1000000 : undefined,
            projectValue: effectivePricingType === 'project_value' ? 5000000 : undefined,
            recurringPrice: effectivePricingType === 'recurring' ? 0 : undefined,
            durationMonths: effectivePricingType === 'recurring' ? 1 : undefined, // Default 1 month
            allocations: [], // Start empty as per unified logic

            // Placeholders; the backend calculation effect fills these in.
            internalCost: 0, clientPrice: 0, marginPercentage: 0
        };

        // Marca explícita de "creado en esta sesión": solo estos ítems exigen alcance.
        setState(prev => ({ ...prev, items: [...prev.items, markItemAsCreatedInSession(newItem)] }));
    };

    const updateItem = (itemId: string, updates: Partial<QuoteItem>) => {
        // No client-side pricing: just merge inputs; the backend effect recalculates.
        setState(prev => ({
            ...prev,
            items: prev.items.map(i => (i.id === itemId ? { ...i, ...updates } : i)),
        }));
    };

    const removeItem = (itemId: string) =>
        setState(prev => ({ ...prev, items: prev.items.filter(i => i.id !== itemId) }));

    const addExpense = (expense: Omit<QuoteExpense, 'id' | 'clientPrice'>) =>
        setState(prev => ({
            ...prev,
            expenses: [...prev.expenses, {
                ...expense,
                id: crypto.randomUUID(),
                clientPrice: expense.cost * expense.quantity * (1 + expense.markupPercentage),
            }],
        }));

    const updateExpense = (expenseId: string, updates: Partial<QuoteExpense>) =>
        setState(prev => ({
            ...prev,
            expenses: prev.expenses.map(e =>
                e.id === expenseId
                    ? { ...e, ...updates, clientPrice: (updates.cost ?? e.cost) * (updates.quantity ?? e.quantity) * (1 + (updates.markupPercentage ?? e.markupPercentage)) }
                    : e
            ),
        }));

    const removeExpense = (expenseId: string) =>
        setState(prev => ({ ...prev, expenses: prev.expenses.filter(e => e.id !== expenseId) }));

    const toggleTax = (taxId: number) =>
        setState(prev => {
            const exists = prev.selectedTaxIds.includes(taxId);
            return {
                ...prev,
                selectedTaxIds: exists
                    ? prev.selectedTaxIds.filter(id => id !== taxId)
                    : [...prev.selectedTaxIds, taxId]
            };
        });

    const toggleResourceAllocation = () => setState(prev => ({ ...prev, showResourceAllocation: !prev.showResourceAllocation }));

    const addResourceAllocation = (allocation: import('@/types/quote-builder').ResourceAllocation) =>
        setState(prev => ({ ...prev, resourceAllocations: [...prev.resourceAllocations, allocation] }));

    const updateResourceAllocation = (id: string, updates: Partial<import('@/types/quote-builder').ResourceAllocation>) =>
        setState(prev => ({ ...prev, resourceAllocations: prev.resourceAllocations.map(a => a.id === id ? { ...a, ...updates } : a) }));

    const removeResourceAllocation = (id: string) =>
        setState(prev => ({ ...prev, resourceAllocations: prev.resourceAllocations.filter(a => a.id !== id) }));


    // No client-side pricing: just set the target; the backend effect recalculates.
    const setTargetMargin = (margin: number) =>
        setState((prev) => ({ ...prev, targetMargin: margin }));
    const setContingency = (contingency: Contingency | undefined) => setState(prev => ({ ...prev, contingency }));

    // --- VALIDATION ---
    const { errors, warnings } = computeQuoteBuilderValidation({ state, summary, teamMembers });

    // --- PERSISTENCE ---
    const saveQuote = async (status?: 'Draft' | 'Sent' | 'Won' | 'Lost') => {
        const { quoteService } = await import('@/services/quoteService');
        const activeTaxIds = new Set(
            (taxes || [])
                .filter((tax) => tax.isActive !== false)
                .map((tax) => tax.id)
        );
        const sanitizedTaxIds = (state.selectedTaxIds || []).filter((taxId) => activeTaxIds.has(taxId));

        const payload = {
            projectName: state.projectName,
            clientId: state.clientId ?? undefined,
            clientName:
                normalizeOptionalText(state.clientName) ||
                normalizeOptionalText(state.clientCompany) ||
                state.clientName,
            clientEmail: state.clientEmail,
            selectedTaxIds: sanitizedTaxIds,
            amount: summary.totalClientPrice,
            currency: (coreState.identity.primaryCurrency || state.currency),
            marginPercentage: summary.netMarginPercent,
            targetMargin: state.targetMargin,
            contingency: state.contingency,
            items: state.items,
            expenses: state.expenses.map(e => ({
                name: e.name,
                description: e.vendorName,
                cost: String(e.cost),
                markup_percentage: String(e.markupPercentage),
                quantity: String(e.quantity),
                category: e.category,
            })),
        };

        if (state.items.length === 0) return undefined;

        try {
            if (state.id) {
                const currentQuote = await quoteService.getById(state.id);
                if (currentQuote && currentQuote.status !== 'draft') {
                    await quoteService.createVersion(state.id, payload as any);
                    alert('Nueva versión creada (V' + (currentQuote.version + 1) + ')');
                } else {
                    await quoteService.update(state.id, payload as any);
                }
                if (status) {
                    await quoteService.setProjectStatus(state.id, status);
                }
                saveQuoteEditorMeta(state.id, {
                    projectType: state.projectType,
                    projectDescription: state.projectDescription,
                });
                trackQuoteSaved({
                    project_id: state.id,
                    quote_id: currentQuote?.quoteId != null ? String(currentQuote.quoteId) : undefined,
                });
                return state.id;
            } else {
                const newProjectId = await quoteService.create(payload as any);
                setState(prev => ({ ...prev, id: newProjectId, version: 1 }));
                if (status) {
                    await quoteService.setProjectStatus(newProjectId, status);
                }
                saveQuoteEditorMeta(newProjectId, {
                    projectType: state.projectType,
                    projectDescription: state.projectDescription,
                });
                trackQuoteCreated({ project_id: newProjectId });
                trackQuoteSaved({ project_id: newProjectId });
                return newProjectId;
            }
        } catch (err) {
            if (err instanceof CreditsRequiredError) {
                setPaywall({
                    open: true,
                    reason: 'credits_insufficient',
                    data: {
                        availableCredits: err.availableCredits,
                        requiredCredits: err.requiredCredits ?? 1,
                    },
                });
                return null;
            }
            throw err;
        }
    };

    const loadQuote = useCallback(async (id: string) => {
        const { quoteService } = await import('@/services/quoteService');
        const q = await quoteService.getBuilderData(id);
        if (q) {
            setTaxes((prevTaxes) => {
                const next = [...prevTaxes];
                for (const selectedTax of q.selectedTaxes || []) {
                    if (!next.some((tax) => tax.id === selectedTax.id)) {
                        next.push(selectedTax);
                    }
                }
                return next;
            });
            const persistedMeta = getQuoteEditorMeta(q.id);
            const inferredProjectType = (() => {
                const firstNamedItem = (q.items || []).find((item) => typeof item.serviceName === 'string' && item.serviceName.includes(' - '));
                if (!firstNamedItem?.serviceName) return '';
                const [prefix] = firstNamedItem.serviceName.split(' - ');
                return PROJECT_TYPES.includes(prefix) ? prefix : '';
            })();

            setState(() => ({
                ...INITIAL_STATE,
                step: 'editor',
                id: q.id,
                version: q.version,
                projectName: normalizeOptionalText(q.projectName),
                clientId: q.clientId ?? undefined,
                clientName: normalizeOptionalText(q.clientName),
                clientEmail: normalizeOptionalText(q.clientEmail),
                clientCompany: normalizeOptionalText(q.clientCompany) || normalizeOptionalText(q.clientName),
                clientRequester: normalizeOptionalText(q.clientRequester),
                projectType: persistedMeta.projectType || inferredProjectType,
                projectDescription: persistedMeta.projectDescription || '',
                currency: (coreState.identity.primaryCurrency || q.currency || 'COP') as QuoteBuilderState['currency'],
                targetMargin: typeof q.targetMargin === 'number' && Number.isFinite(q.targetMargin)
                    ? q.targetMargin
                    : INITIAL_STATE.targetMargin,
                selectedTaxIds: q.selectedTaxIds || [],
                contingency: q.contingency,
                items: q.items || [],
                expenses: q.expenses || [],
            }));
        }
    }, []);

    return (
        <QuoteBuilderContext.Provider value={{
            state, services, taxes, teamMembers,
            updateProjectInfo, addItem, updateItem, removeItem,
            addExpense, updateExpense, removeExpense,
            toggleTax, setTargetMargin, setContingency,
            toggleResourceAllocation, addResourceAllocation, updateResourceAllocation, removeResourceAllocation, getMemberUtilization,
            summary, isValid: errors.length === 0, errors, warnings,
            saveQuote, loadQuote,
            paywall, clearPaywall,
        }}>
            {children}
        </QuoteBuilderContext.Provider>
    );
}

export const useQuoteBuilder = () => {
    const context = useContext(QuoteBuilderContext);
    if (!context) throw new Error('useQuoteBuilder must be used within QuoteBuilderProvider');
    return context;
};
