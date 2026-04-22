"""
Integration tests for GET /api/v1/insights/dashboard/kpi-summary.
"""

import uuid
from datetime import UTC, datetime

import pytest
from httpx import AsyncClient
from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, get_password_hash
from app.models.organization import Organization
from app.models.project import Project, Quote, project_taxes
from app.models.tax import Tax
from app.models.user import User


def _auth_headers(user: User) -> dict:
    token = create_access_token(
        {
            "sub": str(user.id),
            "email": user.email,
            "organization_id": user.organization_id,
        }
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def kpi_org(db_session: AsyncSession) -> Organization:
    org = Organization(
        name="KPI Endpoint Org",
        slug=f"kpi-endpoint-{uuid.uuid4().hex[:10]}",
        subscription_plan="free",
        subscription_status="active",
    )
    db_session.add(org)
    await db_session.commit()
    await db_session.refresh(org)
    return org


@pytest.fixture
async def kpi_user(db_session: AsyncSession, kpi_org: Organization) -> User:
    user = User(
        email=f"kpi-owner-{uuid.uuid4().hex[:8]}@test.com",
        full_name="KPI Owner",
        hashed_password=get_password_hash("test123"),
        role="owner",
        role_type="tenant",
        organization_id=kpi_org.id,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def kpi_seed_data(db_session: AsyncSession, kpi_org: Organization):
    # In-window project with multiple versions (latest version must win).
    p1 = Project(
        name="P1",
        client_name="ACME",
        organization_id=kpi_org.id,
        status="Sent",
        currency="USD",
    )
    # Draft project must be excluded.
    p2 = Project(
        name="P2",
        client_name="DRAFT CLIENT",
        organization_id=kpi_org.id,
        status="Draft",
        currency="USD",
    )
    # Won project in window.
    p3 = Project(
        name="P3",
        client_name="WON CLIENT",
        organization_id=kpi_org.id,
        status="Won",
        currency="USD",
    )
    # Out-of-window project must be excluded by quote.updated_at.
    p4 = Project(
        name="P4",
        client_name="OLD CLIENT",
        organization_id=kpi_org.id,
        status="Sent",
        currency="USD",
    )
    db_session.add_all([p1, p2, p3, p4])
    await db_session.commit()
    for p in (p1, p2, p3, p4):
        await db_session.refresh(p)

    q1_v1 = Quote(
        project_id=p1.id,
        version=1,
        total_client_price=100,
        total_internal_cost=40,
        updated_at=datetime(2025, 6, 10, 12, 0, tzinfo=UTC),
    )
    q1_v2 = Quote(
        project_id=p1.id,
        version=2,
        total_client_price=200,
        total_internal_cost=80,
        updated_at=datetime(2025, 6, 20, 12, 0, tzinfo=UTC),
    )
    q2 = Quote(
        project_id=p2.id,
        version=1,
        total_client_price=1000,
        total_internal_cost=100,
        updated_at=datetime(2025, 6, 15, 10, 0, tzinfo=UTC),
    )
    q3 = Quote(
        project_id=p3.id,
        version=1,
        total_client_price=300,
        total_internal_cost=120,
        updated_at=datetime(2025, 6, 22, 15, 0, tzinfo=UTC),
    )
    q4 = Quote(
        project_id=p4.id,
        version=1,
        total_client_price=999,
        total_internal_cost=500,
        updated_at=datetime(2025, 1, 5, 12, 0, tzinfo=UTC),
    )
    db_session.add_all([q1_v1, q1_v2, q2, q3, q4])
    await db_session.commit()

    tax = Tax(
        name="IVA",
        code=f"IVA_KPI_ENDPOINT_{uuid.uuid4().hex[:8]}",
        percentage=10,
        organization_id=kpi_org.id,
    )
    db_session.add(tax)
    await db_session.commit()
    await db_session.refresh(tax)
    await db_session.execute(insert(project_taxes).values(project_id=p1.id, tax_id=tax.id))
    await db_session.commit()


@pytest.mark.integration
class TestInsightsKpiSummaryEndpoint:
    async def test_custom_range_uses_latest_quote_excludes_draft(
        self,
        async_client: AsyncClient,
        kpi_user: User,
        kpi_seed_data,
    ):
        response = await async_client.get(
            "/api/v1/insights/dashboard/kpi-summary"
            "?range_mode=custom&start_date=2025-06-01&end_date=2025-06-30&timezone=UTC",
            headers=_auth_headers(kpi_user),
        )
        assert response.status_code == 200
        payload = response.json()

        assert payload["meta"]["latest_quote_only"] is True
        assert payload["meta"]["exclude_draft"] is True
        assert payload["meta"]["date_field"] == "quote.updated_at"
        assert payload["meta"]["range_mode"] == "custom"

        # P1 latest v2 = 200 + 10% tax => 220; P3 = 300. Draft/out-of-window excluded.
        assert payload["kpis"]["totalCotizadoConImpuestos"] == pytest.approx(520.0)
        assert payload["kpis"]["costoTotalOperacional"] == pytest.approx(200.0)
        assert payload["kpis"]["margenNetoTotal"] == pytest.approx(320.0)
        assert payload["kpis"]["numeroPropuestasRealizadas"] == 2
        assert payload["kpis"]["numeroPropuestasGanadas"] == 1
        assert payload["kpis"]["margenNetoTotal"] == pytest.approx(
            payload["kpis"]["totalCotizadoConImpuestos"] - payload["kpis"]["costoTotalOperacional"]
        )
        assert payload["currency"] == "USD"

    async def test_relative_range_requires_months_back(
        self,
        async_client: AsyncClient,
        kpi_user: User,
    ):
        response = await async_client.get(
            "/api/v1/insights/dashboard/kpi-summary?range_mode=relative",
            headers=_auth_headers(kpi_user),
        )
        assert response.status_code == 400

    async def test_custom_range_requires_dates(
        self,
        async_client: AsyncClient,
        kpi_user: User,
    ):
        response = await async_client.get(
            "/api/v1/insights/dashboard/kpi-summary?range_mode=custom",
            headers=_auth_headers(kpi_user),
        )
        assert response.status_code == 400

    async def test_custom_range_rejects_start_after_end(
        self,
        async_client: AsyncClient,
        kpi_user: User,
    ):
        response = await async_client.get(
            "/api/v1/insights/dashboard/kpi-summary"
            "?range_mode=custom&start_date=2025-07-01&end_date=2025-06-01",
            headers=_auth_headers(kpi_user),
        )
        assert response.status_code == 400

    async def test_rejects_invalid_timezone(
        self,
        async_client: AsyncClient,
        kpi_user: User,
    ):
        response = await async_client.get(
            "/api/v1/insights/dashboard/kpi-summary"
            "?range_mode=relative&months_back=3&timezone=Invalid/Zone",
            headers=_auth_headers(kpi_user),
        )
        assert response.status_code == 400

    async def test_custom_range_timezone_start_boundary_includes_local_midnight(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        kpi_org: Organization,
        kpi_user: User,
    ):
        """
        America/Bogota (UTC-5):
        local 2025-06-01 00:00:00 == 2025-06-01 05:00:00Z.
        Quote at 04:59:59Z must be excluded; at 05:00:00Z must be included.
        """
        project = Project(
            name="TZ Start Boundary",
            client_name="Boundary Client",
            organization_id=kpi_org.id,
            status="Sent",
            currency="USD",
        )
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        db_session.add_all(
            [
                Quote(
                    project_id=project.id,
                    version=1,
                    total_client_price=50,
                    total_internal_cost=10,
                    updated_at=datetime(2025, 6, 1, 4, 59, 59, tzinfo=UTC),
                ),
                Quote(
                    project_id=project.id,
                    version=2,  # latest; should be selected and included
                    total_client_price=120,
                    total_internal_cost=20,
                    updated_at=datetime(2025, 6, 1, 5, 0, 0, tzinfo=UTC),
                ),
            ]
        )
        await db_session.commit()

        response = await async_client.get(
            "/api/v1/insights/dashboard/kpi-summary"
            "?range_mode=custom&start_date=2025-06-01&end_date=2025-06-01&timezone=America/Bogota",
            headers=_auth_headers(kpi_user),
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["kpis"]["numeroPropuestasRealizadas"] == 1
        assert payload["kpis"]["totalCotizadoConImpuestos"] == pytest.approx(120.0)

    async def test_custom_range_timezone_end_boundary_excludes_next_local_day(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        kpi_org: Organization,
        kpi_user: User,
    ):
        """
        America/Bogota (UTC-5):
        local 2025-06-01 23:59:59 == 2025-06-02 04:59:59Z.
        Quote at 04:59:59Z must be included; at 05:00:00Z excluded.
        """
        project = Project(
            name="TZ End Boundary",
            client_name="Boundary Client 2",
            organization_id=kpi_org.id,
            status="Sent",
            currency="USD",
        )
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        db_session.add_all(
            [
                Quote(
                    project_id=project.id,
                    version=1,
                    total_client_price=200,
                    total_internal_cost=40,
                    updated_at=datetime(2025, 6, 2, 4, 59, 59, tzinfo=UTC),
                ),
                Quote(
                    project_id=project.id,
                    version=2,  # latest but outside local end boundary
                    total_client_price=999,
                    total_internal_cost=100,
                    updated_at=datetime(2025, 6, 2, 5, 0, 0, tzinfo=UTC),
                ),
            ]
        )
        await db_session.commit()

        response = await async_client.get(
            "/api/v1/insights/dashboard/kpi-summary"
            "?range_mode=custom&start_date=2025-06-01&end_date=2025-06-01&timezone=America/Bogota",
            headers=_auth_headers(kpi_user),
        )
        assert response.status_code == 200
        payload = response.json()

        # Latest quote is outside window, so project must be excluded entirely.
        assert payload["kpis"]["numeroPropuestasRealizadas"] == 0
        assert payload["kpis"]["totalCotizadoConImpuestos"] == pytest.approx(0.0)

    async def test_custom_range_timezone_dst_day_new_york_boundaries(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        kpi_org: Organization,
        kpi_user: User,
    ):
        """
        DST start in America/New_York on 2025-03-09 (23-hour local day).
        Local day boundaries map to:
        - start: 2025-03-09 00:00:00 local == 2025-03-09 05:00:00Z
        - end:   2025-03-09 23:59:59 local == 2025-03-10 03:59:59Z
        """
        projects = [
            Project(
                name="NY DST excluded before start",
                client_name="NY",
                organization_id=kpi_org.id,
                status="Sent",
                currency="USD",
            ),
            Project(
                name="NY DST included at start",
                client_name="NY",
                organization_id=kpi_org.id,
                status="Sent",
                currency="USD",
            ),
            Project(
                name="NY DST included at end",
                client_name="NY",
                organization_id=kpi_org.id,
                status="Sent",
                currency="USD",
            ),
            Project(
                name="NY DST excluded after end",
                client_name="NY",
                organization_id=kpi_org.id,
                status="Sent",
                currency="USD",
            ),
        ]
        db_session.add_all(projects)
        await db_session.commit()
        for project in projects:
            await db_session.refresh(project)

        db_session.add_all(
            [
                # Before local day start (excluded)
                Quote(
                    project_id=projects[0].id,
                    version=1,
                    total_client_price=10,
                    total_internal_cost=1,
                    updated_at=datetime(2025, 3, 9, 4, 59, 59, tzinfo=UTC),
                ),
                # Exactly at local day start (included)
                Quote(
                    project_id=projects[1].id,
                    version=1,
                    total_client_price=100,
                    total_internal_cost=20,
                    updated_at=datetime(2025, 3, 9, 5, 0, 0, tzinfo=UTC),
                ),
                # Exactly at local day end (included)
                Quote(
                    project_id=projects[2].id,
                    version=1,
                    total_client_price=200,
                    total_internal_cost=40,
                    updated_at=datetime(2025, 3, 10, 3, 59, 59, tzinfo=UTC),
                ),
                # First instant of next local day (excluded)
                Quote(
                    project_id=projects[3].id,
                    version=1,
                    total_client_price=300,
                    total_internal_cost=60,
                    updated_at=datetime(2025, 3, 10, 4, 0, 0, tzinfo=UTC),
                ),
            ]
        )
        await db_session.commit()

        response = await async_client.get(
            "/api/v1/insights/dashboard/kpi-summary"
            "?range_mode=custom&start_date=2025-03-09&end_date=2025-03-09&timezone=America/New_York",
            headers=_auth_headers(kpi_user),
        )
        assert response.status_code == 200
        payload = response.json()

        assert payload["kpis"]["numeroPropuestasRealizadas"] == 2
        assert payload["kpis"]["numeroPropuestasGanadas"] == 0
        assert payload["kpis"]["totalCotizadoConImpuestos"] == pytest.approx(300.0)
        assert payload["kpis"]["costoTotalOperacional"] == pytest.approx(60.0)
        assert payload["kpis"]["margenNetoTotal"] == pytest.approx(240.0)
