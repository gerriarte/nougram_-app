# Base de Datos - Cotizador

**Fecha:** 14 de febrero de 2026  
**ORM:** SQLAlchemy (async)  
**Motor:** PostgreSQL (producción) / SQLite (desarrollo/pruebas)

---

## 1. Diagrama de Entidad-Relación (ER)

### 1.1 Diagrama textual

```
┌─────────────────────┐
│   organizations     │
│─────────────────────│
│ PK id               │◄──────────────────────────────────────────────┐
│    name             │                                               │
│    slug (UNIQUE)    │                                               │
│    subscription_plan│                                               │
│    subscription_status│                                             │
│    settings (JSONB) │                                               │
│    created_at       │                                               │
│    updated_at       │                                               │
└──────────┬──────────┘                                               │
           │                                                          │
           │ 1:N                                                      │
           ├───────────────┬───────────────┬───────────────┬───────────┼──────────────┬──────────────┬──────────────┬──────────────┬────────────────────┐
           ▼               ▼               ▼               ▼           ▼              ▼              ▼              ▼              ▼                    │
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌──────────────────┐ │
│    users     │ │   projects   │ │   services   │ │ costs_fixed  │ │ team_members│ │   taxes     │ │ subscriptions│ │credit_accounts│ │ credit_transactions│
│──────────────│ │──────────────│ │──────────────│ │──────────────│ │─────────────│ │─────────────│ │─────────────│ │─────────────│ │──────────────────│ │
│ PK id        │ │ PK id        │ │ PK id        │ │ PK id        │ │ PK id       │ │ PK id       │ │ PK id       │ │ PK id       │ │ PK id             │ │
│ FK org_id    │ │ FK org_id    │ │ FK org_id    │ │ FK org_id    │ │ FK org_id   │ │ FK org_id   │ │ FK org_id   │ │ FK org_id   │ │ FK org_id         │──┘
│    email     │ │    name      │ │    name      │ │    name      │ │ FK user_id  │ │    name     │ │ stripe_*    │ │ credits_*   │ │ transaction_type  │
│    ...       │ │    ...       │ │    ...       │ │    ...       │ │    ...      │ │    ...      │ │    ...      │ │    ...      │ │ amount            │
└──────┬───────┘ └──────┬───────┘ └──────┬───────┘ └──────────────┘ └──────┬──────┘ └──────┬──────┘ └─────────────┘ └─────────────┘ └──────────────────┘
       │                │                │                                   │              │
       │                │                │                                   │              │
       │                │                │  N:M (project_taxes)              │              │
       │                └────────────────┼──────────────────────────────────┘              │
       │                                 │                                                   │
       │                ┌────────────────┴────────────┐                                     │
       │                ▼                              ▼                                     │
       │         ┌─────────────┐                ┌─────────────────────┐                     │
       │         │   quotes    │                │   project_taxes      │                     │
       │         │─────────────│                │─────────────────────│                     │
       │         │ PK id       │                │ PK project_id       │                     │
       │         │ FK project_id│               │ PK tax_id            │                     │
       │         │    ...      │                └─────────────────────┘                     │
       │         └──────┬──────┘                                                           │
       │                │                                                                    │
       │                ├────────────────────┬────────────────────┐                         │
       │                ▼                    ▼                    ▼                         │
       │         ┌─────────────┐      ┌──────────────┐     ┌────────────────┐                │
       │         │ quote_items │      │quote_expenses│     │ (QuoteRevision)│                │
       │         │─────────────│      │──────────────│     └────────────────┘                │
       │         │ PK id       │      │ PK id        │                                       │
       │         │ FK quote_id │      │ FK quote_id  │                                       │
       │         │ FK service_id│     │    name      │                                       │
       │         │    ...      │      │    ...       │                                       │
       │         └──────┬──────┘      └──────────────┘                                       │
       │                │                                                                     │
       │                ▼                                                                     │
       │         ┌─────────────────────┐                                                    │
       │         │quote_item_allocations│                                                   │
       │         │─────────────────────│                                                    │
       │         │ PK id               │                                                    │
       │         │ FK quote_item_id    │                                                    │
       │         │ FK team_member_id   │                                                    │
       │         └─────────────────────┘                                                    │
       │                                                                                     │
       ├──────┬──────────────┬──────────────┬──────────────┬──────────────┐                 │
       ▼      ▼              ▼              ▼              ▼              ▼                 │
┌─────────────┐ ┌─────────────┐ ┌──────────────┐ ┌─────────────┐ ┌────────────────────┐   │
│ invitations │ │ audit_logs  │ │ credit_accounts│ │ credit_txn  │ │ annual_sales_*     │   │
│─────────────│ │─────────────│ │──────────────│ │ performed_by │ │ projections        │   │
│ PK id       │ │ PK id       │ │ manual_*_by  │ └─────────────┘ │ created_by_id      │   │
│ FK org_id   │ │ FK user_id  │ └──────────────┘                 └────────────────────┘   │
│ FK created_by│ │ FK org_id   │                                                             │
└─────────────┘ └─────────────┘                                                             │
                                                                                             │
┌─────────────────────┐     ┌──────────────────────────────────┐                          │
│ industry_templates  │     │ equipment_amortization            │                          │
│─────────────────────│     │──────────────────────────────────│                          │
│ PK id               │     │ PK id                             │                          │
│ (sin FK - global)   │     │ FK organization_id                │◄────────────────────────┘
│ industry_type       │     │ FK deleted_by_id                   │
└─────────────────────┘     └──────────────────────────────────┘
```

