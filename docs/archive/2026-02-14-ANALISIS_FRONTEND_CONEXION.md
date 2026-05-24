# Análisis: Frontend - Estado y Conexión con Backend

## Fecha: 2026-02-14

## Resumen Ejecutivo

El frontend actual está **funcionalmente completo** pero utiliza **servicios mock** (localStorage y datos hardcodeados). Está **listo para conectar** con el backend, pero requiere:

1. ✅ Crear cliente API (existe en backup, necesita ser copiado/adaptado)
2. ✅ Reemplazar servicios mock por llamadas reales al backend
3. ⚠️ Adaptar tipos/interfaces para coincidir con respuestas del backend
4. ⚠️ Configurar variables de entorno

---

## Estado Actual del Frontend

### ✅ Componentes Implementados

1. **Dashboard Principal** (`/dashboard`)
   - `QuotePipeline` - Pipeline visual de cotizaciones
   - `KPIWidgets` - Widgets de KPIs (actualmente con datos hardcodeados)
   - `AlertsWidget` - Alertas y notificaciones

2. **Pipeline de Cotizaciones** (`/dashboard/quotes`)
   - Vista de tablero (board) y lista
   - Filtros: búsqueda, status, cliente, rango de fechas, monto
   - Drag & drop para cambiar estados
   - `QuoteCard` - Tarjeta individual de cotización

3. **Admin Panel** (`/admin`)
   - Gestión de equipo, costos fijos, configuración
   - Cálculo de BCR

### ⚠️ Servicios Actuales (Mock)

#### `quoteService.ts` (Mock)
```typescript
// Actualmente usa datos hardcodeados
let MOCK_QUOTES: Quote[] = [...]
```

**Métodos mock:**
- `getAll()` - Retorna array hardcodeado
- `getById()` - Busca en array mock
- `create()` - Agrega a array mock
- `update()` - Actualiza array mock
- `updateStatus()` - Actualiza status en mock
- `sendEmail()` - Simula envío

#### `quoteStorage.ts` (LocalStorage)
```typescript
// Usa localStorage como "base de datos"
const STORAGE_KEY = 'nougram_quotes_db';
```

**Métodos:**
- `getAll()` - Lee de localStorage
- `getById()` - Busca en localStorage
- `create()` - Guarda en localStorage
- `update()` - Actualiza localStorage
- `delete()` - Elimina de localStorage

### ✅ Cliente API Existente (en backup)

**Ubicación:** `frontend/backup/src/lib/api-client.ts`

**Características:**
- ✅ Configuración de `API_URL` desde `NEXT_PUBLIC_API_URL`
- ✅ Manejo de autenticación (Bearer token)
- ✅ Retry logic con exponential backoff
- ✅ Transformación de Decimal a Money (ESTÁNDAR NOUGRAM)
- ✅ Manejo de errores
- ✅ Soporte para descarga de PDF/DOCX

**Base URL:** `http://localhost:8000/api/v1`

---

## Comparación: Frontend vs Backend

### 1. Endpoint: GET /api/dashboard/kpis

**Frontend Espera (KPIWidgets.tsx):**
```typescript
// Actualmente hardcodeado:
{
  title: 'Total Cotizado',
  value: '$248,000',
  change: '+12%',
  trend: 'up'
}
```

**Backend Retorna:**
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

**⚠️ Acción Requerida:**
- Crear hook `useDashboardKPIs()` que llame a `/api/dashboard/kpis`
- Mapear respuesta del backend a formato esperado por `KPIWidgets`
- Agregar parámetro `period` (month, quarter, year)

---

### 2. Endpoint: GET /api/quotes

**Frontend Espera (QuoteCard.tsx):**
```typescript
interface Quote {
  id: string;
  project: string;
  client: string;
  amount: number;
  currency: string;
  margin: number;
  version: string;
  status: 'draft' | 'sent' | 'viewed' | 'accepted' | 'rejected';
  sentAt?: string;
  viewedCount: number;
  downloadCount: number;
}
```

