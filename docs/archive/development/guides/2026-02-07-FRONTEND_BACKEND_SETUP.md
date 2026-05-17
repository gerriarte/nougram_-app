# Configuración Frontend y Backend

## Requisitos Previos

### 1. Backend (FastAPI)

El backend debe estar corriendo **antes** de usar el frontend.

#### Iniciar el Backend:

```bash
# Navega al directorio del backend
cd backend

# Activa el entorno virtual (si lo tienes)
.\venv\Scripts\Activate.ps1  # Windows PowerShell
# o
source venv/bin/activate  # Linux/Mac

# Inicia el servidor
python -m uvicorn main:app --reload --port 5000
```

Deberías ver algo como:
```
INFO:     Uvicorn running on http://127.0.0.1:5000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

#### Verificar que el Backend está funcionando:

Abre en tu navegador: `http://localhost:5000/docs`

Deberías ver la documentación interactiva de FastAPI (Swagger UI).

### 2. Base de Datos (PostgreSQL)

El backend necesita PostgreSQL corriendo.

#### Iniciar PostgreSQL con Docker:

```bash
# En la raíz del proyecto
docker-compose up -d
```

Verifica que el contenedor está corriendo:
```bash
docker ps
```

Deberías ver un contenedor llamado `nougram-postgres` con estado `Up (healthy)`.

### 3. Frontend (Next.js)

Una vez que el backend está corriendo, inicia el frontend:

```bash
# Navega al directorio del frontend
cd frontend

# Instala dependencias (solo la primera vez)
npm install

# Inicia el servidor de desarrollo
npm run dev
```

Deberías ver:
```
✓ Ready in X.Xs
○ Local:        http://localhost:3000
```

## Orden de Inicio Recomendado

1. **PostgreSQL** (si usas Docker): `docker-compose up -d`
2. **Backend**: `cd backend && python -m uvicorn main:app --reload --port 5000`
3. **Frontend**: `cd frontend && npm run dev`

## Solución de Problemas

### Error: `ERR_CONNECTION_REFUSED`

**Causa:** El backend no está corriendo o no está escuchando en el puerto 5000.

**Solución:**
1. Verifica que el backend esté corriendo en otra terminal
2. Verifica que no haya otro proceso usando el puerto 5000
3. Verifica la URL del API en `frontend/.env.local` o `frontend/src/lib/api-client.ts`

### Error: `Failed to connect to database`

**Causa:** PostgreSQL no está corriendo.

**Solución:**
1. Inicia Docker Desktop
2. Ejecuta `docker-compose up -d`
3. Espera a que el contenedor esté `healthy`
4. Reinicia el backend

### Warning: `Extra attributes from the server: cz-shortcut-listen`

**Causa:** Extensión del navegador (probablemente Czech Keyboard).

**Solución:** Este warning es inofensivo y puede ignorarse. Si molesta, desactiva la extensión del navegador.

### El frontend se conecta pero devuelve 401 Unauthorized

**Causa:** No hay token de autenticación o el token es inválido.

**Solución:**
1. Limpia el localStorage: Abre DevTools → Application → Local Storage → `http://localhost:3000` → Borra `auth_token`
2. Vuelve a iniciar sesión

## Variables de Entorno

### Backend

Crea un archivo `backend/.env`:

```env
DATABASE_URL=postgresql://user:password@localhost:5435/nougram
SECRET_KEY=tu-secret-key-aqui
```

### Frontend

El frontend usa estas variables (definidas en `frontend/src/lib/api-client.ts`):

```env
NEXT_PUBLIC_API_URL=http://localhost:5000/api/v1
```

Si necesitas cambiarla, crea `frontend/.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:5000/api/v1
```

## Puertos

- **Frontend**: `http://localhost:3000`
- **Backend**: `http://localhost:5000`
- **PostgreSQL**: `localhost:5435`

## Comandos Útiles

### Ver logs del backend:
```bash
cd backend
python -m uvicorn main:app --reload --port 5000
```

### Ver logs de Docker:
```bash
docker-compose logs -f postgres
```

### Detener Docker:
```bash
docker-compose down
```

### Detener el backend:
Presiona `Ctrl+C` en la terminal donde está corriendo

### Detener el frontend:
Presiona `Ctrl+C` en la terminal donde está corriendo













