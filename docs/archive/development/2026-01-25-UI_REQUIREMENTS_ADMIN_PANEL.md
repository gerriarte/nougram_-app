# Documento de Requerimientos de UI - Panel de Administración

**Versión:** 1.0  
**Fecha:** 2026-01-23  
**Propósito:** Especificaciones técnicas para diseño UI del Panel de Administración en Figma Make  
**Audiencia:** Diseñadores UI/UX, Desarrolladores Frontend

---

## Resumen Ejecutivo

Este documento especifica los requerimientos de interfaz de usuario para el **Panel de Administración** que permite configurar la estructura de costos del negocio. El panel incluye tres módulos principales que alimentan el cálculo del **Blended Cost Rate (BCR)** usado por el cotizador:

1. **Módulo de Nómina**: Configuración de salarios y cargas sociales
2. **Módulo de Overhead & Tools**: Gestión de gastos fijos y amortización de equipos
3. **Configuración Global**: Parámetros organizacionales (horas facturables, margen objetivo)

---

## 1. MÓDULO DE NÓMINA

### 1.1 Data Mapping - Campos de Entrada

#### Información Básica del Miembro del Equipo
```typescript
interface TeamMemberInput {
  // Información básica
  name: string;                        // Nombre completo (requerido, min: 1 caracter)
  role: string;                        // Rol/Cargo (requerido, min: 1 caracter)
  user_id?: number | null;             // ID de usuario asociado (opcional)
  is_active: boolean;                  // Estado activo/inactivo (default: true)
  
  // Compensación
  salary_monthly_brute: string;        // Salario mensual bruto (Decimal como string, > 0)
  currency: "USD" | "COP" | "ARS" | "EUR"; // Moneda (default: "USD")
  
  // Capacidad de facturación
  billable_hours_per_week: number;     // Horas facturables por semana (0-80, default: 32)
  non_billable_hours_percentage?: string; // % horas no facturables (Decimal como string, 0-1, default: "0.0")
  // Ejemplo: "0.20" = 20% del tiempo para admin/compliance
}
```

#### Configuración de Cargas Sociales (Nivel Organización)
```typescript
interface SocialChargesConfig {
  enable_social_charges: boolean;      // Habilitar cálculo de cargas sociales (default: false)
  
  // Cargas sociales básicas (Colombia - Ley 100)
  health_percentage: number;           // Salud (Patrono): 8.5% (0-100)
  pension_percentage: number;         // Pensión (Patrono): 12.0% (0-100)
  arl_percentage: number;             // ARL: 0.522% (0-100)
  parafiscales_percentage: number;    // Parafiscales: 4.0% (0-100)
  
  // Provisiones laborales (Colombia)
  prima_services_percentage: number;  // Prima de servicios: 8.33% (0-100)
  cesantias_percentage: number;       // Cesantías: 8.33% (0-100)
  int_cesantias_percentage: number;   // Intereses cesantías: 1.0% (0-100)
  vacations_percentage: number;       // Vacaciones: 4.17% (0-100)
  
  // Total calculado automáticamente (read-only)
  total_percentage?: number;          // Suma total de porcentajes (~52.852%)
}
```

**Nota:** La configuración de cargas sociales se aplica a **todos** los miembros del equipo de la organización.

### 1.2 Output Logic - Resultados a Mostrar

#### Vista de Lista de Miembros del Equipo
```typescript
interface TeamMemberDisplay {
  id: number;
  name: string;
  role: string;
  salary_monthly_brute: string;       // Decimal como string
  currency: string;
  salary_with_charges: string;         // Decimal como string - Salario con cargas sociales aplicadas
  billable_hours_per_week: number;
  billable_hours_per_month: number;    // Calculado: hours_per_week × 4.33 × (1 - non_billable_percentage)
  cost_per_hour: string;               // Decimal como string - Costo por hora para este miembro
  is_active: boolean;
}
```

#### Cálculo de Salario con Cargas Sociales
```
Salario con Cargas = Salario Bruto × (1 + total_percentage / 100)

Ejemplo:
- Salario Bruto: $3,000,000 COP
- Total Cargas: 52.852%
- Multiplicador: 1.52852
- Salario con Cargas: $3,000,000 × 1.52852 = $4,585,560 COP
```