**Backend Retorna:**
```json
{
  "data": [
    {
      "id": 1234,
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

**⚠️ Diferencias:**
- `id`: Frontend espera `string`, Backend retorna `number`
- `version`: Frontend espera `string` ('v2'), Backend retorna `number` (2)
- `status`: Frontend usa 'accepted'/'rejected', Backend usa 'won'/'lost' (pero el endpoint mapea correctamente)
- `downloadCount`: No existe en backend (puede ser 0 o agregarse después)
- `sentAt`: Backend retorna ISO string, Frontend espera string (compatible)

**✅ Acción Requerida:**
- Adaptar `quoteService.getAll()` para llamar a `/api/quotes`
- Mapear `id` de number a string
- Mapear `version` de number a string ('v' + number)
- Mapear `status` 'won'/'lost' a 'accepted'/'rejected' si es necesario
- Agregar `downloadCount: 0` por defecto

---

### 3. Endpoint: PATCH /api/quotes/:id/status

**Frontend Usa:**
```typescript
await quoteService.updateStatus(id, newStatus);
```

**Backend Espera:**
```json
{
  "status": "accepted"  // 'draft', 'sent', 'accepted', 'rejected'
}
```

**Backend Mapea:**
- 'draft' → 'Draft'
- 'sent' → 'Sent'
- 'accepted' → 'Won'
- 'rejected' → 'Lost'

**✅ Acción Requerida:**
- Actualizar `quoteService.updateStatus()` para llamar a `PATCH /api/quotes/:id/status`
- El mapeo ya está manejado en el backend

---

### 4. Endpoint: GET /api/admin/financial-summary

**Frontend Actualmente:**
- Calcula BCR localmente usando `useAdminData` hook
- Usa datos de `members` y `fixedCosts` del contexto

**Backend Retorna:**
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

**⚠️ Acción Requerida:**
- Crear hook `useFinancialSummary()` que llame a `/api/admin/financial-summary`
- Usar datos del backend en lugar de cálculos locales (opcional, puede mantener ambos)

---

### 5. Endpoint: POST /api/quotes/:id/public-link

**Frontend Actualmente:**
- No implementado (no se ve uso en componentes)

**Backend Espera:**
```json
{
  "daysValid": 30
}
```

**Backend Retorna:**
```json
{
  "token": "nuev-token-uuid",
  "url": "https://app.nougram.com/proposal/nuev-token-uuid",
  "expiresAt": "2024-03-16T10:00:00Z"
}
```

**✅ Acción Requerida:**
- Agregar método `generatePublicLink()` en `quoteService`
- Implementar UI para generar enlace público (cuando se necesite)

---

## Plan de Implementación

### Fase 1: Configuración Base ✅

1. **Copiar cliente API desde backup**
   ```bash
   # Copiar api-client.ts a src/lib/
   cp frontend/backup/src/lib/api-client.ts frontend/src/lib/api-client.ts
   ```

2. **Crear archivo .env.local**
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
   ```

3. **Verificar dependencias**
   - ✅ `fetch` (nativo en navegadores modernos)
   - Verificar si necesita `logger` y `money-transformer` del backup

### Fase 2: Servicios de API

1. **Actualizar `quoteService.ts`**
   - Reemplazar métodos mock por llamadas reales
   - Mapear tipos frontend ↔ backend
   - Manejar paginación

2. **Crear `dashboardService.ts`**
   - `getKPIs(period: string)` → `GET /api/dashboard/kpis?period={period}`
   - Mapear respuesta a formato de `KPIWidgets`

3. **Crear `adminService.ts`** (si no existe)
   - `getFinancialSummary()` → `GET /api/admin/financial-summary`

### Fase 3: Hooks y Contextos

1. **Actualizar `useQuotePipeline`**
   - Usar `quoteService.getAll()` real
   - Manejar loading y errores
   - Implementar paginación

2. **Crear `useDashboardKPIs`**
   - Fetch de KPIs desde backend
   - Cache local (opcional)

3. **Actualizar `DashboardContext`**
   - Usar servicios reales en lugar de `quoteStorage`

### Fase 4: Adaptación de Tipos

1. **Crear tipos de API**
   ```typescript
   // src/types/api.ts
   export interface QuoteAPIResponse {
     id: number;
     project: string;
     client: string;
     amount: number;
     currency: string;
     margin: number;
     status: string;
     version: number;
     createdAt: string;
     updatedAt: string;
     sentAt: string | null;
     viewedCount: number;
     publicToken: string | null;
   }
   ```