### 1.2 Jerarquía Multi-Tenant

Todas las entidades operativas están asociadas a `organization_id` para aislamiento multi-tenant:

- **Organizations** → entidad raíz (tenant)
- **Users** → pueden pertenecer a una organización (role_type="tenant") o ser soporte (role_type="support", org_id NULL)
- **Projects, Services, Taxes, TeamMembers, CostsFixed** → scoped por organización
- **Quotes, QuoteItems, QuoteExpenses** → heredan scope vía Project
- **CreditAccount, Subscriptions, Invitations, AuditLogs, AnnualSalesProjections** → por organización
- **EquipmentAmortization** → por organización
- **IndustryTemplates** → entidad global (sin organización)

---

## 2. Diccionario de Datos

### 2.1 organizations

| Campo | Tipo | Null | Default | Descripción |
|-------|------|------|---------|-------------|
| id | INTEGER | NO | SERIAL | PK |
| name | VARCHAR | NO | - | Nombre de la organización |
| slug | VARCHAR | NO | - | Identificador único (URL-friendly) |
| subscription_plan | VARCHAR | NO | 'free' | Plan: free, starter, professional, enterprise |
| subscription_status | VARCHAR | NO | 'active' | Estado: active, cancelled, past_due, trialing |
| settings | JSONB | SÍ | NULL | Configuración específica del tenant |
| created_at | TIMESTAMPTZ | NO | now() | |
| updated_at | TIMESTAMPTZ | SÍ | - | |

**Índices:** id, name, slug (UNIQUE)

---

### 2.2 users

| Campo | Tipo | Null | Default | Descripción |
|-------|------|------|---------|-------------|
| id | INTEGER | NO | SERIAL | PK |
| email | VARCHAR | NO | - | Email único |
| full_name | VARCHAR | NO | - | Nombre completo |
| hashed_password | VARCHAR(255) | NO | - | Contraseña hasheada |
| google_refresh_token | VARCHAR | SÍ | NULL | Token OAuth Google (encriptado) |
| role | VARCHAR(32) | SÍ | NULL | Rol (string-based) |
| role_type | VARCHAR(16) | SÍ | NULL | "support" o "tenant" |
| organization_id | INTEGER | SÍ | NULL | FK → organizations.id (NULL si support) |
| created_at | - | - | - | *(si existe en migraciones)* |
| updated_at | - | - | - | *(si existe en migraciones)* |

**FK:** organization_id → organizations(id)

**Índices:** id, email (UNIQUE), role, role_type, organization_id

---

### 2.3 projects

