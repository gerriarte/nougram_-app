# Estado de Implementación Backend - Amortización de Equipos

**Fecha:** 2026-01-25  
**Documento Base:** `UI_REQUIREMENTS_EQUIPMENT_AMORTIZATION.md`  
**Plan de Trabajo:** `PLAN_TRABAJO_AMORTIZACION_BACKEND.md`

Este documento compara los requerimientos de UI con la implementación actual del backend para identificar qué está implementado y qué falta.

---

## ❌ ESTADO GENERAL: NO IMPLEMENTADO

**El módulo de amortización de equipos NO está implementado en el backend.**

No se encontraron:
- ❌ Modelo `EquipmentAmortization`
- ❌ Archivo `backend/app/models/equipment.py`
- ❌ Endpoints de equipos
- ❌ Servicio de depreciación
- ❌ Integración con BCR

---

## 📋 REQUERIMIENTOS DEL UI vs BACKEND

### 1. Modelo de Datos

**❌ NO IMPLEMENTADO**

**Requerido:**
- Modelo `EquipmentAmortization` con campos:
  - `name`, `description`, `category`
  - `purchase_price`, `purchase_date`, `currency`
  - `exchange_rate_at_purchase` (TRM histórica) ⚠️ **CRÍTICO**
  - `useful_life_months`, `salvage_value`, `depreciation_method`
  - `monthly_depreciation`, `total_depreciated`, `remaining_value` (calculados)
  - `is_active`
  - Soporte multi-tenant (`organization_id`)
  - Soft delete (`deleted_at`, `deleted_by_id`)

**Ubicación Esperada:** `backend/app/models/equipment.py`

---

### 2. Schemas Pydantic

**❌ NO IMPLEMENTADO**

**Requerido:**
- `EquipmentAmortizationBase`
- `EquipmentAmortizationCreate` (con validación de TRM)
- `EquipmentAmortizationUpdate`
- `EquipmentAmortizationResponse` (con campos calculados: `months_depreciated`, `months_remaining`, `percentage_depreciated`)
- `EquipmentAmortizationListResponse`
- `DepreciationScheduleResponse`
- `DepreciationScheduleEntry`

**Validaciones Requeridas:**
- ✅ `purchase_price > 0`
- ✅ `salvage_value >= 0` y `salvage_value < purchase_price`
- ✅ `purchase_date` no futura
- ✅ `exchange_rate_at_purchase` requerido si `currency != primary_currency`
- ✅ `useful_life_months > 0`
- ✅ `depreciation_method` solo "straight_line" o "declining_balance"
- ✅ `category` solo valores válidos

**Ubicación Esperada:** `backend/app/schemas/equipment.py`

---

### 3. Servicio de Cálculo de Depreciación

**❌ NO IMPLEMENTADO**

**Requerido:**
- Clase `DepreciationService` con métodos:
  - `calculate_straight_line()` - Método línea recta
  - `calculate_declining_balance()` - Método saldo decreciente
  - `generate_depreciation_schedule()` - Cronograma con fechas y porcentajes
  - `calculate_depreciation_progress()` - Progreso actual (meses, porcentaje)

**Funcionalidad Requerida:**
- Cálculo de depreciación mensual
- Generación de cronograma mes a mes con fechas ISO 8601
- Cálculo de porcentaje depreciado por mes
- Cálculo de meses transcurridos y restantes
- No depreciar por debajo del valor de salvamento

**Ubicación Esperada:** `backend/app/services/depreciation_service.py`

---

### 4. Repository Layer

**❌ NO IMPLEMENTADO**

**Requerido:**
- `EquipmentRepository` heredando de `BaseRepository`
- Métodos:
  - `get_all_active()` - Equipos activos
  - `get_by_category()` - Filtrar por categoría
  - `get_by_depreciation_method()` - Filtrar por método
  - `get_active_equipment_for_bcr()` - Para cálculo BCR
- Tenant scoping automático
- Respeto de soft delete

**Ubicación Esperada:** `backend/app/repositories/equipment_repository.py`

**Registro en Factory:**
- Agregar `create_equipment_repository()` en `backend/app/repositories/factory.py`

---

### 5. Endpoints API

**❌ NO IMPLEMENTADO**

**Endpoints Requeridos:**

