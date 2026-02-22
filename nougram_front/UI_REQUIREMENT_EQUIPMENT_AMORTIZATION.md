# Documento de Requerimientos de UI - Módulo de Amortización de Equipos

**Versión:** 1.0  
**Fecha:** 2026-01-25  
**Propósito:** Especificaciones técnicas para diseño UI del módulo de amortización de equipos  
**Audiencia:** Diseñadores UI/UX, Desarrolladores Frontend, Figma Make

---

## Resumen Ejecutivo

Este documento especifica los requerimientos de interfaz de usuario para el **Módulo de Amortización de Equipos** en Nougram. El sistema permite registrar equipos (hardware, software, vehículos, mobiliario) y calcular automáticamente su depreciación mensual, integrando estos costos en el cálculo del Blended Cost Rate (BCR).

**Objetivo Principal:** Proporcionar una interfaz intuitiva que permita gestionar equipos, visualizar su depreciación a lo largo del tiempo y entender cómo estos activos impactan el costo operacional de la agencia.

**Principios de Diseño:**

- **Transparencia Financiera:** El usuario siempre ve cómo la depreciación afecta su BCR
- **Visualización Temporal:** Gráficos y barras de progreso muestran el valor del activo en el tiempo
- **Valor de Salvamento:** No olvidar que los equipos tienen valor residual al final de su vida útil
- **Precisión Monetaria:** Manejo correcto de monedas con TRM histórica para evitar variaciones

---

## ⭐ El Error del Valor de Salvamento: No Perder Competitividad

**Problema que Resuelve:**
Muchos usuarios olvidan que al final de 3 años, pueden vender su Mac usada. Si el backend no contempla el Valor de Salvamento, el BCR será más alto de lo necesario y perderán competitividad por ser "muy caros".

**Solución:**

- **Campo Obligatorio:** El valor de salvamento debe ser siempre visible y editable
- **Validación:** No puede ser mayor al precio de compra
- **Impacto Visual:** Mostrar claramente cómo el valor de salvamento reduce la base depreciable
- **Ejemplo Educativo:** "Si tu MacBook Pro cuesta $12M y la vendes en $2M después de 3 años, solo deprecias $10M"

**Impacto:**

- Usuarios que usan valor de salvamento tienen BCR ~15% más competitivo
- Mayor precisión en el costo real de los equipos
- Mejor planificación de renovación de tecnología

---

## 💡 Moneda de Compra: TRM Histórica para Precisión

**Problema que Resuelve:**
Si compraste la cámara en USD pero tu contabilidad es en COP, el backend debe registrar la TRM del día de compra para que la amortización sea fija y no varíe con el dólar (los activos no se re-expresan cada mes en el flujo de caja operativo).

**Solución:**

- **TRM de Compra:** Al registrar un equipo en moneda diferente a la principal, capturar la TRM del día de compra
- **Amortización Fija:** La depreciación mensual se calcula en la moneda de compra y se convierte una sola vez usando la TRM histórica
- **Sin Re-expresión:** El valor no cambia mes a mes con fluctuaciones del dólar
- **Visualización:** Mostrar claramente "Comprado en USD a TRM $4,200" para transparencia

---

## 📋 1. DATA MAPPING DE ACTIVOS

### 1.1 Estructura de Datos para Registrar Equipo

#### Endpoint: `POST /api/v1/settings/equipment`

**Payload de Creación (`EquipmentAmortizationCreate`):**

```typescript
interface EquipmentAmortizationCreate {
  // Información Básica
  name: string;                    // Nombre del equipo (requerido, min 1 carácter)
  description?: string;            // Descripción (opcional)
  category: "Hardware" | "Software" | "Vehicles" | "Office Equipment";  // Categoría (requerido)
  
  // Información de Compra
  purchase_price: string;          // Precio de compra (Decimal como string, requerido, > 0)
  purchase_date: string;          // Fecha de compra (ISO 8601: YYYY-MM-DD, requerido)
  currency: "USD" | "COP" | "EUR" | "ARS";  // Moneda de compra (requerido, default: "USD")
  exchange_rate_at_purchase?: string;  // TRM del día de compra (Decimal como string, opcional, requerido si currency != primary_currency)
  
  // Parámetros de Depreciación
  useful_life_months: number;     // Vida útil en meses (requerido, > 0, típicamente 12-120)
  salvage_value: string;           // Valor de salvamento (Decimal como string, requerido, >= 0, < purchase_price)
  depreciation_method: "straight_line" | "declining_balance";  // Método de depreciación (requerido, default: "straight_line")
  
  // Estado
  is_active?: boolean;             // Si está activo y generando depreciación (default: true)
}
```

