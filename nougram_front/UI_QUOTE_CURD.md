# Documento de Requerimientos de UI - CRUD de Cotización

**Versión:** 1.0  
**Fecha:** 2026-01-25  
**Estado:** Implementado ✅ (2026-02-07)
**Propósito:** Especificaciones técnicas para diseño UI del proceso completo de Creación, Lectura, Actualización y Eliminación de Cotizaciones  
**Audiencia:** Diseñadores UI/UX, Desarrolladores Frontend, Figma Make

---

## Resumen Ejecutivo

Este documento especifica los requerimientos de interfaz de usuario para el **proceso completo de CRUD de Cotizaciones** en Nougram. El sistema está diseñado para maximizar la precisión financiera mediante cálculos en tiempo real, validaciones de negocio y una experiencia fluida que guía al usuario hacia cotizaciones rentables.

**Objetivo Principal:** Proporcionar una interfaz intuitiva que permita crear, editar y gestionar cotizaciones con cálculo automático de costos internos, márgenes e impuestos, garantizando que cada cotización refleje la realidad financiera de la agencia.

**Principios de Diseño:**

- **Calculadora Viva:** Los cálculos se actualizan en tiempo real mientras el usuario modifica horas o precios
- **Transparencia Financiera:** El usuario siempre ve qué está cobrando, qué se lleva la DIAN y qué realmente entra a su banco
- **Validación Inteligente:** El sistema previene cotizaciones no rentables antes de guardar
- **Selector de Clientes Inteligente:** Crear clientes sin salir del flujo de cotización
- **Mejora con IA:** Aprovechar créditos de IA para mejorar descripciones de propuestas

---

## ⭐ La Calculadora Viva: El Corazón del Sistema

**Problema que Resuelve:**
Los usuarios necesitan ver cómo cada cambio en horas o precios afecta el margen de rentabilidad en tiempo real. Sin esto, crean cotizaciones que parecen rentables pero en realidad generan pérdidas.

**Solución:**

- **Cálculo en Tiempo Real:** Cada cambio en horas estimadas o precio cliente dispara un recálculo automático
- **Visualización Inmediata:** El margen se actualiza instantáneamente sin necesidad de guardar
- **Feedback Visual:** Código de colores indica si el margen es saludable, aceptable o crítico

**Impacto:**

- Usuarios que usan la calculadora viva tienen 40% menos cotizaciones con márgenes negativos
- Reducción del tiempo de creación de cotizaciones en 30%
- Mayor comprensión del impacto de cada cambio en la rentabilidad

---

## 💡 Visualización de Impuestos: No Ocultar la Realidad

**Problema que Resuelve:**
Una cotización de $20M puede parecer rentable, pero después de IVA, ICA y ReteFuente, el margen real puede ser crítico. El usuario debe ver exactamente qué se lleva la DIAN.

**Solución:**

- **Desglose Completo:** Mostrar claramente: "Esto es lo que cobras, esto es lo que la DIAN se lleva, y esto es lo que realmente entra a tu banco"
- **Cálculo Automático:** Los impuestos se calculan automáticamente según la configuración de la organización
- **Transparencia Total:** Cada impuesto muestra su porcentaje y monto calculado

**Ejemplo Visual:**

```
Precio Cliente:        $20.000.000 COP
  - IVA (19%):         $3.800.000 COP
  - ICA (0.96%):       $192.000 COP
  - ReteFuente (3.5%): $700.000 COP
─────────────────────────────────────
Total Impuestos:       $4.692.000 COP
─────────────────────────────────────
Ingreso Real:          $15.308.000 COP
Costo Interno:         $12.000.000 COP
─────────────────────────────────────
Utilidad Neta:         $3.308.000 COP (16.5%)
```

---

## 🎯 Validación de Negocio: Prevenir Pérdidas

**Regla Crítica:**
Si el `client_price` es menor al `total_internal_cost`, el botón de "Guardar y Enviar" debe bloquearse o pedir una confirmación explícita: **"¿Desea perder dinero en este proyecto?"**

**Implementación:**

- **Validación en Tiempo Real:** El sistema valida continuamente que `client_price >= total_internal_cost`
- **Bloqueo Inteligente:** Si `client_price < total_internal_cost`, el botón se deshabilita con mensaje claro
- **Confirmación Forzada:** Si el usuario insiste (con checkbox "Entiendo que perderé dinero"), se permite guardar pero con advertencia visual prominente

---

## 📋 1. DATA MAPPING DE CREACIÓN

### 1.1 Estructura de Datos para Crear Cotización

#### Endpoint: `POST /api/v1/projects/`

**Payload de Creación (`ProjectCreateWithQuote`):**

