# Estado de Implementación Backend - CRUD de Cotización

**Fecha:** 2026-01-25  
**Documento Base:** `UI_REQUIREMENTS_QUOTE_CRUD.md`

Este documento compara los requerimientos de UI con la implementación actual del backend para identificar qué está implementado y qué falta.

---

## ✅ IMPLEMENTADO COMPLETAMENTE

### 1. Creación de Proyectos con Cotizaciones

**✅ Endpoint:** `POST /api/v1/projects/`

**✅ Schema:** `ProjectCreateWithQuote`
- ✅ `name` (requerido)
- ✅ `client_name` (requerido)
- ✅ `client_email` (opcional)
- ✅ `currency` (default: "USD")
- ✅ `tax_ids` (array opcional)
- ✅ `quote_items` (array requerido, mínimo 1)
- ✅ `revisions_included` (default: 2)
- ✅ `revision_cost_per_additional` (opcional)
- ✅ `target_margin_percentage` (opcional, 0-1)
- ✅ `allow_low_margin` (default: false)

**✅ Respuesta:** `QuoteResponseWithItems`
- ✅ Todos los campos calculados (`total_internal_cost`, `total_client_price`, `margin_percentage`)
- ✅ Items con desglose completo
- ✅ Versión inicial (default: 1)
- ✅ Timestamps (`created_at`, `updated_at`)

**✅ Validaciones:**
- ✅ Mínimo 1 item requerido
- ✅ Validación de servicios existentes
- ✅ Validación de campos según tipo de pricing
- ✅ Validación de rentabilidad con `allow_low_margin`

**Ubicación:** `backend/app/api/v1/endpoints/projects.py:138`

---

### 2. Cálculo en Tiempo Real

**✅ Endpoint:** `POST /api/v1/quotes/calculate`

**✅ Schema:** `QuoteCalculateRequest`
- ✅ `items` (array requerido)
- ✅ `expenses` (array opcional, Sprint 15)
- ✅ `tax_ids` (array opcional)
- ✅ `target_margin_percentage` (opcional, 0-1)
- ✅ `revisions_included` (default: 2)
- ✅ `revision_cost_per_additional` (opcional)
- ✅ `revisions_count` (opcional)

**✅ Respuesta:** `QuoteCalculateResponse`
- ✅ `total_internal_cost` (Decimal como string)
- ✅ `total_client_price` (Decimal como string)
- ✅ `total_expenses_cost` (Decimal como string)
- ✅ `total_expenses_client_price` (Decimal como string)
- ✅ `total_taxes` (Decimal como string)
- ✅ `total_with_taxes` (Decimal como string)
- ✅ `margin_percentage` (Decimal como string)
- ✅ `target_margin_percentage` (Decimal como string, opcional)
- ✅ `items` (desglose detallado por item)
- ✅ `expenses` (desglose detallado por gasto)
- ✅ `taxes` (desglose detallado por impuesto)
- ✅ `revisions_cost` (Decimal como string)
- ✅ `revisions_included` (int)
- ✅ `revisions_count` (int, opcional)

**✅ Funcionalidad:**
- ✅ Cálculo automático de BCR antes de calcular
- ✅ Soporte para múltiples tipos de pricing
- ✅ Cálculo de impuestos sobre `total_client_price`
- ✅ Cálculo de gastos con markup
- ✅ Cálculo de revisiones adicionales
- ✅ Aplicación de `target_margin_percentage` cuando se proporciona

**Ubicación:** `backend/app/api/v1/endpoints/quotes.py:25`

---

### 3. Tipos de Pricing Soportados

**✅ Pricing "hourly" (Por Hora):**
- ✅ Campo `estimated_hours` requerido
- ✅ Cálculo: `internal_cost = estimated_hours × BCR`
- ✅ Aplicación de margen objetivo
- ✅ Validación de campos requeridos

**✅ Pricing "fixed" (Precio Fijo):**
- ✅ Campo `fixed_price` requerido
- ✅ Campo `quantity` (default: 1.0)
- ✅ Cálculo: `internal_cost = fixed_price × quantity`
- ✅ Aplicación de margen objetivo

**✅ Pricing "recurring" (Recurrente):**
- ✅ Campo `recurring_price` requerido
- ✅ Campo `billing_frequency` requerido ("monthly" o "annual")
- ✅ Cálculo basado en frecuencia
- ✅ Aplicación de margen objetivo

