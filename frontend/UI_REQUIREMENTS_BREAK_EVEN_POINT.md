# UI Requirements: Módulo de Punto de Equilibrio (Break-Even Point)

**Versión:** 1.0  
**Fecha:** 2026-01-25  
**Documento Base:** `BACKEND_SPEC_BREAK_EVEN_POINT.md`  
**Estado:** Pendiente de Diseño

---

## Resumen Ejecutivo

Este documento detalla los requerimientos de UI para el módulo de **Punto de Equilibrio (Break-Even Point)** que permite a las agencias calcular cuántas horas billables o ingresos necesitan para cubrir todos sus costos operacionales, proyectar escenarios financieros y tomar decisiones estratégicas basadas en datos.

**Objetivo:** Diseñar interfaces de usuario intuitivas que permitan visualizar el punto de equilibrio, simular escenarios financieros y proyectar crecimiento, ayudando a las agencias a tomar decisiones estratégicas informadas.

**Alcance:**

- Dashboard principal de punto de equilibrio
- Visualización de estado actual vs equilibrio
- Simulador de escenarios financieros
- Proyección temporal de crecimiento
- Comparación de escenarios lado a lado

**Principios de Diseño:**

- **Claridad Visual:** Indicadores claros de estado (above/at/below equilibrio)
- **Acción Orientada:** Mostrar qué acciones tomar para alcanzar equilibrio
- **Simplicidad:** Conceptos financieros complejos presentados de forma simple
- **Comparación Visual:** Escenarios lado a lado para fácil comparación

---

## 1. Pantalla Principal: Dashboard de Punto de Equilibrio

### 1.1 Contexto y Ubicación

**Pantalla:** Dashboard de análisis de punto de equilibrio  
**Ruta:** `/analytics/break-even`  
**Acceso:** Desde menú lateral "Analytics" → "Punto de Equilibrio"

### 1.2 Data Mapping

**Endpoint:** `GET /api/v1/analytics/break-even`

**Response:**

```typescript
interface BreakEvenAnalysisResponse {
  period: "monthly" | "quarterly" | "annual";
  currency: string;
  
  // Costos
  total_fixed_costs: string;      // Decimal como string
  total_costs: string;
  
  // Horas
  total_billable_hours_available: number;
  break_even_hours: number;
  current_allocated_hours: number;
  hours_to_break_even: number;
  safety_margin_hours: number;
  safety_margin_percentage: number;
  
  // Ingresos
  break_even_revenue: string;
  current_projected_revenue: string;
  revenue_to_break_even: string;
  average_margin: number;
  
  // Métricas
  operating_leverage: number;
  current_utilization_rate: number;
  break_even_utilization_rate: number;
  
  // Estado
  status: "above_break_even" | "at_break_even" | "below_break_even";
  status_message: string;
  
  // Proyección
  months_to_break_even?: number;
  projected_break_even_date?: string;
}
```

### 1.3 Diseño del Dashboard

**Layout Principal:**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 📊 Punto de Equilibrio                                    [Filtros ▼] [⚙️] │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ ┌───────────────────────────────────────────────────────────────────────┐ │
│ │ Estado Actual                                                         │ │
│ │                                                                       │ │
│ │ 🟡 Por debajo del equilibrio                                          │ │
│ │                                                                       │ │
│ │ Necesitas 50 horas adicionales para alcanzar el punto de equilibrio  │ │
│ │                                                                       │ │
│ │ [Ver Proyección] [Simular Escenarios]                                 │ │
│ └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ ┌───────────────────────────────────────────────────────────────────────┐ │
│ │ Métricas Clave                                                         │ │
│ │                                                                       │ │
│ │ ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                │ │
│ │ │ Horas        │  │ Ingresos     │  │ Utilización  │                │ │
│ │ │              │  │              │  │              │                │ │
│ │ │ Equilibrio:  │  │ Equilibrio:  │  │ Actual:      │                │ │
│ │ │ 300.0h       │  │ $20.000.000  │  │ 50.0%        │                │ │
│ │ │              │  │              │  │              │                │ │
│ │ │ Asignadas:   │  │ Proyectados: │  │ Equilibrio:  │                │ │
│ │ │ 250.0h       │  │ $16.666.667  │  │ 60.0%        │                │ │
│ │ │              │  │              │  │              │                │ │
│ │ │ Faltan:      │  │ Faltan:      │  │ Diferencia:  │                │ │
│ │ │ 50.0h        │  │ $3.333.333   │  │ -10.0%       │                │ │
│ │ └──────────────┘  └──────────────┘  └──────────────┘                │ │
│ └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ ┌───────────────────────────────────────────────────────────────────────┐ │
│ │ Visualización de Equilibrio                                            │ │
│ │                                                                       │ │
│ │ Horas Billables                                                       │ │
│ │                                                                       │ │
│ │ 500h ┤                                                                │ │
│ │      │                                                                │ │
│ │ 400h ┤                                                                │ │
│ │      │                                                                │ │
│ │ 300h ┤═══════════════════════════════════════════════════════════════│ │
│ │      │                    🎯 Punto de Equilibrio                      │ │
│ │ 250h ┤████████████████████████████████████████░░░░░░░░░░░░░░░░░░░░░░│ │
│ │      │                    📊 Horas Asignadas                          │ │
│ │ 200h ┤                                                                │ │
│ │      │                                                                │ │
│ │ 100h ┤                                                                │ │
│ │      │                                                                │ │
│ │   0h └───────────────────────────────────────────────────────────────  │ │
│ │                                                                       │ │
│ │ [500h] Horas Disponibles  │  [300h] Equilibrio  │  [250h] Asignadas │ │
│ └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ ┌───────────────────────────────────────────────────────────────────────┐ │
│ │ Desglose de Costos                                                    │ │
│ │                                                                       │ │
│ │ Costos Fijos Totales: $15.000.000 COP/mes                            │ │
│ │                                                                       │ │
│ │ ┌─────────────────────────────────────────────────────────────────┐ │ │
│ │ │ 💼 Salarios (con cargas sociales)              $12.000.000 (80%) │ │ │
│ │ │ [████████████████████████████████████████████████████████]      │ │ │
│ │ ├─────────────────────────────────────────────────────────────────┤ │ │
│ │ │ 🏢 Overhead (oficina, servicios)              $2.000.000 (13%)   │ │ │
│ │ │ [████████]                                                       │ │ │
│ │ ├─────────────────────────────────────────────────────────────────┤ │ │
│ │ │ 💻 Software y Herramientas                  $1.000.000 (7%)    │ │ │
│ │ │ [████]                                                           │ │ │
│ │ └─────────────────────────────────────────────────────────────────┘ │ │
│ └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ ┌───────────────────────────────────────────────────────────────────────┐ │
│ │ Acciones Rápidas                                                      │ │
│ │                                                                       │ │
│ │ [Simular Escenarios] [Ver Proyección] [Exportar Reporte]            │ │
│ └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### 1.4 Componente: Estado Actual

