# 🔍 Problemas Potenciales Identificados en Nougram

**Fecha de análisis:** 12 de Diciembre, 2025  
**Estado:** Análisis inicial - Requiere validación y corrección

---

## 🚨 CRÍTICOS - Seguridad y Aislamiento

### 1. **✅ RESUELTO: Falta TenantContext en endpoints**

**Ubicación:** `backend/app/api/v1/endpoints/projects.py`

**Problema:**
- El endpoint `list_projects()` usaba `tenant.organization_id` pero NO declaraba `tenant: TenantContext = Depends(get_tenant_context)` en los parámetros
- El endpoint `delete_project()` tenía el mismo problema
- Esto causaría un error `NameError` en tiempo de ejecución

**Impacto:** 
- Los endpoints fallarían completamente
- No se pueden listar o eliminar proyectos

**Solución aplicada:**
- ✅ Agregado `tenant: TenantContext = Depends(get_tenant_context)` a `list_projects()` (línea 48)
- ✅ Agregado `tenant: TenantContext = Depends(get_tenant_context)` a `delete_project()` (línea 447)

**Estado:** ✅ CORREGIDO

---

### 2. **CRÍTICO: Race Condition en Validación JWT**

**Ubicación:** `backend/app/core/security.py:125-140`

**Problema:**
- Un usuario puede obtener un token válido con `organization_id = X`
- Si el usuario es transferido a otra organización mientras el token aún es válido, el token seguirá funcionando hasta que expire
- Hay validación, pero solo cuando se verifica el token; si el token ya está validado y en uso, puede acceder a datos de la organización anterior

**Escenario de ataque:**
1. Usuario obtiene token con `org_id = 1`
2. Usuario es transferido a `org_id = 2` (por admin)
3. Token sigue válido durante 30 minutos
4. Usuario puede seguir accediendo a datos de `org_id = 1` hasta que el token expire

**Impacto:**
- Posible fuga de datos entre organizaciones
- Violación de aislamiento multi-tenant

**Solución recomendada:**
- Implementar token blacklist/revocación
- O reducir el tiempo de expiración del token
- O verificar organización en cada request (ya se hace, pero el token podría estar en cache del cliente)

---

### 3. **CRÍTICO: Falta Rate Limiting**

**Ubicación:** Global - No implementado

**Problema:**
- No hay rate limiting en ningún endpoint
- Endpoints de autenticación (`/login`) son vulnerables a brute force
- Endpoints pueden ser abusados causando DoS

**Impacto:**
- Ataques de fuerza bruta en login
- Posible DoS
- Abuso de recursos del servidor

**Solución recomendada:**
- Implementar `slowapi` o `fastapi-limiter`
- Rate limiting por IP en login (ej: 5 intentos por minuto)
- Rate limiting general por usuario autenticado

---

### 4. **REVISADO: Lógica de Tenant Context es Correcta**

**Ubicación:** `backend/app/core/tenant.py:84`

**Estado:** ✅ La lógica es correcta

**Análisis:**
```python
if not organization.subscription_status == "active" and not is_super_admin:
```

**Interpretación:** "Si el status NO es activo Y el usuario NO es super_admin, entonces bloquea"

Esta lógica es correcta. Bloquea acceso si:
- La organización no está activa Y
- El usuario no es super_admin

Si el usuario es super_admin, puede acceder incluso si la organización no está activa (bypass).

---

## ⚠️ ALTO - Integridad de Datos y Performance

### 5. **Falta Manejo de Transacciones en Operaciones Complejas**

**Ubicación:** Múltiples endpoints

**Problema:**
- Muchos endpoints hacen múltiples operaciones de BD sin transacciones explícitas
- Si una operación falla a mitad de camino, puede dejar datos inconsistentes

**Ejemplo:** `create_project` crea Project, Quote, QuoteItems - si falla en medio, queda inconsistente.

**Impacto:**
- Datos inconsistentes en la base de datos
- Posible corrupción de datos

**Solución:**
- Usar el `transaction` context manager existente en `backend/app/core/transactions.py`
- Envolver operaciones complejas en transacciones

---

### 6. **N+1 Query Problem Potencial**

**Ubicación:** Varios endpoints con relaciones

**Problema:**
- En `list_projects`, se carga `Project.taxes` con `selectinload`, pero luego se itera sobre projects y se accede a `project.taxes` - puede causar queries adicionales si no se maneja bien

**Ejemplo en `projects.py:93-106`:**
```python
for project in projects:
    project_dict = {
        ...
        "taxes": [{"id": tax.id, ...} for tax in project.taxes],  # Ya está cargado, pero verificar
    }
```

**Impacto:**
- Performance degradada con muchos registros
- Alto uso de recursos de BD

**Nota:** Parece que ya se usa `selectinload`, pero requiere validación.

---

### 7. **Falta Validación de Límites por Plan de Suscripción**

**Ubicación:** Global - No implementado

**Problema:**
- No hay validación de límites (max_users, max_projects, etc.) según el plan de suscripción
- Un tenant "free" puede crear ilimitados proyectos/usuarios

**Impacto:**
- Abuso de recursos
- Problemas de escalabilidad
- Pérdida de ingresos (usuarios free usando recursos premium)

**Solución:**
- Implementar validación de límites en endpoints de creación
- Middleware o decorador para validar límites por plan

---

### 8. **Caché No Se Invalida Correctamente en Todos los Casos**

**Ubicación:** `backend/app/core/cache.py` y endpoints que usan caché

**Problema:**
- El `blended_cost_rate` se cachea, pero si se modifican costos o team members, se invalida con `cache.invalidate_pattern("blended_cost_rate:")`
- Sin embargo, si hay múltiples monedas o tenants, la invalidación podría no funcionar correctamente

