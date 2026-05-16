# UI Requirements: Asignación de Recursos (Resource Allocation)

**Versión:** 1.0  
**Fecha:** 2026-01-25  
**Documento Base:** `PLAN_TRABAJO_RESOURCE_ALLOCATION_BACKEND.md`  
**Estado:** Pendiente de Diseño

---

## Resumen Ejecutivo

Este documento detalla los requerimientos de UI para el sistema de asignación de recursos (Resource Allocation) que permite asignar miembros específicos del equipo a cotizaciones con horas específicas, visualizar utilización por miembro, y validar capacidad antes de crear cotizaciones.

**Objetivo:** Diseñar interfaces de usuario intuitivas para gestionar asignaciones de recursos del equipo a cotizaciones, con visualización clara de disponibilidad y utilización.

**Alcance:**
- Selector de recursos en creación/edición de cotizaciones
- Dashboard de disponibilidad del equipo
- Visualización de utilización por miembro
- Alertas y validaciones de capacidad
- Gestión de asignaciones existentes

**Principios de Diseño:**
- **Claridad Visual:** Indicadores claros de disponibilidad y utilización
- **Prevención de Errores:** Validación en tiempo real antes de guardar
- **Feedback Inmediato:** Mostrar impacto de asignaciones mientras se crean
- **Flexibilidad:** Permitir asignaciones opcionales (no bloquea creación sin asignaciones)

---

## 1. Pantalla: Creación/Edición de Cotización con Asignación de Recursos

### 1.1 Contexto y Ubicación

**Pantalla:** Formulario de creación/edición de cotización  
**Ruta:** `/projects/new` o `/projects/{id}/quotes/{quote_id}/edit`  
**Sección:** Nueva sección "Asignación de Recursos" (opcional, colapsable)

### 1.2 Data Mapping

**Campos Requeridos del Backend:**

```typescript
interface ResourceAllocation {
  team_member_id: number;        // ID del miembro del equipo
  allocated_hours: number;       // Horas asignadas (requerido, > 0)
  role_in_project?: string;       // Rol específico (opcional)
  start_date?: Date;              // Fecha inicio (opcional)
  end_date?: Date;                // Fecha fin (opcional)
  notes?: string;                 // Notas (opcional)
}
```

**Payload para Backend:**

```json
{
  "name": "Proyecto XYZ",
  "client_name": "Cliente ABC",
  "quote_items": [...],
  "resource_allocations": [
    {
      "team_member_id": 1,
      "allocated_hours": "40.0",
      "role_in_project": "Lead Developer",
      "start_date": "2026-02-01T00:00:00Z",
      "end_date": "2026-02-28T23:59:59Z"
    }
  ]
}
```

### 1.3 Componente: Selector de Recursos

**Ubicación:** Dentro del formulario de cotización, después de la sección de "Items de Cotización"

**Diseño:**

```
┌─────────────────────────────────────────────────────────────┐
│ 📋 Asignación de Recursos                                   │
│ ─────────────────────────────────────────────────────────── │
│                                                              │
│ [ ] Asignar recursos específicos del equipo                 │
│                                                              │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ + Agregar Recurso                                       │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Estado Inicial (Colapsado):**
- Checkbox: "Asignar recursos específicos del equipo"
- Por defecto: Desmarcado (comportamiento actual: usar BCR global)
- Cuando está desmarcado: Sección oculta

**Estado Expandido (Checkbox marcado):**
- Se muestra lista de asignaciones
- Botón "+ Agregar Recurso"
- Tabla o cards con asignaciones agregadas

---

### 1.4 Componente: Formulario de Asignación de Recurso

**Trigger:** Click en "+ Agregar Recurso" o "Editar" en asignación existente

**Modal/Drawer:**

```
┌─────────────────────────────────────────────────────────────┐
│ Asignar Recurso al Proyecto                          [X]    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│ Miembro del Equipo *                                        │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ [Select: Buscar miembro...]                    ▼       │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                              │
│ Horas Asignadas *                                           │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ [40.0] horas                                           │ │
│ └────────────────────────────────────────────────────────┘ │
│ ℹ️ Disponible: 58.56 horas | Utilización proyectada: 57.7% │
│                                                              │
│ Rol en el Proyecto (Opcional)                               │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ [Lead Developer]                                        │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                              │
│ Fechas de Asignación (Opcional)                             │
│ ┌──────────────────────┐  ┌──────────────────────┐        │
│ │ Inicio: [2026-02-01] │  │ Fin: [2026-02-28]    │        │
│ └──────────────────────┘  └──────────────────────┘        │
│                                                              │
│ Notas (Opcional)                                            │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ [Notas sobre la asignación...]                         │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                              │
│ ┌──────────────┐  ┌──────────────┐                        │
│ │   Cancelar   │  │   Guardar    │                        │
│ └──────────────┘  └──────────────┘                        │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Campos:**

