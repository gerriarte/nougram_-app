# Política de Moneda Primaria Única (Tenant-Level)

## Objetivo
Garantizar consistencia financiera: todos los cálculos y persistencia monetaria de un tenant se realizan en una sola moneda (`primary_currency`), editable únicamente a nivel de cuenta.

## Alcance
- Backend: enforcement de moneda primaria en escrituras financieras.
- Frontend: eliminación de selector de moneda en formularios operativos.
- Datos: migración de histórico para homogeneizar moneda.

## Fuente de verdad
`organization.settings.primary_currency`

No se usa `organization.settings.currency` para cálculos o persistencia.

## Reglas de negocio
1. Cada organización tiene una única moneda de operación.
2. Solo Owner/Super Admin puede cambiarla desde Cuenta/Empresa.
3. Al crear/editar:
   - team members
   - fixed costs
   - equipment amortization
   - quote inputs monetarios relevantes
   se persiste siempre `currency = primary_currency`.
4. Si el cliente envía otra moneda, backend la sobrescribe (o rechaza, según política activa).

## Fórmula BCR (referencia)
\[
BCR = \frac{\text{Nómina mensual (con cargas)} + \text{Fijos mensuales} + \text{Amortización mensual}}{\text{Horas facturables mensuales}}
\]

Horas facturables mensuales:
\[
\sum (\text{horas/semana} \times 4.33 \times (1 - \% no facturable))
\]

## Flujo de cambio de moneda
1. Owner/Super Admin actualiza moneda en `/settings/currency`.
2. Backend invalida caches:
   - financial_summary
   - blended_cost_rate
   - operational_costs
3. UI refresca contexto de moneda.
4. Nuevos registros se guardan en la nueva moneda primaria.

## Migración de histórico
### Diagnóstico
- Identificar registros con `currency != primary_currency` en:
  - team_members
  - costs_fixed
  - equipment_amortization
  - otras entidades monetarias aplicables

### Normalización
- Convertir montos a `primary_currency` con el método de conversión vigente del sistema.
- Persistir monto convertido y currency primaria.
- Registrar bitácora (org, tabla, filas afectadas, timestamp).

## QA Checklist
- [x] No existe selector de moneda en formularios operativos.
- [x] Cambio de moneda solo disponible en Cuenta/Empresa.
- [x] Etiqueta BCR es `/hora`.
- [x] No existen nuevos registros fuera de moneda primaria en altas/ediciones nuevas.
- [ ] BCR, Overhead y Costo Operacional muestran misma moneda en todos los tenants con histórico legado.
- [ ] Reporte post-migración muestra 0 inconsistencias.

## Riesgos y mitigación
- Riesgo: desalineación de caches tras cambio de moneda.
  - Mitigación: invalidación explícita + refresh UI.
- Riesgo: endpoints legacy aceptan currency externa.
  - Mitigación: enforcement server-side en capa endpoint/servicio.
- Riesgo: datos históricos mixtos.
  - Mitigación: auditoría + normalización + reporte.

## Rollback
- Conservar backup lógico antes de normalización.
- Si hay inconsistencia, restaurar backup y re-ejecutar por lotes pequeños.


---

## RFC: Moneda Primaria Única por Tenant

### Estado
Implementado (Fase 1-2)

### Fecha
2026-03-06

### Owners
- Producto
- Backend
- Frontend

### Contexto
Actualmente existen señales de inconsistencia de moneda entre vistas financieras (BCR, overhead, costo operacional), derivadas de:
- coexistencia de más de una llave de moneda en settings (`currency` y `primary_currency`),
- posibilidad de capturar registros en monedas distintas dentro del mismo tenant,
- mezcla de fuentes de datos para render en frontend.

Estas inconsistencias afectan trazabilidad financiera, confianza del usuario y comparabilidad de KPIs.

### Decisión
Adoptar una política de **Moneda Primaria Única por tenant**:

1. `organization.settings.primary_currency` es la única fuente de verdad.
2. Todo dato monetario nuevo/actualizado se persiste en moneda primaria.
3. La moneda solo puede cambiarse a nivel cuenta (Owner/Super Admin).
4. Los formularios operativos no permiten seleccionar moneda.
5. Backend aplica enforcement server-side (no depender de frontend).
6. Dashboards financieros usan exclusivamente la moneda primaria.

### Fuera de alcance
- Conversión con tasa diaria en tiempo real.
- Multi-moneda por proyecto dentro de un mismo tenant.
- Reportería multi-moneda histórica en paralelo.

### Motivación
- Consistencia contable/operativa.
- Menor complejidad de soporte.
- Menor riesgo de errores de interpretación y pricing.
- Mejor gobernanza de datos y auditoría.

### Alternativas consideradas

#### A) Mantener multi-moneda por registro
- Ventaja: flexibilidad operativa.
- Desventaja: complejidad alta en cálculo, UI y auditoría.
- Resultado: descartada por riesgo e inconsistencia.

#### B) Convertir siempre en lectura (sin forzar escritura)
- Ventaja: menos cambios en captura.
- Desventaja: mantiene datos heterogéneos, difícil de auditar.
- Resultado: descartada.

