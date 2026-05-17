# Guía: Ejecutar en Localhost con Funcionalidades de Producción

## Fecha: 2026-02-14

## Objetivo

Ejecutar la aplicación completa en localhost **sin mocks ni hardcoding**, con todas las funcionalidades conectadas al backend real.

---

## ✅ Cambios Realizados

### Frontend - Servicios Reales Implementados

1. **`serviceService.ts`** - Conectado a `/api/v1/services`
2. **`taxService.ts`** - Conectado a `/api/v1/taxes`
3. **`resourceService.ts`** - Conectado a `/api/v1/settings/team`
4. **`useAuth.ts`** - Conectado a `/api/v1/auth/me`
5. **`QuoteBuilderContext.tsx`** - Carga datos reales del backend

### Eliminados
- ❌ `MOCK_SERVICES` en QuoteBuilderContext
- ❌ `MOCK_TAXES` en QuoteBuilderContext
- ❌ `MOCK_TEAM_MEMBERS` en resourceService
- ❌ Mock de usuario en useAuth

---

## 🚀 Inicio Rápido

### Opción 1: Script Automático (Recomendado)

#### Windows (PowerShell)
```powershell
.\scripts\start-localhost.ps1
```

#### Linux/Mac (Bash)
```bash
chmod +x scripts/start-localhost.sh
./scripts/start-localhost.sh
```

### Opción 2: Manual

#### 1. Verificar PostgreSQL

```bash
# Con Docker
docker-compose up -d postgres

# O verificar que PostgreSQL esté corriendo en localhost:5435
```

#### 2. Configurar Backend

```bash
cd backend

# Crear .env si no existe
python setup_env.py

# Crear y activar entorno virtual
python -m venv venv

# Windows
.\venv\Scripts\Activate.ps1

# Linux/Mac
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar migraciones
python -m alembic upgrade head
```

#### 3. Configurar Frontend

```bash
cd frontend

# Crear .env.local si no existe
echo "NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1" > .env.local

# Instalar dependencias
npm install
```

#### 4. Iniciar Servicios

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate  # o .\venv\Scripts\Activate.ps1 en Windows
python -m uvicorn main:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

#### 5. Acceder a la Aplicación

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## 🔐 Autenticación

### Crear Usuario y Organización

1. **Registrar Organización:**
```bash
curl -X POST http://localhost:8000/api/v1/organizations/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Mi Agencia",
    "email": "admin@agencia.com",
    "password": "password123",
    "full_name": "Admin User"
  }'
```

2. **Login:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@agencia.com",
    "password": "password123"
  }'
```

3. **Guardar Token:**
   - Copia el `access_token` de la respuesta
   - En el navegador, abre DevTools > Application > Local Storage
   - Agrega: `auth_token` = `<access_token>`

### O usar el Frontend

1. Navega a http://localhost:3000/register
2. Completa el formulario de registro
3. El token se guardará automáticamente

---

## 📊 Datos Iniciales

### Crear Servicios

```bash
curl -X POST http://localhost:8000/api/v1/services \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Desarrollo Frontend",
    "pricing_type": "hourly",
    "default_margin_target": 0.40
  }'
```

### Crear Impuestos

```bash
curl -X POST http://localhost:8000/api/v1/taxes \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "IVA",
    "percentage": 19.0,
    "country": "CO"
  }'
```

### Crear Miembros del Equipo

```bash
curl -X POST http://localhost:8000/api/v1/settings/team \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Juan Pérez",
    "role": "Lead Developer",
    "monthly_salary": 5000000,
    "billable_hours_per_month": 138.56,
    "currency": "COP"
  }'
