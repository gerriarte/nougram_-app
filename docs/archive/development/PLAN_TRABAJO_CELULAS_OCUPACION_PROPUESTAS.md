# Plan de Trabajo Robusto: Grupos/Celulas y Ocupacion por Propuesta Aprobada

## 1) Objetivo

Implementar un sistema robusto para:

- Crear y administrar grupos/celulas de nomina por organizacion.
- Cotizar usando porcentaje de ocupacion de una celula completa.
- Calcular costos de nomina e impuestos de forma independiente por miembro.
- Hacer seguimiento de ocupacion por estado de propuesta:
  - `tentative` (cotizada),
  - `committed` (aprobada),
  - `actual` (ejecutada).

Resultado esperado: mejor velocidad comercial sin perder control operativo ni precision financiera.

---

## 2) Alcance funcional (version robusta)

### 2.1 Nomina: Grupos y celulas

- CRUD de grupos (ejemplo: Comercial, Finanzas, Medios).
- CRUD de celulas dentro de cada grupo.
- Gestion de miembros por celula con `weight` (peso de participacion).
- Versionado de celulas (publicar version, mantener historial).

### 2.2 Cotizador: Asignacion por celula

- Modo de asignacion por item:
  - `manual` (miembros individuales),
  - `cell` (porcentaje de ocupacion de celula).
- Al usar celula:
  - seleccionar celula/version,
  - definir porcentaje de ocupacion,
  - definir horizonte temporal (mensual/semanal segun configuracion),
  - expandir a asignaciones por miembro para calculo y snapshot.

### 2.3 Seguimiento de ocupacion por propuesta aprobada

- Las propuestas aprobadas mueven capacidad a `committed`.
- Propuestas en borrador/enviadas quedan en `tentative`.
- Propuestas rechazadas/expiradas liberan capacidad.
- Dashboard de capacidad por miembro, celula y periodo.

---

## 3) Principios de negocio

1. **Snapshot historico obligatorio:** una cotizacion debe guardar `cell_version_id` aplicado.
2. **Costo por miembro independiente:** no se usa promedio global opaco.
3. **Trazabilidad completa:** todo cambio relevante genera evento auditable.
4. **Tenant isolation estricto:** ningun dato cruza organizaciones.
5. **No regresion:** flujo actual de asignacion manual debe mantenerse estable.

---

## 4) Arquitectura y modelo de datos propuesto

## 4.1 Entidades nuevas

- `team_groups`
  - `id`, `organization_id`, `name`, `is_active`, timestamps.
- `team_cells`
  - `id`, `organization_id`, `group_id`, `name`, `description`, `is_active`.
- `team_cell_versions`
  - `id`, `cell_id`, `version_number`, `published_at`, `published_by`.
- `team_cell_member_versions`
  - `id`, `cell_version_id`, `team_member_id`, `weight`, `role_override`.
- `quote_item_cell_assignments`
  - `id`, `quote_item_id`, `cell_id`, `cell_version_id`, `occupancy_pct`, `source_period`.
- `capacity_commitments`
  - `id`, `organization_id`, `team_member_id`, `source_type`, `source_id`, `state`, `period_start`, `period_end`, `hours`.
- `capacity_events` (ledger de eventos)
  - `id`, `organization_id`, `event_type`, `source_type`, `source_id`, `payload`, `created_at`.

## 4.2 Estados de capacidad

- `tentative`: cotizacion creada/actualizada no aprobada.
- `committed`: propuesta aprobada.
- `actual`: ejecucion real (futuro, integrado con tracking operativo).

## 4.3 Reglas de transicion

- Quote creada/actualizada -> recalcula `tentative`.
- Propuesta aprobada -> convierte `tentative` a `committed`.
- Propuesta rechazada/expirada -> elimina o revierte `tentative`.
- Proyecto cerrado/cancelado -> limpia `committed` pendiente.

---

## 5) Roadmap (12 semanas / 6 sprints)

## Sprint 0 (Semana 1): Discovery y contratos

**Objetivo:** cerrar definiciones sin ambiguedad.

- Definir granularidad temporal inicial (mensual recomendado para salida).
- Definir politicas de distribucion de horas (`equal`, `weighted`).
- Diseñar contratos API de celulas, versiones y asignacion por ocupacion.
- Acordar criterios de aprobacion y permisos por rol.

**Entregables:**
- RFC tecnico validado.
- Backlog de historias priorizado.
- Matriz de permisos y matriz de eventos.

## Sprint 1 (Semanas 2-3): Fundacion backend

**Objetivo:** construir dominio robusto versionable.

- Migraciones de nuevas tablas e indices.
- Repositories y servicios de dominio para grupos/celulas/versiones.
- Endpoints CRUD de grupos/celulas.
- Endpoint de publicacion de version de celula.
- Validaciones de consistencia (miembro inactivo, duplicados, tenant).

