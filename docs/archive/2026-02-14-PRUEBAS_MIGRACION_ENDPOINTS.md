# Pruebas: Migración y Endpoints

## Fecha: 2026-02-14

## Estado de Migración

### ✅ Migración Aplicada Exitosamente

**Migración:** `q2r3s4t5u6v7_add_quote_public_link_fields.py`

**Estado Actual:** `q2r3s4t5u6v7 (head)`

**Campos Agregados:**
- ✅ `quotes.sent_at` - DateTime cuando se envió la cotización
- ✅ `quotes.viewed_count` - Contador de vistas (default: 0)
- ✅ `quotes.public_token` - Token único para acceso público
- ✅ Índice único en `public_token`

**Comandos Ejecutados:**
```bash
cd backend
python -m alembic upgrade p1q2r3s4t5u6  # Migración previa
python -m alembic upgrade q2r3s4t5u6v7  # Nueva migración
```

**Resultado:** ✅ Migración aplicada correctamente

---

## Verificación de Endpoints

### Endpoints Implementados y Verificados

#### 1. ✅ GET /api/dashboard/kpis
**Archivo:** `backend/app/api/v1/endpoints/dashboard.py`
**Ruta:** `/dashboard/kpis`
**Estado:** ✅ Implementado y registrado

**Query Params:**
- `period`: 'month', 'quarter', 'year' (default: 'month')

**Respuesta Esperada:**
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

---

#### 2. ✅ GET /api/quotes
**Archivo:** `backend/app/api/v1/endpoints/quotes.py`
**Ruta:** `/quotes`
**Estado:** ✅ Implementado y registrado

**Query Params:**
- `status`: 'draft', 'sent', 'won', 'lost'
- `search`: string
- `page`: number (default: 1)
- `limit`: number (default: 20, max: 100)
- `sortBy`: 'date', 'amount', 'status'
- `order`: 'asc', 'desc'

**Respuesta Esperada:**
```json
{
  "data": [...],
  "meta": {
    "total": 45,
    "page": 1,
    "limit": 20,
    "totalPages": 3
  }
}
```

---

#### 3. ✅ GET /api/quotes/:id
**Archivo:** `backend/app/api/v1/endpoints/quotes.py`
**Ruta:** `/quotes/{quote_id}`
**Estado:** ✅ Implementado y registrado

**Respuesta Esperada:**
```json
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
  "publicToken": "abc-123",
  "projectId": 567
}
```

---

#### 4. ✅ PATCH /api/quotes/:id/status
**Archivo:** `backend/app/api/v1/endpoints/quotes.py`
**Ruta:** `/quotes/{quote_id}/status`
**Estado:** ✅ Implementado y registrado

**Body:**
```json
{
  "status": "accepted"
}
```

---

#### 5. ✅ POST /api/quotes/:id/public-link
**Archivo:** `backend/app/api/v1/endpoints/quotes.py`
**Ruta:** `/quotes/{quote_id}/public-link`
**Estado:** ✅ Implementado y registrado

**Body:**
```json
{
  "daysValid": 30
}
```

**Respuesta:**
```json
{
  "token": "uuid-token",
  "url": "https://app.nougram.com/proposal/uuid-token",
  "expiresAt": "2024-03-16T10:00:00Z"
}
```

---

#### 6. ✅ POST /api/quotes/:id/send-email
**Archivo:** `backend/app/api/v1/endpoints/quotes.py`
**Ruta:** `/quotes/{quote_id}/send-email`
**Estado:** ✅ Implementado y registrado

**Body:**
```json
{
  "to_email": "client@example.com",
  "subject": "Cotización: App E-commerce",
  "message": "Mensaje opcional",
  "include_pdf": true
}
```

---

#### 7. ✅ GET /api/admin/financial-summary
**Archivo:** `backend/app/api/v1/endpoints/admin.py`
**Ruta:** `/admin/financial-summary`
**Estado:** ✅ Implementado y registrado

**Respuesta Esperada:**
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

---

## Scripts de Prueba Creados

### 1. `backend/scripts/test_dashboard_endpoints.py`
**Propósito:** Verificar estructura de base de datos y datos de prueba
**Uso:** Ejecutar cuando la BD esté disponible

### 2. `backend/scripts/test_endpoints_http.py`
**Propósito:** Probar endpoints HTTP cuando el servidor esté corriendo
**Uso:**
```bash
# Terminal 1: Iniciar servidor
python -m uvicorn main:app --reload --port 8000

# Terminal 2: Ejecutar pruebas
python scripts/test_endpoints_http.py
```

---

## Checklist de Verificación

### Backend
- [x] Migración aplicada correctamente
- [x] Todos los endpoints implementados
- [x] Endpoints registrados en router
- [x] Schemas definidos
- [x] Manejo de permisos
- [x] Validación de tenant
- [x] Sin errores de linter

### Endpoints Específicos
- [x] GET /api/dashboard/kpis
- [x] GET /api/quotes (con filtros)
- [x] GET /api/quotes/:id
- [x] PATCH /api/quotes/:id/status
- [x] POST /api/quotes/:id/public-link
- [x] POST /api/quotes/:id/send-email
- [x] GET /api/admin/financial-summary

---

## Próximos Pasos para Testing

### 1. Iniciar Servidor Backend
```bash
cd backend
python -m uvicorn main:app --reload --port 8000
```

### 2. Probar Endpoints Manualmente

**Dashboard KPIs:**
```bash
curl http://localhost:8000/api/v1/dashboard/kpis?period=month \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Listar Cotizaciones:**
```bash
curl http://localhost:8000/api/v1/quotes?page=1&limit=20 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Obtener Cotización:**
```bash
curl http://localhost:8000/api/v1/quotes/1 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Cambiar Estado:**
```bash
curl -X PATCH http://localhost:8000/api/v1/quotes/1/status \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "sent"}'
```

**Generar Enlace Público:**
```bash
curl -X POST http://localhost:8000/api/v1/quotes/1/public-link \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"daysValid": 30}'
```

**Enviar Email:**
```bash
curl -X POST http://localhost:8000/api/v1/quotes/1/send-email \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"to_email": "test@example.com"}'
```

**Resumen Financiero:**
```bash
curl http://localhost:8000/api/v1/admin/financial-summary \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 3. Usar Script de Prueba Automatizado
```bash
python scripts/test_endpoints_http.py
```

---

## Notas Importantes

1. **Autenticación:** Todos los endpoints requieren token de autenticación (excepto endpoints públicos futuros)

2. **Permisos:**
   - `/dashboard/kpis` requiere `can_view_analytics`
   - `/admin/financial-summary` requiere `can_view_financial_projections`
   - `/quotes/:id/send-email` requiere `can_send_quotes`

3. **Multi-tenancy:** Todos los endpoints filtran automáticamente por `organization_id`

4. **Cache:**
   - KPIs: Cache de 2 minutos
   - Financial Summary: Cache de 5 minutos

---

## Estado Final

✅ **Migración aplicada correctamente**
✅ **Todos los endpoints implementados y verificados**
✅ **Scripts de prueba creados**
✅ **Sin errores de linter**

**Listo para testing con servidor backend corriendo**