**Diseño:**

```
┌───────────────────────────────────────────────────────────────────────┐
│ Estado Actual                                                         │
│                                                                       │
│ 🟡 Por debajo del equilibrio                                          │
│                                                                       │
│ Necesitas 50 horas adicionales para alcanzar el punto de equilibrio  │
│                                                                       │
│ Proyección: Alcanzarás el equilibrio en aproximadamente 1.5 meses    │
│ (15 de Marzo, 2026)                                                  │
│                                                                       │
│ [Ver Proyección Detallada] [Simular Escenarios]                      │
└───────────────────────────────────────────────────────────────────────┘
```

**Indicadores de Estado:**

- 🟢 Verde: "Por encima del equilibrio" (above_break_even)
- 🟡 Amarillo: "Por debajo del equilibrio" (below_break_even)
- 🔵 Azul: "En el punto de equilibrio" (at_break_even)

**Información Mostrada:**

- Estado actual (above/at/below)
- Mensaje descriptivo del estado
- Horas/ingresos faltantes para equilibrio
- Proyección de cuándo se alcanzará (si aplica)

---

### 1.5 Componente: Métricas Clave

**Diseño (Cards):**

```
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ Horas        │  │ Ingresos     │  │ Utilización  │
│              │  │              │  │              │
│ Equilibrio:  │  │ Equilibrio:  │  │ Actual:      │
│ 300.0h       │  │ $20.000.000  │  │ 50.0%        │
│              │  │              │  │              │
│ Asignadas:   │  │ Proyectados: │  │ Equilibrio:  │
│ 250.0h       │  │ $16.666.667  │  │ 60.0%        │
│              │  │              │  │              │
│ Faltan:      │  │ Faltan:      │  │ Diferencia:  │
│ 50.0h 🟡     │  │ $3.333.333   │  │ -10.0% 🟡    │
└──────────────┘  └──────────────┘  └──────────────┘
```

**Información por Card:**

1. **Horas:**
   - Horas de equilibrio
   - Horas asignadas actualmente
   - Horas faltantes (con indicador de color)

2. **Ingresos:**
   - Ingresos de equilibrio
   - Ingresos proyectados
   - Ingresos faltantes (con indicador de color)

3. **Utilización:**
   - Utilización actual
   - Utilización de equilibrio
   - Diferencia (con indicador de color)

**Indicadores de Color:**

- 🟢 Verde: Por encima del equilibrio
- 🟡 Amarillo: Por debajo del equilibrio
- 🔵 Azul: En equilibrio

---

### 1.6 Componente: Visualización de Equilibrio

**Tipo:** Gráfico de barras o área

**Diseño:**

```
Horas Billables

500h ┤
     │
400h ┤
     │
300h ┤═══════════════════════════════════════════════════════════════
     │                    🎯 Punto de Equilibrio
250h ┤████████████████████████████████████████░░░░░░░░░░░░░░░░░░░░░░
     │                    📊 Horas Asignadas
200h ┤
     │
100h ┤
     │
  0h └───────────────────────────────────────────────────────────────

[500h] Horas Disponibles  │  [300h] Equilibrio  │  [250h] Asignadas
```