**✅ Pricing "project_value" (Valor de Proyecto):**
- ✅ Campo `project_value` requerido
- ✅ Cálculo: `internal_cost = project_value × 0.60`
- ✅ `client_price = project_value`
- ✅ Cálculo de margen resultante

**✅ Override de Pricing Type:**
- ✅ El item puede sobrescribir el `pricing_type` del servicio
- ✅ Validación de campos según tipo efectivo

**Ubicación:** `backend/app/core/calculations.py:365` (función `calculate_quote_totals_enhanced`)

---

### 4. Sistema de Impuestos

**✅ Endpoint:** `GET /api/v1/taxes/`

**✅ Filtros Soportados:**
- ✅ `country` (filtro por país, ej: "CO")
- ✅ `is_active` (solo impuestos activos)
- ✅ `include_deleted` (incluir eliminados)
- ✅ Paginación (`page`, `page_size`)

**✅ Schema:** `TaxResponse`
- ✅ `id`, `name`, `code`
- ✅ `percentage` (Decimal como string)
- ✅ `country` (código de país)
- ✅ `is_active` (boolean)
- ✅ `description` (opcional)

**✅ Cálculo de Impuestos:**
- ✅ Los impuestos se calculan sobre `total_client_price` (antes de impuestos)
- ✅ Cada impuesto se calcula independientemente
- ✅ `total_taxes` = suma de todos los impuestos
- ✅ `total_with_taxes` = `total_client_price + total_taxes`

**✅ CRUD Completo:**
- ✅ Crear impuesto (`POST /api/v1/taxes/`)
- ✅ Actualizar impuesto (`PUT /api/v1/taxes/{tax_id}`)
- ✅ Eliminar impuesto (soft delete) (`DELETE /api/v1/taxes/{tax_id}`)
- ✅ Restaurar impuesto (`POST /api/v1/taxes/{tax_id}/restore`)
- ✅ Listar eliminados (`GET /api/v1/taxes/trash/list`)

**Ubicación:** `backend/app/api/v1/endpoints/taxes.py`

---

### 5. Gestión de Versiones

**✅ Endpoint:** `POST /api/v1/projects/{project_id}/quotes/{quote_id}/new-version`

**✅ Schema:** `QuoteCreateNewVersion`
- ✅ `items` (array requerido, mínimo 1)
- ✅ `notes` (opcional)
- ✅ `target_margin_percentage` (opcional, 0-1)
- ✅ `revisions_included` (opcional, default: 2)
- ✅ `revision_cost_per_additional` (opcional)
- ✅ `allow_low_margin` (default: false)

**✅ Funcionalidad:**
- ✅ Incrementa automáticamente el número de versión
- ✅ Crea nueva cotización con los nuevos items
- ✅ Mantiene relación con el mismo proyecto
- ✅ Valida rentabilidad con `allow_low_margin`
- ✅ Retorna `QuoteResponseWithItems` con versión incrementada

**✅ Listar Versiones:**
- ✅ `GET /api/v1/projects/{project_id}/quotes` retorna todas las versiones
- ✅ Cada `QuoteResponse` incluye campo `version`

**Ubicación:** `backend/app/api/v1/endpoints/projects.py:777`  
**Servicio:** `backend/app/services/project_service.py:240`

---

### 6. Validación de Rentabilidad (`allow_low_margin`)

**✅ Implementación Completa:**

**✅ Validación en Creación:**
- ✅ `ProjectCreateWithQuote.allow_low_margin` (default: false)
- ✅ Validación en `ProjectService.create_project_with_quote()`

**✅ Validación en Actualización:**
- ✅ `QuoteUpdate.allow_low_margin` (default: false)
- ✅ Validación en `ProjectService.update_quote()`

**✅ Validación en Nueva Versión:**
- ✅ `QuoteCreateNewVersion.allow_low_margin` (default: false)
- ✅ Validación en `ProjectService.create_new_quote_version()`

**✅ Lógica de Validación:**
- ✅ Función `_validate_quote_profitability()` en `ProjectService`
- ✅ Compara `margin_percentage` con umbral mínimo configurado
- ✅ Si `allow_low_margin === false` y margen < umbral → lanza `BusinessLogicError`
- ✅ Si `allow_low_margin === true` → permite pero registra warning
- ✅ Mensajes de error detallados con cálculo de precio requerido

