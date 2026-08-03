"""backfill organizations.settings->>'primary_currency'

Cuando `primary_currency` falta en los settings de una organización, el backend
cae silenciosamente a "USD" y termina cotizando en dólares una agencia cuyos
sueldos y costos fijos están en moneda local (dividiendo todo por la tasa). No es
un problema de display: los precios se guardan en la moneda equivocada.

Esta migración rellena `primary_currency` (y la clave legacy `currency`, que se
mantiene en sync). Nunca pisa un `primary_currency` existente.

Fuentes, en orden de confianza:
  1. settings['currency'] (clave legacy)
  2. settings['template_applied_currency'] (lo que escribía el onboarding)
  3. el país: settings['country'] / settings['template_applied_region']
  4. la moneda REAL de los datos: si todos los team_members y costos fijos de la
     organización comparten una única moneda, esa es la moneda de la agencia.

El paso 4 es el que arregla el caso que la primera versión de esta migración
dejaba afuera: organizaciones con `settings` NULL o sin ninguna clave de moneda
(la más común entre las cuentas viejas) ni siquiera entraban al SELECT, y seguían
cotizando en USD una nómina cargada en COP — factor 4000 sobre el BCR.

Una organización con monedas MEZCLADAS en sus filas se deja intacta a propósito:
ahí no hay una respuesta correcta deducible y elegir mal sería peor que no elegir.

Es idempotente: correrla dos veces no cambia nada la segunda vez, porque en la
segunda pasada ya no hay filas que cumplan la condición.

Revision ID: v20260727c_bf_currency
Revises: v20260727b_price_ovr
Create Date: 2026-07-27
"""

from __future__ import annotations

import json

import sqlalchemy as sa
from alembic import op

revision: str = "v20260727c_bf_currency"
down_revision: str | None = "v20260727b_price_ovr"
branch_labels = None
depends_on = None

# Debe coincidir con app.core.currency.CURRENCY_INFO. Se replica acá a propósito:
# una migración no debe depender del código de la app, que puede cambiar después.
SUPPORTED_CURRENCIES = {"USD", "COP", "ARS", "EUR", "PEN", "MXN"}

# Idem app.core.currency.COUNTRY_DEFAULT_CURRENCY (ISO-2, ISO-3 y códigos "region"
# de los templates).
COUNTRY_DEFAULT_CURRENCY = {
    "CO": "COP",
    "COL": "COP",
    "COLOMBIA": "COP",
    "AR": "ARS",
    "ARG": "ARS",
    "ARGENTINA": "ARS",
    "MX": "MXN",
    "MEX": "MXN",
    "MEXICO": "MXN",
    "PE": "PEN",
    "PER": "PEN",
    "PERU": "PEN",
    "ES": "EUR",
    "ESP": "EUR",
    "SPAIN": "EUR",
    "EU": "EUR",
    "US": "USD",
    "USA": "USD",
}


def _valid_code(value: object) -> str | None:
    """Código de moneda soportado, o None."""
    if not isinstance(value, str):
        return None
    code = value.strip().upper()
    return code if code in SUPPORTED_CURRENCIES else None


def _parse_settings(raw_settings: object) -> dict | None:
    """settings como dict; None si es NULL/ilegible (el caller decide qué hacer)."""
    settings = raw_settings
    if isinstance(settings, str):
        try:
            settings = json.loads(settings)
        except (ValueError, TypeError):
            return None
    return settings if isinstance(settings, dict) else None


def derive_primary_currency(settings: dict | None, row_currencies: set[str]) -> str | None:
    """
    Moneda a persistir para una organización, o None si no se puede decidir.

    `row_currencies` son las monedas encontradas en team_members y costos fijos.
    Función pura y sin dependencias de la app: es el corazón testeable del backfill.
    """
    settings = settings or {}

    for key in ("currency", "template_applied_currency"):
        code = _valid_code(settings.get(key))
        if code:
            return code

    for key in ("country", "template_applied_region"):
        raw = settings.get(key)
        if isinstance(raw, str) and raw.strip():
            derived = COUNTRY_DEFAULT_CURRENCY.get(raw.strip().upper())
            if derived in SUPPORTED_CURRENCIES:
                return derived

    # Último recurso: la moneda en la que la agencia realmente carga su plata.
    # Solo si es UNA sola; con monedas mezcladas no hay respuesta deducible.
    valid_rows = {code for code in (_valid_code(c) for c in row_currencies) if code}
    if len(valid_rows) == 1:
        return valid_rows.pop()

    return None


def _row_currencies_by_org(bind) -> dict[int, set[str]]:
    """Monedas usadas por organización en team_members y costos fijos."""
    result: dict[int, set[str]] = {}
    queries = (
        "SELECT organization_id, currency FROM team_members",
        "SELECT organization_id, currency FROM costs_fixed WHERE deleted_at IS NULL",
    )
    for query in queries:
        try:
            rows = bind.execute(sa.text(query)).fetchall()
        except Exception:  # noqa: BLE001 - tabla ausente: el backfill sigue sin ella
            continue
        for org_id, currency in rows:
            if org_id is None:
                continue
            result.setdefault(org_id, set()).add(currency)
    return result


def upgrade() -> None:
    bind = op.get_bind()

    # En PostgreSQL la columna es JSONB y no acepta un bind de tipo text sin cast
    # explícito; en SQLite el JSON se almacena como texto y el cast sobra.
    if bind.dialect.name == "postgresql":
        update_sql = sa.text(
            "UPDATE organizations SET settings = CAST(:settings AS JSONB) WHERE id = :id"
        )
    else:
        update_sql = sa.text("UPDATE organizations SET settings = :settings WHERE id = :id")

    # Sin filtro por `settings IS NOT NULL`: las orgs con settings NULL son
    # justamente las que quedaban cotizando en USD.
    rows = bind.execute(sa.text("SELECT id, settings FROM organizations")).fetchall()
    row_currencies = _row_currencies_by_org(bind)

    for org_id, raw_settings in rows:
        settings = _parse_settings(raw_settings)
        if settings is None and raw_settings not in (None, "", {}):
            # settings ilegible (texto que no es JSON): no se toca.
            continue
        settings = settings or {}

        if _valid_code(settings.get("primary_currency")):
            # Ya tiene moneda primaria válida: no se toca (idempotencia).
            continue

        resolved = derive_primary_currency(settings, row_currencies.get(org_id, set()))
        if resolved is None:
            continue

        updated = dict(settings)
        updated["primary_currency"] = resolved
        # Clave legacy: se alinea solo si está vacía o inválida, para no romper
        # organizaciones que la usen deliberadamente con otro valor.
        if not _valid_code(updated.get("currency")):
            updated["currency"] = resolved

        bind.execute(update_sql, {"settings": json.dumps(updated), "id": org_id})


def downgrade() -> None:
    """
    No-op deliberado.

    El backfill no es distinguible de una moneda primaria elegida por el usuario:
    no se guarda marca de origen, y borrar `primary_currency` devolvería a las
    organizaciones al bug que esta migración corrige (cotizar en USD lo que está
    en moneda local). Revertir sería destructivo, así que no se revierte.
    """
    pass
