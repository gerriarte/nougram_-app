# Configuración de Railway - Guía Completa

## Problema: Railway busca `/app/index.js` en lugar de ejecutar Next.js

Railway está intentando ejecutar Node.js directamente buscando `/app/index.js` en lugar de ejecutar la aplicación Next.js correctamente.

## Soluciones Implementadas

### 1. Archivos de Configuración Creados

#### `Procfile` (raíz del proyecto)
```
web: cd frontend && npm start
```

#### `frontend/Procfile`
```
web: npm start
```

#### `railway.json` (raíz)
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "cd frontend && npm start",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

#### `frontend/railway.json`
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

#### `nixpacks.toml` (raíz)
```toml
[phases.setup]
nixPkgs = ["nodejs-20_x", "npm-10_x"]

[phases.install]
cmds = ["cd frontend && npm ci --production=false"]

[phases.build]
cmds = ["cd frontend && npm run build"]

[start]
cmd = "cd frontend && npm start"
```

#### `frontend/nixpacks.toml`
```toml
[phases.setup]
nixPkgs = ["nodejs-20_x", "npm-10_x"]

[phases.install]
cmds = ["npm ci --production=false"]

[phases.build]
cmds = ["npm run build"]

[start]
cmd = "npm start"
```

### 2. Configuración en Railway Dashboard

**IMPORTANTE**: Debes configurar Railway correctamente en el dashboard:

#### Opción A: Desplegar desde la raíz del proyecto

1. Ve a tu proyecto en Railway
2. Ve a **Settings** → **Service Settings**
3. **Root Directory**: Deja vacío o pon `/` (raíz)
4. **Build Command**: Deja vacío (usa nixpacks.toml)
5. **Start Command**: Deja vacío o pon `cd frontend && npm start`
6. Railway debería detectar automáticamente el `Procfile` o `railway.json`

#### Opción B: Desplegar solo la carpeta frontend (RECOMENDADO)

1. Ve a tu proyecto en Railway
2. Ve a **Settings** → **Service Settings**
3. **Root Directory**: Pon `frontend`
4. **Build Command**: Deja vacío (usa frontend/nixpacks.toml)
5. **Start Command**: Deja vacío o pon `npm start`
6. Railway debería detectar automáticamente el `frontend/Procfile` o `frontend/railway.json`

### 3. Variables de Entorno Requeridas

En Railway Dashboard → Variables:

- `NEXT_PUBLIC_API_URL`: URL de tu backend (ej: `https://tu-backend.railway.app/api/v1`)
- `PORT`: Railway lo asigna automáticamente (no necesitas configurarlo manualmente)

### 4. Verificación del Despliegue

1. **Build Logs**: Deberías ver:
   ```
   Installing dependencies...
   Building Next.js application...
   ```

2. **Deploy Logs**: Deberías ver:
   ```
   Starting Next.js server...
   Ready on http://0.0.0.0:PORT
   ```

3. **Si ves el error `/app/index.js`**: Railway no está usando la configuración correcta. Verifica:
   - Root Directory está configurado correctamente
   - Los archivos `Procfile` o `railway.json` están en el repositorio
   - El Start Command está configurado o Railway detecta el Procfile

## Solución de Problemas

### Error: "Cannot find module '/app/index.js'"

**Causa**: Railway está intentando ejecutar Node.js directamente en lugar de Next.js.

**Soluciones**:

1. **Verifica el Root Directory**:
   - Si despliegas desde la raíz: Root Directory = `/` o vacío
   - Si despliegas solo frontend: Root Directory = `frontend`

2. **Verifica el Start Command**:
   - Desde la raíz: `cd frontend && npm start`
   - Solo frontend: `npm start`
   - O deja vacío para que use el Procfile

3. **Verifica que los archivos estén en Git**:
   ```bash
   git add Procfile frontend/Procfile railway.json frontend/railway.json
   git commit -m "Add Railway configuration files"
   git push
   ```

4. **Forzar redeploy**:
   - En Railway Dashboard → Deployments → Click en "Redeploy"

### Error: "Build failed"

**Causa**: Problemas durante el proceso de build.

**Soluciones**:
- Revisa los logs de build en Railway
- Verifica que todas las dependencias estén en `package.json`
- Asegúrate de que no haya errores de TypeScript o ESLint

### Error: "Port already in use"

**Causa**: Conflicto de puertos.

**Solución**: Railway asigna el puerto automáticamente a través de la variable `PORT`. El script `start` ya está configurado para usar `${PORT:-3000}`.

## Recomendación Final

**Usa la Opción B (Root Directory = `frontend`)** porque:
- Es más simple y directo
- Railway detecta automáticamente Next.js desde el `package.json` en `frontend/`
- Menos problemas de rutas y configuración
- Los archivos de configuración están en el lugar correcto

## Pasos Finales

1. Configura el Root Directory en Railway Dashboard
2. Haz commit y push de todos los archivos de configuración
3. Espera a que Railway detecte los cambios y haga el deploy
4. Verifica los logs para confirmar que está ejecutando `npm start` correctamente
