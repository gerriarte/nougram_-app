# 🎯 Plan para Completar 100% Backend y Frontend Multi-Tenant

**Fecha:** Enero 2025  
**Estado Actual:** Backend ~95% | Frontend ~85%

**Nota:** Este documento complementa `PLAN_MULTI_TENANT.md`. 

**Estado según documentos:**
- `PLAN_MULTI_TENANT.md` marca Sprint 6 como "✅ COMPLETADO"
- `SPRINT6_PROGRESO.md` identifica tareas pendientes específicas

Las tareas aquí listadas corresponden a completar el **100% real** del Sprint 6, completando las funcionalidades que están implementadas de forma básica pero necesitan mejoras para producción.

**Referencias:**
- Ver `docs/sprints/SPRINT6_PROGRESO.md` sección "Tareas Pendientes" para más detalles
- Ver `docs/SPRINT_6_ANALISIS_PENDIENTES.md` para análisis detallado del frontend

---

## 📋 Mapeo con Documentos Existentes

### Tareas Contempladas en `SPRINT6_PROGRESO.md`

Las siguientes tareas están **explícitamente identificadas** como pendientes en `docs/sprints/SPRINT6_PROGRESO.md`:

#### Backend:
1. ✅ **Sistema de Invitaciones Completo** (línea 147-152)
   - Modelo de Invitation en base de datos
   - Endpoint para aceptar invitación
   - Envío de emails de invitación
   - Tokens de invitación con expiración
   - Historial de invitaciones

2. ✅ **Tests Unitarios Adicionales** (línea 143-145)
   - Tests unitarios para OrganizationRepository
   - Tests de edge cases adicionales

3. ✅ **Documentación de API** (línea 164)
   - Documentación OpenAPI/Swagger completa

#### Frontend (identificado en `SPRINT_6_ANALISIS_PENDIENTES.md`):
1. ✅ **Página de registro público** - Ya completada
2. ✅ **Migración de usuarios a endpoints de organizaciones** - Ya completada
3. ✅ **Funcionalidad de invitaciones en UI** - Ya completada
4. ⏳ **Mejorar página de organizaciones** - Pendiente
5. ⏳ **Página de detalle de organización** - Pendiente
6. ⏳ **Validación de límites en frontend** - Pendiente

---

## 📊 BACKEND - Para llegar al 100%

### Estado Actual: ~95% ✅

**Endpoints Implementados:**
- ✅ `GET /organizations/me` - Obtener mi organización
- ✅ `GET /organizations/` - Listar organizaciones (con paginación)
- ✅ `GET /organizations/{id}` - Obtener organización por ID
- ✅ `POST /organizations/` - Crear organización (super admin)
- ✅ `POST /organizations/register` - Registro público de organización
- ✅ `PUT /organizations/{id}` - Actualizar organización
- ✅ `DELETE /organizations/{id}` - Eliminar organización
- ✅ `PUT /organizations/{id}/subscription` - Actualizar plan de suscripción
- ✅ `GET /organizations/{id}/users` - Listar usuarios de organización
- ✅ `POST /organizations/{id}/invite` - Invitar usuario
- ✅ `POST /organizations/{id}/users` - Agregar usuario
- ✅ `PUT /organizations/{id}/users/{user_id}/role` - Actualizar rol
- ✅ `DELETE /organizations/{id}/users/{user_id}` - Remover usuario
- ✅ `GET /organizations/{id}/stats` - Estadísticas de uso
- ✅ Validación de límites por plan integrada

---

### ❌ Lo que FALTA en Backend (5%)

#### 1. Sistema de Invitaciones Completo ⏳ (2-3 días)
**Estado:** Básico implementado, falta completar

**Pendiente:**
- [ ] **Modelo `Invitation` en base de datos**
  - Campos: `id`, `organization_id`, `email`, `role`, `token`, `expires_at`, `accepted_at`, `created_by_id`, `created_at`
  - Índices: `token`, `email`, `organization_id`
  
- [ ] **Endpoint `POST /organizations/{id}/invitations/{token}/accept`**
  - Aceptar invitación con token
  - Crear usuario si no existe o agregar a organización si ya existe
  - Validar que token no haya expirado
  - Retornar token de acceso para login automático

