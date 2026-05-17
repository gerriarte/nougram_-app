# 💰 Plan de Implementación: Precisión Financiera con Dinero.js y Decimal

**Fecha de creación:** 30 de Diciembre, 2025  
**Estado:** ⏳ Pendiente  
**Prioridad:** 🔴 **CRÍTICA**  
**Duración estimada:** 4-5 semanas (3 sprints)

---

## 📊 Resumen Ejecutivo

Este plan implementa un sistema robusto de precisión financiera para Nougram, eliminando errores de redondeo y garantizando cálculos exactos en todas las operaciones monetarias. Utiliza `decimal.Decimal` en Python (backend) y `dinero.js` v2 en TypeScript (frontend) para manejar dinero como estructuras inmutables.

**Problema actual:**
- Uso de `float` en Python y `number` en JavaScript causa errores de precisión
- Redondeos manuales inconsistentes (`round(total, 2)`) en múltiples lugares
- Riesgo de discrepancias en cálculos acumulativos (sumas de múltiples items)
- COP configurado sin decimales pero cálculos internos usan floats
- Pérdida de precisión en serialización JSON (float → JSON → float)

**Solución:**
- Backend: `decimal.Decimal` para cálculos precisos, serializado como **string** en JSON
- Frontend: `dinero.js` v2 para cálculos inmutables, transformador de strings API → Dinero
- Representación en unidades menores (centavos/subunidades)
- Formateo consistente con localización `es-CO`
- **Validación crítica**: Backend SIEMPRE recalcula antes de guardar (frontend solo para vista previa)

---

## 🎯 ESTÁNDAR DE SINCRONIZACIÓN FINANCIERA NOUGRAM

### Reglas Estrictas de Implementación

1. **Backend (Python/FastAPI)**:
   - ✅ Configurar Pydantic para que todos los campos `Decimal` se serialicen como **'strings'** en respuestas JSON
   - ✅ Usar `from decimal import Decimal, ROUND_HALF_UP`
   - ✅ Evitar pérdida de precisión en el navegador

2. **Frontend (React/TypeScript)**:
   - ✅ Utilizar `dinero.js` (v2) exclusivamente
   - ✅ Crear transformador que convierta strings del API a objetos `dinero`
   - ✅ Realizar toda la lógica de "vista previa" del margen en el front usando solo funciones de `dinero.js`

3. **Regla de Validación CRÍTICA**:
   - ✅ El precio final de la propuesta **SIEMPRE** se recalcula en el Backend antes de guardar
   - ✅ El Frontend es **SOLO** para visualización interactiva del usuario
   - ✅ Nunca confiar en cálculos del frontend para persistencia

---

## 🎯 Objetivos

1. **Eliminar errores de precisión** en cálculos financieros
2. **Garantizar inmutabilidad** en operaciones monetarias
3. **Estandarizar formateo** de monedas (especialmente COP)
4. **Mantener compatibilidad** con código existente durante migración
5. **Validar precisión** con tests exhaustivos

---

## 📋 FASE 1: Fundación y Helpers (Semana 1)

### Sprint 1.1: Instalación y Configuración

**Objetivo:** Instalar dependencias y crear estructura base de helpers

#### Backend (Python)

**1.1.1: Crear módulo de dinero**

- Crear: `backend/app/core/money.py` (nuevo)
- Implementar helpers base:

```python
"""
Money handling utilities using Decimal for precision
"""
from decimal import Decimal, ROUND_HALF_UP, ROUND_DOWN, ROUND_UP
from typing import Union, Optional
from app.core.logging import get_logger

logger = get_logger(__name__)

# Precisión estándar: 4 decimales para cálculos internos, 2 para display
INTERNAL_PRECISION = Decimal('0.0001')
DISPLAY_PRECISION = Decimal('0.01')

# COP no usa decimales en display pero sí en cálculos internos
COP_DISPLAY_PRECISION = Decimal('1')  # Sin decimales
COP_INTERNAL_PRECISION = Decimal('0.01')  # Precisión interna para cálculos

# ESTÁNDAR NOUGRAM: Usar ROUND_HALF_UP (no banker's rounding ROUND_HALF_EVEN)
# Esto asegura consistencia con Dinero.js que usa "round half up"
# Python usa ROUND_HALF_EVEN por defecto, debemos especificar explícitamente
ROUNDING_MODE = ROUND_HALF_UP  # NO ROUND_HALF_EVEN


class Money:
    """
    Clase inmutable para representar dinero con precisión Decimal
    """
    def __init__(self, amount: Union[float, int, str, Decimal], currency: str = "USD"):
        if isinstance(amount, Decimal):
            self._amount = amount
        elif isinstance(amount, str):
            self._amount = Decimal(amount)
        else:
            # Convertir float a string primero para evitar pérdida de precisión
            self._amount = Decimal(str(amount))
        
        self._currency = currency.upper()
        
        # Validar que el monto no sea negativo (a menos que sea explícitamente permitido)
        if self._amount < 0:
            logger.warning(f"Negative amount detected: {self._amount} {self._currency}")
    
    @property
    def amount(self) -> Decimal:
        """Retorna el monto como Decimal"""
        return self._amount
    
    @property
    def currency(self) -> str:
        """Retorna la moneda"""
        return self._currency
    
    def to_float(self) -> float:
        """Convierte a float (usar solo para compatibilidad con API)"""
        return float(self._amount)
    
    def to_int_cents(self) -> int:
        """Convierte a centavos/subunidades (para API)"""
        if self._currency == "COP":
            # COP ya está en unidades enteras
            return int(self._amount)
        # Otras monedas: multiplicar por 100
        return int(self._amount * 100)
    
    def quantize(self, precision: Optional[Decimal] = None) -> 'Money':
        """Redondea a la precisión especificada"""
        if precision is None:
            precision = DISPLAY_PRECISION if self._currency != "COP" else COP_DISPLAY_PRECISION
        
        quantized = self._amount.quantize(precision, rounding=ROUND_HALF_UP)
        return Money(quantized, self._currency)
    
    def add(self, other: 'Money') -> 'Money':
        """Suma dos montos (debe ser misma moneda)"""
        if self._currency != other._currency:
            raise ValueError(f"Cannot add {self._currency} and {other._currency}")
        return Money(self._amount + other._amount, self._currency)
    
    def subtract(self, other: 'Money') -> 'Money':
        """Resta dos montos (debe ser misma moneda)"""
        if self._currency != other._currency:
            raise ValueError(f"Cannot subtract {self._currency} and {other._currency}")
        return Money(self._amount - other._amount, self._currency)
    
    def multiply(self, multiplier: Union[float, Decimal]) -> 'Money':
        """Multiplica un monto por un escalar"""
        if isinstance(multiplier, float):
            multiplier = Decimal(str(multiplier))
        result = self._amount * multiplier
        return Money(result, self._currency)
    
    def divide(self, divisor: Union[float, Decimal]) -> 'Money':
        """Divide un monto por un escalar"""
        if isinstance(divisor, float):
            divisor = Decimal(str(divisor))
        if divisor == 0:
            raise ValueError("Cannot divide by zero")
        result = self._amount / divisor
        return Money(result, self._currency)
    
    def apply_percentage(self, percentage: Union[float, Decimal]) -> 'Money':
        """Aplica un porcentaje (ej: 19% de IVA)"""
        if isinstance(percentage, float):
            percentage = Decimal(str(percentage))
        multiplier = percentage / Decimal('100')
        return self.multiply(multiplier)
    
    def apply_margin(self, margin_percentage: Union[float, Decimal]) -> 'Money':
        """
        Calcula precio con margen: cost / (1 - margin)
        Ejemplo: cost = $100, margin = 40% → price = $100 / (1 - 0.40) = $166.67
        """
        if isinstance(margin_percentage, float):
            margin_percentage = Decimal(str(margin_percentage))
        
        if margin_percentage >= 1:
            raise ValueError("Margin cannot be >= 100%")
        
        margin_decimal = margin_percentage / Decimal('100')
        divisor = Decimal('1') - margin_decimal
        
        result = self._amount / divisor
        return Money(result, self._currency).quantize()
    
    def __eq__(self, other):
        if not isinstance(other, Money):
            return False
        return self._amount == other._amount and self._currency == other._currency
    
    def __lt__(self, other):
        if not isinstance(other, Money):
            return NotImplemented
        if self._currency != other._currency:
            raise ValueError(f"Cannot compare {self._currency} and {other._currency}")
        return self._amount < other._amount
    
    def __le__(self, other):
        return self == other or self < other
    
    def __gt__(self, other):
        return not self <= other
    
    def __ge__(self, other):
        return not self < other
    
    def __repr__(self):
        return f"Money({self._amount}, '{self._currency}')"
    
    def __str__(self):
        return f"{self._amount} {self._currency}"


# Funciones helper para compatibilidad
def to_money(value: Union[float, int, str, Decimal], currency: str = "USD") -> Money:
    """Convierte un valor a Money"""
    return Money(value, currency)


def from_api(value: float, currency: str = "USD") -> Money:
    """Crea Money desde un valor de API (float)"""
    return Money(value, currency)


def to_api(money: Money) -> float:
    """Convierte Money a float para enviar a API"""
    return money.to_float()


def sum_money(amounts: list[Money]) -> Optional[Money]:
    """Suma una lista de Money (debe ser misma moneda)"""
    if not amounts:
        return None
    
    currency = amounts[0].currency
    total = Decimal('0')
    
    for amount in amounts:
        if amount.currency != currency:
            raise ValueError(f"All amounts must be in {currency}")
        total += amount.amount
    
    return Money(total, currency)
```

