
import {
    FixedCostTemplate,
} from '@/types/onboarding';
import { apiRequest } from '@/lib/api-client';
import { getAuthToken } from '@/lib/auth';

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

type OnboardingDraftResponse = {
    success: boolean;
    organization_id: number;
    data: Record<string, unknown>;
};

type OnboardingImportPreviewIssue = {
    sheet: string;
    row: number;
    field: string;
    message: string;
};

type OnboardingImportPreviewResponse = {
    success: boolean;
    source: 'excel' | 'google_sheets';
    summary: Record<string, number>;
    issues: OnboardingImportPreviewIssue[];
    payload?: {
        organization_name?: string;
        organization_description?: string;
        country: string;
        currency: string;
        profile_type: 'freelance' | 'company' | 'agency';
        team_members: Array<{
            name: string;
            role: string;
            salary_monthly_brute: string;
            currency: string;
            billable_hours_per_month: number;
        }>;
        expenses: Array<{
            name: string;
            category: 'rent' | 'software' | 'services';
            amount_monthly: string;
            currency: string;
            quantity: number;
        }>;
        inventory_items: Array<{
            name: string;
            category: string;
            amount_monthly?: string;
            purchase_price?: string;
            useful_life_months?: number;
            salvage_value?: string;
            purchase_date?: string;
            depreciation_method?: 'straight_line' | 'declining_balance';
            currency: string;
            quantity: number;
            amortizable: boolean;
        }>;
    };
    temporary_bcr?: {
        blended_cost_rate: string;
        total_monthly_costs: string;
        total_fixed_overhead: string;
        total_salaries: string;
        total_monthly_hours: number;
        team_members_count: number;
        currency: string;
        note: string;
    };
};

export const onboardingService = {

    getTemplates: async (): Promise<FixedCostTemplate[]> => {
        const response = await apiRequest<OnboardingTemplatesResponse>('/onboarding/templates');
        if (response.error || !response.data?.items) return [];
        return response.data.items;
    },

    getDraft: async <T>(): Promise<T | null> => {
        const response = await apiRequest<OnboardingDraftResponse>('/onboarding/draft');
        if (response.error || !response.data?.data) return null;
        return response.data.data as T;
    },

    saveDraft: async <T extends Record<string, unknown>>(data: T): Promise<boolean> => {
        const response = await apiRequest<OnboardingDraftResponse>('/onboarding/draft', {
            method: 'POST',
            body: JSON.stringify({ data }),
        });
        return !response.error;
    },

    downloadImportTemplate: async (): Promise<{ ok: boolean; error?: string }> => {
        const baseUrl = process.env.NEXT_PUBLIC_API_URL?.replace(/\/+$/, '');
        if (!baseUrl) return { ok: false, error: 'NEXT_PUBLIC_API_URL no configurada' };
        const token = getAuthToken();

        try {
            const response = await fetch(`${baseUrl}/onboarding/import-template/excel`, {
                method: 'GET',
                headers: token ? { Authorization: `Bearer ${token}` } : {},
            });
            if (!response.ok) {
                const errorBody = await response.json().catch(() => ({}));
                return { ok: false, error: errorBody?.detail || `Error ${response.status}` };
            }
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'onboarding-import-template.xlsx';
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(url);
            return { ok: true };
        } catch (error) {
            return { ok: false, error: error instanceof Error ? error.message : 'Error descargando plantilla' };
        }
    },

    previewImportExcel: async (file: File): Promise<{ data?: OnboardingImportPreviewResponse; error?: string }> => {
        const baseUrl = process.env.NEXT_PUBLIC_API_URL?.replace(/\/+$/, '');
        if (!baseUrl) return { error: 'NEXT_PUBLIC_API_URL no configurada' };
        const token = getAuthToken();
        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch(`${baseUrl}/onboarding/import-preview/excel`, {
                method: 'POST',
                headers: token ? { Authorization: `Bearer ${token}` } : {},
                body: formData,
            });
            if (!response.ok) {
                const errorBody = await response.json().catch(() => ({}));
                return { error: errorBody?.detail || `Error ${response.status}` };
            }
            const data = (await response.json()) as OnboardingImportPreviewResponse;
            return { data };
        } catch (error) {
            return { error: error instanceof Error ? error.message : 'Error cargando archivo' };
        }
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
        amount: number | string | null | undefined,
        from: string,
        to: string,
        rates: Record<string, { rate: number; lastUpdated: string }> = {}
    ): number => {
        const normalizedAmount = Number(amount);
        const safeAmount = Number.isFinite(normalizedAmount) ? normalizedAmount : 0;
        if (from === to) return safeAmount;
        const fromRate = Number(rates[from]?.rate);
        const toRate = Number(rates[to]?.rate);
        if (!Number.isFinite(fromRate) || fromRate <= 0 || !Number.isFinite(toRate) || toRate <= 0) return safeAmount;
        const converted = (safeAmount / fromRate) * toRate;
        return Number.isFinite(converted) ? converted : safeAmount;
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
