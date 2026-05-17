# Troubleshooting - Nougram

Este documento contiene soluciones a problemas comunes que pueden surgir durante el desarrollo y despliegue de Nougram.

## Problemas de Base de Datos

### Error: "Table already exists" durante migraciones

**Síntoma:** Alembic falla con error de tabla ya existe.

**Solución:**
```bash
# Verificar estado de migraciones
cd backend
alembic current

# Si hay migraciones pendientes, aplicarlas
alembic upgrade head

# Si hay conflictos, revisar el historial
alembic history
```

### Error: "UNIQUE constraint failed" en tests

**Síntoma:** Tests fallan con errores de constraint único.

**Solución:**
- Asegurarse de que los fixtures de test usen datos únicos (emails, códigos, etc.)
- Usar UUIDs o timestamps para generar valores únicos en tests
- Limpiar la base de datos de test antes de ejecutar tests

## Problemas de Autenticación

### Token JWT expirado o inválido

**Síntoma:** Error 401 Unauthorized en todas las peticiones.

**Solución:**
- Hacer logout y login nuevamente
- Verificar que el token en localStorage no esté corrupto
- Verificar que el backend esté usando la misma clave secreta

### Error al cambiar de organización

**Síntoma:** El OrganizationSwitcher no funciona correctamente.

**Solución:**
- Verificar que el endpoint `/api/v1/auth/switch-organization` esté disponible
- Verificar que el usuario tenga permisos para acceder a la organización solicitada
- Verificar que el token se actualice en localStorage después del cambio

## Problemas de Frontend

### Error: "Module not found" o imports rotos

**Síntoma:** Errores de compilación en Next.js.

**Solución:**
```bash
cd frontend
# Limpiar cache y reinstalar dependencias
rm -rf .next node_modules
npm install
npm run dev
```

### Error: "Cannot find module '@/...'"

**Síntoma:** TypeScript no encuentra módulos con alias @.

**Solución:**
- Verificar que `tsconfig.json` tenga configurado correctamente el path alias
- Reiniciar el servidor de TypeScript en VS Code (Ctrl+Shift+P > "TypeScript: Restart TS Server")

## Problemas de Backend

### Error: "Port already in use"

**Síntoma:** El backend no puede iniciar porque el puerto 8000 está ocupado.

**Solución:**
```bash
# Windows - Encontrar proceso usando el puerto
netstat -ano | findstr :8000

# Matar el proceso (reemplazar PID con el número encontrado)
taskkill /PID <PID> /F

# O cambiar el puerto en .env
PORT=8001
```

### Error: "Redis connection failed" (Celery)

**Síntoma:** Celery no puede conectarse a Redis.

**Solución:**
- Verificar que Redis esté corriendo: `docker ps` (si usa Docker)
- Verificar variables de entorno: `CELERY_BROKER_URL` y `CELERY_RESULT_BACKEND`
- Reiniciar servicios de Docker: `docker-compose restart redis celery_worker celery_beat`

## Problemas de Docker

### Error: "Container name already exists"

**Síntoma:** Docker no puede crear contenedores porque ya existen.

**Solución:**
```bash
# Detener y eliminar contenedores existentes
docker-compose down

# Si persiste, forzar eliminación
docker-compose down --remove-orphans
docker-compose up -d
```

### Error: "Volume mount failed"

**Síntoma:** Docker no puede montar volúmenes.

**Solución:**
- Verificar permisos de carpetas
- En Windows, verificar que Docker Desktop tenga acceso a las unidades compartidas
- Verificar rutas en `docker-compose.yml` (usar rutas relativas cuando sea posible)

## Problemas de Tests

### Tests fallan intermitentemente

**Síntoma:** Algunos tests pasan y otros fallan sin razón aparente.

**Solución:**
- Verificar que los tests no compartan estado (usar fixtures únicos)
- Ejecutar tests en modo verbose para ver el orden: `pytest -v`
- Verificar que no haya condiciones de carrera en tests asíncronos

### Error: "Database is locked" en tests SQLite

**Síntoma:** Tests fallan con error de base de datos bloqueada.

**Solución:**
- Asegurarse de que cada test cierre correctamente sus sesiones de base de datos
- Usar `async_sessionmaker` con `expire_on_commit=False` en fixtures
- Verificar que no haya transacciones abiertas sin commit/rollback

## Problemas de CI/CD

### GitHub Actions falla en linting

**Síntoma:** El workflow de linting falla con errores de formato.

**Solución:**
```bash
# Ejecutar ruff localmente para ver errores
cd backend
ruff check .
ruff format .

# Corregir automáticamente
ruff check --fix .
ruff format .
```

### GitHub Actions falla en tests

**Síntoma:** Tests pasan localmente pero fallan en CI.

**Solución:**
- Verificar que las variables de entorno estén configuradas en GitHub Secrets
- Verificar que la versión de Python en CI coincida con la local
- Revisar logs de CI para ver errores específicos

## Problemas de Performance

### Backend lento o con timeouts

**Síntoma:** Las peticiones tardan mucho o fallan con timeout.

**Solución:**
- Verificar logs del backend para identificar queries lentas
- Revisar índices de base de datos
- Verificar que el caché esté funcionando correctamente
- Revisar uso de memoria y CPU

### Frontend lento al cargar

**Síntoma:** La aplicación frontend tarda mucho en cargar.

**Solución:**
- Verificar que no haya bundles muy grandes (usar `npm run build` para analizar)
- Verificar que las imágenes estén optimizadas
- Revisar Network tab en DevTools para identificar recursos lentos

## Contacto y Soporte

Si encuentras un problema que no está documentado aquí:

1. Revisar los logs del backend: `scripts/utils/ver_logs_backend.ps1`
2. Revisar la consola del navegador para errores de frontend
3. Verificar el estado de los servicios: `scripts/deployment/verificar_servicios.bat`
4. Consultar la documentación en [documentación principal](2026-02-07-README.md) (`docs/2026-02-07-README.md`)

---

**Última actualización:** Diciembre 2025