**Impacto:**
- Datos cacheados obsoletos
- Cálculos incorrectos

**Solución:**
- Verificar que la invalidación funcione correctamente con múltiples claves
- Agregar logging para validar invalidaciones

---

## ⚡ MEDIO - Arquitectura y Mantenibilidad

### 9. **Falta Manejo de Errores Específicos en Algunos Endpoints**

**Ubicación:** Varios endpoints

**Problema:**
- Algunos endpoints capturan `Exception` genérico y devuelven 500
- No se diferencian errores de validación, negocio, o sistema

**Ejemplo en `team.py:116`:**
```python
except Exception as e:
    await db.rollback()
    logger.error(...)
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, ...)
```

**Impacto:**
- Difícil debugging
- Usuarios ven errores genéricos

**Solución:**
- Usar excepciones específicas del dominio
- Manejar diferentes tipos de errores apropiadamente

---

### 10. **Falta Validación de Input en Algunos Endpoints**

**Ubicación:** Varios endpoints

**Problema:**
- Aunque se usa Pydantic para validación, algunos endpoints aceptan parámetros de query sin validación estricta
- Ejemplo: `status_filter` en `list_projects` acepta cualquier string

**Impacto:**
- Posibles inyecciones SQL (aunque SQLAlchemy lo previene)
- Datos inválidos procesados

**Solución:**
- Validar valores permitidos con Enum o validación explícita
- Usar Pydantic para query parameters también

---

### 11. **Falta Logging de Auditoría para Operaciones Críticas**

**Ubicación:** Global

**Problema:**
- No hay logging de auditoría para:
  - Cambios de organización de usuarios
  - Cambios de suscripción
  - Accesos a datos sensibles
  - Operaciones administrativas

**Impacto:**
- Imposible auditar quién hizo qué y cuándo
- No se puede rastrear accesos no autorizados

**Solución:**
- Implementar tabla de auditoría
- Logging estructurado para operaciones críticas

---

### 12. **El Fallback a `organization_id = 1` Es Peligroso**

**Ubicación:** `backend/app/core/tenant.py:65`

**Problema:**
```python
if organization_id is None:
    logger.warning(f"User {current_user.id} has no organization_id, using default organization")
    organization_id = 1
```

**Problema:**
- Si un usuario no tiene `organization_id`, se asigna automáticamente a la organización 1
- Esto podría exponer datos de la organización 1 a usuarios que no deberían tener acceso

**Impacto:**
- Posible fuga de datos
- Violación de aislamiento

**Solución:**
- En lugar de fallback, debería ser un error que requiera que el admin asigne al usuario a una organización
- O crear una organización "orphan" para estos casos

---

### 13. **Falta Validación de Unicidad en Algunos Modelos**

**Ubicación:** Modelos

**Problema:**
- Algunos modelos tienen restricciones de unicidad pero solo a nivel de base de datos
- No hay validación a nivel de aplicación antes de intentar crear

**Ejemplo:** `Organization.slug` debe ser único, pero si dos requests simultáneas intentan crear con el mismo slug, ambas fallarán con error de BD en lugar de una validación elegante

**Impacto:**
- Errores confusos para el usuario
- Posibles race conditions

**Solución:**
- Validar existencia antes de crear
- Usar transacciones para prevenir race conditions

---

## 📊 BAJO - Mejoras y Optimizaciones

### 14. **Falta Paginación en Algunos Endpoints**

**Ubicación:** Algunos endpoints de listado

**Problema:**
- No todos los endpoints de listado tienen paginación
- Puede causar problemas de performance con muchos registros

**Solución:**
- Agregar paginación a todos los endpoints de listado

---

### 15. **Falta Documentación de Errores en Swagger**

**Ubicación:** Endpoints

**Problema:**
- No todos los endpoints documentan los códigos de error posibles
- Swagger/OpenAPI no muestra todos los posibles errores

**Solución:**
- Agregar `responses` a todos los endpoints con códigos de error posibles

---

### 16. **CORS Configuración Muy Permisiva**

**Ubicación:** `backend/main.py:40-47`

**Problema:**
```python
allow_headers=["*"],
expose_headers=["*"],
```

**Problema:**
- Muy permisivo para producción
- Puede permitir headers no deseados

**Solución:**
- Especificar headers explícitos permitidos en producción

---

### 17. **Falta Health Check Completo**

**Ubicación:** `backend/main.py:85-88`

**Problema:**
- El health check solo devuelve `{"status": "healthy"}`
- No verifica conexión a BD, servicios externos, etc.

**Solución:**
- Health check que verifique:
  - Conexión a BD
  - Servicios externos (opcional)
  - Estado de caché

---

## 🔄 Próximos Pasos Recomendados

### Prioridad 1 (Críticos - Inmediato):
1. ✅ Corregir `list_projects` - Agregar TenantContext
2. ✅ Revisar lógica de validación en `tenant.py:84`
3. ⏳ Implementar rate limiting básico

### Prioridad 2 (Alto - Esta semana):
4. ⏳ Implementar validación de límites por plan
5. ⏳ Revisar y corregir manejo de transacciones
6. ⏳ Eliminar fallback peligroso a `organization_id = 1`

### Prioridad 3 (Medio - Este mes):
7. ⏳ Mejorar manejo de errores
8. ⏳ Agregar logging de auditoría
9. ⏳ Validar inputs más estrictamente

### Prioridad 4 (Bajo - Mejoras):
10. ⏳ Mejorar documentación
11. ⏳ Optimizar queries
12. ⏳ Mejorar health checks

---

**Última actualización:** 12 de Diciembre, 2025

