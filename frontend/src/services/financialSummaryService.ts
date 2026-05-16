import { apiRequest } from '@/lib/api-client';

type FinancialSummaryResponse = {
  monthlyFixedCosts: number;
  monthlyPayroll: number;
  totalBillableHours: number;
  blendedCostRate: number;
  activeTeamMembers: number;
  currency: string;
};

export const financialSummaryService = {
  async get(): Promise<FinancialSummaryResponse | null> {
    const response = await apiRequest<FinancialSummaryResponse>('/admin/financial-summary');
    if (response.error || !response.data) return null;
    return response.data;
  },
};

