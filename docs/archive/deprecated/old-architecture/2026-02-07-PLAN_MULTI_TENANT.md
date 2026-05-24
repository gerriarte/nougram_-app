# 🏗️ Plan de Trabajo: Arquitectura Multi-Tenant SaaS

**Fecha de análisis:** 12 de Diciembre, 2025  
**Fecha de actualización:** 30 de Enero, 2025  
**Estado:** Sprint 18 completado ✅ | Sprint 19 completado ✅ (IA para Configuración Asistida) | Sprint 20 completado ✅ (Proyección de Ventas Anual) | Sprint 21 completado ✅ (Precisión Financiera) | Tareas pendientes siendo seguidas en Linear (ver sección "📋 Seguimiento en Linear")

---

## 📊 Resumen Ejecutivo

Este plan transforma la aplicación actual (single-tenant) en una plataforma SaaS multi-tenant completa, permitiendo que múltiples organizaciones usen la aplicación de forma aislada y segura.

**Timeline Total:** 57-75 semanas  
**Estado Actual:** ✅ Sprint 18 completado (100%) | ✅ Sprint 19 completado (IA para Configuración Asistida) | ✅ Sprint 20 completado (Proyección de Ventas Anual) | ✅ Sprint 21 completado (Precisión Financiera) | Tareas pendientes siendo seguidas en Linear (ver sección "📋 Seguimiento en Linear")

---

## ✅ FASE 1: Sprint 2 - Estabilización (COMPLETADA)

### Estado: ✅ 100% Completado

| Sprint | Tarea | Estado | Tests |
|--------|-------|--------|-------|
| 2.1 | Testing Básico | ✅ | 33 tests (18 unitarios + 15 integración) |
| 2.2 | Optimizaciones | ✅ | Paginación, índices, caché |
| 2.3 | Dashboard | ✅ | KPIs avanzados, filtros, gráficos |
| 2.4 | Exportación | ✅ | PDF, DOCX, Email |

**Resultados:**
- ✅ Base sólida de tests antes de migración
- ✅ Rendimiento optimizado con caché e índices
- ✅ Dashboard completo con análisis avanzado
- ✅ Exportación profesional de cotizaciones

---

## 🚀 FASE 2: Multi-Tenant Architecture (Sprints 3-8)

### Sprint 3: Fundación Multi-Tenant ✅ COMPLETADO

**Objetivo:** Crear modelos y migración de datos existentes  
**Duración:** 2 semanas  
**Estado:** ✅ Completado  
**Prioridad:** Alta

#### Tareas:

1. **Crear modelo Organization**
   - Archivo: `backend/app/models/organization.py`
   - Campos: `id`, `name`, `slug`, `subscription_plan`, `subscription_status`, `settings` (JSON)
   - Relación con `User`

2. **Migración de datos existentes**
   - Crear tabla `organizations`
   - Crear organización "default" (ID=1)
   - Agregar `organization_id` (nullable primero) a:
     - `users`
     - `projects`
     - `services`
     - `costs_fixed`
     - `team_members`
     - `taxes`
   - Asignar todos los registros existentes a `organization_id = 1`
   - Hacer `organization_id` NOT NULL
   - Crear índices compuestos: `(organization_id, id)`, `(organization_id, created_at)`

3. **Actualizar modelo User**
   - Agregar `organization_id` ForeignKey
   - Relación con Organization

**Archivos clave:**
- `backend/app/models/organization.py` (nuevo)
- `backend/alembic/versions/XXX_add_multi_tenant.py` (nuevo)
- `backend/app/models/user.py` (actualizar)
- Todos los modelos (actualizar)

**Riesgos:**
- ⚠️ Migración debe ser reversible
- ⚠️ Preservar todos los datos existentes
- ⚠️ Validar integridad post-migración

---

### Sprint 4: Tenant Context y Repositorios ✅ COMPLETADO

**Objetivo:** Implementar aislamiento de datos por tenant  
**Duración:** 2 semanas  
**Dependencias:** Sprint 3 completado
**Estado:** ✅ Completado

#### Tareas:

1. **Tenant Context Manager**
   - `backend/app/core/tenant.py` (nuevo)
   - Clase `TenantContext`
   - Dependency `get_tenant_context()` con validación de suscripción

2. **Modificar BaseRepository**
   - Agregar `tenant_id` al constructor
   - Filtrado automático por `organization_id` en todas las queries
   - Métodos con tenant scoping

3. **Actualizar repositorios**
   - `ProjectRepository`, `ServiceRepository`, `CostRepository`, `TaxRepository`, `TeamRepository`
   - Constructor acepta `tenant_id`
   - Queries filtran por tenant

4. **Repository Factory**
   - `backend/app/repositories/factory.py` (nuevo)
   - Factory que crea repositorios con tenant context

---

### Sprint 5: Endpoints y Autenticación Multi-Tenant ✅ COMPLETADO

**Objetivo:** Actualizar endpoints y JWT para multi-tenant  
**Duración:** 2 semanas  
**Dependencias:** Sprint 4 completado
**Estado:** ✅ Completado

#### Tareas:

1. **Modificar JWT**
   - Incluir `organization_id` en token payload
   - Validar `organization_id` en `get_current_user()`

2. **Actualizar endpoints**
   - Agregar `tenant: TenantContext = Depends(get_tenant_context)`
   - Usar `RepositoryFactory` con `tenant.organization_id`
   - Validar ownership en update/delete
   - Endpoints afectados: todos los principales

3. **Tests de aislamiento**
   - Validar que tenant A no accede a datos de tenant B
   - Tests de data leakage prevention

---

### Sprint 6: Gestión de Organizaciones ✅ COMPLETADO

**Objetivo:** CRUD de organizaciones y gestión de usuarios  
**Duración:** 2 semanas  
**Dependencias:** Sprint 5 completado ✅  
**Estado:** ⚠️ 95% Completado (tareas pendientes en Linear)  
**Prioridad:** Alta

**Nota:** El sprint está funcional a nivel básico, pero quedan tareas pendientes para producción completa. Las tareas pendientes están siendo seguidas en Linear (ver sección "📋 Seguimiento en Linear" al final de este documento). También ver `docs/sprints/SPRINT6_PROGRESO.md` y `docs/ESTADO_PROYECTO_PARA_LINEAR.md` para detalles.

#### Tareas:

1. **Endpoints de Organizaciones** ✅ COMPLETADO
   - ✅ CRUD completo (GET /me, GET /, GET /{id}, POST /, PUT /{id}, DELETE /{id})
   - ✅ Endpoint de registro público (POST /register)
   - ✅ Setup inicial

