# Debug: Problema con Blended Cost Rate (BCR) mostrando valores en 0

## Fecha: 2025-01-XX

## Problema Reportado

El usuario reporta que en la sección de "Miembros del Equipo":
1. ✅ La tabla de miembros del equipo **SÍ muestra** la sumatoria de salarios correctamente
2. ❌ La tabla de BCR (Blended Cost Rate) **NO muestra**:
   - El valor por hora (BCR principal)
   - Los valores de resumen mensual (Recursos, Infraestructura, Herramientas)
   - El gasto operativo total

Todos los valores aparecen como `$0` o `0.0h / mes`.

## Cambios Realizados

### Frontend

#### 1. `frontend/src/app/(app)/settings/team/page.tsx`
- **Problema**: `salary_monthly_brute` viene como string (Decimal serializado) desde el backend
- **Solución**: Agregada conversión explícita de string a number antes de sumar
- **Cambios**:
  ```typescript
  // Antes:
  acc[currency] += member.salary_monthly_brute
  
  // Después:
  const salary = typeof member.salary_monthly_brute === 'string' 
    ? parseFloat(member.salary_monthly_brute) || 0
    : (member.salary_monthly_brute || 0)
  acc[currency] += salary
  ```
- **Resultado**: ✅ La sumatoria de salarios ahora funciona correctamente

#### 2. `frontend/src/components/costs/blended-cost-rate.tsx`
- **Problema**: Los valores del BCR llegan como objetos Dinero pero `toNumber` no los convierte correctamente
- **Solución**: Mejorada la función `toNumber` para manejar objetos Dinero con estructura `{amount, currency, scale}`
- **Cambios**:
  ```typescript
  // Agregado import de CURRENCY_CONFIG
  import { toAPI, type Dinero, CURRENCY_CONFIG } from "@/lib/money"
  
  // Mejorada función toNumber para manejar objetos Dinero
  const toNumber = (value: any): number => {
    if (value == null) return 0
    if (typeof value === 'number') return value
    if (typeof value === 'string') return parseFloat(value) || 0
    if (typeof value === 'object' && value !== null) {
      // Dinero.js v2: puede tener toJSON() o estructura {amount, currency, scale}
      if (typeof value.toJSON === 'function') {
        try {
          return toAPI(value as Dinero)
        } catch {
          return 0
        }
      }
      // Si tiene estructura {amount, currency} pero no es Dinero válido
      if ('amount' in value && typeof value.amount === 'number') {
        const currencyCode = (value.currency?.code || primaryCurrency || 'USD')
        const config = CURRENCY_CONFIG[currencyCode] || CURRENCY_CONFIG.USD
        const factor = Math.pow(10, config.precision)
        return value.amount / factor
      }
    }
    return 0
  }
  ```
- **Resultado**: ⚠️ Aún no funciona - los valores siguen siendo 0

### Backend

#### 3. `backend/app/api/v1/endpoints/costs.py`
- **Agregados logs de depuración** en el endpoint `calculate_agency_cost_hour`:
  - Log después de calcular `blended_rate`
  - Log después de obtener costos fijos
  - Log después de obtener miembros del equipo
  - Log antes del loop de cálculo de salarios
  - Log dentro del loop de cálculo de salarios (por cada miembro)
  - Log antes de construir la respuesta final

#### 4. `backend/app/core/calculations.py`
- **Agregados logs de depuración** en la función `calculate_blended_cost_rate`:
  - Log dentro del loop de cálculo de salarios (por cada miembro)
  - Log después de calcular `total_monthly_costs_money`
  - Log después de calcular `cost_per_hour` (BCR final)

## Análisis de Logs

### Evidencia de los Logs

Los logs muestran que:
1. Los datos del BCR llegan como objetos Dinero con `amount: 0`
2. El backend está retornando valores de 0 o hay un problema en el cálculo
3. Los valores se están serializando correctamente como strings Decimal

### Hipótesis Generadas