**Elementos Visuales:**

- Línea horizontal marcando punto de equilibrio
- Barra/área mostrando horas asignadas
- Zona sombreada mostrando horas faltantes
- Leyenda con valores clave

**Interactividad:**

- Hover sobre barras: Mostrar valores exactos
- Click en leyenda: Mostrar/ocultar elementos

---

### 1.7 Componente: Desglose de Costos

**Diseño:**

```
┌───────────────────────────────────────────────────────────────────────┐
│ Desglose de Costos                                                    │
│                                                                       │
│ Costos Fijos Totales: $15.000.000 COP/mes                            │
│                                                                       │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ 💼 Salarios (con cargas sociales)              $12.000.000 (80%) │ │
│ │ [████████████████████████████████████████████████████████]      │ │
│ ├─────────────────────────────────────────────────────────────────┤ │
│ │ 🏢 Overhead (oficina, servicios)              $2.000.000 (13%)   │ │
│ │ [████████]                                                       │ │
│ ├─────────────────────────────────────────────────────────────────┤ │
│ │ 💻 Software y Herramientas                  $1.000.000 (7%)    │ │
│ │ [████]                                                           │ │
│ └─────────────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────────────┘
```

**Información:**

- Total de costos fijos mensuales
- Desglose por categoría (Salarios, Overhead, Software)
- Porcentaje de cada categoría
- Barras de progreso visuales

**Categorías:**

- Salarios (con cargas sociales)
- Overhead (oficina, servicios públicos, etc.)
- Software y Herramientas
- Otros costos fijos

---

## 2. Pantalla: Simulador de Escenarios

### 2.1 Contexto y Ubicación

**Pantalla:** Simulador de escenarios financieros  
**Ruta:** `/analytics/break-even/scenarios`  
**Acceso:** Click en "Simular Escenarios" desde dashboard principal

### 2.2 Data Mapping

**Endpoint:** `POST /api/v1/analytics/break-even/scenarios`

**Payload:**

```typescript
interface BreakEvenScenarioRequest {
  scenarios: ScenarioConfig[];
  currency?: string;
}

interface ScenarioConfig {
  name: string;
  bcr_multiplier: number;        // 1.0 = sin cambio, 1.1 = +10%
  fixed_costs_adjustment: number; // 0 = sin cambio, positivo = aumentar
  average_margin_adjustment: number; // 0 = sin cambio, 0.15 = +15%
}
```

**Response:**

```typescript
interface BreakEvenScenariosResponse {
  base_scenario: {
    break_even_hours: number;
    break_even_revenue: string;
    current_allocated_hours: number;
    hours_to_break_even: number;
  };
  scenarios: ScenarioResult[];
}

interface ScenarioResult {
  name: string;
  break_even_hours: number;
  break_even_revenue: string;
  hours_to_break_even: number;
  impact: {
    hours_change: number;
    revenue_change: string;
    impact_percentage: number;
  };
}
```

### 2.3 Diseño del Simulador