**✅ Umbral Mínimo:**
- ✅ Se obtiene de `Organization.settings.minimum_margin_threshold`
- ✅ Default: 0.15 (15%) si no está configurado

**Ubicación:** `backend/app/services/project_service.py:551`

---

### 7. Gastos de Terceros (Expenses)

**✅ Soporte Completo (Sprint 15):**

**✅ Schema:** `QuoteExpenseCreate`
- ✅ `name` (requerido)
- ✅ `description` (opcional)
- ✅ `cost` (Decimal como string, requerido, min: 0)
- ✅ `markup_percentage` (Decimal como string, default: "0.0", 0-10)
- ✅ `category` (opcional: "Third Party", "Materials", "Licenses")
- ✅ `quantity` (Decimal como string, default: "1.0", min: 0)

**✅ Cálculo:**
- ✅ `expense_cost = cost × quantity`
- ✅ `client_price = expense_cost × (1 + markup_percentage)`
- ✅ Se suma a `total_internal_cost` y `total_client_price`

**✅ Modelo:** `QuoteExpense`
- ✅ Relación con `Quote` (cascade delete)
- ✅ Campos: `name`, `description`, `cost`, `markup_percentage`, `client_price`, `category`, `quantity`

**✅ Endpoint de Cálculo:**
- ✅ `POST /api/v1/quotes/calculate` acepta `expenses` en el request
- ✅ Retorna `expenses` breakdown en la respuesta

**Ubicación:** `backend/app/models/project.py:107` (modelo)  
**Cálculo:** `backend/app/core/calculations.py:505` (función `calculate_quote_totals_enhanced`)

---

### 8. Sistema de Revisiones

**✅ Soporte Completo (Sprint 16):**

**✅ Campos en Quote:**
- ✅ `revisions_included` (int, default: 2)
- ✅ `revision_cost_per_additional` (Numeric, opcional)

**✅ Cálculo:**
- ✅ Si `revisions_count > revisions_included`:
  - `additional_revisions = revisions_count - revisions_included`
  - `revisions_cost = revision_cost_per_additional × additional_revisions`
  - Se suma a `total_client_price`

**✅ Schemas:**
- ✅ `ProjectCreateWithQuote.revisions_included` (opcional, default: 2)
- ✅ `ProjectCreateWithQuote.revision_cost_per_additional` (opcional)
- ✅ `QuoteCalculateRequest.revisions_included` (opcional, default: 2)
- ✅ `QuoteCalculateRequest.revision_cost_per_additional` (opcional)
- ✅ `QuoteCalculateRequest.revisions_count` (opcional, para cálculo)

**✅ Respuesta:**
- ✅ `QuoteCalculateResponse.revisions_cost` (Decimal como string)
- ✅ `QuoteCalculateResponse.revisions_included` (int)
- ✅ `QuoteCalculateResponse.revisions_count` (int, opcional)

**Ubicación:** `backend/app/models/project.py:73` (modelo Quote)  
**Cálculo:** `backend/app/core/calculations.py:581` (función `calculate_quote_totals_enhanced`)

---

### 9. Selector de Servicios

**✅ Endpoint:** `GET /api/v1/services/`

**✅ Filtros Soportados:**
- ✅ `active_only` (solo servicios activos)
- ✅ `include_deleted` (incluir eliminados)
- ✅ Paginación (`page`, `page_size`)

**✅ Schema:** `ServiceResponse`
- ✅ `id`, `name`, `description`
- ✅ `pricing_type` ("hourly", "fixed", "recurring", "project_value")
- ✅ `default_margin_target` (Decimal como string, 0-1)
- ✅ `is_active` (boolean)
- ✅ `fixed_price` (si aplica)
- ✅ `recurring_price` (si aplica)
- ✅ `billing_frequency` (si aplica)

**✅ CRUD Completo:**
- ✅ Crear servicio (`POST /api/v1/services/`)
- ✅ Actualizar servicio (`PUT /api/v1/services/{service_id}`)
- ✅ Eliminar servicio (soft delete) (`DELETE /api/v1/services/{service_id}`)
- ✅ Restaurar servicio (`POST /api/v1/services/{service_id}/restore`)

**Ubicación:** `backend/app/api/v1/endpoints/services.py`

---

### 10. Actualización de Cotizaciones

**✅ Endpoint:** `PUT /api/v1/projects/{project_id}/quotes/{quote_id}`

