
'use client';

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { useNougram } from '@/context/NougramCoreContext';
import {
    QuoteBuilderState, QuoteItem, TaxConfig, CalculationSummary,
    PricingType, Service, Contingency
} from '@/types/quote-builder';
import { taxService } from '@/services/taxService';

import { resourceService } from '@/services/resourceService';
import { pricingService } from '@/services/pricingService';
import { CreditsRequiredError } from '@/lib/errors';
import type { PaywallReason } from '@/components/billing/PaywallModal';

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

const QUOTE_EDITOR_META_KEY = 'nougram_quote_editor_meta_v1';

type QuoteEditorMeta = {
    projectType?: string;
    projectDescription?: string;
};

function normalizeOptionalText(value: unknown): string {
    if (typeof value !== 'string') return '';
    const trimmed = value.trim();
    if (!trimmed) return '';
    if (trimmed.toLowerCase() === 'undefined' || trimmed.toLowerCase() === 'null') return '';
    return trimmed;
}

function saveQuoteEditorMeta(projectId: string, meta: QuoteEditorMeta) {
    if (typeof window === 'undefined' || !projectId) return;
    try {
        const raw = localStorage.getItem(QUOTE_EDITOR_META_KEY);
        const parsed: Record<string, QuoteEditorMeta> = raw ? JSON.parse(raw) : {};
        parsed[projectId] = {
            projectType: meta.projectType || '',
            projectDescription: meta.projectDescription || '',
        };
        localStorage.setItem(QUOTE_EDITOR_META_KEY, JSON.stringify(parsed));
    } catch {
        // Non-blocking persistence
    }
}

function getQuoteEditorMeta(projectId: string): QuoteEditorMeta {
    if (typeof window === 'undefined' || !projectId) return {};
    try {
        const raw = localStorage.getItem(QUOTE_EDITOR_META_KEY);
        if (!raw) return {};
        const parsed = JSON.parse(raw) as Record<string, QuoteEditorMeta>;
        return parsed[projectId] || {};
    } catch {
        return {};
    }
}

interface QuoteBuilderContextType {
    state: QuoteBuilderState;
    services: Service[];
    taxes: TaxConfig[];
    teamMembers: import('@/types/quote-builder').TeamMemberMock[];

    // Actions
    updateProjectInfo: (info: Partial<QuoteBuilderState>) => void;

    addItem: (serviceId: number) => void;
    updateItem: (itemId: string, updates: Partial<QuoteItem>) => void;
    removeItem: (itemId: string) => void;

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

    saveQuote: (status?: 'Draft' | 'Sent') => Promise<void>;
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
        contingencyAmount: 0, contingencyTotal: 0
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
    useEffect(() => {
        calculateTotals();
    }, [state.items, state.selectedTaxIds, state.targetMargin, coreState.financials.bcr, state.contingency, taxes]);

    const calculateTotals = () => {
        const totals = pricingService.calculateQuoteTotals(
            state.items,
            taxes,
            state.selectedTaxIds,
            state.contingency,
            state.targetMargin
        );

        setSummary(totals);
    };

    // Moved to pricingService
    // const calculateItemFinancials = ...

    // --- RESOURCE ALLOCATION HELPERS ---
    const getMemberUtilization = (memberId: number) => {
        const member = teamMembers.find(m => m.id === memberId);
        if (!member) return { capacity: 0, used: 0, percentage: 0, remaining: 0 };

        return resourceService.calculateUtilization(member, state.resourceAllocations);
    };

    // --- ACTIONS ---
    const updateProjectInfo = (info: Partial<QuoteBuilderState>) => setState(prev => ({ ...prev, ...info }));

    const addItem = (serviceId: number) => {
        const service = services.find(s => s.id === serviceId);
        if (!service) return;

        // Dynamic Name based on Project Type + Service Name
        // E.g. "Desarrollo Web - Desarrollo Frontend"
        const initialName = state.projectType
            ? `${state.projectType} - ${service.name}`
            : service.name;

        const newItem: QuoteItem = {
            id: crypto.randomUUID(),
            serviceId: service.id,
            serviceName: initialName, // Start with dynamic name
            pricingType: service.pricingType,
            quantity: 1,
            estimatedHours: service.pricingType === 'hourly' ? 10 : undefined,
            fixedPrice: service.pricingType === 'fixed' ? 1000000 : undefined,
            projectValue: service.pricingType === 'project_value' ? 5000000 : undefined,
            recurringPrice: service.pricingType === 'recurring' ? 0 : undefined,
            durationMonths: service.pricingType === 'recurring' ? 1 : undefined, // Default 1 month
            allocations: [], // Start empty as per unified logic

            // Initial placeholders
            internalCost: 0, clientPrice: 0, marginPercentage: 0
        };

        // Calculate initial values
        const calculated = pricingService.calculateItem(newItem, coreState.financials.bcr, state.targetMargin);
        newItem.internalCost = calculated.internalCost;
        newItem.clientPrice = calculated.clientPrice;
        newItem.marginPercentage = calculated.marginPercentage;

        setState(prev => ({ ...prev, items: [...prev.items, newItem] }));
    };

