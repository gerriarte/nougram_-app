import React from 'react';
import { useAdmin } from '@/context/AdminContext';
import { useNougram } from '@/context/NougramCoreContext';
import { BCRSummaryCard as BCRSummaryCardUI } from '@/components/admin/BCRSummaryCard';

const TOOL_CATEGORIES = ['software', 'saas', 'tool', 'licencia'];
function isTool(category: string): boolean {
    const lower = category.toLowerCase();
    return TOOL_CATEGORIES.some(k => lower.includes(k));
}

export function BCRSummaryCard() {
    const { bcr, globalSettings, teamMembers, fixedCosts } = useAdmin();
    const { state } = useNougram();

    const amortizationMonthly = state.financials.equipmentAmortization || 0;

    // Split fixed costs into tools/SaaS vs pure overhead (consistent with calculateOverhead)
    const toolsCosts = fixedCosts
        .filter(c => c.isActive && isTool(c.category))
        .reduce((sum, c) => sum + c.amountMonthly, 0);
    const overheadCosts = (bcr?.totalFixedCosts || 0) - toolsCosts;

    const summary = {
        blended_cost_rate: state.financials.bcr?.toString() || bcr?.bcr?.toString() || '0',
        total_monthly_costs: ((bcr?.totalMonthlyCosts || 0) + amortizationMonthly).toString(),
        total_monthly_hours: bcr?.totalBillableHours || 0,
        total_salaries: bcr?.totalPayroll?.toString() || '0',
        total_fixed_overhead: overheadCosts.toString(),
        total_tools_costs: (toolsCosts + amortizationMonthly).toString(),
        active_team_members: teamMembers?.filter((m) => m.isActive).length || 0,
        primary_currency: state.identity.primaryCurrency || globalSettings.primary_currency
    };

    return (
        <div className="mb-6">
            <BCRSummaryCardUI summary={summary} />
        </div>
    );
}
