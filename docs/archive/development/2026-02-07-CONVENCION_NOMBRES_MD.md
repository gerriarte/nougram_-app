# Convención de nombres para archivos Markdown

**Fecha de creación:** 2026-02-07

## Regla

Todos los archivos `.md` del proyecto (actuales y futuros) deben tener **la fecha de creación al inicio del nombre**, en formato:

```text
YYYY-MM-DD-Nombre-Descriptivo.md
```

- **YYYY-MM-DD:** fecha de creación del documento (ISO 8601).
- **Nombre-Descriptivo:** nombre en mayúsculas/snake_case que describa el contenido.

## Ejemplos

- `2026-02-07-PLAN_TRABAJO_COTIZACION_BACKEND.md`
- `2025-12-13-PRD.md`
- `2026-02-07-README.md` (índice de una carpeta)
- `2025-12-30-TROUBLESHOOTING.md`

## Cómo obtener la fecha

- **Documentos nuevos:** usar la fecha del día en que se crea el archivo.
- **Documentos existentes migrados:** usar la fecha del primer commit de git del archivo, p. ej.  
  `git log --follow -1 --format=%ci -- ruta/al/archivo.md`

## Excepciones

- Los archivos dentro de `node_modules/`, `venv/` y dependencias de terceros no se renombran.
- Los `README.md` de carpetas tienen prefijo con fecha (p. ej. `2026-02-07-README.md`).
- **Raíz del repo:** GitHub muestra por defecto un archivo `README.md` en la raíz. Si el README principal se renombró a `YYYY-MM-DD-README.md`, puedes crear un `README.md` en la raíz que enlace al document principal, o restaurar el nombre para la portada del repositorio.

## Script de renombrado

El script `scripts/rename_md_with_date.ps1` renombra los `.md` del proyecto (excluyendo node_modules/venv) usando la fecha del último commit. Para nuevos archivos sin commit, se usa la fecha del día. Ejecutar desde la raíz del repo:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/rename_md_with_date.ps1
```

---

*Este documento define la convención para que todos los Markdown del repositorio incluyan la fecha de creación en el nombre.*