**✅ Schema:** `QuoteUpdate`
- ✅ `items` (array requerido, mínimo 1)
- ✅ `notes` (opcional)
- ✅ `target_margin_percentage` (opcional, 0-1)
- ✅ `revisions_included` (opcional)
- ✅ `revision_cost_per_additional` (opcional)
- ✅ `allow_low_margin` (default: false)

**✅ Funcionalidad:**
- ✅ Recalcula totales con nuevos items
- ✅ Valida rentabilidad con `allow_low_margin`
- ✅ Actualiza items existentes (cascade delete y recreate)
- ✅ Retorna `QuoteResponseWithItems` actualizado

**Ubicación:** `backend/app/api/v1/endpoints/projects.py:600`  
**Servicio:** `backend/app/services/project_service.py:300`

---

## ⚠️ IMPLEMENTADO PARCIALMENTE

### 1. Endpoint de BCR (Blended Cost Rate)

**⚠️ Estado:** El BCR se calcula internamente pero **NO existe un endpoint público dedicado**

**✅ Lo que SÍ existe:**
- ✅ Función `calculate_blended_cost_rate()` en `backend/app/core/calculations.py`
- ✅ Se calcula automáticamente en `POST /api/v1/quotes/calculate`
- ✅ Se calcula automáticamente en `POST /api/v1/projects/` (crear cotización)

**❌ Lo que FALTA:**
- ❌ Endpoint `GET /api/v1/quotes/blended-cost-rate` como se especifica en el documento UI
- ❌ Respuesta estructurada `BlendedCostRateResponse` con desglose completo:
  - `blended_cost_rate`
  - `total_monthly_costs`
  - `total_fixed_overhead`
  - `total_tools_costs`
  - `total_salaries`
  - `total_monthly_hours`
  - `active_team_members`
  - `primary_currency`
  - `currencies_used`
  - `exchange_rates_date`

**Recomendación:**
- Crear endpoint `GET /api/v1/quotes/blended-cost-rate` que retorne `BlendedCostRateResponse`
- Útil para mostrar información contextual en el frontend antes de crear cotizaciones

**Ubicación Actual:** `backend/app/core/calculations.py:272` (función `calculate_blended_cost_rate`)

---

### 2. Comparación de Versiones

**⚠️ Estado:** **NO IMPLEMENTADO**

**❌ Endpoint Faltante:**
- ❌ `GET /api/v1/projects/{project_id}/quotes/{quote_id}/compare?compare_with={other_quote_id}`

**❌ Schema Faltante:**
- ❌ `QuoteComparisonResponse`
- ❌ `QuoteDifference`

**Funcionalidad Requerida:**
- Comparar dos versiones de cotización lado a lado
- Identificar diferencias en:
  - `total_client_price`
  - `total_internal_cost`
  - `margin_percentage`
  - Items agregados/eliminados/modificados
  - Cambios en horas estimadas, precios, etc.

**Recomendación:**
- Crear endpoint de comparación que retorne diferencias estructuradas
- Útil para UI de comparación lado a lado

---

### 3. Mejora de Descripción con IA

**⚠️ Estado:** **NO IMPLEMENTADO**

**❌ Endpoint Faltante:**
- ❌ `POST /api/v1/ai/enhance-description`

**❌ Schemas Faltantes:**
- ❌ `EnhanceDescriptionRequest`
- ❌ `EnhanceDescriptionResponse`

**✅ Lo que SÍ existe:**
- ✅ Sistema de créditos de IA (`CreditService`)
- ✅ Endpoints de IA existentes (`POST /api/v1/ai/analyze`, `POST /api/v1/ai/process-command`)
- ✅ Validación de créditos antes de consumir

**Funcionalidad Requerida:**
- Recibir descripción actual y contexto del proyecto
- Mejorar descripción usando IA (OpenAI/Gemini)
- Consumir créditos de IA según el plan
- Retornar descripción mejorada y créditos restantes

**Recomendación:**
- Crear endpoint específico para mejora de descripciones
- Integrar con sistema de créditos existente
- Validar créditos disponibles antes de ejecutar

---

### 4. Selector de Clientes Inteligente

**⚠️ Estado:** **NO EXISTE MODELO CLIENT SEPARADO**

