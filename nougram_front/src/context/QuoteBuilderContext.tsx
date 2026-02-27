
'use client';

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { useNougram } from '@/context/NougramCoreContext';
import {
    QuoteBuilderState, QuoteItem, TaxConfig, CalculationSummary,
    PricingType, Service, Contingency
} from '@/types/quote-builder';

const FALLBACK_TAXES: TaxConfig[] = [
    { id: 1, name: 'IVA', percentage: 19.0 },
    { id: 2, name: 'ReteFuente', percentage: 3.5 },
    { id: 3, name: 'ICA', percentage: 0.966 },
];

// MOCK_TEAM_MEMBERS moved to resourceService
import { resourceService } from '@/services/resourceService';
import { pricingService } from '@/services/pricingService';
import { taxService } from '@/services/taxService';

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

const QUOTE_EDITOR_META_KEY = 'nougram_quote_editor_meta_v1';

type QuoteEditorMeta = {
    projectType?: string;
    projectDescription?: string;
};

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
    refreshTaxes: () => Promise<void>;
    createTax: (payload: { name: string; code: string; percentage: number; country?: string; description?: string }) => Promise<void>;
    updateTax: (id: number, payload: { name?: string; code?: string; percentage?: number; country?: string; description?: string }) => Promise<void>;
    deleteTax: (id: number) => Promise<void>;
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
}

const QuoteBuilderContext = createContext<QuoteBuilderContextType | undefined>(undefined);

