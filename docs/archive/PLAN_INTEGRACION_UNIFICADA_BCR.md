# Plan de Integración Unificada del BCR

**Fecha:** 14 de febrero de 2026  
**Objetivo:** Unificar onboarding ↔ gastos ↔ nómina ↔ cotizaciones bajo una única fuente de verdad del BCR (Blended Cost Rate) en el backend.

---

## 1. Estado actual (diagnóstico)

### 1.1 Backend
| Componente | Estado | Notas |
|------------|--------|-------|
| `POST /onboarding/complete` | ✅ Existe | Guarda team + expenses en BD; retorna BCR calculado |
| `POST /onboarding/calculate-bcr` | ✅ Existe | BCR temporal (preview) antes de guardar |
| `GET /settings/calculations/agency-cost-hour` | ✅ Existe | Retorna BCR desde BD (nómina + gastos) |
| `GET/POST /settings/team` | ✅ Existe | CRUD equipo (nómina) |
| `GET/POST /settings/costs/fixed` | ✅ Existe | CRUD gastos fijos (overhead) |
| `calculate_blended_cost_rate()` | ✅ Central | Usado en cotizaciones, proyecciones, dashboard |

### 1.2 Frontend – fuentes desconectadas
| Componente | Fuente actual | Problema |
|-------------|---------------|----------|
| Onboarding | `localStorage` (`nougram_onboarding_data`) | No envía nada al backend |
| Admin (Nómina) | `adminService` → `localStorage` (`nougram_admin_members`) | Datos mock; no API |
| Admin (Gastos) | `adminService` → `localStorage` (`nougram_admin_costs`) | Datos mock; no API |
| NougramCoreContext | `localStorage` + `hydrateFromOnboarding` | BCR derivado localmente |
| Cotizaciones | `state.financials.bcr` de NougramCore | No usa BCR del backend |

### 1.3 Conclusión
No hay integración unificada. Datos duplicados en varios `localStorage`; cotizaciones no usan el BCR del backend.

---

## 2. Arquitectura objetivo

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           ÚNICA FUENTE DE VERDAD                              │
│                    Backend (PostgreSQL + Redis cache)                         │
│                                                                              │
│  TeamMember  ──┐                                                              │
│  CostFixed   ──┼──► calculate_blended_cost_rate() ──► BCR por organización    │
│  social_charges_config ─┘                                                      │
└─────────────────────────────────────────────────────────────────────────────┘
         │                    │                    │                    │
         ▼                    ▼                    ▼                    ▼
    Onboarding           Admin Nómina         Admin Gastos         Cotizaciones
    (completar)          (CRUD team)           (CRUD costs)         (leer BCR)
         │                    │                    │                    │
         └────────────────────┴────────────────────┴────────────────────┘
                                    API REST
