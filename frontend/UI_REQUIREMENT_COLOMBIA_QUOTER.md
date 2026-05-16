# Documento de Requerimientos de UI - Cotizador Colombia

**Versión:** 1.0  
**Fecha:** 2026-01-23  
**Propósito:** Especificaciones técnicas para diseño UI en Figma Make  
**Audiencia:** Diseñadores UI/UX, Desarrolladores Frontend

---

## Resumen Ejecutivo

Este documento especifica los requerimientos de interfaz de usuario para un cotizador financiero orientado al mercado colombiano. El sistema calcula automáticamente:
- **Costo Hora Real (BCR)**: Basado en salarios, costos fijos y cargas sociales colombianas
- **Impuestos Colombia**: IVA (19%), ICA (variable), ReteFuente (variable)
- **Margen Neto**: Después de impuestos y costos operacionales

---

## 1. DATA MAPPING - Campos de Entrada Requeridos

### 1.1 Información del Proyecto (Inputs del Usuario)

#### Campos Principales
```typescript
interface ProjectInputs {
  // Información básica
  name: string;                    // Nombre del proyecto
  client_name: string;             // Nombre del cliente
  client_email?: string;           // Email del cliente (opcional)
  currency: "COP" | "USD";         // Moneda (default: COP para Colombia)
  
  // Items de cotización
  items: QuoteItemInput[];
  
  // Impuestos (selección múltiple)
  tax_ids: number[];               // IDs de impuestos a aplicar (IVA, ICA, ReteFuente)
  
  // ⚠️ NOTA: Los porcentajes de impuestos NO son editables a nivel de cotización
  // Los porcentajes vienen de la configuración del impuesto en la base de datos.
  // Si necesitas un porcentaje diferente, debes crear un nuevo impuesto o editar el existente.
  
  // 💡 FUNCIONALIDAD FUTURA: Override de porcentajes por cotización
  // taxes_override?: Array<{
  //   tax_id: number;
  //   percentage_override?: string;  // Decimal como string - Override del porcentaje
  // }>;
  
  // Configuración de margen
  target_margin_percentage?: string; // Decimal como string (0-1, ej: "0.40" = 40%)
  
  // Revisiones
  revisions_included?: number;      // Revisiones incluidas (default: 2)
  revision_cost_per_additional?: string; // Costo por revisión adicional (Decimal como string)
  revisions_count?: number;         // Número de revisiones solicitadas
  
  // Gastos de terceros
  expenses?: ExpenseInput[];
}
```

#### Item de Cotización
```typescript
interface QuoteItemInput {
  service_id: number;              // ID del servicio (requerido)
  
  // Para pricing_type "hourly"
  estimated_hours?: number;         // Horas estimadas (requerido si hourly)
  
  // Para pricing_type "fixed"
  fixed_price?: string;             // Precio fijo (Decimal como string)
  quantity?: string;                 // Cantidad (Decimal como string, default: "1.0")
  
  // Para pricing_type "recurring"
  recurring_price?: string;         // Precio recurrente (Decimal como string)
  billing_frequency?: "monthly" | "annual";
  
  // Para pricing_type "project_value"
  project_value?: string;           // Valor del proyecto (Decimal como string)
  
  // Override del tipo de pricing del servicio
  pricing_type?: "hourly" | "fixed" | "recurring" | "project_value";
}
```

#### Gasto de Terceros
```typescript
interface ExpenseInput {
  name: string;                     // Nombre del gasto
  description?: string;              // Descripción (opcional)
  cost: string;                     // Costo interno (Decimal como string)
  markup_percentage: string;        // Markup % (Decimal como string, 0-1, ej: "0.20" = 20%)
  quantity?: string;                 // Cantidad (Decimal como string, default: "1.0")
  category: string;                 // Categoría (ej: "Third-party", "Software", "Hardware")
}
```

### 1.2 Configuración de Cargas Sociales (Colombia)

**Nota:** Estos valores se configuran en la organización, pero la UI debe mostrar su impacto.

```typescript
interface SocialChargesConfig {
  enable_social_charges: boolean;   // Habilitar cargas sociales
  health_percentage: number;        // Salud: 8.5%
  pension_percentage: number;       // Pensión: 12.0%
  arl_percentage: number;           // ARL: 0.522%
  parafiscales_percentage: number;  // Parafiscales: 4.0%
  prima_services_percentage: number; // Prima de servicios: 8.33%
  cesantias_percentage: number;     // Cesantías: 8.33%
  int_cesantias_percentage: number; // Intereses cesantías: 1.0%
  vacations_percentage: number;     // Vacaciones: 4.17%
  total_percentage: number;         // Total: ~52.852%
}
```