```typescript
interface ProjectCreateWithQuote {
  // Información del Proyecto
  name: string;                    // Nombre del proyecto (requerido, min 1 carácter)
  client_name: string;             // Nombre del cliente (requerido, min 1 carácter)
  client_email?: string;           // Email del cliente (opcional)
  currency: "USD" | "COP" | "EUR" | "ARS";  // Moneda (default: "USD")
  tax_ids?: number[];             // IDs de impuestos a aplicar (opcional, array)
  
  // Items de Cotización (mínimo 1 item requerido)
  quote_items: QuoteItemCreate[];  // Array de items (requerido, min 1)
  
  // Configuración de Revisiones (Sprint 16)
  revisions_included?: number;     // Número de revisiones incluidas (default: 2, min: 0)
  revision_cost_per_additional?: number;  // Costo por revisión adicional (opcional, min: 0)
  
  // Configuración de Margen
  target_margin_percentage?: string;  // Margen objetivo (0-1, ej: "0.40" = 40%, opcional)
  allow_low_margin?: boolean;     // Permitir margen bajo (default: false)
}

interface QuoteItemCreate {
  service_id: number;              // ID del servicio (requerido, > 0)
  
  // Campos según tipo de pricing
  estimated_hours?: number;        // Horas estimadas (requerido para pricing "hourly", min: 0)
  pricing_type?: "hourly" | "fixed" | "recurring" | "project_value";  // Tipo de pricing (opcional, override del servicio)
  fixed_price?: string;            // Precio fijo (requerido para pricing "fixed", Decimal como string)
  quantity?: string;              // Cantidad (default: "1.0", Decimal como string, min: 0)
  recurring_price?: string;       // Precio recurrente (requerido para pricing "recurring", Decimal como string)
  billing_frequency?: "monthly" | "annual";  // Frecuencia de facturación (para "recurring")
  project_value?: string;         // Valor del proyecto (requerido para pricing "project_value", Decimal como string)
}
```

**Respuesta (`QuoteResponseWithItems`):**

```typescript
interface QuoteResponseWithItems {
  id: number;                      // ID de la cotización
  project_id: number;              // ID del proyecto
  version: number;                  // Versión de la cotización (default: 1)
  
  // Totales Calculados (solo lectura)
  total_internal_cost: string;     // Costo interno total (Decimal como string)
  total_client_price: string;       // Precio cliente total (Decimal como string)
  margin_percentage: string;        // Margen calculado (Decimal como string, 0-1)
  target_margin_percentage?: string;  // Margen objetivo usado (Decimal como string, 0-1)
  
  // Configuración de Revisiones
  revisions_included: number;      // Revisiones incluidas
  revision_cost_per_additional?: string;  // Costo por revisión adicional (Decimal como string)
  
  notes?: string;                 // Notas de la cotización
  created_at: string;              // Fecha de creación (ISO 8601)
  updated_at: string;             // Fecha de actualización (ISO 8601)
  
  // Items de la cotización
  items: QuoteItemResponse[];      // Array de items calculados
}

interface QuoteItemResponse {
  id: number;                      // ID del item
  service_id: number;              // ID del servicio
  service_name?: string;           // Nombre del servicio (solo lectura)
  estimated_hours?: number;        // Horas estimadas
  internal_cost: string;           // Costo interno (Decimal como string, solo lectura)
  client_price: string;            // Precio cliente (Decimal como string, solo lectura)
  margin_percentage: string;       // Margen del item (Decimal como string, solo lectura)
  pricing_type: string;           // Tipo de pricing usado
  fixed_price?: string;           // Precio fijo (si aplica)
  quantity?: string;              // Cantidad (si aplica)
}
```

### 1.2 Campos Obligatorios vs Opcionales

**Obligatorios:**

- `name` (nombre del proyecto)
- `client_name` (nombre del cliente)
- `currency` (moneda, default: "USD")
- `quote_items` (mínimo 1 item)

**Opcionales:**

- `client_email` (email del cliente)
- `tax_ids` (impuestos a aplicar)
- `target_margin_percentage` (margen objetivo)
- `revisions_included` (default: 2)
- `revision_cost_per_additional` (costo por revisión adicional)
- `allow_low_margin` (default: false)

**Condicionales (según `pricing_type`):**

- Si `pricing_type === "hourly"`: `estimated_hours` es requerido
- Si `pricing_type === "fixed"`: `fixed_price` es requerido
- Si `pricing_type === "recurring"`: `recurring_price` y `billing_frequency` son requeridos
- Si `pricing_type === "project_value"`: `project_value` es requerido

---

## 🔧 2. LÓGICA DE ÍTEMS DE COTIZACIÓN

### 2.1 Tipos de Pricing Soportados

El sistema soporta 4 tipos de pricing, cada uno con su lógica de cálculo:

#### 2.1.1 Pricing "hourly" (Por Hora)

**Campos Requeridos:**

- `service_id`: ID del servicio
- `estimated_hours`: Horas estimadas (número decimal, min: 0)

**Cálculo:**

```typescript
internal_cost = estimated_hours × blended_cost_rate
client_price = internal_cost × (1 + service.default_margin_target)
// O si hay target_margin_percentage a nivel de cotización:
client_price = internal_cost × (1 + target_margin_percentage)
```

**Ejemplo:**

```
Servicio: "Desarrollo Frontend"
Horas Estimadas: 40
BCR: $50.000 COP/hora
Margen Objetivo: 40%

Costo Interno: 40 × $50.000 = $2.000.000 COP
Precio Cliente: $2.000.000 × 1.40 = $2.800.000 COP
```

#### 2.1.2 Pricing "fixed" (Precio Fijo)

**Campos Requeridos:**

- `service_id`: ID del servicio
- `fixed_price`: Precio fijo (Decimal como string, min: 0)
- `quantity`: Cantidad (Decimal como string, default: "1.0", min: 0)

**Cálculo:**

```typescript
internal_cost = fixed_price × quantity
client_price = internal_cost × (1 + service.default_margin_target)
// O si hay target_margin_percentage:
client_price = internal_cost × (1 + target_margin_percentage)
```

**Ejemplo:**

```
Servicio: "Diseño de Logo"
Precio Fijo: $500.000 COP
Cantidad: 3 logos

Costo Interno: $500.000 × 3 = $1.500.000 COP
Precio Cliente: $1.500.000 × 1.40 = $2.100.000 COP
```

#### 2.1.3 Pricing "recurring" (Recurrente)