**Layout Principal:**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ ← Volver a Punto de Equilibrio                                              │
│                                                                             │
│ 🎯 Simulador de Escenarios                                                  │
│                                                                             │
│ Simula el impacto de cambios en tu negocio sobre el punto de equilibrio    │
│                                                                             │
│ ┌───────────────────────────────────────────────────────────────────────┐ │
│ │ Escenario Base                                                        │ │
│ │                                                                       │ │
│ │ Horas de Equilibrio: 300.0h                                          │ │
│ │ Ingresos de Equilibrio: $20.000.000                                  │ │
│ │ Horas Asignadas: 250.0h                                              │ │
│ │ Horas Faltantes: 50.0h                                               │ │
│ └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ ┌───────────────────────────────────────────────────────────────────────┐ │
│ │ Escenarios Simulados                                    [+ Agregar]   │ │
│ │                                                                       │ │
│ │ ┌─────────────────────────────────────────────────────────────────┐ │ │
│ │ │ Escenario 1: Aumentar BCR 10%                                    │ │ │
│ │ │                                                                   │ │ │
│ │ │ Cambios:                                                          │ │ │
│ │ │ • BCR: +10%                                                       │ │ │
│ │ │                                                                   │ │ │
│ │ │ Impacto:                                                          │ │ │
│ │ │ • Horas de Equilibrio: 272.7h (-27.3h, -9.1%)                   │ │ │
│ │ │ • Ingresos de Equilibrio: $22.000.000 (+$2.000.000)             │ │ │
│ │ │ • Horas Faltantes: 22.7h (mejora)                                │ │ │
│ │ │                                                                   │ │ │
│ │ │ 🟢 Este escenario mejora tu posición                             │ │ │
│ │ │                                                                   │ │ │
│ │ │ [Editar] [Eliminar]                                               │ │ │
│ │ └─────────────────────────────────────────────────────────────────┘ │ │
│ │                                                                       │ │
│ │ ┌─────────────────────────────────────────────────────────────────┐ │ │
│ │ │ Escenario 2: Agregar nuevo empleado                              │ │ │
│ │ │                                                                   │ │ │
│ │ │ Cambios:                                                          │ │ │
│ │ │ • Costos Fijos: +$5.000.000/mes                                  │ │ │
│ │ │                                                                   │ │ │
│ │ │ Impacto:                                                          │ │ │
│ │ │ • Horas de Equilibrio: 400.0h (+100h, +33.3%)                   │ │ │
│ │ │ • Ingresos de Equilibrio: $25.000.000 (+$5.000.000)             │ │ │
│ │ │ • Horas Faltantes: 150.0h (empeora)                             │ │ │
│ │ │                                                                   │ │ │
│ │ │ 🔴 Este escenario empeora tu posición                            │ │ │
│ │ │                                                                   │ │ │
│ │ │ [Editar] [Eliminar]                                               │ │ │
│ │ └─────────────────────────────────────────────────────────────────┘ │ │
│ └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ ┌───────────────────────────────────────────────────────────────────────┐ │
│ │ Comparación Visual                                                     │ │
│ │                                                                       │ │
│ │ Horas de Equilibrio                                                   │ │
│ │                                                                       │ │
│ │ 400h ┤                                                                │ │
│ │      │                                                                │ │
│ │ 350h ┤                                                                │ │
│ │      │                                                                │ │
│ │ 300h ┤═══════════════════════════════════════════════════════════════│ │
│ │      │                    🎯 Base                                     │ │
│ │ 272h ┤██████████████████████████████████████████████████████████████│ │
│ │      │                    📊 Escenario 1 (+10% BCR)                  │ │
│ │ 250h ┤                                                                │ │
│ │      │                                                                │ │
│ │ 200h ┤                                                                │ │
│ │      │                                                                │ │
│ │   0h └───────────────────────────────────────────────────────────────  │ │
│ │                                                                       │ │
│ │ [Base] [Escenario 1] [Escenario 2]                                   │ │
│ └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### 2.4 Componente: Formulario de Escenario

**Trigger:** Click en "+ Agregar" o "Editar" en escenario existente

**Modal/Drawer:**

```
┌─────────────────────────────────────────────────────────────┐
│ Crear Escenario                                        [X]    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│ Nombre del Escenario *                                      │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ [Aumentar BCR 10%]                                      │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                              │
│ Cambios en el Negocio                                       │
│                                                              │
│ Multiplicador de BCR                                        │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ [1.10] (1.0 = sin cambio, 1.1 = +10%)                  │ │
│ └────────────────────────────────────────────────────────┘ │
│ ℹ️ Un BCR más alto reduce las horas necesarias para equilibrio│
│                                                              │
│ Ajuste a Costos Fijos (mensual)                            │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ [+5000000] COP (positivo = aumentar, negativo = reducir)│ │
│ └────────────────────────────────────────────────────────┘ │
│ ℹ️ Ejemplo: +$5.000.000 para simular contratar empleado   │
│                                                              │
│ Ajuste al Margen Promedio                                   │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ [+0.15] (0 = sin cambio, 0.15 = +15%)                  │ │
│ └────────────────────────────────────────────────────────┘ │
│ ℹ️ Un margen más alto reduce los ingresos necesarios        │
│                                                              │
│ ┌──────────────┐  ┌──────────────┐                        │
│ │   Cancelar   │  │   Simular    │                        │
│ └──────────────┘  └──────────────┘                        │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Campos:**

1. **Nombre del Escenario:**
   - Input de texto
   - Ejemplos: "Aumentar BCR 10%", "Contratar nuevo Developer", "Aumentar precios 15%"

2. **Multiplicador de BCR:**
   - Input numérico (decimal, 2 decimales)
   - Default: 1.0 (sin cambio)
   - Rango: 0.1 - 5.0
   - Tooltip explicativo

3. **Ajuste a Costos Fijos:**
   - Input numérico (moneda)
   - Default: 0 (sin cambio)
   - Positivo = aumentar costos
   - Negativo = reducir costos
   - Tooltip con ejemplos

4. **Ajuste al Margen Promedio:**
   - Input numérico (decimal, 2 decimales)
   - Default: 0 (sin cambio)
   - Rango: -1.0 a 1.0
   - Tooltip explicativo

**Validaciones:**

- Nombre requerido
- Al menos un cambio debe ser diferente de 0
- Valores dentro de rangos permitidos

---

### 2.5 Componente: Card de Escenario

**Diseño:**

```
┌───────────────────────────────────────────────────────────────────────┐
│ Escenario 1: Aumentar BCR 10%                              [✏️] [🗑️] │
├───────────────────────────────────────────────────────────────────────┤
│                                                                       │
│ Cambios Aplicados:                                                    │
│ • BCR: +10% (de $50.000/h a $55.000/h)                               │
│                                                                       │
│ Impacto en Punto de Equilibrio:                                       │
│                                                                       │
│ ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                │
│ │ Horas        │  │ Ingresos     │  │ Cambio       │                │
│ │              │  │              │  │              │                │
│ │ Equilibrio:  │  │ Equilibrio:  │  │ Horas:       │                │
│ │ 272.7h       │  │ $22.000.000  │  │ -27.3h       │                │
│ │              │  │              │  │ (-9.1%) 🟢   │                │
│ │              │  │              │  │              │                │
│ │ Faltantes:   │  │ Faltan:      │  │ Ingresos:    │                │
│ │ 22.7h        │  │ $5.333.333   │  │ +$2.000.000  │                │
│ └──────────────┘  └──────────────┘  └──────────────┘                │
│                                                                       │
│ 🟢 Este escenario mejora tu posición (menos horas para equilibrio)   │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

