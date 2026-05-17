# Implementación de Allocations y Contingency en Cotizaciones

## Fecha: 2026-02-14

## Resumen de Cambios

Se ha implementado la funcionalidad completa de **Resource Allocations** y **Contingency** en el módulo de cotizaciones según la especificación del documento `2026-14-02-Nuevacotización-increase.md`.

## Cambios Implementados

### 1. Migración de Base de Datos

**Archivo:** `backend/alembic/versions/p1q2r3s4t5u6_add_quote_allocations_and_contingency.py`

**Cambios:**
- ✅ Agregado campo `client_company` a tabla `projects`
- ✅ Agregados campos de contingency a tabla `quotes`:
  - `contingency_description`
  - `contingency_type`
  - `contingency_value`
- ✅ Agregados nuevos campos a tabla `quote_items`:
  - `service_name`
  - `recurring_price`
  - `billing_frequency`
  - `duration_months`
  - `project_value`
  - `manual_price`
- ✅ Creada tabla `quote_item_allocations` con:
  - `quote_item_id` (FK a quote_items)
  - `team_member_id` (FK a team_members)
  - `hours`
  - `role`
  - `start_date`
  - `end_date`
  - Índices en `quote_item_id` y `team_member_id`

### 2. Schemas Actualizados

**Archivo:** `backend/app/schemas/project.py`

**Nuevos Schemas:**
- `ResourceAllocation` - Para allocations en quote items
- `Contingency` - Para contingency en quotes
- `ResourceAllocationResponse` - Para respuestas de allocations
- `ContingencyResponse` - Para respuestas de contingency

**Schemas Modificados:**
- `ProjectBase` - Agregado `client_company`
- `ProjectUpdate` - Agregado `client_company`
- `QuoteItemCreate` - Agregados: `service_name`, `manual_price`, `duration_months`, `allocations`
- `QuoteItemResponse` - Agregados todos los nuevos campos y `allocations`
- `ProjectCreateWithQuote` - Agregados: `target_margin`, `contingency`, `client_company`
- `QuoteUpdate` - Agregado `contingency`
- `QuoteCreateNewVersion` - Agregado `contingency`
- `QuoteResponse` - Agregado `contingency`

### 3. Modelos Actualizados

**Archivo:** `backend/app/models/project.py`

**Modelos Modificados:**
- `Project` - Agregado `client_company`
- `Quote` - Agregados campos de contingency
- `QuoteItem` - Agregados todos los nuevos campos y relación con `allocations`
- `QuoteItemAllocation` - Nuevo modelo para allocations

### 4. Lógica de Cálculo Mejorada

**Archivo:** `backend/app/core/calculations.py`

**Nueva Función:**
- `calculate_team_member_hourly_cost()` - Calcula el costo por hora de un team member específico

**Función Modificada:**
- `calculate_quote_totals_enhanced()` - Ahora:
  - Acepta parámetro `tenant_id` para cálculos de allocations
  - Si un item tiene `allocations` y es tipo `hourly`, calcula costo interno basado en:
    - `horas × costo_hora_recurso` para cada allocation
  - Si no hay allocations, usa `blended_rate` como fallback

### 5. Servicios Actualizados

**Archivo:** `backend/app/services/project_service.py`

**Métodos Modificados:**
- `create_project_with_quote()` - Maneja allocations, contingency, y `target_margin`
- `create_new_quote_version()` - Maneja allocations y contingency
- `_create_quote_items()` - Crea allocations después de crear quote items
- `_build_quote_response()` - Incluye allocations y contingency en respuesta

### 6. Endpoints Actualizados

**Archivo:** `backend/app/api/v1/endpoints/projects.py`

**Endpoints Modificados:**
- `POST /projects/` - Maneja allocations y contingency
- `PUT /projects/{project_id}/quotes/{quote_id}` - Maneja allocations y contingency
- Todos los endpoints de proyectos ahora incluyen `client_company` en respuestas

**Archivo:** `backend/app/api/v1/endpoints/quotes.py`

**Endpoints Modificados:**
- `POST /quotes/calculate` - Pasa `tenant_id` para cálculos de allocations

## Instrucciones para Ejecutar la Migración

### Prerrequisitos
1. Base de datos PostgreSQL corriendo
2. Variables de entorno configuradas (`.env`)

### Pasos

1. **Verificar estado actual de migraciones:**
   ```bash
   cd backend
   python -m alembic current
   ```

2. **Verificar que la nueva migración esté lista:**
   ```bash
   python -m alembic heads
   ```
   Debería mostrar: `p1q2r3s4t5u6 (head)`

3. **Ejecutar la migración:**
   ```bash
   python -m alembic upgrade head
   ```

4. **Verificar que la migración se aplicó correctamente:**
   ```bash
   python -m alembic current
   ```
   Debería mostrar: `p1q2r3s4t5u6`

### Rollback (si es necesario)

Si necesitas revertir la migración:
```bash
python -m alembic downgrade -1
```

## Estructura de Datos Esperada del Frontend

### Request Body para Crear Cotización

```json
{
  "projectName": "Desarrollo E-commerce 2024",
  "clientName": "Juan Pérez",
  "clientCompany": "Tech Solutions SAS",
  "clientEmail": "juan@techsolutions.com",
  "currency": "COP",
  "targetMargin": 35,
  "selectedTaxIds": [1, 3],
  "allowLowMargin": false,
  "contingency": {
    "description": "Riesgo de cambios en alcance",
    "type": "percentage",
    "value": 5
  },
  "items": [
    {
      "serviceId": 101,
      "serviceName": "Desarrollo Backend",
      "pricingType": "hourly",
      "estimatedHours": 120,
      "quantity": 1,
      "allocations": [
        {
          "teamMemberId": 5,
          "hours": 80,
          "role": "Senior Dev",
          "startDate": "2024-03-01",
          "endDate": "2024-03-31"
        },
        {
          "teamMemberId": 8,
          "hours": 40,
          "role": "Junior Dev"
        }
      ]
    },
    {
      "serviceId": 204,
      "serviceName": "Licencia de Software",
      "pricingType": "fixed",
      "fixedPrice": 5000000,
      "quantity": 1,
      "allocations": []
    }
  ]
}
```

### Notas Importantes

1. **targetMargin**: Se envía como porcentaje (0-100), el backend lo convierte a decimal (0-1)
2. **allocations**: Solo se usan para cálculo de costo interno si `pricingType` es `hourly`
3. **contingency**: Opcional, puede ser `fixed` o `percentage`
4. **serviceName**: Opcional, si no se envía se usa el nombre del servicio

## Verificaciones Realizadas

- ✅ No hay errores de linting
- ✅ Migración está correctamente conectada en la cadena
- ✅ Todos los schemas están actualizados
- ✅ Todos los modelos están actualizados
- ✅ Lógica de cálculo implementada
- ✅ Endpoints actualizados
- ✅ Servicios actualizados

## Próximos Pasos

1. Ejecutar la migración en el entorno de desarrollo
2. Probar los endpoints con Postman/Thunder Client
3. Conectar con el frontend
4. Verificar que los cálculos con allocations funcionen correctamente
5. Probar casos edge (sin allocations, con allocations parciales, etc.)

## Notas Técnicas

- Las allocations se almacenan después de crear los quote items (necesitan el ID)
- El cálculo de costo interno usa allocations cuando están presentes, sino usa blended_rate
- La contingency se almacena en la tabla `quotes`, no en `quote_items`
- `target_margin` se convierte de porcentaje a decimal automáticamente
