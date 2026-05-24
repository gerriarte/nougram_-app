# 🧪 Guía de Validación de Aislamiento de Datos Multi-Tenant

Esta guía explica cómo validar que el aislamiento de datos entre organizaciones funciona correctamente.

---

## 📋 Índice

1. [Script Automatizado](#script-automatizado)
2. [Pruebas Manuales](#pruebas-manuales)
3. [Validaciones Específicas](#validaciones-específicas)
4. [Troubleshooting](#troubleshooting)

---

## 🤖 Script Automatizado

### Ejecutar el Script de Validación

El script `backend/scripts/test_tenant_isolation.py` crea automáticamente dos organizaciones de prueba y valida el aislamiento de datos.

```bash
# Desde la raíz del proyecto
cd backend
python scripts/test_tenant_isolation.py
```

### Qué hace el script

1. **Crea dos organizaciones:**
   - Organización A (Org A)
   - Organización B (Org B)

2. **Crea usuarios para cada organización:**
   - `user_a@orga.test` → Org A
   - `user_b@orgb.test` → Org B

3. **Crea datos para cada organización:**
   - Proyectos
   - Servicios
   - Costos fijos

4. **Ejecuta pruebas de aislamiento:**
   - ✅ Org A puede acceder a sus propios datos
   - ✅ Org A NO puede acceder a datos de Org B
   - ✅ Listados solo muestran datos de la organización
   - ✅ Creación de datos asigna correctamente `organization_id`

5. **Opcionalmente limpia los datos de prueba**

### Ejemplo de Salida

```
============================================================
SCRIPT DE VALIDACIÓN DE AISLAMIENTO DE DATOS
============================================================

Base de datos: localhost:5435/nougram_db

============================================================
CONFIGURANDO DATOS DE PRUEBA
============================================================

✅ Organización A creada: ID=2, Name=Organización A - Test
✅ Organización B creada: ID=3, Name=Organización B - Test

✅ Usuario A creado: ID=2, Email=user_a@orga.test, Org=2
✅ Usuario B creado: ID=3, Email=user_b@orgb.test, Org=3

✅ Proyecto A creado: ID=1, Name=Proyecto Org A
✅ Servicio A creado: ID=1, Name=Servicio Org A
✅ Costo A creado: ID=1, Name=Costo Org A

✅ Proyecto B creado: ID=2, Name=Proyecto Org B
✅ Servicio B creado: ID=2, Name=Servicio Org B
✅ Costo B creado: ID=2, Name=Costo Org B

============================================================
PRUEBAS DE AISLAMIENTO DE DATOS
============================================================

------------------------------------------------------------
TEST 1: Usuario de Org A puede acceder a sus propios datos
------------------------------------------------------------
✅ Org A puede acceder a su proyecto: Proyecto Org A
✅ Org A puede acceder a su servicio: Servicio Org A
✅ Org A puede acceder a su costo: Costo Org A

------------------------------------------------------------
TEST 2: Usuario de Org A NO puede acceder a datos de Org B
------------------------------------------------------------
✅ Org A NO puede acceder al proyecto de Org B (correctamente bloqueado)
✅ Org A NO puede acceder al servicio de Org B (correctamente bloqueado)
✅ Org A NO puede acceder al costo de Org B (correctamente bloqueado)

------------------------------------------------------------
TEST 3: Listado de datos solo muestra datos de la organización
------------------------------------------------------------
✅ Org A ve 1 proyecto(s), todos pertenecen a Org A
✅ Org A ve 1 servicio(s), todos pertenecen a Org A
✅ Org A ve 1 costo(s), todos pertenecen a Org A

------------------------------------------------------------
TEST 4: Creación de datos asigna correctamente organization_id
------------------------------------------------------------
✅ Nuevo proyecto creado con organization_id=2 (correcto)
✅ Org B NO puede acceder al nuevo proyecto de Org A (correctamente bloqueado)

============================================================
✅ TODAS LAS PRUEBAS DE AISLAMIENTO PASARON
============================================================
```

---

## 🧪 Pruebas Manuales

### 1. Crear Dos Organizaciones

Usa el script o crea manualmente en la base de datos:

```sql
-- Organización A
INSERT INTO organizations (name, slug, subscription_plan, subscription_status)
VALUES ('Org A Test', 'org-a-test', 'professional', 'active');

-- Organización B
INSERT INTO organizations (name, slug, subscription_plan, subscription_status)
VALUES ('Org B Test', 'org-b-test', 'professional', 'active');
```

### 2. Crear Usuarios

```sql
-- Usuario para Org A
INSERT INTO users (email, full_name, hashed_password, role, organization_id)
VALUES (
    'user_a@test.com',
    'Usuario Org A',
    '$2b$12$...', -- Hash de password
    'product_manager',
    2 -- ID de Org A
);

-- Usuario para Org B
INSERT INTO users (email, full_name, hashed_password, role, organization_id)
VALUES (
    'user_b@test.com',
    'Usuario Org B',
    '$2b$12$...', -- Hash de password
    'product_manager',
    3 -- ID de Org B
);
```

### 3. Crear Datos para Cada Organización

**Usando la API con User A (Org A):**

```bash
# Login como User A
curl -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user_a@test.com", "password": "password123"}'

# Crear proyecto para Org A
curl -X POST http://localhost:5000/api/v1/projects/ \
  -H "Authorization: Bearer <token_user_a>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Proyecto Org A",
    "client_name": "Cliente A",
    "client_email": "cliente_a@test.com",
    "currency": "USD"
  }'
```

**Usando la API con User B (Org B):**

```bash
# Login como User B
curl -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user_b@test.com", "password": "password123"}'

# Crear proyecto para Org B
curl -X POST http://localhost:5000/api/v1/projects/ \
  -H "Authorization: Bearer <token_user_b>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Proyecto Org B",
    "client_name": "Cliente B",
    "client_email": "cliente_b@test.com",
    "currency": "USD"
  }'
```

### 4. Validar Aislamiento

**Test: User A intenta acceder a proyecto de Org B**

```bash
# Obtener ID del proyecto de Org B (ej: 10)
# Intentar acceder con token de User A
curl -X GET http://localhost:5000/api/v1/projects/10 \
  -H "Authorization: Bearer <token_user_a>"

# Debería retornar 404 Not Found (no puede acceder)
```

**Test: Listar proyectos**

```bash
# User A lista proyectos (debería ver solo los suyos)
curl -X GET http://localhost:5000/api/v1/projects/ \
  -H "Authorization: Bearer <token_user_a>"

# User B lista proyectos (debería ver solo los suyos)
curl -X GET http://localhost:5000/api/v1/projects/ \
  -H "Authorization: Bearer <token_user_b>"
```

---

## 🔍 Validaciones Específicas

### 1. Validación a Nivel de Repositorio

Los repositorios deben filtrar automáticamente por `organization_id`:

```python
# Repositorio con tenant scoping
repo = RepositoryFactory.create_project_repository(db, organization_id=2)

# Este get_by_id solo retorna si el proyecto pertenece a org_id=2
project = await repo.get_by_id(project_id)

# Este get_all solo retorna proyectos de org_id=2
projects = await repo.get_all()
```

### 2. Validación a Nivel de Endpoint

Los endpoints deben usar `get_tenant_context()`:

```python
@router.get("/projects/{project_id}")
async def get_project(
    project_id: int,
    tenant: TenantContext = Depends(get_tenant_context),  # ← Importante
    db: AsyncSession = Depends(get_db)
):
    # El repositorio usa tenant.organization_id automáticamente
    repo = RepositoryFactory.create_project_repository(db, tenant.organization_id)
    project = await repo.get_by_id(project_id)  # Solo retorna si pertenece al tenant
    ...
```

### 3. Validación en Base de Datos

Verificar directamente en la base de datos:

```sql
-- Ver proyectos de cada organización
SELECT id, name, organization_id FROM projects ORDER BY organization_id;

-- Verificar que organization_id está asignado correctamente
SELECT 
    p.id, 
    p.name, 
    p.organization_id,
    o.name as org_name
FROM projects p
JOIN organizations o ON p.organization_id = o.id;
```

---

## 🐛 Troubleshooting

### Problema: Usuario puede ver datos de otras organizaciones

**Causa:** El endpoint no está usando `get_tenant_context()` o el repositorio no está filtrando por tenant.

**Solución:**
1. Verificar que el endpoint tiene `tenant: TenantContext = Depends(get_tenant_context)`
2. Verificar que el repositorio se crea con `RepositoryFactory.create_xxx_repository(db, tenant.organization_id)`
3. Verificar que `BaseRepository._apply_tenant_filter()` está funcionando

### Problema: Error 404 al acceder a recursos propios

**Causa:** El `organization_id` no está asignado correctamente al crear el recurso.

**Solución:**
1. Verificar que al crear recursos se asigna `organization_id = tenant.organization_id`
2. Verificar en la base de datos que los registros tienen `organization_id` correcto

### Problema: Listados muestran datos de todas las organizaciones

**Causa:** El repositorio no está aplicando el filtro de tenant en `get_all()`.

**Solución:**
1. Verificar que `BaseRepository.get_all()` llama a `_apply_tenant_filter()`
2. Verificar que el repositorio tiene `tenant_id` asignado

---

## ✅ Checklist de Validación

- [ ] Script automatizado pasa todas las pruebas
- [ ] Usuario de Org A no puede acceder a proyectos de Org B
- [ ] Usuario de Org B no puede acceder a proyectos de Org A
- [ ] Listados solo muestran datos de la propia organización
- [ ] Creación de recursos asigna correctamente `organization_id`
- [ ] Actualización de recursos valida que pertenecen al tenant
- [ ] Eliminación de recursos solo afecta al propio tenant
- [ ] Cálculos (ej: blended_cost_rate) filtran por tenant
- [ ] Dashboard muestra solo métricas del propio tenant

---

## 📝 Notas Importantes

1. **Super Admin:** Los usuarios con rol `super_admin` pueden tener acceso especial. El script de prueba no cubre este caso.

2. **Datos Legacy:** Si hay datos existentes sin `organization_id`, el sistema usa fallback a `organization_id=1`. Esto es temporal para retrocompatibilidad.

3. **Cache:** El cache de `calculate_blended_cost_rate` incluye `tenant_id` en la clave, asegurando que cada organización tenga su propio cache.

---

**Última actualización:** 12 de Diciembre, 2025















