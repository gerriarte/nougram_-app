/**
 * ESTÁNDAR NOUGRAM: Transformador de respuestas API
 * Convierte strings Decimal del backend a objetos Dinero
 * 
 * CRÍTICO: Currency es OBLIGATORIO. Si falta, lanza error en producción.
 */
import { type Dinero } from 'dinero.js';
import { fromAPIString, CURRENCY_CONFIG } from './money';

/**
 * Lista de campos que son montos monetarios (Decimal serializados como string)
 */
const MONEY_FIELDS = [
  'total_internal_cost',
  'total_client_price',
  'total_expenses_cost',
  'total_expenses_client_price',
  'total_taxes',
  'total_with_taxes',
  'revisions_cost',
  'internal_cost',
  'client_price',
  'amount',
  'cost',
  'price',
  'salary',
  'blended_cost_rate',
  'total_monthly_costs',
  'total_fixed_overhead',
  'total_tools_costs',
  'total_salaries',
  'break_even_monthly_cost',
  'total_annual_revenue',
  'revenue',
  'expense_cost',
  'markup_percentage',
  'margin_percentage',
  'net_profit_amount',
  // Agregar más según necesidad
] as const;

/**
 * Detecta la moneda desde el objeto de respuesta
 * ESTÁNDAR NOUGRAM: Currency es OBLIGATORIO, lanza error si falta
 * 
 * CRÍTICO: No usar default porque puede causar errores si una cuenta tiene
 * proyectos en USD y otros en COP. El transformador debe fallar explícitamente.
 */
function detectCurrency(data: any): string {
  // Prioridad 1: Campo explícito currency
  if (data.currency && typeof data.currency === 'string') {
    const currency = data.currency.toUpperCase();
    if (CURRENCY_CONFIG[currency]) {
      return currency;
    }
    throw new Error(
      `Invalid currency: ${data.currency}. Expected: USD, COP, EUR, ARS`
    );
  }
  
  // Prioridad 2: Campo primary_currency (para respuestas de settings)
  if (data.primary_currency && typeof data.primary_currency === 'string') {
    const currency = data.primary_currency.toUpperCase();
    if (CURRENCY_CONFIG[currency]) {
      return currency;
    }
  }
  
  // Prioridad 3: Detectar desde items anidados (para quotes con items)
  if (data.items && Array.isArray(data.items) && data.items.length > 0) {
    try {
      const firstItemCurrency = detectCurrency(data.items[0]);
      if (firstItemCurrency) {
        return firstItemCurrency;
      }
    } catch {
      // Si items tampoco tienen currency, continuar al error final
    }
  }
  
  // CRÍTICO: No usar default, lanzar error
  throw new Error(
    `Currency is required but not found in API response. ` +
    `Response must include 'currency' or 'primary_currency' field. ` +
    `Received keys: ${JSON.stringify(Object.keys(data))}`
  );
}

/**
 * Transforma respuesta de API convirtiendo strings Decimal a Dinero
 * ESTÁNDAR NOUGRAM: Detecta campos monetarios y los convierte automáticamente
 * 
 * CRÍTICO: Currency es OBLIGATORIO. Si falta, lanza error en producción.
 * En desarrollo, usa USD como fallback con warning.
 */
export function transformAPIResponse<T>(
  data: any,
  currency?: string  // Opcional solo si viene explícitamente del contexto (ej: desde hook)
): T {
  if (!data || typeof data !== 'object') {
    return data;
  }
  
  // Si es array, transformar cada elemento (cada elemento debe tener su currency)
  if (Array.isArray(data)) {
    return data.map(item => {
      // Cada item debe tener su propia currency
      try {
        const itemCurrency = detectCurrency(item);
        return transformAPIResponse(item, itemCurrency);
      } catch (error) {
        // Si falla, intentar con currency del contexto si existe
        if (currency) {
          return transformAPIResponse(item, currency);
        }
        throw error;
      }
    }) as T;
  }
  
  const transformed = { ...data };
  let detectedCurrency = currency;
  
  for (const [key, value] of Object.entries(data)) {
    // Si el campo es un monto monetario y es string
    if (MONEY_FIELDS.includes(key as any) && typeof value === 'string') {
      try {
        if (!detectedCurrency) {
          try {
            detectedCurrency = detectCurrency(data);
          } catch (error) {
            console.error('[Money Transformer] Currency detection failed:', error);
            if (process.env.NODE_ENV === 'development') {
              console.warn(
                '[Money Transformer] Using USD as fallback. ' +
                'Fix API response to include currency field.'
              );
              detectedCurrency = 'USD';
            } else {
              throw new Error(
                `Currency required for money transformation. ${error instanceof Error ? error.message : String(error)}`
              );
            }
          }
        }

        // Convertir string Decimal a Dinero
        transformed[key] = fromAPIString(value, detectedCurrency);
      } catch (error) {
        console.warn(`Failed to transform money field ${key}:`, error);
        // Mantener valor original si falla la transformación
        transformed[key] = value;
      }
    } else if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
      // Recursión para objetos anidados (pasar currency detectada)
      transformed[key] = transformAPIResponse(value, detectedCurrency);
    } else if (Array.isArray(value)) {
      // Transformar arrays recursivamente
      transformed[key] = value.map(item => 
        typeof item === 'object' && item !== null
          ? transformAPIResponse(item, detectedCurrency)
          : item
      );
    }
  }
  
  return transformed as T;
}