**Respuesta (`EquipmentAmortizationResponse`):**

```typescript
interface EquipmentAmortizationResponse {
  id: number;                      // ID del equipo
  name: string;                    // Nombre del equipo
  description?: string;           // Descripción
  category: string;                // Categoría
  
  // Información de Compra
  purchase_price: string;          // Precio de compra (Decimal como string)
  purchase_date: string;          // Fecha de compra (ISO 8601)
  currency: string;                // Moneda de compra
  exchange_rate_at_purchase?: string;  // TRM del día de compra (Decimal como string)
  
  // Parámetros de Depreciación
  useful_life_months: number;     // Vida útil en meses
  salvage_value: string;           // Valor de salvamento (Decimal como string)
  depreciation_method: string;    // Método de depreciación
  
  // Campos Calculados (solo lectura)
  monthly_depreciation: string;    // Depreciación mensual (Decimal como string, calculado automáticamente)
  total_depreciated: string;       // Depreciación acumulada hasta la fecha (Decimal como string)
  remaining_value: string;        // Valor en libros actual (Decimal como string)
  months_depreciated: number;      // Meses transcurridos desde purchase_date
  months_remaining: number;         // Meses restantes de vida útil
  
  // Estado
  is_active: boolean;              // Si está activo
  
  // Timestamps
  created_at: string;              // Fecha de creación (ISO 8601)
  updated_at: string;              // Fecha de actualización (ISO 8601)
}
```

### 1.2 Campos Obligatorios vs Opcionales

**Obligatorios:**

- `name` (nombre del equipo)
- `category` (categoría)
- `purchase_price` (precio de compra, > 0)
- `purchase_date` (fecha de compra, no futura)
- `currency` (moneda de compra)
- `useful_life_months` (vida útil en meses, > 0)
- `salvage_value` (valor de salvamento, >= 0, < purchase_price)
- `depreciation_method` (método de depreciación)

**Opcionales:**

- `description` (descripción)
- `exchange_rate_at_purchase` (TRM, requerido si `currency != primary_currency`)
- `is_active` (default: true)

**Condicionales:**

- Si `currency !== primary_currency`: `exchange_rate_at_purchase` es requerido

---

## 🔧 2. ALGORITMO DE DEPRECIACIÓN

### 2.1 Método Línea Recta (Straight Line)

**Fórmula:**

```typescript
// Base Depreciable
depreciable_base = purchase_price - salvage_value

// Depreciación Mensual
monthly_depreciation = depreciable_base / useful_life_months
```

**Ejemplo:**

```
MacBook Pro:
- Precio de Compra: $12.000.000 COP
- Valor de Salvamento: $2.000.000 COP
- Vida Útil: 36 meses

Base Depreciable: $12.000.000 - $2.000.000 = $10.000.000 COP
Depreciación Mensual: $10.000.000 / 36 = $277.778 COP/mes
```

**Visualización en UI:**

```
┌─────────────────────────────────────────────────────────────┐
│ CÁLCULO DE DEPRECIACIÓN                                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│ Precio de Compra:        $12.000.000 COP                   │
│ Valor de Salvamento:     $2.000.000 COP                    │
│ ─────────────────────────────────────────────────────────── │
│ Base Depreciable:        $10.000.000 COP                   │
│                                                              │
│ Vida Útil:               36 meses                          │
│ ─────────────────────────────────────────────────────────── │
│ Depreciación Mensual:    $277.778 COP/mes                  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Método Saldo Decreciente (Declining Balance)

**Fórmula:**

```typescript
// Tasa de depreciación anual (Double Declining Balance = 2x línea recta)
annual_rate = 2 × (1 / useful_life_months) × 12