#### Cálculo de Costo por Hora por Miembro
```
Costo por Hora = Salario con Cargas / Horas Facturables Mensuales

Horas Facturables Mensuales = billable_hours_per_week × 4.33 × (1 - non_billable_hours_percentage)

Ejemplo:
- Salario con Cargas: $4,585,560 COP
- Horas/semana: 32
- % No facturables: 20% (0.20)
- Horas facturables/semana: 32 × (1 - 0.20) = 25.6 horas
- Horas facturables/mes: 25.6 × 4.33 = 110.85 horas
- Costo por hora: $4,585,560 / 110.85 = $41,360 COP/hora
```

#### Resumen de Nómina (Vista Global)
```typescript
interface PayrollSummary {
  total_members: number;               // Total de miembros activos
  total_salary_brute: string;          // Decimal como string - Suma de salarios brutos
  total_salary_with_charges: string;   // Decimal como string - Suma de salarios con cargas
  total_social_charges: string;        // Decimal como string - Total de cargas sociales
  total_billable_hours_per_month: number; // Suma de horas facturables mensuales
  average_cost_per_hour: string;       // Decimal como string - Promedio de costo por hora
  social_charges_multiplier: number;    // Multiplicador de cargas sociales (ej: 1.52852)
  social_charges_total_percentage: number; // Porcentaje total de cargas (ej: 52.852%)
}
```

### 1.3 Validation States

#### Alerta: Sin Miembros del Equipo
```typescript
interface NoTeamMembersAlert {
  type: "NO_TEAM_MEMBERS";
  condition: total_members === 0;
  message: "⚠️ No hay miembros del equipo configurados. El BCR no se puede calcular.";
  severity: "warning";
  color: "#F59E0B";
  icon: "AlertCircle";
  action: "Agregar primer miembro del equipo";
}
```

#### Alerta: Cargas Sociales No Configuradas
```typescript
interface SocialChargesNotConfiguredAlert {
  type: "SOCIAL_CHARGES_NOT_CONFIGURED";
  condition: enable_social_charges === false && country === "CO";
  message: "ℹ️ Las cargas sociales colombianas no están habilitadas. Se recomienda configurarlas para cálculos precisos.";
  severity: "info";
  color: "#3B82F6";
  icon: "Info";
  action: "Configurar cargas sociales";
}
```

#### Validación: Horas Facturables Inválidas
```typescript
interface InvalidBillableHoursError {
  type: "INVALID_BILLABLE_HOURS";
  condition: billable_hours_per_week < 0 || billable_hours_per_week > 80;
  message: "❌ Las horas facturables por semana deben estar entre 0 y 80";
  severity: "error";
  color: "#DC2626";
  icon: "XCircle";
  field: "billable_hours_per_week";
}
```

#### Validación: Porcentaje No Facturable Inválido
```typescript
interface InvalidNonBillablePercentageError {
  type: "INVALID_NON_BILLABLE_PERCENTAGE";
  condition: non_billable_hours_percentage < 0 || non_billable_hours_percentage > 1;
  message: "❌ El porcentaje de horas no facturables debe estar entre 0% y 100%";
  severity: "error";
  color: "#DC2626";
  icon: "XCircle";
  field: "non_billable_hours_percentage";
}
```

### 1.4 Hierarchy - Jerarquía Visual

#### Nivel 1: Resumen de Nómina (Above the Fold)
```
┌─────────────────────────────────────┐
│  RESUMEN DE NÓMINA                   │
├─────────────────────────────────────┤
│  Total Miembros Activos: 5          │
│  Salario Total Bruto: $15,000,000   │
│  Salario con Cargas: $22,927,800    │ ← Destacado
│  Cargas Sociales: $7,927,800        │
│  ─────────────────────────────────── │
│  Horas Facturables/Mes: 554.25      │
│  Costo Promedio/Hora: $41,360 COP   │ ← Destacado
└─────────────────────────────────────┘
```

#### Nivel 2: Lista de Miembros del Equipo
```
┌─────────────────────────────────────┐
│  MIEMBROS DEL EQUIPO                 │
├─────────────────────────────────────┤
│  [Botón: + Agregar Miembro]         │
├─────────────────────────────────────┤
│  Juan Pérez - Senior Developer      │
│  $3,000,000 COP | $4,585,560 con cargas │
│  32 hrs/semana | $41,360/hora       │
│  [Editar] [Desactivar]              │
├─────────────────────────────────────┤
│  María García - Designer            │
│  $2,500,000 COP | $3,821,300 con cargas │
│  30 hrs/semana | $34,480/hora       │
│  [Editar] [Desactivar]              │
└─────────────────────────────────────┘
```

