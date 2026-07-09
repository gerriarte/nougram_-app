import { Currency, SocialChargesConfig } from '@/types/admin';

type PresetMeta = {
  countryCode: string;
  countryLabel: string;
  presetKey: string;
  // Total patronal curado (fuente de verdad para el BCR). Si se omite, se usa
  // la suma del desglose. Se declara explícito cuando el headline oficial no
  // coincide con la suma de los componentes (ej. Colombia: 52.852 vs 46.852).
  totalPercentage?: number;
  percentages: Omit<SocialChargesConfig, 'enable_social_charges' | 'total_percentage'>;
};

const PRESETS_BY_COUNTRY: Record<string, PresetMeta> = {
  CO: {
    countryCode: 'CO',
    countryLabel: 'Colombia',
    presetKey: 'CO',
    // Headline patronal Colombia (incluye SENA+ICBF+Caja completos). El desglose
    // de abajo es informativo/aproximado y no suma exactamente este total.
    totalPercentage: 52.852,
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

// Año de vigencia de las tasas curadas en este archivo. Para actualizar las
// cargas: editar los porcentajes de PRESETS_BY_COUNTRY y subir este año.
// Se persiste en el config de cada org para poder señalar staleness en la UI.
export const SOCIAL_CHARGES_EFFECTIVE_YEAR = 2026;

// Alias de códigos de país: el onboarding usa ISO-3 (COL, MEX, ARG, USA, PER,
// ESP) mientras los presets se indexan por ISO-2/región (CO, MX, AR, US, PE, EU).
const COUNTRY_CODE_ALIASES: Record<string, string> = {
  COL: 'CO',
  COLOMBIA: 'CO',
  MEX: 'MX',
  MEXICO: 'MX',
  ARG: 'AR',
  ARGENTINA: 'AR',
  USA: 'US',
  PER: 'PE',
  PERU: 'PE',
  ESP: 'EU', // España usa el preset de la Eurozona
  SPAIN: 'EU',
};

function resolvePresetKey(countryCode: string): string {
  const normalized = countryCode.toUpperCase();
  if (PRESETS_BY_COUNTRY[normalized]) return normalized;
  return COUNTRY_CODE_ALIASES[normalized] || normalized;
}

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
  const resolved = resolvePresetKey(countryCode);
  return PRESETS_BY_COUNTRY[resolved] || PRESETS_BY_COUNTRY.US;
}

/** True si el país (ISO-2/3) tiene un preset de cargas sociales curado. */
export function hasSocialChargesPreset(countryCode?: string): boolean {
  if (!countryCode) return false;
  return Boolean(PRESETS_BY_COUNTRY[resolvePresetKey(countryCode)]);
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
    total_percentage: preset.totalPercentage ?? computeTotal(preset.percentages),
    country_code: preset.countryCode,
    preset_key: preset.presetKey,
    effective_year: SOCIAL_CHARGES_EFFECTIVE_YEAR,
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
    total_percentage: preset.totalPercentage ?? computeTotal(preset.percentages),
    country_code: preset.countryCode,
    preset_key: preset.presetKey,
    effective_year: SOCIAL_CHARGES_EFFECTIVE_YEAR,
    version: 1,
    updated_at: new Date().toISOString(),
  };
}
