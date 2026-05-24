# Backend Specification: Quotes & Pipeline Module

**Version:** 2.0  
**Date:** 2026-01-25  
**Scope:** Data modeling, API contract, and business logic for the Quote Lifecycle  
**Status:** Partial Implementation - See `BACKEND_IMPLEMENTATION_STATUS_QUOTE_CRUD.md` and `PLAN_TRABAJO_QUOTES_DASHBOARD_BACKEND.md`

---

## Resumen Ejecutivo

Este documento especifica la arquitectura completa del módulo de Cotizaciones (Quotes) y Pipeline de Envío. El sistema está parcialmente implementado: el CRUD básico está completo, pero faltan funcionalidades avanzadas de tracking, estados extendidos y métricas avanzadas.

**Estado Actual:**
- ✅ CRUD básico de cotizaciones implementado
- ✅ Cálculo en tiempo real implementado
- ✅ Sistema de versiones básico implementado
- ✅ BCR locking básico implementado (congelamiento de `total_internal_cost`)
- ❌ **Endpoint de transición de estados (Drag & Drop)** NO implementado (ver Sprint 2)
- ❌ **Snapshots de costos por item** NO implementados (ver Sprint 2)
- ❌ Sistema de tracking NO implementado (ver Sprint 1 del plan)
- ❌ Estados extendidos NO implementados (ver Sprint 2 del plan)
- ❌ Métricas avanzadas parcialmente implementadas (ver Sprint 3 del plan)

**Nuevas Funcionalidades Documentadas (Sprint 2):**
- **Endpoint `PATCH /api/v1/quotes/{id}/status`:** Soporta Drag & Drop del Pipeline con validación de transiciones (State Machine)
- **Snapshots de Costos:** Congelamiento de costos por item al mover a "Sent" para garantizar inmutabilidad
- **Prevención de Regresión:** Bloqueo de transición `Sent → Draft` para mantener integridad financiera
- **Máquina de Estados Completa:** Diagrama y tabla de transiciones permitidas/no permitidas

**Nuevas Funcionalidades Documentadas (Sprint 3):**
- **Endpoint `GET /api/v1/analytics/dashboard`:** Dashboard de analytics con cálculos optimizados directamente en SQL
- **Eficiencia SQL:** Todos los cálculos (Utilidad Neta, agregaciones) se hacen en base de datos, no en memoria
- **Performance:** Diseñado para manejar 1000+ cotizaciones con tiempos de respuesta < 500ms
- **Índices Optimizados:** Especificación de índices de base de datos para queries rápidas

**Referencias:**
- **Plan de Trabajo:** `PLAN_TRABAJO_QUOTES_DASHBOARD_BACKEND.md`
- **Estado de Implementación CRUD:** `BACKEND_IMPLEMENTATION_STATUS_QUOTE_CRUD.md`
- **Requerimientos UI:** `UI_REQUIREMENTS_QUOTES_DASHBOARD.md` y `UI_REQUIREMENTS_QUOTE_CRUD.md`

---

## 1. Database Schema (SQLAlchemy Models)

### 1.1 `projects` Table

**Ubicación:** `backend/app/models/project.py`

Core table for projects (clients and proposals container).

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | Integer | PK | Unique Identifier |
| `name` | String | Not Null | Project name |
| `client_name` | String | Not Null | Client name |
| `client_email` | String | Index, Nullable | Client email (for CRM lookups) |
| `status` | String | Default 'Draft' | **Current:** `Draft`, `Sent`, `Won`, `Lost`<br>**Planned:** `Viewed`, `Accepted`, `Rejected`, `Expired` |
| `currency` | String(3) | Default 'USD' | Currency code (USD, COP, EUR, ARS) |
| `organization_id` | Integer | FK, Index | Multi-tenancy isolation |
| `created_at` | DateTime(timezone) | Auto Now | |
| `updated_at` | DateTime(timezone) | Auto Update | |
| `deleted_at` | DateTime(timezone) | Nullable, Index | Soft delete |
| `deleted_by_id` | Integer | FK, Nullable | User who deleted |

**Relationships:**
- `quotes`: One-to-many with `Quote`
- `taxes`: Many-to-many with `Tax` (via `project_taxes` table)

**Nota:** El estado del proyecto se almacena en `Project.status`, pero el plan de trabajo propone usar estados más granulares a nivel de `Quote` para mejor tracking.

---

### 1.2 `quotes` Table

**Ubicación:** `backend/app/models/project.py`

Core header table for proposals/quotations.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | Integer | PK | Unique Identifier |
| `project_id` | Integer | FK, Not Null | Reference to Project |
| `version` | Integer | Default 1 | Version number for tracking revisions |
| `total_internal_cost` | Numeric(19,4) | Nullable | Internal BCR Cost (ESTÁNDAR NOUGRAM) |
| `total_client_price` | Numeric(19,4) | Nullable | Client Price (Before Tax) (ESTÁNDAR NOUGRAM) |
| `margin_percentage` | Numeric(10,4) | Nullable | Calculated margin (result) (ESTÁNDAR NOUGRAM) |
| `target_margin_percentage` | Numeric(10,4) | Nullable | Target margin (0-1, e.g., 0.40 = 40%) |
| `notes` | String | Nullable | Notes for the quote |
| `revisions_included` | Integer | Default 2, Not Null | Number of included revisions (Sprint 16) |
| `revision_cost_per_additional` | Numeric(19,4) | Nullable | Cost per additional revision (Sprint 16) |
| `created_at` | DateTime(timezone) | Auto Now | |
| `updated_at` | DateTime(timezone) | Auto Update | |

**Campos Planificados (Sprint 1 - Tracking):**
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `tracking_token` | String | Nullable, Unique, Index | Unique token for tracking (generated on send) |
| `tracking_enabled` | Boolean | Default True | Whether tracking is enabled for this quote |
| `sent_at` | DateTime(timezone) | Nullable | When quote was sent |
| `viewed_at` | DateTime(timezone) | Nullable | First time quote was viewed |
| `viewed_count` | Integer | Default 0 | Number of times quote was viewed |
| `last_viewed_at` | DateTime(timezone) | Nullable | Last time quote was viewed |
| `downloaded_count` | Integer | Default 0 | Number of times PDF was downloaded |
| `last_downloaded_at` | DateTime(timezone) | Nullable | Last time PDF was downloaded |
| `expires_at` | DateTime(timezone) | Nullable | Expiration date (30 days from sent_at) |
| `accepted_at` | DateTime(timezone) | Nullable | When quote was accepted |
| `rejected_at` | DateTime(timezone) | Nullable | When quote was rejected |

**Relationships:**
- `project`: Many-to-one with `Project`
- `items`: One-to-many with `QuoteItem` (cascade delete)
- `expenses`: One-to-many with `QuoteExpense` (cascade delete)

**ESTÁNDAR NOUGRAM:**
- Todos los campos monetarios usan `Numeric(precision=19, scale=4)` para precisión grado bancario
- Los valores se serializan como `string` en las respuestas JSON

---

### 1.3 `quote_items` Table

**Ubicación:** `backend/app/models/project.py`

