# Issues para Linear - Debugging BCR

## Problema Principal: BCR muestra valores en 0

**Estado**: En progreso
**Prioridad**: Alta
**Sprint**: Actual

### Descripción
El componente Blended Cost Rate (BCR) en el frontend muestra todos los valores en 0, aunque el backend aparentemente calcula valores correctos.

### Pasos para Reproducir
1. Ir a `/settings/team`
2. Revisar la card de BCR (Blended Cost Rate)
3. Todos los valores aparecen como $0.00 USD

### Hallazgos

#### 1. Endpoint de Prueba Creado
- **Archivo**: `backend/app/api/v1/endpoints/costs.py:388`
- **Endpoint**: `/api/v1/settings/calculations/agency-cost-hour-test`
- **Propósito**: Retornar valores hardcodeados para aislar el problema
- **Estado**: Implementado, backend reiniciado
- **Nota**: El endpoint fue creado pero aún no se ha verificado si funciona correctamente (se recibió error 404 inicialmente, luego se reinició el backend)

#### 2. Problema de Serialización/Transformación
- **Archivos afectados**: 
  - `frontend/src/lib/money-transformer.ts`
  - `frontend/src/components/costs/blended-cost-rate.tsx`
- **Síntoma**: Valores Decimal del backend serializados como string no se convierten correctamente a números
- **Solución temporal**: Se agregó función `toNumber` para convertir strings, números y objetos Dinero

#### 3. Warning sobre Currency Field
- **Ubicación**: Console del navegador
- **Mensaje**: `[Money Transformer] Using USD as fallback. Fix API response to include currency field.`
- **Causa**: El `detectCurrency` en `money-transformer.ts` no detecta `primary_currency` correctamente en algunos casos
- **Estado**: Secundario, no crítico para el funcionamiento

### Cambios Realizados

1. **Endpoint de Prueba** (`backend/app/api/v1/endpoints/costs.py`)
   - Nuevo endpoint `/calculations/agency-cost-hour-test` con valores hardcodeados
   - Retorna: `blended_cost_rate=50.00`, `total_monthly_costs=10000.00`, etc.

2. **Frontend Query Hook** (`frontend/src/lib/queries/dashboard.ts`)
   - Modificado `useGetBlendedCostRate` para usar el endpoint de prueba temporalmente

3. **Componente BCR** (`frontend/src/components/costs/blended-cost-rate.tsx`)
   - Agregada función `toNumber` para manejar conversión de tipos
   - Agregados logs de debugging

4. **Conversión de Tipos** (`frontend/src/app/(app)/settings/costs/page.tsx`)
   - Normalización de `amount_monthly` de string a number

### Próximos Pasos

1. ✅ Crear endpoint de prueba con valores hardcodeados
2. ⏳ Verificar que el endpoint de prueba funcione (probar después de reinicio del backend)
3. ⏳ Si el endpoint de prueba funciona → el problema está en el cálculo del backend
4. ⏳ Si el endpoint de prueba NO funciona → el problema está en la transformación/serialización
5. ⏳ Una vez identificado el problema, implementar fix definitivo
6. ⏳ Remover endpoint de prueba y logs de debugging
7. ⏳ Volver a usar el endpoint real `/calculations/agency-cost-hour`

### Archivos Modificados

- `backend/app/api/v1/endpoints/costs.py` - Endpoint de prueba
- `frontend/src/lib/queries/dashboard.ts` - Query hook temporal
- `frontend/src/components/costs/blended-cost-rate.tsx` - Función toNumber y logs
- `frontend/src/app/(app)/settings/costs/page.tsx` - Normalización de tipos
- `docs/DEBUG_BCR_ISSUE.md` - Documentación del debugging

### Notas Técnicas

- El backend serializa Decimal como string (estándar NOUGRAM)
- El frontend usa dinero.js v2 para manejo de valores monetarios
- El endpoint real calcula BCR usando `calculate_blended_cost_rate`
- El endpoint de prueba retorna valores fijos para aislar problemas de display

### Referencias

- Documentación detallada: `docs/DEBUG_BCR_ISSUE.md`
- Endpoint real: `/api/v1/settings/calculations/agency-cost-hour`
- Endpoint de prueba: `/api/v1/settings/calculations/agency-cost-hour-test`
