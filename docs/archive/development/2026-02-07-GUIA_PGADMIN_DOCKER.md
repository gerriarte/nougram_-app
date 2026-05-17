# Guía: Conectar pgAdmin con PostgreSQL en Docker

**Fecha:** 2026-01-25

---

## Configuración Actual

Se ha agregado **pgAdmin 4** como servicio adicional en `docker-compose.yml` para administrar la base de datos PostgreSQL desde una interfaz gráfica.

---

## Acceso a pgAdmin

**URL:** http://localhost:5050

**Credenciales de acceso:**
- **Email:** `admin@nougram.com`
- **Contraseña:** `admin`

---

## Configurar Conexión a PostgreSQL desde pgAdmin

### Paso 1: Acceder a pgAdmin

1. Abre tu navegador en: http://localhost:5050
2. Ingresa las credenciales:
   - Email: `admin@nougram.com`
   - Password: `admin`

### Paso 2: Agregar Servidor PostgreSQL

1. Click derecho en **"Servers"** → **"Register"** → **"Server"**

2. En la pestaña **"General":**
   - **Name:** `Nougram PostgreSQL` (o el nombre que prefieras)

3. En la pestaña **"Connection":**
   - **Host name/address:** `postgres` (nombre del servicio en Docker)
   - **Port:** `5432` (puerto interno del contenedor)
   - **Maintenance database:** `nougram_db`
   - **Username:** `postgres`
   - **Password:** `postgres`
   - ✅ Marcar **"Save password"** (opcional)

4. Click en **"Save"**

---

## Información de Conexión

### Desde pgAdmin (dentro de Docker):
- **Host:** `postgres` (nombre del servicio)
- **Port:** `5432` (puerto interno)
- **Database:** `nougram_db`
- **Username:** `postgres`
- **Password:** `postgres`

### Desde aplicación externa (fuera de Docker):
- **Host:** `localhost`
- **Port:** `5435` (puerto externo mapeado)
- **Database:** `nougram_db`
- **Username:** `postgres`
- **Password:** `postgres`

---

## Verificar que pgAdmin está corriendo

```powershell
docker ps --filter "name=nougram-pgadmin"
```

Deberías ver:
```
CONTAINER ID   IMAGE                    STATUS         PORTS
xxxxx          dpage/pgadmin4:latest   Up X minutes   0.0.0.0:5050->80/tcp
```

---

## Solución de Problemas

### Error: "No se puede conectar al servidor"

**Verificar que PostgreSQL está corriendo:**
```powershell
docker ps --filter "name=nougram-postgres"
```

**Verificar red de Docker:**
```powershell
docker network inspect cotizador_nougram_network
```

Ambos contenedores (`postgres` y `pgadmin`) deben estar en la misma red.

---

### Error: "pgAdmin no inicia"

**Ver logs:**
```powershell
docker logs nougram-pgadmin
```

**Reiniciar servicios:**
```powershell
docker-compose restart pgadmin
```

---

### Cambiar credenciales de pgAdmin

Edita `docker-compose.yml`:
```yaml
pgadmin:
  environment:
    PGADMIN_DEFAULT_EMAIL: tu-email@ejemplo.com
    PGADMIN_DEFAULT_PASSWORD: tu-password-segura
```

Luego reinicia:
```powershell
docker-compose up -d pgadmin
```

---

## Funcionalidades de pgAdmin

Una vez conectado, podrás:

- ✅ Ver todas las tablas de la base de datos
- ✅ Ejecutar queries SQL
- ✅ Ver estructura de tablas y relaciones
- ✅ Inspeccionar datos
- ✅ Crear/modificar/eliminar tablas (con cuidado)
- ✅ Ver índices y constraints
- ✅ Exportar/importar datos
- ✅ Ver logs de PostgreSQL

---

## Seguridad

**⚠️ IMPORTANTE:**
- Las credenciales por defecto (`admin/admin`) son solo para desarrollo local
- **NO uses estas credenciales en producción**
- Cambia las credenciales antes de desplegar en producción

---

**Última actualización:** 2026-01-25