1. **Selector de Miembro del Equipo:**
   - Tipo: Autocomplete/Select con búsqueda
   - Fuente de datos: `GET /api/v1/team/` (solo miembros activos)
   - Mostrar: Nombre, Rol, Disponibilidad actual
   - Formato: "Juan Pérez (Developer) - 58.56h disponibles"

2. **Horas Asignadas:**
   - Tipo: Input numérico (decimal, 2 decimales)
   - Validación: > 0, máximo según disponibilidad
   - Feedback en tiempo real: Mostrar disponibilidad y utilización proyectada

3. **Rol en el Proyecto:**
   - Tipo: Input de texto libre o Select con opciones comunes
   - Opciones sugeridas: "Lead Developer", "Developer", "Designer", "Project Manager", "QA", etc.
   - Opcional

4. **Fechas de Asignación:**
   - Tipo: Date pickers
   - Validación: `end_date >= start_date`
   - Opcional

5. **Notas:**
   - Tipo: Textarea
   - Opcional

**Validaciones en Tiempo Real:**

- Al seleccionar miembro: Mostrar disponibilidad actual
- Al ingresar horas: Calcular y mostrar utilización proyectada
- Si utilización > 100%: Mostrar error (bloquear guardado)
- Si utilización > 90%: Mostrar warning (permitir guardado con confirmación)

---

### 1.5 Componente: Lista de Asignaciones

**Ubicación:** Dentro de la sección "Asignación de Recursos" expandida

**Diseño (Tabla):**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Asignaciones de Recursos                                                     │
├──────────────┬──────────┬──────────────┬──────────────┬──────────┬──────────┤
│ Miembro      │ Horas    │ Rol          │ Fechas       │ Util.    │ Acciones │
├──────────────┼──────────┼──────────────┼──────────────┼──────────┼──────────┤
│ Juan Pérez   │ 40.0h   │ Lead Dev     │ Feb 1-28    │ 57.7%    │ [✏️] [🗑️]│
│              │          │              │              │ 🟢       │          │
├──────────────┼──────────┼──────────────┼──────────────┼──────────┼──────────┤
│ María López  │ 20.0h   │ Designer     │ -            │ 45.2%    │ [✏️] [🗑️]│
│              │          │              │              │ 🟢       │          │
├──────────────┼──────────┼──────────────┼──────────────┼──────────┼──────────┤
│              │          │              │              │          │          │
│ Total: 60.0 horas asignadas                                                │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Diseño Alternativo (Cards):**

```
┌─────────────────────────────────────────────────────────────┐
│ ┌──────────────────────┐  ┌──────────────────────┐         │
│ │ Juan Pérez           │  │ María López          │         │
│ │ Developer            │  │ Designer             │         │
│ │                      │  │                      │         │
│ │ 40.0 horas           │  │ 20.0 horas           │         │
│ │ Rol: Lead Developer  │  │ Rol: Designer        │         │
│ │                      │  │                      │         │
│ │ Utilización: 57.7%   │  │ Utilización: 45.2%   │         │
│ │ 🟢 Disponible        │  │ 🟢 Disponible        │         │
│ │                      │  │                      │         │
│ │ [✏️ Editar] [🗑️]     │  │ [✏️ Editar] [🗑️]     │         │
│ └──────────────────────┘  └──────────────────────┘         │
│                                                              │
│ Total: 60.0 horas asignadas                                  │
└─────────────────────────────────────────────────────────────┘
```

**Columnas/Información:**