Line items for each quote (services included).

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | Integer | PK | |
| `quote_id` | Integer | FK, Not Null | Reference to Quote |
| `service_id` | Integer | FK, Not Null | Reference to Service Catalog |
| `estimated_hours` | Numeric(10,4) | Nullable | Hours (required for hourly pricing) |
| `internal_cost` | Numeric(19,4) | Nullable | Internal cost (calculated) (ESTÁNDAR NOUGRAM) |
| `client_price` | Numeric(19,4) | Nullable | Client price (calculated) (ESTÁNDAR NOUGRAM) |
| `margin_percentage` | Numeric(10,4) | Nullable | Item margin (calculated) (ESTÁNDAR NOUGRAM) |
| `pricing_type` | String | Nullable | Override service pricing: `hourly`, `fixed`, `recurring`, `project_value` |
| `fixed_price` | Numeric(19,4) | Nullable | Fixed price (if pricing_type = "fixed") |
| `quantity` | Numeric(10,4) | Default 1.0 | Quantity for fixed/recurring pricing |
| `unit_cost_snapshot` | Numeric(19,4) | Nullable | **Sprint 2:** BCR congelado por hora al enviar (ESTÁNDAR NOUGRAM) |
| `internal_cost_snapshot` | Numeric(19,4) | Nullable | **Sprint 2:** Costo interno total congelado (ESTÁNDAR NOUGRAM) |
| `client_price_snapshot` | Numeric(19,4) | Nullable | **Sprint 2:** Precio cliente congelado (ESTÁNDAR NOUGRAM) |
| `snapshot_date` | DateTime(timezone) | Nullable | **Sprint 2:** Fecha en que se congelaron los costos |

**Nota:** El `pricing_type` puede sobrescribir el tipo de pricing del servicio, permitiendo flexibilidad por cotización.

---

### 1.4 `quote_expenses` Table

**Ubicación:** `backend/app/models/project.py`

Third-party costs, materials, licenses with markup (Sprint 15).

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | Integer | PK | |
| `quote_id` | Integer | FK, Not Null, Index | Reference to Quote |
| `name` | String | Not Null | Expense name |
| `description` | String | Nullable | Expense description |
| `cost` | Numeric(19,4) | Not Null | Real cost (ESTÁNDAR NOUGRAM) |
| `markup_percentage` | Numeric(10,4) | Default 0.0 | Mark-up percentage (0.10 = 10%) |
| `client_price` | Numeric(19,4) | Not Null | cost × quantity × (1 + markup) |
| `category` | String | Nullable | "Third Party", "Materials", "Licenses" |
| `quantity` | Numeric(10,4) | Default 1.0 | Quantity |
| `created_at` | DateTime(timezone) | Auto Now | |

---

### 1.5 `quote_tracking_events` Table (PLANIFICADO - Sprint 1)

**Ubicación:** `backend/app/models/quote_tracking.py` (a crear)

Event log for quote tracking.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | Integer | PK | |
| `quote_id` | Integer | FK, Not Null, Index | Reference to Quote |
| `event_type` | String | Not Null | `email_sent`, `email_opened`, `pdf_downloaded`, `link_clicked` |
| `ip_address` | String | Nullable | IP address (anonymized for GDPR) |
| `user_agent` | String | Nullable | Browser user agent |
| `device_type` | String | Nullable | `desktop`, `mobile`, `tablet` |
| `browser` | String | Nullable | Browser name |
| `location_country` | String | Nullable | Country code (if track_location enabled) |
| `location_city` | String | Nullable | City (if track_location enabled) |
| `email` | String | Nullable | Email address (if available) |
| `created_at` | DateTime(timezone) | Auto Now | Event timestamp |

**Nota:** Este modelo solo se crea si `Organization.settings["quote_tracking"]["enabled"] = True`. Los eventos no se registran si tracking está desactivado.

---

## 2. API Endpoints (FastAPI)

### 2.1 CRUD de Cotizaciones (✅ IMPLEMENTADO)

#### `POST /api/v1/projects/`

**Crear proyecto con cotización inicial.**

**Ubicación:** `backend/app/api/v1/endpoints/projects.py:138`

**Payload (`ProjectCreateWithQuote`):**
```json
{
  "name": "New Website",
  "client_name": "Acme Corp",
  "client_email": "contact@acme.com",
  "currency": "COP",
  "tax_ids": [1, 2],
  "quote_items": [
    {
      "service_id": 1,
      "estimated_hours": 40,
      "pricing_type": "hourly"
    }
  ],
  "target_margin_percentage": "0.40",
  "revisions_included": 2,
  "revision_cost_per_additional": "50000",
  "allow_low_margin": false
}
```

**Logic:**
1. Validate tenant context
2. Fetch current BCR (calculated dynamically)
3. Calculate costs & prices based on `quote_items`
4. Apply `target_margin_percentage` if provided
5. Validate profitability (unless `allow_low_margin = true`)
6. Save Project with status = "Draft"
7. Save Quote with version = 1
8. Save QuoteItems with calculated values
9. Return `QuoteResponseWithItems`

**Response:** `QuoteResponseWithItems` (includes calculated totals and items breakdown)

---

#### `PUT /api/v1/projects/{project_id}/quotes/{quote_id}`

**Actualizar cotización existente.**

**Ubicación:** `backend/app/api/v1/endpoints/projects.py:600`

**Payload (`QuoteUpdate`):**
```json
{
  "items": [
    {
      "service_id": 1,
      "estimated_hours": 50,
      "pricing_type": "hourly"
    }
  ],
  "notes": "Updated quote",
  "target_margin_percentage": "0.45",
  "allow_low_margin": false
}
```

**Logic:**
1. Verify quote belongs to project and tenant
2. Recalculate financials with new items
3. Validate profitability (unless `allow_low_margin = true`)
4. Update Quote and QuoteItems (cascade delete and recreate)
5. Return updated `QuoteResponseWithItems`

**Restrictions:**
- Can update if status is "Draft" or "Sent"
- If status is "Sent", consider creating new version instead

---

#### `POST /api/v1/projects/{project_id}/quotes/{quote_id}/new-version`

**Crear nueva versión de cotización.**

**Ubicación:** `backend/app/api/v1/endpoints/projects.py:777`

**Payload (`QuoteCreateNewVersion`):**
```json
{
  "items": [...],
  "notes": "Version 2 with updated pricing",
  "target_margin_percentage": "0.40",
  "allow_low_margin": false
}
```

**Logic:**
1. Find latest version of quote
2. Increment version number (v1 → v2)
3. Create new Quote with incremented version
4. Copy items with new values
5. Maintain same `project_id`
6. Return new `QuoteResponseWithItems`

**Response:** `QuoteResponseWithItems` with incremented `version`

---

#### `GET /api/v1/projects/{project_id}/quotes`

**Listar todas las versiones de cotizaciones de un proyecto.**

**Ubicación:** `backend/app/api/v1/endpoints/projects.py:400` (aproximadamente)

**Query Parameters:**
- `include_deleted`: boolean (default: false)

**Response:** List of `QuoteResponse` (without items, includes version number)

---

#### `GET /api/v1/projects/{project_id}/quotes/{quote_id}`

**Obtener cotización completa con items.**

**Ubicación:** `backend/app/api/v1/endpoints/projects.py:450` (aproximadamente)

**Response:** `QuoteResponseWithItems` (includes all items and expenses)

---

### 2.2 Cálculo en Tiempo Real (✅ IMPLEMENTADO)

#### `POST /api/v1/quotes/calculate`

**Calcular totales de cotización sin guardar (para preview en tiempo real).**

**Ubicación:** `backend/app/api/v1/endpoints/quotes.py:25`

**Payload (`QuoteCalculateRequest`):**
```json
{
  "items": [
    {
      "service_id": 1,
      "estimated_hours": 40,
      "pricing_type": "hourly"
    }
  ],
  "expenses": [
    {
      "name": "Stock Photos",
      "cost": "50000",
      "markup_percentage": "0.20",
      "quantity": "1.0",
      "category": "Third Party"
    }
  ],
  "tax_ids": [1, 2],
  "target_margin_percentage": "0.40",
  "revisions_included": 2,
  "revision_cost_per_additional": "50000",
  "revisions_count": 3
}
```

**Logic:**
1. Validate services exist
2. Calculate current BCR
3. Calculate internal costs and client prices for each item
4. Apply `target_margin_percentage` if provided
5. Calculate expenses with markup
6. Calculate taxes on `total_client_price`
7. Calculate additional revision costs
8. Return complete breakdown