#### Nivel 3: Configuración de Cargas Sociales (Expandible)
```
┌─────────────────────────────────────┐
│  ▼ CONFIGURACIÓN DE CARGAS SOCIALES │ ← Click para expandir
├─────────────────────────────────────┤
│  [Toggle] Habilitar cargas sociales │
│                                     │
│  Salud (Patrono):        [8.5] %    │
│  Pensión (Patrono):      [12.0] %   │
│  ARL:                    [0.522] %  │
│  Parafiscales:           [4.0] %    │
│  Prima de Servicios:     [8.33] %   │
│  Cesantías:              [8.33] %   │
│  Intereses Cesantías:    [1.0] %    │
│  Vacaciones:             [4.17] %   │
│  ─────────────────────────────────── │
│  TOTAL:                  52.852%    │ ← Calculado automáticamente
│  Multiplicador:          1.52852    │ ← Read-only
└─────────────────────────────────────┘
```

---

## 2. MÓDULO DE OVERHEAD & TOOLS

### 2.1 Data Mapping - Campos de Entrada

#### Gastos Fijos (Overhead)
```typescript
interface FixedCostInput {
  // Información básica
  name: string;                        // Nombre del gasto (requerido, min: 1 caracter)
  description?: string;                // Descripción (opcional)
  category: string;                    // Categoría (requerido)
  // Categorías sugeridas: "Overhead", "Software", "Tools", "Infrastructure", "Office", "Utilities", "Rent"
  
  // Costo
  amount_monthly: string;              // Monto mensual (Decimal como string, > 0)
  currency: "USD" | "COP" | "ARS" | "EUR"; // Moneda (default: "USD")
}
```

#### Amortización de Equipos (Futuro)
```typescript
interface EquipmentAmortizationInput {
  // Información del equipo
  name: string;                        // Nombre del equipo (requerido)
  description?: string;                 // Descripción (opcional)
  category: string;                    // Categoría: "Hardware", "Software", "Vehicles", "Office Equipment"
  
  // Costos de adquisición
  purchase_price: string;              // Precio de compra (Decimal como string, > 0)
  purchase_date: string;                // Fecha de compra (ISO format: YYYY-MM-DD)
  currency: "USD" | "COP" | "ARS" | "EUR";
  
  // Parámetros de amortización
  useful_life_months: number;          // Vida útil en meses (ej: 36 meses = 3 años)
  salvage_value: string;               // Valor de salvamento (Decimal como string, >= 0)
  depreciation_method: "straight_line" | "declining_balance"; // Método de depreciación
  
  // Resultado calculado (read-only)
  monthly_depreciation?: string;       // Amortización mensual (Decimal como string)
  // Fórmula línea recta: (purchase_price - salvage_value) / useful_life_months
}
```

**Nota:** Actualmente el backend no tiene soporte para amortización. Este es un requerimiento futuro que debe documentarse.

### 2.2 Output Logic - Resultados a Mostrar

#### Vista de Lista de Gastos Fijos
```typescript
interface FixedCostDisplay {
  id: number;
  name: string;
  category: string;
  amount_monthly: string;              // Decimal como string
  currency: string;
  amount_monthly_normalized: string;   // Decimal como string - Normalizado a moneda primaria
  description?: string;
  created_at: string;                  // ISO format
}
```

#### Resumen de Overhead & Tools
```typescript
interface OverheadSummary {
  total_fixed_costs: string;           // Decimal como string - Total gastos fijos mensuales
  total_tools_costs: string;          // Decimal como string - Total costos de herramientas/SaaS
  total_overhead_costs: string;       // Decimal como string - Total overhead operacional
  costs_by_category: Array<{
    category: string;
    count: number;
    total_amount: string;              // Decimal como string
  }>;
  costs_by_currency: Array<{
    currency: string;
    count: number;
    total_amount: string;              // Decimal como string
    exchange_rate: string;             // Decimal como string - Tasa de cambio a moneda primaria
  }>;
}
```

#### Categorización Automática
El backend categoriza automáticamente los gastos en:
- **Tools/SaaS**: Categorías que contienen: "software", "saas", "tool", "herramienta", "licencia", "license", "subscription", "suscripcion"
- **Overhead**: Categorías que contienen: "overhead", "infrastructure", "office", "utilities", "rent", "alquiler", "general", "otro"
- **Por defecto**: Si no coincide con ninguna, se clasifica como Overhead

