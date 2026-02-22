import React from 'react';
import { useAdmin } from '@/context/AdminContext';
import { BCRSummaryCard as BCRSummaryCardUI } from '@/components/admin/BCRSummaryCard';

export function BCRSummaryCard() {
    const { bcr, globalSettings, teamMembers } = useAdmin();

    if (!bcr) return null;

    const summary = {
        blended_cost_rate: bcr.bcr?.toString() || '0',
        total_monthly_costs: bcr.totalMonthlyCosts?.toString() || '0',
        total_monthly_hours: bcr.totalBillableHours || 0,
        total_salaries: bcr.totalPayroll?.toString() || '0',
        total_fixed_overhead: bcr.totalFixedCosts?.toString() || '0',
        total_tools_costs: '0',
        active_team_members: teamMembers?.filter((m: any) => m.isActive).length || 0,
        primary_currency: globalSettings.primary_currency
    };

    return (
        <div className="mb-6">
            <BCRSummaryCardUI summary={summary} />
        </div>
    );
}
