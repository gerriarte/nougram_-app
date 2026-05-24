# AnÃ¡lisis: Backend vs Frontend - MÃ³dulo Break-Even Point

**Fecha:** 2026-01-25  
**Estado:** âš ï¸ **Backend NO Implementado**  
**Documento Frontend:** `UI_REQUIREMENTS_BREAK_EVEN_POINT.md`

---

## ðŸ“‹ Resumen Ejecutivo

El frontend requiere un mÃ³dulo completo de **Punto de Equilibrio (Break-Even Point)** con 3 endpoints principales, pero **el backend NO tiene implementaciÃ³n** de estos endpoints. Solo existe una referencia parcial en `annual_projection` que calcula `break_even_monthly_cost`, pero no es suficiente para las funcionalidades requeridas.

---

## ðŸ” AnÃ¡lisis de Requerimientos Frontend

### Endpoints Requeridos por el Frontend:

1. **`GET /api/v1/analytics/break-even`**
   - AnÃ¡lisis actual de punto de equilibrio
   - Query params: `currency`, `include_projected`, `period`

2. **`POST /api/v1/analytics/break-even/scenarios`**
   - SimulaciÃ³n de escenarios financieros
   - Body: `BreakEvenScenarioRequest`

3. **`GET /api/v1/analytics/break-even/projection`**
   - ProyecciÃ³n temporal de punto de equilibrio
   - Query params: `months_ahead`, `growth_rate`

---

## ðŸ”Ž Estado Actual del Backend

### âŒ Endpoints NO Existentes:

- **`GET /api/v1/analytics/break-even`** - âŒ NO existe
- **`POST /api/v1/analytics/break-even/scenarios`** - âŒ NO existe
- **`GET /api/v1/analytics/break-even/projection`** - âŒ NO existe

### âš ï¸ Referencias Parciales Encontradas:

1. **`annual_projection.py`** - Tiene campo `break_even_monthly_cost`:
   - Solo calcula costos mensuales de equilibrio (Overhead + Payroll)
   - NO calcula horas de equilibrio
   - NO calcula ingresos de equilibrio
   - NO tiene simulaciÃ³n de escenarios
   - NO tiene proyecciÃ³n temporal

2. **`insights.py`** - Router `/insights`:
   - Solo tiene `/dashboard` y `/ai-advisor`
   - NO tiene endpoints de break-even

3. **`router.py`** - No registra ningÃºn router de break-even:
   - `/insights` existe pero sin break-even
   - No hay `/analytics/break-even`

---

## ðŸ“Š ComparaciÃ³n Detallada

### 1. AnÃ¡lisis Actual (`GET /api/v1/analytics/break-even`)

#### Frontend Requiere:
- Costos totales fijos
- Horas billables disponibles
- Horas de equilibrio
- Horas asignadas actuales
- Ingresos de equilibrio
- Estado (above/at/below)
- ProyecciÃ³n de fecha de equilibrio

#### Backend Actual:
- âŒ NO existe endpoint
- âš ï¸ Solo existe `break_even_monthly_cost` en `annual_projection` (solo costos, no horas ni ingresos)

#### Lo que Falta:
- âœ… Endpoint completo
- âœ… CÃ¡lculo de horas de equilibrio
- âœ… CÃ¡lculo de ingresos de equilibrio
- âœ… CÃ¡lculo de horas asignadas actuales
- âœ… CÃ¡lculo de utilizaciÃ³n
- âœ… Estado (above/at/below)
- âœ… ProyecciÃ³n de fecha de equilibrio

---

### 2. SimulaciÃ³n de Escenarios (`POST /api/v1/analytics/break-even/scenarios`)

#### Backend Actual:
- âŒ NO existe endpoint
- âŒ NO existe lÃ³gica de simulaciÃ³n de escenarios

