# Gestión de Clientes (Catálogo Maestro) – Despliegue y validación

**Fecha:** 14 de febrero de 2026  
**Plan:** Gestión de Clientes lateral (catálogo maestro)

---

## 1. Migración de base de datos

Se añadió la migración **k2l3m4n5o6p7** (`add_clients_table_and_project_client_id`):

- **Tabla `clients`:** id, organization_id, display_name, requester_name, email, status, notes, created_at, updated_at. Índice en `organization_id`.
- **Tabla `projects`:** columna nullable `client_id` (FK a `clients.id` con ON DELETE SET NULL). Se mantienen `client_name` y `client_email` como snapshot/compatibilidad.

**En Railway (o cualquier entorno):** ejecutar migraciones antes de desplegar la nueva versión del backend:

```bash
cd backend
python -m alembic upgrade head
```

O, si Alembic está en el PATH:

```bash
cd backend && alembic upgrade head
```

Asegúrese de que la variable de entorno `DATABASE_URL` esté configurada para el entorno correspondiente.

---

## 2. Flujo a validar

1. **Cliente → Cotización**
   - En **Gestión de Clientes** (`/dashboard/clients`): crear un cliente (empresa, solicitante, email).
   - En **Nueva Cotización** (`/projects/new`): en el selector de cliente, buscar por nombre y seleccionar el cliente creado (o crear uno nuevo desde el modal).
   - Guardar borrador o “Guardar y continuar”: el proyecto debe quedar con `client_id` y el nombre/email del cliente rellenados.

2. **Cotización → Pipeline**
   - En **Dashboard & Pipeline** (`/dashboard`): comprobar que la cotización aparece con el nombre del cliente.
   - Usar el filtro **“Todos los clientes”** y elegir el cliente recién usado: la lista debe filtrar por ese cliente (`client_id`).

3. **Edición de proyecto**
   - Al editar un proyecto existente, si se cambia el cliente por otro del catálogo, el backend actualiza `client_id` y el snapshot (client_name/client_email) desde el cliente maestro.

---

## 3. APIs relevantes

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/clients/` | Listado paginado de clientes (query: page, page_size, status) |
| GET | `/clients/search?q=` | Búsqueda para autocompletado (selector en cotización) |
| POST | `/clients/` | Crear cliente |
| GET | `/clients/{id}` | Detalle de cliente |
| PUT | `/clients/{id}` | Actualizar cliente |
| POST | `/projects/` | Crear proyecto; body puede incluir `client_id`, `client_name`, `client_email` |
| PUT | `/projects/{id}` | Actualizar proyecto; body puede incluir `client_id` |

---

## 4. Resumen de implementación

- **Backend:** modelo `Client`, repositorio, schemas, servicio, endpoints `/clients`; proyectos aceptan y devuelven `client_id`; snapshot name/email se rellena desde el cliente cuando hay `client_id`.
- **Frontend:** selector de cliente en cotización usa `GET /clients/search` y `POST /clients`; estado del builder y `quoteService` persisten `client_id`; página lateral **Gestión de Clientes** con listado y CRUD; pipeline con filtro por cliente (`client_id`).
