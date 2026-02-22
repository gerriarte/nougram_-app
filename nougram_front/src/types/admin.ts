
// Core Data Types for Admin & User Management

export type Currency = 'COP' | 'USD' | 'EUR';

// --- Payroll & Team ---

export interface TeamMember {
    id: string; // UUID or string ID
    name: string;
    role: string;

    // Compensation
    salaryMonthlyBrute: number;
    currency: Currency;
    applySocialCharges: boolean;

    // Calculated (Read-only usually, or calculated on fly)
    salaryWithCharges: number;

    // Capacity
    billableHoursPerWeek: number;
    nonBillablePercentage: number; // 0.0 to 1.0 (e.g. 0.2 for 20%)
    vacationDaysPerYear: number;

    isActive: boolean;
}

export interface SocialChargesConfig {
    enable_social_charges: boolean;
    health_percentage: number;
    pension_percentage: number;
    arl_percentage: number;
    parafiscales_percentage: number;
    prima_services_percentage: number;
    cesantias_percentage: number;
    int_cesantias_percentage: number;
    vacations_percentage: number;
    total_percentage?: number;
}

// --- Overhead & Fixed Costs ---

export type CostCategory = 'Software' | 'Overhead' | 'Tools' | 'Infrastructure' | 'Office' | 'Utilities' | 'Rent' | 'Other';

export interface FixedCost {
    id: string;
    name: string;
    description?: string;
    category: CostCategory;
    amountMonthly: number;
    currency: Currency;
    isActive: boolean;
}

// --- Global Settings ---

export interface GlobalConfig {
    primary_currency: Currency;
    default_billable_hours_per_week: number;
    default_non_billable_percentage: string; // string based on usage "0.20"
    default_margin_target: string; // string based on usage "0.30"
    weeks_per_month?: number; // Optional or check usage
}

// --- BCR Result (Computed) ---

export interface BCRCalculation {
    totalMonthlyCosts: number;
    totalBillableHours: number;
    bcr: number; // Hourly rate

    // Breakdown
    totalPayroll: number;
    totalFixedCosts: number;
}

// Fixed Cost Input for Forms
export interface FixedCostInput {
    id?: number;
    name: string;
    category: string;
    amount_monthly: string;
    description: string;
    currency: string;
}

export interface FixedCostDisplay extends FixedCostInput {
    id: number;
    amount_monthly_normalized: string;
    created_at: string;
}

export interface TeamMemberInput {
    id?: number;
    name: string;
    role: string;
    is_active: boolean;
    salary_monthly_brute: string;
    currency: string;
    billable_hours_per_week: number;
    non_billable_hours_percentage: string;
}

export interface TeamMemberDisplay extends TeamMemberInput {
    id: number;
    salary_with_charges: string;
    billable_hours_per_month: number;
    cost_per_hour: string;
}

export interface PayrollSummary {
    total_members: number;
    total_salary_brute: string;
    total_salary_with_charges: string;
    total_social_charges: string;
    total_billable_hours_per_month: number;
    average_cost_per_hour: string;
    social_charges_multiplier: number;
    social_charges_total_percentage: number;
}

export interface OverheadSummary {
    total_fixed_costs: string;
    total_tools_costs: string;
    total_overhead_costs: string;
    costs_by_category: Array<{
        category: string;
        count: number;
        total_amount: string;
    }>;
}

export interface BCRSummary {
    blended_cost_rate: string;
    total_monthly_costs: string;
    total_fixed_overhead: string;
    total_tools_costs: string;
    total_salaries: string;
    total_monthly_hours: number;
    active_team_members: number;
    primary_currency: string;
}
