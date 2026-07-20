"""
Unit tests for business-health analytics: monthly operating cost, committed
revenue, break-even and resource utilization.
"""

import uuid
from datetime import UTC, date, datetime

import pytest

from app.core.business_health import (
    calculate_break_even,
    calculate_committed_monthly_revenue,
    calculate_monthly_operating_cost,
    calculate_resource_utilization,
)
from app.models.cost import CostFixed
from app.models.equipment import EquipmentAmortization
from app.models.organization import Organization
from app.models.project import Project, Quote, QuoteItem, QuoteItemAllocation
from app.models.service import Service
from app.models.team import TeamMember

CAPACITY = 40 * 4.33  # billable=40 -> 173.2h/month


@pytest.fixture
async def org(db_session):
    o = Organization(
        name="T",
        slug=f"org-{uuid.uuid4().hex[:8]}",
        subscription_plan="free",
        subscription_status="active",
    )
    db_session.add(o)
    await db_session.commit()
    await db_session.refresh(o)
    return o


async def _member(db, org_id, salary=5000, billable=40, currency="USD", non_billable=0.0):
    m = TeamMember(
        name="m",
        role="Dev",
        salary_monthly_brute=salary,
        currency=currency,
        billable_hours_per_week=billable,
        non_billable_hours_percentage=non_billable,
        is_active=True,
        organization_id=org_id,
    )
    db.add(m)
    await db.commit()
    await db.refresh(m)
    return m


async def _service(db, org_id):
    s = Service(name="S", pricing_type="hourly", is_active=True, organization_id=org_id)
    db.add(s)
    await db.commit()
    await db.refresh(s)
    return s


async def _won(db, org_id, service_id, items, status="Won", set_accepted=True, allocs=None):
    project = Project(
        name="P", client_name="C", status=status, organization_id=org_id, currency="USD"
    )
    db.add(project)
    await db.flush()
    quote = Quote(project_id=project.id, version=1)
    db.add(quote)
    await db.flush()
    created_items = []
    for it in items:
        qi = QuoteItem(quote_id=quote.id, service_id=service_id, **it)
        db.add(qi)
        created_items.append(qi)
    await db.flush()
    for idx, alloc in allocs or []:
        db.add(QuoteItemAllocation(quote_item_id=created_items[idx].id, **alloc))
    if set_accepted:
        project.accepted_quote_id = quote.id
    await db.commit()
    return project


@pytest.mark.unit
class TestOperatingCost:
    async def test_fixed_costs(self, db_session, org):
        db_session.add(
            CostFixed(
                name="rent",
                amount_monthly=1000,
                currency="USD",
                category="Overhead",
                organization_id=org.id,
            )
        )
        await db_session.commit()
        res = await calculate_monthly_operating_cost(db_session, "USD", org.id)
        assert float(res["total_fixed"]) == pytest.approx(1000.0)

    async def test_payroll_and_hours(self, db_session, org):
        await _member(db_session, org.id, salary=5000, billable=40)
        res = await calculate_monthly_operating_cost(db_session, "USD", org.id)
        assert float(res["total_payroll"]) == pytest.approx(5000.0)
        assert float(res["billable_hours"]) == pytest.approx(CAPACITY)

    async def test_equipment_amortization(self, db_session, org):
        db_session.add(
            EquipmentAmortization(
                name="laptop",
                category="Hardware",
                purchase_price=1200,
                purchase_date=date(2026, 1, 1),
                currency="USD",
                useful_life_months=12,
                salvage_value=0,
                depreciation_method="straight_line",
                is_active=True,
                organization_id=org.id,
            )
        )
        await db_session.commit()
        res = await calculate_monthly_operating_cost(db_session, "USD", org.id)
        assert float(res["total_equipment"]) == pytest.approx(100.0)  # 1200/12

    async def test_social_charges_applied(self, db_session, org):
        org.settings = {
            "social_charges_config": {"enable_social_charges": True, "total_percentage": 30}
        }
        db_session.add(org)
        await db_session.commit()
        await _member(db_session, org.id, salary=1000)
        res = await calculate_monthly_operating_cost(db_session, "USD", org.id)
        assert float(res["total_payroll"]) == pytest.approx(1300.0)

    async def test_zero_state(self, db_session, org):
        res = await calculate_monthly_operating_cost(db_session, "USD", org.id)
        assert float(res["total_monthly_cost"]) == 0.0
        assert float(res["billable_hours"]) == 0.0


@pytest.mark.unit
class TestCommittedRevenue:
    async def test_recurring_mrr(self, db_session, org):
        svc = await _service(db_session, org.id)
        await _won(
            db_session,
            org.id,
            svc.id,
            [
                {
                    "pricing_type": "recurring",
                    "recurring_price": 500,
                    "quantity": 1,
                    "billing_frequency": "monthly",
                    "client_price": 500,
                },
            ],
        )
        res = await calculate_committed_monthly_revenue(db_session, org.id, "USD")
        assert float(res["mrr"]) == pytest.approx(500.0)
        assert float(res["committed_monthly_revenue"]) == pytest.approx(500.0)

    async def test_annual_normalized(self, db_session, org):
        svc = await _service(db_session, org.id)
        await _won(
            db_session,
            org.id,
            svc.id,
            [
                {
                    "pricing_type": "recurring",
                    "recurring_price": 1200,
                    "quantity": 1,
                    "billing_frequency": "annual",
                    "client_price": 1200,
                },
            ],
        )
        res = await calculate_committed_monthly_revenue(db_session, org.id, "USD")
        assert float(res["mrr"]) == pytest.approx(100.0)

    async def test_one_time_prorated(self, db_session, org):
        svc = await _service(db_session, org.id)
        await _won(
            db_session,
            org.id,
            svc.id,
            [{"pricing_type": "fixed", "client_price": 1200, "quantity": 1}],
        )
        res = await calculate_committed_monthly_revenue(
            db_session, org.id, "USD", one_time_proration_months=12
        )
        assert float(res["one_time_monthly"]) == pytest.approx(100.0)

    async def test_ignores_non_won(self, db_session, org):
        svc = await _service(db_session, org.id)
        await _won(
            db_session,
            org.id,
            svc.id,
            [
                {
                    "pricing_type": "recurring",
                    "recurring_price": 500,
                    "quantity": 1,
                    "billing_frequency": "monthly",
                    "client_price": 500,
                },
            ],
            status="Sent",
            set_accepted=False,
        )
        res = await calculate_committed_monthly_revenue(db_session, org.id, "USD")
        assert float(res["committed_monthly_revenue"]) == pytest.approx(0.0)

    async def test_empty(self, db_session, org):
        res = await calculate_committed_monthly_revenue(db_session, org.id, "USD")
        assert float(res["committed_monthly_revenue"]) == 0.0


