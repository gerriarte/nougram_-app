# 📋 Análisis de Tareas Pendientes - Sprint 6

**Fecha:** 19 de Diciembre, 2025  
**Estado:** Backend 95% completo | Frontend 40% completo

---

## ✅ Backend - Completado (95%)

### Endpoints de Organizaciones ✅
- ✅ `GET /organizations/me` - Obtener mi organización
- ✅ `GET /organizations/` - Listar organizaciones (con paginación)
- ✅ `GET /organizations/{id}` - Obtener organización por ID
- ✅ `POST /organizations/` - Crear organización (super admin)
- ✅ `POST /organizations/register` - Registro público de organización
- ✅ `PUT /organizations/{id}` - Actualizar organización
- ✅ `DELETE /organizations/{id}` - Eliminar organización
- ✅ `PUT /organizations/{id}/subscription` - Actualizar plan de suscripción

### Sistema de Invitaciones ✅
- ✅ `POST /organizations/{id}/invite` - Invitar usuario por email
- ✅ Genera token de invitación (simplificado, listo para emails)
- ✅ Validación de permisos (super admin o org admin)

### Gestión de Usuarios ✅
- ✅ `GET /organizations/{id}/users` - Listar usuarios de organización
- ✅ `POST /organizations/{id}/users` - Agregar usuario (crear nuevo o asignar existente)
- ✅ `PUT /organizations/{id}/users/{user_id}/role` - Actualizar rol de usuario
- ✅ `DELETE /organizations/{id}/users/{user_id}` - Remover usuario de organización

### Validación de Límites ✅
- ✅ `validate_user_limit()` - Validación de límite de usuarios por plan
- ✅ `validate_project_limit()` - Validación de límite de proyectos por plan
- ✅ `validate_service_limit()` - Validación de límite de servicios
- ✅ `validate_team_member_limit()` - Validación de límite de team members
- ✅ Integrado en endpoints de creación correspondientes

### Estadísticas ✅
- ✅ `GET /organizations/{id}/stats` - Estadísticas de uso (usuarios, proyectos, servicios, team members)

---

## ⚠️ Frontend - Pendiente (60% completo)

### Páginas Existentes

#### 1. `/settings/organizations` ✅ Básico
**Estado:** Funcional pero incompleto  
**Implementado:**
- ✅ Lista de organizaciones
- ✅ Visualización de plan y estado
- ✅ Actualización de plan de suscripción (dialog)
- ✅ Diferenciación entre super admin y usuario regular

**Falta:**
- ⚠️ Ver detalles de organización específica
- ❌ Ver usuarios de una organización
- ❌ Navegación a gestión de usuarios de organización
- ❌ Mostrar estadísticas de uso (stats endpoint)

#### 2. `/settings/users` ⚠️ Usa endpoints antiguos
**Estado:** Funcional pero NO usa endpoints de organizaciones  
**Problema:** Usa `useGetUsers()`, `useCreateUser()`, `useUpdateUserRole()` que probablemente apuntan a `/users/` en lugar de `/organizations/{id}/users`

**Implementado:**
- ✅ Lista de usuarios
- ✅ Crear usuario (dialog)
- ✅ Cambiar rol de usuario
- ✅ UI completa

**Falta:**
- ❌ Migrar a usar endpoints de organizaciones
- ❌ Usar `useGetOrganizationUsers()`, `useAddUserToOrganization()`, etc.
- ❌ Agregar funcionalidad de invitaciones
- ❌ Remover usuarios de organización

#### 3. Onboarding `/onboarding` ✅ Completo
**Estado:** Implementado para Sprint 6.5 (plantillas)
- ✅ Flujo multi-step
- ✅ Selección de plantilla
- ✅ Aplicación de plantilla

---

## ❌ Tareas Pendientes Priorizadas

### 🔴 Alta Prioridad

#### 1. Página de Registro Público de Organización
**Ubicación:** `/auth/register` (nueva página)  
**Estado:** ❌ No existe  
**Endpoint Backend:** ✅ `POST /organizations/register` existe  
**Descripción:** 
- Formulario público para registro de nueva organización
- Campos: organization_name, organization_slug (opcional), admin_email, admin_full_name, admin_password, subscription_plan (default: free)
- Después del registro, redirigir a login o directamente autenticar
- Integrar con flujo de onboarding (Sprint 6.5)

