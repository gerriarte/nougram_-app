# 📡 Formato de Respuestas API - Campos Monetarios Decimal

**Versión:** 1.0  
**Fecha:** 2025-12-30  
**Estado:** ✅ Implementado

---

## 📋 Resumen

Todos los campos monetarios y de porcentaje en las respuestas de la API se serializan como **strings** en lugar de números para mantener precisión grado bancario. El frontend transforma automáticamente estos strings a objetos `dinero.js` para cálculos precisos.

---

## 🔢 Formato de Campos Monetarios

### Campos que Retornan Strings Decimal

Los siguientes tipos de campos se serializan como strings:

- **Montos monetarios**: `total_client_price`, `total_internal_cost`, `client_price`, `internal_cost`, `cost`, `price`, `amount`, `salary`, `blended_cost_rate`, etc.
- **Porcentajes**: `margin_percentage`, `target_margin_percentage`, `markup_percentage`, `percentage`, `rate`, etc.

### Ejemplo de Respuesta

**Endpoint:** `POST /api/v1/quotes/calculate`

**Request:**
```json
{
  "items": [
    {
      "service_id": 1,
      "estimated_hours": 40.0
    }
  ],
  "blended_cost_rate": 50.0,
  "currency": "USD"
}
```

**Response:**
```json
{
  "total_internal_cost": "2000.0000",
  "total_client_price": "3333.3333",
  "total_taxes": "0.0000",
  "total_with_taxes": "3333.3333",
  "margin_percentage": "0.4000",
  "target_margin_percentage": null,
  "taxes": [],
  "items": [
    {
      "service_id": 1,
      "estimated_hours": 40.0,
      "internal_cost": "2000.0000",
      "client_price": "3333.3333",
      "margin_percentage": "0.4000"
    }
  ]
}
```

**Nota:** Los valores monetarios aparecen como strings (ej: `"2000.0000"`) en lugar de números (`2000.0`).

---

## 🎯 Precisión Esperada

### Campos Monetarios

- **Precisión en BD**: `Numeric(19, 4)` - 19 dígitos totales, 4 decimales
- **Formato en API**: String con hasta 4 decimales (ej: `"1234.5678"`)
- **Ejemplos**:
  - `"1000.0000"` - Mil unidades exactas
  - `"1234.5678"` - Con 4 decimales
  - `"0.0001"` - Valor mínimo representable

### Campos de Porcentaje

- **Precisión en BD**: `Numeric(10, 4)` - 10 dígitos totales, 4 decimales
- **Formato en API**: String con hasta 4 decimales (ej: `"0.4000"` = 40%)
- **Ejemplos**:
  - `"0.4000"` - 40% de margen
  - `"0.1234"` - 12.34% de margen
  - `"1.0000"` - 100% de margen

---

## 🔄 Transformación Automática en Frontend

El frontend transforma automáticamente estos strings a objetos `dinero.js` usando el transformador integrado en `api-client.ts`.

### Ejemplo de Uso en Frontend

```typescript
import { apiRequest } from '@/lib/api-client';

// El transformador convierte automáticamente strings → Dinero
const response = await apiRequest<QuoteCalculateResponse>({
  method: 'POST',
  url: '/quotes/calculate',
  data: requestData,
  currency: 'USD' // Requerido para transformación
});

// response.total_client_price es ahora un Dinero<number>
const total = response.total_client_price; // Dinero object
const formatted = formatCurrency(total); // "$3,333.33"
```

---

## 📝 Endpoints que Usan Formato Decimal String

### 1. Cálculo de Propuestas

**Endpoint:** `POST /api/v1/quotes/calculate`

**Campos Decimal:**
- `total_internal_cost`: String Decimal
- `total_client_price`: String Decimal
- `total_taxes`: String Decimal
- `total_with_taxes`: String Decimal
- `margin_percentage`: String Decimal
- `items[].internal_cost`: String Decimal
- `items[].client_price`: String Decimal
- `items[].margin_percentage`: String Decimal

**Ejemplo Response:**
```json
{
  "total_internal_cost": "2000.0000",
  "total_client_price": "3333.3333",
  "margin_percentage": "0.4000",
  "items": [
    {
      "internal_cost": "2000.0000",
      "client_price": "3333.3333",
      "margin_percentage": "0.4000"
    }
  ]
}
```