#### C) Moneda primaria única (decisión adoptada)
- Ventaja: simplicidad, consistencia, control.
- Desventaja: requiere migración y ajustes UX/backend.
- Resultado: aprobada.

### Especificación funcional
- Al crear/editar `team_members`, `costs_fixed`, `equipment_amortization` y entradas monetarias de cotización:
  - `currency` debe ser `primary_currency`.
- Si el cliente envía moneda distinta:
  - backend sobrescribe o rechaza (política recomendada: sobrescribir + log estructurado).
- Al cambiar `primary_currency`:
  - invalidar caches financieras y refrescar contexto en UI.

### Impacto técnico
- **Backend**: validación y normalización en endpoints/servicios.
- **Frontend**: eliminación de selectores de moneda operativa.
- **Datos**: script de diagnóstico y normalización de histórico.
- **QA**: suite de consistencia de moneda y regressions financieras.

### Implementación aplicada

#### Backend (enforcement server-side)
- `team`: en alta/edición se fuerza `currency = primary_currency`.
- `costs/fixed`: en alta/edición se fuerza `currency = primary_currency`.
- `equipment`: en alta/edición se fuerza `currency = primary_currency`.
- `projects`: creación y actualización respetan moneda primaria del tenant.
- `admin`, `dashboard` y `costs` toman moneda mediante `SettingsService` para asegurar fuente única.
- Cuando llega una moneda diferente por payload, se sobrescribe y se registra warning estructurado.

#### Frontend (UX sin selección de moneda operativa)
- Formularios de Team, Fixed Costs y Equipment muestran moneda de operación en modo solo lectura.
- Wizard/edición de cotización muestran moneda de operación sin selector editable.
- `QuoteBuilderContext` fuerza moneda primaria al guardar/cargar payloads.
- `NougramCoreContext` usa únicamente `settings.primary_currency` como fuente de verdad.
- `BCRSummaryCard` usa sufijo `/hora` (no `/usd`).

#### Estado de migración histórica
- El enforcement evita nuevos registros inconsistentes.
- La normalización de registros históricos multi-moneda queda como fase de migración controlada (PR de datos), con auditoría antes/después.

#### Script de migración histórica (implementado)
- Archivo: `backend/scripts/normalize_primary_currency.py`
- Tablas incluidas:
  - `team_members` (`salary_monthly_brute`, `currency`)
  - `costs_fixed` (`amount_monthly`, `currency`)
  - `equipment_amortization` (`purchase_price`, `salvage_value`, `currency`)
- Conversión:
  - Usa las tasas vigentes del sistema (`EXCHANGE_RATES_TO_USD`).
  - No usa tasas diarias externas.
- Seguridad:
  - Modo por defecto: **dry-run** (no persiste cambios).
  - Modo `--apply`: persiste cambios por organización.
  - Genera reporte JSON de auditoría con conteos y preview de IDs.

##### Ejecución recomendada
1. Dry-run global:
   - `python backend/scripts/normalize_primary_currency.py`
2. Dry-run por organización:
   - `python backend/scripts/normalize_primary_currency.py --organization-id 123`
3. Aplicar cambios:
   - `python backend/scripts/normalize_primary_currency.py --apply`
4. Aplicar por organización con reporte personalizado:
   - `python backend/scripts/normalize_primary_currency.py --apply --organization-id 123 --report-path backend/scripts/reports/org-123-normalization.json`

##### Salida de auditoría
- Reporte por defecto:
  - `backend/scripts/reports/primary_currency_normalization_report.json`
- Campos clave:
  - `summary.scanned`
  - `summary.mismatched`
  - `summary.converted`
  - `summary.skipped_invalid_currency`

### Riesgos
1. Desalineación temporal de cache tras cambio de moneda.
2. Endpoints legacy aceptando payloads antiguos.
3. Históricos con moneda mixta no normalizados.

### Mitigaciones
- Invalidación explícita de cache al cambiar moneda.
- Enforcement server-side en capa de entrada y dominio.
- Migración por lotes con reporte antes/después.

### Plan de rollout
1. PR1 Backend enforcement.
2. PR2 Frontend UX y consistencia de display.
3. PR3 Migración de datos + QA.
4. Monitoreo de incidencias financieras 7 días post-release.

### Métricas de éxito
- 0 registros nuevos con `currency != primary_currency`.
- 0 discrepancias de moneda en BCR/Overhead/Costo operacional para tenants validados.
- Reducción de tickets de “inconsistencia de moneda”.

### Criterios de aceptación
- Política aplicada y probada en staging.
- Evidencia de migración (reporte audit + post-migration).
- Validación E2E con usuario Owner en tenant QA.

### Rollback
- Backup lógico previo a normalización.
- Reversión por lotes si se detecta desalineación.
- Re-deploy de versión previa si falla enforcement crítico.

### Decisión final
Aplicada en producto para Fase 1-2 (Backend + Frontend). Pendiente Fase 3 (migración histórica + QA final).