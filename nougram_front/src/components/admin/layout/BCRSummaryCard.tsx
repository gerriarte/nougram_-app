import React, { useEffect, useState } from 'react';
import { useAdmin } from '@/context/AdminContext';
import { useNougram } from '@/context/NougramCoreContext';
import { BCRSummaryCard as BCRSummaryCardUI } from '@/components/admin/BCRSummaryCard';
import { financialSummaryService } from '@/services/financialSummaryService';

export function BCRSummaryCard() {
    const { bcr, globalSettings, teamMembers } = useAdmin();
    const { state } = useNougram();
    const [backendSummary, setBackendSummary] = useState<{
        blended_cost_rate: string;
        total_monthly_costs: string;
        total_monthly_hours: number;
        total_salaries: string;
        total_fixed_overhead: string;
        total_tools_costs: string;
        active_team_members: number;
        primary_currency: string;
    } | null>(null);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        const load = async () => {
            setLoading(true);
            const response = await financialSummaryService.get();
            setLoading(false);
            if (!response) return;

            // Backend remains source of truth for BCR and monthly totals.
            setBackendSummary({
                blended_cost_rate: String(response.blendedCostRate || 0),
                total_monthly_costs: String(response.monthlyFixedCosts + response.monthlyPayroll),
                total_monthly_hours: response.totalBillableHours || 0,
                total_salaries: String(response.monthlyPayroll || 0),
                total_fixed_overhead: String(response.monthlyFixedCosts || 0),
                total_tools_costs: String(state.financials.equipmentAmortization || 0),
                active_team_members: response.activeTeamMembers || 0,
                primary_currency: response.currency || state.identity.primaryCurrency || globalSettings.primary_currency,
            });
        };
        void load();
    }, [globalSettings.primary_currency, state.financials.equipmentAmortization, state.identity.primaryCurrency]);

    const amortizationMonthly = state.financials.equipmentAmortization || 0;

    const summary = {
        blended_cost_rate: state.financials.bcr?.toString() || bcr?.bcr?.toString() || '0',
        total_monthly_costs: ((bcr?.totalMonthlyCosts || 0) + amortizationMonthly).toString(),
        total_monthly_hours: bcr?.totalBillableHours || 0,
        total_salaries: bcr?.totalPayroll?.toString() || '0',
        total_fixed_overhead: bcr?.totalFixedCosts?.toString() || '0',
        total_tools_costs: amortizationMonthly.toString(),
        active_team_members: teamMembers?.filter((m) => m.isActive).length || 0,
        primary_currency: state.identity.primaryCurrency || globalSettings.primary_currency
    };

    return (
        <div className="mb-6">
            <BCRSummaryCardUI summary={backendSummary || summary} isLoading={loading} />
        </div>
    );
}