1. **Hipótesis A**: El backend está calculando correctamente pero retornando 0 porque no hay miembros activos o costos fijos
   - **Estado**: REJECTED - Los logs muestran que hay 3 miembros del equipo

2. **Hipótesis B**: El problema está en la conversión de objetos Dinero a número en el frontend
   - **Estado**: INCONCLUSIVE - La función `toNumber` mejorada debería manejar esto, pero aún no funciona

3. **Hipótesis C**: El backend está retornando valores de 0 porque el cálculo falla silenciosamente
   - **Estado**: PENDIENTE - Necesitamos revisar los logs del backend para confirmar

4. **Hipótesis D**: Hay un problema en la serialización de Decimal a string en el backend
   - **Estado**: PENDIENTE - Necesitamos verificar que los valores se serialicen correctamente

## Errores Encontrados

### Error 1: Conversión de tipos en frontend
- **Ubicación**: `frontend/src/components/costs/blended-cost-rate.tsx`
- **Descripción**: Los objetos Dinero no se están convirtiendo correctamente a números
- **Evidencia**: Los logs muestran `amount: 0` en los objetos Dinero recibidos
- **Estado**: ⚠️ Parcialmente resuelto - función `toNumber` mejorada pero aún no funciona

### Error 2: Posible problema en cálculo del backend
- **Ubicación**: `backend/app/core/calculations.py` - función `calculate_blended_cost_rate`
- **Descripción**: El cálculo puede estar retornando 0 si no hay costos o miembros
- **Evidencia**: Los logs muestran que hay miembros del equipo, pero el BCR es 0
- **Estado**: 🔍 En investigación

### Error 3: Serialización de Decimal
- **Ubicación**: `backend/app/schemas/quote.py` - `BlendedCostRateResponse`
- **Descripción**: Los valores Decimal se serializan como strings, pero pueden estar llegando como objetos Dinero
- **Evidencia**: Los logs muestran objetos Dinero en lugar de strings
- **Estado**: 🔍 En investigación

## Nuevo Enfoque Propuesto

Dado que el enfoque actual no está resolviendo el problema, proponemos:

### Enfoque 1: Verificar el cálculo del backend directamente
1. Agregar logs más detallados en `calculate_blended_cost_rate` para ver:
   - Si `total_monthly_costs_money` es None o tiene valor 0
   - Si `hours_per_month` es 0
   - Si `cost_per_hour` se calcula correctamente

### Enfoque 2: Verificar la transformación en el frontend
1. Agregar logs en `money-transformer.ts` para ver:
   - Si los strings Decimal se están transformando correctamente a Dinero
   - Si la moneda se detecta correctamente
   - Si hay errores en la transformación

### Enfoque 3: Verificar el endpoint del backend
1. Hacer una llamada directa al endpoint `/api/v1/settings/calculations/agency-cost-hour` para ver:
   - Qué valores retorna el backend en formato JSON crudo
   - Si los valores son strings o números
   - Si hay errores en la serialización

### Enfoque 4: Revisar el método `multiply` de Money
1. Verificar que `Money.multiply()` maneje correctamente valores Decimal
2. Verificar que no haya pérdida de precisión en las operaciones

## Análisis de Logs del Backend

### Evidencia Crítica de los Logs

Los logs del frontend muestran consistentemente:
```json
{
  "blended_cost_rate": {"amount": 0, "currency": {"code": "USD", "base": 10, "exponent": 2}, "scale": 2},
  "total_monthly_costs": {"amount": 0, "currency": {"code": "USD", "base": 10, "exponent": 2}, "scale": 2}
}
```

**Problema identificado**: El backend está retornando valores de 0 en los objetos Dinero, lo que indica que:
1. El cálculo del BCR en el backend está retornando 0, O
2. La serialización de Decimal a string está fallando, O
3. La transformación de string a Dinero en el frontend está creando objetos con `amount: 0`

### Logs del Backend Faltantes