#### Lo que Falta:
- âœ… Endpoint completo
- âœ… LÃ³gica de simulaciÃ³n con multiplicadores
- âœ… CÃ¡lculo de impacto de cambios
- âœ… ComparaciÃ³n con escenario base

---

### 3. ProyecciÃ³n Temporal (`GET /api/v1/analytics/break-even/projection`)

#### Backend Actual:
- âŒ NO existe endpoint
- âš ï¸ Existe `annual_projection` pero es diferente (proyecciÃ³n de ventas anuales, no break-even)

#### Lo que Falta:
- âœ… Endpoint completo
- âœ… ProyecciÃ³n mes a mes
- âœ… CÃ¡lculo de fecha de equilibrio
- âœ… CÃ¡lculo de horas profit por mes
- âœ… Soporte para tasa de crecimiento

---

## ðŸ—ï¸ Arquitectura Requerida (SegÃºn MVC)

Para implementar este mÃ³dulo siguiendo la arquitectura MVC actual, se necesita:

### Estructura de Archivos:

```
backend/app/
â”œâ”€â”€ api/v1/endpoints/
â”‚   â””â”€â”€ break_even.py              # âš ï¸ NO EXISTE - Crear
â”‚
â”œâ”€â”€ controllers/
â”‚   â””â”€â”€ break_even_controller.py   # âš ï¸ NO EXISTE - Crear
â”‚
â”œâ”€â”€ services/
â”‚   â””â”€â”€ break_even_service.py      # âš ï¸ NO EXISTE - Crear
â”‚
â”œâ”€â”€ views/
â”‚   â””â”€â”€ break_even_view.py         # âš ï¸ NO EXISTE - Crear
â”‚
â””â”€â”€ schemas/
    â””â”€â”€ break_even.py              # âš ï¸ NO EXISTE - Crear
```

### Dependencias de Repositorios Existentes:

- âœ… `CostFixedRepository` - Para obtener costos fijos
- âœ… `TeamMemberRepository` - Para obtener horas billables del equipo
- âœ… `ProjectRepository` - Para obtener horas asignadas actuales
- âœ… `ServiceRepository` - Para obtener servicios y mÃ¡rgenes
- âœ… `OrganizationRepository` - Para obtener configuraciÃ³n de organizaciÃ³n

---

## ðŸ“ Plan de ImplementaciÃ³n Sugerido

### Fase 1: Endpoint de AnÃ¡lisis Actual
1. Crear `schemas/break_even.py` con `BreakEvenAnalysisResponse`
2. Crear `services/break_even_service.py` con lÃ³gica de cÃ¡lculo
3. Crear `views/break_even_view.py` para transformaciÃ³n de datos
4. Crear `controllers/break_even_controller.py` para manejo HTTP
5. Crear `endpoints/break_even.py` con endpoint `GET /analytics/break-even`
6. Registrar router en `router.py`

### Fase 2: SimulaciÃ³n de Escenarios
1. Agregar schemas para `BreakEvenScenarioRequest` y `BreakEvenScenariosResponse`
2. Agregar mÃ©todo `simulate_scenarios()` en `BreakEvenService`
3. Agregar mÃ©todo `simulate_scenarios()` en `BreakEvenController`
4. Agregar endpoint `POST /analytics/break-even/scenarios`

### Fase 3: ProyecciÃ³n Temporal
1. Agregar schemas para `BreakEvenProjectionResponse`
2. Agregar mÃ©todo `get_projection()` en `BreakEvenService`
3. Agregar mÃ©todo `get_projection()` en `BreakEvenController`
4. Agregar endpoint `GET /api/v1/analytics/break-even/projection`

---

## âœ… Checklist de ImplementaciÃ³n

### Schemas (Pydantic)
- [ ] `BreakEvenAnalysisResponse`
- [ ] `BreakEvenScenarioRequest`
- [ ] `BreakEvenScenariosResponse`
- [ ] `BreakEvenProjectionResponse`
- [ ] `MonthProjection`
- [ ] `ScenarioConfig`
- [ ] `ScenarioResult`