**Dependencias:** Ninguna  
**Esfuerzo:** 4-6 horas

---

#### 2. Migrar Página de Usuarios a Endpoints de Organizaciones
**Ubicación:** `/settings/users` (actualizar)  
**Estado:** ⚠️ Existe pero usa endpoints incorrectos  
**Cambios necesarios:**
- Cambiar `useGetUsers()` → `useGetOrganizationUsers(orgId)`
- Cambiar `useCreateUser()` → `useAddUserToOrganization()`
- Cambiar `useUpdateUserRole()` → `useUpdateUserRoleInOrganization()`
- Agregar `useRemoveUserFromOrganization()` para eliminar usuarios
- Obtener `organization_id` del usuario actual

**Dependencias:** Ninguna  
**Esfuerzo:** 3-4 horas

---

### 🟡 Media Prioridad

#### 3. Funcionalidad de Invitaciones en UI
**Ubicación:** `/settings/users` (agregar funcionalidad)  
**Estado:** ❌ No implementado en UI  
**Backend:** ✅ `POST /organizations/{id}/invite` existe  
**Descripción:**
- Dialog/formulario para invitar usuario por email
- Usar hook `useInviteUserToOrganization()`
- Mostrar token de invitación (temporal, hasta implementar emails)
- Agregar botón "Invitar Usuario" en página de usuarios

**Dependencias:** Tarea #2 completada  
**Esfuerzo:** 2-3 horas

---

#### 4. Mejorar Página de Organizaciones
**Ubicación:** `/settings/organizations` (mejorar)  
**Estado:** ⚠️ Básica  
**Mejoras necesarias:**
- Agregar vista de detalle de organización (dialog o nueva página)
- Mostrar usuarios de la organización (usando `useGetOrganizationUsers()`)
- Mostrar estadísticas de uso (usando `useGetOrganizationStats()`)
- Botón para navegar a gestión de usuarios de la organización
- Mejorar layout y organización de la información

**Dependencias:** Tarea #2 completada  
**Esfuerzo:** 4-5 horas

---

#### 5. Página de Detalle de Organización
**Ubicación:** `/settings/organizations/[id]` (nueva página)  
**Estado:** ❌ No existe  
**Descripción:**
- Vista completa de detalles de organización
- Sección de usuarios con gestión integrada
- Estadísticas de uso visuales (gráficos/badges)
- Configuración de organización
- Timeline/actividad reciente

**Dependencias:** Tareas #2 y #4  
**Esfuerzo:** 6-8 horas

---

### 🟢 Baja Prioridad

#### 6. Integración de Emails para Invitaciones
**Estado:** ❌ No implementado  
**Backend:** ⚠️ Endpoint existe pero no envía emails  
**Descripción:**
- Integrar servicio de emails (SendGrid, SES, etc.)
- Enviar email con link de invitación
- Manejar tokens de invitación en base de datos
- Expiración de invitaciones

**Dependencias:** Tarea #3  
**Esfuerzo:** 4-6 horas (depende de servicio de email)

---

#### 7. Validación de Límites en Frontend
**Estado:** ⚠️ Parcial  
**Descripción:**
- Mostrar límites actuales vs usados en UI
- Alertas cuando se acerca al límite
- Deshabilitar acciones cuando se alcanza el límite
- Mensajes informativos sobre upgrade de plan

**Backend:** ✅ Endpoint de stats existe  
**Dependencias:** Tarea #4  
**Esfuerzo:** 3-4 horas

---

## 📊 Resumen por Prioridad

### Alta Prioridad (Crítico para MVP)
1. ✅ Página de registro público (4-6h)
2. ✅ Migrar usuarios a endpoints de organizaciones (3-4h)
**Total:** 7-10 horas

### Media Prioridad (Mejora UX)
3. ✅ Funcionalidad de invitaciones (2-3h)
4. ✅ Mejorar página organizaciones (4-5h)
5. ✅ Página detalle organización (6-8h)
**Total:** 12-16 horas