1. **Miembro:** Nombre y rol del miembro
2. **Horas:** Horas asignadas (formato: "40.0h")
3. **Rol:** Rol específico en el proyecto (si está definido)
4. **Fechas:** Rango de fechas (si está definido) o "-"
5. **Utilización:** Porcentaje de utilización proyectada con indicador visual
6. **Acciones:** Editar y Eliminar

**Indicadores Visuales de Utilización:**

- 🟢 Verde: Utilización < 90% (Saludable)
- 🟡 Amarillo: Utilización 90-100% (Warning)
- 🔴 Rojo: Utilización > 100% (Error - no permitido)

**Total de Horas:**
- Mostrar suma total de horas asignadas
- Si hay asignaciones, mostrar también costo total estimado

---

### 1.6 Validaciones y Alertas

**Validación en Tiempo Real:**

Al agregar/editar asignación, mostrar feedback inmediato:

```
┌─────────────────────────────────────────────────────────────┐
│ ⚠️ Advertencia de Capacidad                                  │
│                                                              │
│ La asignación proyecta una utilización del 95% para         │
│ Juan Pérez. Esto está cerca del límite recomendado.         │
│                                                              │
│ Disponible: 58.56 horas                                     │
│ Asignado actualmente: 80.0 horas                            │
│ Nueva asignación: 40.0 horas                                │
│ Total proyectado: 120.0 horas (95% de 126.4h disponibles)   │
│                                                              │
│ [Cancelar] [Continuar de todas formas]                      │
└─────────────────────────────────────────────────────────────┘
```

**Error de Capacidad Excedida:**

```
┌─────────────────────────────────────────────────────────────┐
│ ❌ Error: Capacidad Excedida                                 │
│                                                              │
│ No se puede asignar 40.0 horas a Juan Pérez porque          │
│ excedería su capacidad disponible.                           │
│                                                              │
│ Disponible: 58.56 horas                                     │
│ Ya asignado: 80.0 horas                                    │
│ Intenta asignar: 40.0 horas                                 │
│ Total requerido: 120.0 horas                                │
│                                                              │
│ Máximo posible: 58.56 horas adicionales                     │
│                                                              │
│ [Ajustar horas] [Cancelar]                                  │
└─────────────────────────────────────────────────────────────┘
```

**Validación al Guardar Cotización:**

- Si hay asignaciones con utilización > 100%: Bloquear guardado, mostrar errores
- Si hay asignaciones con utilización > 90%: Permitir guardado con confirmación
- Si todas las asignaciones están OK: Guardar normalmente

---

## 2. Pantalla: Dashboard de Disponibilidad del Equipo

### 2.1 Contexto y Ubicación

**Pantalla:** Dashboard de disponibilidad de recursos  
**Ruta:** `/team/availability` o `/resources/availability`  
**Acceso:** Desde menú lateral "Recursos" o "Equipo" → "Disponibilidad"

### 2.2 Data Mapping

**Endpoint:** `GET /api/v1/team/availability`

**Query Parameters:**
- `start_date`: Fecha inicio (opcional)
- `end_date`: Fecha fin (opcional)
- `team_member_id`: Filtrar por miembro específico (opcional)

**Response:**

```json
{
  "members": [
    {
      "team_member_id": 1,
      "member_name": "Juan Pérez",
      "role": "Developer",
      "available_hours": 138.56,
      "allocated_hours": 80.0,
      "available_capacity": 58.56,
      "utilization_rate": 57.7
    }
  ],
  "total_available_hours": 500.0,
  "total_allocated_hours": 300.0,
  "overall_utilization": 60.0
}
```

### 2.3 Diseño del Dashboard

