# Propuesta vs Cotizacion (Fuente de Verdad en Backend)

## Objetivo

Separar la **propuesta comercial** del **precio de cotizacion** para permitir:

- cambiar propuesta sin tocar precios;
- cambiar precios/versiones de cotizacion sin tocar propuesta;
- enviar correo combinando `proposal_version` y `quote_version` de forma independiente.

---

## Modelo de datos

Se agrega `proposal_documents` como entidad propia.

Campos clave:

- `project_id`, `organization_id`
- `version` (versionado independiente de `quotes.version`)
- `title`
- `body_json` (estructura flexible para descripcion, objetivos, entregables, resumen, etc.)
- `status` (`draft`, `approved`, `sent`)
- `is_locked` (bloqueo para evitar edicion accidental)
- `created_by_id`, `updated_by_id`

Migracion:

- `backend/alembic/versions/v20260304_add_proposal_documents_table.py`

Modelo:

- `backend/app/models/proposal.py`

Repositorio:

- `backend/app/repositories/proposal_repository.py`

---

## API nueva de propuestas

Base: `/api/v1/projects/{project_id}/proposals`

### 1) Listar propuestas

`GET /api/v1/projects/{project_id}/proposals`

Respuesta:

```json
{
  "items": [
    {
      "id": 10,
      "project_id": 3,
      "organization_id": 1,
      "version": 2,
      "title": "Propuesta comercial V2",
      "body_json": {},
      "status": "draft",
      "is_locked": false
    }
  ],
  "total": 1
}
```

### 2) Crear propuesta (nueva version)

`POST /api/v1/projects/{project_id}/proposals`

Body:

```json
{
  "title": "Propuesta comercial",
  "body_json": {
    "free_text": "Contenido de propuesta"
  },
  "status": "draft"
}
```

### 3) Actualizar propuesta existente

`PUT /api/v1/projects/{project_id}/proposals/{proposal_id}`

Body (parcial):

```json
{
  "title": "Propuesta ajustada",
  "body_json": {
    "description": "Contexto...",
    "objectives": ["Obj 1", "Obj 2"],
    "deliverables": [{"name": "Entregable A", "status": "propuesto"}]
  }
}
```

### 4) Generar propuesta con IA (y guardar version)

`POST /api/v1/projects/{project_id}/proposals/ai-generate`

Body:

```json
{
  "title": "Propuesta IA",
  "language": "es",
  "extra_instructions": "Enfoque ejecutivo"
}
```

Este endpoint:

- toma datos del proyecto + ultima cotizacion;
- usa IA para generar resumen ejecutivo;
- crea una nueva version en `proposal_documents`.

---

## Envio de correo: propuesta y cotizacion desacopladas

El endpoint de envio de quote soporta ahora:

- `proposal_id` (usar propuesta guardada)
- `proposal_message` (override opcional de texto de propuesta)

Schema:

- `backend/app/schemas/quote.py` (`QuoteEmailRequest`)

Regla de prioridad para cuerpo de propuesta en email:

1. propuesta desde `proposal_id` (si existe);
2. `proposal_message`;
3. `quote.notes`;
4. `message` del formulario de envio.

Esto permite enviar:

- misma propuesta con nueva cotizacion;
- nueva propuesta con misma cotizacion;
- o ambas nuevas, de forma independiente.

---

## Frontend implementado

### Servicios

- `nougram_front/src/services/proposalService.ts`
  - `list(projectId)`
  - `getLatest(projectId)`
  - `create(projectId, payload)`
  - `update(projectId, proposalId, payload)`
  - `generateAI(projectId, payload)`

### Pantalla de envio de cotizacion

- `nougram_front/src/app/dashboard/quotes/[id]/send/page.tsx`
  - carga propuesta mas reciente;
  - permite guardar propuesta separada;
  - permite generar propuesta con IA;
  - envia email con `proposalId`.

- `nougram_front/src/components/quotes/QuoteSendView.tsx`
  - editor de propuesta independiente;
  - botones `Generar IA` y `Guardar propuesta`;
  - envio mantiene cotizacion + propuesta desacopladas.

---

## Flujo recomendado de uso

1. Ajustar precios/items en cotizacion (sin tocar propuesta).
2. Editar o regenerar propuesta (sin tocar precios).
3. Guardar propuesta.
4. Enviar correo seleccionando propuesta actual (`proposalId`) y cotizacion vigente.

---

## Notas operativas

- Aplicar migraciones antes de usar endpoints:
  - `alembic upgrade head`
- La propuesta guarda contenido estructurable en `body_json`; se puede evolucionar hacia editor por bloques sin romper compatibilidad.
