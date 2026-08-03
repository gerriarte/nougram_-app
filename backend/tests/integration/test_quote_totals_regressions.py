"""
Regresiones de totales de cotización (paquete P3).

H07/H43 — El impuesto se calculaba sobre la contingencia al releer el presupuesto y
          sin ella en el preview: el mismo presupuesto valía distinto en pantalla que
          al reabrirlo (delta = tasa × contingencia).
H29/H44 — Los expenses se persistían pero quedaban fuera de los totales guardados,
          tanto al guardar el presupuesto como al alta/baja por su propio endpoint.
H47     — quantity=0 (válido según el schema) reventaba con TypeError Decimal * float
          y, de arreglarse a medias, se cobraba como quantity=1.
H08     — create_new_quote_version cotizaba en project.currency en vez de la primaria.
H33/H45 — update_quote reetiquetaba project.currency sin convertir un solo importe.
"""

import uuid
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, get_password_hash
from app.models.organization import Organization
from app.models.project import Project, Quote, QuoteExpense, QuoteItem, project_taxes
from app.models.tax import Tax
from app.models.user import User
from app.services.project_service import compute_quote_tax_totals, quote_taxable_base


def _auth_headers(user: User) -> dict:
    token = create_access_token(
        {
            "sub": str(user.id),
            "email": user.email,
            "name": getattr(user, "full_name", None),
            "organization_id": user.organization_id,
        }
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def unlimited_credits(db_session: AsyncSession, test_organization: Organization) -> None:
    """Crear una versión consume 1 crédito; el plan free del fixture arranca en 0."""
    from app.models.credit_account import CreditAccount

    existing = (
        await db_session.execute(
            select(CreditAccount).where(CreditAccount.organization_id == test_organization.id)
        )
    ).scalar_one_or_none()
    if existing is None:
        db_session.add(
            CreditAccount(
                organization_id=test_organization.id,
                credits_available=0,
                credits_per_month=None,  # NULL = ilimitado
            )
        )
        await db_session.commit()


@pytest.fixture
async def owner_user(db_session: AsyncSession, test_organization: Organization) -> User:
    user = User(
        email=f"owner-{uuid.uuid4().hex[:8]}@example.com",
        full_name="Owner User",
        role="owner",
        role_type="tenant",
        hashed_password=get_password_hash("password123"),
        organization_id=test_organization.id,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


async def _make_project(
    db_session: AsyncSession,
    organization: Organization,
    *,
    currency: str = "USD",
    name: str = "Totals Project",
) -> Project:
    project = Project(
        name=name,
        client_name="Totals Client",
        currency=currency,
        status="Draft",
        organization_id=organization.id,
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)
    return project


async def _make_quote(
    db_session: AsyncSession,
    project: Project,
    *,
    version: int = 1,
    total_internal_cost: Decimal = Decimal("6000000"),
    total_client_price: Decimal = Decimal("10000000"),
    contingency_type: str | None = None,
    contingency_value: Decimal | None = None,
) -> Quote:
    quote = Quote(
        project_id=project.id,
        version=version,
        total_internal_cost=total_internal_cost,
        total_client_price=total_client_price,
        margin_percentage=Decimal("0.4"),
        contingency_type=contingency_type,
        contingency_value=contingency_value,
    )
    db_session.add(quote)
    await db_session.commit()
    await db_session.refresh(quote)
    return quote


@pytest.mark.integration
class TestContingencyIsNotTaxedOnRead:
    """H07/H43: la contingencia se suma DESPUÉS de los impuestos, en todos los caminos."""

    def test_taxable_base_reverses_contingency(self):
        # percentage: 1.100.000 con 10% => base 1.000.000
        assert quote_taxable_base(Decimal("1100000"), "percentage", Decimal("10")) == Decimal(
            "1000000"
        )
        # fixed: 1.100.000 con 100.000 => base 1.000.000
        assert quote_taxable_base(Decimal("1100000"), "fixed", Decimal("100000")) == Decimal(
            "1000000"
        )
        # sin contingencia la base es el precio entero
        assert quote_taxable_base(Decimal("1100000"), None, None) == Decimal("1100000")

        total_taxes, total_with_taxes = compute_quote_tax_totals(
            Decimal("1100000"), "percentage", Decimal("10"), [Decimal("19")]
        )
        # Antes: 19% sobre 1.100.000 = 209.000 (gravaba la contingencia).
        assert total_taxes == Decimal("190000")
        assert total_with_taxes == Decimal("1290000")

    def test_tax_lines_sum_the_total(self):
        """
        El desglose por impuesto (PDF, DOCX, análisis de rentabilidad) usa la MISMA base
        que el agregado: si cada línea se calculara aparte, el documento se contradiría.
        """
        from app.core.quote_taxes import compute_quote_tax_lines

        class _Tax:
            def __init__(self, name, code, percentage):
                self.name, self.code, self.percentage = name, code, percentage

        lines, total_taxes, total_with_taxes = compute_quote_tax_lines(
            Decimal("1100000"),
            "percentage",
            Decimal("10"),
            [_Tax("IVA", "IVA", Decimal("19")), _Tax("ICA", "ICA", Decimal("1"))],
        )

        assert [line["amount"] for line in lines] == [Decimal("190000"), Decimal("10000")]
        assert sum(line["amount"] for line in lines) == total_taxes
        assert total_with_taxes == Decimal("1300000")

        # Un impuesto sin porcentaje no genera línea ni rompe el cálculo.
        lines, total_taxes, _ = compute_quote_tax_lines(
            Decimal("1000"), None, None, [_Tax("Sin tasa", None, None)]
        )
        assert lines == []
        assert total_taxes == Decimal("0")

    async def test_read_path_matches_preview(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        test_organization: Organization,
        test_user: User,
        test_service,
        test_settings,
    ):
        tax = Tax(
            name="IVA",
            code=f"IVA_{uuid.uuid4().hex[:6]}",
            percentage=Decimal("19"),
            country="CO",
            is_active=True,
            organization_id=test_organization.id,
        )
        db_session.add(tax)
        await db_session.commit()
        await db_session.refresh(tax)

        # Preview: 1.000.000 de base + 10% de contingencia, IVA 19%.
        preview = await async_client.post(
            "/api/v1/quotes/calculate",
            json={
                "items": [
                    {
                        "service_id": test_service.id,
                        "pricing_type": "fixed",
                        "fixed_price": "1000000",
                        "quantity": "1",
                    }
                ],
                "tax_ids": [tax.id],
                "contingency_type": "percentage",
                "contingency_value": "10",
            },
            headers=_auth_headers(test_user),
        )
        assert preview.status_code == 200, preview.text
        preview_data = preview.json()
        assert Decimal(str(preview_data["total_client_price"])) == Decimal("1100000")

        # Mismo presupuesto ya guardado.
        project = await _make_project(db_session, test_organization)
        await db_session.execute(insert(project_taxes).values(project_id=project.id, tax_id=tax.id))
        quote = await _make_quote(
            db_session,
            project,
            total_internal_cost=Decimal("600000"),
            total_client_price=Decimal("1100000"),
            contingency_type="percentage",
            contingency_value=Decimal("10"),
        )
        await db_session.commit()

        response = await async_client.get(
            f"/api/v1/projects/{project.id}/quotes/{quote.id}",
            headers=_auth_headers(test_user),
        )
        assert response.status_code == 200, response.text
        data = response.json()

        # Antes: 209.000 y 1.309.000 al leer contra 190.000 y 1.290.000 en el preview.
        assert Decimal(str(data["total_taxes"])) == Decimal(str(preview_data["total_taxes"]))
        assert Decimal(str(data["total_with_taxes"])) == Decimal(
            str(preview_data["total_with_taxes"])
        )
        assert Decimal(str(data["total_taxes"])) == Decimal("190000")


@pytest.mark.integration
class TestExpensesEnterPersistedTotals:
    """H29: guardar el presupuesto con expenses tiene que sumarlos, como hace el preview."""

    async def test_update_quote_includes_expenses(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        test_organization: Organization,
        test_user: User,
        test_service,
        test_settings,
    ):
        project = await _make_project(db_session, test_organization)
        quote = await _make_quote(
            db_session,
            project,
            total_internal_cost=Decimal("0"),
            total_client_price=Decimal("0"),
        )

        response = await async_client.put(
            f"/api/v1/projects/{project.id}/quotes/{quote.id}",
            json={
                "items": [
                    {
                        "service_id": test_service.id,
                        "pricing_type": "fixed",
                        "fixed_price": "1000000",
                        "quantity": "1",
                    }
                ],
                "expenses": [
                    {
                        "name": "Pauta Meta",
                        "cost": "2000000",
                        "markup_percentage": "0.25",
                        "quantity": "1",
                    }
                ],
            },
            headers=_auth_headers(test_user),
        )
        assert response.status_code == 200, response.text
        data = response.json()

        # 1.000.000 del ítem + 2.500.000 del expense (2.000.000 × 1,25).
        assert Decimal(str(data["total_client_price"])) == Decimal("3500000")
        assert Decimal(str(data["total_internal_cost"])) >= Decimal("2000000")

        quote_id = quote.id
        db_session.expire_all()
        stored = (await db_session.execute(select(Quote).where(Quote.id == quote_id))).scalar_one()
        assert Decimal(str(stored.total_client_price)) == Decimal("3500000")
        assert Decimal(str(stored.total_internal_cost)) >= Decimal("2000000")


@pytest.mark.integration
class TestExpenseEndpointsKeepQuoteTotalsInSync:
    """H44 y H47: el endpoint de expenses tiene que recalcular totales y aceptar quantity=0."""

    async def test_create_expense_updates_quote_totals(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        test_organization: Organization,
        owner_user: User,
        test_service,
    ):
        headers = _auth_headers(owner_user)
        project = await _make_project(db_session, test_organization)
        quote = await _make_quote(db_session, project)
        item = QuoteItem(
            quote_id=quote.id,
            service_id=test_service.id,
            internal_cost=Decimal("6000000"),
            client_price=Decimal("10000000"),
            pricing_type="fixed",
            fixed_price=Decimal("10000000"),
            quantity=Decimal("1"),
        )
        db_session.add(item)
        await db_session.commit()

        response = await async_client.post(
            f"/api/v1/projects/{project.id}/quotes/{quote.id}/expenses",
            json={
                "name": "Pauta Meta",
                "cost": "2000000",
                "markup_percentage": "0.20",
                "quantity": "1",
            },
            headers=headers,
        )
        assert response.status_code == 201, response.text
        assert Decimal(str(response.json()["client_price"])) == Decimal("2400000")

        project_id = project.id
        quote_id = quote.id
        db_session.expire_all()
        stored = (await db_session.execute(select(Quote).where(Quote.id == quote_id))).scalar_one()
        # Antes: el expense se guardaba pero el total del presupuesto no se movía.
        assert Decimal(str(stored.total_client_price)) == Decimal("12400000")
        assert Decimal(str(stored.total_internal_cost)) == Decimal("8000000")

        # Y al borrarlo, los totales vuelven.
        expense_id = response.json()["id"]
        delete_response = await async_client.delete(
            f"/api/v1/projects/{project_id}/quotes/{quote_id}/expenses/{expense_id}",
            headers=headers,
        )
        assert delete_response.status_code == 204, delete_response.text

        db_session.expire_all()
        stored = (await db_session.execute(select(Quote).where(Quote.id == quote_id))).scalar_one()
        assert Decimal(str(stored.total_client_price)) == Decimal("10000000")
        assert Decimal(str(stored.total_internal_cost)) == Decimal("6000000")

    async def test_expense_with_zero_quantity_is_free_and_does_not_crash(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        test_organization: Organization,
        owner_user: User,
    ):
        project = await _make_project(db_session, test_organization)
        quote = await _make_quote(
            db_session,
            project,
            total_internal_cost=Decimal("0"),
            total_client_price=Decimal("0"),
        )

        response = await async_client.post(
            f"/api/v1/projects/{project.id}/quotes/{quote.id}/expenses",
            json={
                "name": "Pauta",
                "cost": "500000",
                "markup_percentage": "0.2",
                "quantity": "0",
            },
            headers=_auth_headers(owner_user),
        )
        # Antes: TypeError Decimal * float -> HTTP 500.
        assert response.status_code == 201, response.text
        data = response.json()
        assert Decimal(str(data["quantity"])) == Decimal("0")
        # Antes (arreglando sólo el TypeError): se cobraba 600.000, una unidad fantasma.
        assert Decimal(str(data["client_price"])) == Decimal("0")

        expense_id = data["id"]
        db_session.expire_all()
        stored_expense = (
            await db_session.execute(select(QuoteExpense).where(QuoteExpense.id == expense_id))
        ).scalar_one()
        assert Decimal(str(stored_expense.quantity)) == Decimal("0")


@pytest.mark.integration
class TestQuoteCurrencyIsNormalizedNotRelabeled:
    """H08, H33 y H45: la moneda primaria manda, y reetiquetar exige convertir."""

    async def test_update_quote_converts_other_versions_and_payload(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        test_organization: Organization,
        test_user: User,
        test_service,
        test_settings,
    ):
        test_organization.settings = {"primary_currency": "COP"}
        db_session.add(test_organization)
        await db_session.commit()

        project = await _make_project(db_session, test_organization, currency="USD")
        v1 = await _make_quote(
            db_session,
            project,
            version=1,
            total_internal_cost=Decimal("6000"),
            total_client_price=Decimal("10000"),
        )
        v2 = await _make_quote(
            db_session,
            project,
            version=2,
            total_internal_cost=Decimal("6000"),
            total_client_price=Decimal("10000"),
        )

        response = await async_client.put(
            f"/api/v1/projects/{project.id}/quotes/{v2.id}",
            json={
                "items": [
                    {
                        "service_id": test_service.id,
                        "pricing_type": "fixed",
                        "fixed_price": "5000",
                        "quantity": "1",
                    }
                ]
            },
            headers=_auth_headers(test_user),
        )
        assert response.status_code == 200, response.text
        data = response.json()

        # El precio tipeado en USD por la UI no puede quedar valuado como COP.
        assert Decimal(str(data["total_client_price"])) == Decimal("20000000")

        v1_id = v1.id
        project_id = project.id
        db_session.expire_all()
        stored_v1 = (await db_session.execute(select(Quote).where(Quote.id == v1_id))).scalar_one()
        stored_project = (
            await db_session.execute(select(Project).where(Project.id == project_id))
        ).scalar_one()

        assert stored_project.currency == "COP"
        # Antes: la v1 seguía en 10.000 pero se leía como COP (~USD 2,50).
        assert Decimal(str(stored_v1.total_client_price)) == Decimal("40000000")
        assert Decimal(str(stored_v1.total_internal_cost)) == Decimal("24000000")

    async def test_new_version_uses_primary_currency(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        test_organization: Organization,
        owner_user: User,
        test_service,
        test_settings,
        unlimited_credits,
    ):
        test_organization.settings = {"primary_currency": "COP"}
        db_session.add(test_organization)
        await db_session.commit()

        project = await _make_project(db_session, test_organization, currency="USD")
        v1 = await _make_quote(
            db_session,
            project,
            version=1,
            total_internal_cost=Decimal("6000"),
            total_client_price=Decimal("10000"),
        )

        response = await async_client.post(
            f"/api/v1/projects/{project.id}/quotes/{v1.id}/new-version",
            json={
                "items": [
                    {
                        "service_id": test_service.id,
                        "pricing_type": "fixed",
                        "fixed_price": "5000",
                        "quantity": "1",
                    }
                ]
            },
            headers=_auth_headers(owner_user),
        )
        assert response.status_code in (200, 201), response.text
        data = response.json()

        # Antes: la v2 se cotizaba en project.currency ('USD') y quedaba en 5.000.
        assert Decimal(str(data["total_client_price"])) == Decimal("20000000")

        project_id = project.id
        db_session.expire_all()
        stored_project = (
            await db_session.execute(select(Project).where(Project.id == project_id))
        ).scalar_one()
        assert stored_project.currency == "COP"