**Response (`QuoteCalculateResponse`):**
```json
{
  "total_internal_cost": "2000000",
  "total_client_price": "2800000",
  "total_expenses_cost": "50000",
  "total_expenses_client_price": "60000",
  "total_taxes": "532000",
  "total_with_taxes": "3332000",
  "margin_percentage": "0.2857",
  "target_margin_percentage": "0.40",
  "items": [...],
  "expenses": [...],
  "taxes": [...],
  "revisions_cost": "50000",
  "revisions_included": 2,
  "revisions_count": 3
}
```

**Nota:** Este endpoint se usa para la "Calculadora Viva" en el frontend, permitiendo ver cálculos en tiempo real sin guardar.

---

### 2.3 Envío de Cotizaciones (✅ IMPLEMENTADO)

#### `POST /api/v1/projects/{project_id}/quotes/{quote_id}/send-email`

**Enviar cotización por email.**

**Ubicación:** `backend/app/api/v1/endpoints/projects.py:957`

**Payload (`QuoteEmailRequest`):**
```json
{
  "to_email": "client@example.com",
  "subject": "Propuesta Comercial - Proyecto XYZ",
  "message": "Estimado cliente, adjunto nuestra propuesta...",
  "cc": ["manager@example.com"],
  "bcc": [],
  "include_pdf": true,
  "include_docx": false
}
```

**Logic:**
1. Verify quote exists and belongs to tenant
2. Validate `client_email` is present (or use `to_email`)
3. Generate PDF/DOCX if requested
4. Generate HTML email with quote details
5. **PLANIFICADO (Sprint 1):** Insert tracking pixel if tracking enabled
6. **PLANIFICADO (Sprint 1):** Generate `tracking_token` if tracking enabled
7. **PLANIFICADO (Sprint 1):** Create unique PDF URL with token if tracking enabled
8. Send email via SMTP
9. Update Project status to "Sent"
10. **PLANIFICADO (Sprint 1):** Record `sent_at` timestamp
11. **PLANIFICADO (Sprint 1):** Create tracking event "email_sent"

**Response:** `QuoteEmailResponse` (success/failure)

---

#### `GET /api/v1/projects/{project_id}/quotes/{quote_id}/pdf`

**Descargar PDF de cotización.**

**Ubicación:** `backend/app/api/v1/endpoints/projects.py:812`

**Logic:**
1. Verify quote exists and belongs to tenant
2. Generate PDF using template
3. Return PDF as streaming response

**PLANIFICADO (Sprint 1):** Si tracking está activado, usar URL única con token para registrar descargas.

---

### 2.4 Transición de Estados (Pipeline Drag & Drop) (❌ NO IMPLEMENTADO - Sprint 2)

#### `PATCH /api/v1/quotes/{id}/status`

**Cambiar estado de cotización (soporta Drag & Drop del Pipeline).**

**Estado:** ❌ No implementado (Sprint 2)

**Ubicación Planificada:** `backend/app/api/v1/endpoints/quotes.py`

**Payload (`QuoteStatusUpdate`):**
```json
{
  "status": "Sent",
  "notes": "Optional notes about the status change"
}
```

**Estados Válidos:**
- `Draft`: Borrador (estado inicial)
- `Sent`: Enviada al cliente
- `Viewed`: Cliente abrió el email/PDF (detectado por tracking)
- `Accepted`: Cliente aceptó la cotización
- `Rejected`: Cliente rechazó la cotización
- `Expired`: Cotización expiró (30 días desde envío)
- `Won`: Proyecto ganado (marcado manualmente)
- `Lost`: Proyecto perdido (marcado manualmente)

**Logic (Planificada):**

1. **Validación de Transiciones (State Machine):**
   ```
   Transiciones Permitidas:
   - Draft → Sent ✅
   - Draft → Won ✅ (marcado manualmente como ganado sin enviar)
   - Draft → Lost ✅ (marcado manualmente como perdido sin enviar)
   - Sent → Viewed ✅ (automático por tracking, pero también puede ser manual)
   - Sent → Accepted ✅
   - Sent → Rejected ✅
   - Sent → Expired ✅ (automático por Celery Beat)
   - Viewed → Accepted ✅
   - Viewed → Rejected ✅
   - Viewed → Expired ✅ (automático por Celery Beat)
   - Accepted → Won ✅ (confirmación final)
   - Rejected → Lost ✅ (confirmación final)
   
   Transiciones NO Permitidas:
   - Sent → Draft ❌ (debe crear nueva versión v2)
   - Viewed → Draft ❌ (debe crear nueva versión v2)
   - Accepted → Draft ❌ (irreversible)
   - Rejected → Draft ❌ (irreversible)
   - Expired → Draft ❌ (debe crear nueva versión v2)
   - Won → Cualquier otro estado ❌ (estado final)
   - Lost → Cualquier otro estado ❌ (estado final)
   ```

2. **Lógica Específica por Transición:**

   **Draft → Sent:**
   - ✅ Validar que la cotización tiene al menos 1 item
   - ✅ Validar que `total_client_price >= total_internal_cost` (a menos que `allow_low_margin = true`)
   - ✅ **CRÍTICO:** Generar PDF inmutable y almacenarlo (snapshot)
   - ✅ **CRÍTICO:** Congelar costos internos (BCR snapshot) - ver sección 3.3.1
   - ✅ Generar `tracking_token` si tracking está habilitado
   - ✅ Establecer `sent_at = now()`
   - ✅ Establecer `expires_at = sent_at + 30 days`
   - ✅ Actualizar `Project.status = "Sent"`
   - ✅ Crear tracking event "email_sent" (si tracking habilitado)
   - ✅ Invalidar cache del dashboard

   **Sent → Viewed:**
   - ⚠️ Normalmente se hace automáticamente por tracking pixel
   - ✅ Si es manual, establecer `viewed_at = now()` (si es primera vez)
   - ✅ Incrementar `viewed_count`
   - ✅ Actualizar `last_viewed_at = now()`
   - ✅ Actualizar `Project.status = "Viewed"`

   **Sent/Viewed → Accepted:**
   - ✅ Establecer `accepted_at = now()`
   - ✅ Actualizar `Project.status = "Accepted"`
   - ✅ **OPCIONAL:** Disparar creación automática de Proyecto o Factura (configurable)
   - ✅ Invalidar cache del dashboard

   **Sent/Viewed → Rejected:**
   - ✅ Establecer `rejected_at = now()`
   - ✅ Actualizar `Project.status = "Rejected"`
   - ✅ Invalidar cache del dashboard

   **Sent/Viewed → Expired:**
   - ⚠️ Normalmente se hace automáticamente por Celery Beat task
   - ✅ Si es manual, establecer `expires_at = now()`
   - ✅ Actualizar `Project.status = "Expired"`
   - ✅ Invalidar cache del dashboard

   **Accepted → Won:**
   - ✅ Actualizar `Project.status = "Won"`
   - ✅ Marcar proyecto como ganado
   - ✅ Invalidar cache del dashboard

   **Rejected → Lost:**
   - ✅ Actualizar `Project.status = "Lost"`
   - ✅ Marcar proyecto como perdido
   - ✅ Invalidar cache del dashboard

3. **Validaciones de Negocio:**
   - Verificar que el usuario tiene permisos para cambiar estado
   - Verificar que la cotización pertenece a la organización del tenant
   - Validar que la transición es permitida según la máquina de estados
   - Si la transición no es permitida, retornar HTTP 409 Conflict con mensaje descriptivo

4. **Snapshots de Costos (CRÍTICO):**
   - Al mover a "Sent", se debe guardar snapshot de todos los costos:
     - `QuoteItem.unit_cost_snapshot` (BCR congelado por item)
     - `QuoteItem.internal_cost_snapshot` (costo interno total del item)
     - `Quote.total_internal_cost` (ya está congelado, pero se valida)
   - Estos snapshots **NUNCA** cambian, incluso si el BCR de la agencia sube
   - Ver sección 3.3.1 para detalles técnicos

