
'use client';

import React, { createContext, useContext, useState, useEffect, useMemo } from 'react';
import { useNougram } from '@/context/NougramCoreContext';
import { TeamMember, FixedCost, SocialChargesConfig, GlobalConfig, BCRCalculation } from '@/types/admin';
import { teamService } from '@/services/teamService';

// Initial Mock Data (to avoid starting empty)
const DEFAULT_SOCIAL_CHARGES: SocialChargesConfig = {
    enable_social_charges: true,
    health_percentage: 8.5,
    pension_percentage: 12.0,
    arl_percentage: 0.522,
    parafiscales_percentage: 4.0,
    prima_services_percentage: 8.33,
    cesantias_percentage: 8.33,
    int_cesantias_percentage: 1.0,
    vacations_percentage: 4.17,
    total_percentage: 52.852
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
    addTeamMember: (member: TeamMember) => void;
    updateTeamMember: (id: string, member: Partial<TeamMember>) => void;
    deleteTeamMember: (id: string) => void;

    addFixedCost: (cost: FixedCost) => void;
    updateFixedCost: (id: string, cost: Partial<FixedCost>) => void;
    deleteFixedCost: (id: string) => void;

    updateSocialCharges: (config: SocialChargesConfig) => void;
    updateGlobalSettings: (settings: Partial<GlobalConfig>) => void;
}

const AdminContext = createContext<AdminContextType | undefined>(undefined);

export function AdminProvider({ children }: { children: React.ReactNode }) {
    // 1. State
    const [teamMembers, setTeamMembers] = useState<TeamMember[]>([]);

    const [fixedCosts, setFixedCosts] = useState<FixedCost[]>([
        { id: '1', name: 'Oficina', category: 'Rent', amountMonthly: 2000000, currency: 'COP', isActive: true },
        { id: '2', name: 'Software', category: 'Software', amountMonthly: 500000, currency: 'COP', isActive: true }
    ]);

    const [socialCharges, setSocialCharges] = useState<SocialChargesConfig>(DEFAULT_SOCIAL_CHARGES);
    const [globalSettings, setGlobalSettings] = useState<GlobalConfig>(DEFAULT_GLOBAL);

    // 2. Calculation Logic
    const { updateFinancialBasics } = useNougram(); // Connect to Core

    useEffect(() => {
        const loadTeamMembers = async () => {
            const members = await teamService.getAll();
            setTeamMembers(members);
        };
        void loadTeamMembers();
    }, []);

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
            const hoursMonth = member.billableHoursPerWeek * 4.33 * (1 - member.nonBillablePercentage);

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
    const addTeamMember = (member: TeamMember) => {
        void (async () => {
            const created = await teamService.create(member);
            if (!created) return;
            setTeamMembers(prev => [created, ...prev]);
        })();
    };
    const updateTeamMember = (id: string, updates: Partial<TeamMember>) => {
        const current = teamMembers.find((member) => member.id === id);
        if (!current) return;
        const merged = { ...current, ...updates };
        void (async () => {
            const updated = await teamService.update(merged);
            if (!updated) return;
            setTeamMembers(prev => prev.map(member => member.id === id ? updated : member));
        })();
    };
    const deleteTeamMember = (id: string) => {
        void (async () => {
            const ok = await teamService.remove(id);
            if (!ok) return;
            setTeamMembers(prev => prev.filter(member => member.id !== id));
        })();
    };

    const addFixedCost = (cost: FixedCost) => setFixedCosts(prev => [...prev, cost]);
    const updateFixedCost = (id: string, updates: Partial<FixedCost>) => setFixedCosts(prev => prev.map(c => c.id === id ? { ...c, ...updates } : c));
    const deleteFixedCost = (id: string) => setFixedCosts(prev => prev.filter(c => c.id !== id));

    const updateSocialCharges = (cfg: SocialChargesConfig) => setSocialCharges(cfg);
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