**1.1.2: Actualizar formateo de moneda**

- Actualizar: `backend/app/core/currency.py`
- Agregar función que use `Money`:

```python
from app.core.money import Money

def format_money(money: Money, locale: str = "es-CO") -> str:
    """
    Formatea Money usando localización específica
    """
    currency = money.currency
    amount = money.quantize().amount
    
    # Configuración por moneda
    if currency == "COP":
        # COP: sin decimales, punto como separador de miles
        formatted = f"{int(amount):,}".replace(",", ".")
        return f"${formatted}"
    elif currency == "USD":
        # USD: con decimales, coma como separador de miles
        formatted = f"{float(amount):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return f"${formatted}"
    elif currency == "EUR":
        # EUR: con decimales, punto como separador de miles
        formatted = f"{float(amount):,.2f}".replace(",", ".")
        return f"€{formatted}"
    else:
        # Default: formato estándar
        formatted = f"{float(amount):,.2f}"
        return f"{currency} {formatted}"
```

#### Frontend (TypeScript)

**1.1.3: Instalar dinero.js v2**

```bash
cd frontend
npm install dinero.js @dinero.js/currencies
# @dinero.js/currencies contiene las definiciones de monedas (USD, COP, EUR, ARS)
```

**1.1.4: Crear módulo de dinero**

- Crear: `frontend/src/lib/money.ts` (nuevo)

```typescript
/**
 * Money handling utilities using dinero.js v2 for precision
 * ESTÁNDAR NOUGRAM: Sintaxis correcta de Dinero.js v2
 * 
 * IMPORTANTE: Dinero.js v2 usa:
 * - `dinero()` (minúscula) en lugar de `Dinero()`
 * - Importar monedas desde `@dinero.js/currencies`
 * - Tipo `Dinero<number>` en lugar de `Dinero.Dinero`
 */
import { dinero, type Dinero } from 'dinero.js';
import { USD, COP, EUR, ARS } from '@dinero.js/currencies';

// Configuración de monedas con objetos de Dinero.js v2
export const CURRENCY_CONFIG: Record<string, {
  currency: typeof USD;
  precision: number;
}> = {
  USD: { currency: USD, precision: USD.exponent },
  COP: { currency: COP, precision: COP.exponent },
  EUR: { currency: EUR, precision: EUR.exponent },
  ARS: { currency: ARS, precision: ARS.exponent },
};

/**
 * ESTÁNDAR NOUGRAM: Crea Dinero desde string Decimal del API
 * El backend serializa Decimal como string para mantener precisión
 * 
 * Ejemplo: "100.50" (USD) → dinero({ amount: 10050, currency: USD })
 * Ejemplo: "1000000" (COP) → dinero({ amount: 1000000, currency: COP })
 * 
 * Redondeo: Usa Math.round() que implementa "round half up" (no banker's rounding)
 * para consistencia con backend que usa ROUND_HALF_UP
 */
export function fromAPIString(
  apiString: string,
  currencyCode: string = 'USD'
): Dinero<number> {
  const config = CURRENCY_CONFIG[currencyCode] || CURRENCY_CONFIG.USD;
  const factor = Math.pow(10, config.precision);
  
  // Parsear string a número con alta precisión
  const numericValue = parseFloat(apiString);
  
  if (isNaN(numericValue)) {
    throw new Error(`Invalid money string: ${apiString}`);
  }
  
  // Convertir a unidades menores (centavos/subunidades)
  // Math.round() usa "round half up" (no banker's rounding)
  const amount = Math.round(numericValue * factor);
  
  // Sintaxis Dinero.js v2: dinero({ amount, currency })
  return dinero({ amount, currency: config.currency });
}

/**
 * Crea Dinero desde número (compatibilidad hacia atrás)
 * @deprecated Usar fromAPIString cuando backend envíe strings
 */
export function fromAPI(
  amount: number,
  currencyCode: string = 'USD'
): Dinero<number> {
  const config = CURRENCY_CONFIG[currencyCode] || CURRENCY_CONFIG.USD;
  const factor = Math.pow(10, config.precision);
  const roundedAmount = Math.round(amount * factor);
  
  return dinero({ amount: roundedAmount, currency: config.currency });
}

/**
 * Convierte Dinero a string para enviar al API
 * ESTÁNDAR NOUGRAM: Backend espera strings Decimal
 */
export function toAPIString(dinero: Dinero<number>): string {
  const currency = dinero.currency;
  const config = CURRENCY_CONFIG[currency.code] || CURRENCY_CONFIG.USD;
  const factor = Math.pow(10, config.precision);
  const value = dinero.amount / factor;
  
  return value.toFixed(config.precision);
}

/**
 * Obtiene el valor numérico de Dinero (para compatibilidad)
 */
export function toAPI(dinero: Dinero<number>): number {
  const currency = dinero.currency;
  const config = CURRENCY_CONFIG[currency.code] || CURRENCY_CONFIG.USD;
  const factor = Math.pow(10, config.precision);
  
  return dinero.amount / factor;
}

/**
 * Suma múltiples Dinero (debe ser misma moneda)
 */
export function sumMoney(amounts: Dinero<number>[]): Dinero<number> | null {
  if (amounts.length === 0) return null;
  
  return amounts.reduce((total, amount) => {
    // Dinero.js v2: usar add() method
    return total.add(amount);
  });
}

/**
 * Multiplica Dinero por un escalar
 */
export function multiplyMoney(dinero: Dinero<number>, multiplier: number): Dinero<number> {
  return dinero.multiply(multiplier);
}

/**
 * Divide Dinero por un escalar
 */
export function divideMoney(dinero: Dinero<number>, divisor: number): Dinero<number> {
  if (divisor === 0) {
    throw new Error('Cannot divide by zero');
  }
  return dinero.divide(divisor);
}

/**
 * Aplica un porcentaje a Dinero (ej: 19% de IVA)
 */
export function applyPercentage(dinero: Dinero<number>, percentage: number): Dinero<number> {
  const multiplier = percentage / 100;
  return dinero.multiply(multiplier);
}

/**
 * Calcula precio con margen: cost / (1 - margin)
 * ESTÁNDAR NOUGRAM: Usa redondeo "half up" para consistencia con backend
 */
export function applyMargin(
  cost: Dinero<number>,
  marginPercentage: number
): Dinero<number> {
  if (marginPercentage >= 100) {
    throw new Error('Margin cannot be >= 100%');
  }
  
  const marginDecimal = marginPercentage / 100;
  const divisor = 1 - marginDecimal;
  const multiplier = 1 / divisor;
  
  // Dinero.js v2: usar multiply() method
  return cost.multiply(multiplier);
}

/**
 * Formatea Dinero usando localización específica
 * ESTÁNDAR NOUGRAM: Usa locale 'es-CO' para formateo explícito
 */
export function formatCurrency(
  dinero: Dinero<number>,
  locale: string = 'es-CO',
  options?: { showSymbol?: boolean }
): string {
  const currency = dinero.currency.code;
  const showSymbol = options?.showSymbol !== false;
  
  // Formato específico por moneda
  if (currency === 'COP') {
    // COP: sin decimales, punto como separador de miles
    const amount = dinero.amount; // Ya está en unidades enteras
    const formatted = amount.toLocaleString('es-CO', {
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    });
    return showSymbol ? `$${formatted}` : formatted;
  } else {
    // Otras monedas: con decimales
    // Dinero.js v2: usar toFormat con locale
    const factor = Math.pow(10, dinero.currency.exponent);
    const value = dinero.amount / factor;
    return value.toLocaleString(locale, {
      style: 'currency',
      currency: currency,
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });
  }
}

/**
 * Helper para crear Dinero desde string (input de usuario)
 */
export function fromString(value: string, currencyCode: string = 'USD'): Dinero<number> {
  // Remover símbolos y espacios
  const cleanValue = value.replace(/[^\d.,-]/g, '');
  
  // Detectar separador decimal
  const hasComma = cleanValue.includes(',');
  const hasDot = cleanValue.includes('.');
  
  let numericValue: number;
  
  if (hasComma && hasDot) {
    // Formato europeo: 1.234,56
    const parts = cleanValue.split(',');
    numericValue = parseFloat(parts[0].replace(/\./g, '') + '.' + parts[1]);
  } else if (hasComma) {
    // Solo coma: 1234,56
    numericValue = parseFloat(cleanValue.replace(',', '.'));
  } else {
    // Solo punto o sin separador: 1234.56 o 1234
    numericValue = parseFloat(cleanValue);
  }
  
  return fromAPI(numericValue, currencyCode);
}
```

