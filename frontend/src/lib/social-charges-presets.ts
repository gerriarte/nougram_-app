import { Currency, SocialChargesConfig } from '@/types/admin';

type PresetMeta = {
  countryCode: string;
  countryLabel: string;
  presetKey: string;
  percentages: Omit<SocialChargesConfig, 'enable_social_charges' | 'total_percentage'>;
};

const PRESETS_BY_COUNTRY: Record<string, PresetMeta> = {
  CO: {
    countryCode: 'CO',
    countryLabel: 'Colombia',
    presetKey: 'CO',
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
  MX: {
    countryCode: 'MX',
    countryLabel: 'Mexico',
    presetKey: 'MX',
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
  PE: {
    countryCode: 'PE',
    countryLabel: 'Peru',
    presetKey: 'PE',
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
  AR: {
    countryCode: 'AR',
    countryLabel: 'Argentina',
    presetKey: 'AR',
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
  US: {
    countryCode: 'US',
    countryLabel: 'United States',
    presetKey: 'US',
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
  EU: {
    countryCode: 'EU',
    countryLabel: 'Eurozone',
    presetKey: 'EU',
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

const COUNTRY_BY_CURRENCY: Record<Currency, string> = {
  COP: 'CO',
  MXN: 'MX',
  PEN: 'PE',
  ARS: 'AR',
  USD: 'US',
  EUR: 'EU',
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
  const countryCode = COUNTRY_BY_CURRENCY[currency] || 'US';
  return PRESETS_BY_COUNTRY[countryCode] || PRESETS_BY_COUNTRY.US;
}

export function getSocialChargesPresetMetaByCountry(countryCode?: string): PresetMeta {
  if (!countryCode) return PRESETS_BY_COUNTRY.US;
  const normalized = countryCode.toUpperCase();
  return PRESETS_BY_COUNTRY[normalized] || PRESETS_BY_COUNTRY.US;
}

export function listSocialChargesPresetMeta(): PresetMeta[] {
  return Object.values(PRESETS_BY_COUNTRY);
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
    country_code: preset.countryCode,
    preset_key: preset.presetKey,
    version: 1,
    updated_at: new Date().toISOString(),
  };
}

export function buildSocialChargesConfigFromCountry(
  countryCode: string,
  enabled = false
): SocialChargesConfig {
  const preset = getSocialChargesPresetMetaByCountry(countryCode);
  return {
    enable_social_charges: enabled,
    ...preset.percentages,
    total_percentage: computeTotal(preset.percentages),
    country_code: preset.countryCode,
    preset_key: preset.presetKey,
    version: 1,
    updated_at: new Date().toISOString(),
  };
}
