# Logging Format - Nougram

Este documento describe el formato de logs utilizado en Nougram y cómo se estructura la información de logging.

## Formato de Logs

Nougram utiliza un sistema de logging estructurado que cambia de formato según el entorno:

- **Desarrollo**: Formato legible para humanos (human-readable)
- **Producción**: Formato JSON para fácil ingesta en herramientas de observabilidad

## Formato JSON (Producción)

En producción, los logs se emiten en formato JSON con la siguiente estructura:

```json
{
  "timestamp": "2025-12-28T20:00:00.000Z",
  "level": "INFO",
  "module": "credit_service",
  "function": "consume_credits",
  "message": "Consumed 50 credits for organization 1. Remaining: 50",
  "context": {
    "organization_id": 1,
    "user_id": 42,
    "amount": 50,
    "remaining": 50
  },
  "trace_id": "abc123def456",
  "span_id": "span789"
}
```

### Campos Estándar

| Campo | Tipo | Descripción | Requerido |
|-------|------|-------------|-----------|
| `timestamp` | string (ISO 8601) | Timestamp UTC del log | Sí |
| `level` | string | Nivel de log (DEBUG, INFO, WARNING, ERROR) | Sí |
| `module` | string | Nombre del módulo donde se generó el log | Sí |
| `function` | string | Nombre de la función donde se generó el log | Sí |
| `message` | string | Mensaje del log | Sí |
| `context` | object | Contexto adicional como objeto JSON | Opcional |
| `trace_id` | string | ID de traza para distributed tracing | Opcional |
| `span_id` | string | ID de span para distributed tracing | Opcional |
| `exception` | string | Stack trace de excepción (solo en ERROR) | Opcional |

## Formato Legible (Desarrollo)

En desarrollo, los logs se emiten en formato legible:

```
2025-12-28 20:00:00 | INFO     | credit_service        | consume_credits    | Consumed 50 credits for organization 1. Remaining: 50 | Context: {"organization_id": 1, "user_id": 42, "amount": 50, "remaining": 50} | trace_id: abc123def456 | span_id: span789
```

## Uso del Logger

### Importación

```python
from app.core.logging import get_logger

logger = get_logger(__name__)
```

### Logging Básico

```python
logger.info("User logged in successfully")
```

### Logging con Contexto

```python
logger.info(
    "Quote created",
    extra={
        "quote_id": 123,
        "project_id": 456,
        "organization_id": 1
    }
)
```

### Logging con Keyword Arguments

```python
logger.info(
    "Credit consumed",
    organization_id=1,
    user_id=42,
    amount=50,
    remaining=50
)
```

### Logging de Errores

```python
try:
    # código que puede fallar
    pass
except Exception as e:
    logger.error(
        "Failed to process payment",
        exc_info=True,
        payment_id=789,
        error=str(e)
    )
```

### Distributed Tracing

Para soportar distributed tracing, puedes establecer trace_id y span_id:

```python
logger.set_trace_context(trace_id="abc123", span_id="span789")
logger.info("Processing request")
```

## Configuración

El formato de logs se controla mediante la variable de entorno `ENVIRONMENT`:

- `ENVIRONMENT=development` → Formato legible
- `ENVIRONMENT=production` → Formato JSON
- `ENVIRONMENT=prod` → Formato JSON

## Integración con Herramientas de Observabilidad

### ELK Stack (Elasticsearch, Logstash, Kibana)

Los logs JSON pueden ser ingeridos directamente por Logstash:

```ruby
input {
  stdin {
    codec => json
  }
}
```

### Datadog

Los logs JSON son compatibles con Datadog. Configura el log collector para parsear JSON automáticamente.

### CloudWatch

AWS CloudWatch puede ingerir logs JSON directamente. Configura el agente de CloudWatch para enviar logs.

### Grafana Loki

Loki puede ingerir logs JSON. Configura el promtail para parsear los logs.

## Mejores Prácticas

1. **Siempre incluir contexto relevante**: Agrega información que ayude a debuggear problemas
2. **Usar niveles apropiados**: 
   - `DEBUG`: Información detallada para debugging
   - `INFO`: Eventos importantes del sistema
   - `WARNING`: Situaciones anómalas que no son errores
   - `ERROR`: Errores que requieren atención
3. **No incluir información sensible**: Evita logs de contraseñas, tokens, datos personales sensibles
4. **Usar trace_id para requests**: Establece trace_id al inicio de cada request para rastrear operaciones distribuidas
5. **Contexto estructurado**: Usa objetos JSON para contexto en lugar de strings concatenados

## Ejemplos de Uso

### Endpoint de API

```python
from app.core.logging import get_logger
from fastapi import Request

logger = get_logger(__name__)

@router.post("/quotes")
async def create_quote(request: Request, ...):
    # Establecer trace context desde headers
    trace_id = request.headers.get("X-Trace-Id")
    if trace_id:
        logger.set_trace_context(trace_id=trace_id)
    
    logger.info(
        "Creating quote",
        organization_id=current_user.organization_id,
        user_id=current_user.id
    )
    
    # ... código del endpoint
    
    logger.info(
        "Quote created successfully",
        quote_id=quote.id,
        project_id=quote.project_id
    )
```

### Servicio

```python
from app.core.logging import get_logger

logger = get_logger(__name__)

class CreditService:
    async def consume_credits(self, org_id: int, amount: int, user_id: int):
        logger.info(
            "Consuming credits",
            organization_id=org_id,
            amount=amount,
            user_id=user_id
        )
        
        # ... lógica del servicio
        
        logger.info(
            "Credits consumed",
            organization_id=org_id,
            amount=amount,
            remaining=account.credits_available
        )
```

---

**Última actualización:** Diciembre 2025




