# Documento de Requerimientos de UI - Gestión de Usuarios

**Versión:** 1.0  
**Fecha:** 2026-01-23  
**Propósito:** Especificaciones técnicas para diseño UI de Gestión de Usuarios en Figma Make  
**Audiencia:** Diseñadores UI/UX, Desarrolladores Frontend

---

## Resumen Ejecutivo

Este documento especifica los requerimientos de interfaz de usuario para el módulo de **Gestión de Usuarios** que permite administrar miembros del equipo, roles, permisos e invitaciones. El sistema implementa un control de acceso granular basado en roles con dos niveles: **Support Roles** (multi-tenant) y **Tenant Roles** (usuarios de organización).

**⚠️ BRUTAL HONESTIDAD:** En una startup de servicios, la información financiera es confidencial. No todos los usuarios deben ver el Blended Cost Rate (BCR), salarios de otros miembros, o márgenes operacionales. Este documento define claramente qué información es visible para cada rol.

---

## 1. JERARQUÍA DE ROLES Y PERMISOS

### 1.1 Roles Disponibles

#### Support Roles (Multi-tenant Managers)
```typescript
type SupportRole = "super_admin" | "support_manager" | "data_analyst";
```

#### Tenant Roles (Client Users)
```typescript
type TenantRole = "owner" | "admin_financiero" | "product_manager" | "collaborator";
```

### 1.2 Matriz de Permisos Detallada

| Permiso | super_admin | owner | admin_financiero | product_manager | collaborator | support_manager | data_analyst |
|---------|-------------|-------|------------------|-----------------|--------------|-----------------|--------------|
| **Panel de Administración** |
| Ver BCR (Costo Hora Real) | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Ver Salarios de Miembros | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Ver Costos Fijos | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Ver Cargas Sociales | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Configurar Cargas Sociales | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Agregar/Editar Miembros | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Agregar/Editar Gastos Fijos | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Ver Amortización Equipos | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Cotizador** |
| Crear Proyectos | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| Crear Cotizaciones | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| Enviar Cotizaciones | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ |
| Ver Costo Interno | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Ver Margen Operacional | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Ver Análisis Rentabilidad | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Gestión de Usuarios** |
| Invitar Usuarios | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Cambiar Roles | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Ver Lista de Usuarios | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| Eliminar Usuarios | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Configuración** |
| Gestionar Suscripción | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Configurar Impuestos | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Ver Analytics | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ |
| Ver Proyecciones Financieras | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |

### 1.3 Descripción de Roles

#### Support Roles

**super_admin**
- **Descripción:** Control total de la plataforma
- **Acceso:** Todas las organizaciones
- **Puede:** Cualquier acción en cualquier organización
- **Restricciones:** Solo puede ser asignado a `gerardoriarte@gmail.com`
- **Uso:** Fundador/Gerente de la plataforma

**support_manager**
- **Descripción:** Gestor de Clientes
- **Acceso:** Múltiples organizaciones (datos anonimizados)
- **Puede:** Ver analytics, gestionar clientes
- **No Puede:** Ver datos sensibles (salarios, costos), modificar configuraciones financieras
- **Uso:** Equipo de soporte/customer success

**data_analyst**
- **Descripción:** Analista de Datos
- **Acceso:** Solo datasets anonimizados
- **Puede:** Ver analytics agregados
- **No Puede:** Ver información de usuarios, costos, o datos identificables
- **Uso:** Análisis de datos agregados

#### Tenant Roles

**owner**
- **Descripción:** Dueño de la cuenta
- **Acceso:** Su organización completa
- **Puede:** Todo en su organización (ver BCR, salarios, costos, gestionar suscripción, invitar usuarios)
- **Restricciones:** Solo puede gestionar su propia organización
- **Uso:** Fundador/Dueño del negocio cliente

**admin_financiero**
- **Descripción:** Administrador Financiero
- **Acceso:** Su organización (datos financieros)
- **Puede:** Ver BCR, salarios, costos, crear cotizaciones, enviar cotizaciones, configurar impuestos
- **No Puede:** Invitar usuarios, gestionar suscripción, eliminar recursos
- **Uso:** CFO/Contador/Administrador financiero

**product_manager**
- **Descripción:** Product Manager
- **Acceso:** Su organización (sin datos financieros)
- **Puede:** Crear proyectos, crear cotizaciones, enviar cotizaciones, ver analytics básicos
- **No Puede:** Ver BCR, salarios, costos, márgenes, proyecciones financieras
- **Uso:** PM que arma propuestas sin ver costos internos

**collaborator**
- **Descripción:** Colaborador
- **Acceso:** Su organización (muy limitado)
- **Puede:** Crear proyectos, crear borradores de cotizaciones
- **No Puede:** Enviar cotizaciones, ver costos, ver analytics, ver ninguna información financiera
- **Uso:** Diseñador/Desarrollador que colabora en propuestas

---

## 2. USER PROFILE DATA

### 2.1 Campos Actuales del Backend