**Entregables:**
- API estable de estructura organizativa.
- Tests unitarios backend (dominio y validaciones).

## Sprint 2 (Semanas 4-5): Integracion con cotizaciones

**Objetivo:** aplicar celulas en quote builder y persistir snapshot.

- Endpoint preview para expandir celula -> asignaciones por miembro.
- Endpoint create/update quote aceptando `cell_assignment`.
- Persistencia de `cell_version_id` en quote item.
- Compatibilidad total con asignacion manual existente.

**Entregables:**
- Cotizacion por celula funcional end-to-end.
- Tests de integracion quote + allocations.

## Sprint 3 (Semanas 6-7): Ocupacion por propuesta aprobada

**Objetivo:** seguimiento operativo confiable por estado.

- Modelo `capacity_commitments` + `capacity_events`.
- Jobs/event handlers al cambiar estado de propuesta.
- Recalculo incremental por periodo (mensual).
- Alertas de sobreocupacion (>100%) por miembro/celula.

**Entregables:**
- Ocupacion `tentative`/`committed` funcional.
- Trazabilidad de cambios por evento.

## Sprint 4 (Semanas 8-9): UI de planeacion y seguimiento

**Objetivo:** visibilidad para decision comercial y operativa.

- Dashboard de capacidad por periodo.
- Filtros por cliente/propuesta/estado/celula.
- Indicador de impacto de aprobacion en pipeline.
- Explainability de calculo por miembro (horas/costo/impuestos).

**Entregables:**
- Dashboard usable para ventas + operaciones.
- UAT inicial con usuarios clave.

## Sprint 5 (Semanas 10-11): Gobernanza y finanzas avanzadas

**Objetivo:** control y seguridad empresarial.

- RBAC fino (crear/publicar celulas, aprobar con sobreocupacion, override).
- Flujo de aprobacion en casos criticos (margen bajo, capacidad excedida).
- Auditoria enriquecida de decisiones.
- Manejo robusto de costos efectivos por vigencia y moneda snapshot.

**Entregables:**
- Flujos auditables y gobernados.
- Reportes de riesgo de margen/capacidad.

## Sprint 6 (Semana 12): Hardening y release

**Objetivo:** calidad productiva y rollout controlado.

- Performance tuning (indices, queries agregadas, cache por tenant+periodo).
- E2E completos quote -> aprobacion -> capacidad.
- Observabilidad (metricas p95, errores de recalc, drift).
- Feature flags y despliegue gradual.

**Entregables:**
- Release candidate para produccion.
- Plan de monitoreo post-release.

---

## 6) KPI y criterios de exito

- % propuestas aprobadas con validacion de capacidad previa.
- Precision forecast vs committed (desviacion por periodo).
- % miembros >100% de capacidad.
- Tiempo de calculo p95 de impacto de aprobacion.
- Reduccion de tiempo para cotizar equipos complejos.

---

## 7) Riesgos y mitigaciones

- **Riesgo:** complejidad temporal alta.
  - **Mitigacion:** iniciar mensual y luego evolucionar a semanal.
- **Riesgo:** drift historico por cambios de celula.
  - **Mitigacion:** versionado + snapshot obligatorio.
- **Riesgo:** recalc costoso.
  - **Mitigacion:** eventos incrementales + jobs asincronos.
- **Riesgo:** baja adopcion comercial.
  - **Mitigacion:** UX simple primero + dashboard con valor inmediato.

---

## 8) Inicio inmediato (primeros 10 dias)

## Dia 1-2

- Cerrar RFC de contratos API.
- Definir matriz de permisos por rol.
- Definir estados y transiciones de capacidad.

## Dia 3-5

- Crear migraciones:
  - `team_groups`
  - `team_cells`
  - `team_cell_versions`
  - `team_cell_member_versions`
  - `quote_item_cell_assignments`
- Implementar repositorios de grupos/celulas/versiones.

## Dia 6-7

- Exponer endpoints CRUD de grupos y celulas.
- Exponer endpoint de publicacion de version de celula.
- Agregar pruebas unitarias de dominio.

## Dia 8-10

- Endpoint preview de expansion de celula a asignaciones por miembro.
- Primer wireframe de UI en nomina y cotizador.
- Prueba de punta a punta tecnica en staging (sin feature flag publico).

---

## 9) Definition of Done (global)

Una historia se considera terminada si cumple:

- API/documentacion actualizada.
- Tests automatizados en verde (unit/integration segun aplique).
- Sin regresion de flujo manual de asignaciones.
- Logs estructurados con `level`, `module`, `function`.
- Auditoria de eventos sensible habilitada.
- Validacion funcional en staging.

---

## 10) Proximo paso recomendado

Ejecutar Sprint 0 de inmediato y crear tickets por historia (backend/frontend/qa) con dependencia explicita.
Este documento es la base de planeacion para las ceremonias de sprint.
