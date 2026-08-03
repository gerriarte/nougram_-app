# Continuación: moneda primaria y rigor de cálculo

**Rama:** `fix/moneda-primaria-y-rigor-de-calculo` (8 commits, PR abierto a `develop`)
**Última sesión:** 2026-08-03
**Estado de la suite:** 805 passed, 4 skipped, 0 failed · ruff limpio · `tsc` exit 0 · ESLint 0 errors · build OK

---

## 1. Qué quedó hecho

| Commit | Contenido |
|--------|-----------|
| `0969238` | Moneda primaria, cargas sociales y capacidad con implementación única |
| `8a85442` | Panel financiero, recursos con rol y ocupación, validación por ítem |
| `44ccd0e` | Invariantes de dinero, tests de arquitectura y regresiones |
| `e010d90` | KPIs del dashboard: fecha local sobre timestamps UTC |
| (2026-08-03) | El impuesto deja de gravar la contingencia en los 5 caminos que faltaban |
| (2026-08-03) | Timeout en `api-client`; vía de escape para precio bajo costo |

El problema de fondo no era una función mal escrita: era **el mismo concepto calculado en
varios lugares que divergieron**. Se llegaron a encontrar siete copias del multiplicador de
cargas sociales, dos BCR que diferían por 3.472×, nueve fallbacks silenciosos a USD y seis
copias de la capacidad mensual (una con doble descuento). Ahora cada concepto tiene un dueño:

- `backend/app/core/currency.py` → `resolve_primary_currency()`
- `backend/app/core/social_charges.py` → multiplicador de cargas
- `backend/app/core/capacity.py` y `frontend/src/lib/capacity.ts` → capacidad mensual

Y `backend/tests/unit/test_arquitectura_fuente_unica.py` **impide que la duplicación vuelva**:
falla si alguien recalcula capacidad fuera de `capacity.py`, reintroduce el doble descuento,
agrega un fallback silencioso a USD, o lee tasas en float desde un módulo nuevo.

---

## 2. Decisiones de producto tomadas (no re-discutir sin motivo)

**Horas facturables (H49).** `team_members.billable_hours_per_week` YA son horas
facturables — así lo rotula la UI. NO se le vuelve a aplicar
`non_billable_hours_percentage`. Ese campo queda como dato informativo ("% Admin") y no
participa del cálculo de capacidad. Si alguna vez se revierte, el cambio va en
`capacity.py` y en ningún otro lado.

**Alcance obligatorio (H14).** La descripción del ítem es obligatoria **solo para ítems
agregados en la sesión actual**, con una marca explícita puesta en `addItem`. Las
cotizaciones existentes se re-guardan sin completar el alcance de sus ítems viejos; el
aviso se muestra pero no bloquea. Nota: lo que la validación gatea es **"Crear propuesta"**,
no "Guardar" — "Guardar" siempre permitió guardar como borrador.

**Tasas de cambio.** Configurables por entorno con fecha y origen auditables. **No se
integró ninguna API externa**: requiere credenciales, política de caché y de caída del
servicio. Sigue siendo una decisión abierta.

---

## 3. Próximos pasos, en orden

### Paso 1 — Revisión del diff (hecha 2026-08-03)
Se revisó el núcleo (`currency.py`, `calculations.py`, `capacity.py`,
`social_charges.py`, `project_service.py`, `settings_service.py`, `projects.py`) y los
contextos del frontend. No aparecieron defectos en lo que la rama ya había tocado; el
riesgo que se buscaba explícitamente era el que rompió `agency-cost-hour` en producción
(`float += Decimal` tras cambiar un retorno a Decimal) y los consumidores de
`get_organization_cost_breakdown` están todos en Decimal.

Lo que sí se cerró en esa pasada fueron tres cosas que la rama había dejado
deliberadamente afuera por alcance congelado (ver abajo).

### Paso 2 — Validar en navegador
Verificado end-to-end: la org 5 en COP reconcilia exacto (`97.931 ÷ 0,65 = 150.663`,
`150.663 − 97.931 = 52.732`) y la regla de ítems nuevos funciona en ambos sentidos.

**Falta validar en navegador:** expenses en el PDF.

Los impuestos con contingencia ya no dependen de una validación manual: la regla vive en
`app/core/quote_taxes.py` y hay un test de arquitectura que impide volver a calcularla a
mano, más un test que exige que el cuerpo del mail y su adjunto digan `1.290.000` (el
número correcto, no sólo el mismo número).

### Paso 3 — Triage del backlog nuevo
15 hallazgos **sin verificar** en [`backlog-hallazgos-2026-07-27.md`](backlog-hallazgos-2026-07-27.md).
No arreglar ninguno sin repro confirmado primero: en el loop original se arreglaron
hallazgos sin verificar y eso introdujo 7 regresiones.

**Cerrados el 2026-08-03** (los cuatro tenían causa entendida y fix acotado):