    const updateItem = (itemId: string, updates: Partial<QuoteItem>) => {
        setState(prev => {
            const nextItems = prev.items.map(i => {
                if (i.id !== itemId) return i;

                const updatedItem = { ...i, ...updates };
                // Recalculate financing for this item
                const calculated = pricingService.calculateItem(updatedItem, coreState.financials.bcr, prev.targetMargin);

                return {
                    ...updatedItem,
                    internalCost: calculated.internalCost,
                    clientPrice: calculated.clientPrice,
                    marginPercentage: calculated.marginPercentage
                };
            });
            return { ...prev, items: nextItems };
        });
    };

    const removeItem = (itemId: string) =>
        setState(prev => ({ ...prev, items: prev.items.filter(i => i.id !== itemId) }));

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


    const setTargetMargin = (margin: number) =>
        setState((prev) => {
            const nextItems = prev.items.map((item) => {
                const calculated = pricingService.calculateItem(item, coreState.financials.bcr, margin);
                return {
                    ...item,
                    internalCost: calculated.internalCost,
                    clientPrice: calculated.clientPrice,
                    marginPercentage: calculated.marginPercentage,
                };
            });
            return {
                ...prev,
                targetMargin: margin,
                items: nextItems,
            };
        });
    const setContingency = (contingency: Contingency | undefined) => setState(prev => ({ ...prev, contingency }));

    // --- VALIDATION ---
    const errors: string[] = [];
    if (!state.projectName) errors.push('Project Name Required');
    if (!state.clientName) errors.push('Client Name Required');
    if (state.items.length === 0) errors.push('At least one item required');
    if (summary.totalClientPrice < summary.totalInternalCost && !state.allowLowMargin) {
        errors.push('CRITICAL: Price below Cost');
    }

    // Resource Allocation Validation (Only if active)
    if (state.showResourceAllocation) {
        state.resourceAllocations.forEach(alloc => {
            const member = teamMembers.find(m => m.id === alloc.teamMemberId);
            if (member) {
                const util = getMemberUtilization(member.id);
                // Note: getMemberUtilization calculates TOTAL used including this one.
                // We check if utilization > 100
                if (util.percentage > 100) {
                    errors.push(`Error: ${member.name} allocated > 100% capacity (${util.percentage.toFixed(1)}%)`);
                }
            }
        });
    }

    // --- PERSISTENCE ---
    const saveQuote = async (status: 'Draft' | 'Sent' = 'Draft') => {
        const { quoteService } = await import('@/services/quoteService');

        const payload = {
            projectName: state.projectName,
            clientId: state.clientId ?? undefined,
            clientName: state.clientName,
            clientEmail: state.clientEmail,
            selectedTaxIds: state.selectedTaxIds,
            amount: summary.totalClientPrice,
            currency: state.currency,
            marginPercentage: summary.netMarginPercent,
            targetMargin: state.targetMargin,
            contingency: state.contingency,
            items: state.items
        };

        if (state.items.length === 0) return;

        try {
            if (state.id) {
                const currentQuote = await quoteService.getById(state.id);
                if (currentQuote && currentQuote.status !== 'draft') {
                    await quoteService.createVersion(state.id, payload as any);
                    alert('Nueva versión creada (V' + (currentQuote.version + 1) + ')');
                } else {
                    await quoteService.update(state.id, payload as any);
                }
                await quoteService.setProjectStatus(state.id, status);
                saveQuoteEditorMeta(state.id, {
                    projectType: state.projectType,
                    projectDescription: state.projectDescription,
                });
            } else {
                const newProjectId = await quoteService.create(payload as any);
                setState(prev => ({ ...prev, id: newProjectId, version: 1 }));
                await quoteService.setProjectStatus(newProjectId, status);
                saveQuoteEditorMeta(newProjectId, {
                    projectType: state.projectType,
                    projectDescription: state.projectDescription,
                });
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
                return;
            }
            throw err;
        }
    };

    const loadQuote = useCallback(async (id: string) => {
        const { quoteService } = await import('@/services/quoteService');
        const q = await quoteService.getBuilderData(id);
        if (q) {
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
                currency: (q.currency as any) || 'COP',
                targetMargin: typeof q.targetMargin === 'number' && Number.isFinite(q.targetMargin)
                    ? q.targetMargin
                    : INITIAL_STATE.targetMargin,
                selectedTaxIds: q.selectedTaxIds || [],
                items: q.items || [],
            }));
        }
    }, []);

    return (
        <QuoteBuilderContext.Provider value={{
            state, services, taxes, teamMembers,
            updateProjectInfo, addItem, updateItem, removeItem, toggleTax, setTargetMargin, setContingency,
            toggleResourceAllocation, addResourceAllocation, updateResourceAllocation, removeResourceAllocation, getMemberUtilization,
            summary, isValid: errors.length === 0, errors,
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