1. **`GET /api/v1/settings/equipment`** - Listar equipos
   - Paginación (`page`, `page_size`)
   - Filtros: `category`, `is_active`, `include_deleted`
   - Respuesta: `EquipmentAmortizationListResponse`

2. **`POST /api/v1/settings/equipment`** - Crear equipo
   - Validaciones completas (TRM, fecha, valor de salvamento)
   - Cálculo automático de `monthly_depreciation`
   - Invalidar cache de BCR
   - Respuesta: `EquipmentAmortizationResponse`

3. **`GET /api/v1/settings/equipment/{id}`** - Obtener equipo
   - Incluye campos calculados (`months_depreciated`, `months_remaining`, `percentage_depreciated`)
   - Respuesta: `EquipmentAmortizationResponse`

4. **`PUT /api/v1/settings/equipment/{id}`** - Actualizar equipo
   - Recalcula `monthly_depreciation` si cambian parámetros
   - Invalidar cache de BCR
   - Respuesta: `EquipmentAmortizationResponse`

5. **`DELETE /api/v1/settings/equipment/{id}`** - Eliminar equipo (soft delete)
   - Invalidar cache de BCR
   - Respuesta: `204 No Content`

6. **`POST /api/v1/settings/equipment/{id}/restore`** - Restaurar equipo
   - Respuesta: `EquipmentAmortizationResponse`

7. **`GET /api/v1/settings/equipment/{id}/depreciation-schedule`** - Cronograma
   - Query param: `months` (opcional, default: `useful_life_months`)
   - Respuesta: `DepreciationScheduleResponse` con fechas y porcentajes

8. **`GET /api/v1/settings/equipment/{id}/progress`** - Progreso actual ⚠️ **NUEVO**
   - Respuesta: Dict con `months_depreciated`, `months_remaining`, `percentage_depreciated`, etc.

**Permisos:**
- Crear/Editar/Eliminar: Requiere `can_modify_costs`
- Ver: Requiere autenticación

**Ubicación Esperada:** `backend/app/api/v1/endpoints/equipment.py`

**Registro en Router:**
- Agregar en `backend/app/api/v1/router.py`:
  ```python
  api_router.include_router(equipment.router, prefix="/settings", tags=["equipment"])
  ```

---

### 6. Integración con BCR

**❌ NO IMPLEMENTADO**

**Requerido:**

**Modificar:** `backend/app/core/calculations.py` - Función `calculate_blended_cost_rate()`

**Cambios Necesarios:**

1. **Agregar Query de Equipos:**
   ```python
   from app.models.equipment import EquipmentAmortization
   
   equipment_query = select(EquipmentAmortization).where(
       EquipmentAmortization.deleted_at.is_(None),
       EquipmentAmortization.is_active == True
   )
   if tenant_id is not None:
       equipment_query = equipment_query.where(
           EquipmentAmortization.organization_id == tenant_id
       )
   ```

2. **Conversión con TRM Histórica:**
   - Usar `exchange_rate_at_purchase` si existe
   - Convertir `monthly_depreciation` a moneda principal usando TRM histórica
   - **Sin re-expresión mensual** (valor fijo)

3. **Categorización:**
   - Hardware, Vehicles, Office Equipment → Overhead
   - Software → Tools/SaaS

4. **Agregar a Totales:**
   - Sumar `monthly_depreciation` de equipos a `all_costs`

5. **Actualizar Respuesta:**
   - Agregar `total_equipment_depreciation` a `BlendedCostRateResponse`
   - Agregar `equipment_breakdown` (opcional) con lista de equipos

**Modificar:** `backend/app/schemas/quote.py` - `BlendedCostRateResponse`

**Agregar Campos:**
- `total_equipment_depreciation: Decimal` (serializado como string)
- `equipment_breakdown: Optional[List[EquipmentBreakdown]]` (opcional)

---

### 7. Migración de Base de Datos

**❌ NO IMPLEMENTADO**

**Requerido:**
- Migración Alembic para crear tabla `equipment_amortization`
- Campos según modelo `EquipmentAmortization`
- Índices:
  - `ix_equipment_amortization_id`
  - `ix_equipment_amortization_organization_id`
  - `ix_equipment_amortization_category`
  - `ix_equipment_amortization_deleted_at`
  - `ix_equipment_amortization_is_active`