- **Impuesto sobre la contingencia.** Quedaban cinco copias de la fórmula gravando
  `total_client_price` entero. Ahora hay una sola implementación
  (`app/core/quote_taxes.py`) y la usan el PDF, el DOCX, el mail, el análisis de
  rentabilidad y el costo tributario operativo (este último era un sexto sitio que no
  estaba en el backlog: `operational_cost_service.py` sobreestimaba la carga del período
  en `tasa × contingencia`).
- **`api-client.ts` sin timeout.** `apiRequest` tiene ahora un deadline de 30 s
  (`NEXT_PUBLIC_API_TIMEOUT_MS`) que cubre reintentos y la lectura del body, respeta el
  `AbortSignal` del caller y le da al refresh de token su propio deadline para que el
  timeout de una llamada no le cancele el refresh a las demás.
- **`allowLowMargin` sin setter.** El panel de errores ofrece el checkbox: vender bajo
  costo sigue bloqueando por defecto, pero ya no es un callejón sin salida.
- **Copy del panel de errores.** Decía "Faltan N campos" para errores que no son campos.

**Sigue sin timeout el `fetch` crudo** de `onboardingService` (import de Excel),
`proposalService` (assets) y el portal público de propuestas: no pasan por `apiRequest`.
No se tocaron por alcance; son subidas de archivo y merecen su propio criterio de tiempo.

### Paso 4 — Lo que queda para después del merge

- **Backfill de las orgs sin `template_applied_currency`** (ver deuda, abajo). Es lo único
  con impacto directo en datos reales de producción.
- **Expenses que se pierden al CREAR el proyecto** (`quoteService.ts:534` +
  `ProjectCreateWithQuote`): el POST no manda `expenses`. Es un hallazgo verificable en
  navegador y toca schema + front, así que va en su propio cambio.
- Los 15 hallazgos restantes del backlog, con repro antes de tocar nada.

### Paso 5 — Deuda conocida y acotada
- **4 módulos leen `EXCHANGE_RATES_TO_USD`** (dict de floats) haciendo round-trip sobre
  tasas que ya existen en `Decimal`. Están en la lista `DEUDA_TASAS_EN_FLOAT` de
  `test_arquitectura_fuente_unica.py`, que funciona como trinquete: la deuda no puede
  crecer, y si migrás un módulo el test te obliga a sacarlo de la lista.
- **4 hallazgos quedaron `bloqueado_por_dependencia`** en fase 2 (el fix vivía en un
  archivo de otro paquete). Están en el resultado del workflow, no en este doc.
- **Backfill incompleto:** las orgs sin `template_applied_currency` siguen sin
  `primary_currency`. En local son las orgs 1, 3, 4 y 9 — y la **org 1 (A:BRA Latam) tiene
  cotizaciones reales con datos en COP y sigue resolviendo a USD**.

---

## 4. Sobre cómo trabajar esto con agentes

Lo que la experiencia de esta sesión dejó claro, con números:

| Uso | Resultado |
|-----|-----------|
| Triage de hallazgos (verificar antes de arreglar) | **Muy bueno** — 5,7 min, filtró 28% de ruido (6 falsos, 9 ya corregidos) |
| Arreglar bugs confirmados con repro | **Bueno** — 35/36, con 4 rescates |
| Descubrimiento no supervisado en loop | **Malo** — no convergió en 3 rondas, introdujo 7 regresiones |

Las tres reglas que hicieron converger el trabajo:

1. **Alcance congelado.** Los hallazgos nuevos se anotan, no se arreglan. Un loop cuyo
   input crece más rápido de lo que cierra no termina nunca.
2. **Verificar antes de arreglar.** Ningún hallazgo llega a un desarrollador sin repro.
3. **El loop cierra sobre regresiones, no sobre hallazgos.** "No rompí nada" converge;
   "no queda nada mal en el repo" no converge jamás.

Y la lección de fondo: **la certeza viene de algo ejecutable, no de algo leído**. Los
momentos de certeza real fueron correr la lógica vieja y la nueva lado a lado
(`46.852` vs `30.0`; multiplicador `1` vs `1.46852`) y ver la aritmética cerrar en el
navegador. Ningún veredicto de agente dio esa certeza. Por eso la inversión que queda es
en invariantes ejecutables, no en más lectura.

---

## 5. Estado del entorno local

- **Postgres** en `:5435` (contenedor `nougram-postgres`), migrado a `v20260727c_bf_currency`.
- **Backend** `:8000` y **frontend** `:3001` quedaron corriendo (el 3000 lo ocupa otro proyecto).
- `frontend/.env.local` creado con `NEXT_PUBLIC_API_URL` — está gitignoreado.
- **En la base local** se cambió la contraseña de `qa+174028@nougram.co` y
  `roberto@perez.com` a `DemoLocal123!`, y se cargó un IVA 19% + cliente "Acme Corp S.A.S"
  en la org 5. Todo local; no se tocó staging ni producción.

**Sin commitear a propósito:**
- `.claude/` — contiene un worktree de git completo con su propio `.git`, un `.coverage` y
  settings locales. **Conviene agregarlo a `.gitignore`.**
- `backend/docs/`, `frontend/docs/` — preexisten a esta sesión y no se escribieron acá.