```typescript
interface UserProfile {
  // Información básica (actual)
  id: number;
  email: string;                       // Email (único, usado para login)
  full_name: string;                   // Nombre completo
  role: string;                        // Rol del usuario
  organization_id: number | null;      // ID de organización
  has_calendar_connected: boolean;     // Si tiene Google Calendar conectado
}
```

### 2.2 Campos Propuestos para Perfil Completo

```typescript
interface UserProfileExtended {
  // Información básica (existente)
  id: number;
  email: string;
  full_name: string;
  role: string;
  organization_id: number | null;
  
  // Información de perfil (NUEVO - requerido para frontend)
  bio?: string;                        // Biografía profesional (opcional, max: 500 caracteres)
  photo_url?: string;                  // URL de foto de perfil (opcional)
  specialty?: string;                  // Especialidad (ej: "Diseño UI/UX", "Desarrollo Frontend")
  job_title?: string;                  // Cargo/Título (ej: "Senior Designer", "Product Manager")
  
  // Redes sociales (para propuestas)
  linkedin_url?: string;                // URL de LinkedIn (opcional)
  portfolio_url?: string;               // URL de portfolio personal (opcional)
  github_url?: string;                  // URL de GitHub (opcional)
  behance_url?: string;                 // URL de Behance (opcional)
  
  // Preferencias
  timezone?: string;                    // Zona horaria (ej: "America/Bogota")
  language?: string;                    // Idioma preferido (ej: "es", "en")
  
  // Metadatos
  created_at: string;                   // ISO format
  updated_at: string;                   // ISO format
  last_login_at?: string;               // Último inicio de sesión (ISO format)
}
```

**Nota:** Los campos extendidos (`bio`, `photo_url`, `specialty`, etc.) aún no existen en el backend. Deben implementarse en una fase futura o el frontend puede almacenarlos localmente/separadamente.

### 2.3 Campos Visibles por Rol

#### Campos Siempre Visibles (Todos los Roles)
- Nombre completo (`full_name`)
- Email (`email`)
- Rol (`role`) - con badge de color
- Foto de perfil (`photo_url`) - si existe
- Especialidad (`specialty`) - si existe

#### Campos Solo para Owner/Admin
- `organization_id`
- `has_calendar_connected`
- `last_login_at`
- `created_at`
- `updated_at`

#### Campos Solo para el Usuario Mismo
- Redes sociales (LinkedIn, Portfolio, GitHub, Behance)
- Biografía completa
- Preferencias (timezone, language)

---

## 3. GESTIÓN DE EQUIPO (INVITACIONES)

### 3.1 Flujo de Invitación

```
┌─────────────────────────────────────────────────────────────┐
│  FLUJO DE INVITACIÓN DE USUARIOS                            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. Owner/Super Admin hace click en "Invitar Miembro"       │
│     ↓                                                        │
│  2. Modal se abre con formulario:                           │
│     • Email (requerido)                                     │
│     • Rol (dropdown: owner, admin_financiero,              │
│       product_manager, collaborator)                        │
│     • Mensaje opcional                                      │
│     ↓                                                        │
│  3. Sistema valida:                                         │
│     • Email no está ya en la organización                   │
│     • No hay invitación pendiente                           │
│     • Usuario tiene permiso para invitar                    │
│     ↓                                                        │
│  4. Se crea invitación con:                                 │
│     • Token único                                           │
│     • Fecha de expiración (7 días por defecto)              │
│     • Estado: "pending"                                     │
│     ↓                                                        │
│  5. Email se envía al invitado con link:                    │
│     /accept-invitation?token=XXX                            │
│     ↓                                                        │
│  6. Invitado hace click en link:                            │
│     • Si es usuario nuevo: crea cuenta                       │
│     • Si es usuario existente: agrega a organización        │
│     • Asigna rol especificado                               │
│     • Marca invitación como "accepted"                      │
│     ↓                                                        │
│  7. Usuario puede iniciar sesión                            │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Data Mapping - Invitación

#### Crear Invitación
```typescript
interface InvitationCreate {
  email: string;                        // Email del invitado (requerido)
  role: "owner" | "admin_financiero" | "product_manager" | "collaborator"; // Rol a asignar (default: "collaborator")
  message?: string;                     // Mensaje personalizado (opcional, max: 500 caracteres)
}
```

#### Respuesta de Invitación
```typescript
interface InvitationResponse {
  id: number;
  email: string;
  role: string;
  organization_id: number;
  status: "pending" | "accepted" | "expired" | "cancelled";
  expires_at: string;                  // ISO format
  created_at: string;                   // ISO format
  created_by_name?: string;             // Nombre de quien creó la invitación
}
```

#### Aceptar Invitación
```typescript
interface InvitationAcceptRequest {
  token: string;                        // Token de la invitación (del URL)
  password?: string;                    // Requerido si es usuario nuevo (min: 8 caracteres)
  full_name?: string;                   // Requerido si es usuario nuevo
}

interface InvitationAcceptResponse {
  success: boolean;
  message: string;
  access_token?: string;                // JWT token para login automático
  user_id?: number;
  organization_id?: number;
}
```

### 3.3 Estados de Invitación

#### Estados Visuales
```typescript
type InvitationStatus = "pending" | "accepted" | "expired" | "cancelled";

