"""
P2-moneda / H11 + H32: el backfill de `primary_currency` debe alcanzar a las orgs
que no tienen ninguna clave de moneda en `settings` (incluido `settings` NULL).

La versión anterior filtraba `WHERE settings IS NOT NULL` y solo miraba
`template_applied_currency`, así que una agencia con la nómina y los costos fijos
cargados en COP se quedaba sin moneda primaria y el backend la cotizaba en USD:
24.392.000 COP/mes sobre 692,80 h son 35.207,85 COP/h, y el código devolvía
8,80 "USD"/h. Factor 4000.
"""

import importlib.util
from pathlib import Path

import pytest

_MIGRATION_PATH = (
    Path(__file__).resolve().parents[2]
    / "alembic"
    / "versions"
    / "v20260727c_backfill_primary_currency.py"
)
_spec = importlib.util.spec_from_file_location("_backfill_primary_currency", _MIGRATION_PATH)
migration = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(migration)

derive_primary_currency = migration.derive_primary_currency


@pytest.mark.unit
class TestDerivePrimaryCurrency:
    def test_settings_null_with_cop_rows_resolves_cop(self):
        """El caso de la org 1: settings NULL, todo cargado en COP."""
        assert derive_primary_currency(None, {"COP"}) == "COP"

    def test_settings_without_currency_keys_uses_the_rows(self):
        assert derive_primary_currency({"onboarding_completed": True}, {"COP", "cop"}) == "COP"

    def test_mixed_row_currencies_are_left_alone(self):
        """Sin respuesta deducible: elegir mal sería peor que no elegir."""
        assert derive_primary_currency({}, {"COP", "USD"}) is None

    def test_no_rows_and_no_settings_is_undecidable(self):
        assert derive_primary_currency({}, set()) is None

    def test_legacy_currency_key_wins_over_rows(self):
        assert derive_primary_currency({"currency": "EUR"}, {"COP"}) == "EUR"

    def test_template_applied_currency_still_works(self):
        assert derive_primary_currency({"template_applied_currency": "cop"}, set()) == "COP"

    def test_country_is_used_before_falling_back_to_rows(self):
        assert derive_primary_currency({"country": "CO"}, set()) == "COP"
        assert derive_primary_currency({"template_applied_region": "ARG"}, set()) == "ARS"

    def test_unsupported_codes_are_ignored(self):
        assert derive_primary_currency({"currency": "CLP"}, {"CLP"}) is None
        assert derive_primary_currency({"currency": "CLP"}, {"COP"}) == "COP"

    def test_supported_currencies_match_the_app(self):
        from app.core.currency import CURRENCY_INFO

        assert migration.SUPPORTED_CURRENCIES == set(CURRENCY_INFO)


@pytest.mark.unit
class TestUpgradeRunsOverEveryOrganization:
    """upgrade() de punta a punta sobre un SQLite real, incluidas las orgs con settings NULL."""

    @staticmethod
    def _seed(conn):
        conn.exec_driver_sql("CREATE TABLE organizations (id INTEGER PRIMARY KEY, settings TEXT)")
        conn.exec_driver_sql(
            "CREATE TABLE team_members (id INTEGER PRIMARY KEY, organization_id INTEGER, "
            "currency TEXT)"
        )
        conn.exec_driver_sql(
            "CREATE TABLE costs_fixed (id INTEGER PRIMARY KEY, organization_id INTEGER, "
            "currency TEXT, deleted_at TEXT)"
        )
        # org 1: settings NULL + nómina y costos en COP  -> debe quedar en COP
        conn.exec_driver_sql("INSERT INTO organizations (id, settings) VALUES (1, NULL)")
        for _ in range(4):
            conn.exec_driver_sql(
                "INSERT INTO team_members (organization_id, currency) VALUES (1, 'COP')"
            )
        conn.exec_driver_sql(
            "INSERT INTO costs_fixed (organization_id, currency, deleted_at) "
            "VALUES (1, 'COP', NULL)"
        )
        # org 4: monedas mezcladas -> intocada
        conn.exec_driver_sql("INSERT INTO organizations (id, settings) VALUES (4, '{}')")
        conn.exec_driver_sql(
            "INSERT INTO team_members (organization_id, currency) VALUES (4, 'COP')"
        )
        conn.exec_driver_sql(
            "INSERT INTO team_members (organization_id, currency) VALUES (4, 'USD')"
        )
        # org 7: ya tiene moneda primaria elegida -> intocada
        conn.exec_driver_sql(
            'INSERT INTO organizations (id, settings) VALUES (7, \'{"primary_currency": "USD"}\')'
        )
        conn.exec_driver_sql(
            "INSERT INTO team_members (organization_id, currency) VALUES (7, 'COP')"
        )

    def _run(self, conn, monkeypatch):
        class _FakeOp:
            @staticmethod
            def get_bind():
                return conn

        monkeypatch.setattr(migration, "op", _FakeOp)
        migration.upgrade()

    @staticmethod
    def _settings(conn, org_id):
        import json

        raw = conn.exec_driver_sql(
            f"SELECT settings FROM organizations WHERE id = {org_id}"
        ).scalar()
        return json.loads(raw) if raw else None

    def test_upgrade_backfills_only_what_it_can_decide(self, monkeypatch):
        from sqlalchemy import create_engine

        engine = create_engine("sqlite://")
        with engine.begin() as conn:
            self._seed(conn)
            self._run(conn, monkeypatch)

            # org 1: antes ni siquiera entraba al SELECT (settings IS NOT NULL).
            assert self._settings(conn, 1) == {"primary_currency": "COP", "currency": "COP"}
            # org 4: monedas mezcladas, se deja como estaba.
            assert self._settings(conn, 4) == {}
            # org 7: moneda ya elegida, no se pisa.
            assert self._settings(conn, 7) == {"primary_currency": "USD"}

    def test_upgrade_is_idempotent(self, monkeypatch):
        from sqlalchemy import create_engine

        engine = create_engine("sqlite://")
        with engine.begin() as conn:
            self._seed(conn)
            self._run(conn, monkeypatch)
            first = self._settings(conn, 1)
            self._run(conn, monkeypatch)
            assert self._settings(conn, 1) == first


@pytest.mark.unit
class TestBackfillMatchesTheResolver:
    """Lo que persiste el backfill debe ser lo que después lee resolve_primary_currency."""

    def test_resolver_reads_back_the_backfilled_value(self):
        from app.core.currency import resolve_primary_currency

        settings = {}
        resolved = derive_primary_currency(settings, {"COP"})
        settings["primary_currency"] = resolved
        assert resolve_primary_currency({"settings": settings}) == "COP"
