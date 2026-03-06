import { apiRequest } from '@/lib/api-client';

export type CurrencyOption = {
  code: string;
  symbol: string;
  name: string;
};

export type CurrencySettingsResponse = {
  primary_currency: string;
  currency_symbol: string;
  available_currencies: CurrencyOption[];
};

export const settingsService = {
  async getCurrencySettings(): Promise<CurrencySettingsResponse | null> {
    const response = await apiRequest<CurrencySettingsResponse>('/settings/currency');
    if (response.error || !response.data) {
      return null;
    }
    return response.data;
  },

  async getPrimaryCurrency(): Promise<string | null> {
    const settings = await this.getCurrencySettings();
    if (!settings?.primary_currency) {
      return null;
    }
    return settings.primary_currency;
  },

  async updatePrimaryCurrency(primaryCurrency: string): Promise<CurrencySettingsResponse | null> {
    const response = await apiRequest<CurrencySettingsResponse>('/settings/currency', {
      method: 'PUT',
      body: JSON.stringify({ primary_currency: primaryCurrency }),
    });
    if (response.error || !response.data) {
      return null;
    }
    return response.data;
  },
};
