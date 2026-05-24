# Programas de Migraciones - Base de Datos Cotizador

**Fecha:** 14 de febrero de 2026  
**Ubicación:** `backend/alembic/versions/`  
**ORM:** Alembic (SQLAlchemy)

---

## 1. Resumen

| Métrica | Valor |
|---------|-------|
| Total de migraciones | 25 |
| Migración inicial | 001_initial |
| Puntos de merge | 1 (5e8453f9fad0) |
| Heads actuales | 2 (m20251230, q2r3s4t5u6v7) |

**Nota:** Existen 2 heads. Se recomienda ejecutar `alembic merge` para unificar y generar una migración que las consolide antes de futuros cambios.

---

## 2. Orden de Ejecución (Grafo Completo)

```
<base>
    └── 001_initial (Initial migration)
            └── 362aa60e787f (add_currency_support)
                    └── d7dc269bb824 (add_taxes_support)
                            └── 48d403df0b4b (add_soft_delete_support)
                                    └── r20251109_role_varchar
                                            └── r20251110_user_password
                                                    └── dae436c985e8 (add_performance_indexes)
                                                            └── a1b2c3d4e5f6 (add_multi_tenant_organization_support)
                                                                    └── b2c3d4e5f6a7 (add_industry_templates)
                                                                            └── c3d4e5f6a7b8 (add_audit_logs)
                                                                                    └── d4e5f6a7b8c9 (add_role_type)
                                                                                            ├── 8f0817455976 (add_credit_system)
                                                                                            ├── e5f6a7b8c9d0 (add_invitations)
                                                                                            └── e6f7a8b9c0d1 (add_service_pricing_types)
                                                                                                    └── f7a8b9c0d1e2 (add_legal_finance_templates)
                                                                                                            └── g8h9i0j1k2l3 (add_quote_expenses)
                                                                                                                    └── h9i0j1k2l3m4 (update_templates_with_expenses)
                                                                                                                            └── i0j1k2l3m4n5 (add_quote_revisions)
                                                                                                                                    └── j1k2l3m4n5o6 (update_templates_with_project_value)
                                                                                                                                            ├── 5e8453f9fad0 (merge_heads) ← merge de 8f08, e5f6, j1k2
                                                                                                                                            │       └── bfc774065893 (make estimated_hours nullable)
                                                                                                                                            │               └── 3b000e90aba6 (add_target_margin_percentage)
                                                                                                                                            │                       └── p1q2r3s4t5u6 (add_quote_allocations_and_contingency)
                                                                                                                                            │                               └── q2r3s4t5u6v7 (add_quote_public_link_fields) ★ HEAD
                                                                                                                                            └── m20251230 (migrate_money_to_numeric) ★ HEAD
```

---

## 3. Catálogo de Migraciones

### 3.1 001_initial

| Campo | Valor |
|-------|-------|
| **Archivo** | `001_initial_migration.py` |
| **Revises** | *(ninguno - raíz)* |
| **Descripción** | Migración inicial del esquema |

**Cambios upgrade:**
- Tabla `users` (id, email, full_name, google_refresh_token)
- Tabla `costs_fixed` (costos fijos)
- Tabla `team_members` (con FK a users)
- Tabla `services` (catálogo de servicios)
- Tabla `projects` (proyectos)
- Tabla `quotes` (cotizaciones)
- Tabla `quote_items` (ítems de cotización)

---

### 3.2 362aa60e787f - add_currency_support

| Campo | Valor |
|-------|-------|
| **Archivo** | `362aa60e787f_add_currency_support.py` |
| **Revises** | 001_initial |
| **Descripción** | Soporte de moneda en costos y equipo |

**Cambios upgrade:**
- Tabla `agency_settings` (primary_currency, currency_symbol)
- Columna `currency` en `costs_fixed` (default USD)
- Columna `currency` en `team_members` (default USD)

---

### 3.3 d7dc269bb824 - add_taxes_support

| Campo | Valor |
|-------|-------|
| **Archivo** | `d7dc269bb824_add_taxes_support.py` |
| **Revises** | 362aa60e787f |
| **Descripción** | Impuestos e IVA por proyecto |

**Cambios upgrade:**
- Tabla `taxes` (name, code, percentage, country, is_active, description)
- Tabla `project_taxes` (N:M entre projects y taxes)

