"""
Regresiones de rescate del paquete P3 (totales de cotización).

B1 — El adaptador expenses_to_calculation_dicts() reintrodujo el patrón falsy-cero que
     se había sacado de expenses.py: un expense con quantity=0 entraba a los totales
     persistidos como 1 unidad, mientras la fila QuoteExpense se guardaba con
     quantity=0 / client_price=0. Las dos puertas (PUT del presupuesto y
     recalculate_quote_totals_from_rows, que usa el endpoint de expenses) devolvían
     números distintos para los MISMOS datos.

B2 — El cuerpo del mail al cliente y el PDF/DOCX adjuntos en ESE MISMO envío imprimían
     totales distintos. Mientras pdf_generator/docx_generator graven
     quote.total_client_price entero, el cuerpo del mail tiene que usar la misma regla.
"""

import uuid
from decimal import Decimal
from io import BytesIO

import pytest
from httpx import AsyncClient
from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, get_password_hash
from app.models.organization import Organization
from app.models.project import Project, Quote, QuoteExpense, QuoteItem, project_taxes
from app.models.tax import Tax
from app.models.user import User
from app.services.project_service import (
    ProjectService,
    _expense_internal_cost,
    expenses_to_calculation_dicts,
    recalculate_quote_totals_from_rows,
)


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
async def owner_user(db_session: AsyncSession, test_organization: Organization) -> User:
    user = User(
        email=f"p3-owner-{uuid.uuid4().hex[:8]}@example.com",
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
) -> Project:
    project = Project(
        name="P3 Rescue Project",
        client_name="P3 Client",
        client_email="cliente@example.com",
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
    total_internal_cost: Decimal = Decimal("0"),
    total_client_price: Decimal = Decimal("0"),
    contingency_type: str | None = None,
    contingency_value: Decimal | None = None,
) -> Quote:
    quote = Quote(
        project_id=project.id,
        version=1,
        total_internal_cost=total_internal_cost,
        total_client_price=total_client_price,
        margin_percentage=Decimal("0"),
        contingency_type=contingency_type,
        contingency_value=contingency_value,
    )
    db_session.add(quote)
    await db_session.commit()
    await db_session.refresh(quote)
    return quote


@pytest.mark.integration
class TestZeroQuantityExpenseInSavedTotals:
    """B1: quantity=0 no puede facturarse como 1 en ninguno de los dos caminos."""

    def test_adapter_keeps_zero_quantity(self):
        expense = QuoteExpense(
            name="Pauta",
            cost=Decimal("500000"),
            markup_percentage=Decimal("0.2"),
            quantity=Decimal("0"),
        )

        adapted = expenses_to_calculation_dicts([expense])[0]

        # Antes: Decimal('1') -> el adaptador inventaba una unidad.
        assert adapted["quantity"] == Decimal("0")
        # Y coincide con la otra puerta, que siempre lo hizo bien.
        assert adapted["cost"] * adapted["quantity"] == _expense_internal_cost(expense)

        # None (no especificado) sí sigue valiendo 1.
        sin_cantidad = QuoteExpense(
            name="Pauta", cost=Decimal("500000"), markup_percentage=Decimal("0"), quantity=None
        )
        assert expenses_to_calculation_dicts([sin_cantidad])[0]["quantity"] == Decimal("1")

    async def test_put_totals_match_row_derived_totals(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        test_organization: Organization,
        test_user: User,
        test_service,
        test_settings,
    ):
        project = await _make_project(db_session, test_organization)
        quote = await _make_quote(db_session, project)

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
                        "cost": "500000",
                        "markup_percentage": "0.2",
                        "quantity": "0",
                    }
                ],
            },
            headers=_auth_headers(test_user),
        )
        assert response.status_code == 200, response.text
        data = response.json()

        # Antes: 1.600.000 y 500.000 (una unidad fantasma que la fila no tiene).
        assert Decimal(str(data["total_client_price"])) == Decimal("1000000")
        assert Decimal(str(data["total_internal_cost"])) == Decimal("0")

        quote_id = quote.id
        db_session.expire_all()

        stored_expense = (
            await db_session.execute(select(QuoteExpense).where(QuoteExpense.quote_id == quote_id))
        ).scalar_one()
        assert Decimal(str(stored_expense.quantity)) == Decimal("0")
        assert Decimal(str(stored_expense.client_price)) == Decimal("0")

        # La otra puerta (la que dispara el endpoint de expenses) sobre las MISMAS filas
        # tiene que dar exactamente lo mismo: si no, el precio salta solo en el próximo
        # alta/baja de cualquier expense.
        stored_quote = (
            await db_session.execute(select(Quote).where(Quote.id == quote_id))
        ).scalar_one()
        derived = await recalculate_quote_totals_from_rows(db_session, stored_quote)

        assert derived["total_client_price"] == Decimal(str(data["total_client_price"]))
        assert derived["total_internal_cost"] == Decimal(str(data["total_internal_cost"]))


@pytest.mark.integration
class TestQuoteEmailBodyMatchesItsAttachment:
    """B2: el total del cuerpo del mail y el del adjunto tienen que ser el mismo número."""

    async def test_email_total_equals_docx_total(
        self,
        db_session: AsyncSession,
        test_organization: Organization,
        owner_user: User,
        test_service,
        monkeypatch,
    ):
        import app.core.email as email_module
        from app.schemas.quote import QuoteEmailRequest

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

        project = await _make_project(db_session, test_organization, currency="USD")
        await db_session.execute(insert(project_taxes).values(project_id=project.id, tax_id=tax.id))

        # 1.000.000 de base + 10% de contingencia ya aplicada al persistir.
        quote = await _make_quote(
            db_session,
            project,
            total_internal_cost=Decimal("600000"),
            total_client_price=Decimal("1100000"),
            contingency_type="percentage",
            contingency_value=Decimal("10"),
        )
        db_session.add(
            QuoteItem(
                quote_id=quote.id,
                service_id=test_service.id,
                internal_cost=Decimal("600000"),
                client_price=Decimal("1000000"),
                pricing_type="fixed",
                fixed_price=Decimal("1000000"),
                quantity=Decimal("1"),
            )
        )
        await db_session.commit()

        captured: dict = {}

        async def _fake_send_email(**kwargs):
            captured.update(kwargs)
            return True

        monkeypatch.setattr(email_module, "send_email", _fake_send_email)

        service = ProjectService(db_session, test_organization.id)
        result = await service.send_quote_email(
            project.id,
            quote.id,
            QuoteEmailRequest(to_email="cliente@example.com", include_pdf=False, include_docx=True),
            owner_user,
        )
        assert result.success is True

        body_total = _parse_amount(_extract_after(captured["body_text"], "Total:"))
        docx_total = _parse_amount(_docx_total_cell(captured["attachments"][0]["content"]))

        # Antes: cuerpo 1.290.000 vs adjunto 1.309.000 en el MISMO mail.
        assert body_total == docx_total


def _extract_after(text: str, marker: str) -> str:
    line = next(line for line in text.splitlines() if line.strip().startswith(marker))
    return line.split(marker, 1)[1].strip()


def _parse_amount(raw: str) -> Decimal:
    return Decimal(raw.replace("$", "").replace("€", "").replace(",", "").strip())


def _docx_total_cell(buffer: BytesIO) -> str:
    from docx import Document

    buffer.seek(0)
    document = Document(BytesIO(buffer.read()))
    for table in document.tables:
        for row in table.rows:
            cells = row.cells
            if len(cells) >= 2 and cells[0].text.strip() == "Total:":
                return cells[1].text
    raise AssertionError("El DOCX adjunto no tiene fila 'Total:'")