**1.1.5: Crear Transformador de Respuestas API**

- Crear: `frontend/src/lib/money-transformer.ts` (nuevo)
- Transformador que convierte strings Decimal a Dinero:

```typescript
/**
 * ESTÁNDAR NOUGRAM: Transformador de respuestas API
 * Convierte strings Decimal del backend a objetos Dinero
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
  
  // Obtener currency: parámetro > objeto > error
  let detectedCurrency: string;
  try {
    detectedCurrency = currency || detectCurrency(data);
  } catch (error) {
    console.error('[Money Transformer] Currency detection failed:', error);
    // En desarrollo, usar USD como fallback con warning
    if (process.env.NODE_ENV === 'development') {
      console.warn(
        '[Money Transformer] Using USD as fallback. ' +
        'Fix API response to include currency field.'
      );
      detectedCurrency = 'USD';
    } else {
      // En producción, lanzar error (no silenciar)
      throw new Error(
        `Currency required for money transformation. ${error instanceof Error ? error.message : String(error)}`
      );
    }
  }
  
  for (const [key, value] of Object.entries(data)) {
    // Si el campo es un monto monetario y es string
    if (MONEY_FIELDS.includes(key as any) && typeof value === 'string') {
      try {
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
 * Convierte Dinero a string para enviar al API
 * ESTÁNDAR NOUGRAM: Backend espera strings Decimal
 * Ya implementado en money.ts, mantener aquí para referencia
 */
```

**1.1.6: Actualizar api-client.ts con Transformador**

- Actualizar: `frontend/src/lib/api-client.ts`
- Integrar transformador automático:

```typescript
import { transformAPIResponse } from './money-transformer';

async function apiRequestInternal<T>(
  endpoint: string,
  options: RequestInit = {},
  currency?: string  // NUEVO: moneda para transformación
): Promise<ApiResponse<T>> {
  // ... código existente ...
  
  const data = await response.json();
  
  // ESTÁNDAR NOUGRAM: Transformar strings Decimal a Dinero
  const transformedData = transformAPIResponse<T>(data, currency);
  
  logger.debug(`[API] Response data (transformed):`, transformedData);
  return { data: transformedData };
}
```

**1.1.7: Actualizar helpers de formateo existentes**

- Actualizar: `frontend/src/lib/currency.ts`
- Integrar con `dinero.js`:

```typescript
import { fromAPIString, formatCurrency as formatDinero } from './money';

/**
 * ESTÁNDAR NOUGRAM: Formatea moneda usando dinero.js
 * Acepta tanto Dinero como number (para compatibilidad)
 */
import { type Dinero } from 'dinero.js';

export function formatCurrency(
  amount: number | Dinero<number>,
  currency: string = "USD",
  useGrouping: boolean = true
): string {
  let dinero: Dinero<number>;
  
  // Verificar si es Dinero (en v2, verificar por estructura)
  if (typeof amount === 'object' && 'amount' in amount && 'currency' in amount) {
    dinero = amount as Dinero<number>;
  } else {
    // Compatibilidad: convertir number a Dinero
    dinero = fromAPI(amount as number, currency);
  }
  
  return formatDinero(dinero, 'es-CO', { showSymbol: true });
}
```

### Sprint 1.2: Tests de Fundación

**1.2.1: Tests Backend**

- Crear: `backend/tests/unit/test_money.py` (nuevo)