const STATUS_CONFIG: Record<InvitationStatus, {
  label: string;
  color: string;
  icon: string;
  badgeColor: string;
}> = {
  pending: {
    label: "Pendiente",
    color: "#3B82F6",      // Azul
    icon: "Clock",
    badgeColor: "bg-blue-100 text-blue-700"
  },
  accepted: {
    label: "Aceptada",
    color: "#10B981",      // Verde
    icon: "CheckCircle",
    badgeColor: "bg-green-100 text-green-700"
  },
  expired: {
    label: "Expirada",
    color: "#6B7280",      // Gris
    icon: "XCircle",
    badgeColor: "bg-grey-100 text-grey-700"
  },
  cancelled: {
    label: "Cancelada",
    color: "#DC2626",      // Rojo
    icon: "Ban",
    badgeColor: "bg-red-100 text-red-700"
  }
};
```

---

## 4. SEGURIDAD Y SESIÓN

### 4.1 Estados de Cuenta

```typescript
interface AccountStatus {
  is_active: boolean;                   // Cuenta activa (default: true)
  is_suspended: boolean;                // Cuenta suspendida (futuro)
  is_email_verified: boolean;           // Email verificado (futuro)
  last_login_at?: string;               // Último inicio de sesión (ISO format)
  login_count?: number;                 // Número de logins (futuro)
}
```

### 4.2 Cambio de Contraseña

#### Cambiar Contraseña (Usuario Actual)
```typescript
interface ChangePasswordRequest {
  current_password: string;             // Contraseña actual (requerido)
  new_password: string;                 // Nueva contraseña (min: 8 caracteres)
  confirm_password: string;             // Confirmar nueva contraseña
}
```

#### Resetear Contraseña (Admin)
```typescript
interface ResetPasswordRequest {
  user_id: number;                       // ID del usuario
  new_password: string;                  // Nueva contraseña (min: 8 caracteres)
  send_email?: boolean;                  // Enviar email con nueva contraseña (default: true)
}
```

**Permisos:** Solo `super_admin` puede resetear contraseñas de otros usuarios.

### 4.3 Autenticación

#### Login
```typescript
interface LoginRequest {
  email: string;
  password: string;
}