| Campo | Tipo | Null | Default | Descripción |
|-------|------|------|---------|-------------|
| id | INTEGER | NO | SERIAL | PK |
| name | VARCHAR | NO | - | Nombre del proyecto |
| client_name | VARCHAR | NO | - | Cliente |
| client_email | VARCHAR | SÍ | NULL | Email del cliente |
| client_company | VARCHAR | SÍ | NULL | Empresa del cliente |
| status | VARCHAR | NO | 'Draft' | Draft, Sent, Won, Lost |
| currency | VARCHAR | NO | 'USD' | USD, COP, ARS, EUR |
| created_at | TIMESTAMPTZ | NO | now() | |
| updated_at | TIMESTAMPTZ | SÍ | - | |
| deleted_at | TIMESTAMPTZ | SÍ | NULL | Soft delete |
| deleted_by_id | INTEGER | SÍ | NULL | FK → users.id |
| organization_id | INTEGER | SÍ | NULL | FK → organizations.id |

**FK:** deleted_by_id → users(id), organization_id → organizations(id)

**Relaciones:** quotes, taxes (N:M), deleted_by

---

### 2.4 project_taxes (tabla asociación N:M)

| Campo | Tipo | Null | Descripción |
|-------|------|------|-------------|
| project_id | INTEGER | NO | PK, FK → projects.id |
| tax_id | INTEGER | NO | PK, FK → taxes.id |

---

### 2.5 quotes

| Campo | Tipo | Null | Default | Descripción |
|-------|------|------|---------|-------------|
| id | INTEGER | NO | SERIAL | PK |
| project_id | INTEGER | NO | - | FK → projects.id |
| version | INTEGER | NO | 1 | Versión de cotización |
| total_internal_cost | NUMERIC(19,4) | SÍ | NULL | Costo total interno |
| total_client_price | NUMERIC(19,4) | SÍ | NULL | Precio total al cliente |
| margin_percentage | NUMERIC(10,4) | SÍ | NULL | Margen resultante |
| target_margin_percentage | NUMERIC(10,4) | SÍ | NULL | Margen objetivo (0.40 = 40%) |
| notes | VARCHAR | SÍ | NULL | |
| created_at | TIMESTAMPTZ | NO | now() | |
| updated_at | TIMESTAMPTZ | SÍ | - | |
| revisions_included | INTEGER | NO | 2 | Revisiones incluidas |
| revision_cost_per_additional | NUMERIC(19,4) | SÍ | NULL | Costo por revisión adicional |
| contingency_description | VARCHAR | SÍ | NULL | |
| contingency_type | VARCHAR | SÍ | NULL | 'fixed' o 'percentage' |
| contingency_value | NUMERIC(19,4) | SÍ | NULL | |
| sent_at | TIMESTAMPTZ | SÍ | NULL | Fecha de envío |
| viewed_count | INTEGER | NO | 0 | Veces abierto por cliente |
| public_token | VARCHAR | SÍ | NULL | Token acceso público (UNIQUE) |

**FK:** project_id → projects(id)

---

### 2.6 quote_items

| Campo | Tipo | Null | Default | Descripción |
|-------|------|------|---------|-------------|
| id | INTEGER | NO | SERIAL | PK |
| quote_id | INTEGER | NO | - | FK → quotes.id |
| service_id | INTEGER | NO | - | FK → services.id |
| service_name | VARCHAR | SÍ | NULL | Nombre custom (override) |
| estimated_hours | NUMERIC(10,4) | SÍ | NULL | Horas estimadas |
| internal_cost | NUMERIC(19,4) | SÍ | NULL | Costo interno |
| client_price | NUMERIC(19,4) | SÍ | NULL | Precio cliente |
| margin_percentage | NUMERIC(10,4) | SÍ | NULL | |
| pricing_type | VARCHAR | SÍ | NULL | hourly, fixed, recurring, project_value |
| fixed_price | NUMERIC(19,4) | SÍ | NULL | |
| quantity | NUMERIC(10,4) | NO | 1.0 | |
| recurring_price | NUMERIC(19,4) | SÍ | NULL | |
| billing_frequency | VARCHAR | SÍ | NULL | monthly, annual |
| duration_months | INTEGER | SÍ | NULL | |
| project_value | NUMERIC(19,4) | SÍ | NULL | |
| manual_price | NUMERIC(19,4) | SÍ | NULL | Override manual |

**FK:** quote_id → quotes(id), service_id → services(id)

---

### 2.7 quote_item_allocations