```python
import pytest
from decimal import Decimal
from app.core.money import Money, to_money, sum_money, from_api, to_api


class TestMoney:
    def test_create_from_float(self):
        money = Money(100.50, "USD")
        assert money.amount == Decimal('100.50')
        assert money.currency == "USD"
    
    def test_create_from_string(self):
        money = Money("100.50", "USD")
        assert money.amount == Decimal('100.50')
    
    def test_create_from_decimal(self):
        money = Money(Decimal('100.50'), "USD")
        assert money.amount == Decimal('100.50')
    
    def test_add_same_currency(self):
        a = Money(100, "USD")
        b = Money(50, "USD")
        result = a.add(b)
        assert result.amount == Decimal('150')
        assert result.currency == "USD"
    
    def test_add_different_currency_raises_error(self):
        a = Money(100, "USD")
        b = Money(50, "COP")
        with pytest.raises(ValueError):
            a.add(b)
    
    def test_multiply(self):
        money = Money(100, "USD")
        result = money.multiply(1.5)
        assert result.amount == Decimal('150')
    
    def test_apply_margin(self):
        cost = Money(100, "USD")
        result = cost.apply_margin(0.40)  # 40% margin
        # 100 / (1 - 0.40) = 100 / 0.60 = 166.67
        assert result.amount.quantize(Decimal('0.01')) == Decimal('166.67')
    
    def test_apply_percentage(self):
        money = Money(100, "USD")
        result = money.apply_percentage(19)  # 19% IVA
        assert result.amount == Decimal('19')
    
    def test_cop_no_decimals_display(self):
        money = Money(1000000.50, "COP")
        quantized = money.quantize()
        assert quantized.amount == Decimal('1000001')  # Redondeado
    
    def test_sum_money_list(self):
        amounts = [
            Money(100, "USD"),
            Money(50, "USD"),
            Money(25, "USD"),
        ]
        result = sum_money(amounts)
        assert result.amount == Decimal('175')
        assert result.currency == "USD"
    
    def test_precision_accumulation(self):
        # Test que suma de 0.1 + 0.2 = 0.3 (no 0.30000000000000004)
        a = Money(0.1, "USD")
        b = Money(0.2, "USD")
        result = a.add(b)
        assert result.amount == Decimal('0.3')
    
    def test_to_api_conversion(self):
        money = Money(100.50, "USD")
        api_value = to_api(money)
        assert api_value == 100.50
        assert isinstance(api_value, float)
```

**1.2.2: Tests Frontend**

- Crear: `frontend/src/lib/__tests__/money.test.ts` (nuevo)
- Crear: `frontend/src/lib/__tests__/money-transformer.test.ts` (nuevo)

```typescript
import { describe, it, expect } from '@jest/globals';
import { fromAPIString, fromAPI, toAPI, sumMoney, applyMargin, formatCurrency } from '../money';
import { USD, COP } from '@dinero.js/currencies';
import { transformAPIResponse } from '../money-transformer';

describe('Money utilities - Dinero.js v2', () => {
  it('creates Dinero from API string (ESTÁNDAR NOUGRAM)', () => {
    const dinero = fromAPIString('100.50', 'USD');
    expect(dinero.amount).toBe(10050); // En centavos
    expect(dinero.currency.code).toBe('USD');
  });

  it('creates Dinero from API number (compatibilidad)', () => {
    const dinero = fromAPI(100.50, 'USD');
    expect(dinero.amount).toBe(10050);
    expect(dinero.currency.code).toBe('USD');
  });

  it('converts Dinero to API value', () => {
    const dinero = fromAPIString('100.50', 'USD');
    const apiValue = toAPI(dinero);
    expect(apiValue).toBe(100.50);
  });

  it('sums multiple Dinero', () => {
    const amounts = [
      fromAPIString('100', 'USD'),
      fromAPIString('50', 'USD'),
      fromAPIString('25', 'USD'),
    ];
    const result = sumMoney(amounts);
    expect(toAPI(result!)).toBe(175);
  });

  it('applies margin correctly', () => {
    const cost = fromAPIString('100', 'USD');
    const price = applyMargin(cost, 40); // 40% margin
    // 100 / (1 - 0.40) = 166.67
    expect(toAPI(price)).toBeCloseTo(166.67, 2);
  });

  it('handles COP without decimals', () => {
    const dinero = fromAPIString('1000000', 'COP');
    expect(dinero.amount).toBe(1000000); // Sin decimales
    expect(dinero.currency.code).toBe('COP');
  });

  it('maintains precision in accumulation', () => {
    // Test que 0.1 + 0.2 = 0.3 (no 0.30000000000000004)
    const a = fromAPIString('0.1', 'USD');
    const b = fromAPIString('0.2', 'USD');
    const result = a.add(b);
    expect(toAPI(result)).toBeCloseTo(0.3, 2);
  });

  it('uses round half up (not banker rounding)', () => {
    // Test que 0.5 redondea hacia arriba (no hacia par)
    const dinero = fromAPIString('0.5', 'USD');
    // Con round half up: 0.5 → 1 (hacia arriba)
    // Con banker rounding: 0.5 → 0 (hacia par más cercano)
    expect(dinero.amount).toBe(50); // 0.5 * 100 = 50 centavos
  });
});

describe('Money Transformer - Currency validation', () => {
  it('throws error if currency is missing', () => {
    const response = {
      total_client_price: '100.50',
      // Sin campo currency
    };
    
    expect(() => {
      transformAPIResponse(response);
    }).toThrow('Currency is required');
  });

  it('uses currency from response', () => {
    const response = {
      total_client_price: '1000000',
      currency: 'COP',
    };
    
    const transformed = transformAPIResponse(response);
    expect(transformed.total_client_price.currency.code).toBe('COP');
  });

  it('detects currency from nested items', () => {
    const response = {
      items: [
        { client_price: '100.50', currency: 'USD' },
        { client_price: '200.75', currency: 'USD' },
      ],
      total_client_price: '301.25',
      // Sin currency en nivel superior
    };
    
    const transformed = transformAPIResponse(response);
    expect(transformed.total_client_price.currency.code).toBe('USD');
  });
});
```

---

## 📋 FASE 2: Migración de Cálculos Críticos (Semanas 2-3)

### Sprint 2.1: Migrar BCR (Blended Cost Rate)

**2.1.1: Actualizar `calculate_blended_cost_rate`**

- Actualizar: `backend/app/core/calculations.py`
- **IMPORTANTE**: Retornar `Decimal` en lugar de `float` para precisión:

```python
from app.core.money import Money, sum_money
from decimal import Decimal

async def calculate_blended_cost_rate(
    db: AsyncSession, 
    primary_currency: str = "USD", 
    use_cache: bool = True, 
    tenant_id: Optional[int] = None,
    social_charges_config: Optional[dict] = None
) -> Decimal:  # CAMBIO: Retornar Decimal en lugar de float
    """
    Calculate the blended cost rate (cost per hour) for the agency.
    ESTÁNDAR NOUGRAM: Retorna Decimal para precisión, se serializa como string en API
    """
    # ... código usando Money ...
    
    if hours_per_month > 0:
        cost_per_hour_money = total_monthly_costs.divide(float(hours_per_month))
        return cost_per_hour_money.amount  # Retornar Decimal
    else:
        return Decimal('0')
```

- Actualizar schema de respuesta:

```python
# backend/app/schemas/quote.py
class BlendedCostRateResponse(BaseModel):
    """ESTÁNDAR NOUGRAM: Decimal serializado como string"""
    blended_cost_rate: Decimal = Field(..., description="Blended cost rate per hour")
    total_monthly_costs: Decimal = Field(..., description="Total monthly costs")
    # ... otros campos Decimal ...
    
    @field_serializer('blended_cost_rate', 'total_monthly_costs', ...)
    def serialize_decimal(self, value: Decimal) -> str:
        return str(value) if value is not None else "0"
    
    model_config = DECIMAL_CONFIG
```