### 2.3 Validation States

#### Alerta: Sin Gastos Fijos Configurados
```typescript
interface NoFixedCostsAlert {
  type: "NO_FIXED_COSTS";
  condition: total_fixed_costs === 0;
  message: "ℹ️ No hay gastos fijos configurados. El BCR solo considerará costos de nómina.";
  severity: "info";
  color: "#3B82F6";
  icon: "Info";
  action: "Agregar gastos fijos";
}
```

#### Validación: Monto Inválido
```typescript
interface InvalidAmountError {
  type: "INVALID_AMOUNT";
  condition: amount_monthly <= 0;
  message: "❌ El monto mensual debe ser mayor a cero";
  severity: "error";
  color: "#DC2626";
  icon: "XCircle";
  field: "amount_monthly";
}
```

### 2.4 Hierarchy - Jerarquía Visual

#### Nivel 1: Resumen de Overhead (Above the Fold)
```
┌─────────────────────────────────────┐
│  RESUMEN DE OVERHEAD & TOOLS         │
├─────────────────────────────────────┤
│  Total Gastos Fijos: $5,000,000 COP │ ← Destacado
│  ─────────────────────────────────── │
│  Overhead Operacional: $3,000,000   │
│  Herramientas/SaaS:    $2,000,000   │
│  ─────────────────────────────────── │
│  Por Categoría:                     │
│  • Software: 3 items ($1,500,000)   │
│  • Office: 2 items ($1,000,000)     │
│  • Infrastructure: 1 item ($500,000) │
└─────────────────────────────────────┘
```

#### Nivel 2: Lista de Gastos Fijos
```
┌─────────────────────────────────────┐
│  GASTOS FIJOS                        │
├─────────────────────────────────────┤
│  [Botón: + Agregar Gasto]            │
│  [Filtro: Todas | Overhead | Tools] │
├─────────────────────────────────────┤
│  Adobe Creative Cloud               │
│  Categoría: Software                │
│  $600,000 COP/mes                   │
│  [Editar] [Eliminar]                │
├─────────────────────────────────────┤
│  Alquiler Oficina                   │
│  Categoría: Overhead                │
│  $2,000,000 COP/mes                 │
│  [Editar] [Eliminar]                │
└─────────────────────────────────────┘
```

#### Nivel 3: Amortización de Equipos (Futuro - Colapsado por Defecto)
```
┌─────────────────────────────────────┐
│  ▶ AMORTIZACIÓN DE EQUIPOS           │ ← Click para expandir
│  (Funcionalidad Futura)              │
└─────────────────────────────────────┘
```

---

## 3. CONFIGURACIÓN GLOBAL

### 3.1 Data Mapping - Campos de Entrada

#### Configuración de Horas Facturables
```typescript
interface BillableHoursConfig {
  // Configuración por defecto (aplicada a nuevos miembros)
  default_billable_hours_per_week: number; // Horas facturables por semana por defecto (0-80, default: 32)
  default_non_billable_percentage: string; // % horas no facturables por defecto (Decimal como string, 0-1, default: "0.0")
  
  // Cálculo de horas mensuales
  weeks_per_month: number;             // Semanas por mes (default: 4.33, read-only)
  // Fórmula: Horas mensuales = billable_hours_per_week × weeks_per_month × (1 - non_billable_percentage)
}
```

#### Configuración de Margen Objetivo
```typescript
interface MarginConfig {
  default_margin_target: string;       // Margen objetivo por defecto (Decimal como string, 0-1, default: "0.40" = 40%)
  // Este margen se aplica a nuevos servicios y se puede override por servicio
}
```

#### Configuración de Moneda Primaria
```typescript
interface CurrencyConfig {
  primary_currency: "USD" | "COP" | "ARS" | "EUR"; // Moneda primaria de la organización
  // Todos los costos se normalizan a esta moneda para cálculos
}
```

### 3.2 Output Logic - Resultados a Mostrar

#### Vista de Configuración Global
```typescript
interface GlobalConfigDisplay {
  // Horas
  default_billable_hours_per_week: number;
  default_non_billable_percentage: string;
  weeks_per_month: number;             // Read-only: 4.33
  
  // Margen
  default_margin_target: string;       // Decimal como string (0-1)
  
  // Moneda
  primary_currency: string;
  currency_symbol: string;             // Ej: "$", "€"
  
  // Resumen calculado
  total_billable_hours_per_month: number; // Suma de todas las horas facturables del equipo
  average_margin_target: string;        // Promedio de márgenes objetivo de servicios activos
}
```

