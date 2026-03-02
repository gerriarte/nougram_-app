
import {
    FixedCostTemplate,
} from '@/types/onboarding';
import { apiRequest } from '@/lib/api-client';

// Types
export interface CurrencyRate {
    from: string;
    to: string;
    rate: number;
    lastUpdated: string;
}

type OnboardingTemplatesResponse = {
    items: FixedCostTemplate[];
    source: string;
};

type ExchangeRatesResponse = {
    rates: Record<string, { rate: number | string; rate_to_usd: number | string; last_updated: string }>;
    base_currency: string;
};

export const onboardingService = {

    getTemplates: async (): Promise<FixedCostTemplate[]> => {
        const response = await apiRequest<OnboardingTemplatesResponse>('/onboarding/templates');
        if (response.error || !response.data?.items) return [];
        return response.data.items;
    },

    getExchangeRates: async (): Promise<Record<string, { rate: number; lastUpdated: string }>> => {
        const response = await apiRequest<ExchangeRatesResponse>('/settings/currency/exchange-rates');
        if (response.error || !response.data?.rates) return {};

        const normalized: Record<string, { rate: number; lastUpdated: string }> = {};
        Object.entries(response.data.rates).forEach(([code, info]) => {
            normalized[code] = {
                rate: Number(info.rate),
                lastUpdated: info.last_updated,
            };
        });
        return normalized;
    },

    convertCurrency: (
        amount: number,
        from: string,
        to: string,
        rates: Record<string, { rate: number; lastUpdated: string }> = {}
    ): number => {
        if (from === to) return amount;
        const fromRate = rates[from]?.rate;
        const toRate = rates[to]?.rate;
        if (!fromRate || !toRate) return amount;
        return (amount / fromRate) * toRate;
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

    getExchangeRate: async (from: string, to: string): Promise<CurrencyRate> => {
        const rates = await onboardingService.getExchangeRates();
        if (from === to) {
            return { from, to, rate: 1, lastUpdated: new Date().toISOString() };
        }
        const fromRate = rates[from]?.rate;
        const toRate = rates[to]?.rate;
        const converted = fromRate && toRate ? (1 / fromRate) * toRate : 1;
        return {
            from,
            to,
            rate: converted,
            lastUpdated: rates[to]?.lastUpdated || new Date().toISOString(),
        };
    },
};