**Layout Principal:**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 📊 Disponibilidad del Equipo                                    [Filtros ▼]│
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ ┌───────────────────────────────────────────────────────────────────────┐ │
│ │ Resumen General                                                        │ │
│ │                                                                       │ │
│ │ Total Disponible: 500.0h  │  Total Asignado: 300.0h  │  Utilización: 60%│
│ │                                                                       │ │
│ │ [████████████████░░░░] 60%                                           │ │
│ └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ ┌───────────────────────────────────────────────────────────────────────┐ │
│ │ Miembros del Equipo                                    [+ Asignar]    │ │
│ ├──────────────┬──────────┬──────────┬──────────┬──────────┬───────────┤ │
│ │ Miembro      │ Rol      │ Dispon.  │ Asignado │ Util.    │ Estado    │ │
│ ├──────────────┼──────────┼──────────┼──────────┼──────────┼───────────┤ │
│ │ Juan Pérez   │ Developer│ 138.56h  │ 80.0h    │ 57.7%    │ 🟢 OK     │ │
│ │              │          │          │          │ [████░░] │           │ │
│ ├──────────────┼──────────┼──────────┼──────────┼──────────┼───────────┤ │
│ │ María López  │ Designer │ 120.0h   │ 110.0h   │ 91.7%    │ 🟡 Warning│ │
│ │              │          │          │          │ [█████░] │           │ │
│ ├──────────────┼──────────┼──────────┼──────────┼──────────┼───────────┤ │
│ │ Carlos Ruiz  │ PM       │ 100.0h   │ 100.0h   │ 100.0%   │ 🔴 Crítico│ │
│ │              │          │          │          │ [██████] │           │ │
│ └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ ┌───────────────────────────────────────────────────────────────────────┐ │
│ │ Gráfico de Utilización (Últimos 3 meses)                              │ │
│ │                                                                       │ │
│ │   100% ┤                                                               │ │
│ │    80% ┤     ████                                                     │ │
│ │    60% ┤  ████████                                                     │ │
│ │    40% ┤██████████                                                     │ │
│ │    20% ┤██████████                                                     │ │
│ │     0% └─────────────────────────────────────────────────────────────  │ │
│ │         Ene    Feb    Mar                                             │ │
│ └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.4 Componente: Resumen General

**Información:**
- Total de horas disponibles del equipo
- Total de horas asignadas
- Utilización general (porcentaje)
- Barra de progreso visual

**Indicadores:**
- 🟢 Verde: Utilización < 80% (Saludable)
- 🟡 Amarillo: Utilización 80-90% (Atención)
- 🔴 Rojo: Utilización > 90% (Crítico)

---

### 2.5 Componente: Tabla de Miembros

**Columnas:**

1. **Miembro:** Nombre del miembro (clickeable para ver detalle)
2. **Rol:** Rol del miembro
3. **Disponible:** Horas disponibles mensuales
4. **Asignado:** Horas ya asignadas en proyectos activos
5. **Utilización:** Porcentaje con barra de progreso visual
6. **Estado:** Indicador de color (🟢/🟡/🔴)

**Acciones:**
- Click en nombre: Ver detalle de utilización del miembro
- Botón "+ Asignar": Asignar a nueva cotización (redirige a creación)

**Filtros:**
- Por rol
- Por estado de utilización (OK/Warning/Crítico)
- Por nombre (búsqueda)

**Ordenamiento:**
- Por nombre
- Por utilización (ascendente/descendente)
- Por horas disponibles

---

### 2.6 Componente: Gráfico de Utilización

**Tipo:** Gráfico de líneas o barras

**Datos:** Utilización histórica de los últimos 3-6 meses

**Eje X:** Meses
**Eje Y:** Porcentaje de utilización (0-100%)

**Líneas/Barras:**
- Línea general del equipo (promedio)
- Líneas individuales por miembro (opcional, toggle)

---

## 3. Pantalla: Detalle de Utilización por Miembro

### 3.1 Contexto y Ubicación

**Pantalla:** Detalle de utilización de un miembro específico  
**Ruta:** `/team/{team_member_id}/utilization`  
**Acceso:** Click en nombre de miembro desde dashboard de disponibilidad

### 3.2 Data Mapping

**Endpoint:** `GET /api/v1/team/{team_member_id}/utilization`

**Response:**

```json
{
  "team_member_id": 1,
  "member_name": "Juan Pérez",
  "role": "Developer",
  "available_hours": 138.56,
  "allocated_hours": 80.0,
  "available_capacity": 58.56,
  "utilization_rate": 57.7,
  "allocations": [
    {
      "quote_id": 123,
      "project_name": "Website Redesign",
      "allocated_hours": 40.0,
      "role_in_project": "Lead Developer",
      "start_date": "2026-02-01T00:00:00Z",
      "end_date": "2026-02-28T23:59:59Z"
    }
  ]
}
```

