# 📋 Tareas Pendientes - Sistema de Invitaciones

**Fecha:** 26 de Diciembre, 2025  
**Estado:** Backend ~95% completado | Frontend pendiente

---

## ✅ Completado (Backend)

1. ✅ Modelo `Invitation` en base de datos
2. ✅ Migración Alembic (`e5f6a7b8c9d0_add_invitations.py`)
3. ✅ Repository y schemas completos
4. ✅ Endpoints de invitaciones:
   - `POST /organizations/{id}/invitations` - Crear invitación
   - `GET /organizations/{id}/invitations` - Listar invitaciones
   - `DELETE /organizations/{id}/invitations/{invitation_id}` - Cancelar invitación
   - `POST /organizations/{id}/invitations/{token}/accept` - Aceptar invitación
5. ✅ Envío de emails de invitación (template HTML)
6. ✅ Endpoint existente actualizado para usar nuevo sistema

---

## ⏳ Pendiente

### Backend (5%)

#### 1. Tests de Integración (2-3 horas)
- [ ] Tests para `POST /organizations/{id}/invitations`
- [ ] Tests para `GET /organizations/{id}/invitations`
- [ ] Tests para `DELETE /organizations/{id}/invitations/{invitation_id}`
- [ ] Tests para `POST /organizations/{id}/invitations/{token}/accept`
- [ ] Tests de edge cases (expiración, duplicados, permisos)

**Archivos a crear:**
- `backend/tests/integration/test_invitations.py`

---

### Frontend (100% pendiente)

#### 1. Lista de Invitaciones Pendientes (2-3 horas)
**Ubicación:** `/settings/users` (agregar sección)

**Funcionalidades:**
- [ ] Nueva sección "Invitaciones Pendientes" en página de usuarios
- [ ] Tabla con: email, rol, fecha de invitación, estado, acciones
- [ ] Badge de estado (pendiente, aceptada, expirada)
- [ ] Botón para reenviar invitación
- [ ] Botón para cancelar invitación
- [ ] Filtros por estado (pending, accepted, expired)
- [ ] Indicador de expiración próxima

**Archivos a modificar:**
- `frontend/src/app/(app)/settings/users/page.tsx`

**Hooks necesarios:**
- `useGetInvitations(orgId, status?)` - Nuevo hook
- `useCancelInvitation()` - Nuevo hook
- `useResendInvitation()` - Nuevo hook (opcional)

---

#### 2. Página de Aceptación de Invitación (3-4 horas)
**Ubicación:** `/auth/accept-invitation` (nueva página)

**Funcionalidades:**
- [ ] Página pública para aceptar invitación con token
- [ ] Validar token al cargar página
- [ ] Si usuario no existe: formulario de registro (email, nombre, contraseña)
- [ ] Si usuario existe: confirmación y login automático
- [ ] Mostrar información de organización
- [ ] Mostrar rol que se asignará
- [ ] Manejo de errores (token inválido, expirado, ya aceptado)
- [ ] Redirección después de aceptar exitosamente
- [ ] Mensaje de éxito con información de la organización

**Archivos a crear:**
- `frontend/src/app/(auth)/accept-invitation/page.tsx`

**Hooks necesarios:**
- `useAcceptInvitation(token, data?)` - Nuevo hook

---

#### 3. Mejorar Dialog de Invitación (1 hora)
**Ubicación:** `/settings/users` (mejorar existente)

**Mejoras:**
- [ ] Mostrar mensaje de éxito con información de email enviado
- [ ] Opción para copiar link de invitación (si se muestra token)
- [ ] Instrucciones más claras
- [ ] Mejor feedback visual

**Archivos a modificar:**
- `frontend/src/app/(app)/settings/users/page.tsx`

---

## 📝 Notas

- El backend está funcional y listo para usar
- Los emails se envían automáticamente al crear invitación
- El endpoint de aceptación retorna JWT token para login automático
- La migración debe ejecutarse: `alembic upgrade head`
- Configurar `FRONTEND_URL` en `.env` para links de invitación

---

## 🎯 Prioridad

1. **Alta:** Página de aceptación de invitación (necesaria para que funcione el flujo completo)
2. **Media:** Lista de invitaciones pendientes (mejora UX significativa)
3. **Baja:** Tests de integración (calidad, no bloquea funcionalidad)

---

**Última actualización:** 26 de Diciembre, 2025






