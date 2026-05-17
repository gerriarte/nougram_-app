# Capa de Controllers

**Ubicación:** `backend/app/controllers/`

## Responsabilidades

Los Controllers son responsables de:
- ✅ Validación de requests HTTP
- ✅ Manejo de errores HTTP
- ✅ Logging de operaciones
- ✅ Delegación a Services
- ✅ Transformación de responses usando Views

## Restricciones

- ❌ **NO** acceder directamente a la base de datos
- ❌ **NO** contener lógica de negocio
- ❌ **NO** hacer queries SQLAlchemy
- ❌ **NO** transformar datos directamente (usar Views)

## Estructura Base

Todos los Controllers heredan de `BaseController`:

```python
from app.controllers.base import BaseController

class MyController(BaseController):
    def __init__(self, db: AsyncSession, tenant: TenantContext, current_user: User):
        super().__init__(db, tenant, current_user)
        self.my_service = MyService(db, tenant.organization_id)
        self.my_view = MyView()
    
    async def list_items(self):
        items, total = await self.my_service.list_items()
        return self.my_view.to_paginated_response(items, total, ...)
```

## Métodos Disponibles de BaseController

- `_handle_not_found(resource_type, resource_id)` - Lanzar ResourceNotFoundError
- `_handle_business_error(message)` - Lanzar BusinessLogicError
- `_handle_http_error(status_code, detail)` - Lanzar HTTPException
- `_log_info(message, **kwargs)` - Logging de información
- `_log_error(message, exc_info, **kwargs)` - Logging de errores
- `_log_warning(message, **kwargs)` - Logging de advertencias

## Ejemplos

- **[ProjectController](../../../backend/app/controllers/project_controller.py)** - Controller de Proyectos
- **[ServiceController](../../../backend/app/controllers/service_controller.py)** - Controller de Servicios
- **[QuoteController](../../../backend/app/controllers/quote_controller.py)** - Controller de Quotes

## Referencias

- **BaseController**: [`backend/app/controllers/base.py`](../../../backend/app/controllers/base.py)
- **Arquitectura General**: [2026-02-07-README.md](./2026-02-07-README.md)