### Baja Prioridad (Nice to have)
6. ⚠️ Emails de invitaciones (4-6h)
7. ⚠️ Validación de límites en frontend (3-4h)
**Total:** 7-10 horas

---

## 🎯 Recomendación de Implementación

### Fase 1: MVP (Alta Prioridad) - 7-10 horas
1. Crear página de registro público
2. Migrar página de usuarios a endpoints de organizaciones

**Resultado:** Funcionalidad básica completa para gestionar organizaciones y usuarios

### Fase 2: Mejoras UX (Media Prioridad) - 12-16 horas
3. Agregar funcionalidad de invitaciones
4. Mejorar página de organizaciones
5. Crear página de detalle de organización

**Resultado:** Experiencia completa y profesional

### Fase 3: Polish (Baja Prioridad) - 7-10 horas
6. Integrar emails
7. Validación de límites en frontend

**Resultado:** Experiencia premium

---

## 📝 Notas Técnicas

### Hooks Disponibles en Frontend
Los siguientes hooks ya están implementados en `frontend/src/lib/queries.ts`:
- ✅ `useGetOrganizationUsers(orgId)`
- ✅ `useInviteUserToOrganization()`
- ✅ `useAddUserToOrganization()`
- ✅ `useUpdateUserRoleInOrganization()`
- ✅ `useRemoveUserFromOrganization()` (verificar si existe)
- ✅ `useGetOrganizationStats(orgId)` (verificar si existe)

### Endpoints Backend Listos
Todos los endpoints necesarios están implementados y funcionando:
- ✅ Todos los endpoints de CRUD de organizaciones
- ✅ Todos los endpoints de gestión de usuarios
- ✅ Endpoint de invitaciones
- ✅ Endpoint de estadísticas
- ✅ Validación de límites integrada

---

**Conclusión:** El backend está prácticamente completo. El frontend necesita actualizarse para usar los endpoints correctos y agregar funcionalidades faltantes. Prioridad máxima: registro público y migración de usuarios.




**Fecha:** 19 de Diciembre, 2025  
**Estado:** Backend 95% completo | Frontend 40% completo

---

## ✅ Backend - Completado (95%)

### Endpoints de Organizaciones ✅
- ✅ `GET /organizations/me` - Obtener mi organización
- ✅ `GET /organizations/` - Listar organizaciones (con paginación)
- ✅ `GET /organizations/{id}` - Obtener organización por ID
- ✅ `POST /organizations/` - Crear organización (super admin)
- ✅ `POST /organizations/register` - Registro público de organización
- ✅ `PUT /organizations/{id}` - Actualizar organización
- ✅ `DELETE /organizations/{id}` - Eliminar organización
- ✅ `PUT /organizations/{id}/subscription` - Actualizar plan de suscripción

### Sistema de Invitaciones ✅
- ✅ `POST /organizations/{id}/invite` - Invitar usuario por email
- ✅ Genera token de invitación (simplificado, listo para emails)
- ✅ Validación de permisos (super admin o org admin)

### Gestión de Usuarios ✅
- ✅ `GET /organizations/{id}/users` - Listar usuarios de organización
- ✅ `POST /organizations/{id}/users` - Agregar usuario (crear nuevo o asignar existente)
- ✅ `PUT /organizations/{id}/users/{user_id}/role` - Actualizar rol de usuario
- ✅ `DELETE /organizations/{id}/users/{user_id}` - Remover usuario de organización

### Validación de Límites ✅
- ✅ `validate_user_limit()` - Validación de límite de usuarios por plan
- ✅ `validate_project_limit()` - Validación de límite de proyectos por plan
- ✅ `validate_service_limit()` - Validación de límite de servicios
- ✅ `validate_team_member_limit()` - Validación de límite de team members
- ✅ Integrado en endpoints de creación correspondientes

### Estadísticas ✅
- ✅ `GET /organizations/{id}/stats` - Estadísticas de uso (usuarios, proyectos, servicios, team members)

---