**Impacto:** Las cargas sociales se aplican como multiplicador al salario bruto:
- Multiplicador = 1 + (total_percentage / 100)
- Ejemplo: Si total_percentage = 52.852%, multiplicador = 1.52852
- Salario con cargas = Salario bruto × 1.52852

### 1.3 Impuestos Colombia (Taxes)

```typescript
interface Tax {
  id: number;
  name: string;                     // Ej: "IVA", "ICA", "ReteFuente"
  code: string;                     // Ej: "IVA_CO", "ICA_CO", "RETE_FUENTE_CO"
  percentage: string;                // Decimal como string (ej: "19.00" para 19%)
  country: string;                   // "CO" para Colombia
  is_active: boolean;
}
```

**Impuestos Estándar Colombia:**
- **IVA**: 19% (sobre precio cliente)
- **ICA**: Variable según actividad (ej: 0.966%)
- **ReteFuente**: Variable según tipo de servicio (ej: 11%)

#### ⚠️ IMPORTANTE: Edición de Impuestos

**Estado Actual:**
- Los impuestos se seleccionan por `tax_ids` (array de IDs)
- Los porcentajes NO son editables a nivel de cotización
- Los porcentajes vienen de la configuración del impuesto en la base de datos
- Para cambiar un porcentaje, debes:
  1. Editar el impuesto globalmente en `/taxes/{tax_id}` (afecta todas las cotizaciones futuras)
  2. O crear un nuevo impuesto con el porcentaje deseado

**Recomendación para UI:**
- Mostrar los impuestos como **read-only** en la cotización
- Mostrar el porcentaje del impuesto junto al nombre
- Permitir agregar/remover impuestos (selección múltiple)
- Mostrar tooltip/info: "Los porcentajes se configuran en Configuración > Impuestos"

**Funcionalidad Futura Recomendada:**
Permitir override de porcentajes por cotización para casos especiales:

```typescript
interface TaxOverride {
  tax_id: number;
  percentage_override?: string;      // Decimal como string - Override del porcentaje
  // Si percentage_override está presente, usar este valor en lugar del porcentaje del impuesto
  // Si no está presente, usar el porcentaje del impuesto
}
```

**Casos de Uso para Override:**
- Cliente con acuerdo especial (ej: IVA reducido al 5%)
- Ajuste temporal sin modificar el impuesto global
- Negociación específica por proyecto

---

## 2. OUTPUT LOGIC - Resultados a Mostrar

### 2.1 Respuesta del Cálculo de Cotización

```typescript
interface QuoteCalculationResponse {
  // Totales principales
  total_internal_cost: string;      // Decimal como string - Costo interno total
  total_client_price: string;       // Decimal como string - Precio al cliente (sin impuestos)
  total_expenses_cost: string;      // Decimal como string - Costo de gastos
  total_expenses_client_price: string; // Decimal como string - Precio de gastos al cliente
  total_taxes: string;              // Decimal como string - Total de impuestos
  total_with_taxes: string;         // Decimal como string - Precio final con impuestos
  
  // Margen
  margin_percentage: string;        // Decimal como string (0-1, ej: "0.40" = 40%)
  target_margin_percentage: string | null; // Margen objetivo
  
  // Desglose de items
  items: Array<{
    service_id: number;
    service_name: string;
    internal_cost: string;          // Decimal como string
    client_price: string;           // Decimal como string
    margin_percentage: string;      // Decimal como string (0-1)
    estimated_hours?: number;
    pricing_type: string;
  }>;
  
  // Desglose de gastos
  expenses: Array<{
    id?: number;
    name: string;
    cost: string;                   // Decimal como string
    markup_percentage: string;      // Decimal como string
    client_price: string;           // Decimal como string (cost × quantity × (1 + markup))
    quantity: string;               // Decimal como string
    category: string;
  }>;
  
  // Desglose de impuestos
  taxes: Array<{
    id: number;
    name: string;                   // Ej: "IVA", "ICA", "ReteFuente"
    code: string;                   // Ej: "IVA_CO"
    percentage: string;             // Decimal como string
    amount: string;                 // Decimal como string - Monto del impuesto
  }>;
  
  // Revisiones
  revisions_cost: string;            // Decimal como string - Costo de revisiones adicionales
  revisions_included: number;        // Revisiones incluidas
  revisions_count?: number;          // Revisiones solicitadas
}
```

