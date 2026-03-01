# GitFlow y Ramas (Nougram)

## Ramas y Railway
- **main** → despliegue en **prod**
- **develop** → despliegue en **staging**

## Crear ramas
Usar prefijos según el tipo de trabajo:
- `feature/nombre-descriptivo` – funcionalidades (desde `develop`)
- `fix/descripcion` – correcciones (desde `develop`)
- `release/vX.Y.Z` – preparar versión a prod (desde `develop`)
- `hotfix/descripcion` – urgencias en prod (desde `main`)

## Flujo
1. Crear rama desde la base correcta.
2. Trabajar y hacer commits.
3. PR hacia rama destino; revisar y mergear.
4. Para prod: merge a `main` solo tras pruebas en staging.

Ver detalles en `GITFLOW.md` (raíz del repo).