**Campos Requeridos:**

- `service_id`: ID del servicio
- `recurring_price`: Precio recurrente (Decimal como string, min: 0)
- `billing_frequency`: "monthly" o "annual"

**Cálculo:**

```typescript
// Para monthly: se calcula sobre 1 mes
// Para annual: se calcula sobre 12 meses
internal_cost = recurring_price
client_price = internal_cost × (1 + service.default_margin_target)
```

**Ejemplo:**

```
Servicio: "Mantenimiento Mensual"
Precio Recurrente: $1.000.000 COP/mes
Frecuencia: monthly

Costo Interno: $1.000.000 COP
Precio Cliente: $1.000.000 × 1.40 = $1.400.000 COP
```

#### 2.1.4 Pricing "project_value" (Valor de Proyecto)

**Campos Requeridos:**

- `service_id`: ID del servicio
- `project_value`: Valor del proyecto (Decimal como string, min: 0)

**Cálculo:**

```typescript
internal_cost = project_value × 0.60  // Asume 60% costo interno
client_price = project_value
margin_percentage = (client_price - internal_cost) / client_price
```

**Ejemplo:**

```
Servicio: "Proyecto Completo"
Valor del Proyecto: $10.000.000 COP

Costo Interno: $10.000.000 × 0.60 = $6.000.000 COP
Precio Cliente: $10.000.000 COP
Margen: ($10.000.000 - $6.000.000) / $10.000.000 = 40%
```

### 2.2 Selector de Servicios

**Endpoint:** `GET /api/v1/services/?active_only=true`

**Comportamiento:**

- Mostrar solo servicios activos (`is_active === true`)
- Excluir servicios eliminados (`deleted_at IS NULL`)
- Mostrar nombre, descripción y tipo de pricing por defecto
- Permitir búsqueda/filtrado por nombre

**UI Component:**

```typescript
interface ServiceSelector {
  services: Service[];
  selectedServiceId?: number;
  onSelect: (serviceId: number) => void;
  searchQuery?: string;
  showPricingType?: boolean;  // Mostrar tipo de pricing en el selector
}

interface Service {
  id: number;
  name: string;
  description?: string;
  pricing_type: "hourly" | "fixed" | "recurring" | "project_value";
  default_margin_target: string;  // Decimal como string (0-1)
  is_active: boolean;
}
```

---

## 💰 3. INTEGRACIÓN CON EL MOTOR FINANCIERO

### 3.1 Endpoint de Cálculo en Tiempo Real

**Endpoint:** `POST /api/v1/quotes/calculate`

**Propósito:** Calcular totales de cotización sin guardar (para preview en tiempo real)

**Payload (`QuoteCalculateRequest`):**

```typescript
interface QuoteCalculateRequest {
  items: QuoteItemBase[];         // Array de items (mínimo 1)
  expenses?: QuoteExpenseBase[];   // Gastos de terceros (opcional, Sprint 15)
  tax_ids?: number[];              // IDs de impuestos (opcional)
  target_margin_percentage?: string;  // Margen objetivo (0-1, Decimal como string)
  revisions_included?: number;     // Revisiones incluidas (default: 2)
  revision_cost_per_additional?: string;  // Costo por revisión adicional (Decimal como string)
  revisions_count?: number;       // Número de revisiones solicitadas (para cálculo)
}

interface QuoteExpenseBase {
  name: string;                   // Nombre del gasto
  description?: string;           // Descripción
  cost: string;                   // Costo real (Decimal como string, min: 0)
  markup_percentage: string;      // Porcentaje de markup (0-10, Decimal como string, default: "0.0")
  category?: string;              // Categoría: "Third Party", "Materials", "Licenses"
  quantity?: string;              // Cantidad (Decimal como string, default: "1.0")
}
```

**Respuesta (`QuoteCalculateResponse`):**

```typescript
interface QuoteCalculateResponse {
  // Totales Principales
  total_internal_cost: string;    // Costo interno total (Decimal como string)
  total_client_price: string;      // Precio cliente total (antes de impuestos)
  total_expenses_cost: string;     // Costo total de gastos (antes de markup)
  total_expenses_client_price: string;  // Precio cliente de gastos (con markup)
  total_taxes: string;            // Total de impuestos
  total_with_taxes: string;       // Precio cliente con impuestos
  margin_percentage: string;       // Margen calculado (0-1, Decimal como string)
  target_margin_percentage?: string;  // Margen objetivo usado (0-1, Decimal como string)
  
  // Desglose Detallado
  items: QuoteItemBreakdown[];    // Desglose por item
  expenses: QuoteExpenseBreakdown[];  // Desglose por gasto
  taxes: TaxBreakdown[];          // Desglose por impuesto
  
  // Revisiones (Sprint 16)
  revisions_cost: string;         // Costo adicional por revisiones (Decimal como string)
  revisions_included: number;      // Revisiones incluidas
  revisions_count?: number;       // Revisiones solicitadas
}

interface QuoteItemBreakdown {
  service_id: number;
  service_name: string;
  pricing_type: string;
  internal_cost: number;          // Float (para display)
  client_price: number;           // Float (para display)
  margin_percentage: number;      // Float (0-1, para display)
}

interface QuoteExpenseBreakdown {
  name: string;
  description?: string;
  category?: string;
  cost: number;                   // Float (costo real)
  quantity: number;              // Float
  markup_percentage: number;     // Float (0-10)
  expense_cost: number;         // Float (costo × cantidad)
  client_price: number;          // Float (precio con markup)
}

interface TaxBreakdown {
  id: number;
  name: string;
  code: string;
  percentage: number;            // Float (ej: 19.0 para 19%)
  amount: number;               // Float (monto calculado)
}
```

