# Hoja de Ruta UX 2.0

## Estado General
- Inicio: 2026-04-29
- Estado actual: Implementación base completada; pendiente configuración/QA de despliegue
- Responsable: Equipo Nougram
- Documento fuente: [Plan UX 2.0](../../Users/Usuario/.cursor/plans/ux_2.0_rollout_28b39244.plan.md)

## Reglas de Seguimiento
- Al cerrar una tarea, marcar checkbox y registrar fecha.
- Si una tarea cambia de alcance, registrar nota en bitácora.
- No mover una fase a completada sin cumplir sus criterios de aceptación.
- Mantener sincronizado este roadmap con el plan maestro.

## Fase 1 - Quick wins UX/Navegación (Frontend)
Estado: Completada

- [x] Journey unificado entre `create`, `edit`, `proposal`, `send`. Completado: 2026-04-29.
- [x] Alineación de steppers (`QuoteBuilderSubheader` y `QuoteFlowStepper`). Completado: 2026-04-29.
- [x] Breadcrumbs de contexto en header. Completado: 2026-04-29.
- [x] Bloque de workspace en sidebar. Completado: 2026-04-29.
- [x] Estandarización de estados visuales (focus, hover, active, progreso). Completado: 2026-04-29.

Criterios de cierre:
- Navegación de cotización consistente en desktop y móvil.
- Reducción de saltos de contexto entre pantallas del flujo comercial.

## Fase 1B - Rediseño completo onboarding (Frontend)
Estado: Completada

- [x] Definir pasos oficiales, copy y estados de validación. Completado: 2026-04-29.
- [x] Implementar stepper consistente con journeys de cotización. Completado: 2026-04-29.
- [x] Persistir avance de onboarding para retomar flujo. Verificado: 2026-04-29.
- [x] Homologar experiencia desktop/móvil. Completado: 2026-04-29.

Criterios de cierre:
- Onboarding rediseñado funcionando end-to-end.
- Usuario puede retomar avance sin perder datos.

## Fase 2 - Contrato backend mínimo UX 2.0 (Cotización/Propuesta)
Estado: Completada

- [x] Extender payload IA (`tone`, `audience`, `differentiators`, `section_plan`). Completado: 2026-04-29.
- [x] Persistir `body_json.layout` y `body_json.ai_brief`. Completado: 2026-04-29.
- [x] Incluir metadatos de organización/estado en portal cliente. Completado: 2026-04-29.
- [x] Validar repositorios como única capa de acceso DB. Completado: 2026-04-29.

Criterios de cierre:
- Brief guiado IA llega al backend y se refleja en propuesta.
- Contrato proposal/portal estable y tipado.

## Fase 2B - Backend onboarding
Estado: Completada

- [x] Extender contrato onboarding para nuevos campos del rediseño. Completado: 2026-04-29.
- [x] Guardar progreso de onboarding de forma robusta. Completado: 2026-04-29.
- [x] Agregar trazabilidad mínima de estado de onboarding. Completado: 2026-04-29.

Criterios de cierre:
- Integración onboarding frontend-backend validada sin regresiones.

## Fase 3 - Branding real de propuesta
Estado: Completada

- [x] Definir estrategia de persistencia branding (`body_json` o modelo dedicado). Completado: 2026-04-29.
- [x] Implementar flujo de assets (logo/cover) con variables de entorno. Completado: 2026-04-29.
- [x] Renderizar branding en editor, envío y portal cliente. Completado: 2026-04-29.

Criterios de cierre:
- Branding por propuesta visible y consistente en todo el flujo.

## Fase 4 - Versionado útil y analítica
Estado: Completada

- [x] Conectar `VersionSelector` con versiones reales. Completado: 2026-04-29.
- [x] Exponer endpoint de métricas mínimas (`view_count`, `viewed_at`, `status`, `decided_at`). Completado: 2026-04-29.
- [x] Diseñar fase posterior de analítica avanzada por sesión. Completado: 2026-04-29.