@pytest.mark.unit
class TestBreakEven:
    async def test_deficit(self, db_session, org):
        db_session.add(
            CostFixed(
                name="rent",
                amount_monthly=5000,
                currency="USD",
                category="Overhead",
                organization_id=org.id,
            )
        )
        await db_session.commit()
        res = await calculate_break_even(db_session, org.id, "USD")
        assert res["status"] == "deficit"
        assert res["surplus_or_deficit"] == pytest.approx(-5000.0)

    async def test_surplus(self, db_session, org):
        db_session.add(
            CostFixed(
                name="rent",
                amount_monthly=1000,
                currency="USD",
                category="Overhead",
                organization_id=org.id,
            )
        )
        await db_session.commit()
        svc = await _service(db_session, org.id)
        await _won(
            db_session,
            org.id,
            svc.id,
            [
                {
                    "pricing_type": "recurring",
                    "recurring_price": 3000,
                    "quantity": 1,
                    "billing_frequency": "monthly",
                    "client_price": 3000,
                },
            ],
        )
        res = await calculate_break_even(db_session, org.id, "USD")
        assert res["status"] == "profit"
        assert res["surplus_or_deficit"] == pytest.approx(2000.0)
        assert res["coverage_percentage"] == pytest.approx(3.0)

    async def test_rate_per_hour(self, db_session, org):
        await _member(db_session, org.id, salary=5000, billable=40)
        res = await calculate_break_even(db_session, org.id, "USD")
        assert res["break_even_rate_per_hour"] == pytest.approx(5000 / CAPACITY, rel=1e-3)

    async def test_zero_cost_guard(self, db_session, org):
        res = await calculate_break_even(db_session, org.id, "USD")
        assert res["break_even_cost"] == 0.0
        assert res["coverage_percentage"] == 0.0
        assert res["break_even_rate_per_hour"] == 0.0


@pytest.mark.unit
class TestResourceUtilization:
    async def test_multiple_projects(self, db_session, org):
        m = await _member(db_session, org.id)
        svc = await _service(db_session, org.id)
        await _won(
            db_session,
            org.id,
            svc.id,
            [{"pricing_type": "hourly"}],
            allocs=[(0, {"team_member_id": m.id, "hours": 50})],
        )
        await _won(
            db_session,
            org.id,
            svc.id,
            [{"pricing_type": "hourly"}],
            allocs=[(0, {"team_member_id": m.id, "hours": 50})],
        )
        res = await calculate_resource_utilization(db_session, org.id)
        member = next(x for x in res["members"] if x["team_member_id"] == m.id)
        assert member["allocated_hours"] == pytest.approx(100.0)

    async def test_over_allocation(self, db_session, org):
        m = await _member(db_session, org.id)
        svc = await _service(db_session, org.id)
        await _won(
            db_session,
            org.id,
            svc.id,
            [{"pricing_type": "hourly"}],
            allocs=[(0, {"team_member_id": m.id, "hours": 200})],
        )
        res = await calculate_resource_utilization(db_session, org.id)
        assert res["members"][0]["over_allocated"] is True
        assert res["members"][0]["utilization_percentage"] > 100

    async def test_excludes_non_won(self, db_session, org):
        m = await _member(db_session, org.id)
        svc = await _service(db_session, org.id)
        await _won(
            db_session,
            org.id,
            svc.id,
            [{"pricing_type": "hourly"}],
            status="Sent",
            set_accepted=False,
            allocs=[(0, {"team_member_id": m.id, "hours": 50})],
        )
        res = await calculate_resource_utilization(db_session, org.id)
        assert res["members"][0]["allocated_hours"] == pytest.approx(0.0)

    async def test_date_window(self, db_session, org):
        m = await _member(db_session, org.id)
        svc = await _service(db_session, org.id)
        await _won(
            db_session,
            org.id,
            svc.id,
            [{"pricing_type": "hourly"}],
            allocs=[
                (
                    0,
                    {
                        "team_member_id": m.id,
                        "hours": 50,
                        "start_date": datetime(2026, 1, 1, tzinfo=UTC),
                        "end_date": datetime(2026, 1, 31, tzinfo=UTC),
                    },
                )
            ],
        )
        res = await calculate_resource_utilization(
            db_session,
            org.id,
            start=datetime(2026, 3, 1, tzinfo=UTC),
            end=datetime(2026, 3, 31, tzinfo=UTC),
        )
        assert res["members"][0]["allocated_hours"] == pytest.approx(0.0)

    async def test_empty(self, db_session, org):
        await _member(db_session, org.id)
        res = await calculate_resource_utilization(db_session, org.id)
        assert res["total_allocated_hours"] == 0.0
