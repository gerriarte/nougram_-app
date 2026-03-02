
'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';
import { Equipment } from '@/types/equipment';
import { calculateDepreciation } from '@/lib/depreciation';
import { FixedCostTemplate } from '@/types/onboarding';
import { apiRequest } from '@/lib/api-client';

// --- Types ---

import { UserRole } from '@/types/user';
export type Currency = 'COP' | 'USD';

export interface AgencyIdentity {
    name: string;
    logo?: string;
    primaryCurrency: Currency;
}

export interface FinancialState {
    baseMonthlyCost: number; // From Onboarding (Payroll + Overhead)
    billableHours: number;   // Total capacity
    equipmentAmortization: number; // Calculated from active equipment
    bcr: number; // Final Result: (Base + Amortization) / Hours
    exchangeRateCOP: number;
}

export interface NougramState {
    identity: AgencyIdentity;
    financials: FinancialState;
    equipment: Equipment[]; // Inventory
    user: {
        role: UserRole;
        credits: number;
    };
    isHydrated: boolean;
}

// --- Context ---
interface NougramCoreContextType {
    state: NougramState;

    // Actions
    updateIdentity: (identity: Partial<AgencyIdentity>) => void;
    // updateBCR is now implicit via component updates, but we keep override for base params
    updateFinancialBasics: (baseCost: number, hours: number) => void;

    // Equipment Actions
    addEquipment: (item: Equipment) => void;
    updateEquipment: (id: string, updates: Partial<Equipment>) => void;
    removeEquipment: (id: string) => void;

    updateCredits: (newCredits: number) => void;
    switchRole: (role: UserRole) => void;
    hydrateFromOnboarding: (data: any) => void;
}

const DEFAULT_STATE: NougramState = {
    identity: { name: 'Mi Agencia', primaryCurrency: 'COP' },
    financials: {
        baseMonthlyCost: 0,
        billableHours: 160,
        equipmentAmortization: 0,
        bcr: 0,
        exchangeRateCOP: 4200
    },
    equipment: [],
    user: { role: 'owner', credits: 100 },
    isHydrated: false
};

const NougramCoreContext = createContext<NougramCoreContextType | undefined>(undefined);

