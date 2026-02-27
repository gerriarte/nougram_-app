
export interface FixedCostTemplate {
    id: string;
    name: string;
    amount: number;
    currency: string;
    category: 'Tools' | 'Software' | 'Overhead' | 'Other';
    costType: 'operational' | 'amortization';
    icon: string;
    preSelectedFor?: string[];
    isCustom?: boolean;
}

export interface OnboardingData {
    identity: {
        organizationName: string;
        primaryCurrency: string;
        country?: string;
        profileType: 'freelance' | 'company' | 'agency';
    };
    fixedCosts: Step2FixedCostsData;
    team: Step3MyTeamData[];
    status: 'in_progress' | 'completed';
    lastStep: number;
}

export interface Step2FixedCostsData {
    selectedTemplates: FixedCostTemplate[];
    totalMonthly: number;
}

export interface Step3MyTeamData {
    id: string;
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
}
