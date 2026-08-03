"""
Regresiones del breakdown por ítem (mapeo estable) y del cálculo de horas en Decimal.

Contexto:
- El breakdown que devuelve ``calculate_quote_totals_enhanced`` se indexaba por
  ``service_id`` al persistir los QuoteItem. Dos ítems del mismo servicio colapsaban
  y ambos quedaban guardados con el precio y el costo del último, descuadrando las
  líneas de la propuesta contra el total del presupuesto.
- El endpoint de costo/hora mezclaba float con Decimal al sumar horas facturables.
"""

from decimal import Decimal

import pytest

from app.core.calculations import build_items_breakdown_map, calculate_quote_totals_enhanced


@pytest.mark.unit
class TestItemsBreakdownMapping:
    """El breakdown debe poder mapearse 1:1 a los ítems de entrada."""

    async def test_duplicate_service_produces_one_row_per_item(
        self, db_session, test_organization, test_service
    ):
        """Dos ítems del mismo servicio generan dos filas con item_key distinto."""
        test_service.pricing_type = "hourly"
        db_session.add(test_service)
        await db_session.commit()

        items = [
            {"item_key": 0, "service_id": test_service.id, "estimated_hours": 10.0},
            {"item_key": 1, "service_id": test_service.id, "estimated_hours": 40.0},
        ]

        result = await calculate_quote_totals_enhanced(
            db_session,
            items,
            Decimal("50000"),
            target_margin_percentage=Decimal("0.40"),
            currency="COP",
        )

        breakdown = result["items"]
        assert len(breakdown) == 2
        assert [row["item_key"] for row in breakdown] == [0, 1]

        mapped = build_items_breakdown_map(breakdown)
        assert len(mapped) == 2, "El mapa NO debe colapsar ítems que comparten service_id"
        assert mapped[0]["internal_cost"] == pytest.approx(500_000.0)
        assert mapped[1]["internal_cost"] == pytest.approx(2_000_000.0)

    async def test_sum_of_mapped_rows_equals_quote_total(
        self, db_session, test_organization, test_service
    ):
        """La suma de las filas mapeadas debe igualar el total del presupuesto."""
        test_service.pricing_type = "hourly"
        db_session.add(test_service)
        await db_session.commit()

        items = [
            {"item_key": 0, "service_id": test_service.id, "estimated_hours": 10.0},
            {"item_key": 1, "service_id": test_service.id, "estimated_hours": 40.0},
        ]

        result = await calculate_quote_totals_enhanced(
            db_session,
            items,
            Decimal("50000"),
            target_margin_percentage=Decimal("0.40"),
            currency="COP",
        )

        mapped = build_items_breakdown_map(result["items"])
        # Se simula la persistencia: cada ítem de entrada busca SU fila.
        persisted_prices = [
            Decimal(str(mapped.get(index, {}).get("client_price", 0.0)))
            for index in range(len(items))
        ]
        total_persisted = sum(persisted_prices, Decimal("0"))
        total_quote = Decimal(str(result["total_client_price"]))

        assert abs(total_persisted - total_quote) < Decimal("1")

    async def test_manual_override_is_not_leaked_to_the_sibling_item(
        self, db_session, test_organization, test_service
    ):
        """Un override manual en un ítem no debe pisar al otro ítem del mismo servicio."""
        test_service.pricing_type = "hourly"
        db_session.add(test_service)
        await db_session.commit()

        items = [
            {
                "item_key": 0,
                "service_id": test_service.id,
                "estimated_hours": 10.0,
                "client_price_override": 1_000_000,
            },
            {"item_key": 1, "service_id": test_service.id, "estimated_hours": 40.0},
        ]

        result = await calculate_quote_totals_enhanced(
            db_session,
            items,
            Decimal("50000"),
            target_margin_percentage=Decimal("0.40"),
            currency="COP",
        )

        mapped = build_items_breakdown_map(result["items"])
        assert mapped[0]["client_price"] == pytest.approx(1_000_000.0)
        assert mapped[1]["client_price"] == pytest.approx(3_333_333.33, abs=1.0)

    async def test_map_falls_back_to_position_for_legacy_breakdowns(self):
        """Breakdowns viejos (sin item_key) siguen mapeando por posición."""
        legacy = [
            {"service_id": 7, "internal_cost": 100.0, "client_price": 200.0},
            {"service_id": 7, "internal_cost": 300.0, "client_price": 600.0},
        ]
        mapped = build_items_breakdown_map(legacy)
        assert len(mapped) == 2
        assert mapped[0]["internal_cost"] == 100.0
        assert mapped[1]["internal_cost"] == 300.0

    async def test_map_handles_empty_breakdown(self):
        assert build_items_breakdown_map([]) == {}
        assert build_items_breakdown_map(None) == {}