---

### 3.4 48d403df0b4b - add_soft_delete_support

| Campo | Valor |
|-------|-------|
| **Archivo** | `48d403df0b4b_add_soft_delete_support.py` |
| **Revises** | d7dc269bb824 |
| **Descripción** | Soft delete en proyectos, servicios, costos e impuestos |

**Cambios upgrade:**
- `projects`: deleted_at, deleted_by_id (FK users)
- `services`: deleted_at, deleted_by_id (FK users)
- `costs_fixed`: deleted_at, deleted_by_id (FK users)
- `taxes`: deleted_at, deleted_by_id (FK users)

---

### 3.5 r20251109_role_varchar - add users.role

| Campo | Valor |
|-------|-------|
| **Archivo** | `20251109_add_user_role_varchar_safe.py` |
| **Revises** | 48d403df0b4b |
| **Descripción** | Columna role en users (VARCHAR 32) |

**Cambios upgrade:**
- Columna `role` en `users` (nullable, default product_manager)
- Índice `ix_users_role`

---

### 3.6 r20251110_user_password - add hashed_password

| Campo | Valor |
|-------|-------|
| **Archivo** | `r20251110_add_user_password_hash.py` |
| **Revises** | r20251109_role_varchar |
| **Descripción** | Contraseña hasheada y usuario admin por defecto |

**Cambios upgrade:**
- Columna `hashed_password` en `users` (String 255)
- Migra usuarios existentes con hash por defecto
- Inserta usuario super_admin si no existe (gerriarte@abralatam.com)

---

### 3.7 dae436c985e8 - add_performance_indexes

| Campo | Valor |
|-------|-------|
| **Archivo** | `dae436c985e8_add_performance_indexes.py` |
| **Revises** | r20251110_user_password |
| **Descripción** | Índices para mejorar rendimiento de consultas |

**Cambios upgrade:**
- Índices en `projects`: status, created_at, status+created_at
- Índices en `quotes`: project_id, created_at
- Índices en `quote_items`: quote_id, service_id
- Índices en `quote_items`: quote_id+service_id (compuesto)

---

### 3.8 a1b2c3d4e5f6 - add_multi_tenant_organization_support

| Campo | Valor |
|-------|-------|
| **Archivo** | `a1b2c3d4e5f6_add_multi_tenant_organization_support.py` |
| **Revises** | dae436c985e8 |
| **Descripción** | Arquitectura multi-tenant con organizations |

**Cambios upgrade:**
- Tabla `organizations` (name, slug, subscription_plan, subscription_status, settings)
- Organización por defecto (id=1, Default Organization)
- Columna `organization_id` en: users, projects, services, costs_fixed, team_members, taxes
- Asignación de registros existentes a org por defecto
- FK e índices composite por organización

---

### 3.9 b2c3d4e5f6a7 - add_industry_templates

| Campo | Valor |
|-------|-------|
| **Archivo** | `b2c3d4e5f6a7_add_industry_templates.py` |
| **Revises** | a1b2c3d4e5f6 |
| **Descripción** | Plantillas de industria para onboarding |

**Cambios upgrade:**
- Tabla `industry_templates` (industry_type, name, description, suggested_roles, suggested_services, suggested_fixed_costs, icon, color)
- Seed: 5 templates (Branding, Web Dev, Audiovisual, Legal/Consultoría, Finanzas)

---

### 3.10 c3d4e5f6a7b8 - add_audit_logs

| Campo | Valor |
|-------|-------|
| **Archivo** | `c3d4e5f6a7b8_add_audit_logs.py` |
| **Revises** | b2c3d4e5f6a7 |
| **Descripción** | Auditoría de acciones críticas |

**Cambios upgrade:**
- Tabla `audit_logs` (user_id, organization_id, action, resource_type, resource_id, ip_address, user_agent, details, status, error_message, created_at)
- Índices para búsqueda eficiente

---

### 3.11 d4e5f6a7b8c9 - add_role_type

| Campo | Valor |
|-------|-------|
| **Archivo** | `d4e5f6a7b8c9_add_role_type.py` |
| **Revises** | c3d4e5f6a7b8 |
| **Descripción** | Tipo de rol: support vs tenant |

**Cambios upgrade:**
- Columna `role_type` en `users` (support | tenant)
- Migración: super_admin → support, resto → tenant
- Índice `ix_users_role_type`