export function NougramCoreProvider({ children }: { children: React.ReactNode }) {
    const [state, setState] = useState<NougramState>(DEFAULT_STATE);

    type OrganizationMeResponse = {
        id: number;
        name: string;
        settings?: {
            currency?: Currency;
            primary_currency?: Currency;
        } | null;
    };

    // Initial Hydration from Persistence 
    useEffect(() => {
        const stored = localStorage.getItem('nougram_onboarding_data');
        if (stored) {
            try {
                const parsed = JSON.parse(stored);
                hydrateFromOnboarding(parsed);
            } catch (e) {
                console.error("Hydration failed", e);
                setState(prev => ({ ...prev, isHydrated: true }));
            }
        } else {
            setState(prev => ({ ...prev, isHydrated: true }));
        }
    }, []);

    useEffect(() => {
        const hydrateOrganizationName = async () => {
            const response = await apiRequest<OrganizationMeResponse>('/organizations/me');
            if (response.error || !response.data) return;
            const backendCurrency =
                response.data.settings?.currency ||
                response.data.settings?.primary_currency;
            setState((prev) => ({
                ...prev,
                identity: {
                    ...prev.identity,
                    name: response.data?.name || prev.identity.name,
                    primaryCurrency: backendCurrency || prev.identity.primaryCurrency,
                },
            }));
        };
        void hydrateOrganizationName();
    }, []);

    // BCR Recalculation Effect
    useEffect(() => {
        const { baseMonthlyCost, billableHours } = state.financials;

        // Sum active equipment depreciation
        let totalAmortization = 0;
        state.equipment.forEach(eq => {
            if (eq.isActive) {
                const { monthlyDepreciation } = calculateDepreciation(eq);
                totalAmortization += monthlyDepreciation;
            }
        });

        // Calculate Final BCR
        let newBCR = 0;
        if (billableHours > 0) {
            newBCR = (baseMonthlyCost + totalAmortization) / billableHours;
        }

        // Avoid infinite loop: only update if changed
        if (state.financials.bcr !== newBCR || state.financials.equipmentAmortization !== totalAmortization) {
            setState(prev => ({
                ...prev,
                financials: {
                    ...prev.financials,
                    equipmentAmortization: totalAmortization,
                    bcr: newBCR
                }
            }));
        }

    }, [state.financials.baseMonthlyCost, state.financials.billableHours, state.equipment]);


    const updateIdentity = (id: Partial<AgencyIdentity>) =>
        setState(prev => ({ ...prev, identity: { ...prev.identity, ...id } }));

    const updateFinancialBasics = (baseCost: number, hours: number) =>
        setState(prev => ({ ...prev, financials: { ...prev.financials, baseMonthlyCost: baseCost, billableHours: hours } }));

    // Equipment Actions
    const addEquipment = (item: Equipment) =>
        setState(prev => ({ ...prev, equipment: [...prev.equipment, item] }));

    const updateEquipment = (id: string, updates: Partial<Equipment>) =>
        setState(prev => ({ ...prev, equipment: prev.equipment.map(e => e.id === id ? { ...e, ...updates } : e) }));

    const removeEquipment = (id: string) =>
        setState(prev => ({ ...prev, equipment: prev.equipment.filter(e => e.id !== id) }));


    const updateCredits = (newCredits: number) =>
        setState(prev => ({ ...prev, user: { ...prev.user, credits: newCredits } }));

    const switchRole = (role: UserRole) =>
        setState(prev => ({ ...prev, user: { ...prev.user, role } }));

    const convertToPrimaryCurrency = (
        amount: number,
        from: string,
        to: Currency
    ): number => {
        if (!Number.isFinite(amount)) return 0;
        if (from === to) return amount;
        const rates: Record<string, number> = {
            USD_COP: 4000,
            COP_USD: 0.00025,
            EUR_COP: 4300,
            COP_EUR: 0.00023,
            USD_EUR: 0.93,
            EUR_USD: 1.07,
        };
        const key = `${from}_${to}`;
        return amount * (rates[key] ?? 1);
    };

    const hydrateFromOnboarding = (data: any) => {
        const name = data.identity?.organizationName || data.identity?.name || 'Agencia';
        const currency = (data.identity?.primaryCurrency || data.identity?.currency || 'COP') as Currency;
        const selectedTemplates: FixedCostTemplate[] = Array.isArray(data.fixedCosts?.selectedTemplates)
            ? data.fixedCosts.selectedTemplates
            : [];

        const onboardingHours = Number(data.team?.billableHours);
        const hours = Number.isFinite(onboardingHours) && onboardingHours > 0 ? onboardingHours * 4.33 : 160;

        const salary = Number(data.team?.salary) || 0;
        const salaryWithCharges = data.team?.applySocialCharges ? salary * 1.52852 : salary;
        const nonAmortizableCosts = selectedTemplates
            .filter((template) => !(template.amortizable || template.category === 'Tools'))
            .reduce((sum, template) => {
                return sum + convertToPrimaryCurrency(template.amount || 0, template.currency || currency, currency);
            }, 0);

        const baseMonthlyCost = salaryWithCharges + nonAmortizableCosts;
        const equipmentFromOnboarding: Equipment[] = selectedTemplates
            .filter((template) => template.amortizable || template.category === 'Tools')
            .map((template) => {
                const purchasePrice = convertToPrimaryCurrency(template.amount || 0, template.currency || currency, currency);
                return {
                    id: `onboarding-${template.id}`,
                    name: template.name,
                    description: 'Generado desde onboarding (costo amortizable)',
                    category: 'Hardware',
                    purchasePrice: Number(purchasePrice.toFixed(2)),
                    purchaseDate: new Date().toISOString().slice(0, 10),
                    currency,
                    usefulLifeMonths: 36,
                    salvageValue: 0,
                    depreciationMethod: 'straight_line',
                    isActive: true,
                    createdAt: new Date().toISOString(),
                };
            });
        const bcrValue = hours > 0 ? baseMonthlyCost / hours : 0;

        setState(prev => ({
            ...prev,
            identity: { ...prev.identity, name, primaryCurrency: currency },
            financials: {
                ...prev.financials,
                baseMonthlyCost,
                billableHours: hours,
                bcr: bcrValue
            },
            equipment: equipmentFromOnboarding,
            isHydrated: true
        }));
    };

    return (
        <NougramCoreContext.Provider value={{
            state,
            updateIdentity,
            updateFinancialBasics,
            addEquipment,
            updateEquipment,
            removeEquipment,
            updateCredits,
            switchRole,
            hydrateFromOnboarding
        }}>
            {children}
        </NougramCoreContext.Provider>
    );
}

export const useNougram = () => {
    const context = useContext(NougramCoreContext);
    if (!context) throw new Error('useNougram must be used within NougramCoreProvider');
    return context;
};