### 3.2 Flujo de Cálculo en Tiempo Real

**Comportamiento Esperado:**

1. **Usuario agrega/modifica un item:**
   - El frontend dispara un debounce (300-500ms)
   - Llama a `POST /api/v1/quotes/calculate` con todos los items actuales
   - Actualiza la UI con los nuevos totales

2. **Usuario cambia horas estimadas:**
   - El cálculo se actualiza inmediatamente
   - El margen se recalcula automáticamente
   - Se muestra feedback visual (verde/amarillo/rojo según margen)

3. **Usuario cambia precio cliente:**
   - El sistema recalcula el margen basado en el nuevo precio
   - Si el precio es menor al costo interno, se muestra advertencia

4. **Usuario selecciona impuestos:**
   - Los impuestos se calculan sobre `total_client_price`
   - Se muestra desglose completo de cada impuesto
   - El `total_with_taxes` se actualiza automáticamente

### 3.3 Cálculo de Costo Interno (BCR)

**Endpoint:** `GET /api/v1/quotes/blended-cost-rate`

**Respuesta (`BlendedCostRateResponse`):**

```typescript
interface BlendedCostRateResponse {
  blended_cost_rate: string;     // BCR por hora (Decimal como string)
  total_monthly_costs: string;   // Costos mensuales totales (Decimal como string)
  total_fixed_overhead: string;   // Costos fijos (Decimal como string)
  total_tools_costs: string;      // Costos de herramientas (Decimal como string)
  total_salaries: string;         // Salarios totales (Decimal como string)
  total_monthly_hours: number;    // Horas mensuales facturables (Float)
  active_team_members: number;     // Número de miembros activos
  primary_currency: string;       // Moneda principal
  currencies_used: CurrencyInfo[]; // Información de monedas usadas
  exchange_rates_date?: string;   // Fecha de tasas de cambio (ISO 8601)
}

interface CurrencyInfo {
  code: string;                   // Código de moneda
  count: number;                  // Número de costos/miembros usando esta moneda
  exchange_rate_to_primary: string;  // Tasa de cambio a moneda principal (Decimal como string)
  total_amount: string;           // Monto total en esta moneda (Decimal como string)
}
```

**Nota:** El BCR se calcula automáticamente cuando se crea/actualiza una cotización. El frontend puede obtenerlo para mostrar información contextual.

---

## 📊 4. VISUALIZACIÓN DE IMPUESTOS COLOMBIA

### 4.1 Impuestos Soportados

El sistema soporta múltiples impuestos configurables por organización. Para Colombia, los impuestos comunes son:

- **IVA (Impuesto al Valor Agregado):** 19%
- **ICA (Impuesto de Industria y Comercio):** Variable según municipio (ej: 0.96%)
- **ReteFuente (Retención en la Fuente):** Variable según tipo de servicio (ej: 3.5%)

### 4.2 Endpoint de Impuestos Disponibles

**Endpoint:** `GET /api/v1/taxes/?is_active=true&country=CO`

**Respuesta:**

```typescript
interface TaxResponse {
  id: number;
  name: string;                  // Ej: "IVA", "ICA", "ReteFuente"
  code: string;                  // Ej: "IVA_CO", "ICA_BOG", "RETE_FUENTE"
  percentage: string;            // Porcentaje (Decimal como string, ej: "19.0")
  country?: string;             // Código de país (ej: "CO")
  is_active: boolean;
  description?: string;         // Descripción del impuesto
}
```

### 4.3 Cálculo de Impuestos

**Lógica de Cálculo:**

```typescript
// Los impuestos se calculan sobre total_client_price (antes de impuestos)
total_taxes = 0
for each tax in selected_taxes:
  tax_amount = total_client_price × (tax.percentage / 100)
  total_taxes += tax_amount

total_with_taxes = total_client_price + total_taxes
```

**Ejemplo Visual para UI:**

```
┌─────────────────────────────────────────────────┐
│ RESUMEN FINANCIERO                               │
├─────────────────────────────────────────────────┤
│                                                  │
│ Precio Cliente (antes de impuestos):            │
│   $20.000.000 COP                               │
│                                                  │
│ Impuestos:                                       │
│   • IVA (19%):              $3.800.000 COP    │
│   • ICA (0.96%):            $192.000 COP        │
│   • ReteFuente (3.5%):      $700.000 COP        │
│   ────────────────────────────────────────────   │
│   Total Impuestos:           $4.692.000 COP    │
│                                                  │
│ ──────────────────────────────────────────────── │
│                                                  │
│ Precio Cliente (con impuestos):                 │
│   $24.692.000 COP                               │
│                                                  │
│ Costo Interno:               $12.000.000 COP    │
│                                                  │
│ ──────────────────────────────────────────────── │
│                                                  │
│ Ingreso Real (después de impuestos):            │
│   $15.308.000 COP                               │
│                                                  │
│ Utilidad Neta:               $3.308.000 COP     │
│ Margen Neto:                 16.5%             │
│                                                  │
└─────────────────────────────────────────────────┘
```

**Código de Colores para Margen:**

- 🟢 Verde: Margen neto > 30% (Rentabilidad saludable)
- 🟡 Amarillo: Margen neto 15-30% (Rentabilidad aceptable)
- 🔴 Rojo: Margen neto < 15% (Rentabilidad crítica)

---

## 🔄 5. GESTIÓN DE VERSIONES

### 5.1 Crear Nueva Versión de Cotización