### 2.2 Respuesta del Costo Hora Real (BCR)

```typescript
interface BlendedCostRateResponse {
  blended_cost_rate: string;        // Decimal como string - Costo por hora
  total_monthly_costs: string;      // Decimal como string - Costos mensuales totales
  total_fixed_overhead: string;      // Decimal como string - Overhead fijo
  total_tools_costs: string;        // Decimal como string - Costos de herramientas/SaaS
  total_salaries: string;            // Decimal como string - Salarios con cargas sociales
  total_monthly_hours: number;      // Horas facturables mensuales totales
  active_team_members: number;     // Número de miembros activos
  primary_currency: string;         // Moneda primaria (COP o USD)
  currencies_used: Array<{
    currency: string;
    amount: string;                 // Decimal como string
    exchange_rate: string;          // Decimal como string
  }>;
  exchange_rates_date: string | null; // Fecha de tasas de cambio (ISO format)
}
```

### 2.3 Análisis de Rentabilidad

```typescript
interface RentabilityAnalysisResponse {
  total_internal_cost: string;      // Decimal como string
  total_client_price: string;       // Decimal como string
  net_profit: string;               // Decimal como string - Ganancia neta
  margin_percentage: string;        // Decimal como string (0-1)
  
  // Desglose de costos
  cost_breakdown: {
    talent_cost: string;            // Decimal como string - Costo de talento
    overhead_cost: string;           // Decimal como string - Overhead operacional
    saas_cost: string;              // Decimal como string - Costos SaaS/herramientas
    variable_cost: string;           // Decimal como string - Costos variables
  };
  
  // Carga fiscal
  tax_burden: string;                 // Decimal como string - Total de impuestos
  taxes_list: Array<{
    concept: string;                 // Nombre del impuesto
    amount: string;                  // Decimal como string
    percentage: number;             // Porcentaje del total
  }>;
  
  // Estado de rentabilidad
  status: "healthy" | "warning" | "critical";
}
```

---

## 3. VALIDATION STATES - Estados de Validación y Alertas

### 3.1 Validaciones de Precio vs Costo Operacional

#### Alerta Crítica: Precio por Debajo del Costo
```typescript
interface CriticalAlert {
  type: "PRICE_BELOW_COST";
  condition: total_client_price < total_internal_cost;
  message: "⚠️ El precio propuesto está por debajo del costo operacional";
  severity: "critical";
  color: "#DC2626"; // Rojo
  icon: "AlertTriangle";
  action: "Aumentar precio o reducir costos";
}
```

#### Alerta de Advertencia: Margen Muy Bajo
```typescript
interface WarningAlert {
  type: "LOW_MARGIN";
  condition: margin_percentage < 0.20; // Menos del 20%
  message: "⚠️ El margen está por debajo del recomendado (20%)";
  severity: "warning";
  color: "#F59E0B"; // Amarillo/Ámbar
  icon: "AlertCircle";
  action: "Revisar precio o costos";
}
```

#### Alerta Informativa: Margen Óptimo
```typescript
interface InfoAlert {
  type: "OPTIMAL_MARGIN";
  condition: margin_percentage >= 0.30 && margin_percentage <= 0.50;
  message: "✅ Margen dentro del rango óptimo (30-50%)";
  severity: "info";
  color: "#10B981"; // Verde
  icon: "CheckCircle";
}
```

#### Alerta de Advertencia: Margen Muy Alto
```typescript
interface HighMarginAlert {
  type: "HIGH_MARGIN";
  condition: margin_percentage > 0.60; // Más del 60%
  message: "ℹ️ Margen muy alto, considera revisar competitividad del precio";
  severity: "info";
  color: "#3B82F6"; // Azul
  icon: "Info";
}
```

### 3.2 Validaciones de Impuestos Colombia

#### Alerta: Falta Configurar Impuestos
```typescript
interface MissingTaxesAlert {
  type: "MISSING_COLOMBIA_TAXES";
  condition: tax_ids.length === 0 && currency === "COP";
  message: "⚠️ Para cotizaciones en COP, se recomienda aplicar IVA (19%)";
  severity: "warning";
  color: "#F59E0B";
  icon: "AlertCircle";
  action: "Agregar impuestos colombianos";
  action_link: "/settings/taxes"; // Link a configuración de impuestos
}
```

