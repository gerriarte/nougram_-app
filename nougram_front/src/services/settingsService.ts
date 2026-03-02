import { apiRequest } from '@/lib/api-client';

export type CurrencySettingsResponse = {
  primary_currency: string;
  currency_symbol: string;
  available_currencies: string[];
};

export const settingsService = {
  async getPrimaryCurrency(): Promise<string | null> {
    const response = await apiRequest<CurrencySettingsResponse>('/settings/currency');
    if (response.error || !response.data?.primary_currency) {
      return null;
    }
    return response.data.primary_currency;
  },
};
