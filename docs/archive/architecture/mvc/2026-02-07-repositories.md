# Capa de Repositories

**Ubicación:** `backend/app/repositories/`

## Responsabilidades

Los Repositories son responsables de:
- ✅ Todas las queries SQLAlchemy
- ✅ Acceso a datos (CRUD)
- ✅ Tenant scoping automático
- ✅ Manejo de soft delete
- ✅ Eager loading de relaciones cuando es necesario

## Restricciones

- ❌ **NO** contener lógica de negocio
- ❌ **NO** hacer validaciones de negocio
- ❌ **NO** hacer cálculos
- ✅ **SÍ** solo queries SQLAlchemy

## Estructura Base

Todos los Repositories heredan de `BaseRepository`:

```python
from app.repositories.base import BaseRepository
from app.models.my_model import MyModel

class MyRepository(BaseRepository[MyModel]):
    def __init__(self, db, tenant_id: Optional[int] = None):
        super().__init__(db, MyModel, tenant_id)
    
    async def get_all_active(self):
        query = select(MyModel).where(MyModel.deleted_at.is_(None))
        query = self._apply_tenant_filter(query)
        result = await self.db.execute(query)
        return result.scalars().all()
```

## Métodos Disponibles de BaseRepository

- `get_by_id(id)` - Obtener por ID con tenant scoping
- `get_all()` - Obtener todos con tenant scoping
- `create(model)` - Crear nuevo registro
- `update(model)` - Actualizar registro
- `delete(id)` - Eliminar físicamente
- `soft_delete(model, user_id)` - Soft delete
- `restore(model)` - Restaurar soft deleted
- `count()` - Contar registros
- `_apply_tenant_filter(query)` - Aplicar filtro de tenant

## Factory Pattern

Los Repositories se crean usando `RepositoryFactory`:

```python
from app.repositories.factory import RepositoryFactory

# En Service
self.equipment_repo = RepositoryFactory.create_equipment_repository(db, organization_id)
```

## Ejemplos

- **[ProjectRepository](../../../backend/app/repositories/project_repository.py)** - Repository de Proyectos
- **[ServiceRepository](../../../backend/app/repositories/service_repository.py)** - Repository de Servicios
- **[EquipmentRepository](../../../backend/app/repositories/equipment_repository.py)** - Repository de Equipment

## Referencias

- **BaseRepository**: [`backend/app/repositories/base.py`](../../../backend/app/repositories/base.py)
- **RepositoryFactory**: [`backend/app/repositories/factory.py`](../../../backend/app/repositories/factory.py)
- **Arquitectura General**: [2026-02-07-README.md](./2026-02-07-README.md)
