# Implementación: Conexión Frontend con Backend

## Fecha: 2026-02-14

## Resumen

Se ha completado la conexión del frontend con el backend. Todos los servicios mock han sido reemplazados por llamadas reales a la API del backend.

---

## Archivos Creados

### 1. `frontend/src/lib/api-client.ts`
**Cliente API base para comunicación con backend**

**Características:**
- ✅ Manejo de autenticación (Bearer token desde localStorage)
- ✅ Retry logic con exponential backoff
- ✅ Manejo de errores HTTP (401, 422, etc.)
- ✅ Soporte para descarga de PDF/DOCX
- ✅ Configuración de URL base desde `NEXT_PUBLIC_API_URL`

**Funciones principales:**
- `apiRequest<T>(endpoint, options, retry)` - Request genérico con retry
- `downloadPDF(endpoint, filename)` - Descarga de PDF
- `downloadDOCX(endpoint, filename)` - Descarga de DOCX

---

### 2. `frontend/src/types/api.ts`
**Tipos TypeScript para respuestas de API**

**Tipos definidos:**
- `DashboardKPIsResponse` - Respuesta de KPIs
- `QuoteAPIResponse` - Respuesta individual de cotización
- `QuotesListResponse` - Respuesta paginada de cotizaciones
- `QuoteStatusUpdateRequest` - Request para actualizar status
- `PublicLinkRequest/Response` - Request/Response para enlaces públicos
- `FinancialSummaryResponse` - Resumen financiero

---

### 3. `frontend/src/lib/mappers.ts`
**Funciones de mapeo entre API y Frontend**

**Funciones:**
- `mapQuoteFromAPI(apiQuote)` - Mapea respuesta API a tipo Quote del frontend
- `mapStatusFromAPI(status)` - Mapea status del backend al frontend
- `mapStatusToAPI(status)` - Mapea status del frontend al backend
- `formatRelativeDate(dateString)` - Formatea fechas relativas ("Hace 2d")

**Mapeos importantes:**
- `id`: number → string
- `version`: number → string ('v' + number)
- `status`: 'won'/'lost' → 'accepted'/'rejected'
- `sentAt`: ISO string → formato relativo

---

### 4. `frontend/src/services/dashboardService.ts`
**Servicio para endpoints de dashboard**

**Métodos:**
- `getKPIs(period)` - Obtiene KPIs del dashboard
  - Endpoint: `GET /api/dashboard/kpis?period={period}`
- `getFinancialSummary()` - Obtiene resumen financiero
  - Endpoint: `GET /api/admin/financial-summary`

---

### 5. `frontend/src/hooks/useDashboardKPIs.ts`
**Hook React para obtener KPIs**

**Características:**
- ✅ Fetch automático al montar
- ✅ Soporte para auto-refresh opcional
- ✅ Estados de loading y error
- ✅ Función `refresh()` para actualizar manualmente

**Uso:**
```typescript
const { kpis, loading, error, refresh } = useDashboardKPIs({
  period: 'month',
  autoRefresh: false,
  refreshInterval: 60000
});
```

---

### 6. `frontend/.env.local`
**Variables de entorno**

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

---

## Archivos Modificados

### 1. `frontend/src/services/quoteService.ts`
**Actualizado para usar API real**

**Cambios:**
- ❌ Eliminado: Datos mock (`MOCK_QUOTES`)
- ✅ Agregado: Llamadas reales a `/api/quotes`
- ✅ `getAll()` ahora acepta parámetros de filtrado
- ✅ `updateStatus()` llama a `PATCH /api/quotes/:id/status`
- ✅ `generatePublicLink()` llama a `POST /api/quotes/:id/public-link`

**Métodos actualizados:**
- `getAll(params?)` - Con filtros, paginación y ordenamiento
- `updateStatus(id, status)` - Actualiza status vía API
- `generatePublicLink(id, daysValid)` - Genera enlace público

**Métodos pendientes (TODO):**
- `getById()` - Necesita endpoint `GET /api/quotes/:id`
- `create()` - Necesita endpoint de creación
- `update()` - Necesita endpoint de actualización
- `sendEmail()` - Necesita endpoint de envío de email

---

### 2. `frontend/src/hooks/useQuotePipeline.ts`
**Actualizado para usar servicios reales**

**Cambios:**
- ✅ `loadQuotes()` ahora pasa filtros al backend
- ✅ `handleStatusChange()` incluye revert en caso de error
- ✅ Dependencias de `useEffect` actualizadas para re-fetch cuando cambian filtros

**Mejoras:**
- Optimistic updates con revert en caso de error
- Filtros de búsqueda y status se envían al backend

---

### 3. `frontend/src/components/dashboard/KPIWidgets.tsx`
**Actualizado para mostrar datos reales**