### 3.3 Diseño de la Pantalla

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ ← Volver a Disponibilidad                                                   │
│                                                                             │
│ ┌───────────────────────────────────────────────────────────────────────┐ │
│ │ Juan Pérez - Developer                                                 │ │
│ │                                                                       │ │
│ │ Disponible: 138.56h  │  Asignado: 80.0h  │  Utilización: 57.7%      │ │
│ │                                                                       │ │
│ │ [████████████░░░░░░░░] 57.7%                                         │ │
│ │                                                                       │ │
│ │ Capacidad disponible: 58.56 horas                                    │ │
│ └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ ┌───────────────────────────────────────────────────────────────────────┐ │
│ │ Asignaciones Activas                                                   │ │
│ ├──────────────┬──────────┬──────────────┬──────────────┬──────────────┤ │
│ │ Proyecto     │ Horas    │ Rol          │ Fechas       │ Estado       │ │
│ ├──────────────┼──────────┼──────────────┼──────────────┼──────────────┤ │
│ │ Website      │ 40.0h    │ Lead Dev     │ Feb 1-28    │ 🟢 Activo    │ │
│ │ Redesign     │          │              │              │              │ │
│ │              │          │              │ [Ver Quote] │              │ │
│ ├──────────────┼──────────┼──────────────┼──────────────┼──────────────┤ │
│ │ Mobile App   │ 40.0h    │ Developer    │ -            │ 🟢 Activo    │ │
│ │              │          │              │              │              │ │
│ │              │          │              │ [Ver Quote] │              │ │
│ └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ ┌───────────────────────────────────────────────────────────────────────┐ │
│ │ Timeline de Asignaciones                                               │ │
│ │                                                                       │ │
│ │ Febrero 2026                                                          │ │
│ │ ┌─────────────────────────────────────────────────────────────────┐ │ │
│ │ │ [████████] Website Redesign (40h)                                │ │ │
│ │ │ [████████] Mobile App (40h)                                       │ │ │
│ │ └─────────────────────────────────────────────────────────────────┘ │ │
│ └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.4 Componente: Resumen del Miembro

**Información:**
- Nombre y rol
- Horas disponibles mensuales
- Horas asignadas actualmente
- Utilización porcentual
- Capacidad disponible restante
- Barra de progreso visual

---

### 3.5 Componente: Lista de Asignaciones

**Información por Asignación:**
- Nombre del proyecto (link a cotización)
- Horas asignadas
- Rol específico en el proyecto
- Fechas de asignación (si aplica)
- Estado (Activo/Completado)

**Acciones:**
- Ver cotización completa
- Editar asignación (si es posible)
- Eliminar asignación (con confirmación)

---

### 3.6 Componente: Timeline de Asignaciones

**Tipo:** Gráfico de Gantt simplificado o timeline horizontal

**Visualización:**
- Eje X: Tiempo (meses/semanas)
- Barras horizontales: Asignaciones por proyecto
- Mostrar solapamientos visualmente

**Interactividad:**
- Hover: Mostrar detalles de asignación
- Click: Ir a cotización

---

## 4. Componente: Selector de Miembro del Equipo

### 4.1 Contexto

**Uso:** En formulario de asignación de recurso (modal/drawer)

### 4.2 Diseño

**Tipo:** Autocomplete/Select con búsqueda

**Estado Inicial:**

```
┌─────────────────────────────────────────────────────────────┐
│ Miembro del Equipo *                                        │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ Buscar miembro...                               ▼       │ │
│ └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

**Estado con Búsqueda:**

```
┌─────────────────────────────────────────────────────────────┐
│ Miembro del Equipo *                                        │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ Juan                                            ▼       │ │
│ └────────────────────────────────────────────────────────┘ │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ ✓ Juan Pérez (Developer)                               │ │
│ │   138.56h disponibles | 57.7% utilizado                │ │
│ ├────────────────────────────────────────────────────────┤ │
│ │   Juan Carlos (Designer)                               │ │
│ │   120.0h disponibles | 45.2% utilizado                │ │
│ └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

**Información Mostrada:**
- Nombre del miembro
- Rol
- Horas disponibles
- Utilización actual (con indicador de color)

**Filtrado:**
- Por nombre (búsqueda en tiempo real)
- Solo miembros activos
- Solo miembros de la misma organización