- Foreign Keys:
  - `organization_id` → `organizations.id`
  - `deleted_by_id` → `users.id`

**Ubicación Esperada:** `backend/alembic/versions/XXXX_add_equipment_amortization.py`

---

### 8. Tests

**❌ NO IMPLEMENTADO**

**Tests Requeridos:**

**Unitarios (`backend/tests/unit/test_depreciation_service.py`):**
- ✅ `test_calculate_straight_line_basic`
- ✅ `test_calculate_straight_line_with_salvage`
- ✅ `test_calculate_declining_balance_basic`
- ✅ `test_generate_depreciation_schedule_straight_line` (con fechas)
- ✅ `test_generate_depreciation_schedule_declining_balance` (con fechas)
- ✅ `test_depreciation_below_salvage_value`
- ✅ `test_calculate_depreciation_progress` ⚠️ **NUEVO**
- ✅ `test_schedule_includes_percentage_depreciated` ⚠️ **NUEVO**

**Integración Endpoints (`backend/tests/integration/test_equipment_endpoints.py`):**
- ✅ `test_create_equipment`
- ✅ `test_create_equipment_calculates_depreciation`
- ✅ `test_create_equipment_with_exchange_rate` ⚠️ **NUEVO**
- ✅ `test_create_equipment_requires_exchange_rate` ⚠️ **NUEVO**
- ✅ `test_purchase_date_not_future` ⚠️ **NUEVO**
- ✅ `test_salvage_value_less_than_purchase_price` ⚠️ **NUEVO**
- ✅ `test_list_equipment`
- ✅ `test_get_equipment` (incluye campos calculados)
- ✅ `test_update_equipment`
- ✅ `test_delete_equipment`
- ✅ `test_get_depreciation_schedule`
- ✅ `test_get_depreciation_progress` ⚠️ **NUEVO**
- ✅ `test_equipment_tenant_isolation`
- ✅ `test_equipment_permissions`

**Integración BCR (`backend/tests/integration/test_bcr_with_equipment.py`):**
- ✅ `test_bcr_includes_equipment_depreciation`
- ✅ `test_bcr_excludes_inactive_equipment`
- ✅ `test_bcr_excludes_deleted_equipment`
- ✅ `test_bcr_normalizes_equipment_currency`
- ✅ `test_bcr_uses_historical_exchange_rate` ⚠️ **NUEVO** (sin re-expresión)
- ✅ `test_bcr_categorizes_equipment` ⚠️ **NUEVO** (Hardware → Overhead, Software → Tools)

---

## 🎯 PRIORIZACIÓN DE IMPLEMENTACIÓN

### Prioridad Crítica (Bloqueantes)

1. **Modelo y Migración** (Fase 1)
   - Sin esto, no se puede avanzar
   - Incluir campo `exchange_rate_at_purchase` desde el inicio

2. **Schemas y Validaciones** (Fase 2)
   - Validaciones críticas: fecha no futura, TRM condicional, valor de salvamento
   - Sin validaciones correctas, el sistema puede tener datos inválidos

3. **Servicio de Cálculo** (Fase 2)
   - Core del módulo
   - Incluir `calculate_depreciation_progress()` para barras de vida útil

### Prioridad Alta

4. **Repository y Endpoints CRUD** (Fase 3-4)
   - Necesarios para que el frontend pueda interactuar
   - Incluir endpoint de progreso (`/progress`)

5. **Integración con BCR** (Fase 5)
   - Sin esto, los equipos no afectan el costo operacional
   - **CRÍTICO:** Usar TRM histórica (sin re-expresión mensual)

### Prioridad Media

6. **Tests** (Fase 6)
   - Asegurar calidad y prevenir regresiones
   - Incluir tests de TRM histórica

7. **Documentación** (Fase 7)
   - Actualizar guías de integración frontend

---

## 📊 RESUMEN DE COBERTURA

