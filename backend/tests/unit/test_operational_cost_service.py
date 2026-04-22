"""
Unit tests for OperationalCostService.
Ensures each calculation block (resources, fixed costs, amortization, margin) and totals are correct.
"""

from datetime import date, datetime
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BusinessLogicError
from app.models.cost import CostFixed
from app.models.equipment import EquipmentAmortization
from app.models.organization import Organization
from app.models.project import Project, Quote
from app.models.service import Service
from app.models.tax import Tax
from app.models.team import TeamMember
from app.services.operational_cost_service import (
    _compute_amortization,
    _compute_fixed_costs,
    _compute_resource_costs,
    _compute_tax_costs,
    _get_social_charges_multiplier,
    _get_target_margin_configured,
    _to_decimal,
    get_current_month_operational_costs,
)


@pytest.mark.unit
class TestOperationalCostService:
    """Tests for operational cost calculation service."""

    async def test_to_decimal(self):
        assert _to_decimal(None) == Decimal("0")
        assert _to_decimal("1.5") == Decimal("1.5")
        assert _to_decimal(100) == Decimal("100")
        assert _to_decimal(Decimal("2.5")) == Decimal("2.5")

    async def test_social_charges_multiplier_no_config(
        self, db_session: AsyncSession, test_organization: Organization
    ):
        mult = await _get_social_charges_multiplier(db_session, test_organization.id)
        assert mult == Decimal("1.0")

    async def test_social_charges_multiplier_with_config(
        self, db_session: AsyncSession, test_organization: Organization
    ):
        test_organization.settings = {
            "social_charges_config": {
                "enable_social_charges": True,
                "total_percentage": 30,
            }
        }
        db_session.add(test_organization)
        await db_session.commit()
        await db_session.refresh(test_organization)
        mult = await _get_social_charges_multiplier(db_session, test_organization.id)
        assert mult == Decimal("1.3")

    async def test_compute_resource_costs_empty(
        self, db_session: AsyncSession, test_organization: Organization
    ):
        total = await _compute_resource_costs(db_session, test_organization.id, "USD", "test-id")
        assert total == Decimal("0")

    async def test_compute_resource_costs_one_member(self, db_session: AsyncSession):
        """One member, no social charges: total must be exactly salary (5000). Uses isolated org to avoid test order."""
        import uuid

        slug = f"opcost-res-{uuid.uuid4().hex[:8]}"
        org = Organization(
            name="OpCost Resource Test Org",
            slug=slug,
            subscription_plan="free",
            subscription_status="active",
            settings=None,
        )
        db_session.add(org)
        await db_session.flush()
        member = TeamMember(
            name="Dev",
            role="Developer",
            salary_monthly_brute=Decimal("5000"),
            currency="USD",
            billable_hours_per_week=40,
            is_active=True,
            organization_id=org.id,
        )
        db_session.add(member)
        await db_session.commit()
        total = await _compute_resource_costs(db_session, org.id, "USD", "test-id")
        assert total > 0
        assert total == Decimal("5000")

    async def test_compute_fixed_costs_empty(
        self, db_session: AsyncSession, test_organization: Organization
    ):
        total = await _compute_fixed_costs(db_session, test_organization.id, "USD", "test-id")
        assert total == Decimal("0")

    async def test_compute_fixed_costs_one(
        self, db_session: AsyncSession, test_organization: Organization
    ):
        cost = CostFixed(
            name="Rent",
            amount_monthly=Decimal("1000"),
            currency="USD",
            category="Overhead",
            organization_id=test_organization.id,
        )
        db_session.add(cost)
        await db_session.commit()
        total = await _compute_fixed_costs(db_session, test_organization.id, "USD", "test-id")
        assert total == Decimal("1000")

    async def test_compute_amortization_empty(
        self, db_session: AsyncSession, test_organization: Organization
    ):
        total, ok = await _compute_amortization(db_session, test_organization.id, "USD", "test-id")
        assert total == Decimal("0")
        assert ok is True

    async def test_compute_amortization_one_asset(
        self, db_session: AsyncSession, test_organization: Organization
    ):
        from datetime import date as date_type

        asset = EquipmentAmortization(
            name="Laptop",
            category="Hardware",
            purchase_price=Decimal("1200"),
            purchase_date=date_type(2024, 1, 1),
            currency="USD",
            useful_life_months=36,
            salvage_value=Decimal("0"),
            depreciation_method="straight_line",
            is_active=True,
            organization_id=test_organization.id,
        )
        db_session.add(asset)
        await db_session.commit()
        total, ok = await _compute_amortization(db_session, test_organization.id, "USD", "test-id")
        # 1200 / 36 = 33.333...
        assert total > 0
        assert total.quantize(Decimal("0.01")) == Decimal("33.33")
        assert ok is True

    async def test_get_target_margin_from_services(
        self, db_session: AsyncSession, test_organization: Organization
    ):
        svc = Service(
            name="Consulting",
            default_margin_target=Decimal("0.40"),
            is_active=True,
            organization_id=test_organization.id,
        )
        db_session.add(svc)
        await db_session.commit()
        margin = await _get_target_margin_configured(db_session, test_organization.id, "test-id")
        assert margin is not None
        assert margin == Decimal("0.4")

    async def test_full_payload_totals(
        self,
        db_session: AsyncSession,
        test_organization: Organization,
        test_team_member: TeamMember,
        test_cost: CostFixed,
    ):
        payload = await get_current_month_operational_costs(
            db_session,
            test_organization.id,
            primary_currency="USD",
        )
        assert payload.total_operational_cost >= 0
        expected = (
            payload.resource_costs + payload.fixed_costs + payload.amortization + payload.tax_costs
        )
        assert payload.total_operational_cost == expected
        assert payload.calculation_metadata.currency == "USD"
        assert payload.calculation_metadata.formula_version == "1.0"
        assert payload.calculation_metadata.calculation_id is not None
        assert payload.calculation_metadata.period_start <= payload.calculation_metadata.period_end

    async def test_compute_tax_costs_empty_period_returns_zero(
        self, db_session: AsyncSession, test_organization: Organization
    ):
        total = await _compute_tax_costs(
            db_session,
            test_organization.id,
            "USD",
            "test-id",
            period_start=date(2024, 1, 1),
            period_end=date(2024, 1, 31),
            operational_subtotal=Decimal("0"),
        )
        assert total == Decimal("0.0000")

    async def test_compute_tax_costs_from_won_project(
        self, db_session: AsyncSession, test_organization: Organization
    ):
        tax = Tax(
            name="IVA",
            code=f"IVA_{test_organization.id}_{datetime.utcnow().timestamp()}",
            percentage=Decimal("19"),
            is_active=True,
            organization_id=test_organization.id,
        )
        project = Project(
            name="Tax project",
            client_name="Client",
            status="Won",
            currency="USD",
            organization_id=test_organization.id,
        )
        quote = Quote(
            project=project,
            version=1,
            total_internal_cost=Decimal("100"),
            total_client_price=Decimal("200"),
            updated_at=datetime.utcnow(),
        )
        project.taxes.append(tax)
        db_session.add_all([tax, project, quote])
        await db_session.commit()

        total = await _compute_tax_costs(
            db_session,
            test_organization.id,
            "USD",
            "test-id",
            period_start=date.today().replace(day=1),
            period_end=date.today(),
            operational_subtotal=Decimal("200"),
        )
        # 19% of 200 = 38
        assert total.quantize(Decimal("0.01")) == Decimal("38.00")

    async def test_compute_tax_costs_negative_tax_invalid(
        self, db_session: AsyncSession, test_organization: Organization
    ):
        tax = Tax(
            name="Invalid Tax",
            code=f"INV_TAX_{test_organization.id}_{datetime.utcnow().timestamp()}",
            percentage=Decimal("-5"),
            is_active=True,
            organization_id=test_organization.id,
        )
        project = Project(
            name="Tax invalid project",
            client_name="Client",
            status="Won",
            currency="USD",
            organization_id=test_organization.id,
        )
        quote = Quote(
            project=project,
            version=1,
            total_internal_cost=Decimal("100"),
            total_client_price=Decimal("100"),
            updated_at=datetime.utcnow(),
        )
        project.taxes.append(tax)
        db_session.add_all([tax, project, quote])
        await db_session.commit()

        with pytest.raises(BusinessLogicError):
            await _compute_tax_costs(
                db_session,
                test_organization.id,
                "USD",
                "test-id",
                period_start=date.today().replace(day=1),
                period_end=date.today(),
                operational_subtotal=Decimal("100"),
            )

    async def test_compute_tax_costs_from_configured_active_taxes_when_no_won_quotes(
        self, db_session: AsyncSession
    ):
        import uuid

        org = Organization(
            name="OpCost Tax Config Org",
            slug=f"opcost-tax-config-{uuid.uuid4().hex[:8]}",
            subscription_plan="free",
            subscription_status="active",
        )
        db_session.add(org)
        await db_session.flush()

        tax = Tax(
            name="IVA Config",
            code=f"IVA_CFG_{org.id}_{datetime.utcnow().timestamp()}",
            percentage=Decimal("19"),
            is_active=True,
            organization_id=org.id,
        )
        db_session.add(tax)
        await db_session.commit()

        total = await _compute_tax_costs(
            db_session,
            org.id,
            "USD",
            "test-id",
            period_start=date.today().replace(day=1),
            period_end=date.today(),
            operational_subtotal=Decimal("1000"),
        )
        assert total.quantize(Decimal("0.01")) == Decimal("190.00")

    async def test_compute_amortization_fallback_from_onboarding_inventory_settings(
        self, db_session: AsyncSession, test_organization: Organization
    ):
        test_organization.settings = {
            "onboarding_inventory_items": [
                {
                    "name": "Laptop legacy",
                    "category": "hardware",
                    "amount_monthly": "1200",
                    "currency": "USD",
                    "amortizable": True,
                }
            ]
        }
        db_session.add(test_organization)
        await db_session.commit()
        await db_session.refresh(test_organization)

        total, ok = await _compute_amortization(
            db_session,
            test_organization.id,
            "USD",
            "test-id",
        )
        # hardware => 36 months => 1200/36 = 33.33...
        assert total.quantize(Decimal("0.01")) == Decimal("33.33")
        assert ok is True