### 3.3 Validation States

#### Validación: Horas por Defecto Inválidas
```typescript
interface InvalidDefaultHoursError {
  type: "INVALID_DEFAULT_HOURS";
  condition: default_billable_hours_per_week < 0 || default_billable_hours_per_week > 80;
  message: "❌ Las horas facturables por defecto deben estar entre 0 y 80";
  severity: "error";
  color: "#DC2626";
  icon: "XCircle";
  field: "default_billable_hours_per_week";
}
```

#### Validación: Margen Objetivo Inválido
```typescript
interface InvalidMarginError {
  type: "INVALID_MARGIN";
  condition: default_margin_target < 0 || default_margin_target > 1;
  message: "❌ El margen objetivo debe estar entre 0% y 100%";
  severity: "error";
  color: "#DC2626";
  icon: "XCircle";
  field: "default_margin_target";
}
```

### 3.4 Hierarchy - Jerarquía Visual

#### Nivel 1: Configuración Global (Above the Fold)
```
┌─────────────────────────────────────┐
│  CONFIGURACIÓN GLOBAL                │
├─────────────────────────────────────┤
│  Moneda Primaria: COP               │
│  Horas Facturables/Defecto: 32/semana │
│  Margen Objetivo/Defecto: 40%       │
│                                     │
│  [Botón: Guardar Cambios]           │
└─────────────────────────────────────┘
```

---

## 4. DATA SYNC - Cómo Alimenta el BCR

### 4.1 Flujo de Datos

```
┌─────────────────────────────────────────────────────────────┐
│  PANEL DE ADMINISTRACIÓN                                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │ Módulo Nómina    │  │ Overhead & Tools │                │
│  │                  │  │                  │                │
│  │ • Team Members   │  │ • Fixed Costs    │                │
│  │ • Social Charges │  │ • Equipment      │                │
│  └──────────────────┘  └──────────────────┘                │
│           │                    │                           │
│           └──────────┬─────────┘                           │
│                      │                                      │
│                      ▼                                      │
│         ┌──────────────────────┐                           │
│         │  Cálculo BCR         │                           │
│         │  (Backend)            │                           │
│         └──────────────────────┘                           │
│                      │                                      │
│                      ▼                                      │
│         ┌──────────────────────┐                           │
│         │  Blended Cost Rate    │                           │
│         │  $50,000 COP/hora     │                           │
│         └──────────────────────┘                           │
│                      │                                      │
│                      ▼                                      │
│         ┌──────────────────────┐                           │
│         │  Cotizador            │                           │
│         │  (Usa BCR)            │                           │
│         └──────────────────────┘                           │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 Fórmula del BCR

```
BCR = Total Monthly Costs / Total Billable Hours Available