**Información Mostrada:**

- Nombre del escenario
- Cambios aplicados (resumen)
- Impacto en horas de equilibrio
- Impacto en ingresos de equilibrio
- Cambio porcentual vs escenario base
- Indicador de si mejora/empeora la posición

**Indicadores:**

- 🟢 Verde: Mejora la posición (menos horas/ingresos para equilibrio)
- 🔴 Rojo: Empeora la posición (más horas/ingresos para equilibrio)
- 🔵 Azul: Sin cambio significativo

---

### 2.6 Componente: Comparación Visual

**Tipo:** Gráfico de barras agrupadas

**Diseño:**

```
Horas de Equilibrio

400h ┤
     │
350h ┤
     │
300h ┤═══════════════════════════════════════════════════════════════
     │                    🎯 Base
272h ┤██████████████████████████████████████████████████████████████
     │                    📊 Escenario 1 (+10% BCR)
400h ┤██████████████████████████████████████████████████████████████
     │                    📊 Escenario 2 (+Empleado)
250h ┤
     │
200h ┤
     │
  0h └───────────────────────────────────────────────────────────────

[Base] [Escenario 1] [Escenario 2]
```

**Elementos:**

- Barras para cada escenario (colores diferentes)
- Línea de referencia para escenario base
- Leyenda interactiva (click para mostrar/ocultar)
- Valores exactos en hover

---

## 3. Pantalla: Proyección Temporal

### 3.1 Contexto y Ubicación

**Pantalla:** Proyección temporal de punto de equilibrio  
**Ruta:** `/analytics/break-even/projection`  
**Acceso:** Click en "Ver Proyección" desde dashboard principal

### 3.2 Data Mapping

**Endpoint:** `GET /api/v1/analytics/break-even/projection`

**Query Parameters:**

- `months_ahead`: integer (default: 12)
- `growth_rate`: float (default: 0.0)

**Response:**

```typescript
interface BreakEvenProjectionResponse {
  current_status: {
    allocated_hours: number;
    break_even_hours: number;
    hours_to_break_even: number;
  };
  projection: MonthProjection[];
  break_even_date?: string;
  months_to_break_even?: number;
}

interface MonthProjection {
  month: string;              // "2026-02"
  allocated_hours: number;
  break_even_hours: number;
  hours_to_break_even: number;
  status: "below_break_even" | "at_break_even" | "above_break_even";
  break_even_date?: string;
  profit_hours?: number;
}
```

### 3.3 Diseño de la Pantalla