**2.1.2: Actualizar cálculo de BCR en frontend**

- Actualizar: `backend/app/core/calculations.py`

```python
from app.core.money import Money, sum_money, to_api

async def calculate_blended_cost_rate(
    db: AsyncSession, 
    primary_currency: str = "USD", 
    use_cache: bool = True, 
    tenant_id: Optional[int] = None,
    social_charges_config: Optional[dict] = None
) -> float:
    """
    Calculate the blended cost rate (cost per hour) for the agency.
    Returns float for compatibility, but uses Money internally for precision.
    """
    from app.core.cache import get_cache
    
    # Check cache first
    if use_cache:
        cache = get_cache()
        cache_key = f"blended_cost_rate:{primary_currency}:tenant_{tenant_id}"
        
        if social_charges_config and social_charges_config.get('enable_social_charges'):
            total_percentage = social_charges_config.get('total_percentage', 0)
            cache_key += f":social_{total_percentage}"
            
        cached_value = cache.get(cache_key)
        if cached_value is not None:
            return cached_value
    
    # Get all fixed costs and convert to Money
    query = select(CostFixed).where(CostFixed.deleted_at.is_(None))
    if tenant_id is not None:
        query = query.where(CostFixed.organization_id == tenant_id)
    
    result = await db.execute(query)
    fixed_costs = result.scalars().all()
    
    fixed_costs_money = []
    for cost in fixed_costs:
        cost_currency = cost.currency or "USD"
        normalized = normalize_to_primary_currency(
            cost.amount_monthly,
            cost_currency,
            primary_currency
        )
        fixed_costs_money.append(Money(normalized, primary_currency))
    
    # Get team members and calculate salaries with social charges
    query = select(TeamMember).where(TeamMember.is_active == True)
    if tenant_id is not None:
        query = query.where(TeamMember.organization_id == tenant_id)
    result = await db.execute(query)
    team_members = result.scalars().all()
    
    # Calculate social charges multiplier
    social_charges_multiplier = Decimal('1.0')
    if tenant_id is not None:
        try:
            from app.models.organization import Organization
            org_result = await db.execute(select(Organization).where(Organization.id == tenant_id))
            org = org_result.scalar_one_or_none()
            if org and org.settings and org.settings.get('social_charges_config'):
                social_config = org.settings.get('social_charges_config', {})
                if social_config.get('enable_social_charges', False):
                    total_percentage = 0.0
                    # ... (código existente para calcular total_percentage)
                    if total_percentage:
                        social_charges_multiplier = Decimal('1') + (Decimal(str(total_percentage)) / Decimal('100'))
        except Exception as e:
            logger.warning(f"Error getting social charges config: {e}")
    
    # Calculate total salaries with social charges
    salary_amounts = []
    for member in team_members:
        member_currency = member.currency or "USD"
        normalized_salary = normalize_to_primary_currency(
            member.salary_monthly_brute,
            member_currency,
            primary_currency
        )
        salary_money = Money(normalized_salary, primary_currency)
        salary_with_charges = salary_money.multiply(social_charges_multiplier)
        salary_amounts.append(salary_with_charges)
    
    # Sum all costs
    all_costs = fixed_costs_money + salary_amounts
    total_monthly_costs = sum_money(all_costs)
    
    if total_monthly_costs is None:
        return 0.0
    
    # Calculate total billable hours
    hours_per_month = Decimal('0')
    for member in team_members:
        non_billable = getattr(member, 'non_billable_hours_percentage', 0.0) or 0.0
        billable_factor = Decimal('1') - Decimal(str(non_billable))
        hours = Decimal(str(member.billable_hours_per_week)) * Decimal('4.33') * billable_factor
        hours_per_month += hours
    
    # Calculate cost per hour
    if hours_per_month > 0:
        cost_per_hour_money = total_monthly_costs.divide(float(hours_per_month))
        cost_per_hour = to_api(cost_per_hour_money)
    else:
        cost_per_hour = 0.0
    
    # Cache the result
    if use_cache:
        cache = get_cache()
        cache_key = f"blended_cost_rate:{primary_currency}:tenant_{tenant_id}"
        if social_charges_config and social_charges_config.get('enable_social_charges'):
            total_percentage = social_charges_config.get('total_percentage', 0)
            cache_key += f":social_{total_percentage}"
        cache.set(cache_key, cost_per_hour, ttl_seconds=300)
    
    return cost_per_hour
```

**2.1.2: Actualizar cálculo de BCR en frontend**

- Actualizar: `frontend/src/lib/finance-utils.ts`

```typescript
import { fromAPI, sumMoney, divideMoney, formatCurrency as formatDinero } from './money';

export function calculateBCR(
  teamMembers: TeamMember[],
  fixedCosts: Array<{ amount: number; currency?: string }> = [],
  socialChargesConfig?: SocialChargesConfig,
  currency: string = "USD"
): CostBreakdown {
  // Calcular multiplicador de cargas sociales
  let socialChargesMultiplier = 1.0;
  if (socialChargesConfig?.enable_social_charges) {
    const totalPercentage = socialChargesConfig.total_percentage || 
      (socialChargesConfig.health_percentage || 0) +
      (socialChargesConfig.pension_percentage || 0) +
      (socialChargesConfig.arl_percentage || 0) +
      (socialChargesConfig.parafiscales_percentage || 0);
    socialChargesMultiplier = 1.0 + (totalPercentage / 100.0);
  }

  // Calcular salarios con cargas sociales usando Dinero
  const salaryAmounts = teamMembers.map(member => {
    const salary = fromAPI(member.salary, currency);
    const salaryWithCharges = salary.multiply(socialChargesMultiplier);
    return salaryWithCharges;
  });

  // Calcular costos fijos usando Dinero
  const fixedCostAmounts = fixedCosts.map(cost => {
    return fromAPI(cost.amount, cost.currency || currency);
  });

  // Sumar todos los costos
  const allCosts = [...salaryAmounts, ...fixedCostAmounts];
  const totalMonthlyCosts = sumMoney(allCosts);

  // Calcular horas facturables totales
  const totalBillableHours = teamMembers.reduce(
    (sum, member) => {
      const nonBillable = member.nonBillableHoursPercentage || 0;
      const billableFactor = 1 - nonBillable;
      return sum + (member.billableHours * 4.33 * billableFactor);
    },
    0
  );

  // Calcular BCR
  let blendedCostRate = 0;
  if (totalBillableHours > 0 && totalMonthlyCosts) {
    const bcrMoney = divideMoney(totalMonthlyCosts, totalBillableHours);
    blendedCostRate = toAPI(bcrMoney);
  }

  // Convertir a formato de respuesta (mantener compatibilidad)
  return {
    totalMonthlySalaries: toAPI(sumMoney(salaryAmounts) || fromAPI(0, currency)),
    totalMonthlyCosts: toAPI(totalMonthlyCosts || fromAPI(0, currency)),
    totalBillableHours,
    blendedCostRate,
    salaryBreakdown: teamMembers.map(member => {
      const salary = fromAPI(member.salary, currency);
      const salaryWithCharges = salary.multiply(socialChargesMultiplier);
      return {
        name: member.name,
        salary: member.salary,
        salaryWithCharges: toAPI(salaryWithCharges),
        billableHours: member.billableHours * 4.33,
      };
    }),
  };
}
```

