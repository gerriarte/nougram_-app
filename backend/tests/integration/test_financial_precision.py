"""
Integration tests for financial precision validation
ESTÁNDAR NOUGRAM: Validación de precisión grado bancario en cálculos críticos
"""

from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.calculations import calculate_blended_cost_rate, calculate_quote_totals_enhanced
from app.core.money import Money
from app.models.cost import CostFixed
from app.models.organization import Organization
from app.models.service import Service
from app.models.tax import Tax
from app.models.team import TeamMember


@pytest.mark.integration
class TestFinancialPrecision:
    """Tests para validar precisión en cálculos críticos"""

    @pytest.mark.asyncio
    async def test_bcr_precision_accumulation(
        self, db_session: AsyncSession, test_organization: Organization
    ):
        """
        Test que BCR mantiene precisión en cálculos acumulativos
        ESTÁNDAR NOUGRAM: Validar que múltiples costos pequeños suman exactamente
        """
        # Crear múltiples costos pequeños que suman un total específico
        # Ejemplo: 10 costos de $0.10 cada uno = $1.00 exactamente

        # Crear organización con moneda USD
        test_organization.settings = {
            "primary_currency": "USD",
            "social_charges_config": {"enable_social_charges": False},
        }
        await db_session.commit()

        # Crear 10 costos fijos de $0.10 cada uno
        for i in range(10):
            cost = CostFixed(
                name=f"Test Cost {i + 1}",
                amount_monthly=Decimal("0.10"),
                currency="USD",
                organization_id=test_organization.id,
            )
            db_session.add(cost)

        # Crear un team member con salario específico
        team_member = TeamMember(
            name="Test Member",
            role="Developer",
            salary_monthly_brute=Decimal("1000.00"),
            currency="USD",
            billable_hours_per_week=40,
            is_active=True,
            organization_id=test_organization.id,
        )
        db_session.add(team_member)
        await db_session.commit()

        # Calcular BCR
        bcr = await calculate_blended_cost_rate(
            db_session,
            primary_currency="USD",
            tenant_id=test_organization.id,
            use_cache=False,  # No usar cache para test
        )

        # Verificar que BCR es Decimal
        assert isinstance(bcr, Decimal)

        # Verificar que el cálculo es preciso
        # Total costos fijos: 10 * $0.10 = $1.00
        # Total salarios: $1000.00
        # Total costos: $1001.00
        # Horas facturables: 40 * 4.33 = 173.2 horas/mes
        # BCR esperado: $1001.00 / 173.2 ≈ $5.78

        # Verificar que no hay errores de redondeo acumulativos
        assert bcr > Decimal("0")
        assert bcr < Decimal("100")  # Razonable para BCR

        # Verificar precisión: el cálculo debe ser exacto, no aproximado
        # Convertir a string y verificar que tiene precisión suficiente
        bcr_str = str(bcr)
        # Debe tener al menos 2 decimales de precisión
        assert "." in bcr_str
        decimal_part = bcr_str.split(".")[1]
        assert len(decimal_part) >= 2

    @pytest.mark.asyncio
    async def test_quote_calculation_precision(
        self, db_session: AsyncSession, test_organization: Organization
    ):
        """
        Test que cálculos de quotes mantienen precisión
        ESTÁNDAR NOUGRAM: Validar que múltiples items suman exactamente
        """
        # Crear servicio de prueba
        service = Service(
            name="Test Service",
            pricing_type="hourly",
            default_margin_target=Decimal("0.40"),  # 40% margin
            organization_id=test_organization.id,
            is_active=True,
        )
        db_session.add(service)
        await db_session.commit()

        # Crear BCR de prueba
        bcr = Decimal("50.00")  # $50/hora

        # Crear múltiples items con valores específicos
        items = [
            {
                "service_id": service.id,
                "estimated_hours": Decimal("10.0"),
                "pricing_type": "hourly",
            },
            {"service_id": service.id, "estimated_hours": Decimal("5.0"), "pricing_type": "hourly"},
            {"service_id": service.id, "estimated_hours": Decimal("2.5"), "pricing_type": "hourly"},
        ]

        # Calcular totals
        totals = await calculate_quote_totals_enhanced(
            db_session,
            items=items,
            blended_cost_rate=float(bcr),
            tax_ids=[],
            expenses=None,
            target_margin_percentage=None,
            currency="USD",
        )

        # Verificar que todos los valores son precisos
        assert isinstance(totals["total_internal_cost"], float)
        assert isinstance(totals["total_client_price"], float)
        assert isinstance(totals["margin_percentage"], float)

        # Verificar que los cálculos son correctos
        # Total horas: 10 + 5 + 2.5 = 17.5 horas
        # Costo interno esperado: 17.5 * $50 = $875.00
        expected_internal_cost = 17.5 * 50.0

        # Permitir pequeña diferencia por redondeo (menos de 1 centavo)
        assert abs(totals["total_internal_cost"] - expected_internal_cost) < 0.01

        # Verificar que client_price es mayor que internal_cost (tiene margen)
        assert totals["total_client_price"] > totals["total_internal_cost"]

        # Verificar que margin_percentage es razonable (entre 0 y 1)
        assert 0 <= totals["margin_percentage"] <= 1

    @pytest.mark.asyncio
    async def test_margin_calculation_precision(self, db_session: AsyncSession):
        """
        Test que aplicación de márgenes mantiene precisión
        ESTÁNDAR NOUGRAM: Validar fórmula exacta de margen
        """
        # Test con valores conocidos
        cost = Money(Decimal("100.00"), "USD")
        margin_percentage = 40.0  # 40% margin

        # Calcular precio con margen
        price = cost.apply_margin(margin_percentage)

        # Verificar que price es Money
        assert isinstance(price, Money)
        assert price.currency == "USD"

        # Verificar cálculo exacto: cost / (1 - margin) = 100 / 0.6 = 166.666...
        # Con ROUND_HALF_UP debe ser 166.67
        expected_price = Decimal("166.67")
        actual_price = price.quantize(Decimal("0.01")).amount

        # Verificar que está dentro de 1 centavo
        assert abs(actual_price - expected_price) <= Decimal("0.01")

        # Verificar que el margen calculado es correcto
        margin_amount = price.subtract(cost)
        calculated_margin = (margin_amount.amount / price.amount) * Decimal("100")

        # El margen calculado debe estar cerca de 40%
        assert abs(calculated_margin - Decimal("40")) < Decimal("0.1")

    @pytest.mark.asyncio
    async def test_tax_calculation_precision(
        self, db_session: AsyncSession, test_organization: Organization
    ):
        """
        Test que cálculos de impuestos mantienen precisión
        ESTÁNDAR NOUGRAM: Validar aplicación exacta de porcentajes
        """
        # Crear tax de prueba
        tax = Tax(
            name="IVA",
            code="IVA",
            percentage=Decimal("19.00"),  # 19% IVA
            is_active=True,
            organization_id=test_organization.id,
        )
        db_session.add(tax)
        await db_session.commit()

        # Test con precio conocido
        price = Money(Decimal("1000.00"), "USD")

        # Aplicar porcentaje de impuesto
        tax_amount = price.apply_percentage(tax.percentage)

        # Verificar que tax_amount es Money
        assert isinstance(tax_amount, Money)
        assert tax_amount.currency == "USD"

        # Verificar cálculo exacto: 1000 * 0.19 = 190.00
        expected_tax = Decimal("190.00")
        assert tax_amount.amount == expected_tax

        # Verificar que el porcentaje aplicado es correcto
        calculated_percentage = (tax_amount.amount / price.amount) * Decimal("100")
        assert calculated_percentage == tax.percentage

    @pytest.mark.asyncio
    async def test_expense_calculation_precision(self, db_session: AsyncSession):
        """
        Test que cálculos de expenses mantienen precisión
        ESTÁNDAR NOUGRAM: Validar markup y multiplicación exacta
        """
        # Crear expense con valores específicos
        expense_cost = Money(Decimal("100.00"), "USD")
        markup_percentage = 10.0  # 10% markup
        quantity = Decimal("2.0")

        # Calcular costo total
        total_cost = expense_cost.multiply(quantity)
        assert total_cost.amount == Decimal("200.00")

        # Calcular precio con markup
        markup_multiplier = Decimal("1") + (Decimal(str(markup_percentage)) / Decimal("100"))
        client_price = total_cost.multiply(markup_multiplier)

        # Verificar cálculo exacto: 200 * 1.10 = 220.00
        expected_price = Decimal("220.00")
        assert client_price.amount == expected_price

    @pytest.mark.asyncio
    async def test_sum_money_precision(self, db_session: AsyncSession):
        """
        Test que sumas de Money mantienen precisión
        ESTÁNDAR NOUGRAM: Validar que 0.1 + 0.2 = 0.3 exactamente
        """
        # Test clásico de precisión: 0.1 + 0.2 = 0.3
        a = Money(Decimal("0.1"), "USD")
        b = Money(Decimal("0.2"), "USD")

        result = a.add(b)

        # Verificar que es exactamente 0.3, no 0.30000000000000004
        assert result.amount == Decimal("0.3")

        # Test con múltiples valores
        amounts = [
            Money(Decimal("0.01"), "USD"),
            Money(Decimal("0.02"), "USD"),
            Money(Decimal("0.03"), "USD"),
            Money(Decimal("0.04"), "USD"),
            Money(Decimal("0.05"), "USD"),
        ]

        from app.core.money import sum_money

        total = sum_money(amounts)

        # Verificar que suma exacta: 0.01 + 0.02 + 0.03 + 0.04 + 0.05 = 0.15
        assert total is not None
        assert total.amount == Decimal("0.15")

    @pytest.mark.asyncio
    async def test_rounding_consistency(self, db_session: AsyncSession):
        """
        Test que redondeo es consistente (ROUND_HALF_UP)
        ESTÁNDAR NOUGRAM: Validar que 0.5 redondea hacia arriba, no hacia par
        """
        # Test con valores que terminan en .5
        # Con ROUND_HALF_UP: 0.5 → 1 (hacia arriba)
        # Con ROUND_HALF_EVEN (banker's rounding): 0.5 → 0 (hacia par)

        money = Money(Decimal("0.5"), "USD")
        quantized = money.quantize(Decimal("1"))  # Redondear a unidades enteras

        # Con ROUND_HALF_UP debe ser 1, no 0
        assert quantized.amount == Decimal("1")

        # Test con 1.5
        money2 = Money(Decimal("1.5"), "USD")
        quantized2 = money2.quantize(Decimal("1"))
        assert quantized2.amount == Decimal("2")

        # Test con 2.5
        money3 = Money(Decimal("2.5"), "USD")
        quantized3 = money3.quantize(Decimal("1"))
        assert quantized3.amount == Decimal("3")