---

## 5. Validaciones y Feedback Visual

### 5.1 Indicadores de Utilización

**Colores:**
- 🟢 Verde: < 90% (Saludable)
- 🟡 Amarillo: 90-100% (Warning)
- 🔴 Rojo: > 100% (Error)

**Uso:**
- En barras de progreso
- En badges de estado
- En tooltips

---

### 5.2 Mensajes de Validación

**Error (Bloquea guardado):**
```
❌ No se puede asignar 40.0 horas a Juan Pérez porque excedería su capacidad disponible.
```

**Warning (Permite guardado con confirmación):**
```
⚠️ La asignación proyecta una utilización del 95% para Juan Pérez. 
Esto está cerca del límite recomendado.
```

**Éxito:**
```
✅ Asignación creada exitosamente. Utilización proyectada: 57.7%
```

---

### 5.3 Cálculo en Tiempo Real

**Al seleccionar miembro:**
- Mostrar disponibilidad actual inmediatamente
- Actualizar cuando se ingresen horas

**Al ingresar horas:**
- Calcular utilización proyectada
- Mostrar indicador de color
- Mostrar mensaje de warning/error si aplica

**Ejemplo:**

```
Horas Asignadas *
┌────────────────────────────────────────────────────────┐
│ [40.0] horas                                           │
└────────────────────────────────────────────────────────┘
ℹ️ Disponible: 58.56 horas | Utilización proyectada: 57.7% 🟢
```

---

## 6. Flujos de Usuario

### 6.1 Flujo: Crear Cotización con Asignación de Recursos

1. Usuario está en formulario de creación de cotización
2. Completa información básica (nombre, cliente, items)
3. Marca checkbox "Asignar recursos específicos del equipo"
4. Se expande sección de asignaciones
5. Click en "+ Agregar Recurso"
6. Se abre modal de asignación
7. Selecciona miembro del equipo (autocomplete)
8. Ingresa horas asignadas
9. Sistema calcula y muestra utilización proyectada en tiempo real
10. Si hay warning (>90%), muestra mensaje pero permite continuar
11. Si hay error (>100%), bloquea guardado y muestra error
12. Completa campos opcionales (rol, fechas, notas)
13. Click en "Guardar"
14. Asignación aparece en la lista
15. Usuario puede agregar más asignaciones o continuar
16. Al guardar cotización, se validan todas las asignaciones
17. Si todo está OK, se crea la cotización con asignaciones

---

### 6.2 Flujo: Ver Disponibilidad del Equipo

1. Usuario navega a "Recursos" → "Disponibilidad"
2. Ve dashboard con resumen general
3. Ve tabla de miembros con utilización
4. Identifica miembros con alta utilización (colores 🟡/🔴)
5. Click en nombre de miembro para ver detalle
6. Ve asignaciones activas del miembro
7. Ve timeline de asignaciones
8. Puede hacer click en proyecto para ver cotización completa

---

### 6.3 Flujo: Editar Asignación Existente

1. Usuario está en cotización existente
2. Ve sección de asignaciones
3. Click en "Editar" en una asignación
4. Se abre modal con datos actuales
5. Modifica horas asignadas
6. Sistema recalcula utilización proyectada
7. Si hay cambios que causan error, muestra error
8. Guarda cambios
9. Asignación se actualiza en la lista

---

## 7. Consideraciones de UX

### 7.1 Opcionalidad

**Importante:** Las asignaciones de recursos son completamente opcionales.

- Por defecto, checkbox desmarcado
- Si no se asignan recursos, cotización funciona igual que antes (BCR global)
- No forzar al usuario a asignar recursos

---

### 7.2 Prevención de Errores

- Validación en tiempo real mientras se ingresa información
- Feedback visual inmediato (colores, barras de progreso)
- Mensajes claros de error con sugerencias de solución
- Bloquear acciones que causarían errores

---

### 7.3 Feedback Visual

- Indicadores de color consistentes en toda la aplicación
- Barras de progreso para visualizar utilización
- Tooltips con información adicional
- Animaciones suaves en transiciones

---

### 7.4 Responsive Design