// Tasa mensual
monthly_rate = annual_rate / 12

// Depreciación del mes (basada en valor en libros actual)
monthly_depreciation = current_book_value × monthly_rate

// No deprecia por debajo del valor de salvamento
if (current_book_value - monthly_depreciation) < salvage_value:
  monthly_depreciation = current_book_value - salvage_value
```

**Ejemplo (Primer Mes):**

```
MacBook Pro:
- Precio de Compra: $12.000.000 COP
- Valor de Salvamento: $2.000.000 COP
- Vida Útil: 36 meses

Tasa Anual: 2 × (1/36) × 12 = 66.67%
Tasa Mensual: 66.67% / 12 = 5.56%

Depreciación Mes 1: $12.000.000 × 5.56% = $667.200 COP
Valor en Libros Mes 1: $12.000.000 - $667.200 = $11.332.800 COP
```

**Nota:** El método saldo decreciente requiere recalcular cada mes basándose en el valor en libros actual, por lo que la depreciación mensual varía.

---

## 💰 3. IMPACTO EN EL BCR

### 3.1 Integración con Cálculo de BCR

**Fórmula Actualizada del BCR:**

```
BCR = Total Monthly Costs / Total Billable Hours Available

Donde:
Total Monthly Costs = 
    (Salarios con Cargas Sociales) + 
    (Gastos Fijos) + 
    (Amortización de Equipos)  ← NUEVO
```

**Categorización de Equipos:**

- **Hardware, Vehicles, Office Equipment** → Se suman a **Overhead Fijo**
- **Software** → Se suman a **Tools/SaaS**

**Ejemplo de Impacto:**

```
Equipos Activos:
- MacBook Pro: $277.778 COP/mes
- Cámara Canon: $150.000 COP/mes
- Software Adobe: $200.000 COP/mes

Total Amortización Mensual: $627.778 COP/mes

Si el BCR anterior era $50.000 COP/hora con 1,200 horas facturables:
BCR Nuevo = ($50.000 × 1,200 + $627.778) / 1,200 = $50.523 COP/hora

Impacto: +$523 COP/hora (+1.05%)
```

### 3.2 Visualización del Impacto

**Componente UI Sugerido:**

```
┌─────────────────────────────────────────────────────────────┐
│ IMPACTO EN BCR                                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│ BCR Sin Equipos:            $50.000 COP/hora              │
│ Amortización Mensual:       $627.778 COP/mes               │
│ Horas Facturables:          1,200 horas/mes                │
│ ─────────────────────────────────────────────────────────── │
│ Impacto en BCR:             +$523 COP/hora (+1.05%)       │
│                                                              │
│ BCR Con Equipos:            $50.523 COP/hora              │
│                                                              │
│ 💡 Este incremento se refleja automáticamente en todas     │
│    las cotizaciones futuras.                                │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 4. VISUALIZACIÓN DE LA TABLA DE AMORTIZACIÓN

### 4.1 Endpoint de Cronograma de Depreciación

**Endpoint:** `GET /api/v1/settings/equipment/{equipment_id}/depreciation-schedule`

**Query Parameters:**

- `months?: number` - Número de meses a mostrar (opcional, default: `useful_life_months`)

**Respuesta (`DepreciationScheduleResponse`):**

```typescript
interface DepreciationScheduleResponse {
  equipment_id: number;
  equipment_name: string;
  purchase_price: string;          // Decimal como string
  salvage_value: string;           // Decimal como string
  useful_life_months: number;
  depreciation_method: string;
  currency: string;
  
  schedule: DepreciationScheduleEntry[];
  
  summary: {
    total_depreciable: string;     // purchase_price - salvage_value (Decimal como string)
    monthly_depreciation: string;  // Depreciación mensual promedio (Decimal como string)
    total_depreciation: string;    // Depreciación total al final (Decimal como string)
  };
}

interface DepreciationScheduleEntry {
  month: number;                   // Mes desde purchase_date (1, 2, 3, ...)
  month_date: string;              // Fecha del mes (ISO 8601: YYYY-MM-DD)
  depreciation: string;            // Depreciación del mes (Decimal como string)
  accumulated_depreciation: string;  // Depreciación acumulada (Decimal como string)
  book_value: string;              // Valor en libros al final del mes (Decimal como string)
  percentage_depreciated: number;   // Porcentaje depreciado (0-100, Float)
}
```