## ⚠️ Frontend - Pendiente (60% completo)

### Páginas Existentes

#### 1. `/settings/organizations` ✅ Básico
**Estado:** Funcional pero incompleto  
**Implementado:**
- ✅ Lista de organizaciones
- ✅ Visualización de plan y estado
- ✅ Actualización de plan de suscripción (dialog)
- ✅ Diferenciación entre super admin y usuario regular

**Falta:**
- ⚠️ Ver detalles de organización específica
- ❌ Ver usuarios de una organización
- ❌ Navegación a gestión de usuarios de organización
- ❌ Mostrar estadísticas de uso (stats endpoint)

#### 2. `/settings/users` ⚠️ Usa endpoints antiguos
**Estado:** Funcional pero NO usa endpoints de organizaciones  
**Problema:** Usa `useGetUsers()`, `useCreateUser()`, `useUpdateUserRole()` que probablemente apuntan a `/users/` en lugar de `/organizations/{id}/users`

**Implementado:**
- ✅ Lista de usuarios
- ✅ Crear usuario (dialog)
- ✅ Cambiar rol de usuario
- ✅ UI completa

**Falta:**
- ❌ Migrar a usar endpoints de organizaciones
- ❌ Usar `useGetOrganizationUsers()`, `useAddUserToOrganization()`, etc.
- ❌ Agregar funcionalidad de invitaciones
- ❌ Remover usuarios de organización

#### 3. Onboarding `/onboarding` ✅ Completo
**Estado:** Implementado para Sprint 6.5 (plantillas)
- ✅ Flujo multi-step
- ✅ Selección de plantilla
- ✅ Aplicación de plantilla

---

## ❌ Tareas Pendientes Priorizadas

### 🔴 Alta Prioridad

#### 1. Página de Registro Público de Organización
**Ubicación:** `/auth/register` (nueva página)  
**Estado:** ❌ No existe  
**Endpoint Backend:** ✅ `POST /organizations/register` existe  
**Descripción:** 
- Formulario público para registro de nueva organización
- Campos: organization_name, organization_slug (opcional), admin_email, admin_full_name, admin_password, subscription_plan (default: free)
- Después del registro, redirigir a login o directamente autenticar
- Integrar con flujo de onboarding (Sprint 6.5)

**Dependencias:** Ninguna  
**Esfuerzo:** 4-6 horas

---

#### 2. Migrar Página de Usuarios a Endpoints de Organizaciones
**Ubicación:** `/settings/users` (actualizar)  
**Estado:** ⚠️ Existe pero usa endpoints incorrectos  
**Cambios necesarios:**
- Cambiar `useGetUsers()` → `useGetOrganizationUsers(orgId)`
- Cambiar `useCreateUser()` → `useAddUserToOrganization()`
- Cambiar `useUpdateUserRole()` → `useUpdateUserRoleInOrganization()`
- Agregar `useRemoveUserFromOrganization()` para eliminar usuarios
- Obtener `organization_id` del usuario actual

**Dependencias:** Ninguna  
**Esfuerzo:** 3-4 horas

---

### 🟡 Media Prioridad

#### 3. Funcionalidad de Invitaciones en UI
**Ubicación:** `/settings/users` (agregar funcionalidad)  
**Estado:** ❌ No implementado en UI  
**Backend:** ✅ `POST /organizations/{id}/invite` existe  
**Descripción:**
- Dialog/formulario para invitar usuario por email
- Usar hook `useInviteUserToOrganization()`
- Mostrar token de invitación (temporal, hasta implementar emails)
- Agregar botón "Invitar Usuario" en página de usuarios

**Dependencias:** Tarea #2 completada  
**Esfuerzo:** 2-3 horas

---

#### 4. Mejorar Página de Organizaciones
**Ubicación:** `/settings/organizations` (mejorar)  
**Estado:** ⚠️ Básica  
**Mejoras necesarias:**
- Agregar vista de detalle de organización (dialog o nueva página)
- Mostrar usuarios de la organización (usando `useGetOrganizationUsers()`)
- Mostrar estadísticas de uso (usando `useGetOrganizationStats()`)
- Botón para navegar a gestión de usuarios de la organización
- Mejorar layout y organización de la información

