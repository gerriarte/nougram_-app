import { Currency, SocialChargesConfig } from '@/types/admin';

type PresetMeta = {
  countryCode: string;
  countryLabel: string;
  percentages: Omit<SocialChargesConfig, 'enable_social_charges' | 'total_percentage'>;
};

const PRESETS_BY_CURRENCY: Record<Currency, PresetMeta> = {
  COP: {
    countryCode: 'CO',
    countryLabel: 'Colombia',
    percentages: {
      health_percentage: 8.5,
      pension_percentage: 12.0,
      arl_percentage: 0.522,
      parafiscales_percentage: 4.0,
      prima_services_percentage: 8.33,
      cesantias_percentage: 8.33,
      int_cesantias_percentage: 1.0,
      vacations_percentage: 4.17,
    },
  },
  MXN: {
    countryCode: 'MX',
    countryLabel: 'Mexico',
    percentages: {
      health_percentage: 7.58,
      pension_percentage: 5.15,
      arl_percentage: 2.0,
      parafiscales_percentage: 3.0,
      prima_services_percentage: 8.33,
      cesantias_percentage: 2.0,
      int_cesantias_percentage: 0.0,
      vacations_percentage: 4.17,
    },
  },
  PEN: {
    countryCode: 'PE',
    countryLabel: 'Peru',
    percentages: {
      health_percentage: 9.0,
      pension_percentage: 13.0,
      arl_percentage: 0.8,
      parafiscales_percentage: 0.0,
      prima_services_percentage: 8.33,
      cesantias_percentage: 0.0,
      int_cesantias_percentage: 0.0,
      vacations_percentage: 8.33,
    },
  },
  ARS: {
    countryCode: 'AR',
    countryLabel: 'Argentina',
    percentages: {
      health_percentage: 6.0,
      pension_percentage: 10.17,
      arl_percentage: 3.0,
      parafiscales_percentage: 7.83,
      prima_services_percentage: 8.33,
      cesantias_percentage: 0.0,
      int_cesantias_percentage: 0.0,
      vacations_percentage: 4.17,
    },
  },
  USD: {
    countryCode: 'US',
    countryLabel: 'United States',
    percentages: {
      health_percentage: 1.45,
      pension_percentage: 6.2,
      arl_percentage: 1.0,
      parafiscales_percentage: 5.0,
      prima_services_percentage: 0.0,
      cesantias_percentage: 0.0,
      int_cesantias_percentage: 0.0,
      vacations_percentage: 4.17,
    },
  },
  EUR: {
    countryCode: 'EU',
    countryLabel: 'Eurozone',
    percentages: {
      health_percentage: 8.0,
      pension_percentage: 12.0,
      arl_percentage: 1.5,
      parafiscales_percentage: 6.5,
      prima_services_percentage: 0.0,
      cesantias_percentage: 0.0,
      int_cesantias_percentage: 0.0,
      vacations_percentage: 4.17,
    },
  },
};

function computeTotal(
  percentages: Omit<SocialChargesConfig, 'enable_social_charges' | 'total_percentage'>
): number {
  return (
    percentages.health_percentage +
    percentages.pension_percentage +
    percentages.arl_percentage +
    percentages.parafiscales_percentage +
    percentages.prima_services_percentage +
    percentages.cesantias_percentage +
    percentages.int_cesantias_percentage +
    percentages.vacations_percentage
  );
}

export function getSocialChargesPresetMeta(currency: Currency): PresetMeta {
  return PRESETS_BY_CURRENCY[currency] || PRESETS_BY_CURRENCY.USD;
}

export function buildSocialChargesConfigFromCurrency(
  currency: Currency,
  enabled = false
): SocialChargesConfig {
  const preset = getSocialChargesPresetMeta(currency);
  return {
    enable_social_charges: enabled,
    ...preset.percentages,
    total_percentage: computeTotal(preset.percentages),
  };
}