export function QuoteBuilderProvider({ children }: { children: React.ReactNode }) {
    const { state: coreState } = useNougram();
    const [state, setState] = useState<QuoteBuilderState>(INITIAL_STATE);
    const [services, setServices] = useState<Service[]>([]);
    const [taxes, setTaxes] = useState<TaxConfig[]>(FALLBACK_TAXES);
    const [teamMembers, setTeamMembers] = useState<import('@/types/quote-builder').TeamMemberMock[]>([]); // Load from service
    const [summary, setSummary] = useState<CalculationSummary>({
        totalInternalCost: 0, totalClientPrice: 0, totalTaxes: 0, totalWithTaxes: 0, netMarginAmount: 0, netMarginPercent: 0, realIncome: 0,
        contingencyAmount: 0, contingencyTotal: 0
    });

    // --- LOAD BASE DATA ---
    useEffect(() => {
        resourceService.getAllMembers().then(setTeamMembers);
        import('@/services/quoteService').then(({ quoteService }) => {
            quoteService.getAvailableServices().then((available) => {
                if (available.length > 0) setServices(available);
            }).catch(() => {
                setServices([]);
            });
        });
        taxService.getAll(true).then((items) => {
            if (items.length > 0) {
                setTaxes(items);
            }
        }).catch(() => {
            setTaxes(FALLBACK_TAXES);
        });
    }, []);

    useEffect(() => {
        const orgCurrency = coreState.identity.primaryCurrency;
        if (!orgCurrency) return;

        setState(prev => {
            // Keep existing quote currency when editing loaded quote data.
            if (prev.id) return prev;
            if (prev.currency === orgCurrency) return prev;
            return {
                ...prev,
                currency: orgCurrency as QuoteBuilderState['currency']
            };
        });
    }, [coreState.identity.primaryCurrency]);

    // --- CALCULATION ENGINE ---
    useEffect(() => {
        calculateTotals();
    }, [state.items, state.selectedTaxIds, state.targetMargin, coreState.financials.bcr, state.contingency, taxes]);

    const calculateTotals = () => {
        // 1. Calculate Items
        const calculatedItems = state.items.map(item => {
            // Recalculate each item based on current inputs & global factors using Service
            const result = pricingService.calculateItem(item, coreState.financials.bcr, state.targetMargin);
            return {
                ...item,
                internalCost: result.internalCost,
                clientPrice: result.clientPrice,
                marginPercentage: result.marginPercentage
            };
        });

        // Update items in state if they changed? 
        // No, this causes infinite loop if we setState here.
        // We should just use these calculated values for the summary.
        // Ideally, `updateItem` should trigger a recalculation and update the state.
        // For now, let's keep the pattern where we calculate derived values for summary
        // BUT ALSO we need to update the items in the state so the UI shows the correct cost/price.

        // Refactor: We won't update state here to avoid loops.
        // Instead, valid approach: verify if values changed, then update.
        // OR simpler: Trust that `updateItem` handles the calculation (backend simulation).

        // Let's implement the "Backend Simulation" properly:
        // When an item is updated, we call the service and save the result.
        // calculatedTotals just sums up what's in the state.

        // However, Target Margin is global. If it changes, all items need update.
        // So we do need a way to batch update items.

        // For this refactor, let's assume `calculateTotals` is responsible for global summary
        // passing the current state items to the service.

        const totals = pricingService.calculateQuoteTotals(
            calculatedItems,
            taxes,
            state.selectedTaxIds,
            state.contingency
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

    const refreshTaxes = async () => {
        const items = await taxService.getAll(true);
        setTaxes(items);
        setState(prev => ({
            ...prev,
            selectedTaxIds: prev.selectedTaxIds.filter((id) => items.some((tax) => tax.id === id))
        }));
    };

    const createTax = async (payload: { name: string; code: string; percentage: number; country?: string; description?: string }) => {
        const created = await taxService.create(payload);
        setTaxes(prev => [...prev, created].sort((a, b) => a.name.localeCompare(b.name)));
    };

    const updateTax = async (id: number, payload: { name?: string; code?: string; percentage?: number; country?: string; description?: string }) => {
        const updated = await taxService.update(id, payload);
        setTaxes(prev => prev.map((tax) => tax.id === id ? updated : tax));
    };

    const deleteTax = async (id: number) => {
        await taxService.remove(id);
        setTaxes(prev => prev.filter((tax) => tax.id !== id));
        setState(prev => ({
            ...prev,
            selectedTaxIds: prev.selectedTaxIds.filter((taxId) => taxId !== id)
        }));
    };

    const toggleResourceAllocation = () => setState(prev => ({ ...prev, showResourceAllocation: !prev.showResourceAllocation }));

    const addResourceAllocation = (allocation: import('@/types/quote-builder').ResourceAllocation) =>
        setState(prev => ({ ...prev, resourceAllocations: [...prev.resourceAllocations, allocation] }));

    const updateResourceAllocation = (id: string, updates: Partial<import('@/types/quote-builder').ResourceAllocation>) =>
        setState(prev => ({ ...prev, resourceAllocations: prev.resourceAllocations.map(a => a.id === id ? { ...a, ...updates } : a) }));

    const removeResourceAllocation = (id: string) =>
        setState(prev => ({ ...prev, resourceAllocations: prev.resourceAllocations.filter(a => a.id !== id) }));


    const setTargetMargin = (margin: number) => setState(prev => ({ ...prev, targetMargin: margin }));
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

        if (state.items.length > 0) {
            if (state.id) {
                // Editing existing quote
                // Logic: If status is 'draft', update. If 'sent'/'accepted', create version.
                // We need to know the current status. For this MVP, let's assume if it has an ID, we check with service?
                // Or easier: we can't check status here easily without fetching.
                // BUT, `loadQuote` sets the state. We should probably store `status` in state too if we want to be precise.
                // For now, let's assume ALL edits to existing quotes that are NOT drafts should be versions.
                // How do we know?
                // Let's rely on a simpler rule: "Save and Continue" (Sent) always tries to finalize.
                // "Save Draft" updates draft.

                // Better approach for "Edit Costs":
                // If the user opened an existing quote, we want to save a NEW version if they click "Save".
                // Let's implement a heuristic: ALWAYS create a version if it's an update, unless we explicitly say "update draft".
                // Actually, the requirement "guarde sus versiones de edición" implies we want history.
                // Let's try to fetch the quote first to check status, or just default to versioning for safety?
                // Fetching is safer.

                const currentQuote = await quoteService.getById(state.id);
                if (currentQuote && currentQuote.status !== 'draft') {
                    // It was already sent/finalized. Create new version.
                    await quoteService.createVersion(state.id, payload as any);
                    alert('Nueva versión creada (V' + (currentQuote.version + 1) + ')');
                } else {
                    // It's still a draft, just update it.
                    await quoteService.update(state.id, payload as any);
                }
                await quoteService.setProjectStatus(state.id, status);
                saveQuoteEditorMeta(state.id, {
                    projectType: state.projectType,
                    projectDescription: state.projectDescription,
                });
            } else {
                // Creating new quote
                const newProjectId = await quoteService.create(payload as any);
                // Update state ID so subsequent saves are updates
                setState(prev => ({ ...prev, id: newProjectId, version: 1 }));
                await quoteService.setProjectStatus(newProjectId, status);
                saveQuoteEditorMeta(newProjectId, {
                    projectType: state.projectType,
                    projectDescription: state.projectDescription,
                });
            }
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
                return prefix?.trim() || '';
            })();

            setState(prev => ({
                ...prev,
                step: 'editor',
                id: q.id,
                version: q.version,
                projectName: q.projectName,
                clientId: q.clientId ?? undefined,
                clientName: q.clientName,
                clientEmail: q.clientEmail || '',
                clientCompany: q.clientCompany || q.clientName || '',
                clientRequester: q.clientRequester || '',
                projectType: persistedMeta.projectType || inferredProjectType,
                projectDescription: persistedMeta.projectDescription || '',
                currency: (q.currency as any) || 'COP',
                selectedTaxIds: q.selectedTaxIds || [],
                items: q.items || [],
            }));
        }
    }, []);

    return (
        <QuoteBuilderContext.Provider value={{
            state, services, taxes, teamMembers,
            updateProjectInfo, addItem, updateItem, removeItem, toggleTax, refreshTaxes, createTax, updateTax, deleteTax, setTargetMargin, setContingency,
            toggleResourceAllocation, addResourceAllocation, updateResourceAllocation, removeResourceAllocation, getMemberUtilization,
            summary, isValid: errors.length === 0, errors,
            saveQuote, loadQuote
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