**Dependencias:** Tarea #2 completada  
**Esfuerzo:** 4-5 horas

---

#### 5. Página de Detalle de Organización
**Ubicación:** `/settings/organizations/[id]` (nueva página)  
**Estado:** ❌ No existe  
**Descripción:**
- Vista completa de detalles de organización
- Sección de usuarios con gestión integrada
- Estadísticas de uso visuales (gráficos/badges)
- Configuración de organización
- Timeline/actividad reciente

**Dependencias:** Tareas #2 y #4  
**Esfuerzo:** 6-8 horas

---

### 🟢 Baja Prioridad

#### 6. Integración de Emails para Invitaciones
**Estado:** ❌ No implementado  
**Backend:** ⚠️ Endpoint existe pero no envía emails  
**Descripción:**
- Integrar servicio de emails (SendGrid, SES, etc.)
- Enviar email con link de invitación
- Manejar tokens de invitación en base de datos
- Expiración de invitaciones

**Dependencias:** Tarea #3  
**Esfuerzo:** 4-6 horas (depende de servicio de email)

---

#### 7. Validación de Límites en Frontend
**Estado:** ⚠️ Parcial  
**Descripción:**
- Mostrar límites actuales vs usados en UI
- Alertas cuando se acerca al límite
- Deshabilitar acciones cuando se alcanza el límite
- Mensajes informativos sobre upgrade de plan

**Backend:** ✅ Endpoint de stats existe  
**Dependencias:** Tarea #4  
**Esfuerzo:** 3-4 horas

---

## 📊 Resumen por Prioridad

### Alta Prioridad (Crítico para MVP)
1. ✅ Página de registro público (4-6h)
2. ✅ Migrar usuarios a endpoints de organizaciones (3-4h)
**Total:** 7-10 horas

### Media Prioridad (Mejora UX)
3. ✅ Funcionalidad de invitaciones (2-3h)
4. ✅ Mejorar página organizaciones (4-5h)
5. ✅ Página detalle organización (6-8h)
**Total:** 12-16 horas

### Baja Prioridad (Nice to have)
6. ⚠️ Emails de invitaciones (4-6h)
7. ⚠️ Validación de límites en frontend (3-4h)
**Total:** 7-10 horas

---

## 🎯 Recomendación de Implementación

### Fase 1: MVP (Alta Prioridad) - 7-10 horas
1. Crear página de registro público
2. Migrar página de usuarios a endpoints de organizaciones

**Resultado:** Funcionalidad básica completa para gestionar organizaciones y usuarios

### Fase 2: Mejoras UX (Media Prioridad) - 12-16 horas
3. Agregar funcionalidad de invitaciones
4. Mejorar página de organizaciones
5. Crear página de detalle de organización

**Resultado:** Experiencia completa y profesional

### Fase 3: Polish (Baja Prioridad) - 7-10 horas
6. Integrar emails
7. Validación de límites en frontend

**Resultado:** Experiencia premium

---

## 📝 Notas Técnicas

### Hooks Disponibles en Frontend
Los siguientes hooks ya están implementados en `frontend/src/lib/queries.ts`:
- ✅ `useGetOrganizationUsers(orgId)`
- ✅ `useInviteUserToOrganization()`
- ✅ `useAddUserToOrganization()`
- ✅ `useUpdateUserRoleInOrganization()`
- ✅ `useRemoveUserFromOrganization()` (verificar si existe)
- ✅ `useGetOrganizationStats(orgId)` (verificar si existe)

### Endpoints Backend Listos
Todos los endpoints necesarios están implementados y funcionando:
- ✅ Todos los endpoints de CRUD de organizaciones
- ✅ Todos los endpoints de gestión de usuarios
- ✅ Endpoint de invitaciones
- ✅ Endpoint de estadísticas
- ✅ Validación de límites integrada

---

**Conclusión:** El backend está prácticamente completo. El frontend necesita actualizarse para usar los endpoints correctos y agregar funcionalidades faltantes. Prioridad máxima: registro público y migración de usuarios.