| Campo | Tipo | Null | Default | Descripción |
|-------|------|------|---------|-------------|
| id | INTEGER | NO | SERIAL | PK |
| quote_item_id | INTEGER | NO | - | FK → quote_items.id |
| team_member_id | INTEGER | NO | - | FK → team_members.id |
| hours | NUMERIC(10,4) | NO | - | Horas asignadas |
| role | VARCHAR | SÍ | NULL | Rol override |
| start_date | TIMESTAMPTZ | SÍ | NULL | |
| end_date | TIMESTAMPTZ | SÍ | NULL | |
| created_at | TIMESTAMPTZ | NO | now() | |

**FK:** quote_item_id → quote_items(id), team_member_id → team_members(id)

---

### 2.8 quote_expenses

| Campo | Tipo | Null | Default | Descripción |
|-------|------|------|---------|-------------|
| id | INTEGER | NO | SERIAL | PK |
| quote_id | INTEGER | NO | - | FK → quotes.id |
| name | VARCHAR | NO | - | Nombre del gasto |
| description | VARCHAR | SÍ | NULL | |
| cost | NUMERIC(19,4) | NO | - | Costo real |
| markup_percentage | NUMERIC(10,4) | NO | 0 | Mark-up (0.10 = 10%) |
| client_price | NUMERIC(19,4) | NO | - | Precio al cliente |
| category | VARCHAR | SÍ | NULL | Third Party, Materials, Licenses |
| quantity | NUMERIC(10,4) | NO | 1.0 | |
| created_at | TIMESTAMPTZ | NO | now() | |

**FK:** quote_id → quotes(id)

---

### 2.9 services

| Campo | Tipo | Null | Default | Descripción |
|-------|------|------|---------|-------------|
| id | INTEGER | NO | SERIAL | PK |
| name | VARCHAR | NO | - | |
| description | VARCHAR | SÍ | NULL | |
| default_margin_target | NUMERIC(10,4) | NO | 0.40 | Margen objetivo 40% |
| is_active | BOOLEAN | NO | true | |
| pricing_type | VARCHAR | NO | 'hourly' | hourly, fixed, recurring, project_value |
| fixed_price | NUMERIC(19,4) | SÍ | NULL | |
| is_recurring | BOOLEAN | NO | false | |
| billing_frequency | VARCHAR | SÍ | NULL | monthly, annual |
| recurring_price | NUMERIC(19,4) | SÍ | NULL | |
| created_at | TIMESTAMPTZ | NO | now() | |
| updated_at | TIMESTAMPTZ | SÍ | - | |
| deleted_at | TIMESTAMPTZ | SÍ | NULL | Soft delete |
| deleted_by_id | INTEGER | SÍ | NULL | FK → users.id |
| organization_id | INTEGER | SÍ | NULL | FK → organizations.id |

**FK:** deleted_by_id → users(id), organization_id → organizations(id)

---

### 2.10 taxes

| Campo | Tipo | Null | Default | Descripción |
|-------|------|------|---------|-------------|
| id | INTEGER | NO | SERIAL | PK |
| name | VARCHAR | NO | - | ej: IVA, Transaction Cost |
| code | VARCHAR | NO | - | UNIQUE, ej: IVA_CO, TX_AR |
| percentage | NUMERIC(10,4) | NO | 0 | Porcentaje (19.0 = 19%) |
| country | VARCHAR | SÍ | NULL | Código país CO, AR, US |
| is_active | BOOLEAN | NO | true | |
| description | VARCHAR | SÍ | NULL | |
| created_at | TIMESTAMPTZ | NO | now() | |
| updated_at | TIMESTAMPTZ | SÍ | - | |
| deleted_at | TIMESTAMPTZ | SÍ | NULL | Soft delete |
| deleted_by_id | INTEGER | SÍ | NULL | FK → users.id |
| organization_id | INTEGER | SÍ | NULL | FK → organizations.id |

**FK:** deleted_by_id → users(id), organization_id → organizations(id)

---

### 2.11 team_members

| Campo | Tipo | Null | Default | Descripción |
|-------|------|------|---------|-------------|
| id | INTEGER | NO | SERIAL | PK |
| user_id | INTEGER | SÍ | NULL | FK → users.id (vinculación opcional) |
| name | VARCHAR | NO | - | |
| role | VARCHAR | NO | - | Rol/posición |
| salary_monthly_brute | NUMERIC(19,4) | NO | - | Salario bruto mensual |
| currency | VARCHAR | NO | 'USD' | |
| billable_hours_per_week | INTEGER | NO | 32 | Horas facturables/semana |
| non_billable_hours_percentage | NUMERIC(10,4) | NO | 0 | % tiempo no facturable |
| is_active | BOOLEAN | NO | true | |
| created_at | TIMESTAMPTZ | NO | now() | |
| updated_at | TIMESTAMPTZ | SÍ | - | |
| organization_id | INTEGER | SÍ | NULL | FK → organizations.id |