```

---

## 3. Cambios necesarios

### Fase 1: Conectar Onboarding al Backend

| # | Acción | Archivo(s) | Detalle |
|---|--------|------------|---------|
| 1.1 | Crear cliente API para onboarding | `frontend/src/lib/api-client.ts` | Reutilizar `apiClient` existente |
| 1.2 | Llamar `POST /onboarding/calculate-bcr` en preview | `useOnboarding` / `StepReady` | Reemplazar cálculo local por API (cuando hay token) |
| 1.3 | Llamar `POST /onboarding/complete` al finalizar | `OnboardingStepper` o `StepReady` | Enviar identity, team, expenses; guardar en BD |
| 1.4 | Adaptar payload al schema backend | `CompleteOnboardingRequest` | Mapear `OnboardingData` → `{ organization_name, country, currency, profile_type, team_members, expenses }` |
| 1.5 | Guardar BCR retornado | `NougramCoreContext.hydrateFromOnboarding` | Usar `bcr_calculated` del response en lugar de valor local |

**Prerequisito:** Usuario debe estar autenticado antes de completar onboarding (o registrar org primero vía `POST /organizations/register`).

---

### Fase 2: Conectar Admin (Nómina + Gastos) al Backend

| # | Acción | Archivo(s) | Detalle |
|---|--------|------------|---------|
| 2.1 | Reemplazar `adminService` loaders por API | `adminService.ts` o nuevo `adminApi.ts` | `getMembers()` → `GET /settings/team`; `getCosts()` → `GET /settings/costs/fixed` |
| 2.2 | Reemplazar savers por API | Idem | `saveMembers()` → POST/PUT team; `saveCosts()` → POST/PUT costs |
| 2.3 | Mantener `localStorage` como cache opcional | Opcional | Solo si se requiere offline; prioridad: backend |
| 2.4 | Invalidar cache BCR tras cambios | Backend ya lo hace | `cache.invalidate_pattern("blended_cost_rate:")` en team y costs |

---

### Fase 3: BCR centralizado para Cotizaciones

| # | Acción | Archivo(s) | Detalle |
|---|--------|------------|---------|
| 3.1 | Obtener BCR desde API | `NougramCoreContext` / nuevo hook | `GET /settings/calculations/agency-cost-hour` |
| 3.2 | Hidratar `financials.bcr` desde API | `NougramCoreContext` | Reemplazar `hydrateFromOnboarding` con llamada a API al montar (si hay token) |
| 3.3 | Fallback a localStorage si no hay token | `NougramCoreContext` | Mantener lógica actual para usuarios no autenticados o demo |
| 3.4 | Invalidación en tiempo real | Opcional | Tras cambios en team/costs, refetch BCR o invalidar query |

---

### Fase 4: Sincronización Onboarding ↔ Admin

| # | Acción | Archivo(s) | Detalle |
|---|--------|------------|---------|
| 4.1 | Tras `complete_onboarding` | Frontend | Redirigir a dashboard; Admin cargará datos desde API (ya guardados) |
| 4.2 | Evitar duplicar datos | - | Onboarding crea registros; Admin solo edita los mismos |
| 4.3 | Detectar onboarding ya completado | Backend/Frontend | Flag en org (`onboarding_completed`) o contar team+expenses > 0 |

---

## 4. Endpoints de referencia (Backend)

| Método | Ruta | Uso |
|--------|------|-----|
| POST | `/api/v1/onboarding/complete` | Guardar onboarding completo (team + expenses) |
| POST | `/api/v1/onboarding/calculate-bcr` | Preview BCR antes de guardar |
| GET | `/api/v1/settings/calculations/agency-cost-hour` | Obtener BCR calculado |
| GET | `/api/v1/settings/team` | Listar miembros |
| POST | `/api/v1/settings/team` | Crear miembro |
| PUT | `/api/v1/settings/team/{id}` | Actualizar miembro |
| GET | `/api/v1/settings/costs/fixed` | Listar gastos fijos |
| POST | `/api/v1/settings/costs/fixed` | Crear gasto |
| PUT | `/api/v1/settings/costs/fixed/{id}` | Actualizar gasto |

*Nota:* El router de costs está bajo `/settings`, por tanto el BCR está en `/api/v1/settings/calculations/agency-cost-hour`.

---

## 5. Orden de implementación sugerido

```
1. Fase 2 (Admin → API)     ← Menos dependencias; desbloquea flujo
2. Fase 3 (BCR en cotiz.)   ← Cotizaciones usan BCR real
3. Fase 1 (Onboarding → API)← Cierra el ciclo; datos iniciales en BD
4. Fase 4 (Sincronización)  ← Refinamiento y edge cases
```

Alternativa si se prioriza onboarding: Fase 1 → 3 → 2 → 4.

---

## 6. Consideraciones técnicas

- **Auth:** Todas las llamadas requieren JWT. Flujo: register/login → token → completar onboarding / admin / cotizaciones.
- **Tenant:** El backend usa `organization_id` del token; no enviar org_id en body.
- **Moneda:** BCR se normaliza a `primary_currency` de la organización.
- **Caché:** `calculate_blended_cost_rate` usa Redis; invalidación automática al cambiar team o costs.

---

## 7. Criterios de éxito

- [ ] Onboarding persiste team y expenses en la BD
- [ ] Admin (Nómina y Gastos) lee y escribe en la API
- [ ] Cotizaciones usan BCR de `GET /settings/calculations/agency-cost-hour`
- [ ] Una sola fuente de verdad: BD + `calculate_blended_cost_rate()`
- [ ] Sin dependencia de `nougram_onboarding_data` o `nougram_admin_*` en localStorage para datos críticos
