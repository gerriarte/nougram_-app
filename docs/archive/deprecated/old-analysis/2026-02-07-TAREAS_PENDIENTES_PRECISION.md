# 📋 Tareas Pendientes - Precisión Financiera

**Fecha:** 2025-12-30  
**Estado:** FASE 2 completada (100%), FASE 3 pendiente

---

## ✅ Completadas (FASE 1 y FASE 2)

### FASE 1: Fundación (11/11 - 100%)
- ✅ Clase `Money` con `Decimal` y `ROUND_HALF_UP`
- ✅ Instalación `dinero.js` v2 en frontend
- ✅ Módulos de dinero en backend y frontend
- ✅ Transformer de API con validación currency
- ✅ Configuración Pydantic para serialización Decimal → string
- ✅ Integración automática en `api-client.ts`
- ✅ Tests unitarios completos

### FASE 2: Migración Crítica (9/9 - 100%)
- ✅ Migración BD Float → Numeric(19,4)
- ✅ Actualización modelos SQLAlchemy
- ✅ Migración `calculate_blended_cost_rate` a Money
- ✅ Migración `calculate_quote_totals_enhanced` a Money
- ✅ Actualización endpoints para pasar `currency`
- ✅ Actualización schemas Pydantic con `field_serializer`
- ✅ Migración cálculos BCR en frontend a `dinero.js`
- ✅ Validación endpoint `/quotes/calculate` siempre recalcula
- ✅ Tests de integración de precisión
- ✅ Tests de SUM() en SQL con Numeric

---

## ⏳ Pendientes

### FASE 1: Fundación (1 tarea pendiente)

#### 1.1.2: Actualizar `backend/app/core/currency.py` para usar Money en formateo
**Prioridad:** Media  
**Archivo:** `backend/app/core/currency.py`

**Tareas:**
- [ ] Actualizar `format_currency()` para aceptar `Money` o `Decimal` además de `float`
- [ ] Mantener compatibilidad hacia atrás (aceptar `float`)
- [ ] Usar `Money.quantize()` para redondeo preciso
- [ ] Actualizar `normalize_to_primary_currency()` para usar `Money` internamente
- [ ] Actualizar `convert_currency()` para usar `Money` internamente

**Archivos relacionados que usan `format_currency`:**
- `backend/app/core/pdf_generator.py` - Tiene su propia `format_currency()`
- `backend/app/core/docx_generator.py` - Tiene su propia `format_currency()`
- `backend/app/core/calculations.py` - Usa `normalize_to_primary_currency()`

---

### FASE 3: Migración Completa y Validación (Pendiente)

#### Sprint 3.1: Migrar Todos los Cálculos Financieros

**3.1.1: Actualizar servicios restantes**

- [ ] `backend/app/services/annual_sales_projection_service.py`
  - Migrar cálculos de proyección anual a usar `Money`
  - Validar precisión en sumas acumulativas
  
- [ ] `backend/app/services/sales_projection_service.py`
  - Migrar cálculos de proyección de ventas a usar `Money`
  - Validar precisión en cálculos de margen
  
- [ ] `backend/app/services/credit_service.py`
  - Migrar cálculos de créditos a usar `Money`
  - Validar precisión en cálculos de intereses

- [ ] `backend/app/core/calculations.py` - Funciones restantes
  - [ ] `calculate_quote_totals()` (versión antigua, puede deprecarse)
  - [ ] `get_organization_cost_breakdown()` - Migrar a usar `Money`
  - [ ] `calculate_rentability_analysis()` - Migrar a usar `Money`

**3.1.2: Actualizar componentes frontend**

- [ ] `frontend/src/components/projections/AnnualProjectionMatrix.tsx`
  - Migrar cálculos a usar `dinero.js`
  - Validar precisión en proyecciones
  
- [ ] `frontend/src/components/quotes/QuoteSummary.tsx`
  - Migrar cálculos de resumen a usar `dinero.js`
  - Validar precisión en totales
  
- [ ] `frontend/src/components/costs/CostForm.tsx`
  - Migrar cálculos de costos a usar `dinero.js`
  - Validar precisión en formularios

- [ ] Buscar y migrar otros componentes que hagan cálculos financieros
  - Usar `grep` para encontrar usos de operaciones matemáticas con montos

#### Sprint 3.2: Actualizar Schemas y Validación

**3.2.1: Schemas Backend adicionales**

- [ ] Revisar todos los schemas en `backend/app/schemas/`
  - Identificar campos monetarios que aún usan `float`
  - Actualizar a `Decimal` con `field_serializer`
  
- [ ] Schemas a revisar:
  - `backend/app/schemas/billing.py`
  - `backend/app/schemas/credit.py`
  - `backend/app/schemas/cost.py`
  - `backend/app/schemas/team.py`
  - `backend/app/schemas/service.py`
  - Otros schemas que contengan campos monetarios

**3.2.2: Schemas Frontend**

- [ ] Crear/actualizar `frontend/src/lib/types/quote.ts` (si existe)
- [ ] Agregar tipos para Money usando `Dinero<number>`
- [ ] Crear helpers de conversión API ↔ Dinero

#### Sprint 3.3: Documentación y Guías

**3.3.1: Crear guía de uso**

- [ ] Crear: `docs/PRECISION_FINANCIERA.md`
- [ ] Documentar:
  - Cómo usar `Money` en backend
  - Cómo usar `dinero.js` en frontend
  - Mejores prácticas
  - Ejemplos de uso
  - Patrones comunes
  - Troubleshooting

**3.3.2: Actualizar documentación de API**

- [ ] Actualizar endpoints que retornan montos
- [ ] Especificar precisión esperada
- [ ] Documentar formato de respuesta (strings Decimal)
- [ ] Agregar ejemplos de requests/responses

**3.3.3: Migración completa de BD**

- [ ] Identificar TODOS los campos monetarios restantes que usan `Float`
- [ ] Crear migración Alembic para campos adicionales
- [ ] Validar que todos los modelos usan `Numeric`
- [ ] Tests de migración de datos

---

## 📊 Resumen de Progreso

### Por Fase:
- **FASE 1:** 11/12 tareas completadas (92%) - 1 pendiente
- **FASE 2:** 9/9 tareas completadas (100%) ✅
- **FASE 3:** 0/X tareas completadas (0%) - Pendiente

### Por Prioridad:
- **CRÍTICAS:** ✅ Todas completadas
- **IMPORTANTES:** ⏳ Pendientes (FASE 3)
- **OPCIONALES:** ⏳ Pendientes (Documentación, migración completa BD)

---

## 🎯 Próximos Pasos Recomendados

1. **Inmediato:** Completar FASE 1.1.2 (actualizar `currency.py`)
2. **Corto plazo:** Iniciar FASE 3.1 (migrar servicios restantes)
3. **Medio plazo:** Completar FASE 3.2 (schemas adicionales)
4. **Largo plazo:** FASE 3.3 (documentación y migración completa BD)

---

## 📝 Notas

- Las tareas críticas (FASE 2) están completadas
- El sistema ya tiene precisión grado bancario en cálculos críticos
- Las tareas pendientes son principalmente:
  - Migración de código legacy
  - Documentación
  - Optimización y limpieza
