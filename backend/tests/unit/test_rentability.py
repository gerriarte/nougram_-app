from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.calculations import calculate_rentability_analysis


@pytest.mark.asyncio
async def test_calculate_rentability_analysis_logic():
    # Mock DB session
    db = AsyncMock()

    # Mock Quote with items and expenses
    quote = MagicMock()
    quote.id = 1
    quote.total_client_price = 1000.0
    quote.total_internal_cost = 600.0

    item1 = MagicMock()
    item1.internal_cost = 600.0
    quote.items = [item1]

    expense1 = MagicMock()
    expense1.cost = 50.0
    expense1.quantity = 1.0
    expense1.category = "Software"
    quote.expenses = [expense1]

    project = MagicMock()
    project.currency = "usd"
    tax1 = MagicMock()
    tax1.name = "IVA"
    tax1.percentage = 19.0
    project.taxes = [tax1]
    quote.project = project

    # Mock Organization breakdown
    breakdown = {"talent_ratio": 0.8, "overhead_ratio": 0.2, "total_monthly_costs": 10000.0}

    # Patch the helper function and DB execute
    with patch("app.core.calculations.get_organization_cost_breakdown", return_value=breakdown):
        # Setup mock execute result
        mock_quote_result = MagicMock()
        mock_quote_result.scalar_one_or_none.return_value = quote
        db.execute.return_value = mock_quote_result

        result = await calculate_rentability_analysis(db, 1, 1)

        assert result["quote_id"] == 1
        assert result["total_client_price"] == 1000.0
        assert result["total_internal_cost"] == 600.0

        # Taxes = 1000 * 0.19 = 190
        assert result["total_taxes"] == 190.0

        # Net Profit = Price - InternalCost - Taxes = 1000 - 600 - 190 = 210
        assert result["net_profit_amount"] == 210.0
        assert result["net_profit_margin"] == 21.0
        assert result["status"] == "warning"

        # Check categories
        categories = {c["concept"]: c for c in result["categories"]}
        assert categories["Talento y Recursos"]["amount"] == 480.0
        assert categories["Overhead Fijo"]["amount"] == 120.0
        assert categories["Software y Herramientas"]["amount"] == 50.0
        assert categories["IVA"]["amount"] == 190.0


@pytest.mark.asyncio
async def test_calculate_rentability_critical_status():
    db = AsyncMock()
    quote = MagicMock()
    quote.total_client_price = 1000.0
    quote.total_internal_cost = 900.0
    quote.items = []
    quote.expenses = []
    project = MagicMock()
    project.currency = "usd"
    project.taxes = []
    quote.project = project

    mock_quote_result = MagicMock()
    mock_quote_result.scalar_one_or_none.return_value = quote
    db.execute.return_value = mock_quote_result

    with patch(
        "app.core.calculations.get_organization_cost_breakdown",
        return_value={"talent_ratio": 0.8, "overhead_ratio": 0.2},
    ):
        result = await calculate_rentability_analysis(db, 1, 1)
        assert result["net_profit_margin"] == 10.0
        assert result["status"] == "critical"


@pytest.mark.asyncio
async def test_calculate_rentability_healthy_status():
    db = AsyncMock()
    quote = MagicMock()
    quote.total_client_price = 1000.0
    quote.total_internal_cost = 500.0
    quote.items = []
    quote.expenses = []
    project = MagicMock()
    project.currency = "usd"
    project.taxes = []
    quote.project = project

    mock_quote_result = MagicMock()
    mock_quote_result.scalar_one_or_none.return_value = quote
    db.execute.return_value = mock_quote_result

    with patch(
        "app.core.calculations.get_organization_cost_breakdown",
        return_value={"talent_ratio": 0.8, "overhead_ratio": 0.2},
    ):
        result = await calculate_rentability_analysis(db, 1, 1)
        assert result["net_profit_margin"] == 50.0
        assert result["status"] == "healthy"