| Componente | Estado | Prioridad | Complejidad |
|------------|--------|-----------|-------------|
| Modelo EquipmentAmortization | ❌ No implementado | Crítica | Media |
| Migración de Base de Datos | ❌ No implementado | Crítica | Baja |
| Schemas Pydantic | ❌ No implementado | Crítica | Media |
| Servicio DepreciationService | ❌ No implementado | Crítica | Alta |
| Repository EquipmentRepository | ❌ No implementado | Alta | Baja |
| Endpoints CRUD | ❌ No implementado | Alta | Media |
| Endpoint Cronograma | ❌ No implementado | Alta | Media |
| Endpoint Progreso | ❌ No implementado | Alta | Baja |
| Integración BCR | ❌ No implementado | Crítica | Alta |
| Tests Unitarios | ❌ No implementado | Media | Media |
| Tests Integración | ❌ No implementado | Media | Alta |
| Documentación | ❌ No implementado | Media | Baja |

---

## ⚠️ REQUERIMIENTOS CRÍTICOS DEL UI

### 1. TRM Histórica (exchange_rate_at_purchase)

**Estado:** ❌ No implementado

**Importancia:** ⚠️ **CRÍTICA**

**Razón:**
- Sin TRM histórica, la amortización variaría mensualmente con fluctuaciones cambiarias
- Los activos no se re-expresan en el flujo de caja operativo
- Necesario para precisión contable y competitividad del BCR

**Implementación Requerida:**
- Campo `exchange_rate_at_purchase` en modelo
- Validación condicional: requerido si `currency != primary_currency`
- Uso en conversión de moneda en `calculate_blended_cost_rate()`
- Sin re-expresión mensual (valor fijo)

---

### 2. Valor de Salvamento

**Estado:** ❌ No implementado

**Importancia:** ⚠️ **CRÍTICA**

**Razón:**
- Sin valor de salvamento, el BCR será ~15% más alto de lo necesario
- Pérdida de competitividad en cotizaciones
- Los equipos tienen valor residual al final de su vida útil

**Implementación Requerida:**
- Campo `salvage_value` en modelo
- Validación: `salvage_value < purchase_price`
- Uso en cálculo de base depreciable: `(purchase_price - salvage_value)`
- Visualización clara en UI del impacto

---

### 3. Campos Calculados Dinámicos

**Estado:** ❌ No implementado

**Importancia:** Alta

**Razón:**
- Necesarios para barras de vida útil
- Necesarios para gráficos de valor en el tiempo
- Mejoran UX significativamente

**Implementación Requerida:**
- `calculate_depreciation_progress()` en `DepreciationService`
- Cálculo de `months_depreciated` (diferencia entre `purchase_date` y fecha actual)
- Cálculo de `months_remaining` (`useful_life_months - months_depreciated`)
- Cálculo de `percentage_depreciated` (`(total_depreciated / depreciable_base) × 100`)
- Incluir en `EquipmentAmortizationResponse`

---

### 4. Cronograma con Fechas

**Estado:** ❌ No implementado

**Importancia:** Alta

**Razón:**
- Necesario para gráfico de valor en el tiempo
- Mejora comprensión del usuario

**Implementación Requerida:**
- `generate_depreciation_schedule()` debe incluir `month_date` (ISO 8601)
- Calcular fecha de cada mes desde `purchase_date`
- Incluir `percentage_depreciated` por mes
- Opción `include_past_months` para filtrar meses pasados

---

## 🔧 CONSIDERACIONES TÉCNICAS ADICIONALES

### 1. Modificación de normalize_to_primary_currency

**Problema:**
La función `normalize_to_primary_currency()` en `backend/app/core/currency.py` probablemente no acepta TRM histórica como parámetro.

**Solución Requerida:**
- Agregar parámetro opcional `historical_exchange_rate: Optional[Decimal] = None`
- Si se proporciona, usar TRM histórica en lugar de TRM actual
- Mantener compatibilidad hacia atrás (parámetro opcional)

**Ubicación:** `backend/app/core/currency.py`

---

### 2. Cálculo de Meses Transcurridos

**Problema:**
Calcular meses transcurridos desde `purchase_date` requiere manejo preciso de fechas.

**Solución Requerida:**
- Usar `dateutil.relativedelta` para cálculo preciso
- Considerar timezone de `purchase_date`
- Cap a `useful_life_months` (no más de vida útil)

**Dependencia:** `python-dateutil` (ya puede estar instalado)

---

### 3. Actualización de total_depreciated

**Problema:**
`total_depreciated` debe actualizarse periódicamente o calcularse dinámicamente.

