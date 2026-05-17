# Configuración de Base de Datos

## ¿Está listo el proyecto para crear las bases de datos?

**Sí.** El proyecto está preparado para crear y migrar la base de datos de forma automática.

---

## Flujo automático (Docker Compose)

Al levantar el stack con `docker compose -f docker-compose.prod.yml up -d`:

| Orden | Servicio | Acción |
|-------|----------|--------|
| 1 | **postgres** | Crea la base de datos `nougram_db` (si no existe) usando `POSTGRES_DB` |
| 2 | **backend** | Espera a que postgres esté healthy |
| 3 | **backend** | Ejecuta `alembic upgrade head` → crea tablas y aplica migraciones |
| 4 | **backend** | Las migraciones incluyen datos iniciales (plantillas por industria) |
| 5 | **backend** | Arranca Gunicorn |

No se requiere configuración manual de la base de datos.

---

## Dependencias necesarias

- **PostgreSQL 15+**: proporcionado por la imagen `postgres:15-alpine` en el compose
- **psycopg2**: para que Alembic ejecute migraciones (incluido en `requirements.txt`)
- **asyncpg**: para que la app se conecte en runtime (incluido en `requirements.txt`)

---

## Si usas PostgreSQL externo

1. Crea la base de datos manualmente:
   ```sql
   CREATE DATABASE nougram_db;
   ```
2. Configura `DATABASE_URL` en `.env.production` apuntando a tu instancia
3. Ejecuta migraciones antes de arrancar el backend:
   ```bash
   cd backend
   alembic upgrade head
   ```

---

## Migraciones disponibles

El proyecto incluye 26 migraciones que cubren:

- Tablas base: users, organizations, projects, quotes, services, costs, team_members
- Multi-tenancy (organization_id)
- Impuestos, monedas, soft delete
- Sistema de créditos, invitaciones, audit logs
- Plantillas por industria (seed data)
- Índices de rendimiento

---

## Verificar estado de migraciones

```bash
cd backend
alembic current   # Ver versión actual
alembic history   # Ver historial
alembic heads     # Ver cabezas
```