**Response (`QuoteStatusResponse`):**
```json
{
  "id": 123,
  "status": "Sent",
  "previous_status": "Draft",
  "sent_at": "2026-01-25T10:00:00Z",
  "expires_at": "2026-02-24T10:00:00Z",
  "tracking_token": "abc123...",
  "project_status": "Sent",
  "message": "Quote status updated successfully. PDF generated and costs frozen."
}
```

**Errores Posibles:**
- `HTTP 400 Bad Request`: Estado inválido o transición no permitida
- `HTTP 403 Forbidden`: Usuario no tiene permisos
- `HTTP 404 Not Found`: Cotización no existe
- `HTTP 409 Conflict`: Transición no permitida (ej: Sent → Draft)
- `HTTP 422 Unprocessable Entity`: Validaciones de negocio fallidas (ej: sin items, margen negativo)

**Nota:** Este endpoint es crítico para el funcionamiento del Pipeline Drag & Drop. Debe implementarse con validaciones exhaustivas y logging detallado de todas las transiciones.

---

### 2.5 Tracking de Cotizaciones (❌ NO IMPLEMENTADO - Sprint 1)

#### `GET /api/v1/tracking/pixel/{quote_id}/{tracking_token}`

**Pixel de seguimiento para emails (1x1px transparente).**

**Estado:** ❌ No implementado

**Logic (Planificada):**
1. Validate `tracking_token` matches quote
2. Check if tracking is enabled for organization and quote
3. If enabled:
   - Record event "email_opened"
   - Update `Quote.viewed_at`, `Quote.viewed_count`, `Quote.last_viewed_at`
   - Update Project status to "Viewed" if first time
   - Extract IP, user-agent, device info (if configured)
4. Return 1x1px transparent PNG

**Response:** PNG image (1x1px transparent)

---

#### `GET /api/v1/tracking/pdf/{quote_id}/{tracking_token}`

**URL única para descarga de PDF con tracking.**

**Estado:** ❌ No implementado

**Logic (Planificada):**
1. Validate `tracking_token` matches quote
2. Check if tracking is enabled
3. If enabled:
   - Record event "pdf_downloaded"
   - Update `Quote.downloaded_count`, `Quote.last_downloaded_at`
4. Redirect to actual PDF download endpoint

**Response:** Redirect to PDF download

---

#### `GET /api/v1/projects/{project_id}/quotes/{quote_id}/tracking`

**Obtener eventos de tracking de una cotización.**

**Estado:** ❌ No implementado

**Response:**
```json
{
  "quote_id": 123,
  "sent_at": "2026-01-15T10:00:00Z",
  "viewed_at": "2026-01-15T14:30:00Z",
  "viewed_count": 5,
  "last_viewed_at": "2026-01-20T09:15:00Z",
  "downloaded_count": 2,
  "last_downloaded_at": "2026-01-18T16:45:00Z",
  "events": [
    {
      "event_type": "email_opened",
      "created_at": "2026-01-15T14:30:00Z",
      "device_type": "desktop",
      "browser": "Chrome",
      "location_country": "CO"
    }
  ]
}
```

---

### 2.6 Analytics & Reporting (❌ NO IMPLEMENTADO - Sprint 3)

#### `GET /api/v1/analytics/dashboard`

**Dashboard de Analytics con cálculos optimizados en SQL.**

**Estado:** ❌ No implementado (Sprint 3)

**Ubicación Planificada:** `backend/app/api/v1/endpoints/analytics.py` (nuevo archivo)

**Query Parameters:**
- `start_date`: ISO 8601 date (optional, filter by quote creation date)
- `end_date`: ISO 8601 date (optional, filter by quote creation date)
- `currency`: string (optional, filter by currency: USD, COP, EUR, ARS)
- `status`: string (optional, filter by quote status: Draft, Sent, Viewed, Accepted, Rejected, Expired, Won, Lost)
- `client_name`: string (optional, partial match search)
- `group_by`: string (optional, `month`, `week`, `day`, `client`, `service`)

**Response (`AnalyticsDashboardResponse`):**
```json
{
  "summary": {
    "total_quotes": 150,
    "total_revenue": "45000000",
    "total_internal_costs": "31500000",
    "net_profit": "13500000",
    "average_margin_percentage": "0.30",
    "pipeline_value": "25000000",
    "win_rate": "0.45",
    "average_quote_value": "300000"
  },
  "by_status": {
    "Draft": 20,
    "Sent": 45,
    "Viewed": 30,
    "Accepted": 15,
    "Rejected": 10,
    "Won": 20,
    "Lost": 10
  },
  "by_currency": {
    "COP": {
      "count": 100,
      "revenue": "30000000",
      "costs": "21000000",
      "profit": "9000000"
    },
    "USD": {
      "count": 50,
      "revenue": "15000000",
      "costs": "10500000",
      "profit": "4500000"
    }
  },
  "trends": [
    {
      "period": "2026-01",
      "quotes_count": 25,
      "revenue": "7500000",
      "costs": "5250000",
      "profit": "2250000"
    }
  ],
  "top_clients": [
    {
      "client_name": "Acme Corp",
      "quotes_count": 10,
      "total_revenue": "5000000",
      "win_rate": "0.60"
    }
  ],
  "top_services": [
    {
      "service_name": "Web Development",
      "quotes_count": 45,
      "total_revenue": "15000000",
      "average_margin": "0.35"
    }
  ]
}
```

**CRÍTICO - Eficiencia SQL:**

**❌ INCORRECTO (Carga todo en memoria):**
```python
# NUNCA hacer esto - carga todos los registros en memoria
quotes = await db.execute(select(Quote).join(Project))
all_quotes = quotes.scalars().all()
total_revenue = sum(q.total_client_price for q in all_quotes)  # ❌ Lento con 1000+ quotes
```

**✅ CORRECTO (Cálculos en SQL):**
```python
# Calcular directamente en SQL usando agregaciones
revenue_query = select(
    func.sum(Quote.total_client_price).label("total_revenue"),
    func.sum(Quote.total_internal_cost).label("total_costs"),
    func.sum(Quote.total_client_price - Quote.total_internal_cost).label("net_profit"),
    func.avg(Quote.margin_percentage).label("avg_margin"),
    func.count(Quote.id).label("total_quotes")
).join(Project, Quote.project_id == Project.id).where(
    Project.organization_id == tenant.organization_id,
    Project.deleted_at.is_(None)
)

# Aplicar filtros si existen
if start_date:
    revenue_query = revenue_query.where(Quote.created_at >= start_date)
if end_date:
    revenue_query = revenue_query.where(Quote.created_at <= end_date)
if currency:
    revenue_query = revenue_query.where(Project.currency == currency)
if status:
    revenue_query = revenue_query.where(Project.status == status)

result = await db.execute(revenue_query)
row = result.first()
# Retorna directamente los valores agregados sin cargar registros individuales
```

**Ejemplo de Query Optimizada para Utilidad Neta:**

```sql
-- Query SQL equivalente (PostgreSQL)
SELECT 
    COUNT(q.id) AS total_quotes,
    COALESCE(SUM(q.total_client_price), 0) AS total_revenue,
    COALESCE(SUM(q.total_internal_cost), 0) AS total_internal_costs,
    COALESCE(SUM(q.total_client_price - q.total_internal_cost), 0) AS net_profit,
    COALESCE(AVG(q.margin_percentage), 0) AS average_margin_percentage,
    COALESCE(SUM(CASE WHEN p.status IN ('Sent', 'Viewed') THEN q.total_client_price ELSE 0 END), 0) AS pipeline_value,
    COUNT(CASE WHEN p.status = 'Won' THEN 1 END)::FLOAT / NULLIF(COUNT(CASE WHEN p.status IN ('Sent', 'Viewed', 'Accepted', 'Won', 'Lost') THEN 1 END), 0) AS win_rate
FROM quotes q
INNER JOIN projects p ON q.project_id = p.id
WHERE p.organization_id = :organization_id
  AND p.deleted_at IS NULL
  AND (:start_date IS NULL OR q.created_at >= :start_date)
  AND (:end_date IS NULL OR q.created_at <= :end_date)
  AND (:currency IS NULL OR p.currency = :currency)
  AND (:status IS NULL OR p.status = :status);
```