**✅ Lo que SÍ existe:**
- ✅ Campos `client_name` y `client_email` directamente en `Project`
- ✅ Se pueden crear proyectos con `client_name` y `client_email` sin necesidad de crear cliente primero

**❌ Lo que FALTA:**
- ❌ Modelo `Client` separado
- ❌ Endpoint `POST /api/v1/clients/` para crear clientes
- ❌ Endpoint `GET /api/v1/clients/` para listar clientes
- ❌ Relación `Project.client_id` (actualmente solo `client_name` y `client_email`)

**Impacto:**
- El documento UI especifica un "Selector de Clientes Inteligente" con creación rápida
- Actualmente, el frontend puede usar `client_name` y `client_email` directamente
- No hay reutilización de datos de clientes entre proyectos

**Recomendación:**
- **Opción 1 (Rápida):** Mantener `client_name` y `client_email` en `Project`, pero agregar endpoint `GET /api/v1/projects/?client_name={name}` para buscar proyectos por cliente
- **Opción 2 (Completa):** Crear modelo `Client` y migrar datos existentes, agregar relación `Project.client_id`

---

## ❌ NO IMPLEMENTADO

### 1. Tracking Token

**❌ Estado:** **NO IMPLEMENTADO** (pero está en el plan de trabajo)

**Nota:** El tracking token está planificado en `PLAN_TRABAJO_QUOTES_DASHBOARD_BACKEND.md` (Sprint 1), pero aún no está implementado.

**Faltante:**
- ❌ Campo `tracking_token` en modelo `Quote`
- ❌ Generación automática de `tracking_token` al enviar cotización
- ❌ Endpoints de tracking (`GET /api/v1/tracking/pixel/{quote_id}/{token}`, etc.)

**Referencia:** Ver `docs/development/PLAN_TRABAJO_QUOTES_DASHBOARD_BACKEND.md` para plan de implementación.

---

## 📊 RESUMEN DE COBERTURA

| Funcionalidad | Estado | Prioridad |
|---------------|--------|-----------|
| Crear proyecto con cotización | ✅ Completo | Alta |
| Cálculo en tiempo real | ✅ Completo | Alta |
| Tipos de pricing (4 tipos) | ✅ Completo | Alta |
| Sistema de impuestos | ✅ Completo | Alta |
| Gestión de versiones | ✅ Completo | Alta |
| Validación `allow_low_margin` | ✅ Completo | Alta |
| Gastos de terceros (expenses) | ✅ Completo | Media |
| Sistema de revisiones | ✅ Completo | Media |
| Selector de servicios | ✅ Completo | Alta |
| Actualización de cotizaciones | ✅ Completo | Alta |
| Endpoint BCR público | ⚠️ Parcial | Media |
| Comparación de versiones | ❌ No implementado | Baja |
| Mejora descripción con IA | ❌ No implementado | Media |
| Selector clientes inteligente | ⚠️ Parcial | Media |
| Tracking token | ❌ No implementado | Alta (en plan) |

---

## 🎯 RECOMENDACIONES DE PRIORIZACIÓN

### Prioridad Alta (Bloqueantes para UI)
1. **Ninguna** - Todas las funcionalidades críticas están implementadas ✅

### Prioridad Media (Mejoras UX)
1. **Endpoint BCR Público** - Útil para mostrar información contextual antes de crear cotizaciones
2. **Mejora de Descripción con IA** - Feature diferenciador que consume créditos
3. **Selector de Clientes Inteligente** - Mejora UX pero no bloqueante (se puede usar `client_name` directamente)

### Prioridad Baja (Nice to Have)
1. **Comparación de Versiones** - Útil pero no crítico, se puede implementar después

---

## 📝 NOTAS TÉCNICAS

### Precisión Monetaria
✅ **Implementado Correctamente:**
- Todos los valores monetarios usan `Decimal` en el backend
- Se serializan como `string` en respuestas JSON
- Cumple con ESTÁNDAR NOUGRAM

### Validaciones
✅ **Implementadas:**
- Validación de campos obligatorios según tipo de pricing
- Validación de rentabilidad con `allow_low_margin`
- Validación de servicios existentes
- Validación de impuestos activos

### Manejo de Errores
✅ **Implementado:**
- HTTP 400 para datos inválidos
- HTTP 404 para recursos no encontrados
- HTTP 403 para permisos insuficientes
- `BusinessLogicError` para violaciones de lógica de negocio

---

**Fin del Documento**
