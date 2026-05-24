# 💰 Guía de Precisión Financiera - Estándar Nougram

**Versión:** 1.0  
**Fecha:** 2025-12-30  
**Estado:** ✅ Implementado

---

## 📋 Tabla de Contenidos

1. [Introducción](#introducción)
2. [Estándar de Sincronización Financiera](#estándar-de-sincronización-financiera)
3. [Backend: Uso de `Money` y `Decimal`](#backend-uso-de-money-y-decimal)
4. [Frontend: Uso de `dinero.js`](#frontend-uso-de-dinerojs)
5. [Mejores Prácticas](#mejores-prácticas)
6. [Ejemplos de Uso](#ejemplos-de-uso)
7. [Troubleshooting](#troubleshooting)
8. [Referencias](#referencias)

---

## Introducción

Este documento describe el estándar de precisión financiera implementado en Nougram para garantizar cálculos exactos en todas las operaciones monetarias. El sistema utiliza `decimal.Decimal` en Python (backend) y `dinero.js` v2 en TypeScript (frontend) para manejar dinero como estructuras inmutables.

### Problema que Resuelve

- ❌ **Antes**: Uso de `float` en Python y `number` en JavaScript causaba errores de precisión
- ❌ **Antes**: Redondeos manuales inconsistentes (`round(total, 2)`) en múltiples lugares
- ❌ **Antes**: Riesgo de discrepancias en cálculos acumulativos (sumas de múltiples items)
- ❌ **Antes**: COP configurado sin decimales pero cálculos internos usaban floats
- ❌ **Antes**: Pérdida de precisión en serialización JSON (float → JSON → float)

### Solución Implementada

- ✅ **Ahora**: Backend usa `decimal.Decimal` para cálculos precisos, serializado como **string** en JSON
- ✅ **Ahora**: Frontend usa `dinero.js` v2 para cálculos inmutables, transformador de strings API → Dinero
- ✅ **Ahora**: Representación en unidades menores (centavos/subunidades)
- ✅ **Ahora**: Formateo consistente con localización `es-CO`
- ✅ **Ahora**: **Validación crítica**: Backend SIEMPRE recalcula antes de guardar (frontend solo para vista previa)

---

## Estándar de Sincronización Financiera

### Reglas Estrictas de Implementación

#### 1. Backend (Python/FastAPI)

- ✅ Todos los campos `Decimal` se serializan como **'strings'** en respuestas JSON usando `field_serializer`
- ✅ Usar `from decimal import Decimal, ROUND_HALF_UP` (no `ROUND_HALF_EVEN`)
- ✅ Evitar pérdida de precisión en el navegador

#### 2. Frontend (React/TypeScript)

- ✅ Utilizar `dinero.js` (v2) exclusivamente para cálculos monetarios
- ✅ Transformador automático convierte strings del API a objetos `dinero`
- ✅ Realizar toda la lógica de "vista previa" del margen usando solo funciones de `dinero.js`

#### 3. Regla de Validación CRÍTICA

- ✅ El precio final de la propuesta **SIEMPRE** se recalcula en el Backend antes de guardar
- ✅ El Frontend es **SOLO** para visualización interactiva del usuario
- ✅ Nunca confiar en cálculos del frontend para persistencia

---

## Backend: Uso de `Money` y `Decimal`

### Clase `Money`

La clase `Money` en `backend/app/core/money.py` encapsula `Decimal` para operaciones monetarias precisas.

#### Creación

```python
from app.core.money import Money
from decimal import Decimal

# Crear desde diferentes tipos
money1 = Money(100.50, "USD")  # Desde float
money2 = Money("100.50", "USD")  # Desde string
money3 = Money(Decimal('100.50'), "USD")  # Desde Decimal
```

#### Operaciones Aritméticas

```python
# Suma
total = money1.add(money2)  # Retorna nuevo Money

# Resta
difference = money1.subtract(money2)

# Multiplicación
doubled = money1.multiply(2.0)

# División
half = money1.divide(2.0)
```

#### Aplicación de Porcentajes y Márgenes

```python
# Aplicar porcentaje (ej: 19% de IVA)
tax = money1.apply_percentage(19)  # Retorna nuevo Money

# Aplicar margen (ej: 40% de margen)
# Fórmula: cost / (1 - margin)
price = cost.apply_margin(40.0)  # 40% de margen
```

#### Redondeo

```python
# Redondear a precisión de display
display_money = money1.quantize()  # Usa precisión según moneda

# COP: sin decimales
cop_money = Money(1000000.50, "COP")
display_cop = cop_money.quantize()  # 1000001 (redondeado a unidad entera)

# USD: 2 decimales
usd_money = Money(100.567, "USD")
display_usd = usd_money.quantize()  # 100.57
```

#### Conversión para API

```python
# Convertir a float (solo para compatibilidad)
api_value = money1.to_float()

# Convertir a centavos/subunidades
cents = money1.to_int_cents()  # USD: 10050, COP: 1000000
```

### Uso en Schemas Pydantic

```python
from decimal import Decimal
from pydantic import BaseModel, Field, field_serializer
from app.core.pydantic_config import DECIMAL_CONFIG

class QuoteResponse(BaseModel):
    total_client_price: Decimal = Field(..., description="Total client price")
    
    # ESTÁNDAR NOUGRAM: Serializar Decimal como string
    @field_serializer('total_client_price')
    def serialize_decimal(self, value: Decimal) -> str:
        """Serializa Decimal como string para mantener precisión"""
        return str(value) if value is not None else None
    
    model_config = DECIMAL_CONFIG
```

### Uso en Cálculos

```python
from app.core.money import Money, sum_money

# Calcular totales usando Money
items = [
    Money(100, "USD"),
    Money(50, "USD"),
    Money(25, "USD"),
]

total = sum_money(items)  # Money(175, "USD")

# Aplicar margen objetivo
target_margin = 0.35  # 35%
price_with_margin = total.apply_margin(target_margin * 100)
```

---

## Frontend: Uso de `dinero.js`

### Instalación

```bash
npm install dinero.js @dinero.js/currencies
```

### Creación desde API

```typescript
import { fromAPIString, fromAPI } from '@/lib/money';

// ESTÁNDAR NOUGRAM: Backend envía strings Decimal
const dinero = fromAPIString('100.50', 'USD');  // Preferido

// Compatibilidad hacia atrás (si backend aún envía números)
const dinero2 = fromAPI(100.50, 'USD');  // @deprecated
```

### Operaciones Aritméticas

```typescript
import { sumMoney, multiplyMoney, divideMoney } from '@/lib/money';

// Suma
const total = sumMoney([dinero1, dinero2, dinero3]);

// Multiplicación
const doubled = multiplyMoney(dinero1, 2);

// División
const half = divideMoney(dinero1, 2);
```

### Aplicación de Márgenes

```typescript
import { applyMargin } from '@/lib/money';

// Aplicar margen (ej: 40% de margen)
const price = applyMargin(cost, 40);  // 40% de margen
```

### Formateo

```typescript
import { formatCurrency } from '@/lib/money';

// Formatear con localización es-CO
const formatted = formatCurrency(dinero, 'es-CO');
// USD: "$1,000.50"
// COP: "$1.000.000" (sin decimales)
```

### Conversión para API

```typescript
import { toAPIString, toAPI } from '@/lib/money';

// ESTÁNDAR NOUGRAM: Backend espera strings Decimal
const apiString = toAPIString(dinero);  // "100.50"

// Compatibilidad hacia atrás
const apiNumber = toAPI(dinero);  // 100.50 (number)
```

### Transformación Automática de Respuestas API

El `api-client.ts` transforma automáticamente strings Decimal a objetos Dinero:

```typescript
// El transformador detecta campos monetarios automáticamente
const response = await apiRequest<QuoteResponse>('/quotes/1');
// response.data.total_client_price es Dinero<number>, no string
```

---

## Mejores Prácticas

### ✅ DO (Hacer)

1. **Siempre usar `Money` en backend para cálculos monetarios**
   ```python
   # ✅ Correcto
   total = Money(100, "USD").add(Money(50, "USD"))
   
   # ❌ Incorrecto
   total = 100.0 + 50.0
   ```

2. **Siempre usar `dinero.js` en frontend para cálculos monetarios**
   ```typescript
   // ✅ Correcto
   const total = sumMoney([dinero1, dinero2]);
   
   // ❌ Incorrecto
   const total = dinero1.amount + dinero2.amount;
   ```

3. **Especificar moneda explícitamente**
   ```python
   # ✅ Correcto
   money = Money(100, "USD")
   
   # ❌ Incorrecto (usa default USD, puede causar errores)
   money = Money(100)  # No recomendado
   ```

4. **Usar `field_serializer` en schemas Pydantic**
   ```python
   # ✅ Correcto
   @field_serializer('amount')
   def serialize_decimal(self, value: Decimal) -> str:
       return str(value) if value is not None else None
   ```

5. **Validar currency obligatorio en transformador**
   ```typescript
   // ✅ Correcto: El transformador valida currency
   const transformed = transformAPIResponse(data, currency);
   ```

### ❌ DON'T (No Hacer)

1. **No usar `float` para cálculos monetarios**
   ```python
   # ❌ Incorrecto
   total = 100.50 + 50.25  # Puede causar errores de precisión
   
   # ✅ Correcto
   total = Money(100.50, "USD").add(Money(50.25, "USD"))
   ```

2. **No usar `number` directamente en frontend**
   ```typescript
   // ❌ Incorrecto
   const total = amount1 + amount2;
   
   // ✅ Correcto
   const total = sumMoney([dinero1, dinero2]);
   ```

3. **No confiar en cálculos del frontend para persistencia**
   ```typescript
   // ❌ Incorrecto: Guardar cálculo del frontend
   await saveQuote({ total: calculatedTotal });
   
   // ✅ Correcto: Backend recalcula siempre
   await saveQuote({ items: quoteItems });  // Backend calcula total
   ```

4. **No usar `ROUND_HALF_EVEN` (banker's rounding)**
   ```python
   # ❌ Incorrecto
   from decimal import ROUND_HALF_EVEN
   
   # ✅ Correcto
   from decimal import ROUND_HALF_UP  # Consistente con Dinero.js
   ```

---

## Ejemplos de Uso

### Ejemplo 1: Calcular Precio con Margen

**Backend:**
```python
from app.core.money import Money

cost = Money(100, "USD")
margin_percentage = 40.0  # 40%
price = cost.apply_margin(margin_percentage)
# Resultado: Money(166.67, "USD")  # 100 / (1 - 0.40) = 166.67
```

**Frontend:**
```typescript
import { fromAPIString, applyMargin } from '@/lib/money';

const cost = fromAPIString('100', 'USD');
const price = applyMargin(cost, 40);  // 40% de margen
// Resultado: Dinero con amount = 16667 (centavos)
```

### Ejemplo 2: Sumar Múltiples Items

**Backend:**
```python
from app.core.money import Money, sum_money

items = [
    Money(100.50, "USD"),
    Money(200.75, "USD"),
    Money(50.25, "USD"),
]

total = sum_money(items)
# Resultado: Money(351.50, "USD")
```

**Frontend:**
```typescript
import { fromAPIString, sumMoney } from '@/lib/money';

const items = [
    fromAPIString('100.50', 'USD'),
    fromAPIString('200.75', 'USD'),
    fromAPIString('50.25', 'USD'),
];

const total = sumMoney(items);
// Resultado: Dinero con amount = 35150 (centavos)
```

### Ejemplo 3: Calcular IVA

**Backend:**
```python
from app.core.money import Money

price = Money(1000, "USD")
iva_percentage = 19.0  # 19% IVA
iva_amount = price.apply_percentage(iva_percentage)
total_with_iva = price.add(iva_amount)
# Resultado: Money(1190, "USD")
```

**Frontend:**
```typescript
import { fromAPIString, applyPercentage, sumMoney } from '@/lib/money';

const price = fromAPIString('1000', 'USD');
const iva = applyPercentage(price, 19);  // 19% IVA
const total = sumMoney([price, iva]);
// Resultado: Dinero con amount = 119000 (centavos)
```

### Ejemplo 4: Formatear para Display

**Backend:**
```python
from app.core.currency import format_currency
from app.core.money import Money

money = Money(1000000.50, "COP")
formatted = format_currency(money, "COP")
# Resultado: "$ 1.000.001" (sin decimales, punto como separador de miles)
```

**Frontend:**
```typescript
import { fromAPIString, formatCurrency } from '@/lib/money';

const dinero = fromAPIString('1000000', 'COP');
const formatted = formatCurrency(dinero, 'es-CO');
// Resultado: "$1.000.000" (sin decimales)
```

---

## Troubleshooting

### Problema: Currency no encontrado en respuesta API

**Síntoma:**
```
Error: Currency is required but not found in API response
```

**Solución:**
1. Verificar que el endpoint incluye campo `currency` en la respuesta
2. Si no está disponible, pasar `currency` explícitamente al transformador:
   ```typescript
   const transformed = transformAPIResponse(data, 'USD');
   ```

### Problema: Precisión perdida en cálculos acumulativos

**Síntoma:**
```
0.1 + 0.2 = 0.30000000000000004
```

**Solución:**
- ✅ Usar `Money` en backend y `dinero.js` en frontend
- ❌ No usar `float` o `number` directamente

### Problema: Redondeo inconsistente

**Síntoma:**
```
Backend: 166.67
Frontend: 166.66
```

**Solución:**
- Verificar que ambos usan `ROUND_HALF_UP` (no `ROUND_HALF_EVEN`)
- Backend: `from decimal import ROUND_HALF_UP`
- Frontend: `Math.round()` usa "round half up" por defecto

### Problema: COP muestra decimales

**Síntoma:**
```
COP: $1.000.000,50  (debería ser $1.000.001)
```

**Solución:**
- Usar `quantize()` en backend antes de formatear
- Usar `formatCurrency()` de `money.ts` en frontend (maneja COP correctamente)

### Problema: Schema no serializa Decimal como string

**Síntoma:**
```
API response: {"amount": 100.5}  (debería ser {"amount": "100.50"})
```

**Solución:**
- Agregar `@field_serializer` al schema Pydantic
- Incluir `model_config = DECIMAL_CONFIG`

---

## Referencias

### Documentación Externa

- [Python Decimal](https://docs.python.org/3/library/decimal.html)
- [Dinero.js v2](https://v2.dinerojs.com/)
- [Pydantic Field Serializers](https://docs.pydantic.dev/latest/concepts/serialization/#field-serializers)

### Archivos Clave del Proyecto

**Backend:**
- `backend/app/core/money.py` - Clase Money y helpers
- `backend/app/core/currency.py` - Utilidades de moneda
- `backend/app/core/pydantic_config.py` - Configuración Pydantic
- `backend/app/schemas/quote.py` - Ejemplo de schema con Decimal

**Frontend:**
- `frontend/src/lib/money.ts` - Utilidades Dinero.js
- `frontend/src/lib/money-transformer.ts` - Transformador API → Dinero
- `frontend/src/lib/api-client.ts` - Cliente API con transformación automática
- `frontend/src/lib/types/money.ts` - Tipos TypeScript

### Plan de Implementación

- `docs/PLAN_PRECISION_FINANCIERA.md` - Plan completo de implementación
- `docs/TAREAS_PENDIENTES_PRECISION.md` - Estado de tareas

---

## Changelog

### v1.0 (2025-12-30)
- ✅ Implementación completa de `Money` en backend
- ✅ Implementación completa de `dinero.js` v2 en frontend
- ✅ Migración de cálculos críticos (BCR, Quotes)
- ✅ Migración de schemas a Decimal
- ✅ Tests de integración y precisión
- ✅ Documentación completa

---

**Última actualización:** 2025-12-30  
**Mantenido por:** Equipo de Desarrollo Nougram