**Agregaciones por Período (Trends):**

```python
# Agregar por mes usando funciones de fecha de PostgreSQL
trends_query = select(
    func.date_trunc('month', Quote.created_at).label("period"),
    func.count(Quote.id).label("quotes_count"),
    func.sum(Quote.total_client_price).label("revenue"),
    func.sum(Quote.total_internal_cost).label("costs"),
    func.sum(Quote.total_client_price - Quote.total_internal_cost).label("profit")
).join(Project, Quote.project_id == Project.id).where(
    Project.organization_id == tenant.organization_id,
    Project.deleted_at.is_(None)
).group_by(
    func.date_trunc('month', Quote.created_at)
).order_by(
    func.date_trunc('month', Quote.created_at).desc()
).limit(12)  # Últimos 12 meses
```

**Agregaciones por Cliente (Top Clients):**

```python
# Top 10 clientes por revenue
top_clients_query = select(
    Project.client_name,
    func.count(Quote.id).label("quotes_count"),
    func.sum(Quote.total_client_price).label("total_revenue"),
    func.count(CASE(Project.status == "Won", 1)).label("won_count"),
    func.count(CASE(Project.status.in_(["Sent", "Viewed", "Accepted", "Won", "Lost"]), 1)).label("total_sent")
).join(Project, Quote.project_id == Project.id).where(
    Project.organization_id == tenant.organization_id,
    Project.deleted_at.is_(None)
).group_by(
    Project.client_name
).order_by(
    func.sum(Quote.total_client_price).desc()
).limit(10)
```

**Agregaciones por Servicio (Top Services):**

```python
# Top servicios por revenue
top_services_query = select(
    Service.name.label("service_name"),
    func.count(QuoteItem.id).label("quotes_count"),
    func.sum(QuoteItem.client_price).label("total_revenue"),
    func.avg(QuoteItem.margin_percentage).label("average_margin")
).join(Quote, QuoteItem.quote_id == Quote.id).join(
    Project, Quote.project_id == Project.id
).join(
    Service, QuoteItem.service_id == Service.id
).where(
    Project.organization_id == tenant.organization_id,
    Project.deleted_at.is_(None)
).group_by(
    Service.name
).order_by(
    func.sum(QuoteItem.client_price).desc()
).limit(10)
```

**Índices Requeridos para Performance:**

```sql
-- Índices críticos para queries de analytics
CREATE INDEX idx_quotes_project_id ON quotes(project_id);
CREATE INDEX idx_quotes_created_at ON quotes(created_at);
CREATE INDEX idx_projects_organization_status ON projects(organization_id, status) WHERE deleted_at IS NULL;
CREATE INDEX idx_projects_currency ON projects(currency) WHERE deleted_at IS NULL;
CREATE INDEX idx_quote_items_quote_id ON quote_items(quote_id);
CREATE INDEX idx_quote_items_service_id ON quote_items(service_id);

-- Índice compuesto para filtros comunes
CREATE INDEX idx_quotes_analytics ON quotes(project_id, created_at) 
INCLUDE (total_client_price, total_internal_cost, margin_percentage);
```

**Consideraciones de Performance:**

1. **Siempre usar agregaciones SQL:**
   - `func.sum()`, `func.avg()`, `func.count()` en lugar de sumar en Python
   - `func.date_trunc()` para agrupar por período
   - `CASE WHEN` para cálculos condicionales

2. **Limitar resultados:**
   - Usar `.limit()` para top N (ej: top 10 clientes)
   - Paginar resultados grandes
   - No retornar más de 1000 registros en una respuesta

3. **Cache:**
   - Cachear resultados por 2-5 minutos (dependiendo de frecuencia de actualización)
   - Invalidar cache al crear/actualizar cotizaciones
   - Usar cache key que incluya todos los filtros

4. **Uso de Snapshots:**
   - Para cotizaciones enviadas (`status != 'Draft'`), usar valores snapshot si existen
   - Para cotizaciones en Draft, usar valores actuales
   - Query condicional: `COALESCE(quote_item.internal_cost_snapshot, quote_item.internal_cost)`

**Ejemplo de Query con Snapshots:**

```python
# Calcular costs usando snapshots si existen
costs_query = select(
    func.sum(
        func.coalesce(
            QuoteItem.internal_cost_snapshot,
            QuoteItem.internal_cost
        )
    ).label("total_costs")
).join(Quote, QuoteItem.quote_id == Quote.id).join(
    Project, Quote.project_id == Project.id
).where(
    Project.organization_id == tenant.organization_id,
    Project.deleted_at.is_(None)
)
```

**Response Time Targets:**
- Dashboard completo: < 500ms con 1000 cotizaciones
- Dashboard con filtros: < 800ms
- Trends (12 meses): < 300ms
- Top clients/services: < 200ms

**Nota:** Este endpoint debe ser extremadamente eficiente ya que se llama frecuentemente desde el dashboard del frontend. Todos los cálculos deben hacerse en SQL, nunca cargar registros individuales en memoria.

---

### 2.7 Métricas y Dashboard (⚠️ PARCIALMENTE IMPLEMENTADO)

#### `GET /api/v1/insights/dashboard`

**Obtener métricas del dashboard comercial.**

**Ubicación:** `backend/app/api/v1/endpoints/insights.py:23`

**Query Parameters:**
- `start_date`: ISO 8601 date (optional)
- `end_date`: ISO 8601 date (optional)
- `currency`: string (optional, filter by currency)
- `status`: string (optional, filter by status)
- `client_name`: string (optional, search by client name)

**Response Actual (✅ Implementado):**
```json
{
  "total_projects": 50,
  "total_revenue": "50000000",
  "average_margin": "0.35",
  "conversion_rate": "0.60",
  "projects_by_status": {
    "Draft": 10,
    "Sent": 20,
    "Won": 15,
    "Lost": 5
  },
  "projects_by_client": [...],
  "revenue_by_service": [...]
}
```

**Métricas Planificadas (Sprint 3 - ❌ No implementadas):**
- `pipeline_value`: Total de cotizaciones en pipeline (Sent + Viewed)
- `win_rate`: Tasa de aceptación específica de cotizaciones
- `attention_required`: Cotizaciones que requieren seguimiento (Viewed pero no Accepted después de X días)
- `interest_analysis`: Análisis de interés basado en tracking (múltiples aperturas, descargas)

---

### 2.6 Gestión de Versiones (⚠️ PARCIALMENTE IMPLEMENTADO)

#### `GET /api/v1/projects/{project_id}/quotes/{quote_id}/compare?compare_with={other_quote_id}`

**Comparar dos versiones de cotización lado a lado.**

**Estado:** ❌ No implementado

**Response Planificada:**
```json
{
  "base_quote": {...},
  "compare_quote": {...},
  "differences": [
    {
      "field": "total_client_price",
      "base_value": "2800000",
      "compare_value": "3000000",
      "change_type": "modified"
    },
    {
      "field": "items[0].estimated_hours",
      "base_value": 40,
      "compare_value": 50,
      "change_type": "modified"
    }
  ]
}
```

---

## 3. Business Logic & State Management

### 3.1 Estados de Cotización y Máquina de Estados

**Estados Actuales (✅ Implementados):**
- `Draft`: Borrador, no enviado
- `Sent`: Enviada al cliente
- `Won`: Cliente aceptó (marcado manualmente)
- `Lost`: Cliente rechazó (marcado manualmente)

**Estados Planificados (❌ No implementados - Sprint 2):**
- `Viewed`: Cliente abrió el email/PDF (detectado por tracking pixel)
- `Accepted`: Cliente aceptó la cotización (marcado manualmente)
- `Rejected`: Cliente rechazó la cotización (marcado manualmente)
- `Expired`: Cotización expiró (30 días desde envío, marcado automáticamente)