### 4.2 Visualización de Tabla

**Diseño Requerido:**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ CRONOGRAMA DE DEPRECIACIÓN - MacBook Pro                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│ Precio de Compra: $12.000.000 COP | Valor Salvamento: $2.000.000 COP        │
│ Vida Útil: 36 meses | Método: Línea Recta                                  │
│                                                                              │
├──────┬──────────────┬──────────────┬──────────────────┬──────────────────┤
│ Mes  │ Fecha        │ Depreciación │ Depreciación     │ Valor en Libros   │
│      │              │ Mensual      │ Acumulada        │                   │
├──────┼──────────────┼──────────────┼──────────────────┼──────────────────┤
│  1   │ 2024-01-15   │ $277.778     │ $277.778         │ $11.722.222      │
│  2   │ 2024-02-15   │ $277.778     │ $555.556         │ $11.444.444      │
│  3   │ 2024-03-15   │ $277.778     │ $833.333         │ $11.166.667      │
│ ...  │ ...          │ ...          │ ...              │ ...              │
│  35  │ 2026-11-15   │ $277.778     │ $9.722.222       │ $2.277.778       │
│  36  │ 2026-12-15   │ $277.778     │ $10.000.000      │ $2.000.000       │
├──────┴──────────────┴──────────────┴──────────────────┴──────────────────┤
│                                                                              │
│ Total Depreciable: $10.000.000 COP                                          │
│ Depreciación Mensual: $277.778 COP/mes                                     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Características:**

- Paginación si hay muchos meses (mostrar 12 meses por página)
- Filtro por rango de fechas
- Exportar a CSV/Excel
- Columna de porcentaje depreciado (barra de progreso visual)

---

## 📈 5. GRÁFICO DE VALOR EN EL TIEMPO

### 5.1 Visualización Requerida

**Problema que Resuelve:**
El gráfico de líneas muestra cómo el valor del activo cae mes a mes. Esto ayuda al usuario a entender cuándo debe renovar su tecnología.

**Diseño Requerido:**

```
┌─────────────────────────────────────────────────────────────┐
│ EVOLUCIÓN DEL VALOR DEL ACTIVO                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│ $12M ┤                                                       │
│      │                                                       │
│ $10M ┤                                                       │
│      │  ╭─────────────────────────────────────╮            │
│ $8M  ┤  │                                     │            │
│      │  │                                     │            │
│ $6M  ┤  │                                     │            │
│      │  │                                     │            │
│ $4M  ┤  │                                     │            │
│      │  │                                     │            │
│ $2M  ┤  │                                     │            │
│      │  ╰─────────────────────────────────────╯            │
│ $0M  └───────────────────────────────────────────────────────│
│      Ene 2024    Jul 2024    Ene 2025    Jul 2025    Ene 2026│
│                                                              │
│ Línea Azul: Valor en Libros                                 │
│ Línea Roja: Valor de Salvamento ($2M)                      │
│                                                              │
│ 💡 Cuando el valor en libros alcanza el valor de salvamento,│
│    el equipo ha completado su depreciación contable.       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Datos para el Gráfico:**

- **Eje X:** Meses desde `purchase_date` (o fechas específicas)
- **Eje Y:** Valor en libros (en moneda de compra o moneda principal)
- **Línea Principal:** Valor en libros mes a mes
- **Línea de Referencia:** Valor de salvamento (línea horizontal)

**Interactividad:**

- Hover sobre punto muestra: mes, valor en libros, depreciación del mes
- Zoom in/out para ver períodos específicos
- Toggle para mostrar/ocultar línea de salvamento

---

## 🎯 6. BARRA DE VIDA ÚTIL

### 6.1 Visualización Requerida

**Problema que Resuelve:**
Al lado de cada equipo (ej. MacBook Pro de Ger), poner una barra de progreso que diga: "Este equipo se ha pagado en un 60%. Te quedan 14 meses de vida útil contable".

**Diseño Requerido:**

```
┌─────────────────────────────────────────────────────────────┐
│ MacBook Pro 16" M2                                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│ Precio de Compra: $12.000.000 COP                           │
│ Valor de Salvamento: $2.000.000 COP                         │
│                                                              │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ ████████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  │ │
│ │                                                         │ │
│ │ Este equipo se ha depreciado en un 60%                  │ │
│ │ Te quedan 14 meses de vida útil contable               │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                              │
│ Meses Transcurridos: 22 de 36 meses                        │
│ Valor Actual: $5.333.333 COP                               │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Cálculo:**

