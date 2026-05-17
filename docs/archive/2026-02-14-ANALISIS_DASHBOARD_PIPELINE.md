# Análisis: Dashboard y Pipeline - Backend vs Frontend

## Fecha: 2026-02-14

## Comparación de Endpoints Requeridos vs Implementados

### 1. KPIs y Estadísticas (Widgets)

**Frontend Requiere:**
- **Endpoint:** `GET /api/dashboard/kpis`
- **Query Params:** `period`: 'month', 'quarter', 'year' (Opcional, defecto 'month')
- **Respuesta Esperada:**
  ```json
  {
    "totalRevenue": 150000000,
    "totalRevenueChange": 12.5,
    "activeQuotesCount": 24,
    "activeQuotesChange": 5.0,
    "closeRate": 45.2,
    "closeRateChange": -2.1,
    "averageTicket": 8500000,
    "averageTicketChange": 1.5
  }
  ```

**Backend Actual:**
- ✅ **Existe:** `GET /insights/dashboard`
- ❌ **Formato diferente:** Retorna más campos pero no tiene el formato exacto requerido
- ❌ **Falta:** Parámetro `period` (month, quarter, year)
- ❌ **Falta:** Campos `totalRevenueChange`, `activeQuotesChange`, `closeRateChange`, `averageTicketChange`
- ❌ **Falta:** Campo `activeQuotesCount` (cuenta cotizaciones activas, no proyectos)
- ❌ **Falta:** Campo `averageTicket` (ticket promedio)

**Estado:** ⚠️ **PARCIALMENTE IMPLEMENTADO** - Necesita adaptación

---

### 2. Pipeline de Cotizaciones

**Frontend Requiere:**
- **Endpoint:** `GET /api/quotes`
- **Query Params:**
  - `status`: 'draft' | 'sent' | 'viewed' | 'accepted' | 'rejected'
  - `search`: string (Busca por cliente o proyecto)
  - `page`: number (Defecto 1)
  - `limit`: number (Defecto 20)
  - `sortBy`: 'date' | 'amount' | 'status'
  - `order`: 'asc' | 'desc'
- **Respuesta Esperada:**
  ```json
  {
    "data": [
      {
        "id": "uuid-1234",
        "project": "App E-commerce",
        "client": "TechCorp",
        "amount": 25000000,
        "currency": "COP",
        "margin": 42,
        "status": "sent",
        "version": 2,
        "createdAt": "2024-02-14T10:00:00Z",
        "updatedAt": "2024-02-15T14:30:00Z",
        "sentAt": "2024-02-15T14:30:00Z",
        "viewedCount": 3,
        "publicToken": "abc-123"
      }
    ],
    "meta": {
      "total": 45,
      "page": 1,
      "limit": 20,
      "totalPages": 3
    }
  }
  ```

**Backend Actual:**
- ❌ **No existe:** `GET /api/quotes` (endpoint general para listar cotizaciones)
- ✅ **Existe:** `GET /projects/{project_id}/quotes` (lista cotizaciones de un proyecto específico)
- ✅ **Existe:** `GET /projects/` (lista proyectos con paginación)
- ❌ **Falta:** Endpoint que liste todas las cotizaciones con filtros
- ❌ **Falta:** Campos `sentAt`, `viewedCount`, `publicToken` en modelo Quote
- ❌ **Falta:** Búsqueda por cliente o proyecto en endpoint de quotes
- ❌ **Falta:** Ordenamiento por `amount` y `status`

**Estado:** ❌ **NO IMPLEMENTADO** - Necesita implementación completa

---

### 3. Finanzas y Administrativo (BCR)

**Frontend Requiere:**
- **Endpoint:** `GET /api/admin/financial-summary`
- **Respuesta Esperada:**
  ```json
  {
    "monthlyFixedCosts": 15000000,
    "monthlyPayroll": 45000000,
    "totalBillableHours": 6400,
    "blendedCostRate": 65000,
    "activeTeamMembers": 12,
    "currency": "COP"
  }
  ```