**Máquina de Estados Completa:**

```
                    ┌─────────┐
                    │  Draft  │ (Estado inicial)
                    └────┬────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
         ▼               ▼               ▼
    ┌────────┐     ┌────────┐     ┌────────┐
    │  Sent  │     │  Won   │     │  Lost  │
    └────┬───┘     └────────┘     └────────┘
         │           (Final)        (Final)
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌────────┐ ┌──────────┐
│ Viewed │ │ Expired  │
└────┬───┘ └──────────┘
     │         (Final)
     │
┌────┴────┐
│         │
▼         ▼
┌──────────┐ ┌──────────┐
│ Accepted │ │ Rejected │
└────┬─────┘ └────┬──────┘
     │            │
     ▼            ▼
  ┌──────┐    ┌──────┐
  │ Won  │    │ Lost │
  └──────┘    └──────┘
  (Final)     (Final)
```

**Transiciones Permitidas:**

| Desde | Hacia | Tipo | Descripción |
| :--- | :--- | :--- | :--- |
| `Draft` | `Sent` | Manual | Enviar cotización al cliente |
| `Draft` | `Won` | Manual | Marcar como ganado sin enviar |
| `Draft` | `Lost` | Manual | Marcar como perdido sin enviar |
| `Sent` | `Viewed` | Automático/Manual | Cliente abrió email (tracking pixel) |
| `Sent` | `Accepted` | Manual | Cliente aceptó |
| `Sent` | `Rejected` | Manual | Cliente rechazó |
| `Sent` | `Expired` | Automático | 30 días desde envío (Celery Beat) |
| `Viewed` | `Accepted` | Manual | Cliente aceptó después de ver |
| `Viewed` | `Rejected` | Manual | Cliente rechazó después de ver |
| `Viewed` | `Expired` | Automático | 30 días desde envío (Celery Beat) |
| `Accepted` | `Won` | Manual | Confirmación final de proyecto ganado |
| `Rejected` | `Lost` | Manual | Confirmación final de proyecto perdido |

**Transiciones NO Permitidas (Retornan HTTP 409 Conflict):**

| Desde | Hacia | Razón |
| :--- | :--- | :--- |
| `Sent` | `Draft` | Debe crear nueva versión v2 |
| `Viewed` | `Draft` | Debe crear nueva versión v2 |
| `Accepted` | `Draft` | Estado irreversible |
| `Rejected` | `Draft` | Estado irreversible |
| `Expired` | `Draft` | Debe crear nueva versión v2 |
| `Won` | Cualquier otro | Estado final |
| `Lost` | Cualquier otro | Estado final |

**Lógica de Transición:**
- `Draft → Sent`: Al enviar email o mover manualmente en Pipeline
  - **CRÍTICO:** Genera PDF inmutable y congela costos (BCR snapshot)
- `Sent → Viewed`: Al detectar apertura de email (tracking pixel) o manualmente
- `Viewed → Accepted`: Marcado manualmente por usuario
- `Viewed → Rejected`: Marcado manualmente por usuario
- `Sent/Viewed → Expired`: Automáticamente después de 30 días (Celery Beat task)
- `Accepted → Won`: Confirmación final de proyecto ganado
- `Rejected → Lost`: Confirmación final de proyecto perdido

**Validaciones por Transición:**

**Draft → Sent:**
- ✅ Debe tener al menos 1 `QuoteItem`
- ✅ Debe tener `total_client_price >= total_internal_cost` (a menos que `allow_low_margin = true`)
- ✅ Debe tener `client_email` o `Project.client_email` configurado
- ✅ Genera PDF inmutable (snapshot)
- ✅ Congela costos internos (BCR snapshot)

**Sent → Viewed:**
- ✅ Puede ser automático (tracking pixel) o manual
- ✅ Si es primera vez, establece `viewed_at`
- ✅ Incrementa `viewed_count`

**Sent/Viewed → Accepted:**
- ✅ Establece `accepted_at`
- ✅ **OPCIONAL:** Puede disparar creación automática de Proyecto o Factura (configurable en `Organization.settings`)

**Sent/Viewed → Rejected:**
- ✅ Establece `rejected_at`
- ✅ No requiere confirmación adicional

**Sent/Viewed → Expired:**
- ✅ Normalmente automático (Celery Beat)
- ✅ Puede ser manual para testing
- ✅ Establece `expires_at` si no estaba configurado

---

### 3.2 Versioning (Snapshots)

**✅ IMPLEMENTADO:** Sistema básico de versiones

**Lógica Actual:**
- Cada cotización tiene campo `version` (default: 1)
- Al crear nueva versión, se incrementa `version` y se crea nuevo registro `Quote`
- Todas las versiones comparten el mismo `project_id`
- Las versiones anteriores se mantienen para historial

**Mejoras Planificadas (Sprint 5):**
- Endpoint de comparación de versiones
- Historial completo de cambios
- Visualización lado a lado

**Nota:** No se sobrescriben cotizaciones una vez enviadas. Si el usuario edita una cotización "Sent", se recomienda crear nueva versión.

---

### 3.3 BCR Locking (Costo Interno Congelado) y Snapshots

**✅ IMPLEMENTADO:** Los costos internos se calculan y almacenan al crear la cotización

**⚠️ MEJORA REQUERIDA:** Los snapshots de costos por item deben congelarse al mover a "Sent" (Sprint 2)

#### 3.3.1 Lógica Actual (Al Crear Cotización)

**✅ IMPLEMENTADO:**
- Al crear cotización, se calcula `total_internal_cost` usando el BCR actual
- Este valor se almacena en `Quote.total_internal_cost`
- Cambios futuros al BCR de la agencia **NO afectan** cotizaciones existentes
- Solo nuevas cotizaciones usan el nuevo BCR

**Ejemplo:**
```
Cotización creada en Enero:
- BCR actual: $50,000 COP/hora
- Horas: 40
- total_internal_cost almacenado: $2,000,000 COP

Si en Febrero el BCR sube a $55,000 COP/hora:
- Cotización de Enero sigue mostrando $2,000,000 COP (congelado)
- Nueva cotización en Febrero usa $55,000 COP/hora
```

#### 3.3.2 Snapshots de Costos al Mover a "Sent" (❌ NO IMPLEMENTADO - Sprint 2)

**CRÍTICO:** Cuando una cotización se mueve de `Draft` a `Sent`, se deben congelar TODOS los costos a nivel de item para garantizar inmutabilidad.

**Campos Adicionales Requeridos en `QuoteItem`:**

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `unit_cost_snapshot` | Numeric(19,4) | Nullable | BCR congelado por hora al momento de enviar (ESTÁNDAR NOUGRAM) |
| `internal_cost_snapshot` | Numeric(19,4) | Nullable | Costo interno total del item congelado (ESTÁNDAR NOUGRAM) |
| `client_price_snapshot` | Numeric(19,4) | Nullable | Precio cliente del item congelado (ESTÁNDAR NOUGRAM) |
| `snapshot_date` | DateTime(timezone) | Nullable | Fecha en que se congelaron los costos |

**Lógica de Congelamiento (Al mover Draft → Sent):**

1. **Calcular BCR actual** (si no está calculado)
2. **Para cada `QuoteItem`:**
   ```python
   # Si pricing_type = "hourly"
   unit_cost_snapshot = current_bcr  # BCR del momento
   internal_cost_snapshot = estimated_hours * unit_cost_snapshot
   client_price_snapshot = current_client_price  # Precio actual
   
   # Si pricing_type = "fixed"
   unit_cost_snapshot = fixed_price  # Precio fijo
   internal_cost_snapshot = fixed_price * quantity
   client_price_snapshot = current_client_price
   
   # Guardar snapshots
   quote_item.unit_cost_snapshot = unit_cost_snapshot
   quote_item.internal_cost_snapshot = internal_cost_snapshot
   quote_item.client_price_snapshot = client_price_snapshot
   quote_item.snapshot_date = now()
   ```