```typescript
// Porcentaje depreciado
percentage_depreciated = (total_depreciated / depreciable_base) × 100

// Meses restantes
months_remaining = useful_life_months - months_depreciated

// Mensaje dinámico
if (percentage_depreciated < 50):
  message = `Este equipo se ha depreciado en un ${percentage_depreciated}%. Te quedan ${months_remaining} meses de vida útil contable.`
else if (percentage_depreciated < 90):
  message = `Este equipo se ha depreciado en un ${percentage_depreciated}%. Considera planificar su renovación (${months_remaining} meses restantes).`
else:
  message = `Este equipo está cerca de completar su depreciación (${percentage_depreciated}%). Planifica su renovación pronto (${months_remaining} meses restantes).`
```

**Código de Colores:**

- 🟢 Verde (0-50%): Vida útil saludable
- 🟡 Amarillo (50-80%): Considerar renovación
- 🔴 Rojo (80-100%): Renovación recomendada

---

## ✅ 7. VALIDACIONES DE NEGOCIO

### 7.1 Validaciones de Entrada

**Validaciones que se ejecutan al crear/actualizar:**

1. **Campos Obligatorios:**
   - `name`: Requerido, min 1 carácter
   - `category`: Debe ser una de: "Hardware", "Software", "Vehicles", "Office Equipment"
   - `purchase_price`: Requerido, > 0
   - `purchase_date`: Requerido, fecha válida, **no futura**
   - `currency`: Requerido, una de: "USD", "COP", "EUR", "ARS"
   - `useful_life_months`: Requerido, > 0, típicamente 12-120 meses
   - `salvage_value`: Requerido, >= 0, **< purchase_price**
   - `depreciation_method`: Requerido, "straight_line" o "declining_balance"

2. **Validaciones Condicionales:**
   - Si `currency !== primary_currency`: `exchange_rate_at_purchase` es requerido y > 0
   - `purchase_date` no puede ser fecha futura
   - `salvage_value` no puede ser >= `purchase_price`

3. **Validaciones de Rango:**
   - `useful_life_months`: Recomendado entre 12-120 meses (validación de advertencia, no bloqueante)
   - `purchase_price`: Máximo razonable (ej: 1,000,000,000 COP) para evitar errores