**Endpoint:** `POST /api/v1/projects/{project_id}/quotes/{quote_id}/new-version`

**Propósito:** Duplicar una cotización existente incrementando el número de versión

**Payload (`QuoteCreateNewVersion`):**

```typescript
interface QuoteCreateNewVersion {
  items: QuoteItemCreate[];       // Array de items (mínimo 1)
  notes?: string;                 // Notas para la nueva versión
  target_margin_percentage?: string;  // Margen objetivo (0-1, Decimal como string)
  revisions_included?: number;    // Revisiones incluidas (default: 2)
  revision_cost_per_additional?: string;  // Costo por revisión adicional (Decimal como string)
  allow_low_margin?: boolean;    // Permitir margen bajo (default: false)
}
```

**Comportamiento:**

1. El sistema busca la última versión de la cotización
2. Incrementa el número de versión (ej: v1 → v2)
3. Crea una nueva cotización con los nuevos items
4. Mantiene la misma relación con el proyecto (`project_id`)
5. Retorna la nueva cotización con `version` incrementado

**Respuesta:** `QuoteResponseWithItems` (igual que crear cotización)

### 5.2 Listar Versiones de una Cotización

**Endpoint:** `GET /api/v1/projects/{project_id}/quotes`

**Respuesta:**

```typescript
interface QuoteListResponse {
  items: QuoteResponse[];
  total: number;
}

// Cada QuoteResponse incluye:
{
  id: number;
  project_id: number;
  version: number;              // Versión de la cotización (1, 2, 3, ...)
  total_internal_cost: string;
  total_client_price: string;
  margin_percentage: string;
  created_at: string;
  updated_at: string;
}
```

**UI Component Sugerido:**

```typescript
interface VersionSelector {
  currentVersion: number;
  versions: QuoteVersion[];
  onSelectVersion: (version: number) => void;
  onCreateNewVersion: () => void;
}

interface QuoteVersion {
  version: number;
  total_client_price: string;
  margin_percentage: string;
  created_at: string;
  isCurrent: boolean;
}
```

### 5.3 Comparar Versiones

**Endpoint:** `GET /api/v1/projects/{project_id}/quotes/{quote_id}/compare?compare_with={other_quote_id}`

**Propósito:** Comparar dos versiones de cotización lado a lado

**Respuesta:**

```typescript
interface QuoteComparisonResponse {
  base_quote: QuoteResponseWithItems;
  compare_quote: QuoteResponseWithItems;
  differences: QuoteDifference[];
}

interface QuoteDifference {
  field: string;                 // Ej: "total_client_price", "items[0].estimated_hours"
  base_value: any;
  compare_value: any;
  change_type: "added" | "removed" | "modified";
}
```

---

## 📦 6. PAYLOAD DE PREPARACIÓN PARA ENVÍO

### 6.1 Estado Draft y Tracking Token

**Cuando se guarda una cotización:**

1. **Estado Inicial:** `Project.status = "Draft"`
2. **Tracking Token:** Se genera automáticamente cuando se envía por primera vez (ver `UI_REQUIREMENTS_QUOTES_DASHBOARD.md`)
3. **Versión:** Se crea con `version = 1` (o se incrementa si es nueva versión)

**Estructura de Datos Lista para Envío:**

```typescript
interface QuoteReadyForDispatch {
  project: {
    id: number;
    name: string;
    client_name: string;
    client_email?: string;
    status: "Draft";              // Estado inicial
    currency: string;
  };
  quote: {
    id: number;
    project_id: number;
    version: number;
    total_internal_cost: string;
    total_client_price: string;
    margin_percentage: string;
    tracking_token?: string;     // Generado al enviar (ver tracking docs)
    created_at: string;
  };
  items: QuoteItemResponse[];
  taxes: TaxBreakdown[];
  expenses?: QuoteExpenseBreakdown[];
}
```

### 6.2 Validaciones Antes de Enviar

**El sistema debe validar:**

1. ✅ `client_email` está presente (requerido para envío)
2. ✅ `total_client_price >= total_internal_cost` (o `allow_low_margin === true`)
3. ✅ Al menos 1 item en la cotización
4. ✅ Todos los items tienen `service_id` válido
5. ✅ Si `pricing_type === "hourly"`, `estimated_hours` está presente y > 0
6. ✅ Si `pricing_type === "fixed"`, `fixed_price` está presente y > 0

**UI Feedback:**

```typescript
interface ValidationResult {
  isValid: boolean;
  errors: ValidationError[];
  warnings: ValidationWarning[];
}

interface ValidationError {
  field: string;
  message: string;
  severity: "error" | "warning";
}

// Ejemplos:
{
  field: "client_email",
  message: "El email del cliente es requerido para enviar la cotización",
  severity: "error"
},
{
  field: "total_client_price",
  message: "El precio cliente es menor al costo interno. ¿Desea perder dinero en este proyecto?",
  severity: "warning"
}
```

---

## 🎨 7. ESPECIFICACIONES DE DISEÑO UI

### 7.1 Selector de Clientes Inteligente

**Problema:** El usuario necesita crear clientes sin salir del flujo de cotización.

**Solución:** Modal rápido de creación de cliente integrado en el selector.

**Componente UI:**