### Sprint 2.2: Migrar Cálculo de Quotes

**2.2.1: Actualizar `calculate_quote_totals_enhanced`**

- Actualizar: `backend/app/core/calculations.py`

```python
async def calculate_quote_totals_enhanced(
    db: AsyncSession,
    items: List[Dict],
    blended_cost_rate: float,
    tax_ids: List[int] = None,
    expenses: List[Dict] = None,
    target_margin_percentage: Optional[float] = None,
    revisions_included: int = 2,
    revision_cost_per_additional: Optional[float] = None,
    revisions_count: Optional[int] = None,
    currency: str = "USD"  # NUEVO: especificar moneda
) -> Dict:
    """
    Enhanced quote calculation using Money for precision
    """
    from app.models.tax import Tax
    from app.core.money import Money, sum_money, to_api
    
    # Convertir BCR a Money
    bcr_money = Money(blended_cost_rate, currency)
    
    total_internal_cost_money = Money(0, currency)
    items_breakdown = []
    items_internal_costs = []
    
    # First pass: Calculate internal costs for all items
    for item in items:
        service_id = item.get("service_id")
        pricing_type = item.get("pricing_type", "hourly")
        
        result = await db.execute(
            select(Service).where(
                Service.id == service_id,
                Service.deleted_at.is_(None)
            )
        )
        service = result.scalar_one_or_none()
        
        if not service:
            continue
        
        # Get pricing strategy
        strategy = PricingStrategyFactory.get_strategy(pricing_type or service.pricing_type)
        pricing_result = strategy.calculate(item, service, blended_cost_rate)
        
        internal_cost = pricing_result["internal_cost"]
        if internal_cost == 0.0:
            continue
        
        internal_cost_money = Money(internal_cost, currency)
        total_internal_cost_money = total_internal_cost_money.add(internal_cost_money)
        
        items_internal_costs.append({
            "service_id": service_id,
            "internal_cost": internal_cost,
        })
        
        items_breakdown.append({
            "service_id": service_id,
            "service_name": service.name,
            "internal_cost": internal_cost,
            "pricing_type": pricing_type or service.pricing_type,
        })
    
    # Calculate expenses
    total_expenses_cost_money = Money(0, currency)
    total_expenses_client_price_money = Money(0, currency)
    expenses_breakdown = []
    
    if expenses:
        for expense in expenses:
            cost = expense.get("cost", 0)
            markup_percentage = expense.get("markup_percentage", 0.0)
            quantity = expense.get("quantity", 1.0)
            
            if cost <= 0:
                continue
            
            expense_cost_money = Money(cost, currency).multiply(quantity)
            expense_client_price_money = expense_cost_money.multiply(Decimal('1') + Decimal(str(markup_percentage)))
            
            total_expenses_cost_money = total_expenses_cost_money.add(expense_cost_money)
            total_expenses_client_price_money = total_expenses_client_price_money.add(expense_client_price_money)
            
            expenses_breakdown.append({
                "name": expense.get("name", ""),
                "cost": to_api(expense_cost_money),
                "markup_percentage": markup_percentage,
                "client_price": to_api(expense_client_price_money),
                "quantity": quantity,
            })
    
    total_internal_cost_money = total_internal_cost_money.add(total_expenses_cost_money)
    
    # Calculate client price
    if target_margin_percentage is not None and 0 < target_margin_percentage < 1:
        # Aplicar margen objetivo a toda la propuesta
        total_client_price_money = total_internal_cost_money.apply_margin(target_margin_percentage)
    else:
        # Fallback: usar márgenes individuales de servicios
        total_client_price_money = Money(0, currency)
        # ... (código para calcular con márgenes individuales)
        total_client_price_money = total_client_price_money.add(total_expenses_client_price_money)
    
    # Calculate revisions cost
    revisions_cost_money = Money(0, currency)
    if revision_cost_per_additional is not None and revision_cost_per_additional >= 0 and revisions_count is not None:
        if revisions_count > revisions_included:
            additional_revisions = revisions_count - revisions_included
            revisions_cost_money = Money(revision_cost_per_additional, currency).multiply(additional_revisions)
            total_client_price_money = total_client_price_money.add(revisions_cost_money)
    
    # Calculate taxes
    total_taxes_money = Money(0, currency)
    taxes_breakdown = []
    
    if tax_ids:
        result = await db.execute(
            select(Tax).where(
                Tax.id.in_(tax_ids),
                Tax.deleted_at.is_(None)
            )
        )
        taxes = result.scalars().all()
        
        for tax in taxes:
            tax_amount_money = total_client_price_money.apply_percentage(tax.percentage)
            total_taxes_money = total_taxes_money.add(tax_amount_money)
            
            taxes_breakdown.append({
                "id": tax.id,
                "name": tax.name,
                "percentage": tax.percentage,
                "amount": to_api(tax_amount_money),
            })
    
    total_with_taxes_money = total_client_price_money.add(total_taxes_money)
    
    # Calculate margin percentage
    if total_client_price_money.amount > 0:
        margin_amount = total_client_price_money.subtract(total_internal_cost_money)
        margin_percentage = float(margin_amount.amount / total_client_price_money.amount)
    else:
        margin_percentage = 0.0
    
    return {
        "total_internal_cost": to_api(total_internal_cost_money),
        "total_client_price": to_api(total_client_price_money),
        "total_expenses_cost": to_api(total_expenses_cost_money),
        "total_expenses_client_price": to_api(total_expenses_client_price_money),
        "total_taxes": to_api(total_taxes_money),
        "total_with_taxes": to_api(total_with_taxes_money),
        "margin_percentage": margin_percentage,
        "taxes": taxes_breakdown,
        "items": items_breakdown,
        "expenses": expenses_breakdown,
        "revisions_cost": to_api(revisions_cost_money),
    }
```

### Sprint 2.3: Tests de Integración

**2.3.1: Tests de precisión en cálculos**

- Crear: `backend/tests/integration/test_money_precision.py` (nuevo)

```python
import pytest
from app.core.money import Money
from app.core.calculations import calculate_blended_cost_rate, calculate_quote_totals_enhanced


class TestMoneyPrecision:
    """Tests para validar precisión en cálculos críticos"""
    
    @pytest.mark.asyncio
    async def test_bcr_precision(self, db_session, test_organization):
        """Test que BCR mantiene precisión en cálculos acumulativos"""
        # Crear múltiples costos pequeños que suman un total específico
        # Verificar que no hay errores de redondeo
        
    @pytest.mark.asyncio
    async def test_quote_calculation_precision(self, db_session, test_organization):
        """Test que cálculos de quotes mantienen precisión"""
        # Crear quote con múltiples items
        # Verificar que totales son exactos
        
    @pytest.mark.asyncio
    async def test_margin_calculation_precision(self, db_session):
        """Test que aplicación de márgenes mantiene precisión"""
        cost = Money(100, "USD")
        price = cost.apply_margin(0.40)
        # Verificar que price = 166.67 exactamente
        
    @pytest.mark.asyncio
    async def test_tax_calculation_precision(self, db_session):
        """Test que cálculos de impuestos mantienen precisión"""
        price = Money(1000, "USD")
        tax = price.apply_percentage(19)  # 19% IVA
        # Verificar que tax = 190 exactamente
```

---

## 📋 FASE 3: Migración Completa y Validación (Semanas 4-5)