- [ ] **Envío de emails de invitación**
  - Integrar servicio de email (SendGrid/SES/SMTP)
  - Template de email con link de invitación
  - Link debe incluir token: `/auth/accept-invitation?token=xxx`
  - Reemplazar endpoint actual que solo genera token

- [ ] **Endpoint `GET /organizations/{id}/invitations`**
  - Listar invitaciones pendientes y aceptadas
  - Filtrar por estado (pending, accepted, expired)
  - Solo visible para org_admin y super_admin

- [ ] **Endpoint `DELETE /organizations/{id}/invitations/{invitation_id}`**
  - Cancelar invitación pendiente
  - Solo visible para org_admin y super_admin

**Archivos a crear/modificar:**
- `backend/app/models/invitation.py` (nuevo)
- `backend/alembic/versions/XXX_add_invitations.py` (nuevo)
- `backend/app/repositories/invitation_repository.py` (nuevo)
- `backend/app/schemas/invitation.py` (nuevo)
- `backend/app/api/v1/endpoints/invitations.py` (nuevo)
- `backend/app/core/email.py` (modificar - agregar envío de invitaciones)
- `backend/app/api/v1/endpoints/organizations.py` (modificar - integrar modelo)

**Esfuerzo:** 2-3 días

---

#### 2. Tests Unitarios Adicionales ⏳ (1-2 días)
**Estado:** Tests de integración completos, falta unitarios

**Pendiente:**
- [ ] Tests unitarios para `OrganizationRepository`
  - Test `get_by_slug()`
  - Test `list_all()` con paginación
  - Test `get_with_user_count()`
  - Test `update_subscription()`
  - Test métodos de usuarios y estadísticas

- [ ] Tests de edge cases
  - Validación de límites cuando se alcanza el máximo
  - Comportamiento con límites ilimitados (enterprise)
  - Manejo de organizaciones eliminadas (soft delete si aplica)
  - Validación de permisos edge cases

**Archivos a crear:**
- `backend/tests/unit/test_organization_repository.py` (nuevo)

**Esfuerzo:** 1-2 días

---

#### 3. Documentación API ⏳ (0.5-1 día)
**Estado:** Docstrings básicos, falta documentación completa

**Pendiente:**
- [ ] Documentación OpenAPI/Swagger completa
  - Ejemplos de requests/responses para todos los endpoints
  - Esquemas de autenticación documentados
  - Códigos de error documentados
  - Ejemplos de uso por escenario

**Esfuerzo:** 0.5-1 día

---

### 📝 Resumen Backend

| Tarea | Esfuerzo | Prioridad |
|-------|----------|-----------|
| Sistema de Invitaciones Completo | 2-3 días | Alta |
| Tests Unitarios | 1-2 días | Media |
| Documentación API | 0.5-1 día | Baja |
| **TOTAL** | **3.5-6 días** | |

---

## 🎨 FRONTEND - Para llegar al 100%

### Estado Actual: ~85% ✅

**Páginas Implementadas:**
- ✅ `/auth/register` - Registro público de organización
- ✅ `/settings/users` - Gestión de usuarios (usa endpoints correctos)
- ✅ `/settings/organizations` - Lista básica de organizaciones
- ✅ `/onboarding` - Flujo de onboarding con plantillas

---

### ❌ Lo que FALTA en Frontend (15%)

#### 1. Página de Detalle de Organización ⏳ (1 día)
**Ubicación:** `/settings/organizations/[id]` (nueva página)

**Funcionalidades requeridas:**
- [ ] Vista completa de detalles de organización
  - Información general (nombre, slug, plan, estado)
  - Fechas de creación y última actualización
  - Settings en formato JSON (expandible/colapsable)
  
- [ ] Sección de usuarios con gestión integrada
  - Lista de usuarios con roles
  - Botón para agregar usuario
  - Botón para invitar usuario
  - Acciones inline (cambiar rol, remover)
  - Navegación directa a `/settings/users` con filtro por org

- [ ] Estadísticas de uso visuales
  - Cards/badges mostrando:
    - Total de usuarios (con límite)
    - Total de proyectos (con límite)
    - Total de servicios (con límite)
    - Total de team members (con límite)
  - Barras de progreso mostrando % de uso
  - Alertas cuando se acerca al límite
  - Mensaje de upgrade si se alcanza el límite

- [ ] Configuración de organización
  - Editar nombre y slug (con validación)
  - Cambiar plan de suscripción (dialog)
  - Ver/editar settings (JSON editor o form dinámico)