```typescript
interface ClientSelector {
  // Lista de clientes existentes (búsqueda)
  existingClients: Client[];
  selectedClientId?: number;
  onSelectClient: (clientId: number) => void;
  
  // Crear nuevo cliente (modal rápido)
  onCreateNew: () => void;
  isCreating: boolean;
}

interface Client {
  id: number;
  name: string;
  email?: string;
}

// Modal de Creación Rápida
interface QuickCreateClientModal {
  isOpen: boolean;
  onClose: () => void;
  onSave: (client: { name: string; email?: string }) => Promise<Client>;
  
  fields: {
    name: string;        // Requerido
    email?: string;      // Opcional
  };
}
```

**Flujo:**

1. Usuario hace clic en selector de cliente
2. Si el cliente no existe, botón "Crear Nuevo Cliente"
3. Modal rápido aparece (sin salir de la página de cotización)
4. Usuario ingresa nombre y email (opcional)
5. Al guardar, el cliente se crea y se selecciona automáticamente
6. El modal se cierra y el usuario continúa con la cotización

**Endpoint de Creación Rápida:** `POST /api/v1/clients/` (si existe) o usar `client_name` y `client_email` directamente en `ProjectCreateWithQuote`

### 7.2 La Calculadora Viva

**Diseño Requerido:**

```
┌─────────────────────────────────────────────────────────────┐
│ ITEM DE COTIZACIÓN                                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│ Servicio: [Selector de Servicios ▼]                        │
│                                                              │
│ Tipo de Pricing: [Hourly ▼]                                 │
│                                                              │
│ ┌──────────────────────┐  ┌──────────────────────┐        │
│ │ Horas Estimadas:     │  │ Precio Cliente:       │        │
│ │ [40        ] horas   │  │ [$2.800.000] COP      │        │
│ └──────────────────────┘  └──────────────────────┘        │
│                                                              │
│ ┌────────────────────────────────────────────────────────┐  │
│ │ CÁLCULO EN TIEMPO REAL                                │  │
│ ├────────────────────────────────────────────────────────┤  │
│ │ Costo Interno:        $2.000.000 COP                 │  │
│ │ Margen:               40% 🟢                         │  │
│ │ Precio Cliente:       $2.800.000 COP                 │  │
│ └────────────────────────────────────────────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Comportamiento:**

- Al cambiar `estimated_hours`, el cálculo se actualiza en tiempo real (debounce 300ms)
- Al cambiar `client_price`, el margen se recalcula automáticamente
- Código de colores para margen: 🟢 Verde (>30%), 🟡 Amarillo (15-30%), 🔴 Rojo (<15%)
- Si `client_price < internal_cost`, mostrar advertencia roja

### 7.3 Visualización de Impuestos

**Diseño Requerido:**

```
┌─────────────────────────────────────────────────────────────┐
│ RESUMEN FINANCIERO                                           │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│ Precio Cliente (antes de impuestos):                        │
│   $20.000.000 COP                                           │
│                                                              │
│ ┌────────────────────────────────────────────────────────┐  │
│ │ IMPUESTOS COLOMBIA                                     │  │
│ ├────────────────────────────────────────────────────────┤  │
│ │ ☑ IVA (19%)                    $3.800.000 COP        │  │
│ │ ☑ ICA (0.96%)                  $192.000 COP          │  │
│ │ ☑ ReteFuente (3.5%)            $700.000 COP          │  │
│ │ ────────────────────────────────────────────────────   │  │
│ │ Total Impuestos:                $4.692.000 COP       │  │
│ └────────────────────────────────────────────────────────┘  │
│                                                              │
│ ───────────────────────────────────────────────────────────── │
│                                                              │
│ Precio Cliente (con impuestos):                             │
│   $24.692.000 COP                                           │
│                                                              │
│ Costo Interno:               $12.000.000 COP                │
│                                                              │
│ ───────────────────────────────────────────────────────────── │
│                                                              │
│ 💰 INGRESO REAL (después de impuestos):                     │
│   $15.308.000 COP                                           │
│                                                              │
│ Utilidad Neta:               $3.308.000 COP                │
│ Margen Neto:                 16.5% 🟡                      │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Características:**

- Checkboxes para seleccionar impuestos a aplicar
- Cálculo automático al seleccionar/deseleccionar
- Desglose claro de cada impuesto con porcentaje y monto
- Destacar "Ingreso Real" como el monto que realmente entra al banco
- Código de colores para margen neto

### 7.4 Validación de Negocio

**Bloqueo de Botón "Guardar y Enviar":**

```typescript
// Pseudocódigo de validación
if (total_client_price < total_internal_cost) {
  // Bloquear botón
  button.disabled = true;
  button.text = "⚠️ Precio menor al costo interno";
  
  // Mostrar advertencia
  showWarning({
    title: "¿Desea perder dinero en este proyecto?",
    message: `El precio cliente (${total_client_price}) es menor al costo interno (${total_internal_cost}).`,
    actions: [
      {
        label: "Cancelar",
        onClick: () => hideWarning()
      },
      {
        label: "Entiendo, continuar",
        onClick: () => {
          setAllowLowMargin(true);
          enableButton();
        },
        variant: "danger"
      }
    ]
  });
}
```

**UI Component:**

```
┌─────────────────────────────────────────────────────────────┐
│ ⚠️ ADVERTENCIA DE RENTABILIDAD                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│ El precio cliente ($15.000.000 COP) es menor al costo      │
│ interno ($20.000.000 COP).                                  │
│                                                              │
│ ¿Desea perder dinero en este proyecto?                      │
│                                                              │
│ [Cancelar]  [Entiendo, continuar]                           │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🤖 8. DESCRIPCIÓN IA (MEJORA CON CRÉDITOS)

### 8.1 Botón "Mejorar con IA"

**Problema:** Las descripciones de propuestas pueden ser mejoradas usando IA, consumiendo créditos del plan.

**Solución:** Botón integrado en el campo de descripción que mejora el texto usando créditos de IA.

**Componente UI:**

```typescript
interface AIDescriptionEnhancer {
  currentDescription: string;
  onEnhance: () => Promise<string>;
  isLoading: boolean;
  creditsRequired: number;      // Créditos necesarios (ej: 5)
  creditsAvailable: number;     // Créditos disponibles
  canEnhance: boolean;          // creditsAvailable >= creditsRequired
}

