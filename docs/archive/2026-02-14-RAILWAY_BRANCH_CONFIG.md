# Configuración de Branch en Railway

## Estado Actual

- **Repositorio**: https://github.com/gerriarte/nougram_-app
- **Branch con cambios**: `develop` (3 commits adelante de `main`)
- **Commits en develop**:
  1. `8f7c730` - fix: Actualizar Next.js a 16.1.6 y eslint-config-next
  2. `e0b252d` - fix: Agregar Procfile y mejorar configuración de Railway
  3. `40d988b` - feat: Agregar configuración de Railway para despliegue

## Configuración de Railway

Railway puede estar configurado para usar:
- **Branch `main`** (por defecto)
- **Branch `develop`** (si se configuró manualmente)

## Opciones

### Opción 1: Configurar Railway para usar `develop`

En Railway Dashboard:
1. Ve a tu proyecto
2. Settings → Source
3. Cambia el **Branch** de `main` a `develop`
4. Railway detectará automáticamente los cambios

### Opción 2: Hacer merge de `develop` a `main`

Si Railway está usando `main`, necesitas hacer merge:

```bash
git checkout main
git pull origin main
git merge develop
git push origin main
```

## Recomendación

**Usa la Opción 1** (configurar Railway para usar `develop`) porque:
- Mantiene `main` como branch estable
- `develop` es el branch de trabajo activo
- No necesitas hacer merge manual cada vez

## Verificación

Después de configurar el branch en Railway:
1. Railway debería detectar automáticamente los cambios en `develop`
2. Los logs deberían mostrar los commits recientes
3. El despliegue debería usar los archivos de configuración de Railway