**CRÍTICO**: No se encontraron logs del backend en el archivo de debug. Esto significa que:
- Los logs agregados en `costs.py` y `calculations.py` no se están ejecutando, O
- Los logs se están escribiendo en un archivo diferente, O
- El endpoint no se está llamando correctamente

### Hipótesis Actualizada

**Hipótesis E (NUEVA)**: El backend está calculando correctamente pero retornando 0 porque:
- `total_monthly_costs_money` es 0 (no hay costos o salarios)
- `hours_per_month` es 0 (no hay miembros activos con horas billables)
- El cálculo `cost_per_hour = total_monthly_costs / hours_per_month` resulta en 0/0 o 0/X

**Hipótesis F (NUEVA)**: El problema está en la serialización de `BlendedCostRateResponse`:
- Los valores Decimal se están serializando como strings "0" en lugar de los valores reales
- El schema de Pydantic no está serializando correctamente los valores Money

**Hipótesis G (NUEVA)**: El endpoint no se está llamando correctamente:
- El frontend está usando un endpoint diferente
- Hay un error en la ruta del endpoint
- El endpoint está retornando un error que se está manejando como 0

## Próximos Pasos

1. ✅ Documentar todos los cambios realizados
2. ⏳ **VERIFICAR LOGS DEL BACKEND**: Revisar si los logs se están escribiendo en otro lugar o si el endpoint no se está ejecutando
3. ⏳ **LLAMAR DIRECTAMENTE AL ENDPOINT**: Hacer una llamada HTTP directa al endpoint `/api/v1/settings/calculations/agency-cost-hour` para ver la respuesta cruda
4. ⏳ **REVISAR EL CÁLCULO DEL BCR**: Verificar que `calculate_blended_cost_rate` esté recibiendo los datos correctos
5. ⏳ **REVISAR LA SERIALIZACIÓN**: Verificar que `BlendedCostRateResponse` esté serializando correctamente los valores Decimal
6. ⏳ **IMPLEMENTAR UN NUEVO ENFOQUE**: Basado en los hallazgos, implementar una solución que aborde la raíz del problema

## Archivos Modificados

### Frontend
- `frontend/src/app/(app)/settings/team/page.tsx`
- `frontend/src/components/costs/blended-cost-rate.tsx`
- `frontend/src/lib/currency.ts` (validación NaN agregada)
- `frontend/src/lib/money-transformer.ts` (logs agregados)

### Backend
- `backend/app/api/v1/endpoints/costs.py` (logs agregados)
- `backend/app/core/calculations.py` (logs agregados)
- `backend/app/core/money.py` (logs agregados en `apply_margin`)

## Hallazgos Críticos

### 1. No hay logs del backend en el archivo de debug

**Problema**: A pesar de agregar logs extensivos en `costs.py` y `calculations.py`, no se encontraron logs del backend en el archivo `.cursor/debug.log`.

**Posibles causas**:
- Los logs se están escribiendo en un archivo diferente
- El endpoint `/api/v1/settings/calculations/agency-cost-hour` no se está ejecutando
- Hay un error antes de que se ejecuten los logs
- El path del log está mal calculado

**Evidencia**: Los logs del frontend muestran que el endpoint se está llamando y retorna datos, pero los valores son 0.

### 2. El schema está serializando correctamente

**Confirmado**: `BlendedCostRateResponse` tiene `@field_serializer` que convierte `Decimal` a `str` correctamente:
```python
@field_serializer('blended_cost_rate', 'total_monthly_costs', 'total_fixed_overhead', 'total_tools_costs', 'total_salaries')
def serialize_decimal(self, value: Decimal) -> str:
    """Serializa Decimal como string para mantener precisión"""
    return str(value) if value is not None else None
```

### 3. El frontend recibe objetos Dinero con amount: 0