#### Información: Impuestos No Editables
```typescript
interface TaxesReadOnlyInfo {
  type: "TAXES_READ_ONLY";
  show: true; // Siempre mostrar cuando hay impuestos seleccionados
  message: "ℹ️ Los porcentajes de impuestos se configuran en Configuración > Impuestos";
  severity: "info";
  color: "#3B82F6";
  icon: "Info";
  action: "Ir a Configuración de Impuestos";
  action_link: "/settings/taxes";
}
```

**Cuándo mostrar:**
- Cuando el usuario intenta editar un porcentaje de impuesto en la cotización
- Como tooltip al hacer hover sobre el porcentaje
- Como mensaje informativo en la sección de impuestos

#### Información: Desglose de Impuestos
```typescript
interface TaxBreakdownInfo {
  type: "TAX_BREAKDOWN";
  show: true; // Siempre mostrar cuando hay impuestos
  items: taxes.map(tax => ({
    name: tax.name,
    percentage: tax.percentage,
    amount: tax.amount,
    description: getTaxDescription(tax.code) // Ej: "IVA sobre precio base"
  }));
}
```

**Descripciones de Impuestos:**
- **IVA**: "Impuesto al Valor Agregado - 19% sobre precio base"
- **ICA**: "Impuesto de Industria y Comercio - Variable según actividad"
- **ReteFuente**: "Retención en la Fuente - Variable según tipo de servicio"

### 3.3 Validaciones de Cargas Sociales

#### Información: Impacto de Cargas Sociales
```typescript
interface SocialChargesInfo {
  type: "SOCIAL_CHARGES_IMPACT";
  show: enable_social_charges === true;
  message: `Las cargas sociales colombianas aumentan el costo operacional en ${total_percentage}%`;
  breakdown: {
    health: health_percentage,
    pension: pension_percentage,
    arl: arl_percentage,
    parafiscales: parafiscales_percentage,
    prima_services: prima_services_percentage,
    cesantias: cesantias_percentage,
    int_cesantias: int_cesantias_percentage,
    vacations: vacations_percentage
  };
  total_impact: total_percentage;
}
```

### 3.4 Validaciones de Items

#### Error: Item sin Horas Estimadas (Hourly Pricing)
```typescript
interface MissingHoursError {
  type: "MISSING_HOURS";
  condition: pricing_type === "hourly" && !estimated_hours;
  message: "❌ Se requieren horas estimadas para servicios por hora";
  severity: "error";
  color: "#DC2626";
  icon: "XCircle";
  field: "estimated_hours";
}
```

#### Error: Item sin Precio Fijo (Fixed Pricing)
```typescript
interface MissingFixedPriceError {
  type: "MISSING_FIXED_PRICE";
  condition: pricing_type === "fixed" && !fixed_price;
  message: "❌ Se requiere precio fijo para servicios de precio fijo";
  severity: "error";
  color: "#DC2626";
  icon: "XCircle";
  field: "fixed_price";
}
```

---

## 4. HIERARCHY - Jerarquía Visual de Información

### 4.1 Nivel 1: Información Crítica (Above the Fold)

**Ubicación:** Parte superior de la pantalla, siempre visible

#### 4.1.1 Precio Final con Impuestos
```
┌─────────────────────────────────────┐
│  PRECIO FINAL                       │
│  $15,000,000 COP                    │ ← Tamaño grande, destacado
│  (con impuestos incluidos)          │
└─────────────────────────────────────┘
```

**Prioridad:** Máxima  
**Tamaño de fuente:** 32-40px  
**Peso:** Bold  
**Color:** Primario del sistema

#### 4.1.2 Margen Neto
```
┌─────────────────────────────────────┐
│  MARGEN NETO                         │
│  42.5%                               │ ← Color según estado (verde/amarillo/rojo)
│  ✅ Saludable                         │
└─────────────────────────────────────┘
```

