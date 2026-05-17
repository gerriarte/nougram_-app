# Guía de Integración Frontend - API Backend

**Versión:** 1.0  
**Fecha:** 2026-01-23  
**Base URL:** `http://localhost:8000/api/v1` (desarrollo) / `https://api.nougram.com/api/v1` (producción)

## Tabla de Contenidos

1. [Configuración Base](#configuración-base)
2. [Autenticación y Autorización](#autenticación-y-autorización)
3. [Módulos Principales](#módulos-principales)
   - [Proyectos y Cotizaciones](#-proyectos-y-cotizaciones)
   - [Servicios](#️-servicios)
   - [Equipo (Team Members)](#-equipo-team-members)
   - [Costos Fijos](#-costos-fijos)
   - [Impuestos (Taxes)](#-impuestos-taxes)
   - [Organizaciones](#-organizaciones)
   - [Créditos](#-créditos)
   - [Inteligencia Artificial](#-inteligencia-artificial)
   - [Dashboard e Insights](#-dashboard-e-insights)
   - [Invitaciones](#-invitaciones)
   - [Soporte (Support Roles)](#️-soporte-support-roles)
   - [Mantenimiento](#-mantenimiento)
   - [Gastos de Cotización (Expenses)](#-gastos-de-cotización-expenses)
   - [Integraciones](#-integraciones)
   - [Facturación y Suscripciones](#-facturación-y-suscripciones)
   - [Plantillas de Industria](#-plantillas-de-industria)
   - [Proyecciones](#-proyecciones)
   - [Configuración](#️-configuración)
4. [Manejo de Errores](#manejo-de-errores)
5. [Permisos y Roles](#permisos-y-roles)
6. [Multi-Tenancy](#multi-tenancy)
7. [Tipos TypeScript](#tipos-typescript)

---

## Configuración Base

### Variables de Entorno

```typescript
// frontend/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

### Cliente API Base

El proyecto ya incluye un cliente API configurado en `frontend/src/lib/api-client.ts` que:
- Maneja tokens JWT automáticamente
- Transforma Decimal strings a objetos Money
- Maneja errores y traducciones
- Implementa retry con exponential backoff

### Headers Requeridos

Todas las peticiones autenticadas requieren:

```typescript
{
  "Authorization": "Bearer <access_token>",
  "Content-Type": "application/json"
}
```

---

## Autenticación y Autorización

### 1. Login (Email/Password)

**Endpoint:** `POST /auth/login`

**Request:**
```typescript
interface LoginRequest {
  email: string;
  password: string;
}
```

**Response:**
```typescript
interface TokenResponse {
  access_token: string;
  token_type: "bearer";
  expires_in: number; // segundos
  user: {
    id: number;
    email: string;
    full_name: string;
    role: string;
    organization_id: number | null;
  };
}
```

**Ejemplo:**
```typescript
const response = await apiRequest<TokenResponse>('/auth/login', {
  method: 'POST',
  body: JSON.stringify({ email: 'user@example.com', password: 'password123' })
});

// Guardar token
localStorage.setItem('auth_token', response.data!.access_token);
```

**Rate Limit:** 5 intentos por minuto por IP

### 2. Obtener Usuario Actual

**Endpoint:** `GET /auth/me`

**Response:**
```typescript
interface UserResponse {
  id: number;
  email: string;
  full_name: string;
  has_calendar_connected: boolean;
  role: string; // "owner" | "admin_financiero" | "product_manager" | "collaborator" | "super_admin"
  organization_id: number | null;
}
```

### 3. Actualizar Perfil

**Endpoint:** `PUT /auth/me`

**Request:**
```typescript
interface UserUpdate {
  full_name: string;
}
```

### 4. Cambiar Organización (Multi-tenant)

**Endpoint:** `POST /auth/switch-organization`

**Request:**
```typescript
interface SwitchOrganizationRequest {
  organization_id: number;
}
```

**Response:** Nuevo `TokenResponse` con token actualizado

---

## Módulos Principales

### 📁 Proyectos y Cotizaciones

#### Listar Proyectos

**Endpoint:** `GET /projects/`

**Query Parameters:**
- `status_filter` (opcional): "Draft" | "Sent" | "Won" | "Lost"
- `include_deleted` (opcional): boolean (default: false)
- `page` (opcional): number (default: 1)
- `page_size` (opcional): number (default: 20, max: 100)

**Response:**
```typescript
interface ProjectListResponse {
  items: ProjectResponse[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

interface ProjectResponse {
  id: number;
  name: string;
  client_name: string;
  client_email: string | null;
  status: string;
  currency: string;
  tax_ids: number[];
  taxes: Array<{
    id: number;
    name: string;
    code: string;
    percentage: string; // Decimal como string
  }>;
  created_at: string | null;
  updated_at: string | null;
}
```

**Permisos:** Todos los usuarios autenticados

#### Crear Proyecto con Cotización Inicial

**Endpoint:** `POST /projects/`

**Request:**
```typescript
interface ProjectCreateWithQuote {
  name: string;
  client_name: string;
  client_email?: string;
  currency: string; // "USD" | "COP" | "ARS" | "EUR"
  tax_ids?: number[];
  quote_items: QuoteItemCreate[];
}

interface QuoteItemCreate {
  service_id: number;
  estimated_hours?: number; // Requerido para pricing_type "hourly"
  pricing_type?: "hourly" | "fixed" | "recurring" | "project_value";
  fixed_price?: string; // Decimal como string, requerido para "fixed"
  quantity?: string; // Decimal como string (default: "1.0")
  recurring_price?: string; // Decimal como string, requerido para "recurring"
  billing_frequency?: "monthly" | "annual"; // Requerido para "recurring"
  project_value?: string; // Decimal como string, requerido para "project_value"
}
```

**Response:**
```typescript
interface QuoteResponseWithItems {
  project_id: number;
  id: number; // Quote ID
  version: number;
  total_internal_cost: string; // Decimal como string
  total_client_price: string; // Decimal como string
  margin_percentage: string; // Decimal como string (0-1)
  target_margin_percentage: string | null;
  items: QuoteItemResponse[];
  expenses: QuoteExpenseResponse[];
  taxes: Array<{
    id: number;
    name: string;
    amount: string; // Decimal como string
  }>;
  revisions_included: number;
  revision_cost_per_additional: string | null;
}
```

**Permisos:** Requiere `can_create_projects`
- ✅ Roles permitidos: owner, admin_financiero, product_manager, collaborator, super_admin
- ⚠️ Consume créditos según el rol del usuario

**Ejemplo:**
```typescript
const projectData: ProjectCreateWithQuote = {
  name: "Sitio Web Corporativo",
  client_name: "Acme Corp",
  client_email: "contact@acme.com",
  currency: "USD",
  tax_ids: [1],
  quote_items: [
    {
      service_id: 1,
      estimated_hours: 40,
      pricing_type: "hourly"
    }
  ]
};

const response = await apiRequest<QuoteResponseWithItems>('/projects/', {
  method: 'POST',
  body: JSON.stringify(projectData)
});
```

#### Obtener Proyecto por ID

**Endpoint:** `GET /projects/{project_id}`

**Response:** `ProjectResponse`

#### Actualizar Proyecto

**Endpoint:** `PUT /projects/{project_id}`

**Request:**
```typescript
interface ProjectUpdate {
  name?: string;
  client_name?: string;
  client_email?: string;
  status?: string;
  currency?: string;
  tax_ids?: number[];
}
```

#### Eliminar Proyecto (Soft Delete)

**Endpoint:** `DELETE /projects/{project_id}`

**Response:** `204 No Content`

**Permisos:** Requiere `can_delete_resources`
- ✅ Roles permitidos: owner, super_admin

#### Listar Cotizaciones de un Proyecto

**Endpoint:** `GET /projects/{project_id}/quotes`

**Response:**
```typescript
interface QuoteListResponse {
  items: QuoteResponse[];
  total: number;
}
```

#### Crear Nueva Versión de Cotización

**Endpoint:** `POST /projects/{project_id}/quotes`

**Request:**
```typescript
interface QuoteCreateNewVersion {
  items: QuoteItemCreate[];
  notes?: string;
  target_margin_percentage?: string; // Decimal como string (0-1)
  revisions_included?: number;
  revision_cost_per_additional?: string; // Decimal como string
}
```

**Response:** `QuoteResponseWithItems`

#### Actualizar Cotización

**Endpoint:** `PUT /projects/{project_id}/quotes/{quote_id}`

**Request:** `QuoteCreateNewVersion`

**Response:** `QuoteResponseWithItems`

#### Calcular Cotización (Preview)

**Endpoint:** `POST /quotes/calculate`

**Request:**
```typescript
interface QuoteCalculateRequest {
  items: QuoteItemCreate[];
  currency: string;
  tax_ids?: number[];
  target_margin_percentage?: string; // Decimal como string (0-1)
}
```

**Response:**
```typescript
interface QuoteCalculateResponse {
  total_internal_cost: string; // Decimal como string
  total_client_price: string; // Decimal como string
  total_expenses_cost: string;
  total_expenses_client_price: string;
  total_taxes: string;
  total_with_taxes: string;
  margin_percentage: string; // Decimal como string (0-1)
  target_margin_percentage: string | null;
  items: Array<{
    service_id: number;
    service_name: string;
    internal_cost: string;
    client_price: string;
    margin_percentage: string;
    estimated_hours?: number;
    pricing_type: string;
  }>;
  expenses: QuoteExpenseResponse[];
  taxes: Array<{
    id: number;
    name: string;
    amount: string;
  }>;
  revisions_cost: string;
  revisions_included: number;
  revisions_count?: number;
}
```

**Permisos:** Requiere `can_create_quotes`

#### Enviar Cotización por Email

**Endpoint:** `POST /projects/{project_id}/quotes/{quote_id}/send-email`

**Request:**
```typescript
interface QuoteEmailRequest {
  to_email: string;
  subject?: string;
  message?: string;
}
```

**Response:**
```typescript
interface QuoteEmailResponse {
  success: boolean;
  message: string;
}
```

**Permisos:** Requiere `can_send_quotes`
- ✅ Roles permitidos: owner, admin_financiero, product_manager, super_admin
- ❌ Denegado: collaborator

#### Exportar Cotización a PDF

**Endpoint:** `GET /projects/{project_id}/quotes/{quote_id}/pdf`

**Response:** `application/pdf` (streaming)

#### Obtener Rentabilidad de Cotización

**Endpoint:** `GET /quotes/{quote_id}/rentability`

**Response:**
```typescript
interface RentabilitySummaryResponse {
  total_internal_cost: string;
  total_client_price: string;
  net_profit: string;
  margin_percentage: string;
  cost_breakdown: {
    talent_cost: string;
    overhead_cost: string;
    saas_cost: string;
    variable_cost: string;
  };
  tax_burden: string;
}
```

---

### 🛠️ Servicios

#### Listar Servicios

**Endpoint:** `GET /services/`

**Query Parameters:**
- `active_only` (opcional): boolean (default: false)
- `include_deleted` (opcional): boolean (default: false)
- `page` (opcional): number (default: 1)
- `page_size` (opcional): number (default: 20, max: 100)

**Response:**
```typescript
interface ServiceListResponse {
  items: ServiceResponse[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

interface ServiceResponse {
  id: number;
  name: string;
  description: string | null;
  default_margin_target: string; // Decimal como string (0-1)
  is_active: boolean;
  pricing_type: string; // "hourly" | "fixed" | "recurring" | "project_value"
  fixed_price: string | null; // Decimal como string
  is_recurring: boolean | null;
  billing_frequency: string | null; // "monthly" | "annual"
  recurring_price: string | null; // Decimal como string
  created_at: string | null;
  updated_at: string | null;
}
```

#### Crear Servicio

**Endpoint:** `POST /services/`

**Request:**
```typescript
interface ServiceCreate {
  name: string;
  description?: string;
  default_margin_target?: string; // Decimal como string (0-1), default: "0.40"
  is_active?: boolean; // default: true
  pricing_type?: string; // default: "hourly"
  fixed_price?: string; // Decimal como string
  is_recurring?: boolean; // default: false
  billing_frequency?: string; // "monthly" | "annual"
  recurring_price?: string; // Decimal como string
}
```

**Permisos:** Requiere `can_create_services`
- ✅ Roles permitidos: owner, admin_financiero, super_admin
- ❌ Denegado: product_manager, collaborator
- ⚠️ Valida límites del plan de suscripción

#### Actualizar Servicio

**Endpoint:** `PUT /services/{service_id}`

**Request:** `ServiceCreate` (todos los campos opcionales)

#### Eliminar Servicio (Soft Delete)

**Endpoint:** `DELETE /services/{service_id}`

**Response:** `204 No Content`

**Permisos:** Requiere `can_delete_resources`

---

### 👥 Equipo (Team Members)

#### Listar Miembros del Equipo

**Endpoint:** `GET /settings/team`

**Query Parameters:**
- `page` (opcional): number (default: 1)
- `page_size` (opcional): number (default: 20, max: 100)

**Response:**
```typescript
interface TeamMemberListResponse {
  items: TeamMemberResponse[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

interface TeamMemberResponse {
  id: number;
  name: string;
  role: string;
  salary_monthly_brute: string; // Decimal como string
  currency: "USD" | "COP" | "ARS" | "EUR";
  billable_hours_per_week: number; // 0-80
  is_active: boolean;
  user_id: number | null;
  created_at: string | null;
  updated_at: string | null;
}
```

**Permisos:** Requiere `can_view_sensitive_data` (salarios son datos sensibles)
- ✅ Roles permitidos: owner, admin_financiero, super_admin
- ❌ Denegado: product_manager, collaborator

#### Crear Miembro del Equipo

**Endpoint:** `POST /settings/team`

**Request:**
```typescript
interface TeamMemberCreate {
  name: string;
  role: string;
  salary_monthly_brute: string; // Decimal como string, > 0
  currency: "USD" | "COP" | "ARS" | "EUR"; // default: "USD"
  billable_hours_per_week: number; // default: 32, range: 0-80
  is_active?: boolean; // default: true
  user_id?: number | null;
}
```

**Permisos:** Requiere `can_modify_costs` (miembros afectan costos)
- ⚠️ Valida límites del plan (max_team_members)

#### Actualizar Miembro del Equipo

**Endpoint:** `PUT /settings/team/{member_id}`

**Request:** `TeamMemberCreate` (todos los campos opcionales)

#### Eliminar Miembro del Equipo

**Endpoint:** `DELETE /settings/team/{member_id}`

**Response:** `204 No Content`

**Permisos:** Requiere `can_delete_resources`

---

### 💰 Costos Fijos

#### Listar Costos Fijos

**Endpoint:** `GET /settings/costs/fixed`

**Query Parameters:**
- `include_deleted` (opcional): boolean (default: false)
- `page` (opcional): number (default: 1)
- `page_size` (opcional): number (default: 20, max: 100)

**Response:**
```typescript
interface CostFixedListResponse {
  items: CostFixedResponse[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

interface CostFixedResponse {
  id: number;
  name: string;
  amount_monthly: string; // Decimal como string
  currency: "USD" | "COP" | "ARS" | "EUR";
  category: string; // Ej: "Overhead", "Software", "Tools"
  description: string | null;
  created_at: string | null;
  updated_at: string | null;
}
```

**Permisos:** Requiere `can_view_sensitive_data`
- ✅ Roles permitidos: owner, admin_financiero, super_admin
- ❌ Denegado: product_manager, collaborator

#### Crear Costo Fijo

**Endpoint:** `POST /settings/costs/fixed`

**Request:**
```typescript
interface CostFixedCreate {
  name: string;
  amount_monthly: string; // Decimal como string, > 0
  currency: "USD" | "COP" | "ARS" | "EUR"; // default: "USD"
  category: string; // Requerido
  description?: string;
}
```

**Permisos:** Requiere `can_modify_costs`

#### Actualizar Costo Fijo

**Endpoint:** `PUT /settings/costs/fixed/{cost_id}`

**Request:** `CostFixedCreate` (todos los campos opcionales)

#### Eliminar Costo Fijo

**Endpoint:** `DELETE /settings/costs/fixed/{cost_id}`

**Response:** `204 No Content`

**Permisos:** Requiere `can_delete_resources`

#### Obtener Blended Cost Rate (BCR)

**Endpoint:** `GET /settings/costs/blended-cost-rate`

**Query Parameters:**
- `currency` (opcional): string (default: moneda primaria de la organización)
- `use_cache` (opcional): boolean (default: true)

**Response:**
```typescript
interface BlendedCostRateResponse {
  blended_cost_rate: string; // Decimal como string (costo por hora)
  total_monthly_costs: string; // Decimal como string
  total_fixed_overhead: string; // Decimal como string
  total_tools_costs: string; // Decimal como string
  total_salaries: string; // Decimal como string
  total_monthly_hours: number; // Horas facturables totales
  active_team_members: number;
  primary_currency: string;
  currencies_used: Array<{
    currency: string;
    amount: string;
    exchange_rate: string;
  }>;
  exchange_rates_date: string | null; // ISO format
}
```

**Permisos:** Requiere `can_view_sensitive_data`

---

### 📊 Impuestos (Taxes)

#### Listar Impuestos

**Endpoint:** `GET /taxes/`

**Query Parameters:**
- `include_deleted` (opcional): boolean (default: false)
- `page` (opcional): number (default: 1)
- `page_size` (opcional): number (default: 20, max: 100)

**Response:**
```typescript
interface TaxListResponse {
  items: TaxResponse[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

interface TaxResponse {
  id: number;
  name: string;
  code: string; // Ej: "VAT", "IVA", "GST"
  percentage: string; // Decimal como string (0-100)
  is_active: boolean;
  created_at: string | null;
  updated_at: string | null;
}
```

#### Crear Impuesto

**Endpoint:** `POST /taxes/`

**Request:**
```typescript
interface TaxCreate {
  name: string;
  code: string;
  percentage: string; // Decimal como string (0-100)
  is_active?: boolean; // default: true
}
```

#### Actualizar Impuesto

**Endpoint:** `PUT /taxes/{tax_id}`

**Request:** `TaxCreate` (todos los campos opcionales)

#### Eliminar Impuesto

**Endpoint:** `DELETE /taxes/{tax_id}`

**Response:** `204 No Content`

---

### 🏢 Organizaciones

#### Listar Organizaciones (Solo Super Admin)

**Endpoint:** `GET /organizations/`

**Query Parameters:**
- `page` (opcional): number (default: 1)
- `page_size` (opcional): number (default: 20, max: 100)

**Response:**
```typescript
interface OrganizationListResponse {
  items: OrganizationResponse[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

interface OrganizationResponse {
  id: number;
  name: string;
  slug: string;
  subscription_plan: "free" | "starter" | "professional" | "enterprise";
  subscription_status: "active" | "cancelled" | "past_due" | "trialing";
  settings: Record<string, any> | null;
  created_at: string;
  updated_at: string | null;
  user_count?: number;
}
```

**Permisos:** Solo super_admin

#### Obtener Organización Actual

**Endpoint:** `GET /organizations/me`

**Response:** `OrganizationResponse`

#### Crear Organización

**Endpoint:** `POST /organizations/`

**Request:**
```typescript
interface OrganizationCreate {
  name: string;
  slug?: string; // Auto-generado si no se proporciona
  subscription_plan?: "free" | "starter" | "professional" | "enterprise"; // default: "free"
  subscription_status?: "active" | "cancelled" | "past_due" | "trialing"; // default: "active"
  settings?: Record<string, any>;
}
```

**Permisos:** Solo super_admin

#### Actualizar Organización

**Endpoint:** `PUT /organizations/{organization_id}`

**Request:** `OrganizationCreate` (todos los campos opcionales)

**Permisos:** Solo super_admin o owner (solo su propia organización)

#### Obtener Estadísticas de Uso

**Endpoint:** `GET /organizations/{organization_id}/usage`

**Response:**
```typescript
interface OrganizationUsageStats {
  organization_id: number;
  organization_name: string;
  subscription_plan: string;
  current_usage: {
    users: number;
    projects: number;
    services: number;
    team_members: number;
  };
  limits: {
    users: number; // -1 = ilimitado
    projects: number; // -1 = ilimitado
    services: number; // -1 = ilimitado
    team_members: number; // -1 = ilimitado
  };
  usage_percentage: {
    users: number; // 0-100
    projects: number;
    services: number;
    team_members: number;
  };
}
```

**Permisos:** Solo super_admin o owner (solo su propia organización)

---

### 💳 Créditos

#### Obtener Balance de Créditos

**Endpoint:** `GET /credits/balance`

**Response:**
```typescript
interface CreditBalanceResponse {
  credits_available: number;
  credits_used_this_month: number;
  credits_per_month: number | null; // null = ilimitado
  credits_used_total: number;
  is_unlimited: boolean;
  manual_credits_bonus: number;
  next_reset_at: string | null; // ISO format
}
```

#### Obtener Historial de Créditos

**Endpoint:** `GET /credits/history`

**Query Parameters:**
- `page` (opcional): number (default: 1)
- `page_size` (opcional): number (default: 20, max: 100)

**Response:**
```typescript
interface CreditHistoryResponse {
  items: Array<{
    id: number;
    transaction_type: "subscription_grant" | "manual_adjustment" | "consumption" | "refund";
    amount: number; // Positivo = créditos otorgados, Negativo = créditos consumidos
    reason: string | null;
    created_at: string;
  }>;
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}
```

#### Balance de Créditos (Admin - por Organización)

**Endpoint:** `GET /credits/admin/{organization_id}/balance`

**Permisos:** Solo super_admin

#### Historial de Créditos (Admin)

**Endpoint:** `GET /credits/admin/{organization_id}/history`

**Query Parameters:** `page`, `page_size`

**Permisos:** Solo super_admin

#### Otorgar Créditos Manualmente (Admin)

**Endpoint:** `POST /credits/admin/{organization_id}/grant`

**Request:**
```typescript
interface GrantCreditsRequest {
  amount: number; // > 0
  reason: string;
}
```

**Permisos:** Solo super_admin

#### Forzar Reseteo Mensual (Admin)

**Endpoint:** `POST /credits/admin/{organization_id}/reset-monthly`

**Permisos:** Solo super_admin

---

### 🤖 Inteligencia Artificial

#### Estado del Servicio AI

**Endpoint:** `GET /ai/status`

**Response:**
```typescript
interface AIStatusResponse {
  available: boolean;
  message: string;
}
```

#### Sugerencias de Onboarding

**Endpoint:** `POST /ai/suggest-config`

**Request:**
```typescript
interface OnboardingSuggestionRequest {
  industry: string; // Ej: "Marketing Digital", "Desarrollo Web"
  region?: string; // Ej: "US", "CO", "MX" (default: "US")
  currency?: string; // Ej: "USD", "COP" (default: "USD")
  custom_context?: string;
}
```

**Response:**
```typescript
interface OnboardingSuggestionResponse {
  suggested_roles: Array<{
    name: string;
    role: string;
    salary_monthly_brute: number;
    currency: string;
    billable_hours_per_week: number;
    is_active?: boolean;
  }>;
  suggested_services: Array<{
    name: string;
    description?: string;
    default_margin_target: number; // 0-1
    pricing_type: "hourly" | "fixed" | "recurring" | "project_value";
    is_active?: boolean;
  }>;
  suggested_fixed_costs: Array<{
    name: string;
    amount_monthly: number;
    currency: string;
    category: string;
    description?: string;
  }>;
  confidence_scores: {
    roles?: number; // 0-1
    services?: number;
    costs?: number;
  };
  reasoning?: string;
}
```

**Rate Limit:** 10 requests por minuto por tenant

#### Parsear Documento

**Endpoint:** `POST /ai/parse-document`

**Request:**
```typescript
interface DocumentParseRequest {
  text: string; // Texto del documento (PDF, CSV, etc.)
  document_type?: "payroll" | "expenses" | "mixed";
}
```

**Response:**
```typescript
interface DocumentParseResponse {
  team_members: Array<{
    name: string;
    role: string;
    salary_monthly_brute: string; // Decimal como string
    currency: string;
    billable_hours_per_week: number;
    is_active?: boolean;
  }>;
  fixed_costs: Array<{
    name: string;
    amount_monthly: string; // Decimal como string
    currency: string;
    category: string;
    description?: string;
  }>;
  subscriptions: Array<{
    name: string;
    amount_monthly: number;
    currency: string;
  }>;
  confidence_scores: {
    team_members?: number;
    fixed_costs?: number;
    subscriptions?: number;
  };
  warnings: string[];
}
```

**Rate Limit:** 10 requests por minuto por tenant

#### Procesar Comando en Lenguaje Natural

**Endpoint:** `POST /ai/process-command`

**Request:**
```typescript
interface NaturalLanguageCommandRequest {
  command: string; // Ej: "Añade un Senior Designer que gana 45k anuales"
  context?: Record<string, any>;
}
```

**Response:**
```typescript
interface NaturalLanguageCommandResponse {
  action_type: string; // "add_team_member" | "add_service" | "add_fixed_cost" | "unknown"
  action_data: Record<string, any>;
  confidence: number; // 0-1
  requires_confirmation: boolean;
  reasoning?: string;
}
```

**Rate Limit:** 10 requests por minuto por tenant

#### AI Advisor (Consultas sobre Rentabilidad)

**Endpoint:** `POST /insights/ai-advisor`

**Request:**
```typescript
interface AIAdvisorRequest {
  question: string; // Ej: "What's my average margin?"
  ai_provider?: "openai" | "gemini"; // default: "openai"
}
```

**Response:**
```typescript
interface AIAdvisorResponse {
  answer: string;
  provider: string;
}
```

---

### 📈 Dashboard e Insights

#### Dashboard Principal

**Endpoint:** `GET /insights/dashboard`

**Query Parameters:**
- `start_date` (opcional): string (ISO format)
- `end_date` (opcional): string (ISO format)

**Response:**
```typescript
interface DashboardResponse {
  kpis: {
    total_revenue: string; // Decimal como string
    total_projects: number;
    average_margin: string; // Decimal como string (0-1)
    utilization_rate: string; // Decimal como string (0-1)
  };
  revenue_by_service: Array<{
    service_id: number;
    service_name: string;
    revenue: string; // Decimal como string
    margin: string; // Decimal como string
  }>;
  recent_projects: ProjectResponse[];
  // ... más métricas
}
```

**Permisos:** Todos los usuarios autenticados

---

### 🎫 Invitaciones

#### Crear Invitación

**Endpoint:** `POST /organizations/{organization_id}/invitations`

**Request:**
```typescript
interface InvitationCreate {
  email: string;
  role: string; // "owner" | "admin_financiero" | "product_manager" | "collaborator"
  message?: string;
}
```

**Response:**
```typescript
interface InvitationResponse {
  id: number;
  email: string;
  role: string;
  organization_id: number;
  status: "pending" | "accepted" | "expired";
  expires_at: string; // ISO format
  created_at: string;
}
```

**Permisos:** Requiere `can_invite_users`
- ✅ Roles permitidos: owner, super_admin

#### Listar Invitaciones

**Endpoint:** `GET /organizations/{organization_id}/invitations`

**Response:**
```typescript
interface InvitationListResponse {
  items: InvitationResponse[];
  total: number;
}
```

#### Cancelar Invitación

**Endpoint:** `DELETE /organizations/{organization_id}/invitations/{invitation_id}`

**Response:** `204 No Content`

#### Aceptar Invitación

**Endpoint:** `POST /accept-invitation`

**Request:**
```typescript
interface InvitationAcceptRequest {
  token: string; // Token de la invitación
  password?: string; // Requerido si es usuario nuevo
  full_name?: string; // Requerido si es usuario nuevo
}
```

**Response:**
```typescript
interface InvitationAcceptResponse {
  success: boolean;
  message: string;
  access_token?: string;
  user_id?: number;
  organization_id?: number;
}
```

---

### 🛠️ Soporte (Support Roles)

#### Listar Organizaciones (Support)

**Endpoint:** `GET /support/organizations`

**Query Parameters:**
- `page` (opcional): number (default: 1)
- `page_size` (opcional): number (default: 20, max: 100)
- `include_inactive` (opcional): boolean (default: false)

**Response:** `OrganizationListResponse`

**Permisos:** Roles support (super_admin, support_manager, data_analyst)

#### Obtener Organización (Support)

**Endpoint:** `GET /support/organizations/{organization_id}`

**Response:** `OrganizationResponse`

**Permisos:** Roles support

#### Estadísticas de Uso (Support)

**Endpoint:** `GET /support/organizations/{organization_id}/usage`

**Response:** `OrganizationUsageStats`

**Permisos:** Roles support

---

### 🔧 Mantenimiento

#### Estadísticas de Papelera

**Endpoint:** `GET /maintenance/trash-stats`

**Response:**
```typescript
interface TrashStats {
  services: number;
  costs: number;
  taxes: number;
  projects: number;
  total: number;
}
```

**Permisos:** Todos los usuarios autenticados

#### Limpiar Papelera

**Endpoint:** `POST /maintenance/cleanup-trash`

**Query Parameters:**
- `days_old` (opcional): number (default: 30, range: 1-365)

**Response:**
```typescript
interface CleanupResponse {
  services_deleted: number;
  costs_deleted: number;
  taxes_deleted: number;
  projects_deleted: number;
  total_deleted: number;
  message: string;
}
```

**Permisos:** Todos los usuarios autenticados (pero típicamente solo super_admin)

---

### 💸 Gastos de Cotización (Expenses)

#### Crear Gasto en Cotización

**Endpoint:** `POST /projects/{project_id}/quotes/{quote_id}/expenses`

**Request:**
```typescript
interface QuoteExpenseCreate {
  name: string;
  description?: string;
  cost: string; // Decimal como string (costo interno)
  markup_percentage: string; // Decimal como string (0-1, ej: "0.20" = 20%)
  quantity?: string; // Decimal como string (default: "1.0")
  category: string; // Ej: "Third-party", "Software", "Hardware"
}
```

**Response:**
```typescript
interface QuoteExpenseResponse {
  id: number;
  quote_id: number;
  name: string;
  description: string | null;
  cost: string; // Decimal como string
  markup_percentage: string; // Decimal como string
  client_price: string; // Decimal como string (calculado: cost * quantity * (1 + markup_percentage))
  category: string;
  quantity: string; // Decimal como string
}
```

**Permisos:** Requiere `can_modify_costs`
- ✅ Roles permitidos: owner, admin_financiero, super_admin

**Ejemplo:**
```typescript
const expense = {
  name: "Licencia Adobe Creative Cloud",
  description: "Licencia anual para el equipo de diseño",
  cost: "600.00", // Costo interno
  markup_percentage: "0.20", // 20% markup
  quantity: "1.0",
  category: "Software"
};

const response = await apiRequest<QuoteExpenseResponse>(
  `/projects/${projectId}/quotes/${quoteId}/expenses`,
  {
    method: 'POST',
    body: JSON.stringify(expense)
  }
);
// client_price será: 600 * 1 * 1.20 = 720.00
```

#### Listar Gastos de Cotización

**Endpoint:** `GET /projects/{project_id}/quotes/{quote_id}/expenses`

**Response:**
```typescript
interface QuoteExpenseListResponse {
  items: QuoteExpenseResponse[];
  total: number;
}
```

#### Actualizar Gasto

**Endpoint:** `PUT /projects/{project_id}/quotes/{quote_id}/expenses/{expense_id}`

**Request:** `QuoteExpenseCreate` (todos los campos opcionales)

#### Eliminar Gasto

**Endpoint:** `DELETE /projects/{project_id}/quotes/{quote_id}/expenses/{expense_id}`

**Response:** `204 No Content`

---

### 🔗 Integraciones

#### Sincronizar Google Sheets

**Endpoint:** `POST /integrations/sheets/sync`

**Request:**
```typescript
interface GoogleSheetsSyncRequest {
  sheet_id: string; // ID de la hoja de Google Sheets
  range: string; // Rango a sincronizar (ej: "A1:Z100")
}
```

**Response:**
```typescript
interface GoogleSheetsSyncResponse {
  success: boolean;
  message: string;
  records_synced: number;
  errors: string[];
}
```

**Descripción:**
- Sincroniza datos de Google Sheets (costos, miembros del equipo, etc.)
- Requiere configuración de Service Account de Google
- Los datos se sincronizan al contexto de la organización actual

**Permisos:** Todos los usuarios autenticados

---

### 💳 Facturación y Suscripciones

#### Crear Sesión de Checkout (Stripe)

**Endpoint:** `POST /billing/checkout-session`

**Request:**
```typescript
interface CheckoutSessionCreate {
  plan: "free" | "starter" | "professional" | "enterprise";
  interval: "month" | "year";
  success_url: string; // URL de redirección después de pago exitoso
  cancel_url: string; // URL de redirección si se cancela
}
```

**Response:**
```typescript
interface CheckoutSessionResponse {
  session_id: string; // Stripe Checkout Session ID
  url: string; // URL de checkout de Stripe
}
```

**Permisos:** Requiere `can_manage_subscription`
- ✅ Roles permitidos: owner, super_admin

**Ejemplo:**
```typescript
const checkout = await apiRequest<CheckoutSessionResponse>('/billing/checkout-session', {
  method: 'POST',
  body: JSON.stringify({
    plan: "professional",
    interval: "month",
    success_url: `${window.location.origin}/settings/billing?success=true`,
    cancel_url: `${window.location.origin}/settings/billing?canceled=true`
  })
});

// Redirigir a Stripe Checkout
window.location.href = checkout.data!.url;
```

#### Obtener Suscripción Actual

**Endpoint:** `GET /billing/subscription`

**Response:**
```typescript
interface SubscriptionResponse {
  id: number;
  organization_id: number;
  plan: "free" | "starter" | "professional" | "enterprise";
  status: "active" | "cancelled" | "past_due" | "trialing";
  interval: "month" | "year";
  current_period_start: string; // ISO format
  current_period_end: string; // ISO format
  cancel_at_period_end: boolean;
  stripe_subscription_id: string | null;
  stripe_customer_id: string | null;
}
```

#### Actualizar Suscripción

**Endpoint:** `PUT /billing/subscription`

**Request:**
```typescript
interface SubscriptionUpdate {
  plan: "free" | "starter" | "professional" | "enterprise";
  interval?: "month" | "year";
}
```

#### Cancelar Suscripción

**Endpoint:** `POST /billing/subscription/cancel`

**Request:**
```typescript
interface SubscriptionCancel {
  cancel_immediately?: boolean; // Si true, cancela ahora; si false, al final del período
}
```

#### Listar Planes Disponibles

**Endpoint:** `GET /billing/plans`

**Response:**
```typescript
interface PlansListResponse {
  plans: PlanInfo[];
}

interface PlanInfo {
  id: string; // "free" | "starter" | "professional" | "enterprise"
  name: string;
  description: string;
  price_monthly: number | null; // null = gratis
  price_yearly: number | null;
  features: string[];
  limits: {
    users: number; // -1 = ilimitado
    projects: number;
    services: number;
    team_members: number;
  };
}
```

---

### 📋 Plantillas de Industria

#### Listar Plantillas Disponibles

**Endpoint:** `GET /templates/industries`

**Query Parameters:**
- `active_only` (opcional): boolean (default: true)

**Response:**
```typescript
interface IndustryTemplateListResponse {
  items: IndustryTemplateResponse[];
  total: number;
}

interface IndustryTemplateResponse {
  id: number;
  industry_type: string; // "branding" | "web_development" | "marketing" | etc.
  name: string;
  description: string;
  is_active: boolean;
  suggested_roles: Array<{
    name: string;
    role: string;
    salary_monthly_brute: string; // Decimal como string
    currency: string;
    billable_hours_per_week: number;
  }>;
  suggested_services: Array<{
    name: string;
    description: string;
    default_margin_target: string; // Decimal como string
    pricing_type: string;
  }>;
  suggested_fixed_costs: Array<{
    name: string;
    amount_monthly: string; // Decimal como string
    currency: string;
    category: string;
  }>;
}
```

**Ejemplo de uso:**
```typescript
// Obtener plantillas disponibles
const templates = await apiRequest<IndustryTemplateListResponse>('/templates/industries');

// Mostrar al usuario durante onboarding
templates.data!.items.forEach(template => {
  console.log(template.name, template.description);
});
```

#### Obtener Plantilla Específica

**Endpoint:** `GET /templates/industries/{industry_type}`

**Response:** `IndustryTemplateResponse`

#### Aplicar Plantilla a Organización

**Endpoint:** `POST /templates/industries/{industry_type}/apply`

**Request:**
```typescript
interface ApplyTemplateRequest {
  organization_id: number;
  create_roles?: boolean; // default: true
  create_services?: boolean; // default: true
  create_costs?: boolean; // default: true
}
```

**Response:**
```typescript
interface ApplyTemplateResponse {
  success: boolean;
  message: string;
  created: {
    roles: number;
    services: number;
    costs: number;
  };
  errors: string[];
}
```

**Permisos:** Requiere `can_modify_costs` y `can_create_services`
- ✅ Roles permitidos: owner, admin_financiero, super_admin

**Ejemplo:**
```typescript
// Aplicar plantilla de "branding" durante onboarding
const result = await apiRequest<ApplyTemplateResponse>(
  '/templates/industries/branding/apply',
  {
    method: 'POST',
    body: JSON.stringify({
      organization_id: currentOrgId,
      create_roles: true,
      create_services: true,
      create_costs: true
    })
  }
);

console.log(`Creados: ${result.data!.created.roles} roles, ${result.data!.created.services} servicios`);
```

---

### 📊 Proyecciones

#### Proyección de Ventas

**Endpoint:** `POST /sales/projection`

**Request:**
```typescript
interface SalesProjectionRequest {
  services: Array<{
    service_id: number;
    estimated_hours: number;
  }>;
  win_rate: number; // 0-1 (default: 0.85)
  scenario: "conservative" | "realistic" | "optimistic"; // default: "realistic"
  period_months: number; // default: 12
}
```

**Response:**
```typescript
interface SalesProjectionResponse {
  total_revenue: string; // Decimal como string
  total_hours: number;
  monthly_breakdown: Array<{
    month: number;
    revenue: string;
    hours: number;
  }>;
  // ... más detalles
}
```

#### Proyección Anual

**Endpoint:** `GET /projections/annual`

**Response:**
```typescript
interface AnnualProjectionResponse {
  // ... estructura compleja con proyecciones mensuales
}
```

**Permisos:** Requiere `can_view_financial_projections`
- ✅ Roles permitidos: owner, admin_financiero, super_admin

---

### ⚙️ Configuración

#### Obtener Configuración de Moneda

**Endpoint:** `GET /settings/currency`

**Query Parameters:**
- `include_rates` (opcional): boolean (default: false)

**Response:**
```typescript
interface AgencySettingsResponse {
  primary_currency: string;
  currency_symbol: string;
  available_currencies: string[];
  exchange_rates?: Record<string, number> | null; // Solo si include_rates=true y usuario es owner/super_admin
}
```

#### Actualizar Configuración de Moneda

**Endpoint:** `PUT /settings/currency`

**Request:**
```typescript
interface AgencySettingsUpdate {
  primary_currency: string; // "USD" | "COP" | "ARS" | "EUR"
}
```

#### Obtener Tasas de Cambio

**Endpoint:** `GET /settings/currency/exchange-rates`

**Response:**
```typescript
interface ExchangeRatesResponse {
  rates: Record<string, number>; // Ej: { "COP": 4000, "EUR": 0.92 }
  base_currency: "USD";
}
```

**Permisos:** Solo owner y super_admin

---

## Manejo de Errores

### Códigos de Estado HTTP

- `200 OK`: Operación exitosa
- `201 Created`: Recurso creado exitosamente
- `204 No Content`: Operación exitosa sin contenido
- `400 Bad Request`: Solicitud inválida (validación de datos)
- `401 Unauthorized`: No autenticado o token inválido/expirado
- `403 Forbidden`: Autenticado pero sin permisos
- `404 Not Found`: Recurso no encontrado
- `422 Unprocessable Entity`: Error de validación de schema
- `429 Too Many Requests`: Rate limit excedido
- `500 Internal Server Error`: Error del servidor
- `503 Service Unavailable`: Servicio no disponible (ej: AI service)

### Formato de Error

```typescript
interface ErrorResponse {
  detail: string; // Mensaje de error legible
  error_code?: string; // Código de error estándar (opcional)
}
```

### Ejemplo de Manejo

```typescript
try {
  const response = await apiRequest<ProjectResponse>('/projects/123');
  if (response.error) {
    // Manejar error
    console.error('Error:', response.error);
    toast.error(response.error);
  } else {
    // Usar datos
    const project = response.data!;
  }
} catch (error) {
  if (error instanceof HTTPException) {
    if (error.status === 401) {
      // Token expirado, redirigir a login
      router.push('/login');
    } else if (error.status === 403) {
      // Sin permisos
      toast.error('No tienes permisos para esta acción');
    }
  }
}
```

---

## Permisos y Roles

### Roles Disponibles

#### Support Roles (Multi-tenant)
- `super_admin`: Control total, acceso a todas las organizaciones
- `support_manager`: Gestión de clientes, datos anonimizados
- `data_analyst`: Solo acceso a datasets anonimizados

#### Tenant Roles (Dentro de organización)
- `owner`: Dueño de cuenta, acceso completo
- `admin_financiero`: Administrador financiero, ve costos sensibles
- `product_manager`: Crea propuestas y cotizaciones
- `collaborator`: Puede crear borradores, NO puede enviar cotizaciones

### Matriz de Permisos

| Permiso | owner | admin_financiero | product_manager | collaborator | super_admin |
|---------|-------|------------------|-----------------|--------------|-------------|
| `can_view_sensitive_data` | ✅ | ✅ | ❌ | ❌ | ✅ |
| `can_modify_costs` | ✅ | ✅ | ❌ | ❌ | ✅ |
| `can_create_quotes` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `can_send_quotes` | ✅ | ✅ | ✅ | ❌ | ✅ |
| `can_create_projects` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `can_create_services` | ✅ | ✅ | ❌ | ❌ | ✅ |
| `can_delete_resources` | ✅ | ❌ | ❌ | ❌ | ✅ |
| `can_invite_users` | ✅ | ❌ | ❌ | ❌ | ✅ |
| `can_manage_subscription` | ✅ | ❌ | ❌ | ❌ | ✅ |
| `can_view_analytics` | ✅ | ✅ | ✅ | ❌ | ✅ |
| `can_view_financial_projections` | ✅ | ✅ | ❌ | ❌ | ✅ |

### Verificar Permisos en Frontend

```typescript
import { hasPermission, canViewSensitiveData, canSendQuotes } from '@/lib/permissions';

// Verificar permiso específico
if (hasPermission(currentUser, 'can_send_quotes')) {
  // Mostrar botón de enviar cotización
}

// Usar helpers específicos
if (canViewSensitiveData(currentUser)) {
  // Mostrar sección de costos
}
```

---

## Multi-Tenancy

### Contexto de Tenant

El backend maneja automáticamente el contexto de tenant basado en:
1. `organization_id` del usuario autenticado (del JWT)
2. Validación de que la organización existe y está activa
3. Filtrado automático de datos por `organization_id`

### Cambiar Organización

Los usuarios support pueden cambiar de organización:

```typescript
const response = await apiRequest<TokenResponse>('/auth/switch-organization', {
  method: 'POST',
  body: JSON.stringify({ organization_id: 123 })
});

// Actualizar token
localStorage.setItem('auth_token', response.data!.access_token);
```

### Aislamiento de Datos

- Todos los recursos (proyectos, servicios, costos, etc.) están automáticamente filtrados por `organization_id`
- Los usuarios solo pueden acceder a recursos de su organización
- Los super_admin pueden acceder a todas las organizaciones mediante endpoints `/support/*`

---

## Tipos TypeScript

### Tipos Comunes

```typescript
// Monedas soportadas
type CurrencyCode = "USD" | "COP" | "ARS" | "EUR";

// Roles
type TenantRole = "owner" | "admin_financiero" | "product_manager" | "collaborator";
type SupportRole = "super_admin" | "support_manager" | "data_analyst";
type UserRole = TenantRole | SupportRole;

// Estados de proyecto
type ProjectStatus = "Draft" | "Sent" | "Won" | "Lost";

// Tipos de pricing
type PricingType = "hourly" | "fixed" | "recurring" | "project_value";

// Planes de suscripción
type SubscriptionPlan = "free" | "starter" | "professional" | "enterprise";
type SubscriptionStatus = "active" | "cancelled" | "past_due" | "trialing";
```

### Decimal como String

**IMPORTANTE:** Todos los valores monetarios y porcentajes se serializan como strings para mantener precisión:

```typescript
// ✅ Correcto
const margin: string = "0.40"; // Decimal como string
const price: string = "1000.50"; // Decimal como string

// ❌ Incorrecto
const margin: number = 0.40; // Puede perder precisión
```

El cliente API (`api-client.ts`) transforma automáticamente estos strings a objetos `Money` usando `dinero.js`.

---

## Ejemplos de Integración

### Ejemplo Completo: Crear Proyecto con Cotización

```typescript
import { apiRequest } from '@/lib/api-client';

async function createProjectWithQuote() {
  const projectData = {
    name: "Sitio Web E-commerce",
    client_name: "Tienda Online SA",
    client_email: "contacto@tienda.com",
    currency: "USD",
    tax_ids: [1], // IVA 19%
    quote_items: [
      {
        service_id: 1, // Desarrollo Web
        estimated_hours: 80,
        pricing_type: "hourly"
      },
      {
        service_id: 2, // Diseño UI/UX
        estimated_hours: 40,
        pricing_type: "hourly"
      }
    ]
  };

  try {
    const response = await apiRequest<QuoteResponseWithItems>('/projects/', {
      method: 'POST',
      body: JSON.stringify(projectData)
    });

    if (response.error) {
      throw new Error(response.error);
    }

    const quote = response.data!;
    console.log('Proyecto creado:', quote.project_id);
    console.log('Cotización ID:', quote.id);
    console.log('Precio total:', quote.total_client_price);
    console.log('Margen:', quote.margin_percentage);
    
    return quote;
  } catch (error) {
    console.error('Error creando proyecto:', error);
    throw error;
  }
}
```

### Ejemplo: Calcular Preview de Cotización

```typescript
async function calculateQuotePreview(items: QuoteItemCreate[], currency: string) {
  const request = {
    items,
    currency,
    tax_ids: [1]
  };

  const response = await apiRequest<QuoteCalculateResponse>('/quotes/calculate', {
    method: 'POST',
    body: JSON.stringify(request)
  });

  if (response.error) {
    throw new Error(response.error);
  }

  return response.data!;
}
```

### Ejemplo: Usar AI para Sugerencias

```typescript
async function getAISuggestions(industry: string) {
  const request = {
    industry,
    region: "CO",
    currency: "COP"
  };

  const response = await apiRequest<OnboardingSuggestionResponse>('/ai/suggest-config', {
    method: 'POST',
    body: JSON.stringify(request)
  });

  if (response.error) {
    throw new Error(response.error);
  }

  const suggestions = response.data!;
  
  // Usar sugerencias
  suggestions.suggested_roles.forEach(role => {
    // Crear miembro del equipo
  });
  
  suggestions.suggested_services.forEach(service => {
    // Crear servicio
  });
  
  return suggestions;
}
```

---

## Rate Limiting

Algunos endpoints tienen rate limiting:

- **Login:** 5 requests por minuto por IP
- **AI Endpoints:** 10 requests por minuto por tenant
- **Otros endpoints:** Generalmente sin límite (excepto abuso)

### Manejo de Rate Limit

```typescript
if (response.status === 429) {
  const retryAfter = response.headers.get('Retry-After');
  toast.error(`Demasiadas solicitudes. Intenta de nuevo en ${retryAfter} segundos`);
}
```

---

## Notas Importantes

1. **Decimal Precision:** Todos los valores monetarios se envían/reciben como strings para mantener precisión
2. **Multi-Tenancy:** El backend filtra automáticamente por organización, no es necesario pasar `organization_id` en requests
3. **Permisos:** Verificar permisos en frontend antes de mostrar acciones, pero el backend también valida
4. **Soft Delete:** La mayoría de recursos usan soft delete, usar `include_deleted=true` para ver eliminados
5. **Paginación:** Todos los endpoints de lista soportan paginación con `page` y `page_size`
6. **Créditos:** Algunas acciones consumen créditos según el rol del usuario
7. **Límites de Plan:** El backend valida límites del plan antes de crear recursos

---

## Recursos Adicionales

- **API Docs Interactiva:** http://localhost:8000/docs (Swagger UI)
- **ReDoc:** http://localhost:8000/redoc
- **Código Frontend:** `frontend/src/lib/queries/` - Hooks React Query existentes
- **Código Backend:** `backend/app/api/v1/endpoints/` - Implementación de endpoints

---

**Última actualización:** 2026-01-23