**FK:** user_id → users(id), organization_id → organizations(id)

---

### 2.12 costs_fixed

| Campo | Tipo | Null | Default | Descripción |
|-------|------|------|---------|-------------|
| id | INTEGER | NO | SERIAL | PK |
| name | VARCHAR | NO | - | |
| amount_monthly | NUMERIC(19,4) | NO | - | Costo fijo mensual |
| currency | VARCHAR | NO | 'USD' | |
| category | VARCHAR | NO | - | Overhead, Software, etc. |
| description | VARCHAR | SÍ | NULL | |
| created_at | TIMESTAMPTZ | NO | now() | |
| updated_at | TIMESTAMPTZ | SÍ | - | |
| deleted_at | TIMESTAMPTZ | SÍ | NULL | Soft delete |
| deleted_by_id | INTEGER | SÍ | NULL | FK → users.id |
| organization_id | INTEGER | SÍ | NULL | FK → organizations.id |

**FK:** deleted_by_id → users(id), organization_id → organizations(id)

---

### 2.13 industry_templates

| Campo | Tipo | Null | Default | Descripción |
|-------|------|------|---------|-------------|
| id | INTEGER | NO | SERIAL | PK |
| industry_type | VARCHAR | NO | - | UNIQUE. branding, web_development, etc. |
| name | VARCHAR | NO | - | ej: Agencia de Branding |
| description | TEXT | SÍ | NULL | |
| suggested_roles | JSON/JSONB | SÍ | NULL | Array de roles sugeridos |
| suggested_services | JSON/JSONB | SÍ | NULL | Array de servicios sugeridos |
| suggested_fixed_costs | JSON/JSONB | SÍ | NULL | Array de costos fijos |
| is_active | BOOLEAN | NO | true | |
| icon | VARCHAR | SÍ | NULL | Icono UI |
| color | VARCHAR | SÍ | NULL | Color UI |
| created_at | TIMESTAMPTZ | NO | now() | |
| updated_at | TIMESTAMPTZ | SÍ | - | |

**Sin organization_id** — entidad global para onboarding.

---

### 2.14 invitations

| Campo | Tipo | Null | Default | Descripción |
|-------|------|------|---------|-------------|
| id | INTEGER | NO | SERIAL | PK |
| organization_id | INTEGER | NO | - | FK → organizations.id |
| email | VARCHAR | NO | - | Email invitado |
| role | VARCHAR(32) | NO | - | Rol a asignar |
| token | VARCHAR(255) | NO | - | UNIQUE, para aceptar |
| expires_at | TIMESTAMPTZ | NO | - | |
| accepted_at | TIMESTAMPTZ | SÍ | NULL | |
| created_by_id | INTEGER | NO | - | FK → users.id |
| created_at | TIMESTAMPTZ | NO | now() | |
| updated_at | TIMESTAMPTZ | SÍ | - | |

**FK:** organization_id → organizations(id), created_by_id → users(id)

**Índice:** (organization_id, email)

---

### 2.15 audit_logs

| Campo | Tipo | Null | Default | Descripción |
|-------|------|------|---------|-------------|
| id | INTEGER | NO | SERIAL | PK |
| user_id | INTEGER | SÍ | NULL | FK → users.id |
| organization_id | INTEGER | SÍ | NULL | FK → organizations.id |
| action | VARCHAR(100) | NO | - | user.login, project.create, etc. |
| resource_type | VARCHAR(50) | SÍ | NULL | project, user, subscription |
| resource_id | INTEGER | SÍ | NULL | ID del recurso |
| ip_address | VARCHAR(45) | SÍ | NULL | IPv4/IPv6 |
| user_agent | VARCHAR(500) | SÍ | NULL | |
| details | TEXT | SÍ | NULL | JSON o texto |
| status | VARCHAR(20) | NO | 'success' | success, failure, error |
| error_message | TEXT | SÍ | NULL | |
| created_at | TIMESTAMPTZ | NO | now() | |