---

### 3.12 8f0817455976 - add_credit_system

| Campo | Valor |
|-------|-------|
| **Archivo** | `8f0817455976_add_credit_system.py` |
| **Revises** | d4e5f6a7b8c9 |
| **Descripción** | Sistema de créditos por organización |

**Cambios upgrade:**
- Tabla `credit_accounts` (credits_available, credits_used_total, credits_per_month, etc.)
- Tabla `credit_transactions` (transaction_type, amount, reason, reference_id)
- FK a organizations y users

---

### 3.13 e5f6a7b8c9d0 - add_invitations

| Campo | Valor |
|-------|-------|
| **Archivo** | `e5f6a7b8c9d0_add_invitations.py` |
| **Revises** | d4e5f6a7b8c9 |
| **Descripción** | Invitaciones a usuarios para unirse a organizaciones |

**Cambios upgrade:**
- Tabla `invitations` (organization_id, email, role, token, expires_at, accepted_at, created_by_id)
- Índice compuesto (organization_id, email)

---

### 3.14 e6f7a8b9c0d1 - add_service_pricing_types

| Campo | Valor |
|-------|-------|
| **Archivo** | `e6f7a8b9c0d1_add_service_pricing_types.py` |
| **Revises** | d4e5f6a7b8c9 |
| **Descripción** | Tipos de precios: hourly, fixed, recurring, project_value (Sprint 14) |

**Cambios upgrade:**
- `services`: pricing_type, fixed_price, is_recurring, billing_frequency, recurring_price
- `team_members`: non_billable_hours_percentage
- `quote_items`: pricing_type, fixed_price, quantity

---

### 3.15 f7a8b9c0d1e2 - add_legal_finance_templates

| Campo | Valor |
|-------|-------|
| **Archivo** | `f7a8b9c0d1e2_add_legal_finance_templates.py` |
| **Revises** | e6f7a8b9c0d1 |
| **Descripción** | Plantillas Legal/Consultoría y Finanzas/Contabilidad |

**Cambios upgrade:**
- Seed de 2 templates adicionales en industry_templates

---

### 3.16 g8h9i0j1k2l3 - add_quote_expenses

| Campo | Valor |
|-------|-------|
| **Archivo** | `g8h9i0j1k2l3_add_quote_expenses.py` |
| **Revises** | f7a8b9c0d1e2 |
| **Descripción** | Gastos de cotización con markup (Sprint 15) |

**Cambios upgrade:**
- Tabla `quote_expenses` (quote_id, name, description, cost, markup_percentage, client_price, category, quantity)

---

### 3.17 h9i0j1k2l3m4 - update_templates_with_expenses

| Campo | Valor |
|-------|-------|
| **Archivo** | `h9i0j1k2l3m4_update_templates_with_expenses.py` |
| **Revises** | g8h9i0j1k2l3 |
| **Descripción** | Actualiza templates (audiovisual, branding) con sugerencias de gastos |

**Cambios upgrade:**
- UPDATE en industry_templates: suggested_fixed_costs con gastos Third Party, Materials, Licenses

---

### 3.18 i0j1k2l3m4n5 - add_quote_revisions

| Campo | Valor |
|-------|-------|
| **Archivo** | `i0j1k2l3m4n5_add_quote_revisions.py` |
| **Revises** | h9i0j1k2l3m4 |
| **Descripción** | Campos de revisiones incluidas (Sprint 16) |

**Cambios upgrade:**
- `quotes`: revisions_included (default 2), revision_cost_per_additional

---

### 3.19 j1k2l3m4n5o6 - update_templates_with_project_value

| Campo | Valor |
|-------|-------|
| **Archivo** | `j1k2l3m4n5o6_update_templates_with_project_value.py` |
| **Revises** | i0j1k2l3m4n5 |
| **Descripción** | Plantillas creativas con servicios project_value (Sprint 16) |

**Cambios upgrade:**
- UPDATE en industry_templates: servicios con pricing_type="project_value" para IP/proyecto

---

### 3.20 5e8453f9fad0 - merge_heads

| Campo | Valor |
|-------|-------|
| **Archivo** | `5e8453f9fad0_merge_heads.py` |
| **Revises** | 8f0817455976, e5f6a7b8c9d0, j1k2l3m4n5o6 |
| **Descripción** | Merge de 3 ramas en una sola |

