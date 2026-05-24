# 🚀 Inicio Rápido - Nougram

Guía para iniciar el proyecto completo (Backend + Frontend + Base de Datos)

---

## ⚡ Inicio Rápido (Recomendado)

### Opción 1: Script Automático (Windows)

```bash
start_dev.bat
```

Este script inicia automáticamente:
- ✅ Backend en `http://localhost:8000`
- ✅ Frontend en `http://localhost:3000`
- ✅ Base de datos PostgreSQL (si está configurada)

---

## 📋 Inicio Manual

### 1. Iniciar Base de Datos PostgreSQL

```bash
# Opción A: Docker Compose (recomendado)
docker-compose up -d postgres

# Opción B: PostgreSQL local
# Asegúrate de que PostgreSQL esté corriendo en el puerto configurado
```

**Verificar que PostgreSQL esté corriendo:**
```bash
# Verificar contenedor Docker
docker ps | findstr postgres

# O verificar conexión
psql -U postgres -h localhost -p 5435 -d nougram_db
```

### 2. Iniciar Backend

#### Windows:
```bash
scripts\backend\iniciar_backend.bat
```

#### Linux/Mac:
```bash
cd backend
source venv/bin/activate  # o venv\Scripts\activate en Windows
python main.py
```

**O manualmente:**
```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Verificar que el backend esté corriendo:**
- Abre: `http://localhost:8000`
- Deberías ver: `{"message": "Nougram API is running", "version": "1.0.0", "status": "healthy"}`
- Health check: `http://localhost:8000/health`

### 3. Iniciar Frontend

#### Windows:
```bash
scripts\frontend\iniciar_frontend.bat
```

#### Linux/Mac:
```bash
cd frontend
npm install  # Solo la primera vez
npm run dev
```

**Verificar que el frontend esté corriendo:**
- Abre: `http://localhost:3000`
- Deberías ver la página de login

---

## ⚠️ Solución de Problemas

### Error: "El servidor backend no está disponible"

**Causas comunes:**

1. **Backend no está corriendo**
   ```bash
   # Verificar procesos
   netstat -ano | findstr :8000
   
   # Si no hay nada, iniciar backend
   scripts\backend\iniciar_backend.bat
   ```

2. **Puerto 8000 ocupado**
   ```bash
   # Ver qué está usando el puerto 8000
   netstat -ano | findstr :8000
   
   # Cambiar puerto en backend/main.py línea 117:
   uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
   
   # Y actualizar frontend/.env.local:
   NEXT_PUBLIC_API_URL=http://localhost:8001/api/v1
   ```

3. **Base de datos no disponible**
   ```bash
   # Verificar que PostgreSQL esté corriendo
   docker ps | findstr postgres
   
   # Si no está corriendo:
   docker-compose up -d postgres
   ```

4. **Variables de entorno faltantes**
   ```bash
   # Verificar que existe backend/.env
   # Si no existe, crear:
   cd backend
   python setup_env.py
   ```

### Error: "No se puede conectar a la base de datos"

**Solución:**
```bash
# 1. Verificar que PostgreSQL esté corriendo
docker ps | findstr postgres

# 2. Verificar DATABASE_URL en backend/.env
# Debe ser: postgresql+asyncpg://postgres:postgres@localhost:5435/nougram_db

# 3. Verificar conexión
cd backend
python scripts/validate_database_config.py
```

### Error: "CORS policy"

**Solución:**
- Verificar que `CORS_ORIGINS` en `backend/.env` incluya `http://localhost:3000`
- Reiniciar el backend después de cambiar `.env`

---

## 🔍 Verificación Completa

### Checklist de Inicio

- [ ] PostgreSQL corriendo (puerto 5435 o 5432)
- [ ] Base de datos `nougram_db` existe
- [ ] Migraciones aplicadas (`alembic upgrade head`)
- [ ] Backend corriendo en `http://localhost:8000`
- [ ] Frontend corriendo en `http://localhost:3000`
- [ ] Puedes acceder a `http://localhost:8000/health`
- [ ] Puedes acceder a `http://localhost:3000`

### Comandos de Verificación

```bash
# 1. Verificar PostgreSQL
docker ps | findstr postgres

# 2. Verificar Backend
curl http://localhost:8000/health
# O abrir en navegador: http://localhost:8000

# 3. Verificar Frontend
curl http://localhost:3000
# O abrir en navegador: http://localhost:3000

# 4. Verificar configuración de BD
cd backend
python scripts/validate_database_config.py
```

---

## 📝 Configuración Inicial

### 1. Crear archivo `.env` en backend

```bash
cd backend
python setup_env.py
```

Esto crea `backend/.env` con:
- `DATABASE_URL` configurado para `nougram_db`
- `SECRET_KEY` generado automáticamente
- Variables de Google OAuth (valores dummy para desarrollo)

### 2. Aplicar migraciones

```bash
cd backend
alembic upgrade head
```

### 3. Verificar super admin

```bash
cd backend
python scripts/check_super_admin.py
```

Si no existe, el usuario se crea automáticamente con:
- Email: `gerriarte@abralatam.com`
- Contraseña: `Abracolombia`

---

## 🎯 URLs Importantes

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000/api/v1
- **Backend Health**: http://localhost:8000/health
- **Backend Docs**: http://localhost:8000/docs (Swagger UI)
- **PostgreSQL**: localhost:5435 (o 5432 según configuración)

---

## 🛑 Detener Servicios

### Detener Backend/Frontend
- Presiona `Ctrl+C` en las ventanas de terminal

### Detener PostgreSQL (Docker)
```bash
docker-compose down
```

### Detener Todo
```bash
# Detener contenedores Docker
docker-compose down

# Cerrar ventanas de terminal manualmente
```

---

**Última actualización:** 30 de Diciembre, 2025

