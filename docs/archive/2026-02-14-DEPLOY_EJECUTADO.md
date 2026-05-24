# Deploy Ejecutado - Localhost

## Fecha: 2026-02-14

## ✅ Estado del Deploy

### Servicios Iniciados

1. **PostgreSQL** ✅
   - Puerto: 5435
   - Estado: Corriendo (healthy)
   - Contenedor: `nougram-postgres`

2. **Backend API** ✅
   - Puerto: 8000
   - Estado: Iniciado en background (con --reload)
   - URL: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - **Error corregido**: Agregado `Any` a imports en `ai_service.py`

3. **Frontend** ✅
   - Puerto: 3002 (3000 estaba ocupado)
   - Estado: Iniciado en background
   - URL: http://localhost:3002
   - **Nota**: El puerto 3000 estaba ocupado, usando 3002

### Migraciones Aplicadas

- ✅ `q2r3s4t5u6v7` (head) - Quote public link fields
- ✅ `m20251230` (head) - Migrate money to numeric

### Correcciones Aplicadas

- ✅ Corregido import de `Any` en `backend/app/services/ai_service.py`

---

## 🔗 URLs de Acceso

- **Frontend**: http://localhost:3002 (o http://localhost:3000 si está libre)
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

---

## 📋 Próximos Pasos

### 1. Verificar que los Servicios Estén Corriendo

```powershell
# Backend
Invoke-WebRequest -Uri http://localhost:8000/health

# Frontend (puerto 3002)
Invoke-WebRequest -Uri http://localhost:3002
```

### 2. Crear Usuario y Organización

**Opción A: Desde el Frontend**
1. Navega a http://localhost:3002/register
2. Completa el formulario de registro
3. El token se guardará automáticamente

**Opción B: Desde la API**
```bash
# Registrar organización
curl -X POST http://localhost:8000/api/v1/organizations/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Mi Agencia",
    "email": "admin@agencia.com",
    "password": "password123",
    "full_name": "Admin User"
  }'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@agencia.com",
    "password": "password123"
  }'
```

### 3. Crear Datos Iniciales

Una vez autenticado, crear:

**Servicios:**
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

**Impuestos:**
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

**Miembros del Equipo:**
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

### Backend
```powershell
Invoke-WebRequest -Uri http://localhost:8000/health
# Debe responder: {"status":"healthy"}
```

### Frontend
- Abre http://localhost:3002
- Debe cargar la aplicación sin errores
- Verifica en DevTools > Network que las llamadas al API funcionen

---

## 🐛 Troubleshooting

### Si el backend no responde:
1. Verifica los logs en la terminal del backend
2. Verifica que PostgreSQL esté corriendo: `docker ps | grep postgres`
3. Verifica la conexión: `Invoke-WebRequest -Uri http://localhost:8000/health`

### Si el frontend no carga:
1. Verifica los logs en la terminal del frontend
2. Verifica que el backend esté corriendo
3. Verifica `.env.local`: `NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1`
4. **Nota**: El frontend está en puerto 3002 porque 3000 estaba ocupado

### Si hay errores de autenticación:
1. Verifica que tengas un token válido en `localStorage`
2. Haz login nuevamente desde el frontend
3. Verifica que el token no haya expirado

### Si el puerto 3000 está ocupado:
- El frontend automáticamente usará el siguiente puerto disponible (3002)
- Actualiza la URL en el navegador a http://localhost:3002

---

## 📝 Notas

- Los servicios están corriendo en **background**
- Para detenerlos, usa `Ctrl+C` en las terminales correspondientes
- Los logs se guardan en archivos temporales
- PostgreSQL está corriendo en Docker y persistirá los datos
- El backend tiene `--reload` activado, se reiniciará automáticamente ante cambios

---

## 🎯 Estado Final

✅ **Backend**: Corriendo en puerto 8000 (con auto-reload)
✅ **Frontend**: Corriendo en puerto 3002  
✅ **Base de Datos**: PostgreSQL corriendo y migraciones aplicadas
✅ **Sin Mocks**: Todo conectado al backend real
✅ **Error Corregido**: Import de `Any` en ai_service.py

**La aplicación está lista para usar en localhost.**

**Accede a:** http://localhost:3002
