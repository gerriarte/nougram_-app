# Plan: Carga Prestacional por Pais en Impuestos

## Objetivo

Mover la configuracion de carga prestacional fuera de Nomina y centralizarla en el modulo de Impuestos, con persistencia en base de datos y capacidad de edicion futura.

## Decision tecnica

- Mantener la persistencia en base de datos dentro de `organization.settings.social_charges_config` (JSON).
- Agregar metadata de gobierno de configuracion para soportar pais, preset y version:
  - `country_code`
  - `preset_key`
  - `version`
  - `updated_at`
- Conservar compatibilidad con la logica actual de calculo de BCR:
  - solo aplica carga si `enable_social_charges = true`
  - y el colaborador tiene `applySocialCharges = true`

## Cambios funcionales

### 1) Frontend (UX)

- Quitar el bloque de configuracion de carga prestacional del modulo `Nomina`.
- Mostrarlo en `Impuestos` como bloque dedicado.
- Permitir seleccionar pais y aplicar preset por pais.
- Mantener edicion manual de porcentajes.
- Mostrar total y multiplicador resultante.

### 2) Persistencia

- Al guardar configuracion desde Impuestos, persistir en `organization.settings.social_charges_config`.
- Guardar tambien metadata (`country_code`, `preset_key`, `version`, `updated_at`) para trazabilidad y cambios futuros.

### 3) Backend

- Extender schema `SocialChargesConfig` para aceptar metadata.
- Mantener calculo de `total_percentage` en backend para consistencia.
- No romper contratos existentes: campos legacy siguen vigentes.

## Compatibilidad y migracion

- No se requiere migracion estructural (sin tabla nueva), porque se reutiliza JSON de `organization.settings`.
- Tenants existentes:
  - si ya tienen `social_charges_config`, se usa tal cual;
  - si no tienen metadata, frontend/servicio aplica defaults por preset de moneda/pais.

## Riesgos y mitigacion

- Riesgo: desalineacion entre preset y moneda.
  - Mitigacion: permitir seleccionar pais explicitamente y guardar `country_code`.
- Riesgo: cambios de porcentajes sin trazabilidad.
  - Mitigacion: incrementar `version` y guardar `updated_at`.

## Criterios de aceptacion

- La configuracion no aparece en Nomina.
- La configuracion aparece en Impuestos.
- Se puede seleccionar pais y aplicar preset.
- Se puede editar y guardar.
- La configuracion persiste y reaparece tras recargar.
- El BCR sigue respetando `enable_social_charges` y `applySocialCharges`.
