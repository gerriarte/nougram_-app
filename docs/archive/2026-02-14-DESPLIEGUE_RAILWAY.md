# Guía de Despliegue en Railway

## Problema Identificado

Railway estaba intentando ejecutar Node.js directamente buscando `/app/index.js` en lugar de ejecutar la aplicación Next.js correctamente.

## Solución Implementada

Se crearon archivos de configuración para que Railway detecte y ejecute correctamente la aplicación Next.js.

## Archivos de Configuración Creados

### 1. `railway.json` (raíz del proyecto)

Este archivo le dice a Railway cómo construir y ejecutar la aplicación cuando el proyecto raíz se despliega:

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS",
    "buildCommand": "cd frontend && npm install && npm run build"
  },
  "deploy": {
    "startCommand": "cd frontend && npm start",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

### 2. `frontend/railway.json`

Este archivo se usa cuando se despliega solo la carpeta `frontend`:

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "npm start",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

### 3. `nixpacks.toml` (raíz)

Configuración para Nixpacks cuando se despliega desde la raíz:

```toml
[phases.setup]
nixPkgs = ["nodejs-20_x", "npm-10_x"]

[phases.install]
cmds = ["cd frontend && npm ci"]

[phases.build]
cmds = ["cd frontend && npm run build"]

[start]
cmd = "cd frontend && npm start"
```

### 4. `frontend/nixpacks.toml`

Configuración para Nixpacks cuando se despliega solo la carpeta frontend:

```toml
[phases.setup]
nixPkgs = ["nodejs-20_x", "npm-10_x"]

[phases.install]
cmds = ["npm ci"]

[phases.build]
cmds = ["npm run build"]

[start]
cmd = "npm start"
```

## Pasos para Desplegar en Railway

### Opción 1: Desplegar desde la raíz del proyecto

1. En Railway, crea un nuevo proyecto
2. Conecta tu repositorio de GitHub
3. Railway detectará automáticamente el `railway.json` en la raíz
4. Configura las variables de entorno necesarias:
   - `NEXT_PUBLIC_API_URL`: URL de tu backend API
   - `PORT`: Railway lo asignará automáticamente
5. Railway ejecutará:
   - `cd frontend && npm install && npm run build`
   - `cd frontend && npm start`

### Opción 2: Desplegar solo la carpeta frontend

1. En Railway, crea un nuevo proyecto
2. Conecta tu repositorio de GitHub
3. En la configuración del servicio, establece el **Root Directory** a `frontend`
4. Railway detectará automáticamente el `railway.json` en `frontend/`
5. Configura las variables de entorno necesarias
6. Railway ejecutará:
   - `npm ci`
   - `npm run build`
   - `npm start`

## Variables de Entorno Requeridas

### Frontend

- `NEXT_PUBLIC_API_URL`: URL completa de tu backend API (ej: `https://tu-backend.railway.app/api/v1`)
- `PORT`: Railway lo asigna automáticamente, pero puedes sobrescribirlo si es necesario

### Backend (si también lo despliegas en Railway)

- `DATABASE_URL`: URL de conexión a PostgreSQL
- `SECRET_KEY`: Clave secreta para JWT
- `REDIS_URL`: URL de conexión a Redis (opcional)
- Y todas las demás variables de entorno del backend

## Verificación del Despliegue

1. **Build Logs**: Verifica que el build se complete sin errores
2. **Deploy Logs**: Verifica que el servidor Next.js inicie correctamente
3. **Health Check**: Railway debería mostrar el servicio como "Healthy"
4. **URL**: Railway te proporcionará una URL pública para acceder a la aplicación

## Solución de Problemas

### Error: "Cannot find module '/app/index.js'"

**Causa**: Railway está intentando ejecutar Node.js directamente en lugar de Next.js.

**Solución**: 
- Verifica que los archivos `railway.json` y/o `nixpacks.toml` estén presentes
- Asegúrate de que el Root Directory esté configurado correctamente
- Verifica que el `package.json` tenga el script `start` correcto

### Error: "Build failed"

**Causa**: Problemas durante el proceso de build.

**Solución**:
- Revisa los logs de build en Railway
- Verifica que todas las dependencias estén en `package.json`
- Asegúrate de que no haya errores de TypeScript o ESLint

### Error: "Port already in use"

**Causa**: Conflicto de puertos.

**Solución**:
- Railway asigna el puerto automáticamente a través de la variable `PORT`
- El script `start` ya está configurado para usar `${PORT:-3000}`

## Notas Adicionales

- Railway detecta automáticamente Next.js si encuentra `package.json` con Next.js como dependencia
- El modo `standalone` en `next.config.ts` optimiza el build para producción
- Railway usa Nixpacks por defecto, que detecta automáticamente Node.js y Next.js
- Los archivos de configuración creados aseguran que Railway ejecute los comandos correctos en el orden adecuado