- Tabla de disponibilidad: Scroll horizontal en móviles
- Modal de asignación: Full screen en móviles
- Cards en lugar de tabla en pantallas pequeñas
- Gráficos adaptativos según tamaño de pantalla

---

## 8. Especificaciones Técnicas para Frontend

### 8.1 Endpoints a Consumir

**Crear/Actualizar Cotización con Asignaciones:**
- `POST /api/v1/projects/` (con `resource_allocations` en payload)
- `PUT /api/v1/projects/{project_id}/quotes/{quote_id}` (con `resource_allocations`)

**CRUD de Asignaciones:**
- `POST /api/v1/quotes/{quote_id}/resource-allocations`
- `GET /api/v1/quotes/{quote_id}/resource-allocations`
- `PUT /api/v1/quotes/{quote_id}/resource-allocations/{allocation_id}`
- `DELETE /api/v1/quotes/{quote_id}/resource-allocations/{allocation_id}`

**Disponibilidad:**
- `GET /api/v1/team/availability?start_date=&end_date=`
- `GET /api/v1/team/{team_member_id}/utilization`

**Lista de Miembros:**
- `GET /api/v1/team/` (para autocomplete)

---

### 8.2 Validaciones en Frontend

**Antes de Enviar al Backend:**
- `allocated_hours` > 0
- `team_member_id` existe y es válido
- `end_date >= start_date` (si ambos están presentes)
- No duplicar asignaciones del mismo miembro en la misma cotización

**Validación de Capacidad (Preview):**
- Llamar a endpoint de validación antes de guardar (opcional)
- O calcular en frontend usando datos de disponibilidad

---

### 8.3 Manejo de Errores

**Errores del Backend:**
- 400 Bad Request: Mostrar mensajes de validación específicos
- 409 Conflict: Mostrar error de capacidad excedida con detalles
- 404 Not Found: Miembro no encontrado o inactivo
- 500 Server Error: Mensaje genérico con opción de reintentar

---

### 8.4 Optimizaciones

**Caching:**
- Cachear lista de miembros del equipo (TTL: 5 minutos)
- Cachear disponibilidad del equipo (TTL: 2 minutos)
- Invalidar cache al crear/actualizar asignaciones

**Lazy Loading:**
- Cargar asignaciones solo cuando se expande la sección
- Cargar detalles de utilización solo cuando se necesita

---

## 9. Checklist de Diseño

### Pantallas Principales

- [ ] Formulario de creación/edición de cotización con sección de asignaciones
- [ ] Modal/Drawer de asignación de recurso
- [ ] Lista de asignaciones (tabla o cards)
- [ ] Dashboard de disponibilidad del equipo
- [ ] Detalle de utilización por miembro
- [ ] Timeline de asignaciones

### Componentes

- [ ] Selector de miembro del equipo (autocomplete)
- [ ] Input de horas asignadas con feedback en tiempo real
- [ ] Indicadores de utilización (barras de progreso, badges)
- [ ] Mensajes de validación (error, warning, éxito)
- [ ] Gráfico de utilización histórica

### Validaciones

- [ ] Validación en tiempo real de capacidad
- [ ] Mensajes de error claros y accionables
- [ ] Warnings para utilización alta pero permitida
- [ ] Bloqueo de acciones que causarían errores

### UX/UI

- [ ] Diseño responsive (móvil, tablet, desktop)
- [ ] Indicadores visuales consistentes (colores, iconos)
- [ ] Animaciones suaves en transiciones
- [ ] Tooltips con información adicional
- [ ] Accesibilidad (ARIA labels, keyboard navigation)

---

## 10. Referencias

### Documentos Relacionados

- **Plan de Trabajo Backend:** `PLAN_TRABAJO_RESOURCE_ALLOCATION_BACKEND.md`
- **Especificación Backend:** `BACKEND_SPECT_QUOTE.md` (sección de Resource Allocation)
- **UI Requirements Quotes CRUD:** `UI_REQUIREMENTS_QUOTE_CRUD.md`

### Componentes de Diseño Existentes

- Selector de servicios (similar al selector de miembros)
- Formularios de cotización (base para formulario con asignaciones)
- Dashboard de métricas (base para dashboard de disponibilidad)

---

**Última actualización:** 2026-01-25  
**Versión:** 1.0  
**Estado:** Pendiente de Diseño
