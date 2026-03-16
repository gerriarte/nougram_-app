
export interface FixedCostTemplate {
    id: string;
    name: string;
    amount: number;
    currency: string;
    quantity?: number;
    category: 'Tools' | 'Software' | 'Overhead' | 'Other';
    amortizable?: boolean;
    costType?: 'operational' | 'amortization';
    purchasePrice?: number;
    usefulLifeMonths?: number;
    salvageValue?: number;
    purchaseDate?: string; // ISO YYYY-MM-DD
    depreciationMethod?: 'straight_line' | 'declining_balance';
    paymentType?: 'monthly' | 'annual';
    icon: string;
    preSelectedFor?: string[];
    isCustom?: boolean;
}

export interface OnboardingData {
    identity: {
        organizationName: string;
        primaryCurrency: string;
        country?: string;
    };
    fixedCosts: Step2FixedCostsData;
    team: Step3MyTeamData;
    status: 'in_progress' | 'completed';
    lastStep: number;
}

export interface Step2FixedCostsData {
    selectedTemplates: FixedCostTemplate[];
    totalMonthly: number;
}

export interface Step3MyTeamData {
    payrollHeadcount: number;
    name: string;
    role: string;
    level: 'Junior' | 'Mid' | 'Senior' | '';
    salary: number;
    totalHours: number;
    billableHours: number;
    vacationDays: number;
    applySocialCharges: boolean;
    yearlyBillableHours: number; // Calculated
    hourlyCost: number; // Calculated
    teamMembers?: Array<{
        name: string;
        role: string;
        level: 'Junior' | 'Mid' | 'Senior' | '';
        salary: number;
        totalHours: number;
        billableHours: number;
        vacationDays: number;
        applySocialCharges: boolean;
    }>;
}
