# Celery Setup Guide

Esta guía explica cómo configurar y usar Celery para tareas programadas en Nougram.

## Descripción General

Celery se utiliza para ejecutar tareas programadas, específicamente:
- **Reseteo mensual de créditos**: Tarea que se ejecuta diariamente para verificar y resetear los créditos mensuales de las organizaciones activas.

## Arquitectura

```
Celery Beat (Scheduler)
    ↓
Redis (Message Broker)
    ↓
Celery Worker (Task Executor)
    ↓
Database (PostgreSQL)
```

## Configuración

### Variables de Entorno

Agregar las siguientes variables al archivo `.env`:

```env
# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### Docker Compose

El `docker-compose.yml` incluye los siguientes servicios:

1. **Redis**: Broker de mensajes para Celery
2. **celery_worker**: Worker que ejecuta las tareas
3. **celery_beat**: Scheduler que programa las tareas periódicas

### Archivos de Configuración

- `backend/app/core/celery_app.py`: Configuración de la aplicación Celery
- `backend/app/core/tasks.py`: Definición de tareas Celery
- `backend/app/core/config.py`: Variables de configuración

## Tareas Disponibles

### reset_monthly_credits

**Descripción**: Resetea los créditos mensuales de todas las organizaciones activas que necesiten un reseteo.

**Programación**: Se ejecuta diariamente a las 00:00 UTC

**Funcionalidad**:
1. Obtiene todas las organizaciones activas
2. Para cada organización, verifica si `next_reset_at <= now()`
3. Si es necesario, llama a `CreditService.grant_subscription_credits()`
4. Actualiza `last_reset_at` y `next_reset_at`

**Logs**: La tarea registra:
- Número de organizaciones verificadas
- Número de reseteos realizados
- Número de errores encontrados
- Errores específicos por organización

## Ejecución

### Desarrollo Local (sin Docker)

1. **Iniciar Redis**:
```bash
redis-server
```

2. **Iniciar Celery Worker**:
```bash
cd backend
celery -A app.core.celery_app worker --loglevel=info
```

3. **Iniciar Celery Beat**:
```bash
cd backend
celery -A app.core.celery_app beat --loglevel=info
```

### Producción (con Docker)

```bash
docker-compose up -d redis celery_worker celery_beat
```

O iniciar todos los servicios:

```bash
docker-compose up -d
```

## Verificación

### Verificar que Celery Worker está funcionando

```bash
celery -A app.core.celery_app inspect active
```

### Verificar tareas programadas (Beat)

```bash
celery -A app.core.celery_app inspect scheduled
```

### Ver logs de Celery

```bash
# Worker logs
docker-compose logs -f celery_worker

# Beat logs
docker-compose logs -f celery_beat
```

### Ejecutar tarea manualmente (para testing)

```bash
cd backend
python -c "from app.core.tasks import reset_monthly_credits; reset_monthly_credits()"
```

O usando Celery:

```bash
celery -A app.core.celery_app call app.core.tasks.reset_monthly_credits
```

## Agregar Nueva Tarea

1. **Definir la tarea en `backend/app/core/tasks.py`**:

```python
@celery_app.task(name="app.core.tasks.mi_nueva_tarea")
def mi_nueva_tarea():
    """
    Descripción de la tarea
    """
    import asyncio
    asyncio.run(_mi_nueva_tarea_async())


async def _mi_nueva_tarea_async():
    # Lógica de la tarea aquí
    pass
```

2. **Si es una tarea periódica, agregar a `celery_app.py`**:

```python
celery_app.conf.beat_schedule = {
    # ... tareas existentes ...
    "mi-tarea-periodica": {
        "task": "app.core.tasks.mi_nueva_tarea",
        "schedule": 3600.0,  # Cada hora (en segundos)
        "options": {
            "timezone": "UTC"
        }
    },
}
```

3. **Registrar la tarea en `celery_app.py`**:

Asegúrate de que el módulo esté incluido en el `include`:

```python
celery_app = Celery(
    "nougram",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.core.tasks"]  # Ya incluye tasks.py
)
```

## Troubleshooting

### Worker no ejecuta tareas

1. Verificar que Redis está corriendo
2. Verificar que las variables de entorno están configuradas
3. Verificar logs del worker para errores

### Beat no programa tareas

1. Verificar que Beat está corriendo
2. Verificar configuración de `beat_schedule` en `celery_app.py`
3. Verificar logs de Beat

### Tareas fallan con errores de base de datos

1. Verificar que `DATABASE_URL` está correctamente configurada
2. Verificar que la base de datos está accesible desde el worker
3. Verificar logs del worker para errores específicos

### Redis connection errors

1. Verificar que Redis está corriendo
2. Verificar que `CELERY_BROKER_URL` apunta al Redis correcto
3. Verificar firewall/red si Redis está en otro servidor

## Notas Importantes

- Las tareas Celery se ejecutan en procesos separados, por lo que cada tarea crea su propia conexión a la base de datos
- Para desarrollo, puedes ejecutar worker y beat en la misma terminal usando:
  ```bash
  celery -A app.core.celery_app worker --beat --loglevel=info
  ```
- En producción, es recomendable ejecutar worker y beat en procesos separados para mejor escalabilidad
- Los logs de Celery incluyen información detallada sobre el progreso de las tareas