```

---

## ✅ Verificación

### Verificar que No Hay Mocks

1. **Frontend - Servicios:**
   - Abre http://localhost:3000/quotes/new
   - Los servicios deben cargarse desde el backend
   - Si no hay servicios, verás lista vacía (no mocks)

2. **Frontend - Impuestos:**
   - En el mismo formulario
   - Los impuestos deben cargarse desde el backend

3. **Frontend - Equipo:**
   - En la sección de asignación de recursos
   - Los miembros deben cargarse desde el backend

4. **Frontend - Usuario:**
   - El usuario debe cargarse desde `/api/v1/auth/me`
   - Verifica en DevTools > Network que se hace la llamada

### Verificar Backend

```bash
# Health check
curl http://localhost:8000/health

# Servicios (requiere autenticación)
curl http://localhost:8000/api/v1/services \
  -H "Authorization: Bearer <token>"

# Impuestos
curl http://localhost:8000/api/v1/taxes \
  -H "Authorization: Bearer <token>"

# Equipo
curl http://localhost:8000/api/v1/settings/team \
  -H "Authorization: Bearer <token>"
```

---

## 🐛 Troubleshooting

### Error: "Cannot connect to backend"

1. Verifica que el backend esté corriendo en puerto 8000
2. Verifica `NEXT_PUBLIC_API_URL` en `frontend/.env.local`
3. Verifica CORS en `backend/.env`:
   ```
   CORS_ORIGINS=http://localhost:3000
   ```

### Error: "Unauthorized" o "401"

1. Verifica que tengas un token válido en `localStorage`
2. Verifica que el token no haya expirado
3. Haz login nuevamente

### Error: "Services/Taxes/Team empty"

1. Verifica que hayas creado datos en el backend
2. Verifica que estés autenticado
3. Verifica los logs del backend para errores

### Error: "Database connection refused"

1. Verifica que PostgreSQL esté corriendo:
   ```bash
   docker ps | grep postgres
   ```
2. Verifica `DATABASE_URL` en `backend/.env`
3. Verifica que el puerto sea correcto (5435 para desarrollo)

### Error: "Migration errors"

```bash
cd backend
python -m alembic current
python -m alembic upgrade head
```

---

## 📝 Checklist de Verificación

- [ ] PostgreSQL corriendo
- [ ] Backend `.env` configurado
- [ ] Frontend `.env.local` configurado
- [ ] Migraciones ejecutadas
- [ ] Backend corriendo en puerto 8000
- [ ] Frontend corriendo en puerto 3000
- [ ] Usuario creado y autenticado
- [ ] Token guardado en localStorage
- [ ] Servicios creados en backend
- [ ] Impuestos creados en backend
- [ ] Miembros del equipo creados
- [ ] Frontend carga datos del backend (no mocks)
- [ ] No hay errores en consola del navegador
- [ ] No hay errores en logs del backend

---

## 🎯 Próximos Pasos

Una vez que todo esté funcionando:

1. **Crear datos de prueba** usando los scripts o la API
2. **Probar funcionalidades completas:**
   - Crear cotización
   - Asignar recursos
   - Calcular márgenes
   - Generar PDF/DOCX
   - Enviar por email

3. **Verificar Dashboard:**
   - KPIs deben cargarse desde `/api/v1/dashboard/kpis`
   - Pipeline de cotizaciones desde `/api/v1/quotes`

---

## 📚 Archivos Modificados

- `frontend/src/services/serviceService.ts` (nuevo)
- `frontend/src/services/taxService.ts` (nuevo)
- `frontend/src/services/resourceService.ts` (actualizado)
- `frontend/src/context/QuoteBuilderContext.tsx` (actualizado)
- `frontend/src/hooks/useAuth.ts` (actualizado)
- `scripts/start-localhost.sh` (nuevo)
- `scripts/start-localhost.ps1` (nuevo)

---

## ✅ Estado Final

**Todas las funcionalidades están conectadas al backend real:**
- ✅ Servicios desde `/api/v1/services`
- ✅ Impuestos desde `/api/v1/taxes`
- ✅ Equipo desde `/api/v1/settings/team`
- ✅ Usuario desde `/api/v1/auth/me`
- ✅ Cotizaciones desde `/api/v1/quotes`
- ✅ Dashboard desde `/api/v1/dashboard/kpis`

**Sin mocks ni hardcoding en producción.**
