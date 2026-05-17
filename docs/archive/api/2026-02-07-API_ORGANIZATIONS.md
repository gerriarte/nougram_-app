# API de Organizaciones - Documentación

**Versión:** 1.0  
**Base URL:** `/api/v1/organizations`

---

## Índice

1. [Endpoints de Organizaciones](#endpoints-de-organizaciones)
2. [Endpoints de Usuarios](#endpoints-de-usuarios)
3. [Endpoints de Estadísticas](#endpoints-de-estadísticas)
4. [Permisos y Roles](#permisos-y-roles)
5. [Códigos de Estado HTTP](#códigos-de-estado-http)
6. [Ejemplos de Uso](#ejemplos-de-uso)

---

## Endpoints de Organizaciones

### 1. GET /me

Obtiene la organización del usuario autenticado actual.

**Autenticación:** Requerida  
**Permisos:** Todos los usuarios autenticados

**Response 200 OK:**
```json
{
  "id": 1,
  "name": "Mi Organización",
  "slug": "mi-organizacion",
  "subscription_plan": "professional",
  "subscription_status": "active",
  "settings": {},
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-01-01T00:00:00Z",
  "user_count": 5
}
```

---

### 2. GET /

Lista organizaciones con paginación.

**Autenticación:** Requerida  
**Permisos:**
- **Super Admin:** Puede ver todas las organizaciones
- **Usuarios regulares:** Solo pueden ver su propia organización

**Query Parameters:**
- `page` (int, default: 1): Número de página
- `page_size` (int, default: 20, max: 100): Elementos por página
- `include_inactive` (bool, default: false): Incluir organizaciones inactivas

**Response 200 OK:**
```json
{
  "items": [
    {
      "id": 1,
      "name": "Organización 1",
      "slug": "org-1",
      "subscription_plan": "professional",
      "subscription_status": "active",
      "user_count": 5
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20,
  "total_pages": 1
}
```

---

### 3. GET /{organization_id}

Obtiene detalles de una organización específica por ID.

**Autenticación:** Requerida  
**Permisos:**
- **Super Admin:** Puede acceder a cualquier organización
- **Usuarios regulares:** Solo pueden acceder a su propia organización

**Response 200 OK:** Ver formato de `/me`  
**Response 403 Forbidden:** Sin permisos para acceder a esta organización  
**Response 404 Not Found:** Organización no encontrada

---

### 4. POST /

Crea una nueva organización (solo super admin).

**Autenticación:** Requerida  
**Permisos:** Solo Super Admin

**Request Body:**
```json
{
  "name": "Nueva Organización",
  "slug": "nueva-org",
  "subscription_plan": "professional",
  "subscription_status": "active",
  "settings": {}
}
```

**Response 201 Created:** Ver formato de `/me`  
**Response 400 Bad Request:** Slug duplicado o error de validación  
**Response 403 Forbidden:** Usuario no tiene permisos

**Nota:** Para registro público, use `POST /register` en su lugar.

---

### 5. POST /register

Registro público de nueva organización (sin autenticación requerida).

**Autenticación:** No requerida

**Request Body:**
```json
{
  "organization_name": "Mi Nueva Agencia",
  "organization_slug": "mi-nueva-agencia",
  "admin_email": "admin@agencia.com",
  "admin_full_name": "Juan Pérez",
  "admin_password": "password123456",
  "subscription_plan": "free"
}
```

**Response 201 Created:**
```json
{
  "organization": {
    "id": 1,
    "name": "Mi Nueva Agencia",
    "slug": "mi-nueva-agencia",
    "subscription_plan": "free",
    "subscription_status": "active"
  },
  "user": {
    "id": 1,
    "email": "admin@agencia.com",
    "full_name": "Juan Pérez",
    "role": "org_admin"
  },
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

**Response 400 Bad Request:** Slug duplicado, email ya registrado, o error de validación

---

### 6. PUT /{organization_id}

Actualiza una organización existente.

**Autenticación:** Requerida  
**Permisos:**
- **Super Admin:** Puede actualizar cualquier organización
- **Org Admin:** Puede actualizar su propia organización

**Request Body (todos los campos opcionales):**
```json
{
  "name": "Nombre Actualizado",
  "slug": "nuevo-slug",
  "settings": {
    "theme": "dark"
  }
}
```

**Nota:** Solo Super Admin puede actualizar `subscription_plan` y `subscription_status`.

**Response 200 OK:** Ver formato de `/me`  
**Response 403 Forbidden:** Sin permisos  
**Response 404 Not Found:** Organización no encontrada

---

### 7. DELETE /{organization_id}

Elimina (soft delete) una organización (solo super admin).

**Autenticación:** Requerida  
**Permisos:** Solo Super Admin

**Response 204 No Content:** Organización marcada como "cancelled"  
**Response 403 Forbidden:** Sin permisos  
**Response 404 Not Found:** Organización no encontrada

**Nota:** La organización no se elimina físicamente, solo se marca como `subscription_status: "cancelled"`.

---

## Endpoints de Usuarios

### 8. GET /{organization_id}/users

Lista usuarios de una organización.

**Autenticación:** Requerida  
**Permisos:**
- **Super Admin:** Puede ver usuarios de cualquier organización
- **Org Admin:** Puede ver usuarios de su propia organización

**Response 200 OK:**
```json
{
  "items": [
    {
      "id": 1,
      "email": "user@example.com",
      "full_name": "Usuario Ejemplo",
      "role": "org_member",
      "organization_id": 1,
      "created_at": "2025-01-01T00:00:00Z"
    }
  ],
  "total": 1
}
```

---

### 9. POST /{organization_id}/invite

Invita un usuario a unirse a la organización.

**Autenticación:** Requerida  
**Permisos:**
- **Super Admin:** Puede invitar a cualquier organización
- **Org Admin:** Puede invitar a su propia organización

**Request Body:**
```json
{
  "email": "newuser@example.com",
  "role": "org_member",
  "message": "Te invitamos a unirte a nuestra organización"
}
```

**Response 200 OK:**
```json
{
  "success": true,
  "message": "Invitation sent to newuser@example.com. Token: ...",
  "invitation_token": "abc123..."
}
```

**Nota:** Esta es una implementación simplificada. En producción se enviaría un email con el token.

---

### 10. POST /{organization_id}/users

Agrega un usuario a una organización.

**Autenticación:** Requerida  
**Permisos:**
- **Super Admin:** Puede agregar usuarios a cualquier organización
- **Org Admin:** Puede agregar usuarios a su propia organización

**Request Body:**

Opción 1: Agregar usuario existente
```json
{
  "user_id": 5,
  "role": "org_member"
}
```

Opción 2: Crear nuevo usuario
```json
{
  "email": "newuser@example.com",
  "full_name": "Nuevo Usuario",
  "password": "password123456",
  "role": "org_member"
}
```

**Response 201 Created:** Ver formato de `GET /users`  
**Response 403 Forbidden:** Sin permisos o límite de usuarios excedido  
**Response 404 Not Found:** Organización no encontrada

---

### 11. PUT /{organization_id}/users/{user_id}/role

Actualiza el rol de un usuario en la organización.

**Autenticación:** Requerida  
**Permisos:**
- **Super Admin:** Puede actualizar roles en cualquier organización
- **Org Admin:** Puede actualizar roles en su propia organización

**Request Body:**
```json
{
  "role": "org_admin"
}
```

**Roles válidos:**
- `org_admin`: Administrador de la organización
- `org_member`: Miembro regular

**Response 200 OK:** Ver formato de `GET /users`  
**Response 400 Bad Request:** No se puede remover el último org_admin  
**Response 403 Forbidden:** Sin permisos  
**Response 404 Not Found:** Usuario u organización no encontrados

---

### 12. DELETE /{organization_id}/users/{user_id}

Remueve un usuario de una organización.

**Autenticación:** Requerida  
**Permisos:**
- **Super Admin:** Puede remover usuarios de cualquier organización
- **Org Admin:** Puede remover usuarios de su propia organización

**Response 204 No Content:** Usuario removido exitosamente  
**Response 400 Bad Request:** No se puede auto-eliminar o remover último admin  
**Response 403 Forbidden:** Sin permisos  
**Response 404 Not Found:** Usuario u organización no encontrados

**Nota:** El usuario no se elimina, solo se remueve de la organización (organization_id se establece en null).

---

## Endpoints de Estadísticas

### 13. GET /{organization_id}/stats

Obtiene estadísticas de uso de una organización.

**Autenticación:** Requerida  
**Permisos:**
- **Super Admin:** Puede ver stats de cualquier organización
- **Org Admin:** Puede ver stats de su propia organización

**Response 200 OK:**
```json
{
  "organization_id": 1,
  "organization_name": "Mi Organización",
  "subscription_plan": "professional",
  "current_usage": {
    "users": 15,
    "projects": 45,
    "services": 80,
    "team_members": 25
  },
  "limits": {
    "users": 20,
    "projects": 100,
    "services": 200,
    "team_members": 50
  },
  "usage_percentage": {
    "users": 75.0,
    "projects": 45.0,
    "services": 40.0,
    "team_members": 50.0
  }
}
```

**Límites por plan:**
- **free:** 1 usuario, 5 proyectos, 10 servicios, 3 miembros de equipo
- **starter:** 5 usuarios, 25 proyectos, 50 servicios, 10 miembros de equipo
- **professional:** 20 usuarios, 100 proyectos, 200 servicios, 50 miembros de equipo
- **enterprise:** Ilimitado (-1)

---

### 14. PUT /{organization_id}/subscription

Actualiza el plan de suscripción de una organización (solo super admin).

**Autenticación:** Requerida  
**Permisos:** Solo Super Admin

**Request Body:**
```json
{
  "plan": "professional",
  "status": "active"
}
```

**Planes disponibles:**
- `free`
- `starter`
- `professional`
- `enterprise`

**Estados disponibles:**
- `active`
- `cancelled`
- `past_due`
- `trialing`

**Response 200 OK:** Ver formato de `/me`  
**Response 403 Forbidden:** Sin permisos  
**Response 404 Not Found:** Organización no encontrada

---

## Permisos y Roles

### Roles del Sistema

- **super_admin:** Acceso completo, puede gestionar todas las organizaciones
- **org_admin:** Administrador de organización, puede gestionar su propia organización
- **admin_financiero:** Equivalente a org_admin para gestión financiera
- **org_member:** Miembro regular de la organización
- **product_manager:** Rol de usuario regular (legacy)

### Matriz de Permisos

| Endpoint | super_admin | org_admin | org_member |
|----------|-------------|-----------|------------|
| GET /me | ✅ | ✅ | ✅ |
| GET / | ✅ (todas) | ✅ (solo propia) | ✅ (solo propia) |
| GET /{id} | ✅ (cualquiera) | ✅ (solo propia) | ✅ (solo propia) |
| POST / | ✅ | ❌ | ❌ |
| POST /register | ✅ (público) | ✅ (público) | ✅ (público) |
| PUT /{id} | ✅ (cualquiera) | ✅ (solo propia) | ❌ |
| DELETE /{id} | ✅ | ❌ | ❌ |
| GET /{id}/users | ✅ (cualquiera) | ✅ (solo propia) | ❌ |
| POST /{id}/invite | ✅ (cualquiera) | ✅ (solo propia) | ❌ |
| POST /{id}/users | ✅ (cualquiera) | ✅ (solo propia) | ❌ |
| PUT /{id}/users/{uid}/role | ✅ (cualquiera) | ✅ (solo propia) | ❌ |
| DELETE /{id}/users/{uid} | ✅ (cualquiera) | ✅ (solo propia) | ❌ |
| GET /{id}/stats | ✅ (cualquiera) | ✅ (solo propia) | ❌ |
| PUT /{id}/subscription | ✅ | ❌ | ❌ |

---

## Códigos de Estado HTTP

- **200 OK:** Operación exitosa
- **201 Created:** Recurso creado exitosamente
- **204 No Content:** Operación exitosa sin contenido de respuesta
- **400 Bad Request:** Error de validación o datos inválidos
- **401 Unauthorized:** No autenticado
- **403 Forbidden:** Autenticado pero sin permisos
- **404 Not Found:** Recurso no encontrado
- **500 Internal Server Error:** Error del servidor

---

## Ejemplos de Uso

### Registro de Nueva Organización

```bash
curl -X POST http://localhost:8000/api/v1/organizations/register \
  -H "Content-Type: application/json" \
  -d '{
    "organization_name": "Mi Agencia",
    "admin_email": "admin@agencia.com",
    "admin_full_name": "Juan Pérez",
    "admin_password": "password123456"
  }'
```

### Obtener Estadísticas de Uso

```bash
curl -X GET http://localhost:8000/api/v1/organizations/1/stats \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Agregar Usuario a Organización

```bash
curl -X POST http://localhost:8000/api/v1/organizations/1/users \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "nuevo@example.com",
    "full_name": "Nuevo Usuario",
    "password": "password123456",
    "role": "org_member"
  }'
```

---

**Última actualización:** 14 de Diciembre, 2025