**Decisión:**
- **Calcular dinámicamente** en lugar de almacenar
- Usar `calculate_depreciation_progress()` al obtener equipo
- Evita necesidad de jobs periódicos
- Siempre refleja estado actual

---

## 📝 CHECKLIST DE IMPLEMENTACIÓN

### Fase 1: Modelo y Migración
- [ ] Crear `backend/app/models/equipment.py` con modelo `EquipmentAmortization`
- [ ] Incluir campo `exchange_rate_at_purchase` (Numeric, nullable)
- [ ] Crear migración Alembic
- [ ] Crear índices necesarios
- [ ] Registrar modelo en `__init__.py`
- [ ] Aplicar migración en desarrollo

### Fase 2: Schemas y Servicio
- [ ] Crear `backend/app/schemas/equipment.py` con todos los schemas
- [ ] Implementar validaciones (fecha no futura, TRM condicional, valor de salvamento)
- [ ] Crear `backend/app/services/depreciation_service.py`
- [ ] Implementar `calculate_straight_line()`
- [ ] Implementar `calculate_declining_balance()`
- [ ] Implementar `generate_depreciation_schedule()` (con fechas y porcentajes)
- [ ] Implementar `calculate_depreciation_progress()` ⚠️ **NUEVO**
- [ ] Tests unitarios del servicio

### Fase 3: Repository
- [ ] Crear `backend/app/repositories/equipment_repository.py`
- [ ] Implementar métodos de filtrado
- [ ] Registrar en `RepositoryFactory`

### Fase 4: Endpoints
- [ ] Crear `backend/app/api/v1/endpoints/equipment.py`
- [ ] Implementar todos los endpoints CRUD
- [ ] Implementar endpoint `/depreciation-schedule`
- [ ] Implementar endpoint `/progress` ⚠️ **NUEVO**
- [ ] Aplicar permisos correctos
- [ ] Invalidar cache de BCR
- [ ] Registrar router en `router.py`

### Fase 5: Integración BCR
- [ ] Modificar `calculate_blended_cost_rate()` en `calculations.py`
- [ ] Agregar query de equipos activos
- [ ] Implementar conversión con TRM histórica
- [ ] Implementar categorización (Hardware → Overhead, Software → Tools)
- [ ] Agregar equipos a `all_costs`
- [ ] Actualizar `BlendedCostRateResponse` schema
- [ ] Agregar `total_equipment_depreciation` y `equipment_breakdown`

### Fase 6: Tests
- [ ] Tests unitarios del servicio (incluye progreso y porcentajes)
- [ ] Tests de endpoints (incluye validaciones nuevas)
- [ ] Tests de integración BCR (incluye TRM histórica y categorización)
- [ ] Cobertura > 80%

### Fase 7: Documentación
- [ ] Docstrings completos en endpoints
- [ ] Actualizar `FRONTEND_API_INTEGRATION_GUIDE.md`
- [ ] Documentar manejo de TRM histórica
- [ ] Swagger UI muestra documentación correcta

---

## 🚀 PRÓXIMOS PASOS

1. **Revisar Plan:** Validar que el plan actualizado (`PLAN_TRABAJO_AMORTIZACION_BACKEND.md` v2.0) es correcto
2. **Crear Branch:** `feature/equipment-amortization`
3. **Implementar Fase 1:** Modelo y migración (incluir `exchange_rate_at_purchase`)
4. **Code Review:** Revisar modelo antes de continuar
5. **Implementar Fases Restantes:** Seguir plan secuencialmente
6. **Testing:** Ejecutar suite completa de tests
7. **Documentación:** Actualizar guías y Swagger
8. **Merge a Main:** Después de aprobación

---

## 📚 REFERENCIAS

- **Documento UI:** `docs/development/UI_REQUIREMENTS_EQUIPMENT_AMORTIZATION.md`
- **Plan de Trabajo:** `docs/development/PLAN_TRABAJO_AMORTIZACION_BACKEND.md` (v2.0)
- **Cálculos BCR:** `backend/app/core/calculations.py`
- **Normalización Moneda:** `backend/app/core/currency.py` (requiere modificación para TRM histórica)

---

**Última actualización:** 2026-01-25  
**Estado:** ❌ No implementado - Listo para desarrollo
