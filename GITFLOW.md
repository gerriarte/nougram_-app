# GitFlow y Despliegue en Railway

Flujo de trabajo basado en GitFlow con ambientes **prod** y **staging** en Railway.

---

## Ramas permanentes

| Rama   | Uso                      | Railway     |
|--------|--------------------------|-------------|
| `main` | Producción estable       | **prod**    |
| `develop` | Integración / pruebas | **staging** |

---

## Despliegue en Railway

| Ambiente | Rama origen | Uso                                    |
|----------|-------------|----------------------------------------|
| **prod** | `main`      | Versión estable para clientes          |
| **staging** | `develop` | Pruebas de versiones y mejoras antes de prod |

### Configuración recomendada en Railway

1. **Proyecto prod**: conectar al repo, branch `main`, variables de prod.
2. **Proyecto staging**: conectar al mismo repo, branch `develop`, variables de staging.
3. No usar fallback a `localhost` en variables; definir `NEXT_PUBLIC_API_URL` por ambiente.

---

## Ramas temporales (crear al trabajar)

| Prefijo   | Desde  | Merge a    | Uso                            |
|-----------|--------|------------|--------------------------------|
| `feature/` | develop | develop  | Nuevas funcionalidades         |
| `fix/`    | develop | develop  | Correcciones y refactors       |
| `release/` | develop | main + develop | Preparar release a prod |
| `hotfix/` | main    | main + develop | Urgencias en producción |

---

## Flujos de trabajo

### Nueva funcionalidad

```bash
git checkout develop
git pull origin develop
git checkout -b feature/nombre-descriptivo
# ... desarrollo, commits ...
git push origin feature/nombre-descriptivo
# Abrir PR hacia develop; merge cuando pase revisión.
```

### Corrección / mejora

```bash
git checkout develop
git pull origin develop
git checkout -b fix/descripcion
# ... trabajo, commits ...
git push origin fix/descripcion
# PR hacia develop.
```

### Publicar a producción

```bash
git checkout develop
git pull origin develop
git checkout -b release/v1.2.0
# Ajustes de versión, changelog, etc.
# PR hacia main; al mergear, Railway despliega a prod.
git checkout main
git merge --no-ff release/v1.2.0
git tag v1.2.0
git push origin main --tags
# Merge de vuelta a develop
git checkout develop
git merge release/v1.2.0
git push origin develop
# Eliminar rama
git branch -d release/v1.2.0
```

### Hotfix urgente (producción)

```bash
git checkout main
git pull origin main
git checkout -b hotfix/correccion-critica
# ... fix ...
git push origin hotfix/correccion-critica
# PR hacia main
# Tras merge a main: merge también a develop
git checkout develop
git merge hotfix/correccion-critica
git push origin develop
```

---

## Convenciones

- **Commits**: mensajes claros (español/inglés acordado).
- **PRs**: describir qué cambia y qué probar en staging.
- **Staging**: probar antes de mergear a `main`.
- **Prod**: solo desde `main`; sin merges directos de `develop`.