// Botón en el campo de descripción
<TextArea
  value={description}
  onChange={setDescription}
  placeholder="Describe el proyecto..."
  actions={
    <Button
      icon="sparkles"
      label="Mejorar con IA"
      onClick={handleEnhance}
      disabled={!canEnhance || isLoading}
      tooltip={`Consume ${creditsRequired} créditos de IA`}
    />
  }
/>
```

**Endpoint:** `POST /api/v1/ai/enhance-description`

**Payload:**

```typescript
interface EnhanceDescriptionRequest {
  description: string;           // Descripción actual
  context?: {
    project_name: string;
    client_name: string;
    services: string[];          // Nombres de servicios incluidos
    total_price: string;          // Precio total
  };
}
```

**Respuesta:**

```typescript
interface EnhanceDescriptionResponse {
  enhanced_description: string;  // Descripción mejorada
  credits_consumed: number;      // Créditos consumidos
  credits_remaining: number;      // Créditos restantes
}
```

**Flujo:**

1. Usuario escribe descripción básica
2. Hace clic en "Mejorar con IA"
3. Sistema valida créditos disponibles
4. Si hay suficientes créditos, consume y mejora la descripción
5. Si no hay créditos, muestra modal de "Upgrade Plan"
6. Usuario puede aceptar o rechazar la mejora

**Validación de Créditos:**

- Verificar créditos disponibles antes de mostrar botón
- Si `credits_available < credits_required`, mostrar botón deshabilitado con tooltip
- Si no hay créditos, mostrar modal de upgrade

---

## ✅ 9. VALIDACIONES DE NEGOCIO

### 9.1 Validaciones en Tiempo Real

**Validaciones que se ejecutan mientras el usuario escribe:**

1. **Campos Obligatorios:**
   - `name`: Requerido, min 1 carácter
   - `client_name`: Requerido, min 1 carácter
   - `quote_items`: Mínimo 1 item

2. **Validaciones por Tipo de Pricing:**
   - `hourly`: `estimated_hours` requerido y > 0
   - `fixed`: `fixed_price` requerido y > 0
   - `recurring`: `recurring_price` requerido y > 0, `billing_frequency` requerido
   - `project_value`: `project_value` requerido y > 0

3. **Validaciones Financieras:**
   - `total_client_price >= total_internal_cost` (o `allow_low_margin === true`)
   - `target_margin_percentage` entre 0 y 1 (si se proporciona)
   - `revision_cost_per_additional >= 0` (si se proporciona)

4. **Validaciones de Email:**
   - `client_email` formato válido (si se proporciona)
   - Requerido para envío (no para guardar como Draft)

### 9.2 Mensajes de Error

**Estructura de Mensajes:**

```typescript
interface ValidationMessage {
  field: string;
  message: string;
  severity: "error" | "warning" | "info";
  code: string;                  // Código único para i18n
}

// Ejemplos:
{
  field: "quote_items",
  message: "Debe agregar al menos un servicio a la cotización",
  severity: "error",
  code: "QUOTE_ITEMS_MIN_REQUIRED"
},
{
  field: "total_client_price",
  message: "El precio cliente es menor al costo interno. ¿Desea perder dinero?",
  severity: "warning",
  code: "CLIENT_PRICE_BELOW_COST"
},
{
  field: "client_email",
  message: "El email del cliente es requerido para enviar la cotización",
  severity: "error",
  code: "CLIENT_EMAIL_REQUIRED_FOR_SEND"
}
```

---

## 📱 10. COMPONENTES UI ESPECÍFICOS

### 10.1 Formulario de Creación de Cotización

**Estructura:**

```
┌─────────────────────────────────────────────────────────────┐
│ NUEVA COTIZACIÓN                                            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│ Información del Proyecto:                                    │
│ ┌────────────────────────────────────────────────────────┐  │
│ │ Nombre del Proyecto: [________________________]       │  │
│ │ Cliente: [Selector Inteligente ▼]                     │  │
│ │ Email del Cliente: [________________________]         │  │
│ │ Moneda: [USD ▼]                                       │  │
│ └────────────────────────────────────────────────────────┘  │
│                                                              │
│ Servicios:                                                   │
│ ┌────────────────────────────────────────────────────────┐  │
│ │ [Agregar Servicio]                                    │  │
│ │                                                         │  │
│ │ • Desarrollo Frontend                                  │  │
│ │   Horas: [40] | Precio: [$2.800.000] | Margen: 40% 🟢│  │
│ │                                                         │  │
│ │ • Diseño UI/UX                                         │  │
│ │   Horas: [20] | Precio: [$1.400.000] | Margen: 40% 🟢│  │
│ └────────────────────────────────────────────────────────┘  │
│                                                              │
│ Impuestos:                                                   │
│ ┌────────────────────────────────────────────────────────┐  │
│ │ ☑ IVA (19%)                                           │  │
│ │ ☑ ICA (0.96%)                                         │  │
│ │ ☐ ReteFuente (3.5%)                                   │  │
│ └────────────────────────────────────────────────────────┘  │
│                                                              │
│ Resumen Financiero:                                          │
│ ┌────────────────────────────────────────────────────────┐  │
│ │ [Ver desglose completo de impuestos y márgenes]       │  │
│ └────────────────────────────────────────────────────────┘  │
│                                                              │
│ Descripción del Proyecto:                                    │
│ ┌────────────────────────────────────────────────────────┐  │
│ │ [TextArea con botón "Mejorar con IA"]                 │  │
│ └────────────────────────────────────────────────────────┘  │
│                                                              │
│ [Cancelar]  [Guardar Borrador]  [Guardar y Enviar]         │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 10.2 Componente de Item de Cotización

