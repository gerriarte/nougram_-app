
# Nougram Backend Rules (Python MVC + Repository/Service)

## Architecture Overview
Follow the layered architecture strictly: Controller -> Service -> Repository -> ORM -> Database.
[cite_start]Each layer must only know about the layer immediately below it.

## Directory Structure
Maintain the following folder hierarchy:
- [cite_start]`app/models/`: Entity definitions and ORM mapping (SQLAlchemy).
- [cite_start]`app/repositories/`: Data access and persistence logic.
- [cite_start]`app/services/`: Business logic and orchestration between repositories.
- [cite_start]`app/controllers/`: Input management and delegation to services.
- [cite_start]`app/views/`: Data presentation logic.
- [cite_start]`database/`: Infrastructure, connection, and migrations.

## Naming Conventions
- [cite_start]Files: `snake_case` (e.g., `usuario_repository.py`).
- [cite_start]Classes: `PascalCase` (e.g., `UsuarioRepository`).
- [cite_start]Suffixes: Always include the layer in the name (e.g., `Service`, `Repository`, `Controller`, `Model`).

## Implementation Constraints
- [cite_start]**Models**: No SQL queries, no business logic, no session handling.
- **Repositories**: Encapsulate all ORM/SQL logic. [cite_start]Methods should be clear like `obtener_por_id` or `guardar`.
- **Services**: All business rules and validations must live here. [cite_start]Avoid "Fat Controllers".
- **Controllers**: Keep them thin. [cite_start]Do not access the database directly.
- [cite_start]**Imports**: Always use absolute imports from the project root.