- [ ] Timeline/actividad reciente (opcional)
  - Últimos usuarios agregados
  - Cambios de plan
  - Eventos importantes

**Archivos a crear:**
- `frontend/src/app/(app)/settings/organizations/[id]/page.tsx` (nuevo)

**Dependencias:**
- Hooks ya existen: `useGetOrganization()`, `useGetOrganizationUsers()`, `useGetOrganizationStats()`
- Endpoints backend ya existen

**Esfuerzo:** 6-8 horas (1 día)

---

#### 2. Mejorar Página de Organizaciones ⏳ (4-6 horas)
**Ubicación:** `/settings/organizations` (mejorar existente)

**Mejoras requeridas:**
- [ ] Mostrar estadísticas de uso en la tabla/lista
  - Badge con número de usuarios sobre total permitido
  - Indicador visual de uso (% de límites)
  - Color coding: verde (<50%), amarillo (50-90%), rojo (>90%)
  
- [ ] Agregar acción "Ver Detalles"
  - Link/button que navega a `/settings/organizations/[id]`
  - O dialog con vista de resumen (menos detallada que página completa)

- [ ] Mejorar visualización para usuarios no-super-admin
  - Mostrar estadísticas de SU organización
  - Cards con resumen de uso
  - Quick actions (invitar usuario, ver usuarios, etc.)

- [ ] Agregar filtros y búsqueda (para super-admin)
  - Filtrar por plan
  - Filtrar por estado
  - Buscar por nombre o slug
  - Ordenar por fecha, nombre, etc.

**Archivos a modificar:**
- `frontend/src/app/(app)/settings/organizations/page.tsx` (mejorar)
- Limpiar código duplicado que existe actualmente

**Esfuerzo:** 4-6 horas

---

#### 3. Validación de Límites en UI ⏳ (3-4 horas)
**Ubicación:** Múltiples páginas (proyectos, servicios, usuarios, team)

**Funcionalidades requeridas:**
- [ ] Mostrar límites actuales vs usados en páginas de creación
  - Card o badge mostrando "X de Y usuarios" antes del formulario
  - Barra de progreso visual
  - Mensaje informativo sobre el plan actual
  
- [ ] Alertas cuando se acerca al límite
  - Toast/warning cuando queda <20% del límite disponible
  - Banner en la página cuando queda <10%
  - Mensaje sugeriendo upgrade de plan

- [ ] Deshabilitar acciones cuando se alcanza el límite
  - Botón "Crear Usuario" deshabilitado si ya alcanzó el límite
  - Mensaje claro: "Has alcanzado el límite de tu plan. Considera hacer upgrade."
  - Link a página de suscripción/upgrade

- [ ] Validación en formularios antes de enviar
  - Verificar límites antes de crear recurso
  - Mostrar error específico si se alcanzó el límite
  - Sugerir upgrade con link

**Archivos a modificar:**
- `frontend/src/app/(app)/settings/users/page.tsx`
- `frontend/src/app/(app)/projects/new/page.tsx` (o página de creación)
- `frontend/src/app/(app)/settings/services/page.tsx`
- `frontend/src/app/(app)/settings/team/page.tsx`
- Componente reutilizable: `frontend/src/components/organization/LimitIndicator.tsx` (nuevo)

**Hooks/API:**
- Ya existe: `useGetOrganizationStats(orgId)` devuelve límites y usados

**Esfuerzo:** 3-4 horas

---

#### 4. Sistema de Invitaciones en Frontend ⏳ (2-3 horas)
**Ubicación:** `/settings/users` (agregar funcionalidad)

**Estado:** Backend básico existe, frontend parcialmente implementado

**Funcionalidades requeridas:**
- [ ] Mejorar dialog de invitación existente
  - Mostrar token generado temporalmente (hasta que se implemente email)
  - Copiar token al portapapeles
  - Instrucciones claras de cómo compartir el token
  
- [ ] Lista de invitaciones pendientes
  - Nueva sección en `/settings/users` mostrando invitaciones
  - Tabla con: email, rol, fecha de invitación, estado, acciones
  - Botón para reenviar/cancelar invitación
  - Badge de estado (pendiente, aceptada, expirada)

- [ ] Página de aceptación de invitación (cuando backend esté listo)
  - `/auth/accept-invitation?token=xxx`
  - Formulario para completar registro si no tiene cuenta
  - O login directo si ya tiene cuenta
  - Mensaje de éxito y redirección

