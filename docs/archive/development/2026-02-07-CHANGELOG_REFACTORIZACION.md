# Changelog - Refactorización Arquitectura MVC

## [Unreleased] - 2026-01-25

### Added
- **Arquitectura MVC + Repository/Service completa**
  - Capa de Controllers: BaseController, ProjectController, QuoteController, ServiceController
  - Capa de Views: BaseView, ProjectView, QuoteView, ServiceView
  - ServiceService para gestión de servicios

- **Repositorios mejorados**
  - ProjectRepository: métodos `get_max_quote_version()`, `get_quote_with_relationships()`, `associate_taxes()`
  - ServiceRepository: métodos `get_usage_count()`, `get_all_deleted()`

- **Documentación**
  - `REFACTORIZACION_ARQUITECTURA_MVC.md`: Documentación completa de la refactorización
  - `ESTRATEGIA_RAMAS.md`: Estrategia Git Flow y convenciones de ramas
  - `.cursorrules/nougram_backend_rules.md`: Reglas de arquitectura backend

### Changed
- **ProjectService**: Refactorizado completamente para eliminar acceso directo a DB
  - Eliminadas todas las queries SQLAlchemy directas
  - Agregados métodos CRUD completos: `list_projects()`, `get_project_by_id()`, `update_project()`, `delete_project()`, `restore_project()`
  - Uso exclusivo de repositorios

- **Endpoints refactorizados**
  - `backend/app/api/v1/endpoints/projects.py`: 6 endpoints principales refactorizados
  - `backend/app/api/v1/endpoints/services.py`: 6 endpoints principales refactorizados
  - Endpoints ahora solo delegan a Controllers, sin lógica de negocio

### Removed
- Queries directas a DB desde Services (~20+ eliminadas)
- Lógica de negocio de endpoints (movida a Services)
- Transformación de datos de endpoints (movida a Views)

### Fixed
- Separación de responsabilidades según arquitectura MVC
- Cumplimiento estricto de reglas de arquitectura
- Imports absolutos en todos los archivos nuevos

## Estadísticas

- **Archivos creados**: 12
- **Archivos modificados**: 5
- **Líneas agregadas**: ~1,800+
- **Líneas eliminadas**: ~500+
- **Endpoints refactorizados**: 16
- **Queries directas eliminadas**: ~20+

## Módulos Refactorizados

### ✅ Projects Module
- Controller: `ProjectController`
- View: `ProjectView`
- Service: `ProjectService` (refactorizado)
- Endpoints: 6 refactorizados

### ✅ Quotes Module
- Controller: `QuoteController`
- View: `QuoteView`
- Endpoints: 4 refactorizados

### ✅ Services Module
- Controller: `ServiceController`
- View: `ServiceView`
- Service: `ServiceService` (nuevo)
- Endpoints: 6 refactorizados

## Próximos Módulos a Refactorizar

- [ ] Team Module
- [ ] Taxes Module
- [ ] Costs Module
- [ ] Credits Module
- [ ] Insights/Dashboard Module
- [ ] Billing Module