Donde:
- Total Monthly Costs = (Salarios con Cargas) + (Gastos Fijos)
- Total Billable Hours = Σ (billable_hours_per_week × 4.33 × (1 - non_billable_percentage)) para cada miembro activo
```

### 4.3 Actualización en Tiempo Real

**Comportamiento Esperado:**
- Al agregar/editar/eliminar un miembro del equipo → BCR se recalcula automáticamente
- Al agregar/editar/eliminar un gasto fijo → BCR se recalcula automáticamente
- Al cambiar configuración de cargas sociales → BCR se recalcula automáticamente
- Al cambiar horas facturables de un miembro → BCR se recalcula automáticamente

**Cache:**
- El BCR se cachea por 5 minutos
- Los cambios invalidan el cache automáticamente
- El frontend debe mostrar indicador de "Calculando..." durante el recálculo

### 4.4 Vista de BCR en Panel de Administración

#### Card de BCR (Siempre Visible)
```
┌─────────────────────────────────────┐
│  COSTO HORA REAL (BCR)               │
├─────────────────────────────────────┤
│  $50,000 COP/hora                   │ ← Tamaño grande, destacado
│  ─────────────────────────────────── │
│  Desglose Mensual:                  │
│  • Salarios (con cargas) $10,000,000│
│  • Overhead Fijo        $3,000,000  │
│  • Herramientas/SaaS    $2,000,000  │
│  ─────────────────────────────────── │
│  Total Mensual         $15,000,000  │
│  Horas Facturables              300 │
│                                     │
│  [Botón: Ver Detalles]              │ ← Expandir desglose completo
└─────────────────────────────────────┘
```

**Estados del Card:**
- **Cargando:** Skeleton loader o spinner
- **Error:** Mensaje de error con botón "Reintentar"
- **Sin Datos:** Mensaje "Configura los costos para calcular el BCR"
- **Con Datos:** Muestra BCR y desglose

---

## 5. ESPECIFICACIONES DE DISEÑO

### 5.1 Estructura de Navegación

```
Panel de Administración
├── Nómina
│   ├── Miembros del Equipo (Lista)
│   ├── Agregar/Editar Miembro (Formulario)
│   └── Configuración de Cargas Sociales (Formulario)
├── Overhead & Tools
│   ├── Gastos Fijos (Lista)
│   ├── Agregar/Editar Gasto (Formulario)
│   └── Amortización de Equipos (Futuro)
├── Configuración Global
│   ├── Horas Facturables
│   ├── Margen Objetivo
│   └── Moneda Primaria
└── Resumen BCR (Siempre visible en sidebar o header)
```

### 5.2 Paleta de Colores

- **Primario:** #3B82F6 (Azul)
- **Éxito:** #10B981 (Verde)
- **Advertencia:** #F59E0B (Ámbar)
- **Error:** #DC2626 (Rojo)
- **Información:** #3B82F6 (Azul)

### 5.3 Tipografía

- **H1 (Títulos de Módulo):** 24px, Semibold
- **H2 (Títulos de Sección):** 20px, Medium
- **H3 (Subtítulos):** 18px, Medium
- **Body (Texto normal):** 16px, Regular
- **Small (Texto secundario):** 14px, Regular
- **Caption (Etiquetas):** 12px, Regular

### 5.4 Componentes UI Requeridos

#### 5.4.1 Card de Resumen
```
┌─────────────────────────────────────┐
│  [Padding: 24px]                    │
│                                     │
│  Título del Resumen                 │ ← H2, Semibold
│  Valor Principal: $15,000,000       │ ← H1, Bold, Color Primario
│                                     │
│  Desglose:                          │
│  • Item 1: $5,000,000               │ ← Regular
│  • Item 2: $10,000,000              │
│                                     │
└─────────────────────────────────────┘
```

#### 5.4.2 Tabla de Datos
```
┌─────────────────────────────────────┐
│  [Header con fondo gris claro]      │
│  Columna 1    Columna 2    Acciones │ ← Semibold
├─────────────────────────────────────┤
│  Fila 1       Valor 1      [Editar] │ ← Regular, hover effect
│  Fila 2       Valor 2      [Editar] │
└─────────────────────────────────────┘
```

#### 5.4.3 Formulario de Entrada
```
┌─────────────────────────────────────┐
│  [Padding: 24px]                    │
│                                     │
│  Nombre del Campo                   │ ← Label, Semibold
│  [Input field]                      │ ← Input, Regular
│  Descripción/Help text              │ ← Caption, Regular
│                                     │
│  [Botón: Guardar] [Botón: Cancelar] │
└─────────────────────────────────────┘
```

#### 5.4.4 Indicador de Cálculo en Tiempo Real
```
┌─────────────────────────────────────┐
│  🔄 Calculando BCR...               │ ← Spinner + texto
└─────────────────────────────────────┘
```

---

## 6. FLUJO DE USUARIO

### 6.1 Flujo Principal: Configurar Estructura de Costos

1. **Usuario accede al Panel de Administración**
   - Ve resumen de BCR actual (si existe)
   - Ve alertas si faltan datos

2. **Usuario configura Nómina**
   - Agrega miembros del equipo
   - Configura cargas sociales (si aplica)
   - Ve resumen de nómina actualizado

3. **Usuario configura Overhead & Tools**
   - Agrega gastos fijos
   - Ve resumen de overhead actualizado

4. **Usuario configura Parámetros Globales**
   - Define horas facturables por defecto
   - Define margen objetivo por defecto
   - Selecciona moneda primaria

5. **Sistema calcula BCR automáticamente**
   - Muestra BCR actualizado en tiempo real
   - Muestra desglose completo
   - Cache se invalida automáticamente

6. **Usuario usa BCR en Cotizador**
   - El cotizador usa el BCR para calcular costos
   - Los cambios en el panel se reflejan inmediatamente

### 6.2 Estados de la UI

#### Estado: Sin Datos Iniciales
```
┌─────────────────────────────────────┐
│  📋 Configura tu estructura de costos│
│                                     │
│  Para calcular el BCR, necesitas:  │
│  • Al menos 1 miembro del equipo    │
│  • Configurar gastos fijos (opcional)│
│                                     │
│  [Botón: Agregar Primer Miembro]    │
└─────────────────────────────────────┘
```

#### Estado: Cargando BCR
```
┌─────────────────────────────────────┐
│  🔄 Calculando BCR...               │
│  Por favor espera...                │
└─────────────────────────────────────┘
```

#### Estado: Error al Calcular
```
┌─────────────────────────────────────┐
│  ❌ Error al calcular BCR           │
│  Por favor, verifica los datos      │
│  [Botón: Reintentar]                │
└─────────────────────────────────────┘
```

---

## 7. REQUERIMIENTOS TÉCNICOS

### 7.1 Formato de Números

- **Moneda:** Formato según país (ej: Colombia: `$15,000,000 COP`)
- **Decimales:** 2 decimales para montos, 1-2 decimales para porcentajes
- **Precisión:** Backend usa `Decimal`, frontend recibe strings

### 7.2 Endpoints del Backend

#### Nómina
- `GET /api/v1/settings/team` - Listar miembros del equipo
- `POST /api/v1/settings/team` - Crear miembro
- `PUT /api/v1/settings/team/{id}` - Actualizar miembro
- `DELETE /api/v1/settings/team/{id}` - Eliminar miembro
- `PUT /api/v1/organizations/{id}` - Actualizar configuración de cargas sociales (en `settings.social_charges_config`)

#### Overhead & Tools
- `GET /api/v1/settings/costs/fixed` - Listar gastos fijos
- `POST /api/v1/settings/costs/fixed` - Crear gasto fijo
- `PUT /api/v1/settings/costs/fixed/{id}` - Actualizar gasto fijo
- `DELETE /api/v1/settings/costs/fixed/{id}` - Eliminar gasto fijo

#### BCR
- `GET /api/v1/settings/costs/blended-cost-rate` - Obtener BCR calculado

#### Configuración Global
- `GET /api/v1/settings/currency` - Obtener configuración de moneda
- `PUT /api/v1/settings/currency` - Actualizar moneda primaria
- `GET /api/v1/organizations/me` - Obtener configuración de organización

### 7.3 Validaciones del Backend

- **Salario:** Debe ser > 0
- **Horas facturables:** 0-80 por semana
- **Porcentaje no facturable:** 0-1 (0-100%)
- **Monto mensual:** Debe ser > 0
- **Categoría:** Requerida para gastos fijos
- **Moneda:** Debe ser una de las soportadas (USD, COP, ARS, EUR)

### 7.4 Permisos

- **Ver Panel:** Requiere `can_view_sensitive_data`
  - ✅ Roles permitidos: owner, admin_financiero, super_admin
  - ❌ Denegado: product_manager, collaborator

- **Editar Configuración:** Requiere `can_modify_costs`
  - ✅ Roles permitidos: owner, admin_financiero, super_admin
  - ❌ Denegado: product_manager, collaborator

---

## 8. PROMPT PARA FIGMA MAKE

```
Diseña un Panel de Administración para configurar la estructura de costos del negocio que incluya los siguientes módulos:

**Estructura Principal:**
1. Header con título "Panel de Administración" y navegación por pestañas
2. Sidebar o Card flotante con resumen del BCR (Costo Hora Real) siempre visible
3. Tres módulos principales en pestañas:
   - Nómina
   - Overhead & Tools
   - Configuración Global

**Módulo 1: Nómina**
- Vista de lista de miembros del equipo con: nombre, rol, salario bruto, salario con cargas, horas facturables, costo por hora
- Formulario para agregar/editar miembro con campos: nombre, rol, salario bruto, moneda, horas facturables/semana, % horas no facturables
- Sección expandible para configuración de cargas sociales (8 campos de porcentajes)
- Resumen de nómina mostrando: total miembros, salario total bruto, salario con cargas, total cargas sociales, horas facturables totales, costo promedio/hora

**Módulo 2: Overhead & Tools**
- Vista de lista de gastos fijos con: nombre, categoría, monto mensual, moneda
- Formulario para agregar/editar gasto con campos: nombre, categoría, monto mensual, moneda, descripción
- Resumen de overhead mostrando: total gastos fijos, desglose por categoría (Overhead vs Tools/SaaS)
- Sección colapsada para "Amortización de Equipos" (marcada como funcionalidad futura)

**Módulo 3: Configuración Global**
- Formulario con campos: horas facturables por defecto, % horas no facturables por defecto, margen objetivo por defecto, moneda primaria
- Valores calculados mostrados: total horas facturables mensuales, promedio de márgenes objetivo