**FK:** user_id → users(id), organization_id → organizations(id)

---

### 2.16 credit_accounts

| Campo | Tipo | Null | Default | Descripción |
|-------|------|------|---------|-------------|
| id | INTEGER | NO | SERIAL | PK |
| organization_id | INTEGER | NO | - | FK → organizations.id (UNIQUE) |
| credits_available | INTEGER | NO | 0 | Créditos disponibles |
| credits_used_total | INTEGER | NO | 0 | Total usados históricos |
| credits_used_this_month | INTEGER | NO | 0 | Usados este mes |
| credits_per_month | INTEGER | SÍ | NULL | Asignación mensual (NULL = ilimitado) |
| last_reset_at | TIMESTAMPTZ | SÍ | NULL | |
| next_reset_at | TIMESTAMPTZ | SÍ | NULL | |
| manual_credits_bonus | INTEGER | NO | 0 | |
| manual_credits_last_assigned_at | TIMESTAMPTZ | SÍ | NULL | |
| manual_credits_assigned_by | INTEGER | SÍ | NULL | FK → users.id |
| created_at | TIMESTAMPTZ | NO | now() | |
| updated_at | TIMESTAMPTZ | SÍ | - | |

**FK:** organization_id → organizations(id), manual_credits_assigned_by → users(id)

**Relación:** 1:1 con Organization

---

### 2.17 credit_transactions

| Campo | Tipo | Null | Default | Descripción |
|-------|------|------|---------|-------------|
| id | INTEGER | NO | SERIAL | PK |
| organization_id | INTEGER | NO | - | FK → organizations.id |
| transaction_type | VARCHAR(32) | NO | - | subscription_grant, manual_adjustment, consumption, refund |
| amount | INTEGER | NO | - | Positivo = agregado, negativo = consumido |
| reason | TEXT | SÍ | NULL | Motivo legible |
| reference_id | INTEGER | SÍ | NULL | ID quote/proyecto relacionado |
| performed_by | INTEGER | SÍ | NULL | FK → users.id |
| created_at | TIMESTAMPTZ | NO | now() | |

**FK:** organization_id → organizations(id), performed_by → users(id)

---

### 2.18 subscriptions

| Campo | Tipo | Null | Default | Descripción |
|-------|------|------|---------|-------------|
| id | INTEGER | NO | SERIAL | PK |
| organization_id | INTEGER | NO | - | FK → organizations.id |
| stripe_subscription_id | VARCHAR | SÍ | NULL | UNIQUE |
| stripe_customer_id | VARCHAR | SÍ | NULL | |
| stripe_price_id | VARCHAR | SÍ | NULL | |
| plan | VARCHAR | NO | - | free, starter, professional, enterprise |
| status | VARCHAR | NO | - | active, cancelled, past_due, trialing, incomplete |
| current_period_start | TIMESTAMPTZ | SÍ | NULL | |
| current_period_end | TIMESTAMPTZ | SÍ | NULL | |
| cancel_at_period_end | BOOLEAN | NO | false | |
| canceled_at | TIMESTAMPTZ | SÍ | NULL | |
| latest_invoice_id | VARCHAR | SÍ | NULL | |
| default_payment_method | VARCHAR | SÍ | NULL | |
| trial_start | TIMESTAMPTZ | SÍ | NULL | |
| trial_end | TIMESTAMPTZ | SÍ | NULL | |
| stripe_metadata | JSON/JSONB | SÍ | NULL | |
| created_at | TIMESTAMPTZ | NO | now() | |
| updated_at | TIMESTAMPTZ | SÍ | - | |

**FK:** organization_id → organizations(id)

---

### 2.19 annual_sales_projections

| Campo | Tipo | Null | Default | Descripción |
|-------|------|------|---------|-------------|
| id | INTEGER | NO | SERIAL | PK |
| organization_id | INTEGER | NO | - | FK → organizations.id |
| year | INTEGER | NO | - | Año de proyección |
| is_active | BOOLEAN | NO | true | |
| notes | VARCHAR | SÍ | NULL | |
| created_at | TIMESTAMPTZ | NO | now() | |
| updated_at | TIMESTAMPTZ | SÍ | - | |
| created_by_id | INTEGER | NO | - | FK → users.id |

