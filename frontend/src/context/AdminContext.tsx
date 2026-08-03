
'use client';

import React, { createContext, useContext, useState, useEffect, useMemo } from 'react';
import { useNougram } from '@/context/NougramCoreContext';
import { isAuthenticated } from '@/lib/auth';
import { TeamMember, FixedCost, SocialChargesConfig, GlobalConfig, BCRCalculation } from '@/types/admin';
import { teamService } from '@/services/teamService';
import { socialChargesService } from '@/services/socialChargesService';
import { fixedCostService } from '@/services/fixedCostService';
import { buildSocialChargesConfigFromCurrency } from '@/lib/social-charges-presets';

import { monthlyBillableHours } from '@/lib/capacity';
// Initial Mock Data (to avoid starting empty)
const DEFAULT_SOCIAL_CHARGES: SocialChargesConfig = {
    ...buildSocialChargesConfigFromCurrency('COP', false)
};

const DEFAULT_GLOBAL: GlobalConfig = {
    primary_currency: 'COP',
    default_billable_hours_per_week: 32,
    default_non_billable_percentage: "0.20",
    default_margin_target: "0.40"
};


interface AdminContextType {
    teamMembers: TeamMember[];
    fixedCosts: FixedCost[];
    socialCharges: SocialChargesConfig;
    globalSettings: GlobalConfig;
    bcr: BCRCalculation;

    // Actions
    addTeamMember: (member: TeamMember) => Promise<{ success: boolean; error?: string }>;
    updateTeamMember: (id: string, member: Partial<TeamMember>) => Promise<{ success: boolean; error?: string }>;
    deleteTeamMember: (id: string) => void;

    addFixedCost: (cost: FixedCost) => void;
    updateFixedCost: (id: string, cost: Partial<FixedCost>) => void;
    deleteFixedCost: (id: string) => void;

    updateSocialCharges: (config: SocialChargesConfig) => void;
    updateGlobalSettings: (settings: Partial<GlobalConfig>) => void;
}

const AdminContext = createContext<AdminContextType | undefined>(undefined);

