# Implementación: Dashboard y Pipeline - Backend

## Fecha: 2026-02-14

## Resumen

Se han implementado todos los endpoints requeridos por el frontend para el Dashboard Principal y el Pipeline de Cotizaciones según las especificaciones en `docs/2026-14-02-Backend-Dashboardypipeline`.

## Endpoints Implementados

### 1. ✅ GET /api/dashboard/kpis

**Archivo:** `backend/app/api/v1/endpoints/dashboard.py`

**Funcionalidad:**
- Retorna KPIs del dashboard con formato exacto requerido
- Soporta filtrado por periodo: 'month', 'quarter', 'year'
- Calcula cambios porcentuales vs periodo anterior

**Respuesta:**
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

**Características:**
- Cache de 2 minutos
- Cálculo de ingresos de proyectos "Won"
- Conteo de cotizaciones activas (status "Sent")
- Tasa de cierre (Won / (Won + Lost))
- Ticket promedio

---

### 2. ✅ GET /api/quotes

**Archivo:** `backend/app/api/v1/endpoints/quotes.py`

**Funcionalidad:**
- Lista todas las cotizaciones con filtros avanzados
- Paginación y ordenamiento
- Búsqueda por cliente o proyecto

**Query Parameters:**
- `status`: 'draft', 'sent', 'won', 'lost'
- `search`: Búsqueda por cliente o proyecto
- `page`: Número de página (default: 1)
- `limit`: Items por página (default: 20, max: 100)
- `sort_by`: 'date', 'amount', 'status'
- `order`: 'asc', 'desc'

**Respuesta:**
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

---

### 3. ✅ GET /api/admin/financial-summary

**Archivo:** `backend/app/api/v1/endpoints/admin.py`

**Funcionalidad:**
- Resumen financiero para panel administrativo
- Calcula costos fijos mensuales
- Calcula nómina mensual total
- Calcula capacidad de horas facturables
- Calcula BCR (Blended Cost Rate)

**Respuesta:**
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

**Características:**
- Cache de 5 minutos
- Normalización de monedas a moneda primaria
- Cálculo de BCR usando función existente
- Conteo de miembros activos del equipo

---

### 4. ✅ PATCH /api/quotes/:id/status

**Archivo:** `backend/app/api/v1/endpoints/quotes.py`

**Funcionalidad:**
- Cambia el estado de una cotización (actualiza el estado del proyecto)
- Actualiza `sent_at` cuando se marca como "sent"

**Body:**
```json
{
  "status": "accepted"
}
```

**Status Mapping:**
- 'draft' -> 'Draft'
- 'sent' -> 'Sent'
- 'accepted' -> 'Won'
- 'rejected' -> 'Lost'

**Respuesta:**
- Retorna la cotización actualizada con toda la información

---

### 5. ✅ POST /api/quotes/:id/public-link

**Archivo:** `backend/app/api/v1/endpoints/quotes.py`

**Funcionalidad:**
- Genera un token público para acceso a la cotización
- Configura expiración del enlace
- Almacena token en la base de datos

**Body:**
```json
{
  "daysValid": 30
}
```

**Respuesta:**
```json
{
  "token": "nuev-token-uuid",
  "url": "https://app.nougram.com/proposal/nuev-token-uuid",
  "expiresAt": "2024-03-16T10:00:00Z"
}
```

**Características:**
- Genera UUID único para cada token
- URL configurable vía variable de entorno `PUBLIC_QUOTE_BASE_URL`
- Token almacenado en campo `public_token` de Quote

---

## Cambios en Modelos

### Quote Model (`backend/app/models/project.py`)

**Campos Agregados:**
- `sent_at`: DateTime cuando se envió la cotización
- `viewed_count`: Contador de veces que se abrió el link (default: 0)
- `public_token`: Token para acceso público (único, indexado)

```python
# Public link and tracking fields
sent_at = Column(DateTime(timezone=True), nullable=True)
viewed_count = Column(Integer, default=0, nullable=False)
public_token = Column(String, nullable=True, unique=True, index=True)
```

---

## Migración de Base de Datos

### Archivo: `backend/alembic/versions/q2r3s4t5u6v7_add_quote_public_link_fields.py`

**Cambios:**
- Agrega columna `sent_at` a tabla `quotes`
- Agrega columna `viewed_count` a tabla `quotes` (default: 0)
- Agrega columna `public_token` a tabla `quotes` (nullable, unique)
- Crea índice único en `public_token`

**Down Revision:** `p1q2r3s4t5u6` (add_quote_allocations_and_contingency)

---

## Schemas Nuevos

### `backend/app/schemas/project.py`

**Schemas Agregados:**
1. `QuoteStatusUpdate`: Para actualizar estado de cotización
2. `QuotePublicLinkRequest`: Para generar enlace público
3. `QuotePublicLinkResponse`: Respuesta de enlace público

---

## Archivos Creados/Modificados

### Nuevos Archivos:
1. `backend/app/api/v1/endpoints/dashboard.py` - Endpoints de dashboard
2. `backend/app/api/v1/endpoints/admin.py` - Endpoints administrativos
3. `backend/alembic/versions/q2r3s4t5u6v7_add_quote_public_link_fields.py` - Migración

### Archivos Modificados:
1. `backend/app/api/v1/router.py` - Agregados routers de dashboard y admin
2. `backend/app/api/v1/endpoints/quotes.py` - Agregados endpoints de listado, cambio de estado y enlace público
3. `backend/app/models/project.py` - Agregados campos a Quote
4. `backend/app/schemas/project.py` - Agregados schemas nuevos

---

## Próximos Pasos

1. **Ejecutar Migración:**
   ```bash
   cd backend
   python -m alembic upgrade head
   ```

2. **Configurar Variable de Entorno:**
   - Agregar `PUBLIC_QUOTE_BASE_URL` al archivo `.env` si se desea cambiar la URL base para enlaces públicos

3. **Testing:**
   - Probar todos los endpoints con el frontend
   - Verificar que los cálculos de KPIs sean correctos
   - Verificar que los filtros y paginación funcionen correctamente

4. **Funcionalidad Futura:**
   - Implementar endpoint público para ver cotizaciones usando `public_token`
   - Implementar tracking de `viewed_count` cuando se acceda al enlace público
   - Considerar agregar expiración automática de tokens

---

## Notas Técnicas

1. **Cache:** Los endpoints de KPIs y resumen financiero usan cache para mejorar rendimiento
2. **Multi-tenancy:** Todos los endpoints respetan el contexto de tenant/organización
3. **Permisos:** Los endpoints administrativos requieren permisos específicos (`can_view_financial_projections`, `can_view_analytics`)
4. **Normalización de Moneda:** Los cálculos financieros normalizan todas las monedas a la moneda primaria de la organización
5. **Status Mapping:** Se mapean los estados del frontend a los estados del backend (ej: 'accepted' -> 'Won')

---

## Estado de Implementación

| Endpoint | Estado | Notas |
|----------|--------|-------|
| `GET /api/dashboard/kpis` | ✅ Completo | Implementado con cache |
| `GET /api/quotes` | ✅ Completo | Filtros, paginación y ordenamiento |
| `GET /api/admin/financial-summary` | ✅ Completo | Implementado con cache |
| `PATCH /api/quotes/:id/status` | ✅ Completo | Actualiza proyecto status |
| `POST /api/quotes/:id/public-link` | ✅ Completo | Genera token único |

Todos los endpoints están listos para ser probados con el frontend.