**FK:** organization_id → organizations(id), created_by_id → users(id)

**Unique:** (organization_id, year)

---

### 2.20 annual_sales_projection_entries

| Campo | Tipo | Null | Default | Descripción |
|-------|------|------|---------|-------------|
| id | INTEGER | NO | SERIAL | PK |
| projection_id | INTEGER | NO | - | FK → annual_sales_projections.id |
| service_id | INTEGER | NO | - | FK → services.id |
| month | INTEGER | NO | - | 1-12 |
| quantity | INTEGER | NO | 0 | Cantidad de servicios |
| hours_per_unit | FLOAT | NO | 0.0 | Horas por unidad |
| created_at | TIMESTAMPTZ | NO | now() | |
| updated_at | TIMESTAMPTZ | SÍ | - | |

**FK:** projection_id → annual_sales_projections(id), service_id → services.id

**Unique:** (projection_id, service_id, month)

---

### 2.21 agency_settings

| Campo | Tipo | Null | Default | Descripción |
|-------|------|------|---------|-------------|
| id | INTEGER | NO | SERIAL | PK |
| primary_currency | VARCHAR | NO | 'USD' | USD, COP, ARS, EUR |
| currency_symbol | VARCHAR | NO | '$' | |
| created_at | TIMESTAMPTZ | NO | now() | |
| updated_at | TIMESTAMPTZ | SÍ | - | |

---

### 2.22 equipment_amortization

| Campo | Tipo | Null | Default | Descripción |
|-------|------|------|---------|-------------|
| id | INTEGER | NO | SERIAL | PK |
| name | VARCHAR | NO | - | |
| description | VARCHAR | SÍ | NULL | |
| category | VARCHAR | NO | - | Hardware, Software, Vehicles, Office Equipment |
| purchase_price | NUMERIC(15,2) | NO | - | |
| purchase_date | DATE | NO | - | |
| currency | VARCHAR(3) | NO | - | |
| exchange_rate_at_purchase | NUMERIC(10,4) | SÍ | NULL | TRM histórica |
| useful_life_months | INTEGER | NO | - | |
| salvage_value | NUMERIC(15,2) | NO | 0 | Valor de salvamento |
| depreciation_method | VARCHAR | NO | - | straight_line, declining_balance |
| is_active | BOOLEAN | NO | true | |
| created_at | TIMESTAMPTZ | NO | now() | |
| updated_at | TIMESTAMPTZ | SÍ | - | |
| organization_id | INTEGER | NO | - | FK → organizations.id |
| deleted_at | TIMESTAMPTZ | SÍ | NULL | Soft delete |
| deleted_by_id | INTEGER | SÍ | NULL | FK → users.id |

**FK:** organization_id → organizations(id), deleted_by_id → users(id)

---

## 3. Convenciones y estándares

| Aspecto | Convención |
|---------|------------|
| Valores monetarios | `NUMERIC(19,4)` o `NUMERIC(15,2)` |
| Porcentajes | `NUMERIC(10,4)` (0.40 = 40%) |
| Soft delete | `deleted_at`, `deleted_by_id` |
| Multi-tenant | `organization_id` en entidades operativas |
| Nombres de tablas | snake_case, plural |
| Clases modelo | PascalCase |
| Timestamps | `created_at`, `updated_at` con `TIMESTAMPTZ` |
| Cascade | `cascade="all, delete-orphan"` en relaciones fuertes |

---

## 4. Migraciones (Alembic)

Las migraciones se encuentran en `backend/alembic/versions/`. Orden aproximado de revisiones relevantes:

- `dae436c985e8` — Índices de performance
- `a1b2c3d4e5f6` — Multi-tenant (organizations)
- `e5f6a7b8c9d0` — Invitations
- `8f0817455976` — Sistema de créditos
- `c3d4e5f6a7b8` — Audit logs
- `g8h9i0j1k2l3` — Quote expenses
- `p1q2r3s4t5u6` — Quote allocations y contingency
- `q2r3s4t5u6v7` — Quote public link fields
- `i0j1k2l3m4n5` — Quote revisions
- Entre otras

---

*Documento generado a partir de los modelos en `backend/app/models/`.*