### 2. Blended Cost Rate (BCR)

**Endpoint:** `GET /api/v1/settings/calculations/agency-cost-hour`

**Campos Decimal:**
- `blended_cost_rate`: String Decimal

**Ejemplo Response:**
```json
{
  "blended_cost_rate": "50.0000",
  "currency": "USD",
  "calculation_date": "2025-12-30T10:00:00Z"
}
```

### 3. Propuestas (Quotes)

**Endpoint:** `GET /api/v1/projects/{project_id}/quotes/{quote_id}`

**Campos Decimal:**
- `total_internal_cost`: String Decimal
- `total_client_price`: String Decimal
- `margin_percentage`: String Decimal
- `target_margin_percentage`: String Decimal (nullable)
- `items[].internal_cost`: String Decimal
- `items[].client_price`: String Decimal
- `items[].margin_percentage`: String Decimal
- `expenses[].cost`: String Decimal
- `expenses[].client_price`: String Decimal
- `expenses[].markup_percentage`: String Decimal

### 4. Análisis de Rentabilidad

**Endpoint:** `GET /api/v1/quotes/{quote_id}/rentability`

**Campos Decimal:**
- `total_client_price`: String Decimal
- `total_internal_cost`: String Decimal
- `total_taxes`: String Decimal
- `net_profit_amount`: String Decimal
- `net_profit_margin`: Number (porcentaje calculado)
- `categories[].amount`: String Decimal
- `categories[].percentage`: Number (porcentaje calculado)

---

## ⚠️ Validaciones y Errores

### Currency Obligatorio

**Problema:** Si un endpoint retorna campos monetarios pero no incluye `currency` o `primary_currency`, el transformador puede fallar.

**Solución:** 
- El transformador busca `currency` en múltiples lugares: `currency`, `primary_currency`, `project.currency`
- Si no encuentra currency, lanza error en producción
- En desarrollo, usa USD como fallback con warning

**Ejemplo de Error:**
```json
{
  "error": "Currency is required for money transformation but was not found in response"
}
```

### Formato Inválido

**Problema:** Si un campo Decimal string no puede ser parseado.

**Solución:**
- El transformador valida que el string sea un número válido
- Si falla, lanza error descriptivo

**Ejemplo de Error:**
```json
{
  "error": "Invalid money string: 'invalid'"
}
```

---

## 🔍 Detección de Campos Monetarios

El transformador detecta automáticamente campos monetarios por nombre. Los siguientes nombres de campo se transforman automáticamente:

- `*_cost`, `*_price`, `*_amount`, `*_salary`, `*_rate`
- `total_*`, `cost`, `price`, `amount`, `salary`, `blended_cost_rate`
- `margin_percentage`, `target_margin_percentage`, `markup_percentage`

**Ejemplo:**
```json
{
  "total_client_price": "1000.0000",  // ✅ Transformado
  "internal_cost": "500.0000",         // ✅ Transformado
  "margin_percentage": "0.4000",       // ✅ Transformado
  "name": "Project Name",              // ❌ No transformado (no es campo monetario)
  "status": "active"                   // ❌ No transformado
}
```

---

## 📚 Referencias

- [Guía de Precisión Financiera](./PRECISION_FINANCIERA.md) - Documentación completa del estándar
- [Plan de Precisión Financiera](./PLAN_PRECISION_FINANCIERA.md) - Plan de implementación
- [Backend Money Class](../backend/app/core/money.py) - Implementación de Money
- [Frontend Money Utils](../frontend/src/lib/money.ts) - Implementación de dinero.js

---

## ✅ Checklist para Nuevos Endpoints

Al crear nuevos endpoints que retornen campos monetarios:

- [ ] Usar `Decimal` en schemas Pydantic (no `float`)
- [ ] Agregar `field_serializer` para serializar Decimal como string
- [ ] Incluir `currency` o `primary_currency` en la respuesta
- [ ] Documentar formato Decimal string en la documentación del endpoint
- [ ] Probar que el transformador funciona correctamente
- [ ] Validar precisión en tests de integración

---

**Última actualización:** 2025-12-30  
**Mantenedor:** Equipo de Desarrollo Nougram