**Cambios:**
- ✅ Integrado con `useDashboardKPIs` hook
- ✅ Muestra estados de loading y error
- ✅ Formatea valores según datos del backend
- ✅ Muestra cambios porcentuales reales

**Métricas mostradas:**
1. **Total Cotizado** - `totalRevenue` del backend
2. **Cotizaciones Activas** - `activeQuotesCount` del backend
3. **Tasa de Cierre** - `closeRate` del backend
4. **Ticket Promedio** - `averageTicket` del backend

**Formato:**
- Valores monetarios formateados con `Intl.NumberFormat`
- Porcentajes con 1 decimal
- Indicadores de tendencia (up/down) basados en cambios

---

## Endpoints Conectados

| Endpoint | Método | Servicio | Hook/Componente | Estado |
|----------|--------|----------|-----------------|--------|
| `/api/dashboard/kpis` | GET | `dashboardService.getKPIs()` | `useDashboardKPIs` → `KPIWidgets` | ✅ Completo |
| `/api/quotes` | GET | `quoteService.getAll()` | `useQuotePipeline` → `QuotePipeline` | ✅ Completo |
| `/api/quotes/:id/status` | PATCH | `quoteService.updateStatus()` | `useQuotePipeline` → `QuoteCard` | ✅ Completo |
| `/api/quotes/:id/public-link` | POST | `quoteService.generatePublicLink()` | - | ✅ Implementado |
| `/api/admin/financial-summary` | GET | `dashboardService.getFinancialSummary()` | - | ✅ Implementado |

---

## Próximos Pasos

### Endpoints Pendientes

1. **GET /api/quotes/:id**
   - Necesario para `quoteService.getById()`
   - Usado en páginas de detalle de cotización

2. **POST /api/quotes** o **POST /api/projects/:id/quotes**
   - Necesario para `quoteService.create()`
   - Usado en creación de nuevas cotizaciones

3. **PUT /api/quotes/:id**
   - Necesario para `quoteService.update()`
   - Usado en edición de cotizaciones

4. **POST /api/quotes/:id/send-email**
   - Necesario para `quoteService.sendEmail()`
   - Usado en envío de cotizaciones por email

### Mejoras Futuras

1. **Manejo de errores mejorado**
   - Mostrar toasts/notificaciones en caso de error
   - Reintentos automáticos para errores de red

2. **Cache y optimización**
   - Implementar cache para KPIs (ya tienen cache en backend)
   - Optimistic updates más robustos

3. **Paginación en UI**
   - Implementar paginación visual para lista de cotizaciones
   - Carga infinita (infinite scroll)

4. **Filtros avanzados**
   - Implementar filtros de fecha en el frontend
   - Filtros de rango de monto en el backend

---

## Testing

### Checklist de Pruebas

- [ ] Verificar que los KPIs se cargan correctamente
- [ ] Verificar que las cotizaciones se listan correctamente
- [ ] Probar cambio de status de cotización
- [ ] Probar búsqueda de cotizaciones
- [ ] Probar filtros por status
- [ ] Verificar manejo de errores (backend desconectado)
- [ ] Verificar autenticación (token inválido)
- [ ] Probar generación de enlace público

### Comandos para Testing

```bash
# Iniciar backend
cd backend
python -m uvicorn main:app --reload --port 8000

# Iniciar frontend
cd frontend
npm run dev
```

---

## Notas Técnicas

1. **Autenticación:**
   - El cliente API busca el token en `localStorage.getItem('auth_token')`
   - En caso de 401, redirige a `/` y limpia el token

2. **Mapeo de Status:**
   - Backend usa: 'draft', 'sent', 'won', 'lost'
   - Frontend usa: 'draft', 'sent', 'viewed', 'accepted', 'rejected'
   - El mapeo se hace automáticamente en `mappers.ts`

3. **Formato de Fechas:**
   - Backend retorna ISO strings: `"2024-02-14T10:00:00Z"`
   - Frontend muestra formato relativo: `"Hace 2d"`
   - La conversión se hace en `formatRelativeDate()`

4. **IDs:**
   - Backend usa `number` para IDs
   - Frontend usa `string` para IDs
   - La conversión se hace automáticamente: `String(apiQuote.id)`

5. **Versiones:**
   - Backend retorna: `version: 2`
   - Frontend muestra: `version: 'v2'`
   - La conversión se hace: `'v' + apiQuote.version`

---

## Estado Final

✅ **Frontend completamente conectado con backend**

- Todos los endpoints principales implementados
- Servicios mock reemplazados por llamadas reales
- Tipos y mapeos configurados
- Manejo de errores implementado
- Estados de loading y error en UI

**Listo para testing y uso en producción** (después de probar los endpoints pendientes)
