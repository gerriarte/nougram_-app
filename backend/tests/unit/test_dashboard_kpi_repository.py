"""
Unit tests for DashboardKpiRepository (latest quote per project KPI aggregation).
"""
import uuid
from datetime import datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import insert

from app.models.organization import Organization
from app.models.project import Project, Quote, project_taxes
from app.models.tax import Tax
from app.repositories.dashboard_kpi_repository import DashboardKpiRepository


async def _fresh_org(db_session) -> Organization:
    """Committed rows persist across tests in the shared in-memory DB; isolate by org."""
    org = Organization(
        name="KPI Org",
        slug=f"kpi-org-{uuid.uuid4().hex[:10]}",
        subscription_plan="free",
        subscription_status="active",
    )
    db_session.add(org)
    await db_session.commit()
    await db_session.refresh(org)
    return org


def _window():
    start = datetime(2000, 1, 1, tzinfo=timezone.utc)
    end = datetime(2100, 1, 1, tzinfo=timezone.utc)
    return start, end


@pytest.mark.asyncio
async def test_counts_only_latest_quote_version(db_session):
    org = await _fresh_org(db_session)
    p = Project(
        name="MultiVersion",
        client_name="Client",
        organization_id=org.id,
        status="Sent",
        currency="USD",
    )
    db_session.add(p)
    await db_session.commit()
    await db_session.refresh(p)

    now = datetime(2025, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
    q1 = Quote(
        project_id=p.id,
        version=1,
        total_client_price=Decimal("100"),
        total_internal_cost=Decimal("40"),
        updated_at=now,
    )
    q2 = Quote(
        project_id=p.id,
        version=2,
        total_client_price=Decimal("200"),
        total_internal_cost=Decimal("80"),
        updated_at=now,
    )
    db_session.add_all([q1, q2])
    await db_session.commit()

    repo = DashboardKpiRepository(db_session)
    start, end = _window()
    totals = await repo.aggregate_latest_quotes_kpis(org.id, start, end)

    assert totals.numero_propuestas_realizadas == 1
    assert totals.total_cotizado_con_impuestos == Decimal("200")
    assert totals.costo_total_operacional == Decimal("80")
    assert totals.margen_neto_total == Decimal("120")


@pytest.mark.asyncio
async def test_excludes_draft_projects(db_session):
    org = await _fresh_org(db_session)
    p = Project(
        name="DraftP",
        client_name="C",
        organization_id=org.id,
        status="Draft",
        currency="USD",
    )
    db_session.add(p)
    await db_session.commit()
    await db_session.refresh(p)

    now = datetime(2025, 6, 15, tzinfo=timezone.utc)
    db_session.add(
        Quote(
            project_id=p.id,
            version=1,
            total_client_price=Decimal("50"),
            total_internal_cost=Decimal("10"),
            updated_at=now,
        )
    )
    await db_session.commit()

    repo = DashboardKpiRepository(db_session)
    start, end = _window()
    totals = await repo.aggregate_latest_quotes_kpis(org.id, start, end)

    assert totals.numero_propuestas_realizadas == 0
    assert totals.numero_propuestas_ganadas == 0


@pytest.mark.asyncio
async def test_won_status_and_taxes(db_session):
    org = await _fresh_org(db_session)
    p = Project(
        name="WonP",
        client_name="C",
        organization_id=org.id,
        status="Won",
        currency="USD",
    )
    db_session.add(p)
    await db_session.commit()
    await db_session.refresh(p)

    tax = Tax(
        name="IVA",
        code=f"IVA_TEST_KPI_{uuid.uuid4().hex[:8]}",
        percentage=Decimal("10"),
        organization_id=org.id,
    )
    db_session.add(tax)
    await db_session.commit()
    await db_session.refresh(tax)

    await db_session.execute(
        insert(project_taxes).values(project_id=p.id, tax_id=tax.id)
    )

    now = datetime(2025, 6, 15, tzinfo=timezone.utc)
    db_session.add(
        Quote(
            project_id=p.id,
            version=1,
            total_client_price=Decimal("100"),
            total_internal_cost=Decimal("30"),
            updated_at=now,
        )
    )
    await db_session.commit()

    repo = DashboardKpiRepository(db_session)
    start, end = _window()
    totals = await repo.aggregate_latest_quotes_kpis(org.id, start, end)

    assert totals.numero_propuestas_realizadas == 1
    assert totals.numero_propuestas_ganadas == 1
    # 100 + 10% = 110 billed; margin 110 - 30 = 80
    assert totals.total_cotizado_con_impuestos == Decimal("110")
    assert totals.margen_neto_total == Decimal("80")


@pytest.mark.asyncio
async def test_respects_updated_at_window(db_session):
    org = await _fresh_org(db_session)
    p = Project(
        name="Old",
        client_name="C",
        organization_id=org.id,
        status="Sent",
        currency="USD",
    )
    db_session.add(p)
    await db_session.commit()
    await db_session.refresh(p)

    old = datetime(1990, 1, 1, tzinfo=timezone.utc)
    db_session.add(
        Quote(
            project_id=p.id,
            version=1,
            total_client_price=Decimal("999"),
            total_internal_cost=Decimal("1"),
            updated_at=old,
        )
    )
    await db_session.commit()

    repo = DashboardKpiRepository(db_session)
    start = datetime(2000, 1, 1, tzinfo=timezone.utc)
    end = datetime(2001, 1, 1, tzinfo=timezone.utc)
    totals = await repo.aggregate_latest_quotes_kpis(org.id, start, end)

    assert totals.numero_propuestas_realizadas == 0