**Card de BCR (Siempre Visible)**
- Título: "Costo Hora Real (BCR)"
- Valor principal grande: "$50,000 COP/hora"
- Desglose mensual: salarios con cargas, overhead fijo, herramientas/SaaS, total mensual, horas facturables
- Botón "Ver Detalles" para expandir desglose completo
- Estados: Cargando (spinner), Error (mensaje + botón reintentar), Sin datos (mensaje informativo)

**Paleta de Colores:**
- Primario: #3B82F6 (Azul)
- Éxito: #10B981 (Verde)
- Advertencia: #F59E0B (Ámbar)
- Error: #DC2626 (Rojo)

**Tipografía:**
- Títulos de módulo: 24px, Semibold
- Valores principales: 32-40px, Bold
- Texto normal: 16px, Regular

**Estados a Diseñar:**
- Cargando (skeleton loaders)
- Error (mensajes de error)
- Sin datos (empty states)
- Con datos (estado normal)
- Validación de formularios (errores inline)

**Interacciones:**
- Cálculo en tiempo real del BCR al cambiar cualquier dato
- Indicador visual de "Calculando..." durante recálculo
- Tooltips explicativos en campos complejos (ej: cargas sociales)
- Confirmación antes de eliminar registros
- Validación en tiempo real de formularios
```

---

## 9. CHECKLIST DE VALIDACIÓN

### 9.1 Validaciones Funcionales
- [ ] Los miembros del equipo se pueden agregar/editar/eliminar
- [ ] Las cargas sociales se configuran correctamente
- [ ] El salario con cargas se calcula automáticamente
- [ ] El costo por hora por miembro se calcula correctamente
- [ ] Los gastos fijos se pueden agregar/editar/eliminar
- [ ] La categorización automática funciona (Overhead vs Tools)
- [ ] El BCR se calcula y muestra correctamente
- [ ] El BCR se actualiza en tiempo real al cambiar datos
- [ ] La configuración global se guarda correctamente
- [ ] Los valores se normalizan a la moneda primaria

### 9.2 Validaciones de Diseño
- [ ] La jerarquía visual respeta los niveles especificados
- [ ] Los colores de estado son consistentes
- [ ] La tipografía sigue la jerarquía especificada
- [ ] El espaciado es consistente (8px, 16px, 24px, 32px)
- [ ] Los componentes son reutilizables
- [ ] El diseño es responsive (desktop, tablet, mobile)
- [ ] El BCR está siempre visible (sidebar o header)

### 9.3 Validaciones de UX
- [ ] Los cálculos se muestran en tiempo real
- [ ] Los indicadores de carga son claros
- [ ] Los mensajes de error son informativos
- [ ] Los tooltips explican conceptos complejos
- [ ] La navegación entre módulos es intuitiva
- [ ] Los formularios tienen validación en tiempo real

---

## 10. REFERENCIAS TÉCNICAS

### 10.1 Endpoints del Backend

- **Nómina:** `/api/v1/settings/team`
- **Gastos Fijos:** `/api/v1/settings/costs/fixed`
- **BCR:** `/api/v1/settings/costs/blended-cost-rate`
- **Configuración:** `/api/v1/settings/currency`, `/api/v1/organizations/me`

### 10.2 Schemas TypeScript

Ver archivo: `docs/development/FRONTEND_API_INTEGRATION_GUIDE.md`

### 10.3 Documentación Completa

- **Guía de Integración API:** `docs/development/FRONTEND_API_INTEGRATION_GUIDE.md`
- **Código Backend:** `backend/app/core/calculations.py`
- **Schemas:** `backend/app/schemas/team.py`, `backend/app/schemas/cost.py`, `backend/app/schemas/organization.py`

---

**Última actualización:** 2026-01-23  
**Versión del Backend:** Compatible con v1.0  
**Monedas Soportadas:** COP (Colombia), USD, ARS, EUR
