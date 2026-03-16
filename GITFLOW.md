# GitFlow y Despliegue en Railway

Flujo de trabajo basado en GitFlow con ambientes **prod** y **staging** en Railway.

---

## Ramas permanentes

| Rama   | Uso                      | Railway     |
|--------|--------------------------|-------------|
| `main` | Producción estable       | **prod**    |
| `develop` | Integración / pruebas | **staging** |

---

## Despliegue en Railway

| Ambiente | Rama origen | Uso                                    |
|----------|-------------|----------------------------------------|
| **prod** | `main`      | Versión estable para clientes          |
| **staging** | `develop` | Pruebas de versiones y mejoras antes de prod |

### Configuración recomendada en Railway

1. **Proyecto prod**: conectar al repo, branch `main`, variables de prod.
2. **Proyecto staging**: conectar al mismo repo, branch `develop`, variables de staging.
3. No usar fallback a `localhost` en variables; definir `NEXT_PUBLIC_API_URL` por ambiente.

### Backend para staging (staging → develop)

Para que el frontend staging pueda iniciar sesión, el backend debe estar desplegado y configurado. Ejemplo con backend en `https://qaback.nougram.co` y frontend en `https://qa.nougram.co`:

**1. Crear servicio Backend en Railway**
- Nuevo servicio en el mismo proyecto (o uno dedicado a staging)
- Root directory: `backend`
- Branch: `develop`
- Build: Nixpacks detecta Python, o usar **Dockerfile** en `backend/` (recomendado: el Dockerfile ya ejecuta `alembic upgrade head` antes de Gunicorn).
- Start command: opcional. Si usas el Dockerfile, no hace falta; si usas Nixpacks, pon: `alembic upgrade head && gunicorn main:app -c gunicorn_config.py -w 1 -b 0.0.0.0:$PORT`
- Puerto: Railway inyecta `PORT`; exponer con `0.0.0.0:$PORT`

**2. Variables de entorno del Backend (staging)**

| Variable | Valor | Nota |
|----------|-------|------|
| `DATABASE_URL` | `postgresql+asyncpg://...` | Postgres de Railway (addon) |
| `SECRET_KEY` | clave segura | Distinta a prod si quieres aislar sesiones |
| `CORS_ORIGINS` | `https://qa.nougram.co` | **URL exacta del frontend staging** (sin barra final) |
| `FRONTEND_URL` | `https://qa.nougram.co` | Para links de invitación/reset |
| `ENVIRONMENT` | `staging` o `production` | En prod no crea tablas; usa Alembic |

**3. Dominio público**
- Asignar dominio custom `qaback.nougram.co` al servicio backend, o usar el `.railway.app` que da Railway.

**4. Variables del Frontend staging**
- `NEXT_PUBLIC_API_URL` = `https://qaback.nougram.co/api/v1` (base del API, sin barra final)

**Errores frecuentes**
- **"Error de conexión"**: backend no alcanzable. Revisar que la URL sea correcta y que el backend esté en ejecución.
- **CORS**: si el frontend está en otro dominio, `CORS_ORIGINS` debe incluir esa URL exactamente.
- **Ruta truncada**: `NEXT_PUBLIC_API_URL` debe terminar en `/api/v1` (no `/api/v`).

---

## Ramas temporales (crear al trabajar)

| Prefijo   | Desde  | Merge a    | Uso                            |
|-----------|--------|------------|--------------------------------|
| `feature/` | develop | develop  | Nuevas funcionalidades         |
| `fix/`    | develop | develop  | Correcciones y refactors       |
| `release/` | develop | main + develop | Preparar release a prod |
| `hotfix/` | main    | main + develop | Urgencias en producción |

---

## Flujos de trabajo

### Nueva funcionalidad

```bash
git checkout develop
git pull origin develop
git checkout -b feature/nombre-descriptivo
# ... desarrollo, commits ...
git push origin feature/nombre-descriptivo
# Abrir PR hacia develop; merge cuando pase revisión.
```

### Corrección / mejora

```bash
git checkout develop
git pull origin develop
git checkout -b fix/descripcion
# ... trabajo, commits ...
git push origin fix/descripcion
# PR hacia develop.
```

### Publicar a producción

```bash
git checkout develop
git pull origin develop
git checkout -b release/v1.2.0
# Ajustes de versión, changelog, etc.
# PR hacia main; al mergear, Railway despliega a prod.
git checkout main
git merge --no-ff release/v1.2.0
git tag v1.2.0
git push origin main --tags
# Merge de vuelta a develop
git checkout develop
git merge release/v1.2.0
git push origin develop
# Eliminar rama
git branch -d release/v1.2.0
```

### Hotfix urgente (producción)

```bash
git checkout main
git pull origin main
git checkout -b hotfix/correccion-critica
# ... fix ...
git push origin hotfix/correccion-critica
# PR hacia main
# Tras merge a main: merge también a develop
git checkout develop
git merge hotfix/correccion-critica
git push origin develop
```

---

## Convenciones

- **Commits**: mensajes claros (español/inglés acordado).
- **PRs**: describir qué cambia y qué probar en staging.
- **Staging**: probar antes de mergear a `main`.
- **Prod**: solo desde `main`; sin merges directos de `develop`.

---

## Revisión post-deploy en Railway

Después de un deploy (staging o prod), comprobar:

1. **Backend – migraciones**
   - Si el servicio usa el **Dockerfile** de `backend/`, las migraciones se ejecutan al arrancar (`alembic upgrade head`).
   - En Railway: **Deployments** → último deploy del backend → **View logs**. Deberías ver líneas de Alembic (`Running upgrade ... -> ..., ...`) y luego Gunicorn.
   - Si usas Nixpacks sin Dockerfile, el **Start Command** del servicio debe incluir `alembic upgrade head &&` antes de arrancar la app.

2. **Backend – salud**
   - Abrir `https://<tu-backend>/api/v1/` o `/docs` (staging). Debe responder 200 o cargar Swagger.

3. **Frontend**
   - Abrir la URL del frontend; login y una ruta protegida deben cargar sin error de conexión.

4. **Nuevas tablas (ej. ai_usage_events, financial_ledger_events)**
   - Si añadiste migraciones nuevas, el primer deploy que use el Dockerfile actualizado aplicará las migraciones. Si algo falla, en los logs del backend aparecerá el error de Alembic.
