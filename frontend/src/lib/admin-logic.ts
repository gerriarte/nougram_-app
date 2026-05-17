import {
    TeamMemberInput,
    SocialChargesConfig,
    TeamMemberDisplay,
    PayrollSummary,
    FixedCostInput,
    OverheadSummary,
    BCRSummary,
    GlobalConfig
} from "@/types/admin";

const WEEKS_PER_MONTH = 4.33;

export function calculateSocialChargesMult(config: SocialChargesConfig): number {
    if (!config.enable_social_charges) return 1;

    const total =
        config.health_percentage +
        config.pension_percentage +
        config.arl_percentage +
        config.parafiscales_percentage +
        config.prima_services_percentage +
        config.cesantias_percentage +
        config.int_cesantias_percentage +
        config.vacations_percentage;

    return 1 + (total / 100);
}

export function calculatePayroll(
    members: TeamMemberInput[],
    socialConfig: SocialChargesConfig
): { members: TeamMemberDisplay[], summary: PayrollSummary } {

    const mult = calculateSocialChargesMult(socialConfig);
    let totalSalaryBrute = 0;
    let totalSalaryWithCharges = 0;
    let totalBillableHours = 0;

    const calculatedMembers = members.map((m, index) => {
        const salary = parseFloat(m.salary_monthly_brute || "0");
        const salaryWithCharges = salary * mult;

        // Calculate Monthly Hours
        // Formula: Weekly Hours * 4.33 * (1 - NonBillable%)
        const nonBillablePct = parseFloat(m.non_billable_hours_percentage || "0");
        const weeklyHours = m.billable_hours_per_week || 0;
        const monthlyHours = weeklyHours * WEEKS_PER_MONTH * (1 - nonBillablePct);

        // Cost Per Hour
        const costPerHour = monthlyHours > 0 ? salaryWithCharges / monthlyHours : 0;

        // Accumulators
        if (m.is_active) {
            totalSalaryBrute += salary;
            totalSalaryWithCharges += salaryWithCharges;
            totalBillableHours += monthlyHours;
        }

        return {
            ...m,
            id: m.id || index + 1, // Mock ID if missing
            salary_with_charges: salaryWithCharges.toFixed(2),
            billable_hours_per_month: monthlyHours,
            cost_per_hour: costPerHour.toFixed(2)
        };
    });

    const avgCostPerHour = totalBillableHours > 0
        ? totalSalaryWithCharges / totalBillableHours
        : 0;

    return {
        members: calculatedMembers,
        summary: {
            total_members: members.filter(m => m.is_active).length,
            total_salary_brute: totalSalaryBrute.toFixed(2),
            total_salary_with_charges: totalSalaryWithCharges.toFixed(2),
            total_social_charges: (totalSalaryWithCharges - totalSalaryBrute).toFixed(2),
            total_billable_hours_per_month: totalBillableHours,
            average_cost_per_hour: avgCostPerHour.toFixed(2),
            social_charges_multiplier: mult,
            social_charges_total_percentage: (mult - 1) * 100
        }
    };
}

export function calculateOverhead(costs: FixedCostInput[]): OverheadSummary {
    let totalFixed = 0;
    let totalTools = 0;
    let totalOverhead = 0;
    const categoryMap = new Map<string, number>();

    costs.forEach(c => {
        const amount = parseFloat(c.amount_monthly || "0");
        totalFixed += amount;

        // Simple categorization logic
        const catLower = c.category.toLowerCase();
        const isTool = ["software", "saas", "tool", "licencia"].some(k => catLower.includes(k));

        if (isTool) {
            totalTools += amount;
        } else {
            totalOverhead += amount;
        }

        const currentCatTotal = categoryMap.get(c.category) || 0;
        categoryMap.set(c.category, currentCatTotal + amount);
    });

    const costsByCategory = Array.from(categoryMap.entries()).map(([cat, total]) => ({
        category: cat,
        count: costs.filter(c => c.category === cat).length,
        total_amount: total.toFixed(2)
    }));

    return {
        total_fixed_costs: totalFixed.toFixed(2),
        total_tools_costs: totalTools.toFixed(2),
        total_overhead_costs: totalOverhead.toFixed(2),
        costs_by_category: costsByCategory
    };
}

export function calculateBCR(
    payrollSummary: PayrollSummary,
    overheadSummary: OverheadSummary,
    config: GlobalConfig
): BCRSummary {

    const payrollTotal = parseFloat(payrollSummary.total_salary_with_charges);
    const overheadTotal = parseFloat(overheadSummary.total_fixed_costs);
    const totalMonthlyCosts = payrollTotal + overheadTotal;
    const totalHours = payrollSummary.total_billable_hours_per_month;

    const bcr = totalHours > 0 ? totalMonthlyCosts / totalHours : 0;

    return {
        blended_cost_rate: bcr.toFixed(2),
        total_monthly_costs: totalMonthlyCosts.toFixed(2),
        total_fixed_overhead: overheadSummary.total_overhead_costs,
        total_tools_costs: overheadSummary.total_tools_costs,
        total_salaries: payrollSummary.total_salary_with_charges,
        total_monthly_hours: totalHours,
        active_team_members: payrollSummary.total_members,
        primary_currency: config.primary_currency
    };
}