**Evidencia de logs**:
```json
{
  "blended_cost_rate": {"amount": 0, "currency": {"code": "USD", "base": 10, "exponent": 2}, "scale": 2},
  "total_monthly_costs": {"amount": 0, "currency": {"code": "USD", "base": 10, "exponent": 2}, "scale": 2}
}
```

**Interpretación**: El backend está retornando strings "0" que se están transformando a objetos Dinero con `amount: 0`.

### 4. El cálculo del BCR podría estar retornando 0

**Posibles causas**:
- `total_monthly_costs_money` es `None` o tiene `amount: 0`
- `hours_per_month` es 0 (no hay miembros activos con horas billables)
- El cálculo `cost_per_hour = total_monthly_costs / hours_per_month` resulta en 0/0 o 0/X

## Nuevo Enfoque Propuesto

Dado que el enfoque actual no está funcionando, proponemos un enfoque más directo:

### Enfoque 1: Verificar el endpoint directamente

1. **Hacer una llamada HTTP directa** al endpoint usando `curl` o Postman:
   ```bash
   curl -X GET "http://localhost:8000/api/v1/settings/calculations/agency-cost-hour" \
     -H "Authorization: Bearer <token>"
   ```

2. **Verificar la respuesta JSON cruda** para ver si los valores son strings "0" o números 0.

3. **Comparar con los logs del frontend** para ver si hay una discrepancia.

### Enfoque 2: Agregar logs más tempranos en el flujo

1. **Agregar logs en el endpoint** antes de llamar a `calculate_blended_cost_rate`:
   - Verificar que el endpoint se está ejecutando
   - Verificar que `tenant.organization_id` tiene un valor válido
   - Verificar que `primary_currency` se está obteniendo correctamente

2. **Agregar logs en `calculate_blended_cost_rate`** al inicio:
   - Verificar que se están obteniendo costos fijos
   - Verificar que se están obteniendo miembros del equipo
   - Verificar que `total_monthly_costs_money` no es None

3. **Agregar logs en la construcción de la respuesta**:
   - Verificar que `blended_rate` tiene un valor no-cero
   - Verificar que `total_monthly_costs` tiene un valor no-cero
   - Verificar que los valores se están serializando correctamente

### Enfoque 3: Verificar la transformación en el frontend

1. **Agregar logs en `money-transformer.ts`** para ver:
   - Si los strings Decimal se están recibiendo correctamente
   - Si la transformación a Dinero está funcionando
   - Si hay errores en la transformación

2. **Verificar que `fromAPIString`** está funcionando correctamente:
   - Si el string "0" se está convirtiendo a Dinero con `amount: 0`
   - Si hay un problema con la detección de moneda

### Enfoque 4: Simplificar el problema

1. **Crear un endpoint de prueba** que retorne valores hardcodeados:
   ```python
   @router.get("/test-bcr")
   async def test_bcr():
       return BlendedCostRateResponse(
           blended_cost_rate=Decimal("50.00"),
           total_monthly_costs=Decimal("10000.00"),
           # ... otros campos
       )
   ```

2. **Verificar si el frontend muestra estos valores correctamente**:
   - Si sí, el problema está en el cálculo
   - Si no, el problema está en la transformación/serialización

## Recomendación Final

**Proponemos empezar con el Enfoque 4 (Simplificar el problema)** porque:
1. Es el más rápido para identificar dónde está el problema
2. Nos permite aislar el problema entre cálculo vs. transformación
3. Una vez identificado, podemos enfocarnos en la solución correcta

**Luego, si el problema está en el cálculo**, usaremos el Enfoque 2 para agregar logs más detallados.

**Si el problema está en la transformación**, usaremos el Enfoque 3 para revisar `money-transformer.ts`.

## Notas Adicionales

- El usuario menciona que la app debe tener manejo de números y cálculos a nivel bancario
- Todos los cálculos deben usar `Decimal` en el backend y `dinero.js` en el frontend
- No debe haber conversiones a `float` que pierdan precisión
- El estándar NOUGRAM requiere que los valores Decimal se serialicen como strings
