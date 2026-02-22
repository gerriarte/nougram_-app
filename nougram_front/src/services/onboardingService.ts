
import {
    FixedCostTemplate,
    OnboardingData,
    Step2FixedCostsData,
    Step3MyTeamData
} from '@/types/onboarding'; // We might need to define these types if they don't exist, or use 'any' temporarily and then strict types.

// Mock Data
export const HARDWARE_TEMPLATES: FixedCostTemplate[] = [
    { id: "laptop", name: "Laptop de Trabajo", amount: 800000, currency: "COP", category: "Tools", icon: "💻", preSelectedFor: ['dev', 'design', 'marketing'] },
    { id: "monitor", name: "Monitor Externo", amount: 150000, currency: "COP", category: "Tools", icon: "🖥️", preSelectedFor: ['dev', 'design'] },
];

export const SOFTWARE_TEMPLATES: FixedCostTemplate[] = [
    { id: "adobe_cc", name: "Adobe Creative Cloud", amount: 150000, currency: "COP", category: "Software", icon: "🎨", preSelectedFor: ['design', 'marketing'] },
    { id: "chatgpt_plus", name: "ChatGPT Plus", amount: 20, currency: "USD", category: "Software", icon: "🤖", preSelectedFor: ['dev', 'marketing', 'design'] },
    { id: "figma", name: "Figma Professional", amount: 12, currency: "USD", category: "Software", icon: "🎨", preSelectedFor: ['design'] },
    { id: "notion", name: "Notion Pro", amount: 8, currency: "USD", category: "Software", icon: "📝", preSelectedFor: ['consulting', 'design'] },
];

export const OVERHEAD_TEMPLATES: FixedCostTemplate[] = [
    { id: "coworking", name: "Arriendo Coworking", amount: 300000, currency: "COP", category: "Overhead", icon: "🏢", preSelectedFor: [] },
    { id: "internet", name: "Internet", amount: 80000, currency: "COP", category: "Overhead", icon: "🌐", preSelectedFor: ['dev', 'design', 'marketing', 'consulting'] },
    { id: 'hosting', name: 'Hosting Web', amount: 50000, currency: 'COP', category: 'Overhead', icon: '☁️', preSelectedFor: ['dev'] },
];

export const ALL_TEMPLATES = [...HARDWARE_TEMPLATES, ...SOFTWARE_TEMPLATES, ...OVERHEAD_TEMPLATES];

export const BENCHMARKS = {
    freelance: {
        description: "Operación individual enfocada en proyectos especializados.",
        avgMargin: 38,
        avgMonthlyIncome: "3,500",
    },
    company: {
        description: "Empresa pequeña con estructura y costos operativos fijos.",
        avgMargin: 32,
        avgMonthlyIncome: "12,000",
        avgTeamSize: 6,
    },
    agency: {
        description: "Agencia con múltiples servicios y equipo multidisciplinario.",
        avgMargin: 35,
        avgMonthlyIncome: "25,000",
        avgTeamSize: 12,
    },
} as const;

// Types
export interface CurrencyRate {
    from: string;
    to: string;
    rate: number;
    lastUpdated: string;
}

// Mock Exchange Rates
const MOCK_RATES: Record<string, number> = {
    'USD_COP': 4000,
    'COP_USD': 0.00025,
    'EUR_COP': 4300,
    'COP_EUR': 0.00023,
};

export const onboardingService = {

    getTemplates: async () => {
        // Simulate API delay
        return new Promise<any[]>((resolve) => {
            setTimeout(() => resolve(ALL_TEMPLATES), 100);
        });
    },

    getExchangeRate: async (from: string, to: string): Promise<CurrencyRate> => {
        // Simulate API
        return new Promise((resolve) => {
            const key = `${from}_${to}`;
            const rate = from === to ? 1 : (MOCK_RATES[key] || 1);
            setTimeout(() => {
                resolve({
                    from,
                    to,
                    rate,
                    lastUpdated: new Date().toISOString()
                });
            }, 50);
        });
    },

    convertCurrency: (amount: number, from: string, to: string): number => {
        if (from === to) return amount;
        const key = `${from}_${to}`;
        const rate = MOCK_RATES[key] || 1;
        return amount * rate;
    },

    /**
     * Calculates the True Hourly Cost based on annual logic.
     * Formula: (MonthlyCost * 12) / (WeeklyBillableHours * WeeksWorkedPerYear)
     */
    calculateTrueHourlyCost: (
        monthlyCost: number,
        weeklyBillableHours: number,
        vacationDays: number
    ): { hourlyCost: number, annualBillableHours: number, annualCost: number } => {

        // 1. Calculate Productive Weeks
        // Standard year = 52 weeks
        // 5 days per work week standard implies vacationDays / 5 = weeks off
        const weeksOff = vacationDays / 5;
        const productiveWeeks = 52 - weeksOff;

        // 2. Calculate Annual Billable Hours
        const annualBillableHours = weeklyBillableHours * productiveWeeks;

        // 3. Calculate Annual Cost
        const annualCost = monthlyCost * 12;

        // 4. Calculate Hourly Cost
        // Avoid division by zero
        const hourlyCost = annualBillableHours > 0 ? annualCost / annualBillableHours : 0;

        return {
            hourlyCost,
            annualBillableHours,
            annualCost
        };
    },

    getMarketSalaryThreshold: (role: string, level: string, currency: string): number | null => {
        // Mock Data for COP. In a real app, this would be an API call or a larger dataset.
        // Base baselines for Mid level
        const baselines: Record<string, number> = {
            'Diseñador UI/UX': 3500000,
            'Desarrollador Frontend': 4000000,
            'Desarrollador Backend': 4500000,
            'Product Manager': 5000000,
            'CEO/Founder': 6000000,
            'Otro': 2000000
        };

        const base = baselines[role];
        if (!base) return null;

        let multiplier = 1;
        if (level === 'Junior') multiplier = 0.7;
        if (level === 'Senior') multiplier = 1.5;

        let amount = base * multiplier;

        // Simple conversion if checking against USD (mock)
        if (currency === 'USD') {
            amount = amount / 4000;
        }

        return amount;
    }
};