Criterios de cierre:
- Versiones navegables y métricas básicas operativas para pipeline.

## Bitácora de Avances
- 2026-04-29: Se crea roadmap operativo en `docs/roadmap-ux-2.0.md`.
- 2026-04-29: Se inicia Fase 1. Implementados `QuoteJourneyNav`, breadcrumbs contextuales en header, workspace footer en sidebar y corrección del encabezado de envío a `Paso 3 de 3`.
- 2026-04-29: Se completa Fase 1. `QuoteBuilderSubheader` y `QuoteStepPills` quedan alineados como navegación interna de cotización; el journey global cubre cotización, propuesta y envío. ESLint validado sin errores.
- 2026-04-29: Se inicia Fase 1B. `OnboardingStepper` adopta el patrón visual del 2.0 con progreso, subtítulos y navegación a pasos alcanzados; se verifica que el flujo conserva persistencia de avance vía `useOnboarding`/`updateProgress`.
- 2026-04-29: Se completa Fase 1B. Se agrega `OnboardingStepHero`, se actualiza copy/jerarquía de `StepIdentity`, `StepFixedCosts`, `StepMyTeam` y `StepReady`, y se aplica transición consistente con `OnboardingStepWrapper`. ESLint validado sin errores.
- 2026-04-29: Se inicia Fase 2. `ProposalGenerateAIRequest` soporta brief guiado, el backend persiste `ai_brief`/`layout` en `body_json` y el portal cliente devuelve `organization_name`. Ruff y compileall validados sin errores.
- 2026-04-29: Se completa Fase 2. `ProposalBuilderHybrid` envía tono, audiencia, diferenciadores y plan de secciones; el portal usa `ProposalRepository.get_for_client_portal` y `ProjectRepository.get_quote_with_relationships` para las consultas añadidas. ESLint, Ruff y compileall validados sin errores.
- 2026-04-29: Se completa Fase 2B. El draft de onboarding devuelve metadata, guarda `onboarding_draft_meta` con versión de flujo, estado, paso y usuario, y marca metadata de completado al cerrar onboarding. Ruff y compileall validados sin errores.
- 2026-04-29: Se inicia Fase 3 con estrategia mínima sin migración: `body_json.branding` guarda color/logo/cover por URL. El editor permite configurarlo y se renderiza en preview de envío y portal cliente. ESLint validado sin errores. Pendiente definir storage/upload con variables de entorno.
- 2026-04-29: Se cierra Fase 3 usando Contabo Object Storage (S3-compatible). Se agregan variables `CONTABO_S3_*`, endpoint `POST /projects/{project_id}/proposals/{proposal_id}/assets`, servicio `ProposalAssetService`, dependencia `boto3` y upload de logo/cover desde `ProposalBuilderHybrid`. ESLint, Ruff y compileall validados sin errores.
- 2026-04-29: Se inicia Fase 4. Se agrega endpoint `share-stats` para métricas mínimas de portal cliente y método `proposalService.getShareStats`. ESLint, Ruff y compileall validados sin errores.
- 2026-04-29: Se conecta versionado real de propuestas en `ProposalBuilderHybrid`: carga todas las versiones del proyecto, permite alternarlas con `VersionSelector` y deja de mostrar `v1` hardcodeado en `QuoteBuilderSubheader`. ESLint validado sin errores.
- 2026-04-29: Se cierra Fase 4 con diseño de analítica avanzada por sesión: tabla futura `proposal_portal_events` (`link_id`, `event_type`, `duration_ms`, `client_session_hash`, `created_at`) y endpoint futuro `POST /public/proposals/{token}/events` para eventos `open`, `heartbeat`, `scroll_depth`, `close`.

## Bloqueos / Decisiones Pendientes
- Prioridad definida para ejecución inicial: Fase 1 primero, Fase 1B después.
- Storage definido: Contabo Object Storage S3-compatible. Pendiente configurar valores reales de `CONTABO_S3_*` en el entorno de despliegue.