**Layout Principal:**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ ← Volver a Punto de Equilibrio                                              │
│                                                                             │
│ 📈 Proyección Temporal                                                      │
│                                                                             │
│ Proyecta cuándo alcanzarás el punto de equilibrio basado en tu ritmo actual│
│                                                                             │
│ ┌───────────────────────────────────────────────────────────────────────┐ │
│ │ Configuración de Proyección                              [⚙️]        │ │
│ │                                                                       │ │
│ │ Meses a proyectar: [12] meses                                        │ │
│ │ Tasa de crecimiento mensual: [0%] (opcional)                         │ │
│ │                                                                       │ │
│ │ ℹ️ La tasa de crecimiento simula un aumento mensual en asignaciones  │ │
│ └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ ┌───────────────────────────────────────────────────────────────────────┐ │
│ │ Resumen de Proyección                                                  │ │
│ │                                                                       │ │
│ │ 🎯 Fecha estimada de equilibrio: 15 de Marzo, 2026                    │ │
│ │ ⏱️ Tiempo estimado: 1.5 meses                                         │ │
│ │                                                                       │ │
│ │ Basado en:                                                            │ │
│ │ • Velocidad actual: ~33 horas/mes                                     │ │
│ │ • Horas actuales: 250.0h                                              │ │
│ │ • Horas necesarias: 300.0h                                            │ │
│ └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ ┌───────────────────────────────────────────────────────────────────────┐ │
│ │ Proyección Mes a Mes                                                   │ │
│ │                                                                       │ │
│ │ ┌─────────────────────────────────────────────────────────────────┐ │ │
│ │ │ Mes        │ Horas Asignadas │ Equilibrio │ Estado    │ Profit │ │ │
│ │ ├─────────────────────────────────────────────────────────────────┤ │ │
│ │ │ 2026-02    │ 275.0h          │ 300.0h     │ 🟡 Abajo  │ -      │ │ │
│ │ │ 2026-03    │ 300.0h          │ 300.0h     │ 🔵 Equilib│ -      │ │ │
│ │ │            │                 │            │           │        │ │ │
│ │ │            │ 🎯 Equilibrio alcanzado el 15 de Marzo            │ │ │
│ │ ├─────────────────────────────────────────────────────────────────┤ │ │
│ │ │ 2026-04    │ 325.0h          │ 300.0h     │ 🟢 Arriba │ +25h   │ │ │
│ │ │ 2026-05    │ 350.0h          │ 300.0h     │ 🟢 Arriba │ +50h   │ │ │
│ │ │ 2026-06    │ 375.0h          │ 300.0h     │ 🟢 Arriba │ +75h   │ │ │
│ │ └─────────────────────────────────────────────────────────────────┘ │ │
│ └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ ┌───────────────────────────────────────────────────────────────────────┐ │
│ │ Gráfico de Proyección                                                  │ │
│ │                                                                       │ │
│ │   400h ┤                                                               │ │
│ │        │                                                               │ │
│ │   350h ┤                                                               │ │
│ │        │                                                               │ │
│ │   300h ┤═════════════════════════════════════════════════════════════│ │
│ │        │                    🎯 Punto de Equilibrio                    │ │
│ │   275h ┤████████████████████████████████████████░░░░░░░░░░░░░░░░░░░░│ │
│ │        │                    📊 Proyección                            │ │
│ │   250h ┤                                                                │ │
│ │        │                                                                │ │
│ │   200h ┤                                                                │ │
│ │        │                                                                │ │
│ │     0h └─────────────────────────────────────────────────────────────  │ │
│ │        Feb    Mar    Apr    May    Jun                                │ │
│ │                                                                       │ │
│ │ [Horas Asignadas] [Punto de Equilibrio]                              │ │
│ └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### 3.4 Componente: Configuración de Proyección

**Diseño:**

```
┌───────────────────────────────────────────────────────────────────────┐
│ Configuración de Proyección                              [⚙️]        │
│                                                                       │
│ Meses a proyectar: [12] meses                                        │
│ Tasa de crecimiento mensual: [0%] (opcional)                         │
│                                                                       │
│ ℹ️ La tasa de crecimiento simula un aumento mensual en asignaciones  │
│                                                                       │
│ Ejemplos:                                                             │
│ • 0% = Mantener ritmo actual                                         │
│ • 5% = Aumentar asignaciones 5% cada mes                             │
│ • -10% = Reducir asignaciones 10% cada mes                           │
└───────────────────────────────────────────────────────────────────────┘
```

**Campos:**

1. **Meses a proyectar:**
   - Input numérico (integer)
   - Default: 12
   - Rango: 1-36 meses

2. **Tasa de crecimiento mensual:**
   - Input numérico (decimal, 1 decimal)
   - Default: 0%
   - Rango: -50% a 200%
   - Opcional (puede ser 0 o negativo)

---

### 3.5 Componente: Tabla de Proyección

**Diseño:**

```
┌───────────────────────────────────────────────────────────────────────┐
│ Mes        │ Horas Asignadas │ Equilibrio │ Estado    │ Profit        │
├───────────────────────────────────────────────────────────────────────┤
│ 2026-02    │ 275.0h          │ 300.0h     │ 🟡 Abajo  │ -             │
│ 2026-03    │ 300.0h          │ 300.0h     │ 🔵 Equilib│ -             │
│            │                 │            │           │               │
│            │ 🎯 Equilibrio alcanzado el 15 de Marzo                  │
├───────────────────────────────────────────────────────────────────────┤
│ 2026-04    │ 325.0h          │ 300.0h     │ 🟢 Arriba │ +25h          │
│ 2026-05    │ 350.0h          │ 300.0h     │ 🟢 Arriba │ +50h          │
│ 2026-06    │ 375.0h          │ 300.0h     │ 🟢 Arriba │ +75h          │
└───────────────────────────────────────────────────────────────────────┘
```

**Columnas:**

1. **Mes:** Mes proyectado (formato: "YYYY-MM")
2. **Horas Asignadas:** Horas proyectadas para ese mes
3. **Equilibrio:** Horas de equilibrio (constante)
4. **Estado:** Indicador visual (🟡/🔵/🟢)
5. **Profit:** Horas por encima del equilibrio (si aplica)

**Destacado Especial:**

- Mes donde se alcanza equilibrio: Resaltado con badge especial
- Fecha exacta de equilibrio mostrada

---

### 3.6 Componente: Gráfico de Proyección

**Tipo:** Gráfico de líneas o área

**Diseño:**

```
   400h ┤
        │
   350h ┤
        │
   300h ┤═════════════════════════════════════════════════════════════
        │                    🎯 Punto de Equilibrio
   275h ┤████████████████████████████████████████░░░░░░░░░░░░░░░░░░░░
        │                    📊 Proyección
   250h ┤
        │
   200h ┤
        │
     0h └─────────────────────────────────────────────────────────────
        Feb    Mar    Apr    May    Jun

[Horas Asignadas] [Punto de Equilibrio]
```