**Backend Actual:**
- ✅ **Existe:** `GET /settings/calculations/agency-cost-hour`
- ⚠️ **Formato diferente:** Retorna más información pero no exactamente el formato requerido
- ✅ **Tiene:** `blendedCostRate`, información de costos fijos y nómina
- ❌ **Falta:** Endpoint específico `/api/admin/financial-summary`
- ❌ **Falta:** Campo `monthlyPayroll` explícito (está en el cálculo pero no en formato directo)
- ❌ **Falta:** Campo `activeTeamMembers` explícito

**Estado:** ⚠️ **PARCIALMENTE IMPLEMENTADO** - Necesita adaptación o nuevo endpoint

---

### 4. Acciones sobre Cotizaciones

#### 4.1 Cambiar Estado

**Frontend Requiere:**
- **Endpoint:** `PATCH /api/quotes/:id/status`
- **Body:**
  ```json
  {
    "status": "accepted"
  }
  ```

**Backend Actual:**
- ❌ **No existe:** `PATCH /quotes/:id/status`
- ✅ **Existe:** `PUT /projects/{project_id}` - Actualiza proyecto completo (incluye status)
- ❌ **Falta:** Endpoint específico para cambiar solo el status de una cotización
- ⚠️ **Nota:** El status está en `Project`, no en `Quote`. Necesita clarificación si el frontend quiere cambiar status del proyecto o crear un status específico para quotes

**Estado:** ❌ **NO IMPLEMENTADO** - Necesita implementación

#### 4.2 Generar Enlace Público

**Frontend Requiere:**
- **Endpoint:** `POST /api/quotes/:id/public-link`
- **Body:**
  ```json
  {
    "daysValid": 30
  }
  ```
- **Respuesta:**
  ```json
  {
    "token": "nuev-token-uuid",
    "url": "https://app.nougram.com/proposal/nuev-token-uuid",
    "expiresAt": "2024-03-16T10:00:00Z"
  }
  ```

**Backend Actual:**
- ❌ **No existe:** `POST /quotes/:id/public-link`
- ❌ **Falta:** Modelo para almacenar tokens públicos
- ❌ **Falta:** Campos `publicToken`, `viewedCount`, `sentAt` en modelo Quote
- ❌ **Falta:** Lógica para generar y validar tokens públicos

**Estado:** ❌ **NO IMPLEMENTADO** - Necesita implementación completa

---

## Resumen de Estado

| Endpoint | Estado | Acción Requerida |
|----------|--------|------------------|
| `GET /api/dashboard/kpis` | ⚠️ Parcial | Adaptar endpoint existente o crear nuevo |
| `GET /api/quotes` | ❌ No existe | Crear nuevo endpoint |
| `GET /api/admin/financial-summary` | ⚠️ Parcial | Adaptar o crear nuevo endpoint |
| `PATCH /api/quotes/:id/status` | ❌ No existe | Crear nuevo endpoint |
| `POST /api/quotes/:id/public-link` | ❌ No existe | Crear nuevo endpoint + modelo |

## Campos Faltantes en Modelos

### Quote Model
- `sent_at` - DateTime cuando se envió la cotización
- `viewed_count` - Contador de veces que se abrió el link
- `public_token` - Token para acceso público (o tabla separada)

### Tabla Nueva (si se usa)
- `quote_public_links` - Para almacenar tokens públicos con expiración

## Próximos Pasos

1. Crear endpoint `GET /api/dashboard/kpis` con formato exacto requerido
2. Crear endpoint `GET /api/quotes` para listar cotizaciones con filtros
3. Crear endpoint `GET /api/admin/financial-summary` con formato requerido
4. Crear endpoint `PATCH /api/quotes/:id/status` para cambiar estado
5. Crear endpoint `POST /api/quotes/:id/public-link` para generar enlaces públicos
6. Agregar campos faltantes a modelo Quote (sent_at, viewed_count, public_token)
7. Crear migración para nuevos campos