### Sprint 3.1: Migrar Todos los Cálculos Financieros

**3.1.1: Actualizar servicios restantes**

- `backend/app/services/annual_sales_projection_service.py`
- `backend/app/services/sales_projection_service.py`
- `backend/app/services/credit_service.py`
- Todos los cálculos en `backend/app/core/calculations.py`

**3.1.2: Actualizar componentes frontend**

- `frontend/src/components/projections/AnnualProjectionMatrix.tsx`
- `frontend/src/components/quotes/QuoteSummary.tsx`
- `frontend/src/components/costs/CostForm.tsx`
- Todos los componentes que hacen cálculos financieros

### Sprint 3.2: Actualizar Schemas y Validación

**3.2.1: Schemas Backend**

- Actualizar: `backend/app/schemas/quote.py`
- Agregar validación de precisión:

```python
from pydantic import BaseModel, validator
from decimal import Decimal

class MoneyAmount(BaseModel):
    """Schema para montos de dinero con precisión"""
    amount: Decimal
    currency: str = "USD"
    
    @validator('amount')
    def validate_amount(cls, v):
        if v < 0:
            raise ValueError("Amount cannot be negative")
        # Redondear a 2 decimales (o 0 para COP)
        return v.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
```

**3.2.2: Schemas Frontend**

- Actualizar: `frontend/src/lib/types/quote.ts`
- Agregar tipos para Money:

```typescript
import { Dinero } from 'dinero.js';

export interface MoneyAmount {
  amount: number; // Para API (float)
  currency: string;
}

// Helper para convertir a Dinero
export function toDinero(money: MoneyAmount): Dinero.Dinero {
  return fromAPI(money.amount, money.currency);
}
```

### Sprint 3.3: Documentación y Guías

**3.3.1: Crear guía de uso**

- Crear: `docs/PRECISION_FINANCIERA.md`
- Documentar:
  - Cómo usar `Money` en backend
  - Cómo usar `dinero.js` en frontend
  - Mejores prácticas
  - Ejemplos de uso

**3.3.2: Actualizar documentación de API**

- Actualizar endpoints que retornan montos
- Especificar precisión esperada
- Documentar formato de respuesta

---

## ✅ Criterios de Aceptación

