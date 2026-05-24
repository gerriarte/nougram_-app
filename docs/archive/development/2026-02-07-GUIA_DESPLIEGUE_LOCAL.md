# Guía de Despliegue Local - Nougram

**Fecha:** 2026-01-25  
**Sistema Operativo:** Windows

---

## Requisitos Previos

1. **Docker Desktop** instalado y corriendo
2. **Python 3.11+** instalado
3. **Node.js 18+** y npm instalados
4. **Git** instalado

---

## Opción 1: Despliegue Automático (Recomendado)

### Paso 1: Iniciar Docker Desktop

1. Abre Docker Desktop desde el menú de inicio
2. Espera a que Docker Desktop termine de iniciar completamente (ícono de ballena en la bandeja del sistema)
3. Verifica que Docker esté corriendo: deberías ver "Docker Desktop is running" en la bandeja

### Paso 2: Ejecutar Script de Despliegue

```powershell
cd c:\Users\Usuario\Documents\GitHub\Cotizador
.\scripts\deployment\desplegar_localhost.bat
```

**Este script automáticamente:**
- ✅ Verifica Docker Desktop
- ✅ Inicia PostgreSQL en Docker (puerto 5435)
- ✅ Verifica/crea archivo `.env` del backend
- ✅ Verifica/crea entorno virtual de Python
- ✅ Instala dependencias del backend
- ✅ Instala dependencias del frontend
- ✅ Ejecuta migraciones de base de datos
- ✅ Inicia Backend en nueva ventana (http://localhost:8000)
- ✅ Inicia Frontend en nueva ventana (http://localhost:5000)

---

## Opción 2: Despliegue Manual (Paso a Paso)

### Paso 1: Iniciar PostgreSQL con Docker

```powershell
cd c:\Users\Usuario\Documents\GitHub\Cotizador
docker-compose up -d
```

**Verificar que PostgreSQL está corriendo:**
```powershell
docker ps
```

Deberías ver un contenedor `nougram-postgres` corriendo.

---

### Paso 2: Configurar Backend

**2.1. Verificar/Crear archivo .env:**

```powershell
cd backend
```

Si no existe `.env`, crearlo:
```powershell
python setup_env.py
```

**2.2. Verificar/Crear entorno virtual:**

```powershell
# Si no existe venv
python -m venv venv

# Activar entorno virtual
.\venv\Scripts\activate

# Instalar dependencias
pip install --upgrade pip
pip install -r requirements.txt
```

**2.3. Ejecutar migraciones:**

```powershell
alembic upgrade head
```

**2.4. Iniciar Backend:**

```powershell
python main.py
```

El backend debería estar disponible en: **http://localhost:8000**

---

### Paso 3: Configurar Frontend

**3.1. Instalar dependencias:**

```powershell
cd ..\frontend
npm install
```

**3.2. Iniciar Frontend:**

```powershell
npm run dev
```

El frontend debería estar disponible en: **http://localhost:3000** o **http://localhost:5000** (según configuración)

---

## Verificación de Servicios

### Verificar que todo está corriendo:

**Backend:**
- Abre navegador: http://localhost:8000/docs
- Deberías ver la documentación de Swagger/OpenAPI

**Frontend:**
- Abre navegador: http://localhost:3000 (o http://localhost:5000)
- Deberías ver la aplicación React/Next.js

**PostgreSQL:**
```powershell
docker ps | findstr postgres
```

---

## Solución de Problemas

### Error: "Docker Desktop no está corriendo"

**Solución:**
1. Abre Docker Desktop manualmente
2. Espera a que termine de iniciar
3. Ejecuta el script nuevamente

---

### Error: "Puerto 5435 ya está en uso"

**Solución:**
```powershell
# Ver qué está usando el puerto
netstat -ano | findstr :5435

# Detener contenedor existente
docker-compose down

# Iniciar nuevamente
docker-compose up -d
```

---

### Error: "No se puede conectar a PostgreSQL"

**Verificar:**
1. PostgreSQL está corriendo: `docker ps`
2. Puerto correcto en `.env`: `localhost:5435`
3. Credenciales correctas: `postgres:postgres`

**Probar conexión:**
```powershell
docker exec -it nougram-postgres psql -U postgres -d nougram_db
```

---

### Error: "ModuleNotFoundError" en Backend

**Solución:**
```powershell
cd backend
.\venv\Scripts\activate
pip install -r requirements.txt
```

---

### Error: "npm ERR!" en Frontend

**Solución:**
```powershell
cd frontend
# Limpiar cache
npm cache clean --force
# Reinstalar
rm -rf node_modules package-lock.json
npm install
```

---

## Detener Servicios

### Detener Backend y Frontend:
- Cierra las ventanas de terminal donde están corriendo
- O presiona `Ctrl+C` en cada ventana

### Detener PostgreSQL:
```powershell
docker-compose down
```

### Detener todo:
```powershell
docker-compose down
# Luego cierra las ventanas de Backend y Frontend
```

---

## URLs de Acceso

- **Backend API:** http://localhost:8000
- **Backend Docs (Swagger):** http://localhost:8000/docs
- **Backend Docs (ReDoc):** http://localhost:8000/redoc
- **Frontend:** http://localhost:3000 (o http://localhost:5000 según configuración)

---

## Configuración de Base de Datos

**Conexión:**
- Host: `localhost`
- Puerto: `5435`
- Usuario: `postgres`
- Contraseña: `postgres`
- Base de datos: `nougram_db` (o `agenciops_db` según configuración)

**String de conexión en .env:**
```
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5435/nougram_db
```

---

## Próximos Pasos

1. **Crear usuario inicial:**
   - El sistema debería tener un script para crear el primer usuario
   - O usar el endpoint de registro si está disponible

2. **Configurar organización:**
   - Crear organización inicial
   - Configurar costos fijos
   - Agregar miembros del equipo

3. **Explorar funcionalidades:**
   - Crear servicios
   - Crear cotizaciones
   - Ver dashboard

---

**Última actualización:** 2026-01-25
