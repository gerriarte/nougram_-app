# Capacidades y Permisos de Roles

## Arquitectura de Roles

El sistema utiliza una arquitectura de **dos niveles** de roles:

1. **Roles de Soporte (Support Roles)**: Para el equipo que gestiona la plataforma multi-tenant
2. **Roles de Cliente (Tenant Roles)**: Para usuarios dentro de cada organización

---

## Roles de Soporte (Multi-Tenant Managers)

Estos roles pueden acceder a múltiples organizaciones y gestionar la plataforma.

### 🔴 `super_admin`
**Tipo:** Support  
**Descripción:** Control total de la plataforma. Puede acceder a todas las organizaciones y realizar cualquier acción.

**Capacidades:**
- ✅ Acceso a todas las organizaciones (multi-tenant)
- ✅ Ver datos sensibles (costos, información financiera)
- ✅ Modificar costos y configuraciones
- ✅ Crear y enviar cotizaciones
- ✅ Gestionar suscripciones
- ✅ Invitar usuarios
- ✅ Crear proyectos y servicios
- ✅ Eliminar recursos
- ✅ Ver analytics y reportes

**Uso típico:** Administrador principal de la plataforma

---

### 🟡 `support_manager`
**Tipo:** Support  
**Descripción:** Gestor de Clientes. Acceso limitado, datos anonimizados. Puede gestionar múltiples organizaciones.

**Capacidades:**
- ✅ Acceso a todas las organizaciones (multi-tenant)
- ❌ **NO** puede ver datos sensibles (datos anonimizados)
- ✅ Ver analytics y reportes
- ⚠️ Modificaciones limitadas

**Uso típico:** Equipo de soporte al cliente, gestores de cuenta

---

### 🔵 `data_analyst`
**Tipo:** Support  
**Descripción:** Analista de Datos. Solo acceso a datasets anonimizados para análisis.

**Capacidades:**
- ✅ Ver analytics y reportes (solo datos anonimizados)
- ❌ **NO** puede acceder a organizaciones específicas
- ❌ **NO** puede modificar datos
- ❌ **NO** puede ver datos sensibles

**Uso típico:** Analistas de negocio, equipo de datos

---

## Roles de Cliente (Tenant Roles)

Estos roles están restringidos a su propia organización.

### 🟢 `owner`
**Tipo:** Tenant  
**Descripción:** Dueño de la cuenta. Único que puede pagar, acceso completo a su organización.

**Capacidades:**
- ✅ Ver datos sensibles (costos, información financiera)
- ✅ Modificar costos y configuraciones
- ✅ Crear y enviar cotizaciones
- ✅ Gestionar suscripción (pago, cambio de plan)
- ✅ Invitar usuarios a la organización
- ✅ Crear proyectos y servicios
- ✅ Eliminar recursos
- ✅ Ver analytics y reportes
- ❌ **NO** puede acceder a otras organizaciones

**Uso típico:** Fundador, CEO, dueño de la agencia

---

### 🟠 `admin_financiero`
**Tipo:** Tenant  
**Descripción:** Administrador financiero. Ve costos sensibles, gestiona costos y configuraciones financieras.

**Capacidades:**
- ✅ Ver datos sensibles (costos, información financiera)
- ✅ Modificar costos y configuraciones
- ✅ Crear y enviar cotizaciones
- ✅ Crear proyectos y servicios
- ✅ Ver analytics y reportes
- ❌ **NO** puede gestionar suscripción
- ❌ **NO** puede invitar usuarios
- ❌ **NO** puede eliminar recursos
- ❌ **NO** puede acceder a otras organizaciones

**Uso típico:** CFO, contador, administrador financiero

---

### 🔵 `product_manager`
**Tipo:** Tenant  
**Descripción:** Product Manager. Crea propuestas y cotizaciones, consume créditos.

**Capacidades:**
- ✅ Crear y enviar cotizaciones
- ✅ Crear proyectos
- ✅ Ver analytics básicos
- ❌ **NO** puede ver costos sensibles
- ❌ **NO** puede modificar costos
- ❌ **NO** puede gestionar servicios
- ❌ **NO** puede gestionar suscripción
- ❌ **NO** puede invitar usuarios
- ❌ **NO** puede eliminar recursos
- ❌ **NO** puede acceder a otras organizaciones