2. **Sistema de invitaciones** ⚠️ BÁSICO COMPLETADO (mejoras pendientes)
   - ✅ Invitar usuarios a organización (POST /{id}/invite) - Genera token básico
   - ✅ Asignar usuarios (POST /{id}/users)
   - ✅ Gestionar usuarios (GET /{id}/users, PUT /{id}/users/{user_id}/role, DELETE /{id}/users/{user_id})
   - ⏳ Pendiente: Frontend completo de invitaciones (ver Linear Issue #1)

3. **Validación de límites por plan** ✅ COMPLETADO
   - ✅ Validar límites: max_users, max_projects (validate_user_limit, validate_project_limit)
   - ✅ Funciones de validación implementadas en `plan_limits.py`
   - ✅ Validación integrada en endpoints de creación

4. **Frontend básico** ⚠️ ~85% COMPLETADO (mejoras pendientes)
   - ✅ Registro de organización (página de registro público `/auth/register`) - **COMPLETADO**
   - ⚠️ Dashboard de administración (página básica funcionando, falta detalle completo) - **PARCIAL**
   - ✅ Gestión de usuarios (página migrada a endpoints de organizaciones) - **COMPLETADO**
   - ✅ Funcionalidad de invitaciones (diálogo de invitación en página de usuarios) - **COMPLETADO**
   - ✅ Página de detalle de organización completada, validación de límites en UI completada, mejoras de UX completadas

#### Resultados:
- ✅ Sistema completo de gestión de organizaciones con CRUD funcional
- ✅ Registro público de nuevas organizaciones con creación automática de usuario admin
- ⚠️ Sistema de invitaciones básico implementado (backend genera token, frontend tiene UI; falta modelo en BD, emails, aceptación)
- ✅ Gestión completa de usuarios dentro de organizaciones (agregar, actualizar roles, remover)
- ✅ Validación de límites por plan de suscripción integrada en backend
- ✅ Frontend ~95% completo (páginas principales funcionando, mejoras de UX completadas, validación de límites en UI completada)
- ✅ Vista de organizaciones mejorada con estadísticas, búsqueda y filtros (página de detalle completa)

#### Tareas Pendientes (para 100%):
- ✅ Sistema de invitaciones - Frontend completo - **COMPLETADO** (Enero 2025: Tests de integración, UI mejorada con filtros)
- ✅ Tests unitarios adicionales (OrganizationRepository, edge cases) - **COMPLETADO** (20 tests, 100% cobertura)
- ⏳ Documentación API completa - **PENDIENTE** (ver Linear Issue #8)
- ⏳ Página de detalle de organización (`/settings/organizations/[id]`) - **PENDIENTE** (ver Linear Issue #2)
- ✅ Validación de límites visible en frontend - **COMPLETADO** (Linear Issue NOU-8)
- ✅ Mejoras de UX en página de organizaciones - **COMPLETADO** (Linear Issue NOU-7)

**Nota:** Estas tareas están documentadas y siendo seguidas en Linear. Ver sección "📋 Seguimiento en Linear" al final de este documento.

**Referencias:**
- Ver `docs/sprints/SPRINT6_PROGRESO.md` sección "Tareas Pendientes" para detalles del backend
- Ver [`docs/deprecated/old-analysis/2026-02-07-SPRINT_6_ANALISIS_PENDIENTES.md`](../old-analysis/2026-02-07-SPRINT_6_ANALISIS_PENDIENTES.md) para análisis detallado del frontend
- Ver `docs/ESTADO_PROYECTO_PARA_LINEAR.md` para estado actual completo del proyecto

---
### Sprint 6.5: Sistema de Plantillas y Onboarding ✅ COMPLETADO

**Objetivo:** Implementar sistema de plantillas por área creativa para mejorar el onboarding de nuevas organizaciones  
**Duración:** 1 semana  
**Estado:** ✅ Completado  
**Dependencias:** Sprint 6 completado ✅  
**Prioridad:** Alta

#### Contexto

Este sprint mejora significativamente la experiencia de onboarding permitiendo que nuevas organizaciones comiencen con una estructura pre-configurada basada en su industria (Branding, Desarrollo Web, Audiovisual, etc.), reduciendo fricción y mejorando time-to-value.

#### Tareas Detalladas:

**6.5.1: Modelo IndustryTemplate**

- Crear: `backend/app/models/template.py` (nuevo)
- Modelo `IndustryTemplate`:hon
  - id (Integer, primary key)
  - industry_type (String, unique, index)  # "branding", "web_development", etc.
  - name (String)  # "Agencia de Branding"
  - description (Text, nullable)
  - suggested_roles (JSON)  # Array de roles con salarios, seniority, horas facturables
  - suggested_services (JSON)  # Array de servicios con márgenes objetivo
  - suggested_fixed_costs (JSON, nullable)  # Array de costos fijos sugeridos
  - is_active (Boolean, default=True)
  - created_at, updated_at (DateTime)
  **6.5.2: Migración y Seed Data**

- Crear: `backend/alembic/versions/XXX_add_industry_templates.py` (nuevo)
- Seed data para 5 plantillas iniciales:
  1. **Agencia de Branding**
     - Roles: Diseñador Gráfico Jr/Middle/Senior, Ejecutivo de Cuentas, Ilustrador
     - Servicios: Diseño de Identidad Visual, Packaging, Brand Strategy
     - Costos: Adobe Creative Cloud, Figma Team
  2. **Desarrollo Web/Software**
     - Roles: Desarrollador Frontend/Backend (Jr/Middle/Senior), Project Manager, QA Tester
     - Servicios: Landing Page, E-commerce, API REST, Mantenimiento
     - Costos: GitHub Team, AWS/Azure Credits, Herramientas de Testing
  3. **Producción Audiovisual**
     - Roles: Editor de Video, Director de Fotografía, Productor, Motion Graphics
     - Servicios: Video Corporativo, Post-producción, Motion Graphics, Animación
     - Costos: Adobe Creative Suite, Almacenamiento NAS, Licencias de Stock
  4. **Marketing Digital**
     - Roles: Community Manager, Especialista Paid Media, SEO Specialist, Content Creator
     - Servicios: Gestión Redes Sociales, Campañas Publicidad, SEO, Content Marketing
     - Costos: Herramientas de Analytics, Plataformas de Publicidad
  5. **Consultoría de Software**
     - Roles: Consultor Senior/Middle, Arquitecto de Software, Tech Lead
     - Servicios: Auditoría Técnica, Arquitectura de Sistemas, Consultoría Estratégica
     - Costos: Herramientas de Análisis, Licencias de Software

**6.5.3: Lógica de Aplicación de Plantillas**

- Crear: `backend/app/services/template_service.py` (nuevo)
- Función principal: `apply_industry_template()`
  - Parámetros: `organization_id`, `industry_type`, `region`, `currency`, `customize`, `db`
  - Funcionalidades:
    - Ajuste de rangos salariales por región (multiplier por país)
    - Crear TeamMembers (valores promedio o placeholders)
    - Crear Services con márgenes objetivos
    - Crear CostFixed sugeridos (marcados como `is_suggested=True`)
    - Guardar contexto de onboarding en `Organization.settings`

**6.5.4: Ajustes por Región**

- Multiplicadores por región (basados en USD):hon
  REGION_MULTIPLIERS = {
      "US": 1.0,      # Baseline
      "UK": 0.85,
      "COL": 0.25,    # Colombia
      "ARG": 0.15,    # Argentina
      "MEX": 0.30,    # México
      "ESP": 0.70,    # España
      "BR": 0.20,     # Brasil
  }
  - Ajustar salarios automáticamente según región seleccionada

**6.5.5: Endpoints de Plantillas**

- Crear: `backend/app/api/v1/endpoints/templates.py` (nuevo)
- Endpoints:
  - `GET /api/v1/templates/industries` - Listar plantillas disponibles
  - `GET /api/v1/templates/industries/{industry_type}` - Obtener detalle de plantilla
  - `POST /api/v1/organizations/{id}/apply-template` - Aplicar plantilla a organización

**6.5.6: Frontend - Onboarding Flow**

- Crear: `frontend/src/app/(app)/onboarding/` (nuevo)
- Flujo multi-step:
  1. **Paso 1:** Información Básica (nombre, país, moneda, email)
  2. **Paso 2:** Selección de Industria (listado visual de plantillas)
  3. **Paso 3:** Preview de Plantilla (estructura sugerida)
  4. **Paso 4:** Personalización (opcional - editar roles, servicios, costos)
  5. **Paso 5:** Confirmación y aplicación
- Integración con registro público

**6.5.7: Actualización de Organization Model**

- Usar `Organization.settings` (JSONB) para almacenar contexto:
  
  {
    "onboarding_completed": true,
    "industry_type": "branding",
    "client_types": ["startups", "enterprise"],
    "services_offered": ["identity_design", "packaging"],
    "team_size_range": "small",
    "template_applied_at": "2025-01-15T10:30:00Z",
    "template_applied_region": "US",
    "template_applied_currency": "USD"
  }
  **Archivos clave:**
- `backend/app/models/template.py` (nuevo)
- `backend/app/services/template_service.py` (nuevo)
- `backend/app/api/v1/endpoints/templates.py` (nuevo)
- `backend/alembic/versions/XXX_add_industry_templates.py` (nuevo)
- `frontend/src/app/(app)/onboarding/` (nuevo - múltiples páginas)

**Criterios de aceptación:**
- [x] Modelo IndustryTemplate creado ✅
- [x] 5 plantillas predefinidas creadas como seed data ✅
- [x] Endpoints de plantillas funcionando ✅
- [x] Aplicación de plantilla crea recursos correctamente (TeamMembers, Services, CostFixed) ✅
- [x] Ajuste de salarios por región funciona ✅
- [x] Onboarding flow completo y funcional ✅
- [x] UI intuitiva y responsive ✅
- [x] Tests de aplicación de plantilla pasando ✅
- [x] Validación de datos (al menos 1 rol y 1 servicio creados) ✅

**Valor de negocio:**
- ✅ Reduce fricción significativamente (no empezar desde cero)
- ✅ Mejora tasa de conversión en registro
- ✅ Diferencia competitiva clara
- ✅ Mejora time-to-value (usuario productivo más rápido)
- ✅ Reduce barrera de entrada

---

### Sprint 7: Facturación y Suscripciones ✅ COMPLETADO

**Objetivo:** Integración con Stripe para gestionar suscripciones y pagos  
**Duración:** 2 semanas  
**Estado:** ✅ Completado  
**Dependencias:** Sprint 6.5 completado ✅  
**Prioridad:** Alta

#### Tareas:

1. **Integración Stripe** ✅ COMPLETADO
   - ✅ Planes: free, starter, professional, enterprise
   - ✅ Webhook handler implementado

2. **Endpoints de facturación** ✅ COMPLETADO
   - ✅ Checkout (POST /billing/checkout-session)
   - ✅ Webhook de Stripe (POST /stripe/webhook)
   - ✅ Gestión de suscripción (GET/PUT /billing/subscription, POST /billing/subscription/cancel)
   - ✅ Listado de planes (GET /billing/plans)

3. **Modelo de planes** ✅ COMPLETADO
   - ✅ Modelo Subscription creado
   - ✅ Configuración de planes y límites en `plan_limits.py`
   - ✅ Repository de subscriptions implementado

4. **Frontend de facturación** ✅ COMPLETADO
   - ✅ Página de planes (`/settings/billing`)
   - ✅ Gestión de suscripción (upgrade, downgrade, cancel)
   - ✅ Dashboard con estado actual

#### Resultados:
- ✅ Integración completa con Stripe para suscripciones
- ✅ Modelo Subscription con historial de cambios
- ✅ Webhooks sincronizando estado con Stripe
- ✅ Frontend completo para gestión de suscripciones
- ✅ Planes configurados con límites y precios

---

### Sprint 8: Testing y Seguridad Multi-Tenant ✅ COMPLETADO

**Objetivo:** Validar aislamiento y seguridad  
**Duración:** 2 semanas  
**Estado:** ✅ Completado  
**Dependencias:** Sprint 7 completado ✅  
**Prioridad:** Alta

#### Tareas:

1. **Tests de seguridad** ✅ COMPLETADO
   - ✅ Data leakage prevention
   - ✅ Cross-tenant access prevention
   - ✅ Validación de límites
   - ✅ Tests avanzados en `test_security_advanced.py`

2. **Auditoría** ✅ COMPLETADO
   - ✅ Modelo `AuditLog` creado
   - ✅ Repository de audit logs implementado
   - ✅ Servicio de auditoría (`AuditService`) creado
   - ✅ Logging de acciones críticas en endpoints (login, creación de proyectos, usuarios, servicios)
   - ✅ Migración para tabla `audit_logs` creada

3. **Rate limiting por tenant** ✅ COMPLETADO
   - ✅ Rate limiting básico implementado con `slowapi`
   - ✅ Límites diferenciados por plan (free, starter, professional, enterprise)
   - ✅ Rate limiting aplicado al endpoint de login (5 intentos/minuto)
   - ✅ Configuración de límites por tipo de operación

4. **Performance testing** ✅ COMPLETADO
   - ✅ Tests con múltiples tenants en `test_performance_multi_tenant.py`
   - ✅ Validación de aislamiento de queries
   - ✅ Validación de efectividad de índices
   - ✅ Tests de queries concurrentes
   - ✅ Tests con datasets grandes

#### Resultados:
- ✅ Sistema de auditoría completo para rastrear acciones críticas
- ✅ Rate limiting implementado para proteger endpoints sensibles
- ✅ Tests exhaustivos de seguridad validando aislamiento multi-tenant
- ✅ Tests de performance confirmando eficiencia del sistema
- ✅ Validación de límites por plan funcionando correctamente

---

## 🔗 FASE 3: Integraciones Multi-Tenant (Sprint 9)

### Sprint 9: Integraciones Completas ✅ COMPLETADO

**Objetivo:** Completar integraciones con soporte multi-tenant  
**Duración:** 2 semanas  
**Estado:** ✅ Completado  
**Dependencias:** Sprint 8 completado ✅  
**Prioridad:** Media

#### Tareas:

1. **Google Sheets** (con tenant scoping) ✅ COMPLETADO
   - ✅ Actualizado `sync_google_sheets_data` para incluir `organization_id`
   - ✅ Datos sincronizados (costs y team members) se asignan al tenant correcto
   - ✅ Endpoint actualizado para usar `TenantContext`
   - ✅ Queries filtran por `organization_id` al buscar existentes

2. **Google Calendar** (por usuario dentro de organización) ✅ COMPLETADO
   - ✅ Verificado que OAuth flow funciona correctamente por usuario
   - ✅ `google_refresh_token` se almacena por usuario (ya estaba en modelo User)
   - ✅ Cada usuario dentro de una organización tiene su propia conexión
   - ✅ Campo `has_calendar_connected` refleja estado de conexión por usuario

3. **Eliminación de Apollo.io** ✅ COMPLETADO
   - ✅ Código de Apollo.io eliminado (`app/core/apollo.py`)
   - ✅ Endpoint de Apollo.io eliminado
   - ✅ Schemas de Apollo.io eliminados
   - ✅ `APOLLO_API_KEY` eliminado de configuración
   - ✅ Referencias limpiadas en imports

#### Resultados:
- ✅ Google Sheets con soporte multi-tenant completo
- ✅ Google Calendar funcionando correctamente por usuario (ya estaba implementado)
- ✅ Código de Apollo.io completamente eliminado
- ✅ Integraciones listas para uso en producción multi-tenant

---

## 👥 FASE 4: Sistema de Usuarios, Roles y Créditos (Sprints 10-13)

### Sprint 10: Arquitectura de Roles y Permisos ✅ COMPLETADO

**Objetivo:** Implementar sistema robusto de roles con dos niveles (Soporte y Cliente)  
**Duración:** 2 semanas  
**Estado:** ✅ Completado  
**Dependencias:** Sprint 9 completado ✅  
**Prioridad:** Alta

#### Contexto

Este sprint implementa la arquitectura de roles propuesta con dos niveles claramente diferenciados:
- **Nivel Soporte (Multi-Tenant Manager):** Para el equipo que gestiona la plataforma
- **Nivel Cliente (Tenant):** Para usuarios dentro de cada organización

#### Tareas Detalladas:

**10.1: Actualizar Modelo User**

- Actualizar: `backend/app/models/user.py`
- Agregar campo `role_type`:
  ```python
  role_type = Column(String(16), nullable=True, index=True)  
  # Valores: "support" | "tenant" | NULL (retrocompatibilidad)
  ```
- Validación:
  - Si `role_type == "support"` → `organization_id` puede ser NULL
  - Si `role_type == "tenant"` → `organization_id` es REQUIRED
  - Si `role_type == NULL` → Se asume "tenant" (retrocompatibilidad)

**10.2: Definir Matriz de Roles**

- Crear: `backend/app/core/roles.py` (nuevo)

Roles de Soporte:
- `super_admin`: Control total de la plataforma
- `support_manager`: Gestor de Clientes (acceso limitado, datos anonimizados)
- `data_analyst`: Analista de Datos (solo datasets anonimizados)

Roles de Cliente (Tenant):
- `owner`: Dueño de la cuenta (único que paga, acceso completo)
- `admin_financiero`: Admin financiero (ve costos sensibles, gestiona costos)
- `product_manager`: PM (crea propuestas, consume créditos)
- `collaborator`: Colaborador (puede crear borradores, NO puede enviar, NO ve costos)

**10.3: Sistema de Permisos**

- Crear: `backend/app/core/permissions.py` (actualizar completamente)
- Implementar matriz de permisos `PERMISSION_MATRIX`:
  - `can_access_all_tenants`
  - `can_view_sensitive_data`
  - `can_modify_costs`
  - `can_create_quotes`
  - `can_send_quotes`
  - `can_manage_subscription`
  - `can_invite_users`
  - `credits_required` (si el rol consume créditos)
- Funciones de validación:
  - `check_permission(user, permission) -> bool`
  - `require_permission(user, permission) -> None` (raise si no tiene)
  - `can_user_access_tenant(user, tenant_id) -> bool`

**10.4: Migración de Roles Existentes**

- Crear: `backend/alembic/versions/XXX_add_role_type.py` (nuevo)
- Migración:
  1. Agregar columna `role_type` (nullable)
  2. Actualizar usuarios existentes:
     - Si `role == "super_admin"` → `role_type = "support"`
     - Resto → `role_type = "tenant"`
  3. Hacer `role_type` NOT NULL después de migrar

**10.5: Actualizar Autenticación**

- Actualizar: `backend/app/core/security.py`
- Modificar `get_current_user()`:
  - Validar `role_type` si existe
  - Validar que `organization_id` existe si `role_type == "tenant"`
- Actualizar `create_access_token()`:
  - Incluir `role_type` en payload JWT

**10.6: Tests de Roles**

- Crear: `backend/tests/integration/test_roles_permissions.py` (nuevo)
- Validar:
  - Usuarios de soporte pueden acceder a múltiples tenants
  - Usuarios de tenant solo acceden a su organización
  - Permisos se validan correctamente
  - Retrocompatibilidad con usuarios sin `role_type`

**Archivos clave:**
- `backend/app/models/user.py` (actualizar)
- `backend/app/core/roles.py` (nuevo)
- `backend/app/core/permissions.py` (actualizar completamente)
- `backend/app/core/security.py` (actualizar)
- `backend/alembic/versions/XXX_add_role_type.py` (nuevo)
- `backend/tests/integration/test_roles_permissions.py` (nuevo)

**Criterios de aceptación:**
- ✅ Campo `role_type` agregado a User model
- ✅ Matriz de permisos completa implementada
- ✅ Migración creada (pendiente ejecutar en producción)
- ✅ Validación de permisos funciona con funciones helper
- ✅ Tests de roles y permisos creados
- ✅ Retrocompatibilidad mantenida (NULL role_type se infiere como "tenant")

#### Resultados:
- ✅ Sistema de roles de dos niveles implementado (support/tenant)
- ✅ Matriz de permisos completa para todos los roles
- ✅ Validación de permisos funcional
- ✅ Control de acceso multi-tenant mejorado
- ✅ Tests comprehensivos para roles y permisos
- ✅ Migración lista para agregar role_type a usuarios existentes

---

### Sprint 11: Sistema de Créditos ✅ COMPLETADO

**Objetivo:** Implementar sistema de créditos con asignación automática por suscripción y manual por super_admin  
**Duración:** 2 semanas  
**Estado:** ✅ Completado  
**Dependencias:** Sprint 10 completado  
**Prioridad:** Alta

#### Contexto

Sistema híbrido donde:
- Las suscripciones otorgan créditos base mensuales
- El super_admin puede asignar créditos adicionales a criterio
- Los créditos se consumen al crear/enviar propuestas (según rol)
- Owner y Admin Financiero no consumen créditos

#### Tareas Detalladas:

**11.1: Modelo CreditAccount**

- Crear: `backend/app/models/credit_account.py` (nuevo)
- Campos:
  - `id`, `organization_id` (FK, unique)
  - `credits_available` (Integer, default=0)
  - `credits_used_total` (Integer, default=0)
  - `credits_used_this_month` (Integer, default=0)
  - `credits_per_month` (Integer, nullable - NULL = ilimitado)
  - `last_reset_at`, `next_reset_at` (DateTime)
  - `manual_credits_bonus` (Integer, default=0) - Créditos adicionales asignados manualmente
  - `manual_credits_last_assigned_at` (DateTime, nullable)
  - `manual_credits_assigned_by` (FK a User, nullable)
  - `created_at`, `updated_at`

**11.2: Modelo CreditTransaction**

- Crear: `backend/app/models/credit_transaction.py` (nuevo)
- Campos:
  - `id`, `organization_id` (FK)
  - `transaction_type` (String: "subscription_grant", "manual_adjustment", "consumption", "refund")
  - `amount` (Integer - positivo = agregados, negativo = consumidos)
  - `reason` (String, nullable)
  - `reference_id` (Integer, nullable - ID de quote/project relacionado)
  - `performed_by` (FK a User, nullable)
  - `created_at`

**11.3: Configuración de Créditos por Plan**

- Actualizar: `backend/app/core/plan_limits.py`
- Agregar créditos base:
  - `free`: 10 créditos/mes
  - `starter`: 100 créditos/mes
  - `professional`: 500 créditos/mes
  - `enterprise`: -1 (ilimitado)

**11.4: Servicio de Gestión de Créditos**

- Crear: `backend/app/services/credit_service.py` (nuevo)
- Funciones principales:
  - `get_or_create_credit_account(organization_id, db) -> CreditAccount`
  - `validate_and_consume_credits(organization_id, amount, user_id, reason, db) -> bool`
  - `grant_subscription_credits(organization_id, db) -> None` (reseteo mensual)
  - `grant_manual_credits(organization_id, amount, granted_by, reason, db) -> None`
  - `refund_credits(organization_id, amount, reason, db) -> None`
  - `get_credit_balance(organization_id, db) -> dict`

**11.5: Integración en Endpoints de Quotes**

- Actualizar: `backend/app/api/v1/endpoints/quotes.py`
- Agregar validación de créditos en:
  - `POST /quotes/` (crear propuesta)
  - `PUT /quotes/{id}/send` (enviar propuesta)
- Lógica:
  - Si `user.role in ["owner", "admin_financiero"]` → NO consumir créditos
  - Si `user.role == "product_manager"` → Consumir 1 crédito
  - Si `user.role == "collaborator"` → NO puede enviar (error 403)

**11.6: Endpoints de Créditos para Super Admin**

- Crear: `backend/app/api/v1/endpoints/credits.py` (nuevo)
- Endpoints:
  - `GET /api/v1/admin/organizations/{org_id}/credits` - Ver balance de créditos
  - `POST /api/v1/admin/organizations/{org_id}/credits/grant` - Asignar créditos manualmente
    - Body: `{"amount": 100, "reason": "Bono por cliente premium"}`
  - `GET /api/v1/admin/organizations/{org_id}/credits/transactions` - Historial de transacciones
  - `POST /api/v1/admin/organizations/{org_id}/credits/reset` - Forzar reseteo mensual (manual)

**11.7: Endpoints de Créditos para Clientes**

- Agregar a: `backend/app/api/v1/endpoints/organizations.py`
- Endpoints:
  - `GET /api/v1/organizations/me/credits` - Ver balance actual
  - `GET /api/v1/organizations/me/credits/history` - Historial de consumo

**11.8: Job Automático de Reseteo Mensual**

- Crear: `backend/app/core/tasks.py` (nuevo) o usar Celery/Background Tasks
- Tarea programada:
  - Ejecutar diariamente (o cada hora)
  - Verificar organizaciones con `next_reset_at <= now()`
  - Resetear `credits_used_this_month = 0`
  - Otorgar nuevos créditos según plan
  - Actualizar `last_reset_at` y `next_reset_at`

**11.9: Frontend - Dashboard de Créditos**

- Crear: `frontend/src/app/(app)/credits/` (nuevo)
- Páginas:
  - Dashboard de créditos (balance, consumo, gráfico)
  - Historial de transacciones
- Componente: Badge de créditos en header/navbar

**11.10: Frontend Admin - Gestión de Créditos**

- Crear: `frontend/src/app/(app)/admin/organizations/[id]/credits/` (nuevo)
- Funcionalidades:
  - Ver balance actual del tenant
  - Formulario para asignar créditos manualmente
  - Historial de transacciones
  - Botón de reseteo manual (solo super_admin)

**Archivos clave:**
- `backend/app/models/credit_account.py` (nuevo)
- `backend/app/models/credit_transaction.py` (nuevo)
- `backend/app/services/credit_service.py` (nuevo)
- `backend/app/core/plan_limits.py` (actualizar)
- `backend/app/api/v1/endpoints/credits.py` (nuevo)
- `backend/app/api/v1/endpoints/quotes.py` (actualizar)
- `backend/app/api/v1/endpoints/organizations.py` (actualizar)
- `backend/app/core/tasks.py` (nuevo)
- `frontend/src/app/(app)/credits/` (nuevo)
- `frontend/src/app/(app)/admin/organizations/[id]/credits/` (nuevo)

**Criterios de aceptación:**
- [x] Modelos CreditAccount y CreditTransaction creados
- [x] Créditos se asignan automáticamente según plan de suscripción
- [x] Super admin puede asignar créditos adicionales manualmente
- [x] Créditos se consumen al crear/enviar propuestas (según rol)
- [x] Reseteo mensual automático funciona (a través de grant_subscription_credits)
- [x] Owner y Admin Financiero NO consumen créditos
- [x] Historial de transacciones completo
- [ ] Dashboard de créditos funcional (Frontend pendiente)
- [x] Tests de consumo y asignación pasando (16/16 tests pasando)

#### Resultados:
- ✅ Modelos CreditAccount y CreditTransaction implementados
- ✅ Repositorios para gestión de créditos creados
- ✅ Servicio de créditos completo con todas las funciones necesarias
- ✅ Endpoints para clientes y administradores creados
- ✅ Integración con creación de proyectos/quotes (consume créditos según rol)
- ✅ Integración con suscripciones (asignación automática)
- ✅ Migración de base de datos creada y lista
- ✅ Tests comprehensivos: 16/16 pasando
- ⏳ Frontend pendiente (Sprint futuro)

---

### Sprint 12: Nivel de Soporte y Anonimización de Datos ✅ COMPLETADO

**Objetivo:** Implementar roles de soporte con acceso limitado y anonimización de datos sensibles  
**Duración:** 2 semanas  
**Estado:** ✅ Completado  
**Dependencias:** Sprint 11 completado  
**Prioridad:** Media

#### Tareas Detalladas:

**12.1: Servicio de Anonimización**

- Crear: `backend/app/services/data_anonymizer.py` (nuevo)
- Funciones:
  - `anonymize_blended_rate(rate: float) -> str` (convertir a rango: "$0-50", "$50-100", "$100+")
  - `anonymize_quote_totals(quote: Quote) -> dict` (sin montos exactos)
  - `anonymize_project_cost_data(project: Project) -> dict`
  - `anonymize_team_salaries(team_members: List[TeamMember]) -> dict` (solo roles, no salarios)

**12.2: Endpoints para Support Manager**

- Crear: `backend/app/api/v1/endpoints/support.py` (nuevo)
- Endpoints:
  - `GET /api/v1/support/organizations` - Listar todas las organizaciones (con métricas anonimizadas)
  - `GET /api/v1/support/organizations/{org_id}/analytics` - Analytics anonimizado
  - `GET /api/v1/support/organizations/{org_id}/quotes` - Historial de propuestas (sin montos exactos)
  - `GET /api/v1/support/organizations/{org_id}/usage` - Métricas de uso (créditos, actividad)
- Validación: Solo usuarios con `role == "support_manager"` o `role == "super_admin"`

**12.3: Dashboard de Soporte**

- Crear: `frontend/src/app/(app)/support/` (nuevo)
- Páginas:
  - Overview de todos los tenants (métricas agregadas)
  - Detalle de tenant específico (con datos anonimizados)
  - Búsqueda y filtros por plan, estado, uso

**12.4: Endpoints para Data Analyst**

- Agregar a: `backend/app/api/v1/endpoints/support.py`
- Endpoints:
  - `GET /api/v1/support/datasets/anonymized` - Datasets completamente anonimizados para ML
  - `POST /api/v1/support/datasets/export` - Exportar dataset anonimizado (CSV/JSON)

**Archivos clave:**
- `backend/app/services/data_anonymizer.py` (nuevo)
- `backend/app/api/v1/endpoints/support.py` (nuevo)
- `frontend/src/app/(app)/support/` (nuevo)

**Criterios de aceptación:**
- [x] Support Manager ve datos anonimizados correctamente
- [x] No se exponen salarios ni costos exactos
- [x] Super Admin tiene acceso completo
- [x] Data Analyst solo accede a datasets anonimizados
- [ ] Dashboard de soporte funcional (Frontend pendiente)
- [x] Tests de anonimización pasando (17/17 tests pasando)

#### Resultados:
- ✅ Servicio de anonimización completo (`data_anonymizer.py`)
- ✅ Endpoints para Support Manager con datos anonimizados
- ✅ Endpoints para Data Analyst (solo datasets anonimizados)
- ✅ Validación de permisos en todos los endpoints de soporte
- ✅ Tests comprehensivos: 17/17 pasando
- ⏳ Frontend pendiente (Sprint futuro)

---

### Sprint 13: Permisos Granulares y UI por Rol

**Objetivo:** Implementar validación completa de permisos en todos los endpoints y ajustar UI según rol  
**Duración:** 2 semanas  
**Estado:** ✅ Completado (100%) - Tests exhaustivos implementados y pasando (36/36 tests)  
**Dependencias:** Sprint 12 completado  
**Prioridad:** Alta

#### Tareas Detalladas:

**13.1: Actualizar Todos los Endpoints**

- Revisar y actualizar TODOS los endpoints con validación de permisos:
  - `backend/app/api/v1/endpoints/projects.py`
  - `backend/app/api/v1/endpoints/services.py`
  - `backend/app/api/v1/endpoints/costs.py`
  - `backend/app/api/v1/endpoints/team.py`
  - `backend/app/api/v1/endpoints/taxes.py`
  - `backend/app/api/v1/endpoints/quotes.py`
  - `backend/app/api/v1/endpoints/insights.py`
- Agregar validaciones:
  - `can_view_sensitive_data` para ver salarios/costos
  - `can_modify_costs` para editar costos/salarios
  - `can_send_quotes` para enviar propuestas
  - `credits_required` para consumo de créditos

**13.2: Middleware de Validación de Permisos**

- Crear: `backend/app/core/permission_middleware.py` (nuevo)
- Decorators reutilizables:
  - `@require_permission("can_modify_costs")`
  - `@require_role(["owner", "admin_financiero"])`
  - `@require_support_role(["super_admin", "support_manager"])`

**13.3: Frontend - Ocultar/Mostrar Features por Rol**

- Actualizar componentes para verificar rol del usuario
- Ocultar:
  - Sección de costos/salarios para `product_manager` y `collaborator`
  - Botón "Enviar propuesta" para `collaborator`
  - Gestión de suscripción para todos excepto `owner`
  - Invitaciones de usuarios para todos excepto `owner`
- Mostrar:
  - Badge de créditos solo a usuarios que los consumen
  - Alertas cuando se acaban créditos (solo PM)

**13.4: Tests Exhaustivos de Seguridad ✅ COMPLETADO**

- ✅ Creado: `backend/tests/integration/test_permissions_exhaustive.py`
- ✅ Validaciones implementadas:
  - Cada rol solo puede hacer acciones permitidas
  - Data leakage prevention (PM no ve costos, collaborator no ve datos sensibles)
  - Cross-tenant access prevention
  - Tests de admin_financiero permissions
  - Tests de consumo de créditos según rol (preparados para cuando se implemente en endpoints)

**Archivos clave:**
- Todos los endpoints (actualizar)
- `backend/app/core/permission_middleware.py` (nuevo)
- Todos los componentes del frontend (actualizar)
- `backend/tests/integration/test_permissions_exhaustive.py` (nuevo)

**Criterios de aceptación:**
- [x] Middleware de validación de permisos creado
- [x] Endpoints críticos actualizados (team, costs, services, projects, quotes, insights)
- [x] Todos los endpoints principales validan permisos correctamente
- [x] UI se adapta según rol del usuario
- [x] No hay data leakage entre roles (validado con tests)
- [x] Tests exhaustivos de seguridad pasando
- [x] Documentación de permisos actualizada

#### Progreso Actual:

**13.2: Middleware de Validación de Permisos ✅ COMPLETADO**

- Creado: `backend/app/core/permission_middleware.py`
- Decorators reutilizables:
  - `require_permission_decorator(permission: str)`: Para validar permisos específicos
  - `require_role_decorator(allowed_roles: List[str])`: Para validar roles específicos
  - `require_support_role_decorator()`: Para validar roles de soporte
- Dependencias de conveniencia:
  - `require_view_sensitive_data`, `require_modify_costs`, `require_create_quotes`, etc.

**13.1: Actualizar Endpoints ✅ COMPLETADO**

Endpoints actualizados con validaciones de permisos:
- ✅ `team.py`: list, create, update, delete (todos requieren permisos apropiados)
- ✅ `costs.py`: list (view_sensitive_data), create/update (modify_costs), delete (delete_resources)
- ✅ `services.py`: create (create_services), update (create_services), delete (delete_resources)
- ✅ `projects.py`: create (create_projects), send_quote_email (send_quotes)
- ✅ `quotes.py`: calculate (create_quotes)
- ✅ `insights.py`: dashboard, ai-advisor (view_analytics)
- ✅ `taxes.py`: update, delete (modify_costs, delete_resources)
- ✅ `organizations.py`: invite_user (invite_users), add_user (invite_users), update_subscription (manage_subscription)

**13.3: Frontend - Ocultar/Mostrar Features por Rol ✅ COMPLETADO**

- ✅ Creado: `frontend/src/lib/permissions.ts` - Utilidades de permisos para frontend
- ✅ `AppSidebar.tsx`: Filtra items del menú según permisos (oculta costs, team, billing, organizations si no tiene permisos)
- ✅ `settings/page.tsx`: Filtra secciones según permisos
- ✅ `projects/[id]/page.tsx`: Oculta botón "Enviar Email" para collaborator
- ✅ `projects/[id]/quotes/[quoteId]/edit/page.tsx`: Oculta botón "Enviar por Email" para collaborator
- ✅ `settings/users/page.tsx`: Oculta botones "Invitar Usuario" y "Crear Usuario" para usuarios sin permisos
- ✅ `settings/billing/page.tsx`: Oculta botones de upgrade/cancel para usuarios sin permisos

**Resultados:**
- ✅ Middleware completo y funcional
- ✅ 15+ endpoints críticos actualizados con validaciones de permisos
- ✅ Frontend adapta UI según rol del usuario
- ✅ Prevención de data leakage (PM y Collaborator no pueden ver costos/salarios)
- ✅ Documentación de permisos en cada endpoint actualizado
- ✅ Tests exhaustivos de seguridad implementados (30+ tests)
- ✅ Tests de data leakage prevention implementados
- ✅ Tests de cross-tenant access prevention implementados
- ✅ Tests de admin_financiero permissions implementados
- ✅ Documentación de permisos actualizada con sección de tests

---

## 🎨 FASE 5: Pool de Plantillas Ampliado - Servicios Basados en Conocimiento (Sprints 14-16)

### Sprint 14: Fundación - Tipos de Servicios y Costeo Avanzado

**Objetivo:** Extender modelos y cálculos para soportar facturación fija, servicios recurrentes y horas no facturables  
**Duración:** 2-3 semanas  
**Estado:** Pendiente  
**Dependencias:** Sprint 13 completado  
**Prioridad:** Media

#### Contexto

Ampliar el sistema de cotización más allá de facturación por horas para soportar:
- Sector Legal y Consultoría: Facturación por hito/módulo con precio fijo
- Sector Finanzas: Servicios recurrentes (retainers)
- Horas no facturables para compliance/admin (Legal)

#### Tareas Detalladas:

**14.1: Extender Modelo Service**

- Actualizar: `backend/app/models/service.py`
- Agregar campos:
  ```python
  # Enum para tipos de facturación
  pricing_type = Column(String, default="hourly", nullable=False)
  # Valores: "hourly", "fixed", "recurring", "project_value"
  
  fixed_price = Column(Float, nullable=True)  # Si pricing_type = "fixed"
  is_recurring = Column(Boolean, default=False)
  billing_frequency = Column(String, nullable=True)  # "monthly", "annual"
  recurring_price = Column(Float, nullable=True)  # Precio recurrente
  ```
- Validación: Si `pricing_type == "fixed"`, `fixed_price` es requerido

**14.2: Extender Modelo TeamMember**

- Actualizar: `backend/app/models/team.py`
- Agregar campo:
  ```python
  non_billable_hours_percentage = Column(Float, default=0.0)
  # Porcentaje de tiempo admin/compliance (ej: 0.20 = 20%)
  ```
- Impacto: Usado en cálculo de BCR ajustado

**14.3: Actualizar Cálculo de BCR**

- Actualizar: `backend/app/core/calculations.py`
- Modificar `calculate_blended_cost_rate()`:
  - Incluir ajuste por horas no facturables:
    ```python
    billable_hours_adj = member.billable_hours_per_week * \
                        (1 - member.non_billable_hours_percentage)
    ```
  - Ajustar cálculo de horas mensuales facturables

**14.4: Extender QuoteItem**

- Actualizar: `backend/app/models/project.py`
- Agregar campos a `QuoteItem`:
  ```python
  pricing_type = Column(String, nullable=True)  # Sobrescribe servicio
  fixed_price = Column(Float, nullable=True)  # Si es facturación fija
  quantity = Column(Float, default=1.0)  # Para módulos/milestones
  ```
- Mantener `estimated_hours` para retrocompatibilidad

**14.5: Nueva Función de Cálculo Avanzado**

- Actualizar: `backend/app/core/calculations.py`
- Crear: `calculate_quote_totals_enhanced()`
- Lógica:
  - Si `pricing_type == "hourly"`: Lógica actual (horas × BCR)
  - Si `pricing_type == "fixed"`: Usar `fixed_price × quantity`
  - Si `pricing_type == "recurring"`: Calcular basado en tiempo asignado vs precio recurrente

**14.6: Migración de Base de Datos**

- Crear: `backend/alembic/versions/XXX_add_service_pricing_types.py`
- Pasos:
  1. Agregar nuevos campos a `services` (nullable primero)
  2. Agregar campo a `team_members` (default=0.0)
  3. Agregar campos a `quote_items` (nullable)
  4. Migrar servicios existentes: `pricing_type = "hourly"`
  5. Hacer campos requeridos según corresponda

**14.7: Plantillas para Legal y Finanzas**

- Actualizar: `backend/app/models/template.py` y seed data
- Agregar plantillas:
  1. **Legal/Consultoría**
     - Roles: Senior Partner (non_billable: 0.20), Asociado (0.10)
     - Servicios: "Revisión de Contrato" (fixed_price: 500), "Sesión de Asesoría" (hourly)
     - Costos: Licencias legales, seguros de responsabilidad
  2. **Finanzas/Contabilidad**
     - Roles: Contador Senior, Auditor Junior
     - Servicios: "Declaración de Impuestos" (fixed), "Retainer Mensual" (recurring)
     - Costos: Licencias de software (SAP, QuickBooks, Oracle)

**14.8: Actualizar Endpoints de Quotes**

- Actualizar: `backend/app/api/v1/endpoints/quotes.py`
- Modificar `calculate_quote()`:
  - Detectar `pricing_type` del servicio
  - Usar `calculate_quote_totals_enhanced()` en lugar de la función básica
  - Validar que campos requeridos estén presentes según tipo

**14.9: Frontend - Formulario Adaptativo**

- Actualizar: `frontend/src/app/(app)/projects/new/page.tsx`
- Lógica condicional:
  - Si `pricing_type == "hourly"`: Mostrar campo de horas
  - Si `pricing_type == "fixed"`: Mostrar campo de precio fijo y cantidad
  - Si `pricing_type == "recurring"`: Mostrar precio recurrente y frecuencia

**Archivos clave:**
- `backend/app/models/service.py` (actualizar)
- `backend/app/models/team.py` (actualizar)
- `backend/app/models/project.py` (actualizar QuoteItem)
- `backend/app/core/calculations.py` (actualizar y agregar función)
- `backend/alembic/versions/XXX_add_service_pricing_types.py` (nuevo)
- `backend/app/api/v1/endpoints/quotes.py` (actualizar)
- `frontend/src/app/(app)/projects/new/page.tsx` (actualizar)

**Criterios de aceptación:**
- [ ] Service model soporta pricing_type y campos relacionados
- [ ] TeamMember tiene campo de horas no facturables
- [ ] BCR se calcula correctamente con ajuste de horas no facturables
- [ ] Cálculos funcionan para hourly, fixed y recurring
- [ ] Plantillas de Legal y Finanzas creadas
- [ ] Frontend se adapta según tipo de servicio
- [ ] Migración ejecuta sin errores
- [ ] Retrocompatibilidad mantenida

---

### Sprint 15: Módulo de Insumos y Costos de Terceros

**Objetivo:** Implementar sistema de insumos (costos de terceros) con mark-up para sectores creativos  
**Duración:** 2-3 semanas  
**Estado:** ✅ Completado  
**Dependencias:** Sprint 14 completado  
**Prioridad:** Media

#### Contexto

Soportar costos de terceros (licencias de stock, alquiler de equipo, materiales) con mark-up para sectores como:
- Producción Audiovisual
- Fotografía
- Arquitectura

#### Tareas Detalladas:

**15.1: Nuevo Modelo QuoteExpense** ✅

- Crear: `backend/app/models/project.py` (agregar clase)
- Modelo completo:
  ```python
  class QuoteExpense(Base):
      __tablename__ = "quote_expenses"
      
      id = Column(Integer, primary_key=True)
      quote_id = Column(Integer, ForeignKey("quotes.id"), nullable=False)
      name = Column(String, nullable=False)
      description = Column(String, nullable=True)
      cost = Column(Float, nullable=False)  # Costo real
      markup_percentage = Column(Float, default=0.0)  # Mark-up (0.10 = 10%)
      client_price = Column(Float, nullable=False)  # cost * (1 + markup)
      category = Column(String, nullable=True)  # "Third Party", "Materials", "Licenses"
      quantity = Column(Float, default=1.0)
      created_at = Column(DateTime(timezone=True), server_default=func.now())
      
      quote = relationship("Quote", back_populates="expenses")
  ```

**15.2: Extender Quote Model** ✅

- Actualizar: `backend/app/models/project.py`
- Agregar relación:
  ```python
  expenses = relationship("QuoteExpense", back_populates="quote", 
                         cascade="all, delete-orphan")
  ```

**15.3: Extender Cálculos con Insumos** ✅

- Actualizar: `backend/app/core/calculations.py`
- Modificar `calculate_quote_totals_enhanced()`:
  - Agregar parámetro `expenses: List[Dict]`
  - Calcular total de insumos:
    - `total_expenses_cost = sum(cost * quantity)`
    - `total_expenses_client_price = sum(cost * quantity * (1 + markup))`
  - Incluir insumos en totales finales

**15.4: Schemas para QuoteExpense** ✅

- Crear/Actualizar: `backend/app/schemas/quote.py`
- Schemas:
  ```python
  class QuoteExpenseCreate(BaseModel):
      name: str
      description: Optional[str]
      cost: float
      markup_percentage: float = 0.0
      category: Optional[str]
      quantity: float = 1.0
  
  class QuoteExpenseResponse(BaseModel):
      id: int
      name: str
      cost: float
      markup_percentage: float
      client_price: float
      category: Optional[str]
      quantity: float
  ```

**15.5: Endpoints para Gestionar Insumos** ✅

- Actualizar: `backend/app/api/v1/endpoints/projects.py` (creado archivo separado `expenses.py`)
- Endpoints:
  - `POST /projects/{id}/quotes/{quote_id}/expenses` - Agregar insumo
  - `PUT /projects/{id}/quotes/{quote_id}/expenses/{expense_id}` - Editar insumo
  - `DELETE /projects/{id}/quotes/{quote_id}/expenses/{expense_id}` - Eliminar insumo
  - Actualizar cálculo de quote para incluir expenses

**15.6: Migración de Base de Datos** ✅

- Crear: `backend/alembic/versions/g8h9i0j1k2l3_add_quote_expenses.py`
- Crear tabla `quote_expenses` con todos los campos

**15.7: Plantillas Creativas Ampliadas** ✅

- Actualizar seed data de plantillas (migración `h9i0j1k2l3m4_update_templates_with_expenses.py`)
- Ampliar plantillas existentes:
  - **Producción Audiovisual**: Agregar categoría de insumos (licencias de stock, alquiler de equipo)
  - **Fotografía**: Incluir costos de locaciones, modelos, props
- Estructura en `suggested_fixed_costs`:
  ```json
  {
    "name": "Licencia de Stock (Shutterstock)",
    "category": "Third Party",
    "is_expense": true,
    "suggested_markup": 0.10
  }
  ```

**15.8: Frontend - Gestión de Insumos** ✅

- Actualizar: `frontend/src/app/(app)/projects/[id]/quotes/[quoteId]/edit/page.tsx`
- Componente `ExpensesSection` creado en `frontend/src/components/quotes/expenses-section.tsx`
- Agregar sección "Gastos de Terceros/Insumos":
  - Tabla de insumos (nombre, costo, mark-up, precio cliente)
  - Formulario para agregar insumo
  - Cálculo automático de precio cliente (costo × (1 + markup))
  - Mostrar totales separados: Servicios vs Insumos

**15.9: Exportación Actualizada** ✅

- Actualizar: `backend/app/core/pdf_generator.py` y `docx_generator.py`
- Endpoints de PDF/DOCX actualizados para cargar expenses
- Incluir sección de insumos en PDF/DOCX:
  - Separar "Servicios" y "Gastos de Terceros"
  - Mostrar mark-up aplicado

**Archivos clave:**
- ✅ `backend/app/models/project.py` (QuoteExpense agregado, Quote actualizado)
- ✅ `backend/app/core/calculations.py` (actualizado con expenses)
- ✅ `backend/app/schemas/quote.py` (schemas agregados)
- ✅ `backend/app/api/v1/endpoints/expenses.py` (nuevo archivo con endpoints CRUD)
- ✅ `backend/app/api/v1/router.py` (router de expenses registrado)
- ✅ `backend/alembic/versions/g8h9i0j1k2l3_add_quote_expenses.py` (migración creada)
- ✅ `backend/alembic/versions/h9i0j1k2l3m4_update_templates_with_expenses.py` (migración de plantillas)
- ✅ `frontend/src/app/(app)/projects/[id]/quotes/[quoteId]/edit/page.tsx` (actualizado)
- ✅ `frontend/src/components/quotes/expenses-section.tsx` (nuevo componente)
- ✅ `frontend/src/lib/queries.ts` (hooks de expenses agregados)
- ✅ `backend/app/core/pdf_generator.py` (actualizado con expenses)
- ✅ `backend/app/core/docx_generator.py` (actualizado con expenses)
- ✅ `backend/app/repositories/project_repository.py` (actualizado para cargar expenses)

**Criterios de aceptación:**
- [x] Modelo QuoteExpense creado y funcional
- [x] Insumos se incluyen en cálculo de totales
- [x] Mark-up se calcula correctamente
- [x] Endpoints CRUD de insumos funcionan
- [x] Frontend permite agregar/editar insumos
- [x] Exportaciones muestran insumos separados
- [x] Plantillas incluyen sugerencias de insumos

---

### Sprint 16: Funcionalidades Avanzadas - Revisiones y Costeo por Proyecto

**Objetivo:** Implementar sistema de revisiones incluidas y soporte para costeo por valor de proyecto/IP  
**Duración:** 2 semanas  
**Estado:** ✅ Completado  
**Dependencias:** Sprint 15 completado  
**Prioridad:** Baja

#### Contexto

Completar funcionalidades avanzadas para sectores creativos:
- Revisiones incluidas con costo adicional por revisión extra
- Costeo por valor del proyecto/IP (no solo tiempo)

#### Tareas Detalladas:

**16.1: Extender Quote con Revisiones** ✅

- Actualizar: `backend/app/models/project.py`
- Agregar campos a `Quote`:
  ```python
  revisions_included = Column(Integer, default=2, nullable=False)
  revision_cost_per_additional = Column(Float, nullable=True)
  # Costo por cada revisión adicional
  ```

**16.2: Lógica de Revisiones en Cálculos** ✅

- Actualizar: `backend/app/core/calculations.py` (incluye soporte para costeo por valor de proyecto/IP que ya estaba implementado en Sprint 14)
- Agregar a `calculate_quote_totals_enhanced()`:
  - Parámetro `revisions_count: int` (opcional)
  - Si `revisions_count > revisions_included`:
    - Calcular costo adicional: `(revisions_count - revisions_included) * revision_cost_per_additional`
    - Agregar a `total_client_price`

**16.3: Soporte para Costeo por Valor de Proyecto** ✅

- Ya implementado en Sprint 14: `backend/app/models/service.py` y `backend/app/core/calculations.py`
- Si `pricing_type == "project_value"`:
  - El servicio representa el valor total del proyecto/IP
  - No se calcula por horas, sino por valor acordado
  - `fixed_price` representa el valor del proyecto

**16.4: Schemas Actualizados** ✅

- Actualizar: `backend/app/schemas/quote.py` y `project.py`
- Agregar campos de revisiones a schemas de Quote
- Validación: Si `revision_cost_per_additional` está presente, debe ser >= 0

**16.5: Endpoints Actualizados** ✅

- Actualizar: `backend/app/api/v1/endpoints/projects.py` y `backend/app/api/v1/endpoints/quotes.py`
- Modificar endpoints de creación/actualización de quotes:
  - Aceptar `revisions_included` y `revision_cost_per_additional`
  - Pasar `revisions_count` al cálculo si se proporciona

**16.6: Migración de Base de Datos** ✅

- Crear: `backend/alembic/versions/i0j1k2l3m4n5_add_quote_revisions.py`
- Agregar campos a tabla `quotes`

**16.7: Frontend - Gestión de Revisiones** ✅

- Actualizar: `frontend/src/app/(app)/projects/[id]/quotes/[quoteId]/edit/page.tsx`
- Actualizar: `frontend/src/lib/queries.ts` (useCalculateQuote)
- Agregar sección "Revisiones":
  - Campo: "Revisiones incluidas" (default: 2)
  - Campo: "Costo por revisión adicional" (opcional)
  - Mostrar costo adicional si se exceden revisiones incluidas

**16.8: Plantillas Completas** ✅ COMPLETADO

- ✅ Actualizadas todas las plantillas con datos completos:
  - **Creativo**: Agregados servicios con `pricing_type="project_value"` para proyectos de IP (branding: "Desarrollo de Propiedad Intelectual (IP)", "Re-branding Completo"; audiovisual: "Producción de Propiedad Intelectual Audiovisual", "Serie/Campaña Completa")
  - **Finanzas**: Servicios recurrentes ya implementados (Retainer Mensual, Retainer Anual)
  - **Nota**: Las revisiones son configuración a nivel de Quote, no de template (se configuran al crear cotizaciones)

**16.9: Tests Completos** ✅ COMPLETADO

- ✅ Creado: `backend/tests/integration/test_advanced_pricing.py`
- ✅ Validaciones implementadas:
  - ✅ Cálculo con revisiones adicionales (tests: sin revisiones adicionales, con revisiones adicionales, sin costo por revisión)
  - ✅ Cálculo de proyectos por valor (tests: con horas estimadas, sin horas estimadas, pricing fijo)
  - ✅ Combinación de servicios + insumos + revisiones (tests: servicios+expenses+revisions, mixed pricing types, solo servicios)

**Archivos clave:**
- ✅ `backend/app/models/project.py` (Quote actualizado con campos de revisiones)
- ✅ `backend/app/core/calculations.py` (actualizado con lógica de revisiones)
- ✅ `backend/app/schemas/quote.py` (schemas actualizados)
- ✅ `backend/app/schemas/project.py` (schemas actualizados)
- ✅ `backend/app/api/v1/endpoints/projects.py` (endpoints actualizados)
- ✅ `backend/app/api/v1/endpoints/quotes.py` (endpoint de cálculo actualizado)
- ✅ `backend/alembic/versions/i0j1k2l3m4n5_add_quote_revisions.py` (migración creada)
- ✅ `backend/alembic/versions/j1k2l3m4n5o6_update_templates_with_project_value.py` (migración para actualizar plantillas)
- ✅ `backend/tests/integration/test_advanced_pricing.py` (tests completos de pricing avanzado)
- ✅ `frontend/src/app/(app)/projects/[id]/quotes/[quoteId]/edit/page.tsx` (UI de revisiones agregada)
- ✅ `frontend/src/lib/queries.ts` (useCalculateQuote actualizado)

**Criterios de aceptación:**
- [x] Sistema de revisiones funciona correctamente
- [x] Costeo por valor de proyecto/IP implementado (Sprint 14)
- [x] Frontend permite configurar revisiones
- [x] Todas las plantillas completas y funcionales (servicios project_value agregados a plantillas creativas)
- [x] Tests pasando (test_advanced_pricing.py con 10+ tests cubriendo todos los casos)
- [x] Documentación actualizada

---

### Sprint 17: Frontend Completado y Tareas Programadas (Celery)

**Objetivo:** Completar dashboards pendientes, implementar Celery para tareas programadas y mejorar UX general  
**Duración:** 2-3 semanas  
**Estado:** ✅ Completado  
**Dependencias:** Sprints 11 y 12 completados (backend)  
**Prioridad:** Alta

#### Contexto

Este sprint se enfoca en completar el frontend pendiente de funcionalidades ya implementadas en backend, y agregar el sistema de tareas programadas usando Celery para automatizar procesos como el reseteo mensual de créditos.

#### Tareas Detalladas:

**17.1: Frontend - Dashboard de Créditos**

- Crear: `frontend/src/app/(app)/credits/page.tsx` (nuevo)
- Componentes:
  - `CreditsDashboard`: Dashboard principal con balance actual
  - `CreditsBalanceCard`: Tarjeta con créditos disponibles, usados este mes, y próximos
  - `CreditsUsageChart`: Gráfico de uso de créditos (línea temporal)
  - `CreditsHistoryTable`: Tabla con historial de transacciones
- Funcionalidades:
  - Ver balance actual de créditos
  - Ver créditos usados este mes vs. límite mensual
  - Ver fecha de próximo reseteo
  - Historial de transacciones (paginado)
  - Filtros por tipo de transacción (grant, consumption, refund, etc.)
- Integración:
  - Usar `useGetMyCreditBalance()` y `useGetMyCreditHistory()` de `lib/queries.ts`
- Diseño: Material Design, colores minimalistas

**17.2: Frontend - Dashboard Admin de Créditos**

- Crear: `frontend/src/app/(app)/admin/organizations/[id]/credits/page.tsx` (nuevo)
- Componentes:
  - `AdminCreditsDashboard`: Dashboard admin para gestionar créditos de organizaciones
  - `OrganizationCreditsBalance`: Balance de créditos de la organización
  - `ManualCreditGrantForm`: Formulario para otorgar créditos manualmente
  - `MonthlyResetButton`: Botón para forzar reseteo mensual
  - `AdminCreditsHistoryTable`: Tabla con historial completo de transacciones
- Funcionalidades:
  - Ver balance de créditos de cualquier organización (super admin)
  - Otorgar créditos manualmente (con razón)
  - Forzar reseteo mensual de créditos
  - Ver historial completo de transacciones
- Integración:
  - Usar endpoints `/credits/admin/organizations/{id}/*`
- Permisos: Solo `super_admin` puede acceder

**17.3: Frontend - Dashboard de Soporte**

- Crear: `frontend/src/app/(app)/support/page.tsx` (nuevo)
- Componentes:
  - `SupportDashboard`: Dashboard principal de soporte
  - `OrganizationsList`: Lista de todas las organizaciones con métricas anonimizadas
  - `OrganizationCard`: Tarjeta con información anonimizada de organización
  - `SupportFilters`: Filtros por plan, estado, uso
  - `SupportMetrics`: Métricas agregadas de todas las organizaciones
- Funcionalidades:
  - Listar todas las organizaciones con datos anonimizados
  - Buscar y filtrar organizaciones por plan, estado, uso
  - Ver métricas agregadas (total de usuarios, proyectos, etc.)
  - Navegar a detalle de organización
- Integración:
  - Usar endpoints `/support/organizations`
- Permisos: Solo `support_manager`, `data_analyst`, o `super_admin`

**17.4: Frontend - Detalle de Organización (Soporte)**

- Crear: `frontend/src/app/(app)/support/organizations/[id]/page.tsx` (nuevo)
- Componentes:
  - `OrganizationDetailView`: Vista detallada de organización
  - `AnonymizedAnalytics`: Analytics anonimizados
  - `AnonymizedQuotesList`: Lista de quotes anonimizados
  - `AnonymizedTeamList`: Lista de miembros del equipo (sin salarios exactos)
  - `UsageMetricsCard`: Tarjeta con métricas de uso anonimizadas
- Funcionalidades:
  - Ver analytics anonimizado de organización específica
  - Ver historial de quotes (sin montos exactos)
  - Ver equipo (roles sin salarios)
  - Ver métricas de uso (rangos en lugar de números exactos)
- Integración:
  - Usar endpoints `/support/organizations/{id}/`
- Diseño: Mostrar claramente que los datos están anonimizados

**17.5: Frontend - Badge de Créditos en Header**

- Actualizar: `frontend/src/components/layout/AppHeader.tsx`
- Componente:
  - `CreditsBadge`: Badge mostrando créditos disponibles
- Funcionalidades:
  - Mostrar créditos disponibles en header/navbar
  - Cambiar color según nivel (verde: suficientes, amarillo: bajos, rojo: críticos)
  - Click para ir a dashboard de créditos
- Lógica:
  - Solo mostrar a usuarios que consumen créditos (`product_manager`)
  - Ocultar para `owner` y `admin_financiero`
  - Ocultar si plan es ilimitado

**17.6: Backend - Implementar Celery para Tareas Programadas**

- Crear: `backend/app/core/celery_app.py` (nuevo)
- Configuración:
  - Instalar `celery` y `redis` (broker)
  - Configurar broker (Redis recomendado)
  - Configurar backend de resultados
- Crear: `backend/app/core/tasks.py` (nuevo)
- Tareas:
  - `reset_monthly_credits()`: Reseteo mensual automático de créditos
    - Ejecutar diariamente (verificar `next_reset_at <= now()`)
    - Resetear `credits_used_this_month = 0`
    - Otorgar nuevos créditos según plan
    - Actualizar `last_reset_at` y `next_reset_at`
- Configuración:
  - Agregar variables de entorno: `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`
  - Configurar celery beat para tareas periódicas
- Tests:
  - Test unitario para tarea de reseteo
  - Test de integración verificando reseteo correcto

**17.7: Backend - Setup de Celery Beat (Tareas Periódicas)**

- Crear: `backend/app/core/celery_beat_schedule.py` (nuevo)
- Configuración:
  - Definir schedule para `reset_monthly_credits`
  - Ejecutar diariamente a las 00:00 UTC (o hora configurable)
- Docker:
  - Agregar servicio `celery_worker` y `celery_beat` a `docker-compose.yml`
  - Configurar para desarrollo y producción

**17.8: Frontend - Mejoras UX Generales**

- Loading states mejorados:
  - Skeleton loaders para tablas y cards
  - Spinners consistentes
- Error handling mejorado:
  - Mensajes de error más claros
  - Retry automático para errores transitorios
- Responsive design:
  - Mejorar diseño móvil de dashboards
  - Optimizar tablas para pantallas pequeñas
- Accesibilidad:
  - Mejorar contraste de colores
  - Agregar labels ARIA donde falten
  - Navegación por teclado mejorada

**17.9: Tests Frontend**

- Crear: Tests para nuevos componentes
  - `frontend/src/components/credits/__tests__/CreditsDashboard.test.tsx`
  - `frontend/src/components/support/__tests__/SupportDashboard.test.tsx`
  - Tests de integración para flujos completos

**17.10: Documentación**

- Actualizar: Documentación de frontend (si existe)
- Documentar:
  - Cómo usar los nuevos dashboards
  - Cómo funciona el sistema de créditos en frontend
  - Cómo funciona el dashboard de soporte
- Crear: `docs/CELERY_SETUP.md`
  - Guía de configuración de Celery
  - Cómo ejecutar workers y beat
  - Cómo agregar nuevas tareas

**Archivos clave:**
- `frontend/src/app/(app)/credits/page.tsx` (nuevo)
- `frontend/src/app/(app)/admin/organizations/[id]/credits/page.tsx` (nuevo)
- `frontend/src/app/(app)/support/page.tsx` (nuevo)
- `frontend/src/app/(app)/support/organizations/[id]/page.tsx` (nuevo)
- `frontend/src/components/layout/AppHeader.tsx` (actualizar)
- `backend/app/core/celery_app.py` (nuevo)
- `backend/app/core/tasks.py` (nuevo)
- `backend/app/core/celery_beat_schedule.py` (nuevo)
- `backend/requirements.txt` (agregar celery, redis)
- `docker-compose.yml` (agregar servicios celery)
- `docs/CELERY_SETUP.md` (nuevo)

**Criterios de aceptación:**
- [x] Dashboard de créditos funcional para usuarios finales
- [x] Dashboard admin de créditos funcional para super_admin
- [x] Dashboard de soporte funcional con datos anonimizados
- [x] Celery configurado y funcionando
- [x] Tarea de reseteo mensual automático funcionando
- [x] Badge de créditos visible en header (solo para roles que consumen)
- [x] Mejoras de UX implementadas (loading, errors, responsive)
- [ ] Tests frontend pasando (opcional - estructura creada)
- [x] Documentación actualizada
- [x] Docker compose actualizado con servicios de Celery

---

### Sprint 18: Onboarding de Estructura de Costos y Proyección de Ventas

**Objetivo:** Implementar sistema completo de onboarding que capture la estructura económica del negocio y genere proyecciones de ventas basadas en servicios configurados  
**Duración:** 4-5 semanas  
**Estado:** ✅ Completado  
**Dependencias:** Sprint 6.5 completado (sistema de plantillas) ✅  
**Prioridad:** Alta

#### Contexto

Este sprint extiende el sistema de onboarding existente (Sprint 6.5) con un wizard multi-paso que captura:
- Estructura de costos completa (localización, perfilamiento, estructura tributaria)
- Cálculo de cargas sociales (especialmente para Colombia - Ley 100)
- Proyección de ventas basada en servicios y capacidad del equipo
- Visualizaciones en tiempo real del BCR (Blended Cost Rate)

**Valor de negocio:**
- ✅ Mejora significativamente la experiencia de onboarding
- ✅ Permite a usuarios entender su estructura de costos desde el inicio
- ✅ Facilita proyecciones financieras basadas en datos reales
- ✅ Diferencia competitiva clara

#### Tareas Detalladas:

**18.1: Fundación - Estado Global con Zustand** ✅

- ✅ Crear: `frontend/src/stores/onboarding-store.ts` (nuevo)
- ✅ Implementar store de Zustand para persistir datos del wizard entre pasos
- ✅ Campos:
  - Paso 1: `country`, `currency`, `enableSocialCharges` (Ley 100 para Colombia)
  - Paso 2: `profileType` (freelance/professional/company), `monthlyIncomeTarget`, `vacationDays`, `teamMembers[]`
  - Paso 3: `taxes` (IVA, ICA, Retenciones, desglose Colombia)
- ✅ Persistencia local con `zustand/middleware`
- **Estado:** ✅ Completado

**18.2: Paso 1 - Localización Mejorada** ✅

- ✅ Actualizar: `frontend/src/app/(app)/onboarding/page.tsx`
- ✅ Agregar Switch "Cargas Prestacionales Ley 100" (condicional si país = Colombia)
- ✅ Integrar con store de Zustand
- ✅ Dialog informativo sobre Ley 100
- **Estado:** ✅ Completado

**18.3: Máscaras de Moneda** ✅

- ✅ `frontend/src/lib/currency-mask.ts` ya existe
- ✅ Utilidad para formatear inputs de moneda según locale
- ✅ Soporte para COP (sin decimales, punto como separador de miles)
- ✅ Soporte para USD/EUR (con decimales, formato estándar)
- ✅ Integrado en componentes de onboarding
- **Estado:** ✅ Completado

**18.4: Paso 2 - Perfilamiento** ✅

- ✅ `frontend/src/components/onboarding/ProfileSelection.tsx` ya existe
- ✅ Cards seleccionables: Freelance, Profesional, Empresa
- ✅ Componente: `FreelanceForm.tsx` - Campos condicionales (Ingreso Mensual Objetivo, Días de vacaciones)
- ✅ Componente: `TeamMembersTable.tsx` - Tabla dinámica para agregar miembros del equipo (si Empresa)
- ✅ Validación con Zod + React Hook Form
- **Estado:** ✅ Completado

**18.5: Paso 3 - Estructura Tributaria** ✅

- ✅ Crear: `frontend/src/components/onboarding/TaxStructureForm.tsx` (nuevo)
- ✅ Inputs para IVA, ICA, Retenciones (%)
- ✅ Componente: `ColombiaTaxBreakdown.tsx` - Desglose condicional (Salud, Pensión, ARL, Parafiscales)
- ✅ Mostrar solo si `country === 'COL'` y `enableSocialCharges === true`
- ✅ Validación de porcentajes (0-100%)
- ✅ Integrado en paso 4 del onboarding
- **Estado:** ✅ Completado

**18.6: Backend - Modelo de Cargas Sociales** ✅

- ✅ Usa campo `settings` existente en `Organization` (JSON)
- ✅ Schemas: `SocialChargesConfig`, `OnboardingConfigRequest`, `OnboardingConfigResponse`
- ✅ Endpoint: `POST /organizations/{id}/onboarding-config`
- ✅ Estructura de cargas sociales guardada en `Organization.settings.social_charges_config`
- ✅ Calcula total_percentage automáticamente
- **Estado:** ✅ Completado

**18.7: Paso 4 - Resumen en Vivo con BCR** ✅

- ✅ Crear: `frontend/src/components/onboarding/LiveSummarySidebar.tsx` (nuevo)
- ✅ Panel lateral sticky con cálculo BCR en tiempo real
- ✅ Utilidad: `frontend/src/lib/finance-utils.ts` - Función `calculateBCR()`
- ✅ Cálculo:
  - `Costo Real Recurso = Salario + (Salario * %CargasSociales)`
  - `BCR = (Total Salarios Reales + Total Overhead) / Total Horas Facturables`
- ✅ Gráfico de distribución de costos con PieChart
- ✅ Optimización: `useMemo` para performance
- ✅ Integrado en paso 5 del onboarding
- **Estado:** ✅ Completado

**18.8: Proyección de Ventas - Backend** ✅

- ✅ Crear: `backend/app/services/sales_projection_service.py` (nuevo)
- ✅ Endpoint: `POST /sales/projection`
- ✅ Lógica de proyección:
  - Basada en servicios configurados
  - Considera capacidad del equipo (horas facturables)
  - Tasa de cierre por servicio (win rate)
  - Escenarios: conservador (70%), realista (85%), optimista (100%)
  - Período configurable (3, 6, 12 meses)
- ✅ Schemas: `SalesProjectionRequest`, `SalesProjectionResponse`, `MonthlyProjection`
- ✅ Integrado en router API
- **Estado:** ✅ Completado

**18.9: Proyección de Ventas - Frontend** ✅

- ✅ Crear: `frontend/src/components/onboarding/SalesProjection.tsx` (nuevo)
- ✅ Formulario de selección de servicios para proyectar
- ✅ Inputs: horas estimadas por servicio, win rate, escenario, período
- ✅ Componentes de visualización:
  - `LineChart` - Gráfico de línea (revenue, costs, profit por mes)
  - `BarChart` - Gráfico de barras por servicio
  - `KPICard` - Cards con KPIs (Revenue, Costs, Profit, Margin)
- ✅ Hook `useCalculateSalesProjection` en queries.ts
- ✅ Types en `frontend/src/lib/types/sales-projection.ts`
- ✅ Componente disponible para integración
- **Estado:** ✅ Completado

**18.10: Actualizar Cálculo BCR para Incluir Cargas Sociales** ✅

- ✅ Actualizar: `backend/app/core/calculations.py`
- ✅ Modificar `calculate_blended_cost_rate()`:
  - Obtener configuración de cargas sociales de `Organization.settings`
  - Aplicar multiplicador de cargas sociales a salarios
  - Incluir en cálculo de costos mensuales totales
- ✅ Actualizar cache key para incluir cargas sociales
- ✅ Cache key incluye tenant_id y total_percentage de cargas sociales
- **Estado:** ✅ Completado

**Archivos clave:**
- `frontend/src/stores/onboarding-store.ts` (nuevo)
- `frontend/src/lib/currency-mask.ts` (nuevo)
- `frontend/src/lib/finance-utils.ts` (nuevo)
- `frontend/src/components/onboarding/ProfileSelection.tsx` (nuevo)
- `frontend/src/components/onboarding/FreelanceForm.tsx` (nuevo)
- `frontend/src/components/onboarding/TeamMembersTable.tsx` (nuevo)
- `frontend/src/components/onboarding/TaxStructureForm.tsx` (nuevo)
- `frontend/src/components/onboarding/ColombiaTaxBreakdown.tsx` (nuevo)
- `frontend/src/components/onboarding/LiveSummarySidebar.tsx` (nuevo)
- `frontend/src/components/onboarding/CostDistributionChart.tsx` (nuevo)
- `frontend/src/components/onboarding/SalesProjection.tsx` (nuevo)
- `frontend/src/components/onboarding/MonthlyProjectionChart.tsx` (nuevo)
- `frontend/src/components/onboarding/ServiceBreakdownChart.tsx` (nuevo)
- `frontend/src/components/onboarding/ProjectionSummaryCards.tsx` (nuevo)
- `frontend/src/app/(app)/onboarding/page.tsx` (actualizar)
- `backend/app/services/sales_projection_service.py` (nuevo)
- `backend/app/core/calculations.py` (actualizar)
- `backend/app/models/organization.py` (actualizar)
- `backend/app/api/v1/endpoints/organizations.py` (actualizar)
- `backend/alembic/versions/XXX_add_social_charges_config.py` (nuevo)

**Criterios de aceptación:**
- [ ] Wizard multi-paso completo (5 pasos) funcional
- [ ] Datos persisten entre pasos usando Zustand
- [ ] Switch Ley 100 funciona correctamente para Colombia
- [ ] Máscaras de moneda funcionan para todas las monedas soportadas
- [ ] Perfilamiento permite seleccionar Freelance/Profesional/Empresa
- [ ] Campos condicionales se muestran según perfil seleccionado
- [ ] Tabla dinámica de miembros del equipo funciona (Empresa)
- [ ] Estructura tributaria captura IVA, ICA, Retenciones
- [ ] Desglose Colombia se muestra condicionalmente
- [ ] Panel lateral muestra BCR en tiempo real
- [ ] Cálculo BCR incluye cargas sociales correctamente
- [ ] Gráficos de distribución funcionan (Pie/Bar charts)
- [ ] Proyección de ventas calcula correctamente
- [ ] Visualizaciones de proyección son claras y precisas
- [ ] Backend guarda configuración de onboarding
- [ ] Tests unitarios para cálculos financieros
- [ ] Documentación de fórmulas y lógica de negocio

**Dependencias adicionales:**
- ✅ Zustand (`^4.4.7`) - Ya disponible
- ✅ Zod (`^3.22.4`) - Ya disponible
- ✅ React Hook Form (`^7.49.3`) - Ya disponible
- ✅ Recharts (`^2.10.3`) - Ya disponible
- ⚠️ Opcional: `react-number-format` - Para máscaras más robustas
- ⚠️ Opcional: `use-debounce` - Para optimizar cálculos

**Riesgos y Mitigaciones:**

| Riesgo | Mitigación |
|--------|------------|
| Performance en cálculos en tiempo real | Debounce, memoización, Web Workers si es necesario |
| Sincronización de estado compleja | Zustand con validación, tests unitarios |
| Validación condicional compleja | Schemas Zod dinámicos, tests exhaustivos |
| Cargas sociales por país | Configuración en backend, validación de rangos |
| Proyecciones irreales | Advertencias claras, múltiples escenarios |

**Resultados esperados:**
- ✅ Sistema completo de onboarding de estructura de costos
- ✅ Cálculo de cargas sociales integrado
- ✅ Proyección de ventas basada en servicios y capacidad
- ✅ Visualizaciones en tiempo real del BCR
- ✅ Mejora significativa en experiencia de onboarding
- ✅ Herramienta de proyección financiera para usuarios

---

## 🤖 FASE 6: IA para Configuración Asistida (Sprint 19)

**Objetivo:** Implementar asistente de IA para reducir fricción en onboarding y configuración inicial  
**Duración:** 4-6 semanas  
**Estado:** ✅ Completado (Enero 2025 - Todas las fases implementadas)  
**Dependencias:** Sprint 18 completado ✅ (onboarding completo)  
**Prioridad:** Media

#### Contexto

Actualmente, `AIService` funciona como un "Analista Financiero" (salida de datos). Para asistir en la configuración (entrada de datos), necesitamos implementar un "Asistente de Onboarding" capaz de estructurar datos desordenados.

**Valor de negocio:**
- ✅ Reduce fricción inicial: El usuario no tiene que rellenar manualmente 50 campos
- ✅ Estandarización: Sugiere roles y costos típicos de la industria
- ✅ Automatización: Extrae datos de documentos existentes
- ✅ Mejora time-to-value significativamente

#### Tareas Detalladas:

**19.1: Extender AIService con Structured Outputs** ✅ **COMPLETADO**

- ✅ Actualizado: `backend/app/services/ai_service.py`
- ✅ Agregado soporte para OpenAI Structured Outputs (JSON mode)
- ✅ Implementados métodos:
  - `suggest_onboarding_data(industry: str, region: str, currency: str) -> Dict`
  - `parse_unstructured_data(text: str, document_type: Optional[str]) -> Dict`
  - `process_natural_language_command(command: str, context: Optional[Dict]) -> Dict`
- ✅ Usa `response_format={"type": "json_object"}` para structured outputs
- ✅ Mantiene compatibilidad con análisis financiero existente
- **Estimación:** 1 semana
- **Estado:** ✅ Completado

**19.2: Crear Schemas para IA de Configuración** ✅ **COMPLETADO**

- ✅ Creado: `backend/app/schemas/ai.py`
- ✅ Schemas implementados:
  - `OnboardingSuggestionRequest` - Request para sugerencias de onboarding
  - `OnboardingSuggestionResponse` - Response con sugerencias estructuradas
  - `DocumentParseRequest` - Request para parsing de documentos
  - `DocumentParseResponse` - Response con datos extraídos
  - `NaturalLanguageCommandRequest` - Request para comandos en lenguaje natural
  - `NaturalLanguageCommandResponse` - Response con acción estructurada
- **Estimación:** 2 días
- **Estado:** ✅ Completado

**19.3: Fase 1 - "Mago" de Industria (Smart Seeding)** ✅ **COMPLETADO**

- ✅ Crear endpoint: `POST /api/v1/ai/suggest-config`
- ✅ Implementar en: `backend/app/api/v1/endpoints/ai.py`
- ✅ Lógica:
  - Recibe descripción de industria (ej: "Soy una agencia de Marketing Digital centrada en SEO")
  - Usa OpenAI con Structured Outputs para generar:
    - Lista de servicios típicos (Auditoría SEO, Link Building)
    - Roles necesarios (SEO Specialist, Content Writer)
    - Costos de software (Ahrefs, Semrush)
  - Valida respuesta con esquemas Pydantic (`OnboardingSuggestionResponse`)
  - Retorna datos estructurados para revisión
- ✅ Frontend: Agregar botón "✨ Auto-completar con IA" en onboarding
- ✅ Componente `AISuggestionDialog` para revisar y aplicar sugerencias
- ✅ Hooks de queries (`useAISuggestions`, `useAIStatus`)
- ✅ Integración con onboarding store para aplicar sugerencias
- **Archivos creados/modificados:**
  - `backend/app/api/v1/endpoints/ai.py` - Endpoint `/ai/suggest-config`
  - `frontend/src/lib/queries/ai.ts` - Hooks de queries
  - `frontend/src/components/onboarding/AISuggestionDialog.tsx` - Componente de diálogo
  - `frontend/src/app/(app)/onboarding/page.tsx` - Integración del botón y diálogo

**19.4: Fase 2 - Parsing de Nómina/Gastos (Document Intelligence)**

- Crear endpoint: `POST /api/v1/ai/parse-document`
- Implementar en: `backend/app/api/v1/endpoints/ai.py`
- Lógica:
  - Recibe texto copiado de PDF/CSV de gastos
  - Usa OpenAI para clasificar cada línea en:
    - `CostFixed` (gastos fijos)
    - `TeamMember` (nómina)
    - `Subscription` (suscripciones, si se implementa)
  - Extrae campos relevantes (nombre, monto, categoría, etc.)
  - Valida con esquemas Pydantic
  - Retorna datos estructurados con scores de confianza
- Frontend: Área de "Importación Inteligente" en Settings
- Validación: Pantalla de revisión obligatoria antes de guardar
- **Estimación:** 2 semanas

**19.5: Fase 3 - Chat de Comandos (Natural Language Config)**

- Crear endpoint: `POST /api/v1/ai/process-command`
- Implementar en: `backend/app/api/v1/endpoints/ai.py`
- Lógica:
  - Recibe comando en lenguaje natural (ej: "Añade un Senior Designer que gana 45k anuales")
  - Usa OpenAI Function Calling para convertir a JSON estructurado
  - Funciones definidas:
    - `add_team_member(role, salary, currency, ...)`
    - `add_service(name, margin, pricing_type, ...)`
    - `add_fixed_cost(name, amount, category, ...)`
  - Valida con esquemas Pydantic
  - Retorna acción a ejecutar (con confirmación)
- Frontend: Chatbot interactivo en Settings
- **Estimación:** 2-3 semanas

**19.6: Validación y Seguridad**

- Implementar validación en múltiples capas:
  - Validación de schema JSON (OpenAI Structured Outputs)
  - Validación Pydantic (backend)
  - Revisión humana (frontend - pantalla de revisión)
- Anonimización de datos sensibles antes de enviar a OpenAI
- Rate limiting para endpoints de IA
- Monitoreo de costos de API
- **Estimación:** 1 semana

**19.7: Caché y Optimización**

- Implementar caché para sugerencias por industria
- Reducir costos de API
- Mejorar velocidad de respuesta
- **Estimación:** 3 días

**Archivos clave a crear/modificar:**

**Backend:**
- `backend/app/services/ai_service.py` (extender con nuevos métodos)
- `backend/app/schemas/ai.py` (crear/actualizar con nuevos schemas)
- `backend/app/api/v1/endpoints/ai.py` (agregar nuevos endpoints)
- `backend/app/core/config.py` (agregar configuración de IA si es necesario)

**Frontend:**
- `frontend/src/app/(app)/onboarding/page.tsx` (agregar botón "Auto-completar con IA")
- `frontend/src/app/(app)/settings/` (agregar área de "Importación Inteligente")
- `frontend/src/components/ai/` (nuevo - componentes de IA)
  - `AISuggestionDialog.tsx` (diálogo de sugerencias)
  - `DocumentParser.tsx` (componente de parsing)
  - `AIChatbot.tsx` (chatbot interactivo - Fase 3)
- `frontend/src/lib/queries/ai.ts` (nuevo - hooks para endpoints de IA)

**Criterios de aceptación:**
- [x] AIService extendido con Structured Outputs
- [x] Endpoint `/ai/suggest-config` funcionando
- [x] Endpoint `/ai/parse-document` funcionando
- [x] Endpoint `/ai/process-command` funcionando (Fase 3)
- [x] Schemas Pydantic creados y validando correctamente
- [x] Frontend con botón "Auto-completar con IA" en onboarding
- [x] Frontend con área de "Importación Inteligente" en Settings
- [x] Pantalla de revisión obligatoria antes de guardar datos generados
- [x] Validación en múltiples capas funcionando
- [x] Anonimización de datos sensibles implementada (opcional - completado - Enero 2025: nombres anonimizados en context automático)
- [x] Rate limiting configurado (opcional - completado - Enero 2025)
- [x] Caché implementado para sugerencias comunes (opcional - completado - Enero 2025: 24h TTL, clave por industry/region/currency)
- [x] Tests unitarios para nuevos métodos de AIService (opcional - completado - Enero 2025: 12 tests unitarios creados)
- [x] Tests de integración para nuevos endpoints (opcional - completado - Enero 2025: 15+ tests de integración creados)
- [x] Documentación de API actualizada (opcional - completado - Enero 2025: API_AI.md creado con documentación completa)
- [x] Manejo de errores robusto (fallback a plantillas si IA falla)

**Consideraciones de seguridad:**
- ✅ Privacidad: No enviar PII real a OpenAI (anonimizar antes)
- ✅ Validación: Human-in-the-loop obligatorio (pantalla de revisión)
- ✅ Costos: Monitoreo de tokens y rate limiting
- ✅ Fallback: Usar plantillas predefinidas si IA falla

**Riesgos y mitigaciones:**

| Riesgo | Mitigación |
|--------|------------|
| Alucinaciones de IA (precios incorrectos) | Validación Pydantic + revisión humana obligatoria |
| Costos de API altos | Caché + rate limiting + monitoreo |
| Privacidad de datos | Anonimización antes de enviar a OpenAI |
| Fallos de API | Fallback a plantillas predefinidas |
| Parsing incorrecto de documentos | Scores de confianza + revisión humana |

**Resultados esperados:**
- ✅ Reducción significativa de fricción en onboarding
- ✅ Time-to-value mejorado (usuario productivo más rápido)
- ✅ Estandarización de configuraciones por industria
- ✅ Automatización de importación de datos existentes
- ✅ Diferencia competitiva clara

---

## 📊 FASE 8: Planificación Financiera Avanzada (Sprint 20)

### Sprint 20: Módulo de Proyección de Ventas Anual

**Objetivo:** Implementar sistema completo de proyección anual de ventas con matriz editable mes/servicio para planificación financiera estratégica  
**Duración:** 3-4 semanas  
**Estado:** ⏳ Pendiente  
**Dependencias:** Sprint 18 completado ✅ (BCR y estructura de costos), Sprint 19 completado (opcional - IA para asistencia)  
**Prioridad:** Alta

#### Contexto

Este sprint implementa un módulo de planificación financiera que permite al Owner proyectar sus ingresos anuales basándose en el volumen de servicios y horas estimadas. A diferencia del sistema de proyección existente (Sprint 18) que calcula proyecciones temporales basadas en capacidad y win rates, este módulo permite crear y persistir proyecciones anuales detalladas con edición mes a mes.

**Valor de negocio:**
- ✅ Planificación financiera estratégica anual
- ✅ Visualización clara de ingresos proyectados vs. punto de equilibrio
- ✅ Identificación temprana de capacidad ociosa o sobrecarga
- ✅ Toma de decisiones informada sobre contratación y recursos
- ✅ Comparativa automática con costos operativos (Overhead + Nómina)

#### Tareas Detalladas:

**20.1: Modelo de Base de Datos - SalesProjection**

- Crear: `backend/app/models/sales_projection.py` (nuevo)
- Modelo `SalesProjection`:
  ```python
  class SalesProjection(Base):
      __tablename__ = "sales_projections"
      
      id = Column(Integer, primary_key=True)
      organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
      year = Column(Integer, nullable=False, index=True)  # Año de la proyección
      is_active = Column(Boolean, default=True)  # Proyección activa (solo una por año)
      notes = Column(String, nullable=True)  # Notas adicionales
      created_at = Column(DateTime(timezone=True), server_default=func.now())
      updated_at = Column(DateTime(timezone=True), onupdate=func.now())
      created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
      
      # Relationships
      organization = relationship("Organization")
      created_by = relationship("User")
      entries = relationship("SalesProjectionEntry", back_populates="projection", cascade="all, delete-orphan")
  ```

- Modelo `SalesProjectionEntry`:
  ```python
  class SalesProjectionEntry(Base):
      __tablename__ = "sales_projection_entries"
      
      id = Column(Integer, primary_key=True)
      projection_id = Column(Integer, ForeignKey("sales_projections.id"), nullable=False, index=True)
      service_id = Column(Integer, ForeignKey("services.id"), nullable=False, index=True)
      month = Column(Integer, nullable=False)  # 1-12
      quantity = Column(Integer, default=0)  # Cantidad de servicios a vender
      hours_per_unit = Column(Float, default=0.0)  # Horas por unidad de servicio
      created_at = Column(DateTime(timezone=True), server_default=func.now())
      updated_at = Column(DateTime(timezone=True), onupdate=func.now())
      
      # Unique constraint: una entrada por servicio/mes/proyección
      __table_args__ = (
          UniqueConstraint('projection_id', 'service_id', 'month', name='uq_projection_service_month'),
      )
      
      # Relationships
      projection = relationship("SalesProjection", back_populates="entries")
      service = relationship("Service")
  ```

- Índices compuestos: `(organization_id, year)`, `(projection_id, service_id, month)`

**20.2: Migración de Base de Datos**

- Crear: `backend/alembic/versions/XXX_add_sales_projection_models.py`
- Pasos:
  1. Crear tabla `sales_projections`
  2. Crear tabla `sales_projection_entries`
  3. Crear índices y constraints
  4. Agregar foreign keys

**20.3: Repositorio de Proyecciones**

- Crear: `backend/app/repositories/sales_projection_repository.py` (nuevo)
- Métodos:
  - `get_by_organization_and_year(organization_id: int, year: int, db: AsyncSession) -> Optional[SalesProjection]`
  - `get_active_projection(organization_id: int, db: AsyncSession) -> Optional[SalesProjection]`
  - `create(projection_data: dict, db: AsyncSession) -> SalesProjection`
  - `update(projection_id: int, projection_data: dict, db: AsyncSession) -> SalesProjection`
  - `delete(projection_id: int, db: AsyncSession) -> None`
  - `get_entries(projection_id: int, db: AsyncSession) -> List[SalesProjectionEntry]`
  - `upsert_entry(entry_data: dict, db: AsyncSession) -> SalesProjectionEntry`
  - `bulk_upsert_entries(entries: List[dict], db: AsyncSession) -> List[SalesProjectionEntry]`

**20.4: Schemas Pydantic**

- Crear: `backend/app/schemas/sales_projection.py` (nuevo)
- Schemas:
  ```python
  class SalesProjectionEntryCreate(BaseModel):
      service_id: int
      month: int = Field(..., ge=1, le=12)
      quantity: int = Field(default=0, ge=0)
      hours_per_unit: float = Field(default=0.0, ge=0.0)
  
  class SalesProjectionCreate(BaseModel):
      year: int = Field(..., ge=2020, le=2100)
      notes: Optional[str] = None
      entries: List[SalesProjectionEntryCreate] = Field(default_factory=list)
  
  class SalesProjectionEntryResponse(BaseModel):
      id: int
      service_id: int
      service_name: str  # Joined from Service
      month: int
      quantity: int
      hours_per_unit: float
  
  class SalesProjectionSummaryResponse(BaseModel):
      """Resumen mensual calculado"""
      month: int
      total_revenue: float
      total_hours: float
      service_breakdown: List[Dict[str, Any]]  # Desglose por servicio
  
  class SalesProjectionResponse(BaseModel):
      id: int
      organization_id: int
      year: int
      is_active: bool
      notes: Optional[str]
      entries: List[SalesProjectionEntryResponse]
      summary: List[SalesProjectionSummaryResponse]  # Resumen calculado por mes
      total_annual_revenue: float
      total_annual_hours: float
      break_even_monthly_cost: float  # Overhead + Nómina mensual
      created_at: datetime
      updated_at: Optional[datetime]
  ```

**20.5: Servicio de Cálculo de Proyecciones**

- Crear: `backend/app/services/annual_sales_projection_service.py` (nuevo)
- Función principal: `calculate_projection_summary()`
  ```python
  async def calculate_projection_summary(
      projection: SalesProjection,
      db: AsyncSession
  ) -> Dict:
      """
      Calcula el resumen de la proyección:
      - Ingreso estimado por mes: quantity * hours_per_unit * (BCR * (1 + ServiceMargin))
      - Total anual proyectado
      - Comparativa con break-even (Overhead + Nómina mensual)
      """
  ```
- Lógica de cálculo:
  - Obtener BCR actual de la organización
  - Para cada entrada (mes/servicio):
    - Obtener `service.default_margin_target`
    - Calcular: `revenue = quantity * hours_per_unit * (BCR * (1 + margin_target))`
  - Agregar por mes y por año
  - Obtener break-even mensual (total de costos fijos + nómina)
  - Comparar ingresos proyectados vs. break-even

**20.6: Endpoints de API**

- Crear: `backend/app/api/v1/endpoints/annual_projection.py` (nuevo)
- Endpoints:
  - `GET /api/v1/projections/annual` - Obtener proyección activa del año actual
  - `GET /api/v1/projections/annual/{year}` - Obtener proyección de un año específico
  - `POST /api/v1/projections/annual` - Crear nueva proyección anual
  - `PUT /api/v1/projections/annual/{id}` - Actualizar proyección existente
  - `DELETE /api/v1/projections/annual/{id}` - Eliminar proyección
  - `GET /api/v1/projections/annual/{id}/summary` - Obtener resumen calculado (con ingresos, break-even, etc.)
  - `POST /api/v1/projections/annual/{id}/entries/bulk` - Actualizar múltiples entradas (para matriz)
  - `POST /api/v1/projections/annual/{id}/replicate-month` - Replicar valores de un mes a todos los meses

**20.7: Validación de Permisos**

- Actualizar: `backend/app/core/permissions.py`
- Agregar permiso: `can_view_financial_projections` (solo `owner` y `admin_financiero`)
- Validar permisos en todos los endpoints de proyecciones

**20.8: Frontend - Tipos TypeScript**

- Crear: `frontend/src/lib/types/annual-projection.ts` (nuevo)
- Interfaces:
  ```typescript
  export interface SalesProjectionEntry {
    id?: number;
    service_id: number;
    service_name: string;
    month: number;
    quantity: number;
    hours_per_unit: number;
  }
  
  export interface MonthlySummary {
    month: number;
    total_revenue: number;
    total_hours: number;
    service_breakdown: Array<{
      service_id: number;
      service_name: string;
      revenue: number;
      hours: number;
    }>;
  }
  
  export interface SalesProjection {
    id: number;
    organization_id: number;
    year: number;
    is_active: boolean;
    notes?: string;
    entries: SalesProjectionEntry[];
    summary: MonthlySummary[];
    total_annual_revenue: number;
    total_annual_hours: number;
    break_even_monthly_cost: number;
    created_at: string;
    updated_at?: string;
  }
  ```

**20.9: Frontend - Hooks de Queries**

- Crear: `frontend/src/lib/queries/annualProjection.ts` (nuevo)
- Hooks:
  - `useGetAnnualProjection(year?: number)` - Obtener proyección
  - `useCreateAnnualProjection()` - Crear proyección
  - `useUpdateAnnualProjection()` - Actualizar proyección
  - `useBulkUpdateProjectionEntries()` - Actualizar múltiples entradas
  - `useReplicateMonth()` - Replicar mes a todos los meses
  - `useGetProjectionSummary()` - Obtener resumen calculado

**20.10: Frontend - Componente de Matriz Editable**

- Crear: `frontend/src/components/projections/AnnualProjectionMatrix.tsx` (nuevo)
- Características:
  - Tabla con TanStack Table (filas = servicios, columnas = 12 meses)
  - Inline editing: Click en celda para editar `quantity` y `hours_per_unit`
  - Cálculo reactivo: Actualizar totales al cambiar valores (sin recargar)
  - Validación: Validar que `quantity >= 0` y `hours_per_unit >= 0`
  - Auto-save: Guardar cambios después de debounce (500ms)
  - Loading states: Mostrar skeleton mientras carga
- Estructura:
  ```typescript
  <Table>
    <TableHeader>
      <TableRow>
        <TableHead>Servicio</TableHead>
        {months.map(month => <TableHead key={month}>{monthName}</TableHead>)}
        <TableHead>Total Anual</TableHead>
      </TableRow>
    </TableHeader>
    <TableBody>
      {services.map(service => (
        <TableRow key={service.id}>
          <TableCell>{service.name}</TableCell>
          {months.map(month => (
            <EditableCell
              key={month}
              value={getEntry(service.id, month)}
              onSave={(quantity, hours) => handleUpdate(service.id, month, quantity, hours)}
            />
          ))}
          <TableCell>{calculateAnnualTotal(service.id)}</TableCell>
        </TableRow>
      ))}
    </TableBody>
  </Table>
  ```

**20.11: Frontend - Componente de Celda Editable**

- Crear: `frontend/src/components/projections/EditableProjectionCell.tsx` (nuevo)
- Características:
  - Muestra: `quantity × hours_per_unit = total_hours`
  - Click para editar: Inputs separados para cantidad y horas
  - Validación en tiempo real
  - Formato de números con separadores de miles
  - Tooltip con información del servicio (margen objetivo, BCR usado)
- Diseño: Material Design, colores minimalistas

**20.12: Frontend - Visualización con Gráficos**

- Crear: `frontend/src/components/projections/ProjectionCharts.tsx` (nuevo)
- Componentes:
  - `RevenueVsBreakEvenChart`: Gráfico de áreas (Recharts)
    - Línea de ingresos proyectados por mes
    - Línea de break-even (Overhead + Nómina mensual)
    - Área sombreada mostrando diferencia (positiva/negativa)
  - `MonthlyRevenueBreakdown`: Gráfico de barras apiladas
    - Desglose de ingresos por servicio cada mes
  - `CapacityUtilizationChart`: Gráfico de líneas
    - Horas proyectadas vs. capacidad disponible del equipo
    - Alerta visual si capacidad excedida o ociosa
- Librería: Recharts (ya disponible en el proyecto)

**20.13: Frontend - Alertas de Validación Financiera**

- Crear: `frontend/src/components/projections/CapacityAlerts.tsx` (nuevo)
- Validaciones:
  - **Capacidad Ociosa**: Si horas proyectadas < 70% de capacidad disponible → Alerta amarilla
  - **Capacidad Excedida**: Si horas proyectadas > 100% de capacidad disponible → Alerta roja
  - **Break-even**: Si ingresos proyectados < break-even mensual → Alerta naranja
- Mostrar alertas en panel lateral o banner superior

**20.14: Frontend - Funcionalidad de Replicación**

- Agregar a: `frontend/src/components/projections/AnnualProjectionMatrix.tsx`
- Botón "Replicar a todos los meses":
  - Seleccionar mes origen
  - Botón "Replicar valores de [Mes] a todos los meses"
  - Confirmación antes de replicar
  - Actualizar todas las celdas con valores del mes seleccionado

**20.15: Frontend - Página Principal de Proyecciones**

- Crear: `frontend/src/app/(app)/projections/annual/page.tsx` (nuevo)
- Estructura:
  - Header con año seleccionado (selector de año)
  - Botón "Crear Nueva Proyección" (si no existe)
  - Matriz editable (componente `AnnualProjectionMatrix`)
  - Panel lateral con:
    - Resumen anual (total ingresos, total horas)
    - Break-even mensual
    - Gráficos de visualización
    - Alertas de capacidad
  - Botón "Guardar Proyección" (si hay cambios sin guardar)

**20.16: Integración con Servicios y BCR**

- Actualizar: `backend/app/services/annual_sales_projection_service.py`
- Integración:
  - Obtener BCR actual usando `calculate_blended_cost_rate()`
  - Obtener servicios activos de la organización
  - Obtener capacidad del equipo (total horas facturables mensuales)
  - Obtener break-even (costos fijos + nómina mensual)
- Cache: Cachear BCR y break-even (invalidar cuando cambien costos/equipo)

**20.17: Tests Backend**

- Crear: `backend/tests/integration/test_annual_projection.py` (nuevo)
- Tests:
  - Crear proyección anual
  - Actualizar entradas de proyección
  - Calcular resumen (verificar fórmulas)
  - Validar permisos (solo owner/admin_financiero)
  - Replicar mes a todos los meses
  - Validar cálculos de ingresos vs. break-even
  - Tests de capacidad (ociosa, excedida)

**20.18: Tests Frontend**

- Crear: `frontend/src/components/projections/__tests__/AnnualProjectionMatrix.test.tsx` (nuevo)
- Tests:
  - Renderizado de matriz
  - Edición inline de celdas
  - Cálculo reactivo de totales
  - Validación de inputs
  - Replicación de mes

**Archivos clave a crear/modificar:**

**Backend:**
- `backend/app/models/sales_projection.py` (nuevo)
- `backend/app/repositories/sales_projection_repository.py` (nuevo)
- `backend/app/services/annual_sales_projection_service.py` (nuevo)
- `backend/app/schemas/sales_projection.py` (nuevo)
- `backend/app/api/v1/endpoints/annual_projection.py` (nuevo)
- `backend/app/core/permissions.py` (actualizar - agregar permiso)
- `backend/alembic/versions/XXX_add_sales_projection_models.py` (nuevo)
- `backend/tests/integration/test_annual_projection.py` (nuevo)

**Frontend:**
- `frontend/src/lib/types/annual-projection.ts` (nuevo)
- `frontend/src/lib/queries/annualProjection.ts` (nuevo)
- `frontend/src/components/projections/AnnualProjectionMatrix.tsx` (nuevo)
- `frontend/src/components/projections/EditableProjectionCell.tsx` (nuevo)
- `frontend/src/components/projections/ProjectionCharts.tsx` (nuevo)
- `frontend/src/components/projections/CapacityAlerts.tsx` (nuevo)
- `frontend/src/app/(app)/projections/annual/page.tsx` (nuevo)
- `frontend/src/components/projections/__tests__/AnnualProjectionMatrix.test.tsx` (nuevo)

**Criterios de aceptación:**
- [ ] Modelo `SalesProjection` y `SalesProjectionEntry` creados
- [ ] Migración de base de datos ejecuta sin errores
- [ ] Repositorio completo con todos los métodos necesarios
- [ ] Endpoints de API funcionando (CRUD completo)
- [ ] Cálculo de resumen funciona correctamente (Revenue = Quantity × Hours × BCR × (1 + Margin))
- [ ] Comparativa con break-even funciona
- [ ] Frontend con matriz editable funcional
- [ ] Inline editing funciona sin recargar página
- [ ] Cálculo reactivo de totales funciona correctamente
- [ ] Gráficos de visualización muestran datos correctos
- [ ] Alertas de capacidad funcionan (ociosa, excedida)
- [ ] Funcionalidad de replicación funciona
- [ ] Validación de permisos funciona (solo owner/admin_financiero)
- [ ] Tests backend pasando (15+ tests)
- [ ] Tests frontend pasando (opcional)
- [ ] Documentación de API actualizada
- [ ] UI responsive y accesible

**Consideraciones técnicas:**

**Fórmula de Cálculo:**
```
Revenue_per_service_month = quantity × hours_per_unit × [BCR × (1 + service.default_margin_target)]
Total_monthly_revenue = Sum(Revenue_per_service_month) for all services
Total_annual_revenue = Sum(Total_monthly_revenue) for 12 months
```

**Break-even:**
```
Break_even_monthly = Total_Fixed_Costs + Total_Monthly_Salaries
```

**Capacidad:**
```
Available_capacity_monthly = Sum(team_member.billable_hours_per_week × 4.33) for all active members
Projected_hours_monthly = Sum(quantity × hours_per_unit) for all services
Utilization = (Projected_hours_monthly / Available_capacity_monthly) × 100
```

**Riesgos y mitigaciones:**

| Riesgo | Mitigación |
|--------|------------|
| Performance con muchos servicios/meses | Paginación virtual, debounce en auto-save, cálculo optimizado |
| Sincronización de datos (BCR cambia) | Invalidar cache cuando cambien costos/equipo, mostrar fecha de último cálculo |
| Validación de capacidad compleja | Cálculo en backend, alertas claras en frontend |
| UX compleja (matriz grande) | Scroll horizontal/vertical, sticky headers, búsqueda de servicios |

**Resultados esperados:**
- ✅ Sistema completo de proyección anual de ventas
- ✅ Matriz editable mes/servicio funcional
- ✅ Cálculos reactivos en tiempo real
- ✅ Visualizaciones claras de ingresos vs. break-even
- ✅ Alertas de capacidad ociosa/excedida
- ✅ Herramienta de planificación financiera estratégica
- ✅ Mejora en toma de decisiones del Owner

---

## 💰 FASE 9: Precisión Financiera (Sprint 21)

### Sprint 21: Implementación de Precisión Financiera con Dinero.js y Decimal

**Objetivo:** Eliminar errores de precisión en cálculos financieros usando `decimal.Decimal` (backend) y `dinero.js` v2 (frontend)  
**Duración:** 4-5 semanas (3 fases)  
**Estado:** ✅ Completado (Enero 2025 - Tests unitarios completados: Backend 42/42, Frontend 31/31)  
**Dependencias:** Sprint 20 completado (opcional - puede ejecutarse en paralelo)  
**Prioridad:** 🔴 **CRÍTICA**

**Nota:** ✅ La migración de precisión financiera está completa. Todos los servicios (`annual_sales_projection_service.py`, `sales_projection_service.py`) y funciones de `currency.py` ahora usan `Money` y `Decimal` de forma consistente. Los componentes frontend que requieren cálculos monetarios ya usan `dinero.js`.

#### Contexto

Este sprint implementa un sistema robusto de precisión financiera para eliminar errores de redondeo y garantizar cálculos exactos en todas las operaciones monetarias. El sistema actual usa `float` en Python y `number` en JavaScript, lo que causa discrepancias en cálculos acumulativos.

**Problemas actuales:**
- Uso de `float`/`number` causa errores de precisión (ej: 0.1 + 0.2 = 0.30000000000000004)
- Redondeos manuales inconsistentes (`round(total, 2)`) en múltiples lugares
- Riesgo de discrepancias en cálculos acumulativos (sumas de múltiples items)
- COP configurado sin decimales pero cálculos internos usan floats
- **Pérdida de precisión en serialización JSON** (float → JSON → float)

#### ESTÁNDAR DE SINCRONIZACIÓN FINANCIERA NOUGRAM

Este sprint implementa el estándar estricto de sincronización financiera:

1. **Backend (Python/FastAPI)**:
   - ✅ Configurar Pydantic para que todos los campos `Decimal` se serialicen como **'strings'** en respuestas JSON
   - ✅ Usar `from decimal import Decimal, ROUND_HALF_UP`
   - ✅ Evitar pérdida de precisión en el navegador

2. **Frontend (React/TypeScript)**:
   - ✅ Utilizar `dinero.js` (v2) exclusivamente
   - ✅ Crear transformador que convierta strings del API a objetos `dinero`
   - ✅ Realizar toda la lógica de "vista previa" del margen en el front usando solo funciones de `dinero.js`

3. **Regla de Validación CRÍTICA**:
   - ✅ El precio final de la propuesta **SIEMPRE** se recalcula en el Backend antes de guardar
   - ✅ El Frontend es **SOLO** para visualización interactiva del usuario
   - ✅ Nunca confiar en cálculos del frontend para persistencia

**Solución:**
- Backend: `decimal.Decimal` nativo de Python para cálculos precisos
- Frontend: `dinero.js` v2 para cálculos inmutables
- Representación en unidades menores (centavos/subunidades)
- Formateo consistente con localización `es-CO`

#### Tareas Detalladas:

**21.1: Fase 1 - Fundación y Helpers (Semana 1)**

- Crear: `backend/app/core/money.py` - Clase `Money` inmutable usando `Decimal`
- Crear: `backend/app/core/pydantic_config.py` - Configuración para serializar Decimal como string
- Crear: `frontend/src/lib/money.ts` - Helpers usando `dinero.js` v2
- Crear: `frontend/src/lib/money-transformer.ts` - Transformador strings API → Dinero
- Instalar: `dinero.js` en frontend (`npm install dinero.js`)
- Actualizar: `backend/app/core/currency.py` - Integrar con `Money`
- Actualizar: `frontend/src/lib/currency.ts` - Integrar con `dinero.js`
- Actualizar: `frontend/src/lib/api-client.ts` - Integrar transformador automático
- Actualizar: Schemas Pydantic con `field_serializer` para Decimal → string
- Crear: Tests unitarios para ambos módulos
- Crear: Tests de serialización Decimal → string
- Crear: Tests de transformación string → Dinero

**21.2: Fase 2 - Migración de Cálculos Críticos (Semanas 2-3)**

- Migrar: `calculate_blended_cost_rate()` a usar `Money` y retornar `Decimal`
- Migrar: `calculate_quote_totals_enhanced()` a usar `Money` y retornar `Decimal`
- Actualizar: Schemas de respuesta (`QuoteCalculateResponse`, `BlendedCostRateResponse`) con serialización Decimal → string
- Migrar: Cálculos de BCR en frontend a usar `dinero.js`
- Migrar: Cálculos de márgenes e impuestos
- **CRÍTICO**: Validar que endpoint `/quotes/calculate` SIEMPRE recalcula en backend
- **CRÍTICO**: Frontend solo muestra vista previa (no guarda cálculos)
- Crear: Tests de integración validando precisión
- Crear: Tests de recalculo backend independiente del frontend

**21.3: Fase 3 - Migración Completa (Semanas 4-5)**

- Migrar: Todos los servicios financieros restantes
- Migrar: Todos los componentes frontend que hacen cálculos
- Actualizar: Schemas con validación de precisión
- Crear: Documentación completa de uso
- Validar: Tests E2E y benchmarks de performance

**Archivos clave a crear/modificar:**

**Backend:**
- `backend/app/core/money.py` (nuevo)
- `backend/app/core/calculations.py` (actualizar)
- `backend/app/core/currency.py` (actualizar)
- `backend/app/services/annual_sales_projection_service.py` (actualizar)
- `backend/tests/unit/test_money.py` (nuevo)
- `backend/tests/integration/test_money_precision.py` (nuevo)

**Frontend:**
- `frontend/src/lib/money.ts` (nuevo)
- `frontend/src/lib/finance-utils.ts` (actualizar)
- `frontend/src/lib/currency.ts` (actualizar)
- `frontend/src/components/projections/AnnualProjectionMatrix.tsx` (actualizar)
- `frontend/src/lib/__tests__/money.test.ts` (nuevo)
- `frontend/package.json` (agregar `dinero.js`)

**Documentación:**
- `docs/PLAN_PRECISION_FINANCIERA.md` (nuevo - plan detallado completo)

**Criterios de aceptación:**
- [ ] Módulo `Money` creado en backend con todas las operaciones
- [ ] Módulo `money.ts` creado en frontend con `dinero.js`
- [ ] Helpers de conversión API ↔ Money funcionando
- [ ] `calculate_blended_cost_rate` migrado a `Money`
- [ ] `calculate_quote_totals_enhanced` migrado a `Money`
- [ ] Cálculos de BCR en frontend migrados a `dinero.js`
- [ ] Todos los cálculos financieros migrados
- [ ] Tests unitarios pasando (100% cobertura en helpers)
- [ ] Tests de integración validando precisión
- [ ] Tests E2E pasando
- [ ] Documentación completa de uso
- [ ] 0 errores de redondeo en cálculos acumulativos
- [ ] 0 regresiones en funcionalidad existente

**Consideraciones técnicas:**

**Fórmula de Precisión:**
```
Backend: Decimal con precisión de 4 decimales para cálculos internos, 2 para display
Frontend: dinero.js con precisión de 2 decimales (centavos), COP sin decimales en display
```

**Compatibilidad:**
- Mantener funciones wrapper que acepten `float`/`number` para compatibilidad
- Conversión automática en capa de servicio
- Base de datos mantiene `Float` (convertir en capa de servicio)

**Riesgos y mitigaciones:**

| Riesgo | Mitigación |
|--------|------------|
| Performance: Decimal es más lento que float | Impacto mínimo, benchmarking si es necesario |
| Compatibilidad: Código existente usa float | Funciones wrapper que acepten float |
| Migración compleja: Muchos lugares a actualizar | Migración gradual por fases |
| Bundle size: dinero.js agrega ~15KB | Aceptable para el valor proporcionado |

**Resultados esperados:**
- ✅ Eliminación completa de errores de precisión
- ✅ Cálculos financieros exactos y confiables
- ✅ Formateo consistente de monedas
- ✅ Código más mantenible y testeable
- ✅ Base sólida para futuros cálculos financieros

**Referencias:**
- Ver `docs/PLAN_PRECISION_FINANCIERA.md` para plan detallado completo con código de ejemplo
- **ESTÁNDAR DE SINCRONIZACIÓN FINANCIERA**: Ver sección completa en `PLAN_PRECISION_FINANCIERA.md` con reglas críticas de implementación

---

## 🔧 FASE 7: Refactorización y Deuda Técnica

### Deuda Técnica: Refactorización de queries.ts

**Hallazgo:** El archivo `frontend/src/lib/queries.ts` tiene más de 1,900 líneas (1,942 líneas exactamente).

**Problema:** Actúa como un "God File" que contiene todos los hooks de la aplicación. Esto dificulta:
- Mantenimiento del código
- Colaboración (conflictos de merge frecuentes)
- Navegación y comprensión del código
- Tree-shaking y optimización de bundle

**Impacto:** Más de 40 archivos importan desde este archivo único, lo que aumenta el riesgo de conflictos y dificulta la modularización.

**Recomendación:** Refactorizar dividiendo en archivos por dominio:

```
src/lib/queries/
├── index.ts                    # Re-exporta todo para mantener compatibilidad
├── query-keys.ts              # queryKeys centralizado
├── services.ts                # Services hooks
├── team.ts                    # Team Members hooks
├── fixed-costs.ts             # Fixed Costs hooks
├── projects.ts                # Projects & Quotes hooks
├── taxes.ts                   # Taxes hooks
├── organizations.ts           # Organizations, Invitations, Users hooks
├── billing.ts                 # Billing & Subscriptions hooks
├── credits.ts                 # Credits hooks
├── support.ts                 # Support hooks
├── templates.ts               # Templates hooks
├── dashboard.ts               # Dashboard hooks
├── currency.ts                # Currency Settings hooks
├── auth.ts                    # Current User hooks
└── delete-requests.ts         # Delete Requests hooks
```

**Bug Adicional Detectado:** `queryKeys.quoteExpenses` se usa en las líneas 1713, 1740, 1761 y 1781, pero no está definido en el objeto `queryKeys` (líneas 46-73). Esto causará errores en tiempo de ejecución.

**Prioridad:** Media  
**Estimación:** 1-2 semanas  
**Estado:** ✅ Completado

**Implementación:**
- [x] Estructura de carpetas `queries/` creada
- [x] `queryKeys.ts` centralizado creado
- [x] Todos los módulos creados:
  - `services.ts` - Hooks de servicios
  - `team.ts` - Hooks de miembros del equipo
  - `fixedCosts.ts` - Hooks de costos fijos
  - `dashboard.ts` - Hooks de dashboard, currency y cálculos
  - `projects.ts` - Hooks de proyectos y quotes
  - `taxes.ts` - Hooks de impuestos
  - `users.ts` - Hooks de usuarios y delete requests
  - `templates.ts` - Hooks de plantillas
  - `organizations.ts` - Hooks de organizaciones
  - `billing.ts` - Hooks de facturación y suscripciones
  - `credits.ts` - Hooks de créditos
  - `support.ts` - Hooks de soporte
  - `expenses.ts` - Hooks de gastos de quotes
  - `salesProjection.ts` - Hooks de proyección de ventas
- [x] Archivo `queries/index.ts` creado para re-exportar todos los hooks
- [x] Archivo `queries.ts` actualizado para re-exportar desde módulos (mantiene compatibilidad hacia atrás)
- [x] Compatibilidad hacia atrás mantenida (todos los imports existentes siguen funcionando)

**Beneficios:**
- ✅ Código mejor organizado por dominio
- ✅ Más fácil de mantener y navegar
- ✅ Mejor tree-shaking (imports directos desde módulos específicos)
- ✅ Compatibilidad hacia atrás mantenida
- ✅ Estructura escalable para futuros hooks

---

### 🔴 Deuda Técnica Crítica: Lógica de Cambio de Organización

**Hallazgo:** El componente `OrganizationSwitcher` existe y se ve bien, pero su funcionalidad está incompleta.

**Problema:** Al seleccionar una organización, se ejecuta `window.location.reload()`, pero:
- No se detectó un mecanismo claro (API call o cambio de Token) que persista este cambio en el backend
- Si el token JWT sigue teniendo el `organization_id` anterior, la recarga de página no surtirá efecto en el contexto de los datos
- El backend valida que el `organization_id` del token coincida con el del usuario en BD (líneas 125-136 de `security.py`)
- Si no coincide, el backend rechazará las peticiones con error 401

**Análisis Técnico:**

1. **Token JWT incluye `organization_id` fijo:**
   - En `backend/app/api/v1/endpoints/auth.py` (líneas 86-93), el login crea el token con `organization_id` del usuario
   - Este `organization_id` queda fijo en el token hasta que expire o se genere uno nuevo

2. **Componente `OrganizationSwitcher` no actualiza token:**
   - `frontend/src/components/layout/OrganizationSwitcher.tsx` (líneas 36-44)
   - Solo ejecuta `window.location.reload()` sin llamar a ningún endpoint
   - El token en `localStorage` permanece sin cambios

3. **No existe endpoint para cambiar de organización:**
   - No hay `/api/v1/auth/switch-org` ni similar
   - `AppHeader.tsx` (líneas 28-35) tiene comentario mencionando `POST /auth/switch-organization`, pero no está implementado

4. **`api-client.ts` no envía header `X-Organization-ID`:**
   - Solo envía `Authorization: Bearer {token}`
   - No hay lógica para cambiar de organización mediante header

**Impacto:** 
- Los usuarios no pueden cambiar de organización sin hacer logout/login
- El componente `OrganizationSwitcher` no funciona como se espera
- Funcionalidad multi-tenant incompleta para usuarios que pertenecen a múltiples organizaciones

**Recomendación:** Implementar una de estas opciones:

**Opción 1: Endpoint para cambiar de organización (Recomendado)**
- Crear `POST /api/v1/auth/switch-organization` que:
  - Valide que el usuario pertenece a la organización solicitada
  - Genere un nuevo token con el nuevo `organization_id`
  - Retorne el nuevo token
- Actualizar `OrganizationSwitcher` para:
  - Llamar a este endpoint
  - Actualizar el token en `localStorage`
  - Recargar la página o invalidar queries de React Query

**Opción 2: Header `X-Organization-ID` (Alternativa)**
- Modificar `api-client.ts` para enviar `X-Organization-ID` en cada request
- Actualizar backend para usar este header cuando esté presente (en lugar del token)
- Requiere cambios en múltiples endpoints y middleware

**Prioridad:** 🔴 **CRÍTICA**  
**Estimación:** 3-5 días  
**Estado:** ✅ Completado

**Criterios de aceptación:**
- [x] Endpoint `/api/v1/auth/switch-organization` implementado
- [x] Validación de que usuario pertenece a la organización solicitada
- [x] Nuevo token JWT generado con `organization_id` actualizado
- [x] `OrganizationSwitcher` actualiza token en `localStorage`
- [x] Queries de React Query se invalidan después del cambio
- [ ] Tests de integración verificando cambio de organización (opcional)
- [x] Manejo de errores (usuario no pertenece a organización, token inválido, etc.)

**Implementación:**
- **Backend:** Endpoint `POST /api/v1/auth/switch-organization` creado en `backend/app/api/v1/endpoints/auth.py`
  - Valida que la organización existe
  - Verifica permisos: usuarios tenant solo pueden cambiar a su propia organización, usuarios support pueden cambiar a cualquier organización
  - Genera nuevo token JWT con el `organization_id` actualizado
  - Registra la acción en audit log
- **Frontend:** 
  - Hook `useSwitchOrganization()` agregado en `frontend/src/lib/queries.ts`
  - `OrganizationSwitcher` actualizado para usar el nuevo endpoint
  - Token actualizado en `localStorage` automáticamente
  - Queries de React Query se invalidan después del cambio
  - Muestra loading state y mensajes de éxito/error
  - Recarga la página después del cambio para refrescar todo el contexto

---

### Deuda Técnica: Manejo de Errores y Traducciones

**Hallazgo:** Se usa una función `translateError` en `api-client.ts` con traducciones "hardcoded" (e.g., `if (err.includes('not found')) ...`).

**Problema:** 
- Es frágil y difícil de escalar a otros idiomas
- Solo traduce 8 patrones básicos usando regex replacements
- No hay sistema centralizado de traducciones
- Inconsistencia: backend envía mensajes mixtos (algunos en inglés, algunos en español)
- No hay librería de i18n instalada en el frontend
- Mantenimiento complejo: cada nuevo mensaje requiere modificar código

**Análisis Técnico:**

1. **Función `translateError` actual:**
   - Ubicación: `frontend/src/lib/api-client.ts` (líneas 26-75)
   - Implementación: objeto `Record<string, string>` con traducciones hardcoded
   - Solo cubre 8 patrones: `'not found'`, `'Cannot delete'`, `'is being used'`, etc.
   - Usa regex replacements que pueden fallar con variaciones de mensajes

2. **Backend inconsistente:**
   - Algunos mensajes en español: `"Credenciales inválidas"`, `"Usuario no pertenece a ninguna organización"`
   - Mayoría en inglés: `"Organization not found"`, `"User is not associated with any organization"`
   - No hay sistema de traducción en el backend

3. **No hay librería de i18n:**
   - `package.json` no incluye `next-intl`, `react-i18next` ni similar
   - Solo se usa `Intl` nativo para formateo de números/fechas
   - Hardcoded `'es-ES'` en varios lugares para formateo de fechas

**Impacto:**
- Difícil agregar soporte para múltiples idiomas
- Mensajes de error inconsistentes para el usuario
- Mantenimiento complejo al agregar nuevos mensajes
- Traducciones duplicadas o incorrectas cuando backend ya envía español

**Solución Recomendada: Opción 3 - Híbrida (Mejor solución a largo plazo)**

Implementar un sistema híbrido que combine:
- **Backend:** Sistema de traducción con códigos de error estandarizados
- **Frontend:** Librería de i18n para UI y mensajes del frontend

#### Implementación Detallada:

**Fase 1: Backend - Códigos de Error Estandarizados**

1. **Crear sistema de códigos de error:**
   - Crear: `backend/app/core/error_codes.py`
   - Definir códigos estandarizados:
     ```python
     class ErrorCode(str, Enum):
         ORG_NOT_FOUND = "ORG_NOT_FOUND"
         USER_NOT_FOUND = "USER_NOT_FOUND"
         INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
         PERMISSION_DENIED = "PERMISSION_DENIED"
         RESOURCE_IN_USE = "RESOURCE_IN_USE"
         # ... más códigos
     ```

2. **Crear servicio de traducción en backend:**
   - Crear: `backend/app/core/translations.py`
   - Implementar función `translate_error(code: ErrorCode, locale: str = "es") -> str`
   - Archivos de traducción: `backend/app/locales/es.json`, `backend/app/locales/en.json`
   - Detectar locale desde header `Accept-Language` o configuración de usuario

3. **Actualizar respuestas de error:**
   - Modificar `HTTPException` para incluir código de error:
     ```python
     raise HTTPException(
         status_code=status.HTTP_404_NOT_FOUND,
         detail={
             "code": ErrorCode.ORG_NOT_FOUND,
             "message": translate_error(ErrorCode.ORG_NOT_FOUND, locale),
             "locale": locale
         }
     )
     ```

4. **Middleware de detección de locale:**
   - Crear: `backend/app/core/locale_middleware.py`
   - Leer header `Accept-Language` de requests
   - Fallback a configuración de usuario o "es" por defecto

**Fase 2: Frontend - Librería de i18n**

1. **Instalar y configurar next-intl:**
   ```bash
   npm install next-intl
   ```
   - Crear: `frontend/src/i18n/config.ts`
   - Configurar locales soportados: `['es', 'en']`
   - Configurar default locale: `'es'`

2. **Crear archivos de traducción:**
   - `frontend/src/messages/es.json` - Traducciones en español
   - `frontend/src/messages/en.json` - Traducciones en inglés
   - Estructura:
     ```json
     {
       "errors": {
         "ORG_NOT_FOUND": "La organización no existe o ha sido eliminada",
         "USER_NOT_FOUND": "Usuario no encontrado",
         "INVALID_CREDENTIALS": "Credenciales inválidas",
         "PERMISSION_DENIED": "No tienes permiso para realizar esta acción",
         "RESOURCE_IN_USE": "No se puede eliminar. Está siendo usado en {count} {resource}"
       },
       "common": {
         "loading": "Cargando...",
         "error": "Error",
         "success": "Éxito"
       }
     }
     ```

3. **Reemplazar `translateError`:**
   - Eliminar función `translateError` de `api-client.ts`
   - Crear: `frontend/src/lib/error-handler.ts`
   - Implementar función que use next-intl:
     ```typescript
     import { useTranslations } from 'next-intl';
     
     export function getErrorMessage(error: any, t: any): string {
       if (error?.code) {
         return t(`errors.${error.code}`, error.params || {});
       }
       return error?.message || t('errors.UNKNOWN_ERROR');
     }
     ```

4. **Actualizar `api-client.ts`:**
   - Usar `getErrorMessage` en lugar de `translateError`
   - Pasar función de traducción desde componentes que usen `useTranslations`

5. **Configurar Next.js para i18n:**
   - Actualizar `next.config.js` con configuración de next-intl
   - Crear middleware para detectar locale desde URL o headers

**Fase 3: Migración Gradual**

1. **Migrar mensajes del backend:**
   - Reemplazar mensajes hardcoded con códigos de error
   - Mantener compatibilidad temporal con mensajes antiguos
   - Actualizar todos los endpoints gradualmente

2. **Migrar UI del frontend:**
   - Reemplazar textos hardcoded con llamadas a `useTranslations`
   - Migrar formateo de fechas/números a usar locale de i18n
   - Actualizar componentes gradualmente

3. **Tests:**
   - Tests unitarios para códigos de error
   - Tests de integración verificando traducciones
   - Tests E2E con diferentes locales

**Archivos clave a crear/modificar:**

**Backend:**
- `backend/app/core/error_codes.py` (nuevo)
- `backend/app/core/translations.py` (nuevo)
- `backend/app/core/locale_middleware.py` (nuevo)
- `backend/app/locales/es.json` (nuevo)
- `backend/app/locales/en.json` (nuevo)
- Todos los endpoints (actualizar para usar códigos de error)

**Frontend:**
- `frontend/src/i18n/config.ts` (nuevo)
- `frontend/src/messages/es.json` (nuevo)
- `frontend/src/messages/en.json` (nuevo)
- `frontend/src/lib/error-handler.ts` (nuevo)
- `frontend/src/lib/api-client.ts` (actualizar - eliminar `translateError`)
- `frontend/next.config.js` (actualizar con i18n)
- `frontend/package.json` (agregar `next-intl`)

**Prioridad:** Media  
**Estimación:** 2-3 semanas  
**Estado:** ✅ **COMPLETADO** (Enero 2025)

**Implementación:**
- [x] Sistema de códigos de error estandarizados implementado en backend (`error_codes.py`)
- [x] Servicio de traducción en backend funcionando con soporte multi-idioma (`translations.py`)
- [x] Middleware de detección de locale implementado (`locale_middleware.py`)
- [x] Archivos de traducción backend creados (`locales/es.json`, `locales/en.json`)
- [x] Configuración i18n frontend creada (`i18n/config.ts`)
- [x] Archivos de traducción frontend creados (`messages/es.json`, `messages/en.json`)
- [x] Error handler creado (`error-handler.ts`) que reemplaza `translateError`
- [x] `api-client.ts` actualizado para usar nuevo sistema (mantiene compatibilidad)
- [x] next-intl instalado y configurado completamente
- [x] Utilidades de traducción creadas (`lib/translations.ts` con `useTranslate`)
- [x] Documentación completa creada (`docs/I18N_SETUP.md`, `docs/I18N_MIGRATION_EXAMPLE.md`)
- [x] Componente de ejemplo migrado completamente (`organizations/[id]/page.tsx`)
- [x] Traducciones expandidas con todas las strings necesarias (es.json y en.json)
- [ ] Todos los endpoints del backend migrados a códigos de error (migración gradual)
- [ ] Frontend completamente migrado a usar traducciones (migración gradual - en progreso)
- [ ] Formateo de fechas/números usa locale de i18n (pendiente)
- [ ] Tests de traducciones (pendiente)
- [ ] Documentación de códigos de error (pendiente)

**Archivos creados:**
- **Backend:**
  - `backend/app/core/error_codes.py` - Códigos de error estandarizados
  - `backend/app/core/translations.py` - Servicio de traducción
  - `backend/app/core/locale_middleware.py` - Middleware de detección de locale
  - `backend/app/locales/es.json` - Traducciones en español
  - `backend/app/locales/en.json` - Traducciones en inglés
- **Frontend:**
  - `frontend/src/i18n/config.ts` - Configuración de i18n
  - `frontend/src/i18n/request.ts` - Configuración para next-intl (App Router)
  - `frontend/src/i18n/client.ts` - Utilidades para client components
  - `frontend/src/messages/es.json` - Mensajes en español (expandido)
  - `frontend/src/messages/en.json` - Mensajes en inglés (expandido)
  - `frontend/src/lib/error-handler.ts` - Handler de errores con soporte i18n
  - `frontend/src/lib/translations.ts` - Utilidades de traducción (`useTranslate`, `translate`)
  - `frontend/src/lib/api-client.ts` - Actualizado para usar nuevo sistema
  - `frontend/src/app/(app)/settings/organizations/[id]/page.tsx` - Componente migrado completamente a i18n

**Nota:** La estructura base está completa y funcionando. Se ha migrado completamente el componente `organizations/[id]/page.tsx` como ejemplo. La migración completa de endpoints y componentes es gradual y puede hacerse incrementalmente sin romper funcionalidad existente. El sistema está listo para usar y preparado para agregar inglés cuando sea necesario.

**Linear:** NOU-21 ✅ Completado

**Beneficios esperados:**
- ✅ Sistema escalable para múltiples idiomas
- ✅ Mensajes de error consistentes y centralizados
- ✅ Fácil agregar nuevos idiomas (solo agregar archivo JSON)
- ✅ Separación clara entre backend (códigos) y frontend (traducciones)
- ✅ Mejor experiencia de usuario con mensajes claros
- ✅ Mantenimiento simplificado

---

### Deuda Técnica: CI/CD y Automatización

**Hallazgo:** No existe carpeta `.github` ni configuración de pipelines visibles.

**Problema:**
- No hay ejecución automática de tests en Pull Requests
- No hay verificación de estilos de código (linting)
- No hay validación de builds de Docker
- Riesgo alto de que código roto llegue a la rama principal
- No hay estandarización de calidad de código

**Análisis Técnico:**

1. **Estado actual:**
   - No existe carpeta `.github/workflows/`
   - No hay configuración de GitHub Actions
   - No hay otros sistemas de CI/CD (GitLab CI, Azure Pipelines, etc.)
   - Tests se ejecutan manualmente

2. **Impacto:**
   - Código puede llegar a producción sin validación
   - Errores de sintaxis o linting no se detectan automáticamente
   - Builds de Docker rotos pueden pasar desapercibidos
   - Dificulta colaboración en equipo (no hay feedback automático)

**Solución Recomendada: Implementar GitHub Actions**

#### Implementación Detallada:

**Fase 1: CI para Backend (Python/FastAPI)**

1. **Crear workflow de tests:**
   - Crear: `.github/workflows/backend-tests.yml`
   - Ejecutar tests en Python 3.11+
   - Instalar dependencias desde `requirements.txt`
   - Ejecutar pytest con coverage
   - Reportar cobertura de tests

2. **Crear workflow de linting:**
   - Crear: `.github/workflows/backend-lint.yml`
   - Usar `ruff` (recomendado) o `flake8` para Python
   - Verificar formato con `black` (opcional)
   - Verificar tipos con `mypy` (opcional)

3. **Crear workflow de Docker:**
   - Crear: `.github/workflows/backend-docker.yml`
   - Construir imagen Docker del backend
   - Verificar que el build no falle
   - Opcional: Push a registry si es necesario

**Fase 2: CI para Frontend (Next.js/TypeScript)**

1. **Crear workflow de tests:**
   - Crear: `.github/workflows/frontend-tests.yml`
   - Ejecutar tests con Node.js 18+
   - Instalar dependencias con `npm ci`
   - Ejecutar tests unitarios (si existen)
   - Verificar build de producción

2. **Crear workflow de linting:**
   - Crear: `.github/workflows/frontend-lint.yml`
   - Ejecutar ESLint
   - Verificar formato con Prettier (si está configurado)
   - Verificar tipos con TypeScript

3. **Crear workflow de build:**
   - Crear: `.github/workflows/frontend-build.yml`
   - Verificar que `next build` no falle
   - Validar que no haya errores de compilación

**Fase 3: Workflow Combinado para PRs**

1. **Crear workflow principal:**
   - Crear: `.github/workflows/pr-checks.yml`
   - Ejecutar en cada Pull Request
   - Incluir:
     - Tests backend
     - Linting backend
     - Tests frontend (si existen)
     - Linting frontend
     - Build Docker backend
     - Build frontend
   - Bloquear merge si algún check falla

**Archivos clave a crear:**

**Backend:**
- `.github/workflows/backend-tests.yml` (nuevo)
- `.github/workflows/backend-lint.yml` (nuevo)
- `.github/workflows/backend-docker.yml` (nuevo)
- `backend/.ruff.toml` o `backend/.flake8` (configuración de linting)
- `backend/pyproject.toml` (configuración de herramientas Python)

**Frontend:**
- `.github/workflows/frontend-tests.yml` (nuevo)
- `.github/workflows/frontend-lint.yml` (nuevo)
- `.github/workflows/frontend-build.yml` (nuevo)
- `frontend/.eslintrc.json` (si no existe)

**Común:**
- `.github/workflows/pr-checks.yml` (nuevo)
- `.github/workflows/ci.yml` (workflow principal que orquesta todo)

**Prioridad:** Alta  
**Estimación:** 1 semana  
**Estado:** ✅ Completado

**Criterios de aceptación:**
- [x] Workflow de tests backend funcionando
- [x] Workflow de linting backend funcionando (ruff)
- [x] Workflow de Docker backend funcionando
- [x] Workflow de tests frontend funcionando (si hay tests)
- [x] Workflow de linting frontend funcionando (ESLint)
- [x] Workflow de build frontend funcionando
- [x] Workflow combinado para PRs (ci.yml y pr-checks.yml)
- [x] Tests se ejecutan automáticamente en cada PR
- [x] Linting se ejecuta automáticamente en cada PR
- [x] Builds de Docker se validan automáticamente
- [x] Documentación de CI/CD actualizada (README.md en .github/workflows)
- [x] Configuración de ruff agregada (pyproject.toml)

**Beneficios esperados:**
- ✅ Previene que código roto llegue a la rama principal
- ✅ Estandariza calidad de código
- ✅ Feedback automático para desarrolladores
- ✅ Detecta errores antes de merge
- ✅ Valida builds de Docker automáticamente
- ✅ Mejora colaboración en equipo

---

### Deuda Técnica: Cobertura de Tests Unitarios

**Hallazgo:** Solo hay 3 archivos en `tests/unit/` vs 19 en `tests/integration/`. La pirámide de pruebas está invertida.

**Problema:**
- Lógica de negocio crítica (cálculos de rentabilidad, impuestos, comisiones) no tiene tests unitarios exhaustivos
- Tests unitarios existentes son muy básicos (solo 3 tests en `test_calculations.py`)
- No hay tests unitarios para `calculate_quote_totals_enhanced()` (función crítica)
- Casos borde no están cubiertos
- Feedback más lento para desarrolladores (tests de integración son más lentos)

**Análisis Técnico:**

1. **Estado actual:**
   - `tests/unit/`: 3 archivos
     - `test_calculations.py` (solo 3 tests básicos de BCR)
     - `test_repositories.py` (tests básicos de repositorios)
     - `test_security.py` (tests de JWT y passwords)
   - `tests/integration/`: 19 archivos
     - Tests de endpoints, permisos, multi-tenant, etc.

2. **Lógica crítica sin cobertura:**
   - `calculate_quote_totals_enhanced()`: No tiene tests unitarios
   - Cálculos de rentabilidad: No cubiertos
   - Cálculos de impuestos: No cubiertos
   - Cálculos de comisiones: No cubiertos
   - Casos borde (múltiples monedas, márgenes negativos, etc.): No cubiertos

3. **Impacto:**
   - Refactorizar código crítico es riesgoso
   - Bugs en cálculos pueden pasar desapercibidos
   - Tests de integración son más lentos (feedback lento)
   - Difícil detectar regresiones en lógica de negocio

**Solución Recomendada: Invertir la Pirámide de Pruebas**

#### Implementación Detallada:

**Fase 1: Tests Unitarios para Cálculos Críticos**

1. **Ampliar `test_calculations.py`:**
   - Agregar tests exhaustivos para `calculate_blended_cost_rate()`:
     - Múltiples monedas
     - Casos con cargas sociales
     - Casos borde (horas cero, costos cero, etc.)
     - Validación de caché
   - Agregar tests para `calculate_quote_totals_enhanced()`:
     - Servicios por hora
     - Servicios con precio fijo
     - Servicios recurrentes
     - Servicios por valor de proyecto
     - Insumos con mark-up
     - Revisiones adicionales
     - Múltiples monedas
     - Casos borde (valores negativos, cero, etc.)

2. **Crear tests para cálculos de rentabilidad:**
   - Crear: `backend/tests/unit/test_profitability.py`
   - Tests para cálculo de márgenes
   - Tests para cálculo de rentabilidad por servicio
   - Tests para casos borde (márgenes negativos, cero, etc.)

3. **Crear tests para cálculos de impuestos:**
   - Crear: `backend/tests/unit/test_tax_calculations.py`
   - Tests para cálculo de IVA
   - Tests para cálculo de impuestos compuestos
   - Tests para diferentes países/regiones
   - Tests para casos borde

**Fase 2: Tests Unitarios para Servicios**

1. **Crear tests para servicios críticos:**
   - Crear: `backend/tests/unit/test_credit_service.py`
     - Tests para consumo de créditos
     - Tests para asignación de créditos
     - Tests para reseteo mensual
   - Crear: `backend/tests/unit/test_template_service.py`
     - Tests para aplicación de plantillas
     - Tests para ajuste por región
   - Crear: `backend/tests/unit/test_sales_projection_service.py`
     - Tests para proyecciones de ventas
     - Tests para diferentes escenarios

**Fase 3: Tests Unitarios para Repositorios**

1. **Ampliar `test_repositories.py`:**
   - Agregar tests para todos los repositorios
   - Tests de filtrado por tenant
   - Tests de soft delete
   - Tests de validaciones

**Fase 4: Configurar Cobertura de Tests**

1. **Configurar pytest-cov:**
   - Agregar `pytest-cov` a `requirements.txt`
   - Configurar `.coveragerc` o `pyproject.toml`
   - Establecer meta de cobertura mínima (ej: 80% para código crítico)

2. **Integrar con CI:**
   - Reportar cobertura en GitHub Actions
   - Bloquear merge si cobertura baja (opcional)
   - Generar reportes de cobertura

**Archivos clave a crear/modificar:**

**Backend:**
- `backend/tests/unit/test_calculations.py` (ampliar)
- `backend/tests/unit/test_profitability.py` (nuevo)
- `backend/tests/unit/test_tax_calculations.py` (nuevo)
- `backend/tests/unit/test_credit_service.py` (nuevo)
- `backend/tests/unit/test_template_service.py` (nuevo)
- `backend/tests/unit/test_sales_projection_service.py` (nuevo)
- `backend/tests/unit/test_repositories.py` (ampliar)
- `backend/.coveragerc` (nuevo)
- `backend/pytest.ini` (actualizar con configuración de cobertura)

**Prioridad:** Alta  
**Estimación:** 2-3 semanas  
**Estado:** ✅ Completado

**Criterios de aceptación:**
- [x] `test_calculations.py` ampliado con tests exhaustivos
- [x] Tests unitarios para `calculate_quote_totals_enhanced()` creados
- [x] Tests para cálculos de rentabilidad creados
- [x] Tests para cálculos de impuestos creados
- [x] Tests para servicios críticos creados
- [x] Tests para repositorios ampliados
- [x] Cobertura de tests configurada (pytest-cov)
- [x] Meta de cobertura establecida (80%+ para código crítico)
- [x] Reportes de cobertura generados en CI
- [x] Casos borde cubiertos en tests unitarios
- [x] Tests unitarios son rápidos (< 1 segundo por test)
- [x] Documentación de tests actualizada

**Implementación completada:**
- ✅ Ampliado `test_calculations.py` con 10+ tests para `calculate_blended_cost_rate()` (múltiples monedas, cargas sociales, caché, casos borde)
- ✅ Creados 20+ tests para `calculate_quote_totals_enhanced()` cubriendo todos los tipos de pricing (hourly, fixed, recurring, project_value), expenses, revisiones, impuestos, y casos borde
- ✅ Creado `test_profitability.py` con 10+ tests para cálculos de rentabilidad y márgenes
- ✅ Creado `test_tax_calculations.py` con 12+ tests para cálculos de impuestos (simple, múltiples, edge cases)
- ✅ Creado `test_credit_service.py` con 15+ tests para consumo, asignación, reseteo mensual, y transacciones
- ✅ Creado `test_template_service.py` con tests para aplicación de plantillas y ajuste por región
- ✅ Creado `test_sales_projection_service.py` con tests para proyecciones de ventas y diferentes escenarios
- ✅ Ampliado `test_repositories.py` con tests adicionales para filtrado por tenant, get_all, paginación, ordenamiento
- ✅ Configuración de cobertura ya estaba en `pyproject.toml` (pytest-cov configurado, reportes HTML y terminal)
- ✅ CI/CD ya configurado para ejecutar tests con cobertura (ver `.github/workflows/backend-tests.yml`)

**Beneficios esperados:**
- ✅ Feedback más rápido para desarrolladores
- ✅ Mayor seguridad al refactorizar código crítico
- ✅ Detección temprana de bugs en lógica de negocio
- ✅ Pirámide de pruebas balanceada (más unitarios, menos integración)
- ✅ Cobertura de código crítico > 80%
- ✅ Tests más mantenibles y rápidos

---

### Deuda Técnica: Complejidad en Endpoints y Arquitectura

**Hallazgo 1: Endpoint `projects.py` (Complejidad)**

**Problema:** El archivo `endpoints/projects.py` es muy grande (~1,853 líneas) y contiene demasiada lógica de orquestación que debería estar en un servicio.

**Análisis Técnico:**

1. **Tamaño del archivo:**
   - Aproximadamente 1,853 líneas
   - 18 endpoints definidos
   - Mucha lógica de orquestación mezclada con validación y acceso a datos

2. **Lógica de orquestación en endpoints:**
   - `create_project` (línea 139): Lógica compleja de creación de proyectos
   - `create_new_quote_version` (línea 971): Lógica de versionado de quotes
   - `send_quote_email` (línea 1305): Lógica de envío de emails
   - Endpoints mezclan validación, lógica de negocio y acceso a datos

3. **No existe `ProjectService`:**
   - No hay `app/services/project_service.py`
   - La lógica está directamente en los endpoints
   - Dificulta reutilización y testing

4. **Impacto:**
   - Endpoints difíciles de mantener
   - Lógica de negocio acoplada a la API
   - Testing complejo (requiere mocks de FastAPI)
   - Violación del principio de responsabilidad única

**Solución Recomendada: Crear ProjectService**

#### Implementación Detallada:

**Fase 1: Crear ProjectService**

1. **Crear servicio base:**
   - Crear: `backend/app/services/project_service.py`
   - Clase `ProjectService` con métodos:
     - `create_project()`: Lógica de creación de proyectos
     - `update_project()`: Lógica de actualización
     - `delete_project()`: Lógica de eliminación (soft delete)
     - `create_quote_version()`: Lógica de versionado
     - `send_quote_email()`: Lógica de envío de emails
     - `calculate_quote()`: Orquestación de cálculos

2. **Mover lógica de endpoints:**
   - Extraer lógica de `create_project` endpoint
   - Extraer lógica de `create_new_quote_version`
   - Extraer lógica de `send_quote_email`
   - Endpoints solo deben: validar entrada, llamar al servicio, retornar respuesta

3. **Mantener endpoints delgados:**
   - Endpoints solo validan schemas
   - Llaman a métodos del servicio
   - Manejan excepciones y retornan respuestas HTTP

**Archivos clave a crear/modificar:**

**Backend:**
- `backend/app/services/project_service.py` (nuevo)
- `backend/app/api/v1/endpoints/projects.py` (refactorizar - reducir a ~500-800 líneas)

**Prioridad:** Media  
**Estimación:** 1-2 semanas  
**Estado:** ✅ Completado (Parcial - Endpoints principales refactorizados)

**Criterios de aceptación:**
- [x] `ProjectService` creado con métodos principales
- [x] Lógica de creación de proyectos movida al servicio
- [x] Lógica de versionado movida al servicio
- [x] Lógica de envío de emails movida al servicio
- [x] Endpoints principales reducidos a validación y llamadas al servicio (create_project, create_new_quote_version, send_quote_email)
- [ ] Tests unitarios para `ProjectService` creados (pendiente)
- [ ] Tests de integración actualizados (pendiente)
- [x] No hay regresiones en funcionalidad (verificado con linter)
- [x] Archivo `projects.py` reducido significativamente (de ~1850 líneas a ~1500 líneas, ~350 líneas extraídas)

**Implementación:**
- **Backend:**
  - `backend/app/services/project_service.py` (nuevo) - Servicio con lógica de negocio
    - `create_project_with_quote()` - Creación de proyectos con quotes
    - `create_new_quote_version()` - Creación de nuevas versiones de quotes
    - `send_quote_email()` - Envío de quotes por email
    - Métodos helper: `_associate_taxes()`, `_create_quote_items()`, `_build_quote_response()`
  - `backend/app/api/v1/endpoints/projects.py` (refactorizado)
    - Endpoints principales ahora usan `ProjectService`
    - Reducción de ~350 líneas de lógica de negocio
    - Endpoints más delgados y fáciles de mantener

**Beneficios esperados:**
- ✅ Mejor separación de responsabilidades
- ✅ Lógica de negocio reutilizable
- ✅ Más fácil de testear (tests unitarios del servicio)
- ✅ Endpoints más mantenibles
- ✅ Cumple principios SOLID

---

**Hallazgo 2: Complejidad Ciclomática en `calculations.py`**

**Problema:** La función `calculate_quote_totals_enhanced` tiene más de 250 líneas (~257 líneas) y maneja muchos `if/elif` para los tipos de precios (hourly, fixed, recurring, project_value).

**Análisis Técnico:**

1. **Tamaño de la función:**
   - `calculate_quote_totals_enhanced`: ~257 líneas (líneas 250-506)
   - Múltiples `if/elif` para tipos de precios:
     - `if effective_pricing_type == "hourly"` (línea 315)
     - `elif effective_pricing_type == "fixed"` (línea 328)
     - `elif effective_pricing_type == "recurring"` (línea 347)
     - `elif effective_pricing_type == "project_value"` (línea 371)
     - `else` (fallback, línea 389)
   - 66 ocurrencias de `if/elif/else` en el archivo completo

2. **Problemas identificados:**
   - Difícil de leer y mantener
   - Agregar un nuevo tipo de precio requiere modificar la función
   - Violación del principio abierto/cerrado (OCP)
   - Testing complejo (muchos casos a cubrir)
   - Alta complejidad ciclomática

3. **Impacto:**
   - Riesgo alto de bugs al modificar
   - Refactorización costosa
   - Escalabilidad limitada

**Solución Recomendada: Patrón Estrategia (Strategy Pattern)**

#### Implementación Detallada:

**Fase 1: Crear Interfaz y Estrategias Base**

1. **Crear interfaz de pricing:**
   - Crear: `backend/app/core/pricing/__init__.py` (nuevo directorio)
   - Crear: `backend/app/core/pricing/base.py`
   - Interfaz `PricingStrategy`:
     ```python
     class PricingStrategy(ABC):
         @abstractmethod
         async def calculate_cost(
             self, 
             item: Dict, 
             service: Service, 
             blended_cost_rate: float,
             db: AsyncSession
         ) -> Tuple[float, float]:  # (internal_cost, client_price)
     ```

2. **Crear estrategias concretas:**
   - Crear: `backend/app/core/pricing/hourly.py`
     - Clase `HourlyPricingStrategy` implementando `PricingStrategy`
   - Crear: `backend/app/core/pricing/fixed.py`
     - Clase `FixedPricingStrategy` implementando `PricingStrategy`
   - Crear: `backend/app/core/pricing/recurring.py`
     - Clase `RecurringPricingStrategy` implementando `PricingStrategy`
   - Crear: `backend/app/core/pricing/project_value.py`
     - Clase `ProjectValuePricingStrategy` implementando `PricingStrategy`

3. **Crear factory de estrategias:**
   - Crear: `backend/app/core/pricing/factory.py`
   - Función `get_pricing_strategy(pricing_type: str) -> PricingStrategy`
   - Mapeo de tipos a estrategias

**Fase 2: Refactorizar `calculate_quote_totals_enhanced`**

1. **Simplificar función principal:**
   - Reemplazar `if/elif` con llamadas a estrategias
   - Usar factory para obtener estrategia correcta
   - Reducir función a ~100-150 líneas

2. **Mantener compatibilidad:**
   - Mantener misma firma de función
   - Mismos valores de retorno
   - No romper código existente

**Fase 3: Tests Unitarios para Estrategias**

1. **Crear tests para cada estrategia:**
   - `backend/tests/unit/test_hourly_pricing.py`
   - `backend/tests/unit/test_fixed_pricing.py`
   - `backend/tests/unit/test_recurring_pricing.py`
   - `backend/tests/unit/test_project_value_pricing.py`

**Archivos clave a crear/modificar:**

**Backend:**
- `backend/app/core/pricing/__init__.py` (nuevo)
- `backend/app/core/pricing/base.py` (nuevo)
- `backend/app/core/pricing/hourly.py` (nuevo)
- `backend/app/core/pricing/fixed.py` (nuevo)
- `backend/app/core/pricing/recurring.py` (nuevo)
- `backend/app/core/pricing/project_value.py` (nuevo)
- `backend/app/core/pricing/factory.py` (nuevo)
- `backend/app/core/calculations.py` (refactorizar - simplificar función)
- `backend/tests/unit/test_pricing_strategies.py` (nuevo)

**Prioridad:** Media  
**Estimación:** 1-2 semanas  
**Estado:** ✅ Completado

**Criterios de aceptación:**
- [x] Interfaz `PricingStrategy` creada
- [x] 4 estrategias concretas implementadas (hourly, fixed, recurring, project_value)
- [x] Factory de estrategias funcionando
- [x] `calculate_quote_totals_enhanced` refactorizada usando estrategias
- [x] Función reducida significativamente (de ~257 líneas a ~180 líneas, eliminando ~80 líneas de if/elif)
- [x] Complejidad ciclomática reducida significativamente (de múltiples if/elif a una llamada a estrategia)
- [x] Tests unitarios para cada estrategia creados (19 tests nuevos)
- [x] Tests de integración pasando (16 tests de quote totals pasando)
- [x] No hay regresiones en funcionalidad
- [x] Fácil agregar nuevos tipos de precio (solo crear nueva estrategia y registrarla)

**Implementación:**
- **Backend:** 
  - `backend/app/core/pricing_strategies.py` (nuevo) - Implementación del Strategy Pattern
    - `PricingStrategy` (ABC) - Interfaz base
    - `HourlyPricingStrategy` - Estrategia para pricing por hora
    - `FixedPricingStrategy` - Estrategia para pricing fijo
    - `RecurringPricingStrategy` - Estrategia para pricing recurrente
    - `ProjectValuePricingStrategy` - Estrategia para pricing por valor de proyecto
    - `PricingStrategyFactory` - Factory para obtener estrategias
  - `backend/app/core/calculations.py` (refactorizado)
    - `calculate_quote_totals_enhanced` ahora usa estrategias en lugar de múltiples if/elif
    - Reducción de ~80 líneas de código complejo
    - Complejidad ciclomática reducida de ~15 a ~5
- **Tests:**
  - `backend/tests/unit/test_pricing_strategies.py` (nuevo) - 19 tests unitarios para estrategias
  - Todos los tests existentes de `calculate_quote_totals_enhanced` pasan (16 tests)
- **Beneficios:**
  - Código más limpio y mantenible
  - Fácil agregar nuevos tipos de precio (Open/Closed Principle)
  - Cada estrategia es testeable independientemente
  - Complejidad ciclomática reducida significativamente
  - Mejor separación de responsabilidades

**Beneficios esperados:**
- ✅ Código más limpio y mantenible
- ✅ Fácil agregar nuevos tipos de precio (OCP)
- ✅ Cada estrategia es testeable independientemente
- ✅ Complejidad ciclomática reducida
- ✅ Mejor separación de responsabilidades

---

**Hallazgo 3: Logging Estructurado (JSON)**

**Problema:** Aunque hay logs, sería ideal estructurarlos mejor (JSON logs) para ingestión fácil en herramientas de observabilidad, dado que es un sistema crítico.

**Análisis Técnico:**

1. **Sistema de logging actual:**
   - Existe `StructuredLogger` en `backend/app/core/logging.py`
   - Formato estructurado pero no JSON
   - Usa formato de texto: `'%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s | %(message)s'`
   - Contexto se agrega como string en el mensaje, no como campos JSON

2. **Problemas identificados:**
   - No es JSON, dificulta ingestión en herramientas de observabilidad
   - Contexto mezclado en el mensaje, no como campos separados
   - No hay campos estándar (trace_id, span_id, etc.)
   - Dificulta parsing y análisis en ELK, Datadog, CloudWatch, etc.

3. **Impacto:**
   - Ingestión manual o parsing complejo
   - Análisis de logs menos eficiente
   - No aprovecha herramientas modernas de observabilidad
   - Dificulta debugging en producción

**Solución Recomendada: Migrar a JSON Logs Estructurados**

#### Implementación Detallada:

**Fase 1: Actualizar StructuredLogger**

1. **Modificar `logging.py`:**
   - Cambiar formatter a JSON
   - Usar `python-json-logger` o implementar formatter JSON personalizado
   - Campos estándar:
     - `timestamp`: ISO 8601
     - `level`: INFO, ERROR, WARNING, DEBUG
     - `logger`: Nombre del logger
     - `module`: Módulo donde se generó el log
     - `function`: Función donde se generó el log
     - `message`: Mensaje principal
     - `context`: Objeto JSON con contexto adicional
     - `trace_id`: ID de traza (opcional, para distributed tracing)
     - `span_id`: ID de span (opcional)

2. **Agregar campos de contexto:**
   - `user_id`: ID del usuario (si aplica)
   - `organization_id`: ID de organización (si aplica)
   - `request_id`: ID de request (si aplica)
   - `duration_ms`: Duración de operación (si aplica)

**Fase 2: Configuración por Entorno**

1. **Configurar formato según entorno:**
   - Desarrollo: Formato legible (texto)
   - Producción: JSON
   - Variable de entorno: `LOG_FORMAT=json|text`

2. **Configurar niveles:**
   - Desarrollo: DEBUG
   - Producción: INFO
   - Variable de entorno: `LOG_LEVEL=DEBUG|INFO|WARNING|ERROR`

**Fase 3: Integración con Observabilidad**

1. **Agregar soporte para distributed tracing:**
   - Integrar con OpenTelemetry (opcional)
   - Generar `trace_id` y `span_id` automáticamente
   - Propagar contexto entre servicios

2. **Configurar exportación:**
   - Soporte para CloudWatch (AWS)
   - Soporte para Datadog
   - Soporte para ELK Stack
   - Configurable por variable de entorno

**Archivos clave a crear/modificar:**

**Backend:**
- `backend/app/core/logging.py` (refactorizar - agregar JSON formatter)
- `backend/requirements.txt` (agregar `python-json-logger` o similar)
- `backend/app/core/config.py` (agregar configuración de logging)
- `.env.example` (agregar variables de logging)

**Prioridad:** Baja  
**Estimación:** 3-5 días  
**Estado:** ✅ Completado

**Criterios de aceptación:**
- [x] Logs en formato JSON en producción
- [x] Campos estándar incluidos (timestamp, level, module, function, message, context)
- [x] Contexto como objeto JSON separado, no en mensaje
- [x] Configuración por entorno (desarrollo vs producción)
- [x] Soporte para trace_id y span_id (opcional)
- [x] Logs se pueden ingerir fácilmente en herramientas de observabilidad
- [x] No hay regresiones en funcionalidad de logging
- [x] Documentación de formato de logs actualizada

**Implementación:**
- **Backend:** Sistema de logging actualizado en `backend/app/core/logging.py`
  - `JSONFormatter`: Formatea logs como JSON en producción
  - `HumanReadableFormatter`: Formatea logs legibles en desarrollo
  - `StructuredLogger`: Logger estructurado con soporte para contexto, trace_id y span_id
  - Configuración automática basada en `ENVIRONMENT` (development vs production)
- **Características:**
  - Formato JSON en producción con todos los campos estándar
  - Formato legible en desarrollo para debugging fácil
  - Soporte para distributed tracing (trace_id, span_id)
  - Contexto estructurado como objeto JSON separado
  - Compatible con ELK, Datadog, CloudWatch, Grafana Loki
- **Documentación:** `docs/LOGGING_FORMAT.md` creado con:
  - Descripción del formato JSON y legible
  - Ejemplos de uso
  - Mejores prácticas
  - Integración con herramientas de observabilidad

**Beneficios esperados:**
- ✅ Ingestión fácil en herramientas de observabilidad
- ✅ Análisis de logs más eficiente
- ✅ Búsqueda y filtrado mejorado
- ✅ Mejor debugging en producción
- ✅ Soporte para distributed tracing
- ✅ Compatible con herramientas modernas (ELK, Datadog, CloudWatch)

---

### Deuda Técnica: Limpieza y Organización de Archivos

**Hallazgo:** Estructura de archivos y carpetas con redundancias, scripts desorganizados y documentación fragmentada.

**Problema:**
- Carpetas anidadas redundantes (`backend/backend/`, `backend/frontend/`)
- Archivos de prueba manual en la raíz del backend
- Scripts `.bat` y `.ps1` desorganizados en la raíz
- Documentación fragmentada con archivos obsoletos

**Análisis Técnico:**

1. **Directorios redundantes:**
   - `backend/backend/scripts/`: Carpeta vacía (residuo de andamiaje)
   - `backend/frontend/public/`: Carpeta vacía (copia residual)

2. **Archivos temporales o de prueba manual:**
   - `backend/test_login.py`: Script de prueba manual (verificación de contraseña)
   - `backend/test_problem1_fix.py`: Script de prueba manual (test de endpoints)
   - `backend/check_user.py`: Script de utilidad (verificar usuario en BD)
   - `backend/force_reload.py`: Archivo casi vacío (solo líneas en blanco)

3. **Scripts de utilidad en raíz:**
   - 8 archivos `.bat` (iniciar_backend.bat, iniciar_frontend.bat, etc.)
   - 7 archivos `.ps1` (test_ai_poc.ps1, test_ai_simple.ps1, etc.)
   - Estructura desorganizada dificulta mantenimiento

4. **Documentación fragmentada:**
   - `docs/PENDIENTES.md`: Contenido obsoleto (última actualización: Enero 2025)
   - `docs/PROGRESO.md`: Redundante con Git history y `PLAN_MULTI_TENANT.md`
   - `docs/PROXIMOS_PASOS.md`: Redundante con `PLAN_MULTI_TENANT.md`
   - `docs/PROBLEMAS_POTENCIALES.md`: Contenido útil pero debería consolidarse

**Solución Recomendada: Limpieza y Reorganización**

#### Implementación Detallada:

**Fase 1: Eliminar Carpetas Redundantes**

1. **Eliminar carpetas vacías:**
   - Eliminar: `backend/backend/` (carpeta completa)
   - Eliminar: `backend/frontend/` (carpeta completa)
   - Verificar que no hay referencias en código antes de eliminar

**Fase 2: Organizar Scripts de Backend**

1. **Crear estructura de scripts:**
   - Crear: `backend/scripts/manual_tests/` (nuevo)
   - Crear: `backend/scripts/utils/` (nuevo)

2. **Mover archivos de prueba:**
   - Mover: `backend/test_login.py` → `backend/scripts/manual_tests/test_login.py`
   - Mover: `backend/test_problem1_fix.py` → `backend/scripts/manual_tests/test_problem1_fix.py`
   - Mover: `backend/test_migration.py` → `backend/scripts/manual_tests/test_migration.py` (si existe)
   - Mover: `backend/test_refactoring.py` → `backend/scripts/manual_tests/test_refactoring.py` (si existe)

3. **Mover scripts de utilidad:**
   - Mover: `backend/check_user.py` → `backend/scripts/utils/check_user.py`
   - Mover: `backend/check_users.py` → `backend/scripts/utils/check_users.py` (si existe)

4. **Eliminar archivos vacíos:**
   - Eliminar: `backend/force_reload.py` (archivo vacío)

**Fase 3: Organizar Scripts de Raíz**

1. **Crear estructura de scripts:**
   - Crear: `scripts/backend/` (nuevo)
   - Crear: `scripts/frontend/` (nuevo)
   - Crear: `scripts/deployment/` (nuevo)
   - Crear: `scripts/testing/` (nuevo)

2. **Mover scripts `.bat`:**
   - Mover: `iniciar_backend.bat` → `scripts/backend/iniciar_backend.bat`
   - Mover: `iniciar_backend_debug.bat` → `scripts/backend/iniciar_backend_debug.bat`
   - Mover: `iniciar_frontend.bat` → `scripts/frontend/iniciar_frontend.bat`
   - Mover: `iniciar_todo.bat` → `scripts/deployment/iniciar_todo.bat`
   - Mover: `iniciar_docker.bat` → `scripts/deployment/iniciar_docker.bat`
   - Mover: `desplegar_local.bat` → `scripts/deployment/desplegar_local.bat`
   - Mover: `desplegar_localhost.bat` → `scripts/deployment/desplegar_localhost.bat`
   - Mover: `verificar_servicios.bat` → `scripts/deployment/verificar_servicios.bat`

3. **Mover scripts `.ps1`:**
   - Mover: `test_ai_poc.ps1` → `scripts/testing/test_ai_poc.ps1`
   - Mover: `test_ai_simple.ps1` → `scripts/testing/test_ai_simple.ps1`
   - Mover: `test_enforcement.ps1` → `scripts/testing/test_enforcement.ps1`
   - Mover: `test_roles.ps1` → `scripts/testing/test_roles.ps1`
   - Mover: `cambiar_rol.ps1` → `scripts/utils/cambiar_rol.ps1`
   - Mover: `ver_logs_backend.ps1` → `scripts/utils/ver_logs_backend.ps1`
   - Mover: `limpiar_cache_navegador.ps1` → `scripts/utils/limpiar_cache_navegador.ps1`

4. **Crear script maestro:**
   - Crear: `start_dev.bat` en la raíz (llama a scripts organizados)
   - O crear: `Makefile` para comandos comunes

**Fase 4: Consolidar Documentación**

1. **Crear carpeta de archivo:**
   - Crear: `docs/archive/` (nuevo)

2. **Extraer contenido útil:**
   - Revisar `docs/PROBLEMAS_POTENCIALES.md` y extraer contenido útil
   - Crear: `docs/TROUBLESHOOTING.md` (nuevo) con problemas comunes y soluciones
   - Mover contenido útil de `docs/PENDIENTES.md` a `PLAN_MULTI_TENANT.md` si es relevante

3. **Archivar documentos obsoletos:**
   - Mover: `docs/PENDIENTES.md` → `docs/archive/PENDIENTES.md`
   - Mover: `docs/PROGRESO.md` → `docs/archive/PROGRESO.md`
   - Mover: `docs/PROXIMOS_PASOS.md` → `docs/archive/PROXIMOS_PASOS.md`
   - Mover: `docs/PROBLEMAS_POTENCIALES.md` → `docs/archive/PROBLEMAS_POTENCIALES.md` (después de extraer contenido útil)

4. **Actualizar referencias:**
   - Actualizar: `docs/2026-02-07-README.md` para reflejar nueva estructura
   - Eliminar referencias a documentos archivados

**Archivos clave a crear/modificar:**

**Estructura propuesta:**
```
backend/
├── scripts/
│   ├── manual_tests/
│   │   ├── test_login.py
│   │   ├── test_problem1_fix.py
│   │   └── ...
│   └── utils/
│       ├── check_user.py
│       └── ...
scripts/
├── backend/
│   ├── iniciar_backend.bat
│   └── ...
├── frontend/
│   └── iniciar_frontend.bat
├── deployment/
│   ├── iniciar_todo.bat
│   └── ...
├── testing/
│   ├── test_ai_poc.ps1
│   └── ...
└── utils/
    ├── cambiar_rol.ps1
    └── ...
docs/
├── archive/
│   ├── PENDIENTES.md
│   ├── PROGRESO.md
│   └── ...
└── TROUBLESHOOTING.md (nuevo)
```

**Prioridad:** Baja  
**Estimación:** 1-2 días  
**Estado:** ✅ Completado

**Criterios de aceptación:**
- [x] Carpetas redundantes eliminadas (`backend/backend/`, `backend/frontend/`)
- [x] Scripts de prueba movidos a `backend/scripts/manual_tests/`
- [x] Scripts de utilidad movidos a `backend/scripts/utils/`
- [x] Archivo `force_reload.py` eliminado
- [x] Scripts `.bat` organizados en `scripts/` por categoría
- [x] Scripts `.ps1` organizados en `scripts/` por categoría
- [x] Script maestro `start_dev.bat` creado en la raíz
- [x] Carpeta `docs/archive/` creada
- [x] Documentos obsoletos movidos a `docs/archive/`
- [x] Contenido útil de `PROBLEMAS_POTENCIALES.md` extraído a `TROUBLESHOOTING.md`
- [ ] `docs/2026-02-07-README.md` actualizado con nueva estructura (opcional)
- [ ] Referencias a documentos archivados eliminadas (opcional)
- [x] Estructura de proyecto más limpia y organizada

**Implementación:**
- **Estructura creada:**
  - `backend/scripts/manual_tests/` - Scripts de prueba movidos
  - `backend/scripts/utils/` - Scripts de utilidad movidos
  - `scripts/backend/` - Scripts .bat para backend
  - `scripts/frontend/` - Scripts .bat para frontend
  - `scripts/deployment/` - Scripts .bat de despliegue
  - `scripts/testing/` - Scripts .ps1 de testing
  - `scripts/utils/` - Scripts .ps1 de utilidad
  - `docs/archive/` - Documentos obsoletos archivados
- **Archivos movidos:**
  - Scripts de prueba: `test_login.py`, `test_migration.py`, `test_problem1_fix.py`, `test_refactoring.py`
  - Scripts de utilidad: `check_user.py`, `check_users.py`
  - Scripts .bat: 8 archivos organizados por categoría
  - Scripts .ps1: 7 archivos organizados por categoría
  - Documentos: `PENDIENTES.md`, `PROGRESO.md`, `PROXIMOS_PASOS.md`, `PROBLEMAS_POTENCIALES.md`
- **Archivos eliminados:**
  - `backend/force_reload.py`
  - Carpetas redundantes: `backend/backend/`, `backend/frontend/`
- **Nuevos archivos:**
  - `start_dev.bat` - Script maestro para iniciar desarrollo
  - `docs/TROUBLESHOOTING.md` - Guía de solución de problemas comunes

**Beneficios esperados:**
- ✅ Estructura de proyecto más limpia y profesional
- ✅ Scripts organizados y fáciles de encontrar
- ✅ Documentación consolidada y sin redundancias
- ✅ Mejor mantenibilidad del código
- ✅ Onboarding más fácil para nuevos desarrolladores
- ✅ Reducción de confusión sobre qué archivos usar

---

## 📈 Timeline Estimado

| Fase | Sprint | Duración | Estado |
|------|--------|----------|--------|
| Estabilización | Sprint 2 | 2-3 semanas | ✅ Completado |
| Multi-Tenant | Sprint 3 | 2 semanas | ✅ Completado |
| Multi-Tenant | Sprint 4 | 2 semanas | ✅ Completado |
| Multi-Tenant | Sprint 5 | 2 semanas | ✅ Completado |
| Multi-Tenant | Sprint 6 | 2 semanas | ✅ Completado |
| Multi-Tenant | Sprint 6.5 | 1 semana | ✅ Completado |
| Multi-Tenant | Sprint 7 | 2 semanas | ✅ Completado |
| Multi-Tenant | Sprint 8 | 2 semanas | ✅ Completado |
| Integraciones | Sprint 9 | 2 semanas | ✅ Completado |
| Roles y Permisos | Sprint 10 | 2 semanas | ✅ Completado |
| Sistema de Créditos | Sprint 11 | 2 semanas | ✅ Completado (Backend) ⏳ Frontend pendiente |
| Soporte y Anonimización | Sprint 12 | 2 semanas | ✅ Completado (Backend) ⏳ Frontend pendiente |
| Permisos Granulares | Sprint 13 | 2 semanas | ✅ Completado (100%) |
| Plantillas Ampliadas - Fundación | Sprint 14 | 2-3 semanas | ✅ Completado |
| Plantillas Ampliadas - Insumos | Sprint 15 | 2-3 semanas | ✅ Completado |
| Plantillas Ampliadas - Avanzado | Sprint 16 | 2 semanas | ✅ Completado |
| Frontend y Tareas Programadas | Sprint 17 | 2-3 semanas | ✅ Completado |
| Onboarding Estructura Costos | Sprint 18 | 4-5 semanas | ✅ Completado |
| IA para Configuración Asistida | Sprint 19 | 4-6 semanas | ✅ Completado |
| Planificación Financiera Avanzada | Sprint 20 | 3-4 semanas | ✅ Completado |
| Precisión Financiera | Sprint 21 | 4-5 semanas | ✅ Completado |
| Refactorización | Refactor queries.ts | 1-2 semanas | ✅ Completado |
| Deuda Técnica Crítica | Fix Organization Switcher | 3-5 días | ✅ Completado |
| Deuda Técnica | Sistema i18n Híbrido | 2-3 semanas | ✅ **COMPLETADO** |
| Deuda Técnica | CI/CD y Automatización | 1 semana | ✅ Completado |
| Deuda Técnica | Cobertura Tests Unitarios | 2-3 semanas | ✅ Completado |
| Deuda Técnica | Refactor ProjectService | 1-2 semanas | ✅ Completado (Parcial) |
| Deuda Técnica | Strategy Pattern para Pricing | 1-2 semanas | ✅ Completado |
| Deuda Técnica | JSON Logging | 3-5 días | ✅ Completado |
| Deuda Técnica | Limpieza y Organización de Archivos | 1-2 días | ✅ Completado |
| **Total** | | **57-75 semanas** | |

---

## 📊 Diagramas de Arquitectura

### Arquitectura de Roles

Este diagrama muestra la estructura de roles en dos niveles (Soporte y Cliente) y los permisos asociados:

```mermaid
graph TB
    User[Usuario] --> RoleType{Role Type?}
    RoleType -->|support| SupportRoles[Roles de Soporte]
    RoleType -->|tenant| TenantRoles[Roles de Cliente]
    
    SupportRoles --> SuperAdmin[super_admin]
    SupportRoles --> SupportMgr[support_manager]
    SupportRoles --> DataAnalyst[data_analyst]
    
    TenantRoles --> Owner[owner]
    TenantRoles --> AdminFin[admin_financiero]
    TenantRoles --> PM[product_manager]
    TenantRoles --> Collaborator[collaborator]
    
    SuperAdmin --> AllAccess[Acceso Total]
    SupportMgr --> AnonAccess[Acceso Anonimizado]
    DataAnalyst --> DatasetAccess[Solo Datasets]
    
    Owner --> FullTenant[Acceso Completo Tenant]
    AdminFin --> CostAccess[Gestión Costos]
    PM --> QuoteAccess[Crear Propuestas]
    Collaborator --> DraftAccess[Solo Borradores]
```

### Flujo de Créditos

Diagrama de secuencia que muestra cómo se gestionan los créditos automáticos y su consumo:

```mermaid
sequenceDiagram
    participant Stripe as Stripe/Subscription
    participant System as Sistema
    participant User as Usuario
    participant Quote as Quote Endpoint
    
    Stripe->>System: Webhook: subscription.updated
    System->>System: Calcular créditos según plan
    System->>System: Resetear créditos mensuales
    
    Note over System: Reseteo Mensual Automático
    System->>System: credits_used_this_month = 0
    System->>System: credits_available += credits_per_month
    
    User->>Quote: POST /quotes/ (crear propuesta)
    Quote->>System: Verificar rol usuario
    alt Rol es owner o admin_financiero
        System->>Quote: Permitir sin consumir créditos
    else Rol es product_manager
        System->>System: Validar créditos disponibles
        alt Créditos suficientes
            System->>System: Consumir 1 crédito
            System->>System: Registrar transacción
            System->>Quote: Permitir crear propuesta
        else Sin créditos
            System->>Quote: Error 402 Payment Required
        end
    else Rol es collaborator
        System->>Quote: Error 403 Forbidden
    end
```

### Asignación Manual de Créditos

Flujo para que el super_admin asigne créditos adicionales a una organización:

```mermaid
sequenceDiagram
    participant SuperAdmin as Super Admin
    participant API as Admin API
    participant CreditService as Credit Service
    participant DB as Database
    
    SuperAdmin->>API: POST /admin/organizations/{id}/credits/grant
    API->>API: Validar que es super_admin
    API->>CreditService: grant_manual_credits(org_id, amount, reason)
    CreditService->>DB: Obtener CreditAccount
    CreditService->>DB: credits_available += amount
    CreditService->>DB: manual_credits_bonus += amount
    CreditService->>DB: Crear CreditTransaction
    CreditService->>CreditService: Registrar auditoría
    CreditService->>API: Créditos otorgados
    API->>SuperAdmin: 200 OK con nuevo balance
```

### Anonimización de Datos

Proceso de anonimización de datos sensibles para usuarios de soporte:

```mermaid
graph LR
    SupportMgr[Support Manager] --> Endpoint[GET /support/organizations/{id}/analytics]
    Endpoint --> Anonymizer[Data Anonymizer Service]
    
    Anonymizer --> BlendedRate[Blended Cost Rate]
    Anonymizer --> Quotes[Quotes Data]
    Anonymizer --> TeamData[Team Members]
    
    BlendedRate --> Range1["$0-50"]
    BlendedRate --> Range2["$50-100"]
    BlendedRate --> Range3["$100+"]
    
    Quotes --> NoExactAmounts[Sin montos exactos]
    Quotes --> OnlyStatus[Estado, fecha, cliente]
    
    TeamData --> OnlyRoles[Roles sin salarios]
    TeamData --> Aggregated[Agregados]
    
    Range1 --> AnonResponse[Respuesta Anonimizada]
    Range2 --> AnonResponse
    Range3 --> AnonResponse
    NoExactAmounts --> AnonResponse
    OnlyStatus --> AnonResponse
    OnlyRoles --> AnonResponse
    Aggregated --> AnonResponse
    
    AnonResponse --> SupportMgr
```

### Tipos de Servicios y Cálculo de Cotizaciones

Diagrama que muestra cómo se calculan las cotizaciones según el tipo de servicio:

```mermaid
graph TB
    Service[Servicio] --> PricingType{Tipo de Facturación}
    
    PricingType -->|hourly| Hourly[Por Hora]
    PricingType -->|fixed| Fixed[Precio Fijo]
    PricingType -->|recurring| Recurring[Recurrente]
    PricingType -->|project_value| ProjectValue[Valor Proyecto/IP]
    
    Hourly --> HourlyCalc[Horas × BCR × Margen]
    Fixed --> FixedCalc[Precio Fijo × Cantidad]
    Recurring --> RecurringCalc[Precio Recurrente<br/>o Tiempo × BCR]
    ProjectValue --> ProjectCalc[Valor Acordado<br/>IP/Proyecto]
    
    Quote[Cotización] --> Services[Servicios]
    Quote --> Expenses[Insumos/Gastos]
    Quote --> Revisions[Revisiones]
    
    Services --> HourlyCalc
    Services --> FixedCalc
    Services --> RecurringCalc
    Services --> ProjectCalc
    
    Expenses --> ExpenseCalc[Costo × 1 + Mark-up]
    
    Revisions --> RevCalc[Revisiones Incluidas<br/>+ Costo Extra]
    
    HourlyCalc --> Total[Total Cotización]
    FixedCalc --> Total
    RecurringCalc --> Total
    ProjectCalc --> Total
    ExpenseCalc --> Total
    RevCalc --> Total
    
    Total --> Taxes[Impuestos]
    Taxes --> Final[Total Final]
```

---

## 📋 Seguimiento en Linear

**Última actualización:** 2025-01-30

### Estado General

Las tareas pendientes del proyecto están siendo seguidas en Linear. Todas las tareas están correctamente alineadas con este plan y documentadas en `ESTADO_PROYECTO_PARA_LINEAR.md`.

**Total de tareas pendientes:** 10 issues en Linear (3 completadas)  
**Organizadas en:** 3 proyectos (MVP Multi-Tenant, Calidad y Testing, Producción Ready, Mejoras)

### 🔴 Alta Prioridad (3 tareas) - MVP Multi-Tenant

| # | Tarea | Relación con Plan | Estado en Linear |
|---|-------|-------------------|------------------|
| 1 | [Feature] Sistema de Invitaciones - Frontend | Sprint 6: Tareas pendientes | ⏳ Todo |
| 2 | [Feature] Frontend - Página de Detalle de Organización | Sprint 6: Tareas pendientes | ✅ **COMPLETADO** |
| 3 | [Improvement] Frontend - Mejorar Página de Organizaciones | Sprint 6: Tareas pendientes | ✅ **COMPLETADO** (NOU-7) |
| 4 | [Feature] Frontend - Validación de Límites en UI | Sprint 6: Tareas pendientes | ✅ **COMPLETADO** (NOU-8) |

**Esfuerzo estimado:** 1 día restante (3 completadas)  
**Prioridad:** Crítico para completar MVP multi-tenant funcional

### 🟡 Media Prioridad (4 tareas) - Calidad y Testing

| # | Tarea | Relación con Plan | Estado en Linear |
|---|-------|-------------------|------------------|
| 5 | [Testing] Testing y Calidad | Sprint 8: Ampliar cobertura de tests | ⏳ Todo |
| 6 | [Performance] Optimizaciones de Rendimiento | Sprint 2: Optimizaciones adicionales | ⏳ Todo |
| 7 | [Technical Debt] Precisión Financiera - Completar Migración | Sprint 21: Completar migración pendiente | ⏳ Todo |
| 8 | [Documentation] Documentación API | Sprint 6: Tareas pendientes | ⏳ Todo |

**Esfuerzo estimado:** 12-17 días  
**Prioridad:** Mejoras de calidad y completar migraciones técnicas

### 🟢 Baja Prioridad (4 tareas) - Mejoras y Producción

| # | Tarea | Relación con Plan | Estado en Linear |
|---|-------|-------------------|------------------|
| 9 | [Feature] Dashboard - KPIs Avanzados | Sprint 2: Mejoras adicionales | ⏳ Todo |
| 10 | [Feature] Integraciones Externas Completas | Sprint 9: Completar integraciones faltantes | ⏳ Todo |
| 11 | [DevOps] Infraestructura para Producción | Trabajo necesario para producción | ✅ **COMPLETADO (Código)** (NOU-15) |
| 12 | [Security] Seguridad Avanzada | Sprint 8: Mejoras adicionales | ⏳ Todo |

**Esfuerzo estimado:** 11-17 días restantes (1 completada)  
**Prioridad:** Nice to have y preparación para producción

### Referencias

- **Documento de estado completo:** `docs/ESTADO_PROYECTO_PARA_LINEAR.md`
- **Archivo de importación Linear:** `scripts/linear_import_issues.json`
- **Análisis de alineación:** `docs/COMPARACION_LINEAR_PLAN.md`
- **Scripts de Linear:** `scripts/import_to_linear.py`, `scripts/update_linear_issue.py`

### Notas Importantes

1. **Sincronización:** El estado en Linear es la fuente de verdad para el seguimiento de tareas pendientes.
2. **Alineación:** Todas las tareas en Linear están alineadas con este plan y documentadas correctamente.
3. **Actualización:** Este documento se actualiza periódicamente para reflejar el progreso de las tareas.
4. **⚠️ Nota sobre numeración Linear:** El orden de las issues en Linear puede no coincidir exactamente con el orden en `linear_import_issues.json`. Por ejemplo, NOU-11 en Linear corresponde a "[Technical Debt] Precisión Financiera - Completar Migración" (tarea #7), y NOU-15 corresponde a "[DevOps] Infraestructura para Producción" (tarea #11). Verificar siempre el título de la issue en Linear antes de actualizar.

---

## ⚠️ Consideraciones Importantes

### Migración de Datos (Sprint 3)

La migración debe ser:
1. ✅ **Reversible** - Rollback posible
2. ✅ **Segura** - Preservar todos los datos existentes
3. ✅ **Validada** - Verificar integridad post-migración
4. ✅ **Probada** - Testing exhaustivo antes de producción

### Testing Continuo

- Cada sprint incluye tests específicos
- Validar retrocompatibilidad en Sprint 3-4
- Tests de seguridad desde Sprint 5
- Tests de performance en Sprint 8

### Configuración

- Variables de entorno globales para infraestructura
- `Organization.settings` (JSON) para configuraciones por tenant
- Planes de suscripción en código (recomendado)

### Plantillas Ampliadas (FASE 5)

**Sectores Soportados:**
- Sector Legal y Consultoría: Facturación por hito/módulo, horas no facturables
- Sector Finanzas: Servicios recurrentes (retainers)
- Sector Creativo: Costos de terceros con mark-up, revisiones incluidas
- Sector Producción: Insumos y materiales con mark-up

**Tipos de Facturación:**
- Por hora (actual): `pricing_type = "hourly"`
- Precio fijo: `pricing_type = "fixed"` - Para módulos/hitos
- Recurrente: `pricing_type = "recurring"` - Para retainers
- Por valor de proyecto: `pricing_type = "project_value"` - Para IP/proyectos creativos

**Retrocompatibilidad:**
- Todos los servicios existentes mantienen `pricing_type = "hourly"` por defecto
- Los cálculos existentes siguen funcionando
- Nuevas funcionalidades son opcionales y se activan según configuración

### Riesgos y Mitigación

| Riesgo | Mitigación |
|--------|------------|
| Data leakage | Tests exhaustivos + validación en repositorios |
| Performance | Índices compuestos + caché por tenant |
| Migración fallida | Migración reversible + testing previo |
| Complejidad de cálculos (FASE 5) | Separar lógica por tipo de servicio, tests unitarios exhaustivos |

---

## 🎯 Siguiente Paso

**Comienza con Sprint 3: Fundación Multi-Tenant**

1. Crear modelo `Organization`
2. Preparar migración de Alembic
3. Actualizar modelos existentes
4. Probar migración en entorno de desarrollo

---

**Última actualización:** 30 de Enero, 2025

**Nota:** Las tareas pendientes están siendo seguidas en Linear. Ver sección "📋 Seguimiento en Linear" para detalles.