### Services (LÃ³gica de Negocio)
- [ ] `BreakEvenService.get_current_analysis()`
- [ ] `BreakEvenService.calculate_break_even_hours()`
- [ ] `BreakEvenService.calculate_break_even_revenue()`
- [ ] `BreakEvenService.get_current_allocated_hours()`
- [ ] `BreakEvenService.calculate_utilization_rate()`
- [ ] `BreakEvenService.determine_status()`
- [ ] `BreakEvenService.simulate_scenarios()`
- [ ] `BreakEvenService.get_projection()`

### Views (TransformaciÃ³n de Datos)
- [ ] `BreakEvenView.to_analysis_response()`
- [ ] `BreakEvenView.to_scenarios_response()`
- [ ] `BreakEvenView.to_projection_response()`

### Controllers (Manejo HTTP)
- [ ] `BreakEvenController.get_current_analysis()`
- [ ] `BreakEvenController.simulate_scenarios()`
- [ ] `BreakEvenController.get_projection()`

### Endpoints (API REST)
- [ ] `GET /api/v1/analytics/break-even`
- [ ] `POST /api/v1/analytics/break-even/scenarios`
- [ ] `GET /api/v1/analytics/break-even/projection`

### Router
- [ ] Registrar `break_even.router` en `router.py` con prefix `/analytics`

---

## ðŸ”— Dependencias y ReutilizaciÃ³n

### CÃ³digo Existente que Puede Reutilizarse:

1. **`app.core.calculations.calculate_blended_cost_rate()`**
   - âœ… Ya existe
   - âœ… Calcula BCR correctamente

2. **`CostFixedRepository`**
   - âœ… Ya existe
   - âœ… Puede obtener costos fijos por organizaciÃ³n

3. **`TeamMemberRepository`**
   - âœ… Ya existe
   - âœ… Puede obtener horas billables del equipo

4. **`ProjectRepository`**
   - âœ… Ya existe
   - âœ… Puede obtener proyectos activos y horas asignadas

5. **`OrganizationRepository`**
   - âœ… Ya existe
   - âœ… Puede obtener configuraciÃ³n (moneda, etc.)

### CÃ³digo que NO Existe y Debe Crearse:

1. **CÃ¡lculo de horas de equilibrio**
2. **CÃ¡lculo de ingresos de equilibrio**
3. **CÃ¡lculo de horas asignadas actuales**
4. **CÃ¡lculo de utilizaciÃ³n**
5. **DeterminaciÃ³n de estado (above/at/below)**
6. **SimulaciÃ³n de escenarios**
7. **ProyecciÃ³n temporal**

---

## ðŸŽ¯ ConclusiÃ³n

### Estado Actual:
- âŒ **Backend NO estÃ¡ implementado**
- âš ï¸ Solo existe referencia parcial en `annual_projection` (insuficiente)
- âŒ No hay endpoints de break-even
- âŒ No hay lÃ³gica de cÃ¡lculo de break-even
- âŒ No hay simulaciÃ³n de escenarios
- âŒ No hay proyecciÃ³n temporal

### AcciÃ³n Requerida:
**Implementar mÃ³dulo completo de Break-Even Point siguiendo arquitectura MVC:**

1. Crear todos los archivos necesarios (schemas, services, views, controllers, endpoints)
2. Implementar lÃ³gica de cÃ¡lculo de break-even
3. Implementar simulaciÃ³n de escenarios
4. Implementar proyecciÃ³n temporal
5. Registrar endpoints en router
6. Agregar permisos apropiados (`require_view_analytics`)

### Prioridad:
ðŸ”´ **ALTA** - El frontend ya estÃ¡ diseÃ±ado y requiere estos endpoints para funcionar.

---

**Ãšltima actualizaciÃ³n:** 2026-01-25