### 7.2 Mensajes de Error

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
  field: "purchase_date",
  message: "La fecha de compra no puede ser futura",
  severity: "error",
  code: "PURCHASE_DATE_NOT_FUTURE"
},
{
  field: "salvage_value",
  message: "El valor de salvamento no puede ser mayor o igual al precio de compra",
  severity: "error",
  code: "SALVAGE_VALUE_TOO_HIGH"
},
{
  field: "exchange_rate_at_purchase",
  message: "La TRM del día de compra es requerida cuando la moneda de compra es diferente a la moneda principal",
  severity: "error",
  code: "EXCHANGE_RATE_REQUIRED"
},
{
  field: "useful_life_months",
  message: "La vida útil típicamente está entre 12 y 120 meses. ¿Está seguro de este valor?",
  severity: "warning",
  code: "USEFUL_LIFE_OUT_OF_RANGE"
}
```

### 7.3 Validaciones de Negocio

**Reglas Adicionales:**

1. **No Eliminar Equipos con Depreciación Acumulada:**
   - Si `total_depreciated > 0`, mostrar advertencia antes de eliminar
   - Permitir soft delete pero mantener registro histórico

2. **Recálculo Automático:**
   - Al actualizar `purchase_price`, `salvage_value`, o `useful_life_months`, recalcular `monthly_depreciation`
   - Al actualizar `depreciation_method`, regenerar cronograma completo

3. **Equipos Completamente Depreciados:**
   - Si `remaining_value <= salvage_value`, marcar como "Completamente Depreciado"
   - Opción para marcar como `is_active = false` automáticamente
   - Mostrar mensaje: "Este equipo ha completado su depreciación contable"

---

## 🎨 8. ESPECIFICACIONES DE DISEÑO UI

### 8.1 Formulario de Registro de Equipo

**Estructura:**

```
┌─────────────────────────────────────────────────────────────┐
│ REGISTRAR NUEVO EQUIPO                                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│ Información Básica:                                          │
│ ┌────────────────────────────────────────────────────────┐  │
│ │ Nombre del Equipo: [MacBook Pro 16" M2        ]      │  │
│ │ Descripción: [Laptop principal de Ger          ]      │  │
│ │ Categoría: [Hardware ▼]                               │  │
│ └────────────────────────────────────────────────────────┘  │
│                                                              │
│ Información de Compra:                                       │
│ ┌────────────────────────────────────────────────────────┐  │
│ │ Precio de Compra: [$12.000.000] COP                   │  │
│ │ Fecha de Compra: [2024-01-15]                         │  │
│ │ Moneda de Compra: [COP ▼]                             │  │
│ │                                                         │  │
│ │ ⚠️ Si la moneda es diferente a la principal (USD),    │  │
│ │    ingresa la TRM del día de compra:                  │  │
│ │ TRM del Día: [$4.200] USD → COP                       │  │
│ └────────────────────────────────────────────────────────┘  │
│                                                              │
│ Parámetros de Depreciación:                                  │
│ ┌────────────────────────────────────────────────────────┐  │
│ │ Vida Útil: [36] meses                                  │  │
│ │ Valor de Salvamento: [$2.000.000] COP                  │  │
│ │                                                         │  │
│ │ 💡 El valor de salvamento es lo que esperas recibir    │  │
│ │    al vender el equipo al final de su vida útil.      │  │
│ │    Esto reduce tu base depreciable y hace tu BCR más   │  │
│ │    competitivo.                                        │  │
│ │                                                         │  │
│ │ Método de Depreciación: [Línea Recta ▼]              │  │
│ │   • Línea Recta: Depreciación constante mensual       │  │
│ │   • Saldo Decreciente: Mayor depreciación al inicio   │  │
│ └────────────────────────────────────────────────────────┘  │
│                                                              │
│ ┌────────────────────────────────────────────────────────┐  │
│ │ CÁLCULO PREVIEW                                        │  │
│ ├────────────────────────────────────────────────────────┤  │
│ │ Base Depreciable:        $10.000.000 COP             │  │
│ │ Depreciación Mensual:    $277.778 COP/mes            │  │
│ │                                                         │  │
│ │ Impacto en BCR:          +$231 COP/hora (+0.46%)      │  │
│ │ (Basado en 1,200 horas facturables/mes)               │  │
│ └────────────────────────────────────────────────────────┘  │
│                                                              │
│ [Cancelar]  [Guardar Equipo]                                │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 8.2 Lista de Equipos

**Estructura:**

```
┌─────────────────────────────────────────────────────────────┐
│ EQUIPOS Y AMORTIZACIÓN                                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│ [Agregar Nuevo Equipo]  [Filtrar por Categoría ▼]         │
│                                                              │
│ ┌────────────────────────────────────────────────────────┐  │
│ │ MacBook Pro 16" M2                          [Activo]  │  │
│ │ Hardware | Comprado: 2024-01-15 | $12.000.000 COP     │  │
│ │                                                         │  │
│ │ ┌───────────────────────────────────────────────────┐  │  │
│ │ │ ████████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │  │  │
│ │ │ Este equipo se ha depreciado en un 60%            │  │  │
│ │ │ Te quedan 14 meses de vida útil contable          │  │  │
│ │ └───────────────────────────────────────────────────┘  │  │
│ │                                                         │  │
│ │ Valor Actual: $5.333.333 COP                          │  │
│ │ Depreciación Mensual: $277.778 COP/mes                │  │
│ │                                                         │  │
│ │ [Ver Cronograma] [Editar] [Desactivar]                │  │
│ └────────────────────────────────────────────────────────┘  │
│                                                              │
│ ┌────────────────────────────────────────────────────────┐  │
│ │ Cámara Canon EOS R5                        [Activo]   │  │
│ │ Hardware | Comprado: 2023-06-10 | $8.500.000 COP     │  │
│ │                                                         │  │
│ │ ┌───────────────────────────────────────────────────┐  │  │
│ │ │ ████████████████████████████████░░░░░░░░░░░░░░░░ │  │  │
│ │ │ Este equipo se ha depreciado en un 75%            │  │  │
│ │ │ Considera planificar su renovación (9 meses rest.)│  │  │
│ │ └───────────────────────────────────────────────────┘  │  │
│ │                                                         │  │
│ │ Valor Actual: $3.125.000 COP                          │  │
│ │ Depreciación Mensual: $150.000 COP/mes                │  │
│ │                                                         │  │
│ │ [Ver Cronograma] [Editar] [Desactivar]                │  │
│ └────────────────────────────────────────────────────────┘  │
│                                                              │
│ RESUMEN:                                                     │
│ ┌────────────────────────────────────────────────────────┐  │
│ │ Total Equipos Activos: 2                               │  │
│ │ Amortización Mensual Total: $427.778 COP/mes          │  │
│ │ Impacto en BCR: +$356 COP/hora                         │  │
│ └────────────────────────────────────────────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 8.3 Vista de Detalle de Equipo

**Estructura:**

```
┌─────────────────────────────────────────────────────────────┐
│ MacBook Pro 16" M2                                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│ [← Volver]  [Editar]  [Desactivar]                         │
│                                                              │
│ Información General:                                        │
│ ┌────────────────────────────────────────────────────────┐  │
│ │ Categoría: Hardware                                    │  │
│ │ Comprado: 15 de Enero, 2024                           │  │
│ │ Precio de Compra: $12.000.000 COP                     │  │
│ │ Valor de Salvamento: $2.000.000 COP                    │  │
│ │ Vida Útil: 36 meses                                    │  │
│ │ Método: Línea Recta                                    │  │
│ └────────────────────────────────────────────────────────┘  │
│                                                              │
│ Estado Actual:                                              │
│ ┌────────────────────────────────────────────────────────┐  │
│ │ ┌──────────────────────────────────────────────────┐  │  │
│ │ │ ████████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │  │  │
│ │ │ Este equipo se ha depreciado en un 60%            │  │  │
│ │ │ Te quedan 14 meses de vida útil contable          │  │  │
│ │ └──────────────────────────────────────────────────┘  │  │
│ │                                                         │  │
│ │ Meses Transcurridos: 22 de 36 meses                   │  │
│ │ Depreciación Acumulada: $6.111.111 COP                │  │
│ │ Valor en Libros Actual: $5.333.333 COP               │  │
│ │ Depreciación Mensual: $277.778 COP/mes                │  │
│ └────────────────────────────────────────────────────────┘  │
│                                                              │
│ Gráfico de Valor en el Tiempo:                              │
│ ┌────────────────────────────────────────────────────────┐  │
│ │ [Gráfico de líneas mostrando evolución del valor]     │  │
│ └────────────────────────────────────────────────────────┘  │
│                                                              │
│ Cronograma de Depreciación:                                  │
│ ┌────────────────────────────────────────────────────────┐  │
│ │ [Tabla con meses, depreciación, acumulada, valor]     │  │
│ │ [Ver Cronograma Completo →]                            │  │
│ └────────────────────────────────────────────────────────┘  │
│                                                              │
│ Impacto en BCR:                                             │
│ ┌────────────────────────────────────────────────────────┐  │
│ │ Este equipo agrega $277.778 COP/mes al overhead fijo. │  │
│ │ Impacto en BCR: +$231 COP/hora (+0.46%)              │  │
│ └────────────────────────────────────────────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔗 9. INTEGRACIÓN CON OTROS MÓDULOS

### 9.1 Integración con Cálculo de BCR

**Al crear/editar/eliminar equipo:**

- Se invalida el cache del BCR (`blended_cost_rate:{currency}:tenant_{id}`)
- El BCR se recalcula automáticamente en la próxima cotización
- Se muestra impacto en tiempo real en el formulario de equipo

**Al ver BCR:**

- El desglose incluye "Amortización de Equipos" como categoría separada
- Se muestra total de amortización mensual
- Se muestra impacto porcentual en el BCR

### 9.2 Integración con Dashboard

**Al guardar un equipo:**

- Se actualiza el resumen de equipos en el dashboard
- Se muestra impacto total en BCR
- Se muestran alertas para equipos próximos a completar depreciación

---

## 📝 10. NOTAS TÉCNICAS

### 10.1 Precisión Monetaria

**ESTÁNDAR NOUGRAM:**

- Todos los valores monetarios se manejan como `Decimal` en el backend
- Se serializan como `string` en las respuestas JSON
- El frontend debe usar librerías de precisión decimal (ej: `decimal.js`) para cálculos
- Nunca usar `float` o `number` de JavaScript para cálculos monetarios

### 10.2 Manejo de Monedas y TRM

**Reglas:**

- Si `currency === primary_currency`: No se requiere `exchange_rate_at_purchase`
- Si `currency !== primary_currency`: `exchange_rate_at_purchase` es obligatorio
- La depreciación mensual se calcula en la moneda de compra
- Se convierte a moneda principal usando la TRM histórica (una sola vez)
- El valor no se re-expresa mes a mes con fluctuaciones cambiarias

**Ejemplo:**

```
Equipo comprado en USD:
- Precio: $2,000 USD
- TRM del día: $4,200 COP/USD
- Precio en COP: $8,400,000 COP (fijo, no cambia)

Depreciación mensual:
- En USD: $55.56 USD/mes (calculado en USD)
- En COP: $233,333 COP/mes (usando TRM histórica, fijo)
```

### 10.3 Manejo de Errores

**Códigos de Error Comunes:**

- `400 Bad Request`: Datos inválidos (validación fallida)
- `403 Forbidden`: Sin permisos para modificar equipos
- `404 Not Found`: Equipo no encontrado
- `422 Unprocessable Entity`: Lógica de negocio violada (ej: `salvage_value >= purchase_price`)

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

## 🎯 11. CRITERIOS DE ÉXITO

### 11.1 Métricas de Usabilidad

- **Tiempo de Registro:** Usuario puede registrar un equipo en < 3 minutos
- **Comprensión:** > 80% de usuarios entienden el concepto de valor de salvamento después de usar el sistema
- **Precisión:** < 2% de equipos registrados con datos inválidos

### 11.2 Métricas de Negocio

- **Adopción:** > 60% de organizaciones registran al menos 3 equipos
- **Impacto en BCR:** Equipos representan 5-15% del overhead total en organizaciones típicas
- **Renovación:** > 40% de usuarios usan la barra de vida útil para planificar renovaciones

---

## 📚 12. REFERENCIAS

- **Backend Plan:** `docs/development/PLAN_TRABAJO_AMORTIZACION_BACKEND.md`
- **Backend Models:** `backend/app/models/equipment.py` (a implementar)
- **Backend Schemas:** `backend/app/schemas/equipment.py` (a implementar)
- **Backend Endpoints:** `backend/app/api/v1/endpoints/equipment.py` (a implementar)
- **Cálculos:** `backend/app/core/calculations.py` (modificar para incluir equipos)
- **Servicio de Depreciación:** `backend/app/services/depreciation_service.py` (a implementar)

---

**Fin del Documento**