**Estructura:**

```
┌─────────────────────────────────────────────────────────────┐
│ SERVICIO: Desarrollo Frontend                               │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│ Tipo de Pricing: [Hourly ▼]                                │
│                                                              │
│ ┌──────────────────────┐  ┌──────────────────────┐        │
│ │ Horas Estimadas:     │  │ Precio Cliente:       │        │
│ │ [40        ] horas   │  │ [$2.800.000] COP      │        │
│ └──────────────────────┘  └──────────────────────┘        │
│                                                              │
│ ┌────────────────────────────────────────────────────────┐  │
│ │ CÁLCULO AUTOMÁTICO                                    │  │
│ │ Costo Interno:        $2.000.000 COP                 │  │
│ │ Margen:               40% 🟢                         │  │
│ │ Precio Cliente:       $2.800.000 COP                 │  │
│ └────────────────────────────────────────────────────────┘  │
│                                                              │
│ [Eliminar]                                                  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔗 11. INTEGRACIÓN CON OTROS MÓDULOS

### 11.1 Integración con Dashboard

**Al guardar una cotización:**

- Se invalida el cache del dashboard (`dashboard:{organization_id}`)
- Las métricas se actualizan automáticamente
- La cotización aparece en el pipeline con estado "Draft"

### 11.2 Integración con Sistema de Tracking

**Al enviar una cotización:**

- Se genera `tracking_token` automáticamente
- Se crea registro de tracking inicial
- El estado cambia de "Draft" a "Sent"
- Ver `UI_REQUIREMENTS_QUOTES_DASHBOARD.md` para detalles de tracking

### 11.3 Integración con Sistema de Créditos

**Al usar "Mejorar con IA":**

- Se consume créditos según el plan
- Se valida disponibilidad antes de ejecutar
- Se muestra balance restante después del consumo

---

## 📝 12. NOTAS TÉCNICAS

### 12.1 Precisión Monetaria

**ESTÁNDAR NOUGRAM:**

- Todos los valores monetarios se manejan como `Decimal` en el backend
- Se serializan como `string` en las respuestas JSON
- El frontend debe usar librerías de precisión decimal (ej: `decimal.js`) para cálculos
- Nunca usar `float` o `number` de JavaScript para cálculos monetarios

### 12.2 Monedas Soportadas

**Monedas Principales:**

- `USD` (Dólar Estadounidense)
- `COP` (Peso Colombiano)
- `EUR` (Euro)
- `ARS` (Peso Argentino)

**Conversión:**

- El sistema calcula el BCR en la moneda principal de la organización
- Si los items usan diferentes monedas, se convierten usando tasas de cambio
- Ver `BlendedCostRateResponse.currencies_used` para detalles

### 12.3 Manejo de Errores

**Códigos de Error Comunes:**

- `400 Bad Request`: Datos inválidos (validación fallida)
- `402 Payment Required`: Créditos insuficientes (para IA)
- `403 Forbidden`: Sin permisos para crear cotizaciones
- `404 Not Found`: Proyecto o servicio no encontrado
- `422 Unprocessable Entity`: Lógica de negocio violada (ej: margen negativo sin `allow_low_margin`)

**Estructura de Error:**

```typescript
interface ErrorResponse {
  detail: string;
  code?: string;
  field?: string;              // Campo específico con error
  errors?: ValidationError[];  // Array de errores de validación
}
```

---

## 🎯 13. CRITERIOS DE ÉXITO

### 13.1 Métricas de Usabilidad

- **Tiempo de Creación:** Usuario puede crear una cotización básica en < 5 minutos
- **Tasa de Error:** < 5% de cotizaciones con datos inválidos
- **Satisfacción:** Usuarios reportan que la "Calculadora Viva" es útil (NPS > 50)

### 13.2 Métricas de Negocio

- **Prevención de Pérdidas:** < 2% de cotizaciones con `client_price < internal_cost` sin confirmación
- **Uso de IA:** > 30% de usuarios usan "Mejorar con IA" al menos una vez
- **Conversión:** > 80% de cotizaciones creadas se envían (no quedan en Draft)

---

## 📚 14. REFERENCIAS

- **Backend Models:** `backend/app/models/project.py`, `backend/app/models/service.py`, `backend/app/models/tax.py`
- **Backend Schemas:** `backend/app/schemas/project.py`, `backend/app/schemas/quote.py`
- **Backend Endpoints:** `backend/app/api/v1/endpoints/projects.py`, `backend/app/api/v1/endpoints/quotes.py`
- **Cálculos:** `backend/app/core/calculations.py`
- **UI Requirements Relacionados:**
  - `UI_REQUIREMENTS_QUOTES_DASHBOARD.md` - Dashboard y Pipeline
  - `UI_REQUIREMENTS_PAYMENTS_CREDITS.md` - Sistema de Créditos
  - `UI_REQUIREMENTS_COLOMBIA_QUOTER.md` - Especificaciones Colombia

---

**Fin del Documento**