export function AdminProvider({ children }: { children: React.ReactNode }) {
    const [adminDataKey, setAdminDataKey] = useState(0);

    useEffect(() => {
        const onSessionRestored = () => setAdminDataKey((k) => k + 1);
        if (typeof window !== 'undefined') {
            window.addEventListener('nougram:session-restored', onSessionRestored);
        }
        return () => {
            if (typeof window !== 'undefined') {
                window.removeEventListener('nougram:session-restored', onSessionRestored);
            }
        };
    }, []);

    // 1. State
    const [teamMembers, setTeamMembers] = useState<TeamMember[]>([]);

    const [fixedCosts, setFixedCosts] = useState<FixedCost[]>([]);

    const [socialCharges, setSocialCharges] = useState<SocialChargesConfig>(DEFAULT_SOCIAL_CHARGES);
    const [socialChargesSource, setSocialChargesSource] = useState<'preset' | 'persisted'>('preset');
    const [globalSettings, setGlobalSettings] = useState<GlobalConfig>(DEFAULT_GLOBAL);

    // 2. Calculation Logic
    const { state: nougramState, updateFinancialBasics } = useNougram(); // Connect to Core

    useEffect(() => {
        if (!isAuthenticated()) return;
        const loadTeamMembers = async () => {
            const members = await teamService.getAll();
            setTeamMembers(members);
        };
        void loadTeamMembers();
    }, [adminDataKey]);

    useEffect(() => {
        if (!isAuthenticated()) return;
        const loadFixedCosts = async () => {
            const costs = await fixedCostService.getAll();
            setFixedCosts(costs);
        };
        void loadFixedCosts();
    }, [adminDataKey]);

    useEffect(() => {
        if (!isAuthenticated()) return;
        const loadSocialCharges = async () => {
            const config = await socialChargesService.get();
            if (config) {
                setSocialCharges(config);
                setSocialChargesSource('persisted');
                return;
            }
            const primaryCurrency = (nougramState.identity.primaryCurrency || 'COP') as GlobalConfig['primary_currency'];
            setSocialCharges(buildSocialChargesConfigFromCurrency(primaryCurrency, false));
            setSocialChargesSource('preset');
        };
        void loadSocialCharges();
    }, [nougramState.identity.primaryCurrency, adminDataKey]);

    useEffect(() => {
        const primaryCurrency = (nougramState.identity.primaryCurrency || 'COP') as GlobalConfig['primary_currency'];
        if (socialChargesSource === 'preset') {
            setSocialCharges(buildSocialChargesConfigFromCurrency(primaryCurrency, false));
        }
        setGlobalSettings((prev) => (
            prev.primary_currency === primaryCurrency
                ? prev
                : { ...prev, primary_currency: primaryCurrency }
        ));
    }, [nougramState.identity.primaryCurrency, socialChargesSource]);

    const bcr: BCRCalculation = useMemo(() => {
        // A. Payroll Costs
        let totalPayroll = 0;
        let totalHours = 0;

        teamMembers.forEach(member => {
            if (!member.isActive) return;

            // Recalculate charges dynamically just in case
            const chargesMult = member.applySocialCharges && socialCharges.enable_social_charges
                ? (1 + (socialCharges.total_percentage || 0) / 100)
                : 1;

            const monthlyCost = member.salaryMonthlyBrute * chargesMult;
            const hoursMonth = monthlyBillableHours(member.billableHoursPerWeek);

            totalPayroll += monthlyCost;
            totalHours += hoursMonth;
        });

        // B. Fixed Costs
        const totalFixed = fixedCosts
            .filter(c => c.isActive)
            .reduce((sum, c) => sum + c.amountMonthly, 0);

        // C. Final
        const totalMonthly = totalPayroll + totalFixed;
        const finalBCR = totalHours > 0 ? totalMonthly / totalHours : 0;

        return {
            totalMonthlyCosts: totalMonthly,
            totalBillableHours: totalHours,
            bcr: finalBCR,
            totalPayroll,
            totalFixedCosts: totalFixed
        };
    }, [teamMembers, fixedCosts, socialCharges]);

    useEffect(() => {
        // Sync base payroll+overhead to NougramCore; final BCR is computed there with amortization.
        // updateFinancialBasics function identity is not stable across renders, so we intentionally
        // depend only on the computed numeric values to avoid a render loop in admin pages.
        updateFinancialBasics(bcr.totalMonthlyCosts, bcr.totalBillableHours);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [bcr.totalMonthlyCosts, bcr.totalBillableHours]);

    // 3. Actions
    const addTeamMember = async (member: TeamMember) => {
        const result = await teamService.create(member);
        if (!result.ok) {
            return { success: false, error: result.error };
        }
        setTeamMembers((prev) => [result.member, ...prev]);
        return { success: true };
    };
    const updateTeamMember = async (id: string, updates: Partial<TeamMember>) => {
        const current = teamMembers.find((member) => member.id === id);
        if (!current) {
            return { success: false, error: 'Miembro no encontrado.' };
        }
        const merged = { ...current, ...updates };
        const result = await teamService.update(merged);
        if (!result.ok) {
            return { success: false, error: result.error };
        }
        setTeamMembers((prev) => prev.map((member) => (member.id === id ? result.member : member)));
        return { success: true };
    };
    const deleteTeamMember = (id: string) => {
        void (async () => {
            const ok = await teamService.remove(id);
            if (!ok) return;
            setTeamMembers(prev => prev.filter(member => member.id !== id));
        })();
    };

    const addFixedCost = (cost: FixedCost) => {
        const payload = {
            name: cost.name,
            description: cost.description,
            category: cost.category,
            amountMonthly: cost.amountMonthly,
            currency: cost.currency,
        };
        void (async () => {
            const created = await fixedCostService.create(payload);
            if (!created) return;
            setFixedCosts(prev => [created, ...prev]);
        })();
    };
    const updateFixedCost = (id: string, updates: Partial<FixedCost>) => {
        const current = fixedCosts.find((cost) => cost.id === id);
        if (!current) return;
        void (async () => {
            const updated = await fixedCostService.update(id, { ...current, ...updates });
            if (!updated) return;
            setFixedCosts(prev => prev.map(cost => (cost.id === id ? updated : cost)));
        })();
    };
    const deleteFixedCost = (id: string) => {
        void (async () => {
            const ok = await fixedCostService.remove(id);
            if (!ok) return;
            setFixedCosts(prev => prev.filter(cost => cost.id !== id));
        })();
    };

    const updateSocialCharges = (cfg: SocialChargesConfig) => {
        setSocialCharges(cfg);
        setSocialChargesSource('persisted');
        void socialChargesService.save(cfg);
    };
    const updateGlobalSettings = (settings: Partial<GlobalConfig>) => setGlobalSettings(prev => ({ ...prev, ...settings }));

    return (
        <AdminContext.Provider value={{
            teamMembers, fixedCosts, socialCharges, globalSettings, bcr,
            addTeamMember, updateTeamMember, deleteTeamMember,
            addFixedCost, updateFixedCost, deleteFixedCost,
            updateSocialCharges, updateGlobalSettings
        }}>
            {children}
        </AdminContext.Provider>
    );
}

export const useAdmin = () => {
    const context = useContext(AdminContext);
    if (!context) throw new Error('useAdmin must be used within AdminProvider');
    return context;
};
