"""
Integration tests for SQL Numeric precision validation
ESTÁNDAR NOUGRAM: Validar que SUM() en SQL con Numeric mantiene exactitud
"""

from decimal import Decimal

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.organization import Organization
from app.models.project import Project, Quote, QuoteExpense, QuoteItem


@pytest.mark.integration
class TestSQLNumericPrecision:
    """Tests para validar precisión de SUM() en SQL con campos Numeric"""

    @pytest.mark.asyncio
    async def test_sum_quote_items_precision(
        self, db_session: AsyncSession, test_organization: Organization
    ):
        """
        Test que SUM() de QuoteItems mantiene precisión exacta
        ESTÁNDAR NOUGRAM: Validar que múltiples items suman exactamente en SQL
        """
        # Crear proyecto de prueba
        project = Project(
            name="Test Project",
            client_name="Test Client",
            currency="USD",
            organization_id=test_organization.id,
        )
        db_session.add(project)
        await db_session.commit()

        # Crear quote de prueba
        quote = Quote(project_id=project.id, version=1, organization_id=test_organization.id)
        db_session.add(quote)
        await db_session.commit()

        # Crear múltiples items con valores específicos que suman exactamente
        # Ejemplo: 3 items de $33.333... cada uno = $100.00 exactamente
        items = [
            QuoteItem(
                quote_id=quote.id,
                service_id=1,  # Service ID no importa para este test
                internal_cost=Decimal("33.3333"),
                client_price=Decimal("55.5555"),
                margin_percentage=Decimal("0.40"),
                organization_id=test_organization.id,
            ),
            QuoteItem(
                quote_id=quote.id,
                service_id=1,
                internal_cost=Decimal("33.3333"),
                client_price=Decimal("55.5555"),
                margin_percentage=Decimal("0.40"),
                organization_id=test_organization.id,
            ),
            QuoteItem(
                quote_id=quote.id,
                service_id=1,
                internal_cost=Decimal("33.3334"),  # Último item ajustado para sumar exactamente
                client_price=Decimal("55.5556"),
                margin_percentage=Decimal("0.40"),
                organization_id=test_organization.id,
            ),
        ]

        for item in items:
            db_session.add(item)
        await db_session.commit()

        # Calcular SUM() en SQL usando Numeric
        result = await db_session.execute(
            select(
                func.sum(QuoteItem.internal_cost).label("total_internal_cost"),
                func.sum(QuoteItem.client_price).label("total_client_price"),
            ).where(QuoteItem.quote_id == quote.id)
        )

        row = result.first()
        total_internal_cost = row.total_internal_cost
        total_client_price = row.total_client_price

        # Verificar que los valores son Decimal (no float)
        assert isinstance(total_internal_cost, Decimal)
        assert isinstance(total_client_price, Decimal)

        # Verificar que la suma es exacta
        # 33.3333 + 33.3333 + 33.3334 = 100.0000
        expected_internal = Decimal("100.0000")
        assert total_internal_cost == expected_internal

        # Verificar que no hay errores de precisión
        # La diferencia debe ser exactamente 0, no 0.00000000000001
        assert abs(total_internal_cost - expected_internal) == Decimal("0")

    @pytest.mark.asyncio
    async def test_sum_quote_expenses_precision(
        self, db_session: AsyncSession, test_organization: Organization
    ):
        """
        Test que SUM() de QuoteExpenses mantiene precisión exacta
        ESTÁNDAR NOUGRAM: Validar que expenses con markup suman exactamente
        """
        # Crear proyecto y quote
        project = Project(
            name="Test Project",
            client_name="Test Client",
            currency="USD",
            organization_id=test_organization.id,
        )
        db_session.add(project)
        await db_session.commit()

        quote = Quote(project_id=project.id, version=1, organization_id=test_organization.id)
        db_session.add(quote)
        await db_session.commit()

        # Crear múltiples expenses con valores específicos
        expenses = [
            QuoteExpense(
                quote_id=quote.id,
                name="Expense 1",
                cost=Decimal("10.1234"),
                markup_percentage=Decimal("0.10"),  # 10% markup
                quantity=Decimal("1.0"),
                client_price=Decimal("11.1357"),  # 10.1234 * 1.1
                organization_id=test_organization.id,
            ),
            QuoteExpense(
                quote_id=quote.id,
                name="Expense 2",
                cost=Decimal("20.5678"),
                markup_percentage=Decimal("0.10"),
                quantity=Decimal("1.0"),
                client_price=Decimal("22.6246"),  # 20.5678 * 1.1
                organization_id=test_organization.id,
            ),
            QuoteExpense(
                quote_id=quote.id,
                name="Expense 3",
                cost=Decimal("30.9012"),
                markup_percentage=Decimal("0.10"),
                quantity=Decimal("1.0"),
                client_price=Decimal("33.9913"),  # 30.9012 * 1.1
                organization_id=test_organization.id,
            ),
        ]

        for expense in expenses:
            db_session.add(expense)
        await db_session.commit()

        # Calcular SUM() en SQL
        result = await db_session.execute(
            select(
                func.sum(QuoteExpense.cost).label("total_cost"),
                func.sum(QuoteExpense.client_price).label("total_client_price"),
            ).where(QuoteExpense.quote_id == quote.id)
        )

        row = result.first()
        total_cost = row.total_cost
        total_client_price = row.total_client_price

        # Verificar que son Decimal
        assert isinstance(total_cost, Decimal)
        assert isinstance(total_client_price, Decimal)

        # Verificar suma exacta de costos
        expected_cost = Decimal("10.1234") + Decimal("20.5678") + Decimal("30.9012")
        assert total_cost == expected_cost

        # Verificar suma exacta de precios
        expected_price = Decimal("11.1357") + Decimal("22.6246") + Decimal("33.9913")
        assert total_client_price == expected_price

    @pytest.mark.asyncio
    async def test_sum_with_quantity_precision(
        self, db_session: AsyncSession, test_organization: Organization
    ):
        """
        Test que SUM() con quantity mantiene precisión
        ESTÁNDAR NOUGRAM: Validar multiplicación y suma exacta
        """
        # Crear proyecto y quote
        project = Project(
            name="Test Project",
            client_name="Test Client",
            currency="USD",
            organization_id=test_organization.id,
        )
        db_session.add(project)
        await db_session.commit()

        quote = Quote(project_id=project.id, version=1, organization_id=test_organization.id)
        db_session.add(quote)
        await db_session.commit()

        # Crear items con quantity
        items = [
            QuoteItem(
                quote_id=quote.id,
                service_id=1,
                internal_cost=Decimal("10.00"),
                client_price=Decimal("16.67"),
                quantity=Decimal("2.5"),  # Quantity con decimales
                organization_id=test_organization.id,
            ),
            QuoteItem(
                quote_id=quote.id,
                service_id=1,
                internal_cost=Decimal("20.00"),
                client_price=Decimal("33.33"),
                quantity=Decimal("1.5"),
                organization_id=test_organization.id,
            ),
        ]

        for item in items:
            db_session.add(item)
        await db_session.commit()

        # Calcular SUM() de internal_cost * quantity en SQL
        # Nota: SQLAlchemy puede requerir usar func.sum() con expresión
        result = await db_session.execute(
            select(
                func.sum(QuoteItem.internal_cost * QuoteItem.quantity).label("total_weighted_cost")
            ).where(QuoteItem.quote_id == quote.id)
        )

        row = result.first()
        total_weighted_cost = row.total_weighted_cost

        # Verificar que es Decimal
        assert isinstance(total_weighted_cost, Decimal)

        # Verificar cálculo exacto
        # Item 1: 10.00 * 2.5 = 25.00
        # Item 2: 20.00 * 1.5 = 30.00
        # Total: 55.00
        expected_total = Decimal("55.00")
        assert total_weighted_cost == expected_total

    @pytest.mark.asyncio
    async def test_sum_margin_percentage_precision(
        self, db_session: AsyncSession, test_organization: Organization
    ):
        """
        Test que SUM() de porcentajes mantiene precisión
        ESTÁNDAR NOUGRAM: Validar que porcentajes suman exactamente
        """
        # Crear proyecto y quote
        project = Project(
            name="Test Project",
            client_name="Test Client",
            currency="USD",
            organization_id=test_organization.id,
        )
        db_session.add(project)
        await db_session.commit()

        quote = Quote(
            project_id=project.id,
            version=1,
            margin_percentage=Decimal("0.40"),  # 40% margin
            organization_id=test_organization.id,
        )
        db_session.add(quote)
        await db_session.commit()

        # Verificar que margin_percentage se guarda como Numeric
        await db_session.refresh(quote)
        assert isinstance(quote.margin_percentage, Decimal)
        assert quote.margin_percentage == Decimal("0.40")

        # Calcular AVG() de margin_percentage en múltiples quotes
        quote2 = Quote(
            project_id=project.id,
            version=2,
            margin_percentage=Decimal("0.35"),  # 35% margin
            organization_id=test_organization.id,
        )
        db_session.add(quote2)
        await db_session.commit()

        result = await db_session.execute(
            select(func.avg(Quote.margin_percentage).label("avg_margin")).where(
                Quote.project_id == project.id
            )
        )

        row = result.first()
        avg_margin = row.avg_margin

        # Verificar que es Decimal
        assert isinstance(avg_margin, Decimal)

        # Verificar cálculo exacto: (0.40 + 0.35) / 2 = 0.375
        expected_avg = Decimal("0.375")
        assert avg_margin == expected_avg

    @pytest.mark.asyncio
    async def test_numeric_vs_float_precision_comparison(
        self, db_session: AsyncSession, test_organization: Organization
    ):
        """
        Test comparativo: Numeric vs Float en SUM()
        ESTÁNDAR NOUGRAM: Demostrar que Numeric es más preciso que Float
        """
        # Crear múltiples items con valores que causan error de precisión en Float
        # Ejemplo: 0.1 + 0.2 en Float = 0.30000000000000004
        # En Numeric debe ser exactamente 0.3

        project = Project(
            name="Test Project",
            client_name="Test Client",
            currency="USD",
            organization_id=test_organization.id,
        )
        db_session.add(project)
        await db_session.commit()

        quote = Quote(project_id=project.id, version=1, organization_id=test_organization.id)
        db_session.add(quote)
        await db_session.commit()

        # Crear items con valores problemáticos para Float
        items = [
            QuoteItem(
                quote_id=quote.id,
                service_id=1,
                internal_cost=Decimal("0.1"),
                client_price=Decimal("0.1667"),
                organization_id=test_organization.id,
            ),
            QuoteItem(
                quote_id=quote.id,
                service_id=1,
                internal_cost=Decimal("0.2"),
                client_price=Decimal("0.3333"),
                organization_id=test_organization.id,
            ),
        ]

        for item in items:
            db_session.add(item)
        await db_session.commit()

        # Calcular SUM() en SQL
        result = await db_session.execute(
            select(func.sum(QuoteItem.internal_cost).label("total_cost")).where(
                QuoteItem.quote_id == quote.id
            )
        )

        row = result.first()
        total_cost = row.total_cost

        # Verificar que es exactamente 0.3, no 0.30000000000000004
        assert isinstance(total_cost, Decimal)
        assert total_cost == Decimal("0.3")

        # Verificar que NO es el valor incorrecto de Float
        float_result = 0.1 + 0.2
        assert total_cost != Decimal(str(float_result))  # Debe ser diferente del resultado Float
