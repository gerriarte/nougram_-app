# Equipment Amortization - Migración Alembic

**Archivo:** `backend/alembic/versions/n20260125_add_equipment_amortization.py`

## Descripción

Migración para crear la tabla `equipment_amortization` con todos los campos necesarios para gestionar la amortización de equipos.

## Campos Creados

### Campos Básicos
- `id` - Primary key
- `name` - Nombre del equipo
- `description` - Descripción opcional
- `category` - Categoría (Hardware, Software, Vehicles, Office Equipment)

### Información Financiera
- `purchase_price` - Precio de compra (Numeric(15, 2))
- `purchase_date` - Fecha de compra (Date)
- `currency` - Moneda (String(3))
- `exchange_rate_at_purchase` - TRM histórica (Numeric(10, 4), nullable) ⚠️ **CRÍTICO**

### Parámetros de Depreciación
- `useful_life_months` - Vida útil en meses (Integer)
- `salvage_value` - Valor de salvamento (Numeric(15, 2), default=0) ⚠️ **CRÍTICO**
- `depreciation_method` - Método de depreciación (String: "straight_line" o "declining_balance")

### Estado
- `is_active` - Equipo activo (Boolean, default=true)

### Timestamps
- `created_at` - Fecha de creación (DateTime with timezone)
- `updated_at` - Fecha de actualización (DateTime with timezone)

### Multi-tenant y Soft Delete
- `organization_id` - Foreign key a organizations (Integer, NOT NULL)
- `deleted_at` - Fecha de eliminación (DateTime with timezone, nullable)
- `deleted_by_id` - Usuario que eliminó (Foreign key a users, nullable)

## Índices Creados

1. `ix_equipment_amortization_id` - Índice en id
2. `ix_equipment_amortization_organization_id` - Índice en organization_id
3. `ix_equipment_amortization_category` - Índice en category
4. `ix_equipment_amortization_deleted_at` - Índice en deleted_at
5. `ix_equipment_amortization_is_active` - Índice en is_active
6. `ix_equipment_amortization_org_active_deleted` - Índice compuesto (organization_id, is_active, deleted_at)

## Foreign Keys

- `fk_equipment_amortization_organization_id` → `organizations.id`
- `fk_equipment_amortization_deleted_by_id` → `users.id`

## Aplicar Migración

```bash
cd backend
alembic upgrade head
```

## Revertir Migración

```bash
cd backend
alembic downgrade -1
```

## Referencias

- **Modelo**: [`../../../../backend/app/models/equipment.py`](../../../../backend/app/models/equipment.py)
- **Arquitectura Models**: [`../../architecture/mvc/models.md`](../../architecture/mvc/models.md)
