# Git Release Flow

Flujo recomendado para trabajar con ramas `develop` y `main` en este proyecto.

## Objetivo

- `develop`: integración continua de cambios diarios.
- `main`: rama estable para deploy (Railway debe apuntar aquí).

## Reglas base

- No trabajar directo en `main`.
- Todo cambio entra por PR.
- Antes de abrir PR, correr `npm run build` en el frontend.
- Mantener `package-lock.json` bajo control (si cambia, se decide explícitamente si se commitea).

## 1) Crear fix o feature

Partir de `develop` actualizado:

```bash
git checkout develop
git pull origin develop
git checkout -b fix/nombre-del-fix
# o: feat/nombre-feature
```

Validar build local:

```bash
npm run build
```

Commit y push:

```bash
git add .
git commit -m "fix: descripcion corta"
git push -u origin HEAD
```

Crear PR hacia `develop`.

## 2) Integrar cambios diarios en develop

Cuando un PR esté aprobado y mergeado:

```bash
git checkout develop
git pull origin develop
```

## 3) Publicar release a producción

Cuando `develop` esté estable:

```bash
git checkout main
git pull origin main
git merge --no-ff develop -m "release: sync develop into main"
git push origin main
```

Luego, relanzar deploy en Railway si no se despliega automáticamente.

## 4) Sincronizar develop después de release (opcional)

Recomendado para evitar divergencias si hubo hotfixes en `main`:

```bash
git checkout develop
git pull origin develop
git merge --no-ff main -m "chore: sync main back into develop"
git push origin develop
```

## Checklist antes de push

- `git status` limpio o con cambios esperados.
- Build local OK (`npm run build`).
- Rama de destino correcta (`develop` para integración, `main` para deploy).
- Railway configurado para desplegar desde `main`.

## Errores comunes y cómo evitarlos

- **Railway construye código viejo**: verificar rama configurada y SHA del deploy.
- **`next: not found`**: validar instalación de dependencias en entorno de build y que `next` esté en `dependencies`.
- **Errores por mayúsculas/minúsculas**: usar imports con casing exacto (Linux es case-sensitive).
- **Archivos de debug rompen TypeScript**: excluir `src/scripts/**/*` del `tsconfig` productivo.