3. **Validar que `Quote.total_internal_cost` coincide con la suma de snapshots:**
   ```python
   total_from_snapshots = sum(item.internal_cost_snapshot for item in quote.items)
   assert abs(total_from_snapshots - quote.total_internal_cost) < 0.01  # Tolerancia de centavos
   ```

4. **Generar PDF inmutable** usando los valores snapshot (no los valores actuales)

**Ejemplo Completo:**

```
Cotización creada en Enero (Draft):
- BCR actual: $50,000 COP/hora
- Item 1: 40 horas × $50,000 = $2,000,000 COP
- Item 2: 20 horas × $50,000 = $1,000,000 COP
- total_internal_cost: $3,000,000 COP
- total_client_price: $4,200,000 COP

Usuario mueve a "Sent" en Enero:
- Se calculan snapshots:
  - Item 1: unit_cost_snapshot = $50,000, internal_cost_snapshot = $2,000,000
  - Item 2: unit_cost_snapshot = $50,000, internal_cost_snapshot = $1,000,000
  - snapshot_date = 2026-01-25

Si en Febrero el BCR sube a $55,000 COP/hora:
- Cotización sigue mostrando:
  - Item 1: $2,000,000 COP (usando snapshot)
  - Item 2: $1,000,000 COP (usando snapshot)
  - total_internal_cost: $3,000,000 COP (congelado)
- PDF generado usa valores snapshot
- Nueva cotización en Febrero usa $55,000 COP/hora
```

**Uso de Snapshots:**

1. **Visualización en Dashboard:**
   - Si `snapshot_date` existe, mostrar valores snapshot
   - Si no existe, mostrar valores actuales (cotizaciones en Draft)

2. **Generación de PDF:**
   - Siempre usar valores snapshot si existen
   - Si no existen, usar valores actuales (para cotizaciones Draft)

3. **Cálculos de Rentabilidad:**
   - Usar valores snapshot para cotizaciones enviadas
   - Usar valores actuales para cotizaciones en Draft

**Migración de Datos Existentes:**

- Cotizaciones existentes con `status = "Sent"` deben migrarse:
  - Calcular snapshots retroactivamente usando `created_at` como `snapshot_date`
  - Si no se puede calcular BCR histórico, usar BCR actual como aproximación

**Nota:** Este mecanismo asegura que las cotizaciones enviadas mantengan su rentabilidad calculada, independientemente de cambios en costos operacionales. Es crítico para la integridad financiera del sistema.

---

### 3.4 Prevención de Regresión (Sent → Draft)

**❌ NO IMPLEMENTADO - Sprint 2**

**Problema:** Si un usuario intenta mover una cotización de `Sent` a `Draft`, esto podría permitir modificar costos que ya fueron enviados al cliente.

**Solución:**
- **Opción 1 (Recomendada):** Bloquear transición `Sent → Draft`
  - Retornar HTTP 409 Conflict
  - Mensaje: "No se puede revertir una cotización enviada. Crea una nueva versión (v2) para hacer cambios."

- **Opción 2:** Permitir transición pero mantener snapshots
  - Si se permite `Sent → Draft`, los snapshots deben mantenerse
  - Los valores snapshot siguen siendo los que se muestran en PDFs
  - Los valores actuales solo se usan para edición

**Implementación Recomendada:**
```python
# En el endpoint PATCH /api/v1/quotes/{id}/status
if current_status == "Sent" and new_status == "Draft":
    raise HTTPException(
        status_code=409,
        detail="Cannot revert sent quote to draft. Create a new version (v2) instead."
    )
```

---

### 3.5 Cálculo de Rentabilidad

**✅ IMPLEMENTADO:** Validación de rentabilidad con `allow_low_margin`

**Lógica:**
- Al crear/actualizar cotización, se valida que `total_client_price >= total_internal_cost`
- Si `total_client_price < total_internal_cost` y `allow_low_margin = false`:
  - Lanza `BusinessLogicError` con mensaje detallado
  - Calcula precio requerido para alcanzar margen mínimo
- Si `allow_low_margin = true`:
  - Permite guardar pero registra warning en logs
  - Usuario debe confirmar explícitamente

**Umbral Mínimo:**
- Se obtiene de `Organization.settings.minimum_margin_threshold`
- Default: 15% si no está configurado
- Configurable por organización

---

### 3.6 Feature Flag de Tracking (❌ NO IMPLEMENTADO - Sprint 1)

**Configuración en `Organization.settings`:**
```json
{
  "quote_tracking": {
    "enabled": true,
    "track_email_opens": true,
    "track_pdf_downloads": true,
    "track_location": false,
    "track_device_info": true,
    "notify_on_events": true
  }
}
```

**Comportamiento cuando Desactivado:**
- Email se envía normalmente (sin pixel de tracking)
- PDF usa URL normal (sin token)
- No se registran eventos de tracking
- Dashboard funciona normalmente (métricas básicas)
- Métricas avanzadas muestran valores por defecto

**Endpoint de Configuración:**
- `PUT /api/v1/organizations/{organization_id}/quote-tracking-config`
- `GET /api/v1/organizations/{organization_id}/quote-tracking-config`

---

## 4. Plan de Trabajo - Features Pendientes

### Sprint 1: Sistema de Tracking Core + Feature Flag (❌ NO IMPLEMENTADO)

**Duración:** 2 semanas  
**Prioridad:** CRÍTICA

**Tareas:**
1. **Tarea 1.0:** Configuración de Feature Flag de Tracking
   - Agregar `quote_tracking` config a `Organization.settings`
   - Crear `QuoteTrackingConfig` schema
   - Endpoint para gestionar configuración

2. **Tarea 1.1:** Modelo `QuoteTrackingEvent`
   - Crear modelo con campos de tracking
   - Migración de base de datos
   - Repository para eventos

3. **Tarea 1.2:** Campos de tracking en `Quote`
   - Agregar `tracking_token`, `tracking_enabled`
   - Agregar campos de timestamps (`sent_at`, `viewed_at`, etc.)
   - Migración de base de datos

4. **Tarea 1.3:** Generación de `tracking_token`
   - Generar token único al enviar cotización
   - Validación de token en endpoints de tracking

5. **Tarea 1.4:** Pixel de seguimiento
   - Endpoint `GET /api/v1/tracking/pixel/{quote_id}/{token}`
   - Lógica condicional basada en feature flag
   - Registro de eventos "email_opened"

6. **Tarea 1.5:** URLs únicas para PDFs
   - Endpoint `GET /api/v1/tracking/pdf/{quote_id}/{token}`
   - Generar URL única al enviar email
   - Registro de eventos "pdf_downloaded"

7. **Tarea 1.6:** Integración con envío de emails
   - Modificar `generate_quote_email_html()` para incluir pixel condicional
   - Generar URL única para PDF si tracking activado
   - Actualizar `sent_at` timestamp

8. **Tarea 1.7:** Endpoint de eventos de tracking
   - `GET /api/v1/projects/{project_id}/quotes/{quote_id}/tracking`
   - Retornar resumen de eventos y estadísticas

**Estimación:** 92 horas (~13 días)

---

### Sprint 2: Estados Extendidos y Transiciones (❌ NO IMPLEMENTADO)

**Duración:** 1.5 semanas  
**Prioridad:** ALTA

**Tareas:**
1. Agregar estados: `Viewed`, `Accepted`, `Rejected`, `Expired`
2. Lógica de transición automática (`Sent → Viewed` cuando se detecta apertura)
3. Tarea Celery Beat para marcar cotizaciones expiradas (30 días)
4. Endpoints para marcar manualmente `Accepted`/`Rejected`
5. Validaciones de transición (no permitir transiciones inválidas)

**Estimación:** 60 horas (~8 días)

---

### Sprint 3: Métricas Avanzadas y Dashboard (⚠️ PARCIALMENTE IMPLEMENTADO)