**Archivos a modificar/crear:**
- `frontend/src/app/(app)/settings/users/page.tsx` (mejorar)
- `frontend/src/app/(auth)/accept-invitation/page.tsx` (nuevo, cuando backend esté listo)

**Esfuerzo:** 2-3 horas (frontend básico), 3-4 horas adicionales cuando backend esté completo

---

#### 5. Limpieza y Optimizaciones ⏳ (2-3 horas)
**Ubicación:** Múltiples archivos

**Pendiente:**
- [ ] Limpiar código duplicado
  - `frontend/src/app/(app)/settings/organizations/page.tsx` tiene código duplicado
  - Revisar otros archivos similares

- [ ] Optimizar carga de datos
  - Usar `useGetOrganizationStats()` de forma eficiente
  - Evitar llamadas duplicadas
  - Implementar caché adecuado

- [ ] Mejorar manejo de errores
  - Mensajes más descriptivos
  - Manejo de errores de límites
  - Validación de permisos en UI

- [ ] Testing básico (opcional pero recomendado)
  - Tests E2E con Playwright para flujos críticos
  - Tests de componentes clave

**Esfuerzo:** 2-3 horas

---

### 📝 Resumen Frontend

| Tarea | Esfuerzo | Prioridad |
|-------|----------|-----------|
| Página de Detalle de Organización | 6-8 horas | Alta |
| Mejorar Página de Organizaciones | 4-6 horas | Alta |
| Validación de Límites en UI | 3-4 horas | Media |
| Sistema de Invitaciones en Frontend | 2-3 horas | Media |
| Limpieza y Optimizaciones | 2-3 horas | Baja |
| **TOTAL** | **17-24 horas (2-3 días)** | |

---

## 🎯 PLAN DE TRABAJO RECOMENDADO

### Fase 1: Backend - Sistema de Invitaciones (2-3 días)
**Prioridad:** Alta - Necesario para funcionalidad completa

1. Crear modelo y migración de `Invitation`
2. Crear repository y schemas
3. Implementar endpoints de invitaciones
4. Integrar envío de emails
5. Tests de integración

**Resultado:** Sistema de invitaciones completo funcionando

---

### Fase 2: Frontend - Páginas Principales (2 días)
**Prioridad:** Alta - Mejora UX significativamente

1. Crear página de detalle de organización
2. Mejorar página de organizaciones (limpiar código, agregar estadísticas)
3. Validación de límites en UI

**Resultado:** Gestión de organizaciones completa y profesional

---

### Fase 3: Frontend - Invitaciones y Polish (1-2 días)
**Prioridad:** Media - Completar funcionalidad

1. Mejorar UI de invitaciones
2. Crear página de aceptación de invitación
3. Limpieza y optimizaciones

**Resultado:** Sistema completo y pulido

---

### Fase 4: Backend - Tests y Documentación (1-2 días)
**Prioridad:** Baja - Mejora calidad pero no bloquea

1. Tests unitarios adicionales
2. Documentación API completa

**Resultado:** Código bien documentado y testeado

---

## 📊 RESUMEN TOTAL

### Backend
- **Esfuerzo restante:** 3.5-6 días
- **Componente principal faltante:** Sistema de invitaciones completo

### Frontend
- **Esfuerzo restante:** 2-3 días
- **Componente principal faltante:** Página de detalle y mejoras de UX

### Total para 100%
- **Esfuerzo total:** 5.5-9 días de desarrollo
- **Componentes críticos:** Sistema de invitaciones (backend) + Páginas de detalle (frontend)

---

## ✅ CHECKLIST FINAL

### Backend
- [ ] Modelo Invitation creado
- [ ] Endpoints de invitaciones completos
- [ ] Envío de emails funcionando
- [ ] Tests unitarios de OrganizationRepository
- [ ] Documentación API completa

### Frontend
- [ ] Página `/settings/organizations/[id]` creada
- [ ] Página de organizaciones mejorada
- [ ] Validación de límites implementada
- [ ] UI de invitaciones completa
- [ ] Página de aceptación de invitación
- [ ] Código limpio y optimizado

---

**Nota:** El backend está muy cerca del 100% (~95%). El frontend necesita más trabajo pero es principalmente UI/UX. El sistema funcional básico ya está operativo.