**Elementos:**

- Línea horizontal: Punto de equilibrio (constante)
- Línea/área: Proyección de horas asignadas
- Marcador especial: Mes donde se cruzan (equilibrio alcanzado)
- Leyenda interactiva

**Interactividad:**

- Hover: Mostrar valores exactos por mes
- Click en mes: Resaltar y mostrar detalles
- Zoom: Para ver más meses en detalle

---

## 4. Componentes Reutilizables

### 4.1 Componente: Indicador de Estado

**Uso:** En múltiples lugares para mostrar estado (above/at/below equilibrio)

**Diseño:**

```
┌───────────────────────────────────────────────────────────────────────┐
│ 🟡 Por debajo del equilibrio                                          │
│                                                                       │
│ Necesitas 50 horas adicionales para alcanzar el punto de equilibrio  │
└───────────────────────────────────────────────────────────────────────┘
```

**Variantes:**

- 🟢 Verde: "Por encima del equilibrio" (above_break_even)
- 🟡 Amarillo: "Por debajo del equilibrio" (below_break_even)
- 🔵 Azul: "En el punto de equilibrio" (at_break_even)

---

### 4.2 Componente: Card de Métrica

**Uso:** Para mostrar métricas individuales (horas, ingresos, utilización)

**Diseño:**

```
┌──────────────┐
│ Horas        │
│              │
│ Equilibrio:  │
│ 300.0h       │
│              │
│ Asignadas:   │
│ 250.0h       │
│              │
│ Faltan:      │
│ 50.0h 🟡     │
└──────────────┘
```

**Props:**

- `title`: Título de la métrica
- `equilibrium_value`: Valor de equilibrio
- `current_value`: Valor actual
- `difference`: Diferencia (calculada)
- `status`: Estado (above/at/below)

---

### 4.3 Componente: Barra de Progreso de Equilibrio

**Uso:** Visualización visual de progreso hacia equilibrio

**Diseño:**

```
Horas Billables

500h ┤
     │
300h ┤═══════════════════════════════════════════════════════════════
     │                    🎯 Punto de Equilibrio
250h ┤████████████████████████████████████████░░░░░░░░░░░░░░░░░░░░░░
     │                    📊 Horas Asignadas
  0h └───────────────────────────────────────────────────────────────
```

**Props:**

- `total_available`: Total disponible
- `equilibrium_value`: Valor de equilibrio
- `current_value`: Valor actual
- `show_labels`: Mostrar etiquetas

---

## 5. Flujos de Usuario

### 5.1 Flujo: Ver Estado Actual

1. Usuario navega a "Analytics" → "Punto de Equilibrio"
2. Ve dashboard con estado actual
3. Identifica si está por encima o debajo del equilibrio
4. Ve métricas clave (horas, ingresos, utilización)
5. Ve visualización gráfica del equilibrio
6. Puede hacer click en "Ver Proyección" o "Simular Escenarios"

---

### 5.2 Flujo: Simular Escenario

1. Usuario está en dashboard de punto de equilibrio
2. Click en "Simular Escenarios"
3. Ve lista de escenarios existentes (si hay)
4. Click en "+ Agregar"
5. Se abre modal de creación de escenario
6. Ingresa nombre del escenario
7. Ajusta variables (BCR, costos fijos, margen)
8. Click en "Simular"
9. Ve resultado del escenario con impacto calculado
10. Compara visualmente con escenario base
11. Puede agregar más escenarios para comparar

---

### 5.3 Flujo: Ver Proyección Temporal

1. Usuario está en dashboard de punto de equilibrio
2. Click en "Ver Proyección"
3. Ve configuración de proyección (meses, tasa de crecimiento)
4. Ajusta parámetros si es necesario
5. Ve resumen con fecha estimada de equilibrio
6. Ve tabla mes a mes con proyección
7. Ve gráfico visual de la proyección
8. Identifica mes donde se alcanzará equilibrio
9. Puede ajustar tasa de crecimiento para ver diferentes escenarios

---

## 6. Consideraciones de UX

### 6.1 Claridad de Conceptos Financieros

**Problema:** El punto de equilibrio puede ser un concepto complejo para usuarios no financieros.

**Solución:**

- Explicaciones simples en tooltips
- Lenguaje claro y directo
- Visualizaciones que faciliten comprensión
- Ejemplos prácticos

**Ejemplos de Tooltips:**

- "El punto de equilibrio es cuando tus ingresos igualan tus costos (sin ganancia ni pérdida)"
- "Horas de equilibrio: Las horas que necesitas facturar para cubrir todos tus costos"
- "Margen de seguridad: Qué tan lejos estás del punto de equilibrio"

---

### 6.2 Acción Orientada

**Principio:** No solo mostrar datos, sino guiar al usuario sobre qué hacer.

**Implementación:**

- Mensajes claros de acción ("Necesitas 50 horas adicionales")
- Sugerencias concretas ("Considera aumentar precios 15%")
- Botones de acción prominentes ("Simular Escenarios", "Ver Proyección")