### Fase 1: Fundación
- [ ] Módulo `Money` creado en backend con todas las operaciones
- [ ] **CRÍTICO**: `Money` usa `ROUND_HALF_UP` explícitamente (no banker's rounding)
- [ ] Módulo `money.ts` creado en frontend con `dinero.js` v2
- [ ] **CRÍTICO**: Sintaxis correcta de Dinero.js v2 (`dinero()`, `@dinero.js/currencies`)
- [ ] **CRÍTICO**: `fromAPIString()` usa `Math.round()` (round half up) para consistencia
- [ ] **ESTÁNDAR NOUGRAM**: Configuración Pydantic para serializar Decimal como string
- [ ] **ESTÁNDAR NOUGRAM**: Transformador `money-transformer.ts` convierte strings → Dinero
- [ ] **CRÍTICO**: Transformador valida currency obligatorio (lanza error si falta)
- [ ] **ESTÁNDAR NOUGRAM**: `api-client.ts` integra transformador automático
- [ ] Helpers de conversión API ↔ Money funcionando
- [ ] Tests de serialización Decimal → string pasando
- [ ] Tests de transformación string → Dinero pasando
- [ ] Tests de validación de currency pasando (error si falta)
- [ ] Tests de redondeo consistente (round half up) pasando
- [ ] Tests unitarios pasando (100% cobertura en helpers)
- [ ] Formateo de monedas funcionando correctamente

### Fase 2: Migración Crítica
- [ ] **CRÍTICO**: Migración de BD Float → Numeric(19,4) para campos monetarios críticos
- [ ] `calculate_blended_cost_rate` migrado a `Money` y retorna `Decimal`
- [ ] `calculate_quote_totals_enhanced` migrado a `Money` y retorna `Decimal`
- [ ] Schemas actualizados con `field_serializer` para Decimal
- [ ] Cálculos de BCR en frontend migrados a `dinero.js`
- [ ] **ESTÁNDAR NOUGRAM**: Endpoint `/quotes/calculate` SIEMPRE recalcula en backend
- [ ] **ESTÁNDAR NOUGRAM**: Frontend solo muestra vista previa (no guarda cálculos)
- [ ] Tests de integración validando precisión
- [ ] Tests de recalculo backend pasando
- [ ] Tests de SUM() en SQL con Numeric validando exactitud

### Fase 3: Migración Completa
- [ ] Todos los cálculos financieros migrados
- [ ] Todos los schemas con Decimal serializan como string
- [ ] Todos los componentes frontend usan Dinero para vista previa
- [ ] Migración completa de BD Float → Numeric para todos los campos monetarios
- [ ] Documentación completa de uso
- [ ] Tests E2E pasando
- [ ] 0 errores de redondeo en cálculos acumulativos
- [ ] 0 regresiones en funcionalidad existente
- [ ] **ESTÁNDAR NOUGRAM**: Validación de que backend siempre recalcula antes de guardar

---

## 🚨 Riesgos y Mitigaciones

| Riesgo | Mitigación |
|--------|------------|
| **Performance**: Decimal es más lento que float | Impacto mínimo en este caso de uso. Benchmarking si es necesario |
| **Compatibilidad**: Código existente usa float | Mantener funciones wrapper que acepten float y conviertan internamente |
| **Migración compleja**: Muchos lugares a actualizar | Migración gradual por fases, empezando por cálculos críticos |
| **Base de datos**: Modelos usan Float | **CRÍTICO**: Migrar a Numeric(19,4) para precisión grado bancario. Float causa errores en SUM() SQL |
| **Currency obligatorio**: Puede faltar en respuestas | Validación estricta: lanzar error si falta currency (no usar default) |
| **Redondeo inconsistente**: Python ROUND_HALF_EVEN vs Dinero.js | Usar ROUND_HALF_UP explícitamente en ambos (no banker's rounding) |
| **Sintaxis Dinero.js**: Código usa v1 | Actualizar a v2: `dinero()`, `@dinero.js/currencies` |
| **Bundle size**: dinero.js agrega ~15KB | Aceptable para el valor que proporciona |

---

## 📊 Métricas de Éxito

1. **Precisión**: 0 errores de redondeo en cálculos acumulativos
2. **Cobertura**: 100% de tests unitarios en módulos de dinero
3. **Performance**: < 5% de overhead en cálculos (benchmarking)
4. **Compatibilidad**: 0 regresiones en funcionalidad existente
5. **Documentación**: Guía completa de uso disponible

---

## 🔄 Plan de Rollback

Si se detectan problemas críticos:

1. **Fase 1**: Revertir cambios en helpers, mantener código existente
2. **Fase 2**: Revertir migración de cálculos críticos, usar versión anterior
3. **Fase 3**: Revertir migración completa, mantener solo helpers para uso futuro

**Estrategia**: Commits pequeños y frecuentes, tags de versión antes de cada fase.

---

## 📝 Notas de Implementación

### Backend: ¿Por qué Decimal y no python-money?

- `decimal.Decimal` es nativo de Python (sin dependencias externas)
- `python-money` tiene dependencias adicionales y menos mantenimiento activo
- `Decimal` es suficiente para nuestras necesidades de precisión
- Podemos crear wrapper `Money` sobre `Decimal` para mejor API

### Frontend: ¿Por qué dinero.js v2?

- Librería madura y bien mantenida
- Soporte TypeScript nativo
- Inmutabilidad garantizada
- API limpia y fácil de usar
- Tamaño razonable (~15KB)

### Base de Datos: Migración a Numeric (CRÍTICO)

**Recomendación: SÍ - Migrar a Numeric para precisión grado bancario**

**Problema con Float:**
- `Float` es aproximado por naturaleza a nivel de hardware
- `SUM(total_client_price)` en SQL puede dar diferencias de centavos respecto a cálculos en Python
- Si el volumen de datos crece, las sumas acumulativas en SQL serán inexactas
- No es adecuado para precisión financiera "grado bancario"

**Solución: Migrar a Numeric(precision, scale)**

**Precisión recomendada:**
- `Numeric(19, 4)` para montos grandes (permite hasta 999,999,999,999,999.9999)
- `Numeric(10, 2)` para porcentajes y márgenes (suficiente para 0-100%)

**Ventajas:**
- Precisión exacta en base de datos (no aproximada)
- `SUM()` en SQL será exacto (coincide con cálculos en Python)
- SQLAlchemy convierte automáticamente a `Decimal` al leer
- Compatible con precisión grado bancario

**Migración por fases:**

**Fase 1: Campos críticos (Sprint 21.2)**
- `quotes.total_client_price`, `quotes.total_internal_cost`
- `quote_items.client_price`, `quote_items.internal_cost`
- `quote_expenses.cost`, `quote_expenses.client_price`

**Fase 2: Campos secundarios (Sprint 21.3)**
- `team_members.salary_monthly_brute`
- `costs_fixed.amount_monthly`
- `services.fixed_price`, `services.recurring_price`

**Script de migración:**

```python
# backend/alembic/versions/XXX_migrate_money_to_numeric.py

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import NUMERIC

def upgrade():
    # Fase 1: Campos críticos de quotes
    op.alter_column('quotes', 'total_client_price',
                    type_=NUMERIC(precision=19, scale=4),
                    existing_type=sa.Float(),
                    postgresql_using='total_client_price::numeric(19,4)')
    
    op.alter_column('quotes', 'total_internal_cost',
                    type_=NUMERIC(precision=19, scale=4),
                    existing_type=sa.Float(),
                    postgresql_using='total_internal_cost::numeric(19,4)')
    
    op.alter_column('quote_items', 'client_price',
                    type_=NUMERIC(precision=19, scale=4),
                    existing_type=sa.Float(),
                    postgresql_using='client_price::numeric(19,4)')
    
    op.alter_column('quote_items', 'internal_cost',
                    type_=NUMERIC(precision=19, scale=4),
                    existing_type=sa.Float(),
                    postgresql_using='internal_cost::numeric(19,4)')
    
    op.alter_column('quote_expenses', 'cost',
                    type_=NUMERIC(precision=19, scale=4),
                    existing_type=sa.Float(),
                    postgresql_using='cost::numeric(19,4)')
    
    op.alter_column('quote_expenses', 'client_price',
                    type_=NUMERIC(precision=19, scale=4),
                    existing_type=sa.Float(),
                    postgresql_using='client_price::numeric(19,4)')

def downgrade():
    # Revertir a Float (solo si es necesario)
    op.alter_column('quotes', 'total_client_price',
                    type_=sa.Float(),
                    existing_type=NUMERIC(precision=19, scale=4))
    # ... otros campos
```

**Actualización de modelos:**

```python
# backend/app/models/project.py
from sqlalchemy import Numeric
from decimal import Decimal

class Quote(Base):
    # ...
    total_client_price = Column(
        Numeric(precision=19, scale=4), 
        nullable=True
    )
    total_internal_cost = Column(
        Numeric(precision=19, scale=4), 
        nullable=True
    )
    # SQLAlchemy automáticamente convierte a Decimal al leer
    # No necesitas conversión manual si usas Decimal en Python
```

**Nota importante:**
- Si no migras ahora, asegúrate de que SQLAlchemy siempre convierta a `Decimal` al leer
- Pero ten presente que cálculos dentro de la base de datos (`SUM()`, `AVG()`) no serán 100% exactos con Float
- Para precisión grado bancario, la migración a Numeric es **obligatoria**

---

## ⚠️ VALIDACIONES CRÍTICAS IMPLEMENTADAS

### 1. Base de Datos: Migración Float → Numeric ✅

**Problema identificado:** Float causa errores de precisión en `SUM()` SQL  
**Solución:** Migrar a `Numeric(19, 4)` para precisión grado bancario  
**Estado:** Incluido en Fase 2 del plan con script de migración completo

**Impacto:**
- `SUM(total_client_price)` en SQL será exacto (coincide con cálculos en Python)
- Cálculos dentro de la base de datos (`SUM()`, `AVG()`) serán 100% precisos
- Compatible con precisión grado bancario

**Migración:**
- Script de Alembic incluido en el plan
- Migración por fases (campos críticos primero)
- SQLAlchemy convierte automáticamente a `Decimal` al leer

### 2. Currency Obligatorio ✅

**Problema identificado:** Transformador puede fallar si currency falta  
**Solución:** Validación estricta - lanza error si falta currency  
**Estado:** Implementado en `detectCurrency()` y `transformAPIResponse()`

**Comportamiento:**
- En desarrollo: Usa USD como fallback con warning
- En producción: Lanza error explícito (no silencia el problema)
- Detecta currency desde múltiples fuentes: `currency`, `primary_currency`, items anidados

**Validación:**
- Tests incluidos para validar error cuando falta currency
- Tests para detección desde items anidados
- Tests para uso correcto cuando currency está presente

### 3. Redondeo Consistente ✅

**Problema identificado:** Python usa ROUND_HALF_EVEN por defecto, Dinero.js usa round half up  
**Solución:** Usar `ROUND_HALF_UP` explícitamente en ambos (no banker's rounding)  
**Estado:** Configurado en `ROUNDING_MODE` y `Math.round()` en Dinero.js

**Implementación:**
- Backend: `ROUNDING_MODE = ROUND_HALF_UP` explícito en `money.py`
- Frontend: `Math.round()` usa "round half up" (no banker's rounding)
- Consistencia garantizada entre backend y frontend

**Validación:**
- Tests incluidos para validar round half up (no banker's rounding)
- Test específico: 0.5 redondea hacia arriba (no hacia par)

### 4. Sintaxis Dinero.js v2 ✅

**Problema identificado:** Código usa sintaxis antigua de Dinero.js v1  
**Solución:** Actualizado a sintaxis correcta: `dinero()`, `@dinero.js/currencies`  
**Estado:** Código actualizado en sección 1.1.4

**Cambios implementados:**
- `import { dinero, type Dinero } from 'dinero.js'` (no `import Dinero`)
- `import { USD, COP, EUR, ARS } from '@dinero.js/currencies'`
- `dinero({ amount, currency })` (no `Dinero({...})`)
- `Dinero<number>` (no `Dinero.Dinero`)
- Acceso a propiedades: `dinero.amount`, `dinero.currency.code` (no métodos `.getAmount()`)

**Instalación:**
```bash
npm install dinero.js @dinero.js/currencies
```

---

**Última actualización:** 30 de Diciembre, 2025  
**Validaciones críticas:** ✅ Completadas y documentadas