interface LoginResponse {
  access_token: string;                 // JWT token
  token_type: "bearer";
  expires_in: number;                    // Segundos (ej: 3600 = 1 hora)
  user: {
    id: number;
    email: string;
    full_name: string;
    role: string;
    organization_id: number | null;
  };
}
```

#### OAuth (Google)
```typescript
interface GoogleLoginRequest {
  code: string;                          // Código de autorización OAuth
}
```

---

## 5. ESPECIFICACIONES DE PANTALLAS

### 5.1 Pantalla: Lista de Miembros del Equipo

#### Estructura Visual

```
┌─────────────────────────────────────────────────────────────┐
│  MIEMBROS DEL EQUIPO                          [Invitar Miembro] │ ← Botón destacado
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  [Filtros: Todos | Activos | Por Rol]                       │
│  [Búsqueda: Buscar por nombre o email...]                   │
│                                                              │
├─────────────────────────────────────────────────────────────┤
│  Avatar │ Nombre          │ Rol          │ Estado │ Acciones │
├─────────────────────────────────────────────────────────────┤
│  [👤]   │ Juan Pérez      │ [Owner]      │ Activo │ [⋮]      │
│         │ juan@example.com│              │        │          │
├─────────────────────────────────────────────────────────────┤
│  [👤]   │ María García    │ [Admin Fin.] │ Activo │ [⋮]      │
│         │ maria@example.com│             │        │          │
├─────────────────────────────────────────────────────────────┤
│  [👤]   │ Carlos López    │ [PM]         │ Activo │ [⋮]      │
│         │ carlos@example.com│            │        │          │
├─────────────────────────────────────────────────────────────┤
│  [👤]   │ Ana Martínez    │ [Collaborator]│ Activo │ [⋮]      │
│         │ ana@example.com │              │        │          │
└─────────────────────────────────────────────────────────────┘
```

#### Componentes Requeridos

**Tabla de Usuarios:**
- **Avatar:** Foto de perfil o iniciales en círculo
- **Nombre:** Nombre completo + email debajo (texto secundario)
- **Rol:** Badge con color según rol:
  - `owner`: Verde (#10B981)
  - `admin_financiero`: Azul (#3B82F6)
  - `product_manager`: Púrpura (#8B5CF6)
  - `collaborator`: Gris (#6B7280)
- **Estado:** Badge "Activo" o "Inactivo"
- **Acciones:** Menú dropdown (⋮) con opciones según permisos:
  - Ver Perfil
  - Editar Rol (solo owner/super_admin)
  - Eliminar (solo owner/super_admin)
  - Suspender (futuro)

**Filtros:**
- Dropdown: "Todos", "Activos", "Inactivos"
- Dropdown: "Todos los roles", "Owner", "Admin Financiero", etc.
- Input de búsqueda con icono de lupa

**Paginación:**
- Mostrar "Mostrando 1-20 de 45"
- Botones: Anterior, Siguiente
- Selector de items por página: 20, 50, 100

#### Permisos de Visualización

**Columnas Visibles por Rol:**

| Columna | owner | admin_financiero | product_manager | collaborator |
|---------|-------|------------------|-----------------|--------------|
| Avatar | ✅ | ✅ | ✅ | ✅ |
| Nombre | ✅ | ✅ | ✅ | ✅ |
| Email | ✅ | ✅ | ✅ | ✅ |
| Rol | ✅ | ✅ | ✅ | ✅ |
| Estado | ✅ | ✅ | ✅ | ✅ |
| Último Login | ✅ | ✅ | ❌ | ❌ |
| Organización | ✅ | ❌ | ❌ | ❌ |
| Acciones | ✅ | ✅ (limitado) | ❌ | ❌ |

**Acciones Disponibles:**
- **owner/super_admin:** Ver, Editar Rol, Eliminar, Suspender
- **admin_financiero:** Ver (solo)
- **product_manager/collaborator:** Ver (solo, sin acciones)

### 5.2 Pantalla: Modal de Invitación

#### Estructura Visual

```
┌─────────────────────────────────────┐
│  Invitar Miembro al Equipo      [×] │
├─────────────────────────────────────┤
│                                     │
│  Email del Invitado                 │
│  [Input: email@example.com]         │
│  ℹ️ Se enviará un email de invitación│
│                                     │
│  Rol a Asignar                       │
│  [Dropdown: Seleccionar rol...]     │
│  • Owner                            │
│  • Admin Financiero                 │
│  • Product Manager                  │
│  • Collaborator                     │
│                                     │
│  Mensaje Personalizado (Opcional)  │
│  [Textarea: Escribe un mensaje...] │
│  [0/500 caracteres]                 │
│                                     │
│  ─────────────────────────────────── │
│                                     │
│  [Cancelar]  [Enviar Invitación]    │
└─────────────────────────────────────┘
```

#### Validaciones en Tiempo Real

**Email:**
- Validar formato de email
- Verificar si ya existe en organización (mostrar error)
- Verificar si hay invitación pendiente (mostrar advertencia)

**Rol:**
- Solo mostrar roles que el usuario actual puede asignar
- Owner puede asignar: admin_financiero, product_manager, collaborator
- Super_admin puede asignar: owner, admin_financiero, product_manager, collaborator

**Mensaje:**
- Máximo 500 caracteres
- Contador de caracteres visible

#### Estados del Modal

**Estado: Cargando**
```
┌─────────────────────────────────────┐
│  Invitar Miembro al Equipo      [×] │
├─────────────────────────────────────┤
│                                     │
│  🔄 Enviando invitación...          │
│                                     │
└─────────────────────────────────────┘
```

**Estado: Éxito**
```
┌─────────────────────────────────────┐
│  Invitar Miembro al Equipo      [×] │
├─────────────────────────────────────┤
│                                     │
│  ✅ Invitación enviada exitosamente │
│                                     │
│  Se ha enviado un email a:          │
│  email@example.com                  │
│                                     │
│  El invitado recibirá un link para  │
│  unirse a la organización.          │
│                                     │
│  [Cerrar]                           │
└─────────────────────────────────────┘
```

**Estado: Error**
```
┌─────────────────────────────────────┐
│  Invitar Miembro al Equipo      [×] │
├─────────────────────────────────────┤
│                                     │
│  ❌ Error al enviar invitación       │
│                                     │
│  Este usuario ya es miembro de la   │
│  organización.                      │
│                                     │
│  [Cerrar]  [Reintentar]             │
└─────────────────────────────────────┘
```

### 5.3 Pantalla: Mi Perfil (User Settings)

#### Estructura Visual (Layout de Dos Columnas)

```
┌─────────────────────────────────────────────────────────────┐
│  MI PERFIL                                                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────┐  ┌─────────────────────────────────┐ │
│  │                  │  │  Información Personal             │ │
│  │   [Avatar]      │  │  ─────────────────────────────── │ │
│  │                  │  │                                   │ │
│  │  [Cambiar Foto] │  │  Nombre Completo                  │ │
│  │                  │  │  [Input: Juan Pérez]              │ │
│  │                  │  │                                   │ │
│  │                  │  │  Email                            │ │
│  │                  │  │  juan@example.com (read-only)     │ │
│  │                  │  │                                   │ │
│  │                  │  │  Especialidad                     │ │
│  │                  │  │  [Input: Diseño UI/UX]            │ │
│  │                  │  │                                   │ │
│  │                  │  │  Cargo                            │ │
│  │                  │  │  [Input: Senior Designer]         │ │
│  │                  │  │                                   │ │
│  │                  │  │  Biografía                        │ │
│  │                  │  │  [Textarea: Escribe tu bio...]   │ │
│  │                  │  │  [0/500 caracteres]                │ │
│  └──────────────────┘  └─────────────────────────────────┘ │
│                                                              │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  Redes Sociales (para propuestas)                       │ │
│  ├─────────────────────────────────────────────────────────┤ │
│  │                                                          │ │
│  │  LinkedIn                                                │ │
│  │  [Input: linkedin.com/in/juanperez]                     │ │
│  │                                                          │ │
│  │  Portfolio                                               │ │
│  │  [Input: juanperez.design]                              │ │
│  │                                                          │ │
│  │  GitHub                                                  │ │
│  │  [Input: github.com/juanperez]                          │ │
│  │                                                          │ │
│  │  Behance                                                 │ │
│  │  [Input: behance.net/juanperez]                          │ │
│  │                                                          │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  Seguridad y Sesión                                      │ │
│  ├─────────────────────────────────────────────────────────┤ │
│  │                                                          │ │
│  │  Estado de Cuenta                                       │ │
│  │  ✅ Activa                                               │ │
│  │  Último inicio de sesión: Hace 2 horas                   │ │
│  │                                                          │ │
│  │  Cambiar Contraseña                                     │ │
│  │  [Botón: Cambiar Contraseña]                            │ │
│  │                                                          │ │
│  │  Conectar Google Calendar                                │ │
│  │  [Botón: Conectar] (si no conectado)                    │ │
│  │  ✅ Conectado (si ya conectado)                          │ │
│  │                                                          │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  Preferencias                                            │ │
│  ├─────────────────────────────────────────────────────────┤ │
│  │                                                          │ │
│  │  Zona Horaria                                            │ │
│  │  [Dropdown: America/Bogota]                              │ │
│  │                                                          │ │
│  │  Idioma                                                  │ │
│  │  [Dropdown: Español]                                     │ │
│  │                                                          │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                              │
│  [Cancelar]  [Guardar Cambios]                              │
└─────────────────────────────────────────────────────────────┘
```

#### Modal: Cambiar Contraseña

```
┌─────────────────────────────────────┐
│  Cambiar Contraseña             [×] │
├─────────────────────────────────────┤
│                                     │
│  Contraseña Actual                  │
│  [Input: ••••••••] (password type)  │
│                                     │
│  Nueva Contraseña                   │
│  [Input: ••••••••] (password type)  │
│  ℹ️ Mínimo 8 caracteres              │
│                                     │
│  Confirmar Nueva Contraseña         │
│  [Input: ••••••••] (password type)  │
│                                     │
│  ─────────────────────────────────── │
│                                     │
│  [Cancelar]  [Cambiar Contraseña]   │
└─────────────────────────────────────┘
```

**Validaciones:**
- Contraseña actual debe ser correcta
- Nueva contraseña mínimo 8 caracteres
- Nueva contraseña y confirmación deben coincidir
- Nueva contraseña debe ser diferente a la actual

### 5.4 Pantalla: Lista de Invitaciones

#### Estructura Visual

```
┌─────────────────────────────────────────────────────────────┐
│  INVITACIONES PENDIENTES                    [Invitar Miembro] │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  [Filtros: Todas | Pendientes | Aceptadas | Expiradas]      │
│                                                              │
├─────────────────────────────────────────────────────────────┤
│  Email              │ Rol          │ Estado    │ Fecha    │ Acciones │
├─────────────────────────────────────────────────────────────┤
│  nuevo@example.com  │ Collaborator │ Pendiente │ Hace 2d  │ [Cancelar]│
│  Invitado por: Juan Pérez                                    │
│  Expira: 23/01/2026                                          │
├─────────────────────────────────────────────────────────────┤
│  otro@example.com   │ Product Mgr  │ Aceptada  │ Hace 5d  │ [Ver]     │
│  Aceptada: 20/01/2026                                        │
├─────────────────────────────────────────────────────────────┤
│  expirado@example.com│ Collaborator│ Expirada │ Hace 10d │ [Reenviar]│
└─────────────────────────────────────────────────────────────┘
```

**Acciones Disponibles:**
- **Pendiente:** Cancelar, Reenviar
- **Aceptada:** Ver detalles (read-only)
- **Expirada:** Reenviar, Cancelar

---

## 6. VISIBILIDAD DE INFORMACIÓN SENSIBLE

### 6.1 ⚠️ BRUTAL HONESTIDAD: Qué NO Debe Ver Cada Rol

#### Collaborator y Product Manager
**NO PUEDEN VER:**
- ❌ Blended Cost Rate (BCR)
- ❌ Salarios de otros miembros del equipo
- ❌ Costos fijos (overhead, herramientas)
- ❌ Cargas sociales
- ❌ Márgenes operacionales
- ❌ Análisis de rentabilidad
- ❌ Proyecciones financieras
- ❌ Configuración de impuestos (solo pueden ver qué impuestos aplicar, no los porcentajes)

**PUEDEN VER:**
- ✅ Lista de miembros (solo nombre, rol, email)
- ✅ Crear y editar proyectos
- ✅ Crear cotizaciones (sin ver costo interno)
- ✅ Precio al cliente (sin margen)
- ✅ Analytics básicos (sin datos financieros)

#### Admin Financiero
**NO PUEDEN VER:**
- ❌ Salarios de otros miembros (solo puede ver el total agregado)
- ❌ Información personal de otros usuarios (redes sociales, bio)
- ❌ Invitar usuarios
- ❌ Gestionar suscripción

**PUEDEN VER:**
- ✅ BCR completo
- ✅ Costos fijos
- ✅ Cargas sociales
- ✅ Márgenes operacionales
- ✅ Análisis de rentabilidad
- ✅ Proyecciones financieras

#### Owner
**PUEDE VER TODO:**
- ✅ BCR completo
- ✅ Salarios individuales de todos los miembros
- ✅ Costos fijos
- ✅ Cargas sociales
- ✅ Márgenes operacionales
- ✅ Análisis de rentabilidad
- ✅ Proyecciones financieras
- ✅ Gestionar usuarios e invitaciones
- ✅ Gestionar suscripción

### 6.2 Indicadores Visuales de Restricción

#### Badge de "Información Confidencial"
```
┌─────────────────────────────────────┐
│  🔒 Información Confidencial         │
│  Solo visible para Owner y           │
│  Admin Financiero                    │
└─────────────────────────────────────┘
```

#### Overlay de Blur (Opcional)
Para información que el usuario no puede ver, mostrar con blur y mensaje:
```
┌─────────────────────────────────────┐
│  [Blurred Content]                   │
│  ─────────────────────────────────── │
│  🔒 No tienes permisos para ver      │
│     esta información                 │
└─────────────────────────────────────┘
```

---

## 7. ESPECIFICACIONES DE DISEÑO

### 7.1 Paleta de Colores para Roles

```typescript
const ROLE_COLORS: Record<string, {
  background: string;
  text: string;
  border: string;
}> = {
  super_admin: {
    background: "#FEF3C7",  // Amarillo claro
    text: "#92400E",         // Amarillo oscuro
    border: "#F59E0B"       // Ámbar
  },
  owner: {
    background: "#D1FAE5",  // Verde claro
    text: "#065F46",        // Verde oscuro
    border: "#10B981"       // Verde
  },
  admin_financiero: {
    background: "#DBEAFE",  // Azul claro
    text: "#1E40AF",        // Azul oscuro
    border: "#3B82F6"       // Azul
  },
  product_manager: {
    background: "#EDE9FE",  // Púrpura claro
    text: "#5B21B6",        // Púrpura oscuro
    border: "#8B5CF6"       // Púrpura
  },
  collaborator: {
    background: "#F3F4F6",  // Gris claro
    text: "#374151",        // Gris oscuro
    border: "#6B7280"       // Gris
  },
  support_manager: {
    background: "#FCE7F3",  // Rosa claro
    text: "#9F1239",        // Rosa oscuro
    border: "#EC4899"       // Rosa
  },
  data_analyst: {
    background: "#E0E7FF",  // Índigo claro
    text: "#3730A3",        // Índigo oscuro
    border: "#6366F1"       // Índigo
  }
};
```

### 7.2 Tipografía

- **H1 (Título de Pantalla):** 32px, Bold
- **H2 (Títulos de Sección):** 24px, Semibold
- **H3 (Subtítulos):** 18px, Medium
- **Body (Texto normal):** 16px, Regular
- **Small (Texto secundario):** 14px, Regular
- **Caption (Etiquetas):** 12px, Regular

### 7.3 Componentes UI Requeridos

#### Badge de Rol
```
┌──────────────────┐
│ [Background Color]│
│ Owner            │ ← Texto con color de texto
└──────────────────┘
```

**Estados:**
- Hover: Sombra ligera
- Click: N/A (no interactivo)

#### Avatar
```
┌─────────┐
│   👤    │ ← Foto o iniciales
└─────────┘
```

**Variantes:**
- Con foto: Mostrar imagen redondeada
- Sin foto: Mostrar iniciales en círculo con color de fondo según nombre
- Tamaños: `sm` (32px), `md` (48px), `lg` (64px)

#### Tabla de Usuarios
- Filas alternadas con fondo gris muy claro (#F9FAFB)
- Hover effect en filas (fondo gris claro #F3F4F6)
- Acciones en columna derecha con icono de menú (⋮)
- Responsive: En mobile, convertir a cards apilados

#### Modal de Invitación
- Overlay oscuro (backdrop blur opcional)
- Modal centrado con sombra
- Botón de cerrar (×) en esquina superior derecha
- Botones de acción alineados a la derecha
- Validación inline debajo de cada campo

---

## 8. PROMPT PARA FIGMA MAKE

```
Diseña un módulo completo de Gestión de Usuarios para una plataforma de cotización que incluya las siguientes pantallas:

**Pantalla 1: Lista de Miembros del Equipo**
- Header con título "Miembros del Equipo" y botón destacado "Invitar Miembro"
- Tabla con columnas: Avatar, Nombre (con email debajo), Rol (badge con color), Estado, Acciones
- Filtros: Dropdown para filtrar por estado (Todos/Activos/Inactivos) y por rol
- Búsqueda: Input con icono de lupa para buscar por nombre o email
- Paginación: Mostrar "Mostrando X-Y de Z" con botones Anterior/Siguiente
- Badges de rol con colores específicos:
  • Owner: Verde (#10B981)
  • Admin Financiero: Azul (#3B82F6)
  • Product Manager: Púrpura (#8B5CF6)
  • Collaborator: Gris (#6B7280)
- Menú de acciones (⋮) con opciones según permisos del usuario actual

**Pantalla 2: Modal de Invitación**
- Título: "Invitar Miembro al Equipo"
- Campo Email (requerido) con validación en tiempo real
- Dropdown de Rol con opciones: Owner, Admin Financiero, Product Manager, Collaborator
- Textarea para mensaje personalizado (opcional, max 500 caracteres)
- Botones: Cancelar (outline) y "Enviar Invitación" (primary)
- Estados: Cargando (spinner), Éxito (checkmark + mensaje), Error (X + mensaje)

**Pantalla 3: Mi Perfil (Layout de Dos Columnas)**
- Columna Izquierda:
  • Avatar grande (64px) con botón "Cambiar Foto"
  • Información básica visible
- Columna Derecha:
  • Sección "Información Personal": Nombre, Email (read-only), Especialidad, Cargo, Biografía
  • Sección "Redes Sociales": LinkedIn, Portfolio, GitHub, Behance (para propuestas)
  • Sección "Seguridad y Sesión": Estado de cuenta, Último login, Botón "Cambiar Contraseña"
  • Sección "Preferencias": Zona horaria, Idioma
- Botones: Cancelar y "Guardar Cambios" al final

**Pantalla 4: Modal Cambiar Contraseña**
- Título: "Cambiar Contraseña"
- Campo "Contraseña Actual" (password type)
- Campo "Nueva Contraseña" (password type) con indicador de fortaleza
- Campo "Confirmar Nueva Contraseña" (password type)
- Validaciones inline debajo de cada campo
- Botones: Cancelar y "Cambiar Contraseña"

**Pantalla 5: Lista de Invitaciones**
- Tabla con: Email, Rol, Estado (badge con color), Fecha, Acciones
- Estados de invitación con colores:
  • Pendiente: Azul
  • Aceptada: Verde
  • Expirada: Gris
  • Cancelada: Rojo
- Acciones según estado: Cancelar, Reenviar, Ver

**Restricciones de Visibilidad (CRÍTICO):**
- Collaborator y Product Manager NO deben ver:
  • BCR (Costo Hora Real)
  • Salarios de otros miembros
  • Costos fijos
  • Márgenes operacionales
  • Análisis de rentabilidad
- Mostrar badge "🔒 Información Confidencial" o blur en información restringida
- Owner y Admin Financiero ven todo
- Admin Financiero NO puede invitar usuarios ni gestionar suscripción

**Paleta de Colores:**
- Primario: #3B82F6 (Azul)
- Éxito: #10B981 (Verde)
- Advertencia: #F59E0B (Ámbar)
- Error: #DC2626 (Rojo)
- Colores de roles según tabla de colores especificada

**Tipografía:**
- Títulos: 24-32px, Bold/Semibold
- Texto normal: 16px, Regular
- Texto secundario: 14px, Regular

**Estados a Diseñar:**
- Cargando (skeleton loaders)
- Error (mensajes de error)
- Vacío (empty states)
- Con datos (estado normal)
- Validación de formularios (errores inline)
```

---

## 9. ENDPOINTS DEL BACKEND

### 9.1 Gestión de Usuarios

#### Listar Usuarios de Organización
**Endpoint:** `GET /api/v1/organizations/{organization_id}/users`

**Permisos:** 
- Owner: Puede ver usuarios de su organización
- Super_admin: Puede ver usuarios de cualquier organización
- Otros roles: Pueden ver lista básica (sin información sensible)

**Response:**
```typescript
interface OrganizationUsersListResponse {
  items: Array<{
    id: number;
    email: string;
    full_name: string;
    role: string;
    organization_id: number;
    created_at?: string;
  }>;
  total: number;
}
```

#### Obtener Usuario Actual
**Endpoint:** `GET /api/v1/auth/me`

**Response:** `UserResponse`

#### Actualizar Perfil
**Endpoint:** `PUT /api/v1/auth/me`

**Request:** `UserUpdate` (solo `full_name` actualmente)

### 9.2 Invitaciones

#### Crear Invitación
**Endpoint:** `POST /api/v1/organizations/{organization_id}/invitations`

**Permisos:** Requiere `can_invite_users`
- ✅ Roles permitidos: owner, super_admin

**Request:** `InvitationCreate`

**Response:** `InvitationResponse`

#### Listar Invitaciones
**Endpoint:** `GET /api/v1/organizations/{organization_id}/invitations`

**Permisos:** Requiere `can_invite_users`

**Response:**
```typescript
interface InvitationListResponse {
  items: InvitationResponse[];
  total: number;
}
```

#### Cancelar Invitación
**Endpoint:** `DELETE /api/v1/organizations/{organization_id}/invitations/{invitation_id}`

**Permisos:** Requiere `can_invite_users`

#### Aceptar Invitación
**Endpoint:** `POST /api/v1/accept-invitation`

**Request:** `InvitationAcceptRequest`

**Response:** `InvitationAcceptResponse` (incluye JWT token para login automático)

### 9.3 Cambio de Contraseña

#### Cambiar Contraseña (Usuario Actual)
**Endpoint:** `PUT /api/v1/auth/me/password`

**Request:**
```typescript
interface ChangePasswordRequest {
  current_password: string;
  new_password: string;
}
```

**Permisos:** Usuario autenticado (solo puede cambiar su propia contraseña)

#### Resetear Contraseña (Admin)
**Endpoint:** `PUT /api/v1/users/{user_id}/password`

**Permisos:** Solo super_admin

**Request:**
```typescript
interface ResetPasswordRequest {
  new_password: string;
  send_email?: boolean;
}
```

---

## 10. VALIDACIONES Y ESTADOS

### 10.1 Validaciones de Invitación

#### Error: Email Ya en Organización
```typescript
interface UserAlreadyMemberError {
  type: "USER_ALREADY_MEMBER";
  condition: user.organization_id === organization_id;
  message: "❌ Este usuario ya es miembro de la organización";
  severity: "error";
  color: "#DC2626";
  icon: "XCircle";
}
```

#### Advertencia: Invitación Pendiente
```typescript
interface PendingInvitationWarning {
  type: "PENDING_INVITATION";
  condition: exists_pending_invitation === true;
  message: "⚠️ Ya existe una invitación pendiente para este email";
  severity: "warning";
  color: "#F59E0B";
  icon: "AlertCircle";
  action: "Reenviar invitación o cancelar la anterior";
}
```

#### Error: Sin Permisos para Invitar
```typescript
interface NoInvitePermissionError {
  type: "NO_INVITE_PERMISSION";
  condition: !has_permission(user, PERM_INVITE_USERS);
  message: "❌ No tienes permisos para invitar usuarios";
  severity: "error";
  color: "#DC2626";
  icon: "XCircle";
}
```

### 10.2 Validaciones de Perfil

#### Error: Email Inválido
```typescript
interface InvalidEmailError {
  type: "INVALID_EMAIL";
  condition: !is_valid_email(email);
  message: "❌ El formato del email no es válido";
  severity: "error";
  color: "#DC2626";
  icon: "XCircle";
  field: "email";
}
```

#### Error: Contraseña Débil
```typescript
interface WeakPasswordError {
  type: "WEAK_PASSWORD";
  condition: password.length < 8 || !has_complexity(password);
  message: "❌ La contraseña debe tener al menos 8 caracteres";
  severity: "error";
  color: "#DC2626";
  icon: "XCircle";
  field: "password";
}
```

---

## 11. CHECKLIST DE VALIDACIÓN

### 11.1 Validaciones Funcionales
- [ ] Lista de usuarios muestra solo información permitida según rol
- [ ] BCR y costos sensibles están ocultos para roles sin permiso
- [ ] Invitaciones se crean correctamente
- [ ] Estados de invitación se muestran correctamente
- [ ] Cambio de contraseña funciona
- [ ] Perfil se actualiza correctamente
- [ ] Permisos se respetan en todas las acciones

### 11.2 Validaciones de Diseño
- [ ] Badges de rol tienen colores correctos
- [ ] Tabla es responsive (mobile-friendly)
- [ ] Modales tienen overlay y animaciones
- [ ] Validaciones se muestran inline
- [ ] Estados de carga son claros
- [ ] Mensajes de error son informativos

### 11.3 Validaciones de Seguridad
- [ ] Información sensible está protegida por permisos
- [ ] Badges de "Confidencial" se muestran donde corresponde
- [ ] Roles no pueden ver información que no deben ver
- [ ] Validaciones del backend se reflejan en frontend

---

## 12. REFERENCIAS TÉCNICAS

### 12.1 Endpoints del Backend

- **Usuarios:** `/api/v1/users/`, `/api/v1/auth/me`
- **Invitaciones:** `/api/v1/organizations/{id}/invitations`
- **Aceptar Invitación:** `/api/v1/accept-invitation`
- **Cambiar Contraseña:** `/api/v1/auth/me/password`

### 12.2 Schemas TypeScript

Ver archivo: `docs/development/FRONTEND_API_INTEGRATION_GUIDE.md`

### 12.3 Documentación Completa

- **Guía de Integración API:** `docs/development/FRONTEND_API_INTEGRATION_GUIDE.md`
- **Código Backend:** `backend/app/core/permissions.py`, `backend/app/core/roles.py`
- **Schemas:** `backend/app/schemas/auth.py`, `backend/app/schemas/invitation.py`

---

**Última actualización:** 2026-01-23  
**Versión del Backend:** Compatible con v1.0  
**Nota de Seguridad:** Este documento enfatiza la protección de información financiera confidencial según roles
