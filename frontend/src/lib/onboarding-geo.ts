export type SupportedCurrencyCode = 'USD' | 'COP' | 'ARS' | 'EUR' | 'PEN' | 'MXN';
export type SupportedCountryCode = 'COL' | 'USA' | 'ARG' | 'MEX' | 'PER' | 'ESP';

export const SUPPORTED_CURRENCIES: Array<{ code: SupportedCurrencyCode; label: string }> = [
    { code: 'COP', label: 'COP - Peso Colombiano' },
    { code: 'USD', label: 'USD - Dólar Estadounidense' },
    { code: 'ARS', label: 'ARS - Peso Argentino' },
    { code: 'EUR', label: 'EUR - Euro' },
    { code: 'PEN', label: 'PEN - Sol Peruano' },
    { code: 'MXN', label: 'MXN - Peso Mexicano' },
];

export const SUPPORTED_COUNTRIES: Array<{ code: SupportedCountryCode; label: string }> = [
    { code: 'COL', label: 'Colombia' },
    { code: 'USA', label: 'Estados Unidos' },
    { code: 'ARG', label: 'Argentina' },
    { code: 'MEX', label: 'México' },
    { code: 'PER', label: 'Perú' },
    { code: 'ESP', label: 'España' },
];

const COUNTRY_ALIASES: Record<string, SupportedCountryCode> = {
    COL: 'COL',
    COLOMBIA: 'COL',
    USA: 'USA',
    US: 'USA',
    UNITEDSTATES: 'USA',
    ARG: 'ARG',
    ARGENTINA: 'ARG',
    MEX: 'MEX',
    MEXICO: 'MEX',
    MX: 'MEX',
    PER: 'PER',
    PERU: 'PER',
    ESP: 'ESP',
    SPAIN: 'ESP',
    ESPANA: 'ESP',
    ESPAÑA: 'ESP',
};

const CURRENCY_ALIASES: Record<string, SupportedCurrencyCode> = {
    USD: 'USD',
    COP: 'COP',
    ARS: 'ARS',
    EUR: 'EUR',
    PEN: 'PEN',
    MXN: 'MXN',
};

function normalizeKey(value?: string): string {
    if (!value) return '';
    return value.trim().toUpperCase().replace(/\s+/g, '');
}

export function normalizeCountryCode(value?: string): SupportedCountryCode | null {
    const key = normalizeKey(value);
    if (!key) return null;
    return COUNTRY_ALIASES[key] || null;
}

export function normalizeCurrencyCode(value?: string): SupportedCurrencyCode | null {
    const key = normalizeKey(value);
    if (!key) return null;
    return CURRENCY_ALIASES[key] || null;
}

