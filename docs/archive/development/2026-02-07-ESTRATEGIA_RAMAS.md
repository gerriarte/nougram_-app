# Estrategia de Ramas - Git Flow

## Estructura de Ramas

### Ramas Principales

#### `main`
- **Propósito**: Código de producción estable
- **Protección**: Solo merge desde `develop` o `hotfix/*`
- **Política**: Requiere code review y tests pasando
- **Deploy**: Automático a producción

#### `develop`
- **Propósito**: Código de desarrollo integrado
- **Protección**: Merge desde `feature/*` y `bugfix/*`
- **Política**: Debe estar estable para testing
- **Deploy**: Automático a ambiente de staging

### Ramas de Soporte

#### `feature/*`
- **Propósito**: Nuevas funcionalidades
- **Nomenclatura**: `feature/nombre-descriptivo` (ej: `feature/refactor-mvc-architecture`)
- **Origen**: Siempre desde `develop`
- **Destino**: Merge a `develop` cuando esté completo
- **Lifetime**: Temporal, se elimina después del merge

**Ejemplos**:
- `feature/refactor-mvc-architecture`
- `feature/add-equipment-amortization`
- `feature/resource-allocation`

#### `bugfix/*`
- **Propósito**: Correcciones de bugs en desarrollo
- **Nomenclatura**: `bugfix/descripcion-bug` (ej: `bugfix/fix-quote-calculation`)
- **Origen**: Siempre desde `develop`
- **Destino**: Merge a `develop`
- **Lifetime**: Temporal, se elimina después del merge

#### `hotfix/*`
- **Propósito**: Correcciones urgentes para producción
- **Nomenclatura**: `hotfix/descripcion-urgente` (ej: `hotfix/fix-security-vulnerability`)
- **Origen**: Siempre desde `main`
- **Destino**: Merge a `main` y `develop`
- **Lifetime**: Temporal, se elimina después del merge

## Flujo de Trabajo

### Crear Nueva Feature

```bash
# 1. Asegurarse de estar en develop actualizado
git checkout develop
git pull origin develop

# 2. Crear rama feature
git checkout -b feature/nombre-feature

# 3. Trabajar en la feature
# ... hacer commits ...

# 4. Push de la rama
git push origin feature/nombre-feature

# 5. Crear Pull Request a develop
# (usar interfaz de GitHub/GitLab)

# 6. Después del merge, eliminar rama local
git checkout develop
git pull origin develop
git branch -d feature/nombre-feature
```

### Crear Hotfix Urgente

```bash
# 1. Crear rama desde main
git checkout main
git pull origin main
git checkout -b hotfix/descripcion-urgente

# 2. Hacer cambios y commits
# ... hacer commits ...

# 3. Push de la rama
git push origin hotfix/descripcion-urgente

# 4. Crear Pull Request a main
# (usar interfaz de GitHub/GitLab)

# 5. Después del merge a main, merge también a develop
git checkout develop
git merge main
git push origin develop
```

## Convenciones de Commits

### Formato
```
<tipo>(<alcance>): <descripción>

[descripción detallada opcional]

[footer opcional]
```

### Tipos de Commit

- `feat`: Nueva funcionalidad
- `fix`: Corrección de bug
- `refactor`: Refactorización de código
- `docs`: Cambios en documentación
- `test`: Agregar o modificar tests
- `style`: Cambios de formato (no afectan funcionalidad)
- `chore`: Tareas de mantenimiento
- `perf`: Mejoras de rendimiento
- `ci`: Cambios en CI/CD

### Ejemplos

```
feat(projects): Agregar endpoint para crear nueva versión de quote

- Implementar lógica de versionado en ProjectService
- Agregar validación de margen mínimo
- Crear tests unitarios

Refs: #123
```

```
refactor(services): Eliminar acceso directo a DB en ServiceService

- Mover queries a ServiceRepository
- Agregar métodos get_usage_count() y get_all_deleted()
- Actualizar endpoints para usar repositorios
```

## Pull Requests

### Título
Debe seguir el formato de commits: `<tipo>(<alcance>): <descripción>`

### Descripción
Debe incluir:
1. **Resumen**: Qué cambia y por qué
2. **Cambios técnicos**: Detalles de implementación
3. **Testing**: Cómo se probó
4. **Checklist**:
   - [ ] Código sigue las convenciones del proyecto
   - [ ] Tests pasan
   - [ ] Documentación actualizada
   - [ ] Sin errores de linting

### Ejemplo de PR

```markdown
## Resumen
Refactorizar módulo de Projects para implementar arquitectura MVC + Repository/Service

## Cambios Técnicos
- Crear ProjectController y ProjectView
- Refactorizar ProjectService para usar solo repositorios
- Eliminar queries directas de endpoints
- Agregar métodos a ProjectRepository

## Testing
- [x] Tests unitarios pasan
- [x] Tests de integración pasan
- [x] Manual testing completado

## Checklist
- [x] Código sigue convenciones
- [x] Tests pasan
- [x] Documentación actualizada
- [x] Sin errores de linting
```

## Protección de Ramas

### `main`
- Requiere Pull Request
- Requiere aprobación de al menos 1 reviewer
- Requiere que todos los checks pasen
- No permite push directo

### `develop`
- Requiere Pull Request
- Requiere que todos los checks pasen
- No requiere aprobación (auto-merge si checks pasan)

## Mejores Prácticas

1. **Commits frecuentes**: Hacer commits pequeños y frecuentes
2. **Mensajes descriptivos**: Usar mensajes claros y descriptivos
3. **Una feature por rama**: No mezclar múltiples features en una rama
4. **Actualizar develop**: Mantener la rama feature actualizada con develop
5. **Limpiar ramas**: Eliminar ramas después del merge

## Comandos Útiles

```bash
# Ver ramas locales y remotas
git branch -a

# Ver ramas remotas eliminadas
git remote prune origin

# Actualizar develop y rebase feature
git checkout develop
git pull origin develop
git checkout feature/mi-feature
git rebase develop

# Ver commits en una rama
git log develop..feature/mi-feature

# Ver diferencias entre ramas
git diff develop..feature/mi-feature
```

## Referencias

- [Git Flow](https://nvie.com/posts/a-successful-git-branching-model/)
- [Conventional Commits](https://www.conventionalcommits.org/)
