"""
Unit tests for template service
"""

import pytest

from app.models.template import IndustryTemplate
from app.services.template_service import apply_industry_template, get_region_multiplier


@pytest.mark.unit
class TestTemplateService:
    """Tests for template service"""

    def test_get_region_multiplier_us(self):
        """Test region multiplier for US"""
        assert get_region_multiplier("US") == 1.0
        assert get_region_multiplier("us") == 1.0  # Case insensitive

    def test_get_region_multiplier_colombia(self):
        """Test region multiplier for Colombia"""
        assert get_region_multiplier("COL") == 0.25
        assert get_region_multiplier("col") == 0.25

    def test_get_region_multiplier_argentina(self):
        """Test region multiplier for Argentina"""
        assert get_region_multiplier("ARG") == 0.15

    def test_get_region_multiplier_default(self):
        """Test region multiplier for unknown region"""
        assert get_region_multiplier("UNKNOWN") == 0.5  # Default
        assert get_region_multiplier("XX") == 0.5

    def test_get_region_multiplier_all_regions(self):
        """Test all known region multipliers"""
        assert get_region_multiplier("US") == 1.0
        assert get_region_multiplier("UK") == 0.85
        assert get_region_multiplier("COL") == 0.25
        assert get_region_multiplier("ARG") == 0.15
        assert get_region_multiplier("MEX") == 0.30
        assert get_region_multiplier("ESP") == 0.70
        assert get_region_multiplier("BR") == 0.20

    async def test_apply_industry_template_not_found(self, db_session, test_organization):
        """Test applying non-existent template"""
        with pytest.raises(ValueError, match="not found"):
            await apply_industry_template(
                test_organization.id,
                "non_existent_template",
                region="US",
                currency="USD",
                db=db_session,
            )

    async def test_apply_industry_template_organization_not_found(self, db_session):
        """Test applying template to non-existent organization"""
        # Create a template first
        template = IndustryTemplate(
            industry_type="test_industry",
            name="Test Template",
            is_active=True,
            suggested_roles=[],
            suggested_services=[],
            suggested_fixed_costs=[],
        )
        db_session.add(template)
        await db_session.commit()

        with pytest.raises(ValueError, match="Organization.*not found"):
            await apply_industry_template(
                99999,  # Non-existent org
                "test_industry",
                region="US",
                currency="USD",
                db=db_session,
            )

    async def test_apply_industry_template_missing_db(self, test_organization):
        """Test applying template without database session"""
        with pytest.raises(ValueError, match="Database session is required"):
            await apply_industry_template(
                test_organization.id, "test_industry", region="US", currency="USD", db=None
            )
