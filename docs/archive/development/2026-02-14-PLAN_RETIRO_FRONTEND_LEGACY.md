# Plan de Retiro Frontend Legacy (`frontend`)

Fecha: 2026-02-14  
Estado: En curso (Fase 1 completada, Fase 3 en progreso)

## Objetivo

Consolidar `nougram_front` como frontend principal y retirar `frontend` de manera controlada, sin interrumpir despliegues ni flujos críticos.

## Alcance

- Frontend principal: `nougram_front`
- Frontend legacy a retirar: `frontend`
- Configuraciones de despliegue: `railway.json`, `docker-compose.prod.yml`, `README.md`

## Fase 1: Canonicalización (completada)

- Se define `nougram_front` como frontend oficial del repositorio.
- Se actualiza documentación raíz para comandos de arranque/build con `nougram_front`.
- Se actualizan rutas de build/deploy en Railway a `nougram_front`.
- Se actualiza Docker Compose de producción para construir desde `nougram_front`.
- Se agrega `Dockerfile` en `nougram_front` para despliegue contenedorizado.

## Fase 2: Congelamiento Legacy (pendiente)

- No agregar nuevas funcionalidades en `frontend`.
- Permitir únicamente fixes críticos temporales si bloquean producción.
- Agregar aviso de deprecación en `frontend/README.md` indicando migración activa.

## Fase 3: Validación previa a retiro (pendiente)

- Smoke test funcional sobre `nougram_front`:
  - login
  - registro + onboarding
  - dashboard
  - crear/editar/enviar cotización
  - tracking de cotización
- Validación de build:
  - `npm run build` en `nougram_front`
  - despliegue Railway exitoso
  - despliegue Docker Compose producción exitoso
- Validación backend:
  - CORS y `FRONTEND_URL` apuntando al frontend nuevo
  - flujo de correo (SMTP) validado con mensaje de error explícito en UI

### Avance actual Fase 3

- `nougram_front` build validado exitosamente (`npm run build`).
- Scripts y despliegue principal actualizados a `nougram_front`:
  - `railway.json`
  - `docker-compose.prod.yml`
  - `Procfile`
  - `scripts/frontend/iniciar_frontend.bat`
  - `scripts/start-localhost.sh`
  - `scripts/start-localhost.ps1`
  - `scripts/deployment/desplegar_local.bat`
  - `scripts/deployment/desplegar_localhost.bat`

### Pendientes detectados (residuales)

- No quedan referencias operativas en scripts a `http://localhost:5000` ni a `cd frontend`.
- Se mantiene pendiente únicamente la eliminación física de `frontend` (Fase 4), después de smoke test final y un ciclo de release estable.

## Fase 4: Retiro definitivo (pendiente)

- Eliminar carpeta `frontend` y referencias residuales.
- Actualizar scripts/documentación que aún usen `frontend`.
- Ejecutar regresión rápida post-retiro.

## Criterios de salida

- No existen referencias activas a `frontend` en build/deploy principal.
- `nougram_front` cubre flujos operativos críticos.
- Build y despliegue productivo estables por al menos un ciclo de release.