**Cambios upgrade:** Ninguno (solo unificación del grafo)

---

### 3.21 bfc774065893 - make estimated_hours nullable

| Campo | Valor |
|-------|-------|
| **Archivo** | `bfc774065893_make_estimated_hours_nullable_in_quote_.py` |
| **Revises** | 5e8453f9fad0 |
| **Descripción** | estimated_hours nullable para pricing fixed/recurring |

**Cambios upgrade:**
- `quote_items.estimated_hours`: nullable=True (antes NOT NULL)

---

### 3.22 3b000e90aba6 - add_target_margin_percentage

| Campo | Valor |
|-------|-------|
| **Archivo** | `3b000e90aba6_add_target_margin_percentage_to_quotes.py` |
| **Revises** | bfc774065893 |
| **Descripción** | Margen objetivo en cotizaciones |

**Cambios upgrade:**
- `quotes`: target_margin_percentage (Float, nullable)

---

### 3.23 p1q2r3s4t5u6 - add_quote_allocations_and_contingency

| Campo | Valor |
|-------|-------|
| **Archivo** | `p1q2r3s4t5u6_add_quote_allocations_and_contingency.py` |
| **Revises** | 3b000e90aba6 |
| **Descripción** | Asignaciones de recursos y contingencia en cotizaciones |

**Cambios upgrade:**
- `projects`: client_company
- `quotes`: contingency_description, contingency_type, contingency_value
- `quote_items`: service_name, recurring_price, billing_frequency, duration_months, project_value, manual_price
- Tabla `quote_item_allocations` (quote_item_id, team_member_id, hours, role, start_date, end_date)

---

### 3.24 q2r3s4t5u6v7 - add_quote_public_link_fields ★ HEAD

| Campo | Valor |
|-------|-------|
| **Archivo** | `q2r3s4t5u6v7_add_quote_public_link_fields.py` |
| **Revises** | p1q2r3s4t5u6 |
| **Descripción** | Enlace público y seguimiento de cotizaciones |

**Cambios upgrade:**
- `quotes`: sent_at (DateTime), viewed_count (default 0), public_token (unique)
- Índice único en public_token

---

### 3.25 m20251230 - migrate_money_to_numeric ★ HEAD

| Campo | Valor |
|-------|-------|
| **Archivo** | `m20251230_migrate_money_to_numeric.py` |
| **Revises** | j1k2l3m4n5o6 |
| **Descripción** | Migración Float → Numeric para precisión bancaria (ESTÁNDAR NOUGRAM) |

**Cambios upgrade:**
- `quotes`: total_internal_cost, total_client_price, revision_cost_per_additional → NUMERIC(19,4)
- `quote_items`: estimated_hours, internal_cost, client_price, fixed_price, quantity, recurring_price, project_value, manual_price, margin_percentage → Numeric
- `quote_expenses`: cost, markup_percentage, client_price, quantity → Numeric
- `services`: default_margin_target, fixed_price, recurring_price → Numeric
- `team_members`: salary_monthly_brute, non_billable_hours_percentage → Numeric
- `costs_fixed`: amount_monthly → Numeric
- `taxes`: percentage → Numeric

---

## 4. Comandos útiles

```bash
# Ver estado actual
alembic current

# Ver heads (debe mostrar 2)
alembic heads

# Aplicar todas las migraciones pendientes
alembic upgrade head

# Generar merge de los 2 heads actuales (recomendado antes de nuevos cambios)
alembic merge -m "merge_heads_unify" m20251230 q2r3s4t5u6v7

# Crear nueva migración
alembic revision -m "descripcion_cambio"

# Revertir última migración
alembic downgrade -1

# Historial
alembic history --verbose
```

---

## 5. Dependencias no documentadas

- **subscriptions**: La tabla `subscriptions` no aparece en migraciones; puede estar en otra rama o script manual. El modelo existe en `app.models.subscription`.
- **agency_settings**: No tiene `organization_id`; parece configuración global.
- **annual_sales_projections** / **annual_sales_projection_entries**: Los modelos existen pero no hay migración explícita en el directorio revisado; puede estar en migraciones adicionales no listadas.

---

*Documento generado a partir de `backend/alembic/versions/`.*