2. **Crear funciones de mapeo**
   ```typescript
   // src/lib/mappers.ts
   export function mapQuoteFromAPI(apiQuote: QuoteAPIResponse): Quote {
     return {
       id: String(apiQuote.id),
       project: apiQuote.project,
       client: apiQuote.client,
       amount: apiQuote.amount,
       currency: apiQuote.currency,
       margin: apiQuote.margin,
       version: `v${apiQuote.version}`,
       status: mapStatusFromAPI(apiQuote.status),
       sentAt: apiQuote.sentAt || undefined,
       viewedCount: apiQuote.viewedCount,
       downloadCount: 0, // Default
       createdAt: apiQuote.createdAt
     };
   }
   ```

### Fase 5: Testing y Ajustes

1. **Probar cada endpoint individualmente**
2. **Verificar mapeo de datos**
3. **Ajustar UI según respuestas reales**
4. **Manejar casos de error**

---

## Checklist de Conexión

### Configuración
- [ ] Copiar `api-client.ts` desde backup
- [ ] Crear `.env.local` con `NEXT_PUBLIC_API_URL`
- [ ] Verificar dependencias (logger, money-transformer)

### Servicios
- [ ] Actualizar `quoteService.ts` con llamadas reales
- [ ] Crear `dashboardService.ts` para KPIs
- [ ] Crear/actualizar `adminService.ts` para financial summary

### Hooks
- [ ] Actualizar `useQuotePipeline` para usar servicios reales
- [ ] Crear `useDashboardKPIs` hook
- [ ] Actualizar `DashboardContext` para usar servicios reales

### Tipos y Mapeo
- [ ] Crear tipos de API response
- [ ] Crear funciones de mapeo frontend ↔ backend
- [ ] Adaptar componentes para usar tipos mapeados

### Testing
- [ ] Probar GET /api/quotes con filtros
- [ ] Probar GET /api/dashboard/kpis
- [ ] Probar PATCH /api/quotes/:id/status
- [ ] Probar GET /api/admin/financial-summary
- [ ] Verificar manejo de errores

---

## Archivos a Crear/Modificar

### Nuevos Archivos:
1. `frontend/src/lib/api-client.ts` - Cliente API (copiar desde backup)
2. `frontend/src/services/dashboardService.ts` - Servicio de dashboard
3. `frontend/src/types/api.ts` - Tipos de respuestas API
4. `frontend/src/lib/mappers.ts` - Funciones de mapeo
5. `frontend/src/hooks/useDashboardKPIs.ts` - Hook para KPIs
6. `frontend/.env.local` - Variables de entorno

### Archivos a Modificar:
1. `frontend/src/services/quoteService.ts` - Reemplazar mock por API calls
2. `frontend/src/hooks/useQuotePipeline.ts` - Usar servicios reales
3. `frontend/src/context/DashboardContext.tsx` - Usar servicios reales
4. `frontend/src/components/dashboard/KPIWidgets.tsx` - Conectar con hook de KPIs
5. `frontend/src/services/adminService.ts` - Agregar método de financial summary (si existe)

---

## Notas Importantes

1. **Autenticación:** El cliente API del backup maneja tokens desde `localStorage.getItem('auth_token')`. Asegurarse de que el sistema de auth esté funcionando.

2. **Mapeo de Status:** El backend mapea correctamente los estados, pero hay que verificar que el frontend use los mismos valores ('accepted'/'rejected' vs 'won'/'lost').

3. **Paginación:** El endpoint `/api/quotes` retorna paginación. El frontend actualmente carga todas las cotizaciones. Considerar implementar paginación o mantener carga completa según necesidad.

4. **IDs:** El frontend usa `string` para IDs, el backend usa `number`. El mapeo es simple pero importante.

5. **Versiones:** El frontend muestra 'v1', 'v2', etc. El backend retorna números. Mapear con `'v' + version`.

6. **Download Count:** No existe en backend actualmente. Puede ser 0 por defecto o agregarse después.

---

## Conclusión

El frontend está **estructuralmente listo** para conectarse con el backend. Los componentes están bien diseñados y separados de la lógica de datos. Solo necesita:

1. ✅ Cliente API (existe en backup)
2. ✅ Reemplazar servicios mock por llamadas reales
3. ✅ Adaptar tipos y mapeos
4. ✅ Configurar variables de entorno

**Tiempo estimado de implementación:** 4-6 horas de desarrollo + testing

**Prioridad:** Alta - Es el siguiente paso lógico después de implementar los endpoints del backend.