**Duración:** 1.5 semanas  
**Prioridad:** ALTA

**Tareas:**
1. Pipeline Value (Sent + Viewed)
2. Win Rate específico de cotizaciones
3. Cotizaciones que requieren atención
4. Análisis de interés basado en tracking
5. Filtros avanzados por rentabilidad y monto
6. Búsqueda inteligente

**Estimación:** 60 horas (~8 días)

---

### Sprint 4: Filtros Avanzados y Búsqueda (⚠️ PARCIALMENTE IMPLEMENTADO)

**Duración:** 1 semana  
**Prioridad:** MEDIA

**Tareas:**
1. Filtros por rango de monto
2. Filtros por nivel de rentabilidad
3. Filtros por múltiples estados
4. Búsqueda inteligente (cliente, proyecto, servicios)
5. Ordenamiento avanzado

**Estimación:** 40 horas (~5 días)

---

### Sprint 5: Gestión de Versiones Avanzada (⚠️ PARCIALMENTE IMPLEMENTADO)

**Duración:** 1 semana  
**Prioridad:** MEDIA

**Tareas:**
1. Endpoint de comparación de versiones
2. Historial de cambios entre versiones
3. Visualización lado a lado
4. Duplicación inteligente (copiar items de versión anterior)

**Estimación:** 40 horas (~5 días)

---

## 5. Integraciones con Otros Módulos

### 5.1 Integración con BCR

**✅ IMPLEMENTADO:**
- El BCR se calcula automáticamente antes de crear/calcular cotizaciones
- Los costos internos se basan en el BCR actual
- Los costos se "congelan" al guardar la cotización

**Cache:**
- El BCR se cachea por organización y moneda
- Se invalida automáticamente al cambiar costos fijos, equipo o miembros del equipo

---

### 5.2 Integración con Sistema de Créditos

**✅ IMPLEMENTADO:**
- Al crear proyecto con cotización, se consume 1 crédito de IA (si usuario es `product_manager`)
- Validación de créditos antes de consumir
- Error HTTP 402 si créditos insuficientes

---

### 5.3 Integración con Dashboard

**✅ IMPLEMENTADO:**
- Al crear/actualizar cotización, se invalida cache del dashboard
- Métricas se actualizan automáticamente
- Cotizaciones aparecen en pipeline con estado actual

---

## 6. Consideraciones Técnicas

### 6.1 Precisión Monetaria (ESTÁNDAR NOUGRAM)

**✅ IMPLEMENTADO:**
- Todos los valores monetarios usan `Decimal` en el backend
- Se serializan como `string` en las respuestas JSON
- Frontend debe usar librerías de precisión decimal (`decimal.js`)
- Nunca usar `float` o `number` de JavaScript para cálculos monetarios

**Campos Monetarios:**
- `total_internal_cost`: `Numeric(19,4)`
- `total_client_price`: `Numeric(19,4)`
- `margin_percentage`: `Numeric(10,4)`
- `internal_cost` (en QuoteItem): `Numeric(19,4)`
- `client_price` (en QuoteItem): `Numeric(19,4)`

---

### 6.2 Manejo de Monedas

**✅ IMPLEMENTADO:**
- Soporte para múltiples monedas (USD, COP, EUR, ARS)
- Normalización a moneda principal para cálculos
- Conversión automática usando tasas de cambio
- Moneda se almacena en `Project.currency`

---

### 6.3 Performance

**✅ IMPLEMENTADO:**
- Cache de BCR para evitar recálculos innecesarios
- Paginación en listados de cotizaciones
- Índices en campos frecuentemente consultados (`project_id`, `organization_id`, `status`)

**Planificado:**
- Cache de métricas del dashboard
- Optimización de queries con `selectinload` para relaciones
- Índices adicionales para tracking (`tracking_token`, `sent_at`, `viewed_at`)

---

### 6.4 Seguridad y Privacidad

**✅ IMPLEMENTADO:**
- Tenant isolation (solo ve cotizaciones de su organización)
- Permisos basados en roles
- Soft delete (no elimina físicamente)

**Planificado (Sprint 1):**
- Anonimización de IPs para GDPR
- Opción de desactivar tracking completamente
- Información clara sobre qué datos se recopilan
- Exportación/eliminación de datos de tracking

---

## 7. Referencias y Documentación

### Documentos Relacionados

- **Plan de Trabajo Completo:** `PLAN_TRABAJO_QUOTES_DASHBOARD_BACKEND.md`
- **Estado de Implementación CRUD:** `BACKEND_IMPLEMENTATION_STATUS_QUOTE_CRUD.md`
- **Requerimientos UI Dashboard:** `UI_REQUIREMENTS_QUOTES_DASHBOARD.md`
- **Requerimientos UI CRUD:** `UI_REQUIREMENTS_QUOTE_CRUD.md`

### Archivos de Código

- **Modelos:** `backend/app/models/project.py`
- **Schemas:** `backend/app/schemas/project.py`, `backend/app/schemas/quote.py`
- **Endpoints:** `backend/app/api/v1/endpoints/projects.py`, `backend/app/api/v1/endpoints/quotes.py`
- **Cálculos:** `backend/app/core/calculations.py`
- **Servicios:** `backend/app/services/project_service.py`

---

## 8. Checklist de Implementación

### ✅ Completado

- [x] Modelos básicos (Project, Quote, QuoteItem, QuoteExpense)
- [x] CRUD completo de cotizaciones
- [x] Cálculo en tiempo real
- [x] Sistema de versiones básico
- [x] Envío de emails
- [x] Generación de PDFs/DOCX
- [x] Métricas básicas del dashboard
- [x] Validación de rentabilidad
- [x] Integración con BCR
- [x] Integración con sistema de créditos

### ❌ Pendiente (Sprint 1)

- [ ] Feature flag de tracking en `Organization.settings`
- [ ] Modelo `QuoteTrackingEvent`
- [ ] Campos de tracking en `Quote`
- [ ] Generación de `tracking_token`
- [ ] Pixel de seguimiento
- [ ] URLs únicas para PDFs
- [ ] Integración con envío de emails
- [ ] Endpoint de eventos de tracking

### ❌ Pendiente (Sprint 2)

- [ ] Estados extendidos (Viewed, Accepted, Rejected, Expired)
- [ ] **Endpoint `PATCH /api/v1/quotes/{id}/status` para Drag & Drop**
- [ ] Máquina de estados con validación de transiciones
- [ ] Snapshots de costos al mover a "Sent" (`unit_cost_snapshot`, `internal_cost_snapshot`, `client_price_snapshot`)
- [ ] Generación de PDF inmutable usando snapshots
- [ ] Prevención de regresión (Sent → Draft bloqueado)
- [ ] Lógica de transición automática
- [ ] Tarea Celery Beat para expiración
- [ ] Endpoints para marcar Accepted/Rejected

### ❌ Pendiente (Sprint 3)

- [ ] **Endpoint `GET /api/v1/analytics/dashboard` con cálculos SQL optimizados**
- [ ] Utilidad Neta calculada directamente en SQL (no en memoria)
- [ ] Agregaciones por período (trends mensuales/semanales)
- [ ] Top clients y top services con agregaciones SQL
- [ ] Índices de base de datos para performance
- [ ] Cache de resultados de analytics
- [ ] Pipeline Value
- [ ] Win Rate específico
- [ ] Cotizaciones que requieren atención
- [ ] Análisis de interés

### ❌ Pendiente (Sprint 4)

- [ ] Filtros avanzados por rentabilidad
- [ ] Filtros por rango de monto
- [ ] Búsqueda inteligente

### ❌ Pendiente (Sprint 5)

- [ ] Comparación de versiones
- [ ] Historial de cambios
- [ ] Visualización lado a lado

---

**Última actualización:** 2026-01-25  
**Versión:** 2.0  
**Estado:** Documento actualizado con implementación real y plan de trabajo
