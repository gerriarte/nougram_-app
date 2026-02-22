import React from 'react';
import { useAdmin } from '@/context/AdminContext';
import { useNougram } from '@/context/NougramCoreContext';
import { BCRSummaryCard as BCRSummaryCardUI } from '@/components/admin/BCRSummaryCard';

export function BCRSummaryCard() {
    const { bcr, globalSettings, teamMembers } = useAdmin();
    const { state } = useNougram();

    if (!bcr) return null;

    const amortizationMonthly = state.financials.equipmentAmortization || 0;

    const summary = {
        blended_cost_rate: state.financials.bcr?.toString() || bcr.bcr?.toString() || '0',
        total_monthly_costs: (bcr.totalMonthlyCosts + amortizationMonthly).toString(),
        total_monthly_hours: bcr.totalBillableHours || 0,
        total_salaries: bcr.totalPayroll?.toString() || '0',
        total_fixed_overhead: bcr.totalFixedCosts?.toString() || '0',
        total_tools_costs: amortizationMonthly.toString(),
        active_team_members: teamMembers?.filter((m) => m.isActive).length || 0,
        primary_currency: globalSettings.primary_currency
    };

    return (
        <div className="mb-6">
            <BCRSummaryCardUI summary={summary} />
        </div>
    );
}
