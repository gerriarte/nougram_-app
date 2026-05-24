# 🏗️ Sprint 3: Fundación Multi-Tenant

**Estado:** ⏳ Pendiente (Siguiente)  
**Duración estimada:** 2 semanas  
**Prioridad:** Alta  
**Dependencias:** ✅ Sprint 2 completado

---

## 🎯 Objetivo

Crear la fundación para arquitectura multi-tenant:
1. Crear modelo `Organization`
2. Migrar datos existentes de forma segura
3. Agregar `organization_id` a todas las tablas
4. Mantener retrocompatibilidad

---

## ✅ Tareas Detalladas

### 3.1: Crear Modelo Organization

**Archivo:** `backend/app/models/organization.py` (nuevo)

**Campos requeridos:**
- `id` (Integer, primary key)
- `name` (String, nullable=False)
- `slug` (String, unique, index)
- `subscription_plan` (String, default="free")
- `subscription_status` (String, default="active")
- `settings` (JSON, nullable=True) - Configuraciones por tenant
- `created_at` (DateTime)
- `updated_at` (DateTime)

**Relaciones:**
- `users` - relationship con User (one-to-many)

---

### 3.2: Preparar Migración de Alembic

**Archivo:** `backend/alembic/versions/XXX_add_multi_tenant.py` (nuevo)

**Pasos de migración:**

1. **Crear tabla `organizations`**
   ```python
   op.create_table(
       'organizations',
       sa.Column('id', sa.Integer(), nullable=False),
       sa.Column('name', sa.String(), nullable=False),
       sa.Column('slug', sa.String(), nullable=False, unique=True),
       sa.Column('subscription_plan', sa.String(), default='free'),
       sa.Column('subscription_status', sa.String(), default='active'),
       sa.Column('settings', sa.JSON(), nullable=True),
       sa.Column('created_at', sa.DateTime(timezone=True)),
       sa.Column('updated_at', sa.DateTime(timezone=True)),
       sa.PrimaryKeyConstraint('id')
   )
   ```

2. **Crear organización "default"**
   ```python
   op.execute("""
       INSERT INTO organizations (id, name, slug, subscription_plan, subscription_status, created_at, updated_at)
       VALUES (1, 'Default Organization', 'default', 'enterprise', 'active', NOW(), NOW())
   """)
   ```

3. **Agregar `organization_id` a tablas (nullable primero)**
   - `users`
   - `projects`
   - `services`
   - `costs_fixed`
   - `team_members`
   - `taxes`

4. **Asignar registros existentes a organización default**
   ```python
   op.execute("UPDATE users SET organization_id = 1 WHERE organization_id IS NULL")
   op.execute("UPDATE projects SET organization_id = 1 WHERE organization_id IS NULL")
   # ... para cada tabla
   ```

5. **Hacer `organization_id` NOT NULL**
   ```python
   op.alter_column('users', 'organization_id', nullable=False)
   # ... para cada tabla
   ```

6. **Crear índices compuestos**
   ```python
   op.create_index('ix_projects_organization_id_created_at', 'projects', ['organization_id', 'created_at'])
   op.create_index('ix_projects_organization_id_id', 'projects', ['organization_id', 'id'])
   # ... para cada tabla relevante
   ```

7. **Crear Foreign Keys**
   ```python
   op.create_foreign_key('fk_users_organization', 'users', 'organizations', ['organization_id'], ['id'])
   # ... para cada tabla
   ```

---

### 3.3: Actualizar Modelos Existentes

**Archivos a actualizar:**

1. **`backend/app/models/user.py`**
   ```python
   organization_id = Column(Integer, ForeignKey('organizations.id'), nullable=False, index=True)
   organization = relationship("Organization", back_populates="users")
   ```

2. **`backend/app/models/project.py`**
   ```python
   organization_id = Column(Integer, ForeignKey('organizations.id'), nullable=False, index=True)
   ```

3. **`backend/app/models/service.py`**
   ```python
   organization_id = Column(Integer, ForeignKey('organizations.id'), nullable=False, index=True)
   ```

4. **`backend/app/models/cost.py`** (CostFixed)
   ```python
   organization_id = Column(Integer, ForeignKey('organizations.id'), nullable=False, index=True)
   ```

5. **`backend/app/models/team.py`** (TeamMember)
   ```python
   organization_id = Column(Integer, ForeignKey('organizations.id'), nullable=False, index=True)
   ```

6. **`backend/app/models/tax.py`**
   ```python
   organization_id = Column(Integer, ForeignKey('organizations.id'), nullable=False, index=True)
   ```

---

### 3.4: Actualizar Repositorios (Preliminar)

**Nota:** Esta es una actualización mínima. El tenant scoping completo será en Sprint 4.

- Actualizar `create` methods para asignar `organization_id` automáticamente
- Preparar para filtrado por tenant en Sprint 4

---

### 3.5: Tests de Migración

**Crear:** `backend/tests/integration/test_migration_multi_tenant.py`

**Tests:**
- ✅ Migración crea tabla organizations
- ✅ Migración crea organización default
- ✅ Todos los registros existentes tienen organization_id = 1
- ✅ organization_id es NOT NULL después de migración
- ✅ Índices compuestos existen
- ✅ Foreign keys funcionan correctamente

---

## 📁 Archivos a Crear/Modificar

### Nuevos:
- ✅ `backend/app/models/organization.py`
- ✅ `backend/alembic/versions/XXX_add_multi_tenant.py`
- ✅ `backend/tests/integration/test_migration_multi_tenant.py`

### Modificar:
- ✅ `backend/app/models/user.py`
- ✅ `backend/app/models/project.py`
- ✅ `backend/app/models/service.py`
- ✅ `backend/app/models/cost.py`
- ✅ `backend/app/models/team.py`
- ✅ `backend/app/models/tax.py`
- ✅ `backend/app/models/__init__.py` (exportar Organization)

---

## ⚠️ Consideraciones de Seguridad

1. **Backup antes de migración**
   - Hacer backup completo de la base de datos
   - Documentar proceso de rollback

2. **Migración en etapas**
   - Primero hacer nullable
   - Luego asignar valores
   - Finalmente hacer NOT NULL

3. **Validación post-migración**
   - Verificar integridad referencial
   - Contar registros por organización
   - Validar que no hay NULLs

---

## ✅ Criterios de Aceptación

- [ ] Modelo `Organization` creado y funciona
- [ ] Migración ejecuta sin errores
- [ ] Todos los datos existentes preservados
- [ ] Todos los registros tienen `organization_id = 1`
- [ ] Índices compuestos creados
- [ ] Foreign keys funcionan
- [ ] Tests de migración pasan
- [ ] Migración es reversible (rollback funciona)
- [ ] Aplicación funciona correctamente después de migración

---

## 🚀 Siguiente Sprint

Después de completar Sprint 3, continuar con:
- **Sprint 4:** Tenant Context y Repositorios (aislamiento completo)

---

**Última actualización:** 12 de Diciembre, 2025