**Uso típico:** Product Manager, Account Manager, creador de propuestas

---

### ⚪ `collaborator`
**Tipo:** Tenant  
**Descripción:** Colaborador. Puede crear borradores, NO puede enviar cotizaciones, NO ve costos.

**Capacidades:**
- ✅ Crear cotizaciones (solo borradores)
- ✅ Crear proyectos
- ❌ **NO** puede enviar cotizaciones
- ❌ **NO** puede ver costos
- ❌ **NO** puede ver analytics
- ❌ **NO** puede modificar costos
- ❌ **NO** puede gestionar servicios
- ❌ **NO** puede gestionar suscripción
- ❌ **NO** puede invitar usuarios
- ❌ **NO** puede eliminar recursos
- ❌ **NO** puede acceder a otras organizaciones

**Uso típico:** Colaborador junior, asistente, editor de borradores

---

## Matriz de Permisos Comparativa

| Permiso | super_admin | support_manager | data_analyst | owner | admin_financiero | product_manager | collaborator |
|---------|:-----------:|:---------------:|:------------:|:-----:|:----------------:|:---------------:|:------------:|
| **Acceso Multi-Tenant** |
| Acceder a todas las organizaciones | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Datos Sensibles** |
| Ver costos e información financiera | ✅ | ❌ | ❌ | ✅ | ✅ | ❌ | ❌ |
| Modificar costos | ✅ | ❌ | ❌ | ✅ | ✅ | ❌ | ❌ |
| **Cotizaciones** |
| Crear cotizaciones | ✅ | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ |
| Enviar cotizaciones | ✅ | ❌ | ❌ | ✅ | ✅ | ✅ | ❌ |
| **Gestión** |
| Gestionar suscripción | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |
| Invitar usuarios | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |
| Crear proyectos | ✅ | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ |
| Crear servicios | ✅ | ❌ | ❌ | ✅ | ✅ | ❌ | ❌ |
| Eliminar recursos | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |
| **Analytics** |
| Ver analytics y reportes | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |

---

## Permisos Especiales

### Consumo de Créditos
Algunas acciones consumen créditos del plan:
- **Enviar cotizaciones** (`PERM_SEND_QUOTES`)
- **Ver analytics avanzados** (`PERM_VIEW_ANALYTICS`)

### Aprobación de Eliminaciones
Solo los siguientes roles pueden aprobar solicitudes de eliminación:
- `super_admin`
- `owner`

---

## Validaciones Importantes

### Organización (organization_id)
- **Roles Support**: Pueden tener `organization_id = NULL` (acceso multi-tenant)
- **Roles Tenant**: **DEBEN** tener `organization_id` asignado (solo su organización)

### Acceso a Recursos
- Los usuarios **tenant** solo pueden acceder a recursos de su propia organización
- Los usuarios **support** pueden acceder a recursos de cualquier organización (según permisos)

---

## Notas de Implementación

- El sistema valida automáticamente los permisos en cada endpoint
- Los permisos se verifican tanto en backend como en frontend
- Los roles `support` tienen acceso a datos anonimizados cuando no tienen permiso de datos sensibles
- El sistema de créditos está preparado para limitar acciones según el plan de suscripción

---

## Referencias

- **Backend:** `backend/app/core/roles.py` - Definición de roles
- **Backend:** `backend/app/core/permissions.py` - Matriz de permisos
- **Frontend:** `frontend/src/lib/permissions.ts` - Utilidades de permisos (frontend)
- **Tests:** `backend/tests/integration/test_permissions_exhaustive.py` - Tests exhaustivos de seguridad y permisos

## Tests de Seguridad

Los tests exhaustivos validan:
- Cada rol solo puede realizar acciones permitidas
- No hay data leakage entre roles (PM/collaborator no ven costos/salarios)
- Acceso cross-tenant está prevenido
- Todos los endpoints validan permisos correctamente
- Consumo de créditos según rol (cuando esté implementado)

**Estado de Tests:**
- ✅ Tests de permisos por endpoint implementados
- ✅ Tests de data leakage prevention implementados
- ✅ Tests de cross-tenant access prevention implementados
- ⏳ Tests de consumo de créditos según rol (pendiente implementación en endpoints)