---

### 6.3 Comparación Visual

**Principio:** Facilitar comparación de escenarios y proyecciones.

**Implementación:**

- Gráficos lado a lado
- Tablas comparativas
- Indicadores de cambio (flechas, colores)
- Resaltado de diferencias

---

## 7. Especificaciones Técnicas para Frontend

### 7.1 Endpoints a Consumir

**Análisis Actual:**

- `GET /api/v1/analytics/break-even?currency=&include_projected=&period=`

**Simulación de Escenarios:**

- `POST /api/v1/analytics/break-even/scenarios`

**Proyección Temporal:**

- `GET /api/v1/analytics/break-even/projection?months_ahead=&growth_rate=`

---

### 7.2 Manejo de Datos

**Formato de Moneda:**

- Usar `Decimal` en cálculos (librería `decimal.js`)
- Formatear para display con `Intl.NumberFormat`
- Mostrar siempre moneda en formato localizado

**Formato de Porcentajes:**

- Mostrar con 1-2 decimales
- Formato: "57.7%" o "57.70%"

**Formato de Fechas:**

- ISO 8601 desde backend
- Formatear para display: "15 de Marzo, 2026"
- Considerar timezone del usuario

---

### 7.3 Validaciones en Frontend

**Antes de Enviar Escenario:**

- Nombre requerido (min 3 caracteres)
- Al menos un cambio diferente de 0
- Valores dentro de rangos permitidos
- BCR multiplier: 0.1 - 5.0
- Margen adjustment: -1.0 a 1.0

---

### 7.4 Optimizaciones

**Caching:**

- Cachear análisis de punto de equilibrio (TTL: 5 minutos)
- Invalidar cache al cambiar costos fijos o equipo
- Cachear escenarios simulados (TTL: 10 minutos)

**Lazy Loading:**

- Cargar proyección solo cuando se solicita
- Cargar gráficos solo cuando están visibles
- Paginar tabla de proyección si hay muchos meses

---

## 8. Diseño Responsive

### 8.1 Desktop (>1024px)

- Dashboard con 3 columnas de métricas
- Gráficos grandes y detallados
- Tablas completas con todas las columnas
- Sidebar con acciones rápidas

---

### 8.2 Tablet (768px - 1024px)

- Dashboard con 2 columnas de métricas
- Gráficos medianos
- Tablas con scroll horizontal
- Modal full-screen para formularios

---

### 8.3 Móvil (<768px)

- Dashboard con 1 columna de métricas (stack vertical)
- Gráficos adaptativos (scroll horizontal si es necesario)
- Cards en lugar de tablas
- Drawer bottom para formularios
- Navegación simplificada

---

## 9. Accesibilidad

### 9.1 Contraste y Colores

- Indicadores de color acompañados de texto
- Contraste mínimo WCAG AA
- No depender solo del color para transmitir información

---

### 9.2 Navegación por Teclado

- Todos los elementos interactivos accesibles por teclado
- Tab order lógico
- Focus visible en todos los elementos

---

### 9.3 Screen Readers

- ARIA labels en todos los gráficos
- Descripciones textuales de visualizaciones
- Mensajes de estado anunciados

---

## 10. Checklist de Diseño

### Pantallas Principales

- [ ] Dashboard principal de punto de equilibrio
- [ ] Simulador de escenarios
- [ ] Proyección temporal
- [ ] Comparación de escenarios

### Componentes

- [ ] Indicador de estado (above/at/below)
- [ ] Cards de métricas (horas, ingresos, utilización)
- [ ] Visualización de equilibrio (gráfico)
- [ ] Desglose de costos
- [ ] Formulario de escenario
- [ ] Card de escenario simulado
- [ ] Tabla de proyección mes a mes
- [ ] Gráfico de proyección temporal

### Validaciones

- [ ] Validación de formularios de escenarios
- [ ] Mensajes de error claros
- [ ] Tooltips explicativos

### UX/UI

- [ ] Diseño responsive (móvil, tablet, desktop)
- [ ] Indicadores visuales consistentes
- [ ] Animaciones suaves en transiciones
- [ ] Tooltips con información adicional
- [ ] Accesibilidad (ARIA, keyboard navigation)

---

## 11. Referencias

### Documentos Relacionados

- **Especificación Backend:** `BACKEND_SPEC_BREAK_EVEN_POINT.md`
- **UI Requirements Resource Allocation:** `UI_REQUIREMENTS_RESOURCE_ALLOCATION.md`
- **UI Requirements Dashboard:** `UI_REQUIREMENTS_QUOTES_DASHBOARD.md`

### Conceptos Financieros

- **Break-Even Point:** Punto donde ingresos = costos
- **Safety Margin:** Margen de seguridad sobre equilibrio
- **Operating Leverage:** Apalancamiento operativo
- **Contribution Margin:** Margen de contribución

---

**Última actualización:** 2026-01-25  
**Versión:** 1.0  
**Estado:** Pendiente de Diseño