**Prioridad:** Alta  
**Tamaño de fuente:** 24-28px  
**Indicador visual:** Badge con color según estado
- Verde (#10B981): ≥ 30%
- Amarillo (#F59E0B): 20-30%
- Rojo (#DC2626): < 20%

#### 4.1.3 Alertas Críticas
```
┌─────────────────────────────────────┐
│  ⚠️ PRECIO POR DEBAJO DEL COSTO     │ ← Solo si aplica
│  El precio propuesto ($10M) está    │
│  por debajo del costo ($12M)        │
└─────────────────────────────────────┘
```

**Prioridad:** Crítica (solo si aplica)  
**Color de fondo:** #FEE2E2 (rojo claro)  
**Borde:** #DC2626 (rojo)

### 4.2 Nivel 2: Información Importante (Scroll Down)

**Ubicación:** Debajo del precio final, visible sin scroll

#### 4.2.1 Desglose de Totales
```
┌─────────────────────────────────────┐
│  DESGLOSE DE COSTOS                  │
├─────────────────────────────────────┤
│  Costo Interno Total    $8,500,000  │
│  Precio Base            $12,000,000 │
│  Gastos de Terceros     $1,500,000  │
│  ─────────────────────────────────── │
│  Subtotal               $13,500,000 │
│  Impuestos:                         │
│    • IVA (19%)          $2,565,000  │
│    • ICA (0.966%)       $130,410    │
│  ─────────────────────────────────── │
│  TOTAL CON IMPUESTOS    $15,000,000 │ ← Destacado
└─────────────────────────────────────┘
```

**Prioridad:** Alta  
**Formato:** Tabla con separadores visuales  
**Alineación:** Números a la derecha

#### 4.2.2 Desglose de Impuestos Colombia
```
┌─────────────────────────────────────┐
│  IMPUESTOS COLOMBIA                  │
├─────────────────────────────────────┤
│  IVA (19%)                          │
│  $2,565,000                         │
│  [Icono: Info] ℹ️                   │ ← Tooltip: "Porcentaje configurado en Impuestos"
│  ─────────────────────────────────── │
│  ICA (0.966%)                       │
│  $130,410                           │
│  [Icono: Info] ℹ️                   │
│  ─────────────────────────────────── │
│  ReteFuente (11%)                   │
│  $1,485,000                         │
│  [Icono: Info] ℹ️                   │
│  ─────────────────────────────────── │
│  TOTAL IMPUESTOS      $4,180,410   │
│                                     │
│  [Botón: Editar Impuestos]          │ ← Link a Configuración > Impuestos
└─────────────────────────────────────┘
```

**Prioridad:** Media-Alta  
**Formato:** Cards o lista expandible  
**Acción:** Click para expandir detalles  
**Edición:** Los porcentajes NO son editables aquí (mostrar como read-only con tooltip)

**💡 Funcionalidad Futura:**
Si se implementa override de porcentajes, agregar:
- Botón "Editar" en cada impuesto
- Modal/Dialog para ingresar porcentaje override
- Indicador visual cuando hay override (ej: badge "Personalizado")
- Opción "Usar valor por defecto" para remover override

### 4.3 Nivel 3: Información Detallada (Scroll Down)

**Ubicación:** Sección expandible o en scroll

#### 4.3.1 Items de Cotización
```
┌─────────────────────────────────────┐
│  ITEMS DE COTIZACIÓN                │
├─────────────────────────────────────┤
│  Desarrollo Web                     │
│  80 horas × $50,000/hora            │
│  Costo: $4,000,000 | Precio: $6,000,000 │
│  Margen: 33.3%                       │
├─────────────────────────────────────┤
│  Diseño UI/UX                       │
│  40 horas × $50,000/hora            │
│  Costo: $2,000,000 | Precio: $3,000,000 │
│  Margen: 33.3%                       │
└─────────────────────────────────────┘
```

**Prioridad:** Media  
**Formato:** Lista expandible con detalles  
**Acción:** Click para ver detalles completos

#### 4.3.2 Gastos de Terceros
```
┌─────────────────────────────────────┐
│  GASTOS DE TERCEROS                 │
├─────────────────────────────────────┤
│  Licencia Adobe Creative Cloud      │
│  Costo: $600,000 | Markup: 20%      │
│  Precio: $720,000                   │
└─────────────────────────────────────┘
```

**Prioridad:** Media  
**Formato:** Lista compacta

#### 4.3.3 Costo Hora Real (BCR)
```
┌─────────────────────────────────────┐
│  COSTO HORA REAL (BCR)               │
├─────────────────────────────────────┤
│  $50,000 COP/hora                   │
│  ─────────────────────────────────── │
│  Desglose Mensual:                  │
│  • Salarios (con cargas) $5,000,000 │
│  • Overhead Fijo        $3,000,000  │
│  • Herramientas/SaaS    $2,000,000  │
│  ─────────────────────────────────── │
│  Total Mensual         $10,000,000  │
│  Horas Facturables              200 │
└─────────────────────────────────────┘
```

**Prioridad:** Media-Baja  
**Formato:** Card colapsable  
**Acción:** Click para expandir/colapsar

### 4.4 Nivel 4: Información Técnica (Opcional)

**Ubicación:** Sección avanzada, colapsada por defecto

#### 4.4.1 Análisis de Rentabilidad Detallado
```
┌─────────────────────────────────────┐
│  ANÁLISIS DE RENTABILIDAD           │
├─────────────────────────────────────┤
│  Costo de Talento       $6,000,000  │
│  Overhead Operacional    $2,000,000  │
│  Costos SaaS/Tools      $500,000    │
│  Costos Variables        $0         │
│  ─────────────────────────────────── │
│  Costo Total            $8,500,000  │
│  ─────────────────────────────────── │
│  Carga Fiscal           $4,180,410  │
│  Ganancia Neta          $2,319,590  │
│  Margen Neto              27.3%      │
└─────────────────────────────────────┘
```

**Prioridad:** Baja  
**Formato:** Sección avanzada, colapsada  
**Acción:** Toggle para mostrar/ocultar

---

## 5. ESPECIFICACIONES DE DISEÑO

### 5.1 Paleta de Colores

#### Colores Principales
- **Primario:** #3B82F6 (Azul)
- **Secundario:** #10B981 (Verde)
- **Acento:** #F59E0B (Ámbar)

#### Colores de Estado
- **Éxito/Positivo:** #10B981 (Verde)
- **Advertencia:** #F59E0B (Amarillo/Ámbar)
- **Error/Crítico:** #DC2626 (Rojo)
- **Información:** #3B82F6 (Azul)

#### Colores de Fondo para Alertas
- **Crítico:** #FEE2E2 (Rojo claro)
- **Advertencia:** #FEF3C7 (Amarillo claro)
- **Información:** #DBEAFE (Azul claro)
- **Éxito:** #D1FAE5 (Verde claro)

### 5.2 Tipografía

#### Jerarquía de Tamaños
- **H1 (Precio Final):** 32-40px, Bold
- **H2 (Títulos de Sección):** 24px, Semibold
- **H3 (Subtítulos):** 18px, Medium
- **Body (Texto normal):** 16px, Regular
- **Small (Texto secundario):** 14px, Regular
- **Caption (Etiquetas):** 12px, Regular

#### Fuente
- **Recomendada:** Inter, Roboto, o fuente del sistema

### 5.3 Espaciado

- **Padding de Cards:** 24px
- **Espaciado entre secciones:** 32px
- **Espaciado entre elementos:** 16px
- **Espaciado interno de elementos:** 8px

### 5.4 Componentes UI Requeridos

#### 5.4.1 Card de Precio Final
```
┌─────────────────────────────────────┐
│  [Padding: 24px]                    │
│                                     │
│  Precio Final                       │ ← H2, Semibold
│  $15,000,000 COP                    │ ← H1, Bold, Color Primario
│  (con impuestos incluidos)          │ ← Caption, Color Secundario
│                                     │
└─────────────────────────────────────┘
```

#### 5.4.2 Badge de Margen
```
┌─────────────────────────────────────┐
│  [Padding: 12px 16px]               │
│  Margen Neto                        │
│  42.5%                              │ ← Tamaño grande, Bold
│  ✅ Saludable                        │ ← Icono + texto
└─────────────────────────────────────┘
```

**Estados del Badge:**
- Verde: `background: #D1FAE5`, `border: #10B981`, `text: #065F46`
- Amarillo: `background: #FEF3C7`, `border: #F59E0B`, `text: #92400E`
- Rojo: `background: #FEE2E2`, `border: #DC2626`, `text: #991B1B`

#### 5.4.3 Alerta
```
┌─────────────────────────────────────┐
│  [Padding: 16px]                    │
│  [Border-left: 4px sólido]          │
│  [Background: según severidad]      │
│                                     │
│  ⚠️ [Icono]                         │
│  Título de la Alerta                │ ← Semibold
│  Descripción detallada del problema │ ← Regular
│                                     │
└─────────────────────────────────────┘
```

#### 5.4.4 Tabla de Desglose
```
┌─────────────────────────────────────┐
│  [Header con fondo gris claro]      │
│  Concepto              Monto        │ ← Semibold
├─────────────────────────────────────┤
│  Costo Interno Total   $8,500,000  │ ← Regular
│  Precio Base            $12,000,000 │
│  ─────────────────────────────────── │ ← Separador
│  Subtotal               $13,500,000 │ ← Semibold
└─────────────────────────────────────┘
```

**Características:**
- Filas alternadas con fondo gris muy claro (#F9FAFB)
- Números alineados a la derecha
- Separadores visuales para subtotales
- Hover effect en filas (opcional)

#### 5.4.5 Lista de Items Expandible
```
┌─────────────────────────────────────┐
│  ▼ Items de Cotización              │ ← Click para expandir
├─────────────────────────────────────┤
│  Desarrollo Web                     │
│  80 horas × $50,000/hora            │
│  Costo: $4,000,000 | Precio: $6,000,000 │
│  Margen: 33.3%                       │
└─────────────────────────────────────┘
```

**Interacción:**
- Click en header para expandir/colapsar
- Icono de chevron que rota al expandir
- Animación suave de transición

---

## 6. FLUJO DE USUARIO

### 6.1 Flujo Principal de Cotización

1. **Usuario ingresa información del proyecto**
   - Nombre, cliente, moneda
   - Agrega items (servicios con horas/precios)
   - Selecciona impuestos (IVA, ICA, ReteFuente)

2. **Sistema calcula automáticamente**
   - Obtiene BCR (Costo Hora Real)
   - Calcula costos internos
   - Aplica margen objetivo
   - Calcula impuestos

3. **Sistema muestra resultados**
   - Precio final destacado (Nivel 1)
   - Margen neto con badge de estado (Nivel 1)
   - Alertas si hay problemas (Nivel 1)
   - Desglose de costos e impuestos (Nivel 2)

4. **Usuario revisa y ajusta**
   - Ve alertas si precio < costo
   - Ajusta precio o margen objetivo
   - Recalcula automáticamente

5. **Usuario finaliza**
   - Guarda cotización
   - Envía por email
   - Exporta PDF

### 6.2 Estados de la UI

#### Estado: Cargando
```
┌─────────────────────────────────────┐
│  [Skeleton loader o spinner]        │
│  Calculando cotización...           │
└─────────────────────────────────────┘
```

#### Estado: Error
```
┌─────────────────────────────────────┐
│  ❌ Error al calcular               │
│  Por favor, verifica los datos      │
│  [Botón: Reintentar]                │
└─────────────────────────────────────┘
```

#### Estado: Sin Datos
```
┌─────────────────────────────────────┐
│  📋 Agrega items para calcular      │
│  [Botón: Agregar Item]              │
└─────────────────────────────────────┘
```

---

## 7. REQUERIMIENTOS TÉCNICOS

### 7.1 Formato de Números

- **Moneda:** Formato colombiano con separadores de miles
  - Ejemplo: `$15,000,000 COP` (no `$15.000.000`)
- **Decimales:** Mostrar 2 decimales para montos
  - Ejemplo: `$1,234.56 COP`
- **Porcentajes:** Mostrar 1 decimal para porcentajes
  - Ejemplo: `42.5%` (no `42.50%`)

### 7.2 Precisión de Cálculos

- **Backend:** Usa `Decimal` para precisión bancaria
- **Frontend:** Recibe strings, convierte a `dinero.js`
- **Display:** Formatea con separadores pero mantiene precisión interna

### 7.3 Responsive Design

- **Desktop:** Layout de 2-3 columnas
- **Tablet:** Layout de 1-2 columnas
- **Mobile:** Layout de 1 columna, cards apilados

### 7.4 Accesibilidad

- **Contraste:** Mínimo 4.5:1 para texto normal, 3:1 para texto grande
- **Focus:** Indicadores visibles en elementos interactivos
- **ARIA Labels:** Etiquetas descriptivas para lectores de pantalla
- **Keyboard Navigation:** Navegación completa por teclado

---

## 8. EJEMPLOS DE IMPLEMENTACIÓN

### 8.1 Prompt para Figma Make

```
Diseña una pantalla de cotizador financiero para Colombia que incluya los siguientes elementos:

**Estructura Principal:**
1. Header con título "Nueva Cotización"
2. Sección de Precio Final (Nivel 1):
   - Precio final grande y destacado: $15,000,000 COP
   - Badge de margen neto con color según estado (verde/amarillo/rojo)
   - Alerta crítica si precio < costo (solo si aplica)

3. Sección de Desglose (Nivel 2):
   - Tabla con: Costo Interno, Precio Base, Gastos, Subtotal, Impuestos (IVA, ICA), Total
   - Cards expandibles para desglose de impuestos colombianos

4. Sección de Items (Nivel 3):
   - Lista expandible con items de cotización
   - Cada item muestra: nombre, horas/precio, costo, precio, margen

5. Sección de BCR (Nivel 4, colapsada):
   - Card con costo hora real y desglose mensual

**Paleta de Colores:**
- Primario: #3B82F6 (Azul)
- Éxito: #10B981 (Verde)
- Advertencia: #F59E0B (Ámbar)
- Error: #DC2626 (Rojo)

**Tipografía:**
- Precio Final: 32-40px, Bold
- Títulos: 24px, Semibold
- Texto: 16px, Regular

**Estados a Diseñar:**
- Cargando (skeleton loader)
- Error (mensaje de error)
- Sin datos (empty state)
- Con datos (estado normal)

**Componentes Requeridos:**
- Card de precio final
- Badge de margen (3 estados)
- Alertas (3 niveles de severidad)
- Tabla de desglose
- Lista expandible de items
- **Selector de impuestos (multi-select con checkboxes)**
- **Cards de impuestos con porcentajes read-only**
- **Tooltip/Info para explicar que porcentajes no son editables**
- Botones de acción (Guardar, Enviar, Exportar)

**Nota Importante sobre Impuestos:**
- Los porcentajes de impuestos NO son editables a nivel de cotización
- Los porcentajes vienen de la configuración global del impuesto
- La UI debe mostrar los porcentajes como read-only con tooltip informativo
- Proporcionar link a Configuración > Impuestos para editar porcentajes globalmente
```

---

## 9. CHECKLIST DE VALIDACIÓN

### 9.1 Validaciones Funcionales
- [ ] Precio final se muestra correctamente con formato colombiano
- [ ] Margen neto se calcula y muestra con badge de color correcto
- [ ] Alertas se muestran cuando precio < costo
- [ ] Desglose de impuestos muestra IVA, ICA, ReteFuente correctamente
- [ ] **Los porcentajes de impuestos se muestran como read-only (no editables)**
- [ ] **Tooltip/info muestra que los porcentajes se configuran en Configuración > Impuestos**
- [ ] **Link a configuración de impuestos está presente y funcional**
- [ ] BCR se muestra con desglose de costos mensuales
- [ ] Items se pueden expandir/colapsar
- [ ] Cálculos se actualizan en tiempo real al cambiar inputs
- [ ] **Selección de impuestos funciona (agregar/remover por tax_ids)**

### 9.2 Validaciones de Diseño
- [ ] Jerarquía visual respeta niveles 1-4
- [ ] Colores de estado son consistentes
- [ ] Tipografía sigue la jerarquía especificada
- [ ] Espaciado es consistente (8px, 16px, 24px, 32px)
- [ ] Componentes son reutilizables
- [ ] Diseño es responsive (desktop, tablet, mobile)

### 9.3 Validaciones de Accesibilidad
- [ ] Contraste de colores cumple WCAG AA
- [ ] Navegación por teclado funciona
- [ ] ARIA labels están presentes
- [ ] Lectores de pantalla pueden leer el contenido

---

## 10. REFERENCIAS TÉCNICAS

### 10.1 Endpoints del Backend

- **Calcular Cotización:** `POST /api/v1/quotes/calculate`
- **Obtener BCR:** `GET /api/v1/settings/costs/blended-cost-rate`
- **Análisis de Rentabilidad:** `GET /api/v1/quotes/{quote_id}/rentability`

### 10.2 Schemas TypeScript

Ver archivo: `docs/development/FRONTEND_API_INTEGRATION_GUIDE.md`

### 10.3 Documentación Completa

- **Guía de Integración API:** `docs/development/FRONTEND_API_INTEGRATION_GUIDE.md`
- **Código Backend:** `backend/app/core/calculations.py`
- **Schemas:** `backend/app/schemas/quote.py`, `backend/app/schemas/organization.py`

---

**Última actualización:** 2026-01-23  
**Versión del Backend:** Compatible con v1.0  
**Monedas Soportadas:** COP (Colombia), USD
