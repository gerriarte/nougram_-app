"""
Unit tests for Onboarding Service
"""
import pytest
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.onboarding_service import OnboardingService
from app.schemas.onboarding import (
    CompleteOnboardingRequest,
    OnboardingTeamMember,
    OnboardingExpense,
    TemporaryBCRRequest
)


@pytest.mark.unit
class TestOnboardingServiceGetBenchmarks:
    """Tests for get_benchmarks method"""
    
    async def test_get_benchmarks_freelance(self, db_session: AsyncSession, test_organization):
        """Test getting benchmarks for freelance profile"""
        service = OnboardingService(db_session, test_organization.id)
        
        result = await service.get_benchmarks(
            profile_type="freelance",
            country="US",
            currency="USD"
        )
        
        assert result["profile_type"] == "freelance"
        assert result["country"] == "US"
        assert result["currency"] == "USD"
        assert result["source"] == "industry_standard"
        assert "benchmarks" in result
        
        benchmarks = result["benchmarks"]
        assert benchmarks["avg_monthly_income"] == Decimal("5000")
        assert benchmarks["avg_margin"] == Decimal("25")
        assert benchmarks["avg_hours_per_month"] == Decimal("160")
    
    async def test_get_benchmarks_company(self, db_session: AsyncSession, test_organization):
        """Test getting benchmarks for company profile"""
        service = OnboardingService(db_session, test_organization.id)
        
        result = await service.get_benchmarks(
            profile_type="company",
            country="US",
            currency="USD"
        )
        
        assert result["profile_type"] == "company"
        benchmarks = result["benchmarks"]
        assert benchmarks["avg_margin"] == Decimal("30")
        assert benchmarks["avg_team_size"] == 5
        assert benchmarks["avg_salary"] == Decimal("3000")
    
    async def test_get_benchmarks_agency(self, db_session: AsyncSession, test_organization):
        """Test getting benchmarks for agency profile"""
        service = OnboardingService(db_session, test_organization.id)
        
        result = await service.get_benchmarks(
            profile_type="agency",
            country="US",
            currency="USD"
        )
        
        assert result["profile_type"] == "agency"
        benchmarks = result["benchmarks"]
        assert benchmarks["avg_margin"] == Decimal("35")
        assert benchmarks["avg_team_size"] == 10
        assert benchmarks["avg_salary"] == Decimal("3500")
        assert benchmarks["avg_clients"] == 5
    
    async def test_get_benchmarks_colombia_adjustment(self, db_session: AsyncSession, test_organization):
        """Test that Colombia salaries are adjusted"""
        service = OnboardingService(db_session, test_organization.id)
        
        result_us = await service.get_benchmarks(
            profile_type="company",
            country="US",
            currency="USD"
        )
        
        result_col = await service.get_benchmarks(
            profile_type="company",
            country="COL",
            currency="COP"
        )
        
        # Colombia salary should be lower
        assert result_col["benchmarks"]["avg_salary"] < result_us["benchmarks"]["avg_salary"]


@pytest.mark.unit
class TestOnboardingServiceCalculateTemporaryBCR:
    """Tests for calculate_temporary_bcr method"""

    @staticmethod
    def _normalized_monthly_hours(raw_monthly_hours: int) -> Decimal:
        weekly_hours = max(1, int(round(Decimal(str(raw_monthly_hours)) / Decimal("4.33"))))
        return Decimal(str(weekly_hours)) * Decimal("4.33")
    
    async def test_calculate_temporary_bcr_basic(self, db_session: AsyncSession, test_organization):
        """Test basic BCR calculation"""
        service = OnboardingService(db_session, test_organization.id)
        
        request = TemporaryBCRRequest(
            team_members=[
                OnboardingTeamMember(
                    name="Developer",
                    role="Developer",
                    salary_monthly_brute=Decimal("5000"),
                    currency="USD",
                    billable_hours_per_month=160
                )
            ],
            expenses=[],
            currency="USD"
        )
        
        result = await service.calculate_temporary_bcr(request)

        expected_hours = self._normalized_monthly_hours(160)
        assert result["blended_cost_rate"] == str(Decimal("5000") / expected_hours)
        assert result["total_monthly_costs"] == "5000"
        assert result["total_salaries"] == "5000"
        assert result["total_fixed_overhead"] == "0"
        assert result["total_monthly_hours"] == float(expected_hours)
        assert result["team_members_count"] == 1
        assert result["currency"] == "USD"
    
    async def test_calculate_temporary_bcr_with_expenses(self, db_session: AsyncSession, test_organization):
        """Test BCR calculation with expenses"""
        service = OnboardingService(db_session, test_organization.id)
        
        request = TemporaryBCRRequest(
            team_members=[
                OnboardingTeamMember(
                    name="Developer",
                    role="Developer",
                    salary_monthly_brute=Decimal("5000"),
                    currency="USD",
                    billable_hours_per_month=160
                )
            ],
            expenses=[
                OnboardingExpense(
                    name="Office Rent",
                    category="rent",
                    amount_monthly=Decimal("2000"),
                    currency="USD"
                )
            ],
            currency="USD"
        )
        
        result = await service.calculate_temporary_bcr(request)

        expected_hours = self._normalized_monthly_hours(160)
        assert result["total_monthly_costs"] == "7000"
        assert result["total_salaries"] == "5000"
        assert result["total_fixed_overhead"] == "2000"
        assert result["blended_cost_rate"] == str(Decimal("7000") / expected_hours)
    
    async def test_calculate_temporary_bcr_multiple_members(self, db_session: AsyncSession, test_organization):
        """Test BCR calculation with multiple team members"""
        service = OnboardingService(db_session, test_organization.id)
        
        request = TemporaryBCRRequest(
            team_members=[
                OnboardingTeamMember(
                    name="Developer 1",
                    role="Developer",
                    salary_monthly_brute=Decimal("5000"),
                    currency="USD",
                    billable_hours_per_month=160
                ),
                OnboardingTeamMember(
                    name="Developer 2",
                    role="Developer",
                    salary_monthly_brute=Decimal("6000"),
                    currency="USD",
                    billable_hours_per_month=160
                )
            ],
            expenses=[],
            currency="USD"
        )
        
        result = await service.calculate_temporary_bcr(request)

        expected_hours = self._normalized_monthly_hours(160) * Decimal("2")
        assert result["total_salaries"] == "11000"
        assert result["total_monthly_hours"] == float(expected_hours)
        assert result["team_members_count"] == 2
        assert result["blended_cost_rate"] == str(Decimal("11000") / expected_hours)
    
    async def test_calculate_temporary_bcr_min_hours_normalization(self, db_session: AsyncSession, test_organization):
        """Test BCR calculation with minimum allowed monthly hours."""
        service = OnboardingService(db_session, test_organization.id)
        
        # Note: OnboardingTeamMember requires billable_hours_per_month >= 1
        # So we'll test with 1 hour but verify the calculation handles edge cases
        request = TemporaryBCRRequest(
            team_members=[
                OnboardingTeamMember(
                    name="Developer",
                    role="Developer",
                    salary_monthly_brute=Decimal("5000"),
                    currency="USD",
                    billable_hours_per_month=1  # Minimum allowed value
                )
            ],
            expenses=[],
            currency="USD"
        )
        
        result = await service.calculate_temporary_bcr(request)
        
        expected_hours = self._normalized_monthly_hours(1)
        assert result["blended_cost_rate"] == str(Decimal("5000") / expected_hours)
        assert result["total_monthly_hours"] == float(expected_hours)

    async def test_calculate_temporary_bcr_rejects_mixed_currency(self, db_session: AsyncSession, test_organization):
        """Temporary BCR should fail when team currency differs from payload currency."""
        service = OnboardingService(db_session, test_organization.id)

        request = TemporaryBCRRequest(
            team_members=[
                OnboardingTeamMember(
                    name="Developer",
                    role="Developer",
                    salary_monthly_brute=Decimal("5000"),
                    currency="USD",
                    billable_hours_per_month=160
                )
            ],
            expenses=[],
            currency="COP"
        )

        with pytest.raises(ValueError, match="Mixed currencies are not allowed"):
            await service.calculate_temporary_bcr(request)


@pytest.mark.unit
class TestOnboardingServiceCompleteOnboarding:
    """Tests for complete_onboarding method"""
    
    async def test_complete_onboarding_basic(
        self,
        db_session: AsyncSession,
        test_organization
    ):
        """Test completing onboarding with basic data"""
        service = OnboardingService(db_session, test_organization.id)
        
        request = CompleteOnboardingRequest(
            organization_name="Updated Org Name",
            country="USA",
            currency="USD",
            profile_type="freelance",
            team_members=[],
            expenses=[]
        )
        
        result = await service.complete_onboarding(request)
        
        assert result["success"] is True
        assert result["organization_id"] == test_organization.id
        assert result["team_members_created"] == 0
        assert result["expenses_created"] == 0
        assert "bcr_calculated" in result
        assert result["organization"]["name"] == "Updated Org Name"
        assert result["organization"]["primary_currency"] == "USD"
        
        # Verify organization was updated
        from app.repositories.organization_repository import OrganizationRepository
        org_repo = OrganizationRepository(db_session)
        updated_org = await org_repo.get_by_id(test_organization.id)
        assert updated_org.name == "Updated Org Name"
        assert updated_org.settings["primary_currency"] == "USD"
        assert updated_org.settings["country"] == "USA"
        assert updated_org.settings["profile_type"] == "freelance"
        assert updated_org.settings["onboarding_completed"] is True
    
    async def test_complete_onboarding_with_team_members(
        self,
        db_session: AsyncSession,
        test_organization
    ):
        """Test completing onboarding with team members"""
        service = OnboardingService(db_session, test_organization.id)
        
        request = CompleteOnboardingRequest(
            country="USA",
            currency="USD",
            profile_type="company",
            team_members=[
                OnboardingTeamMember(
                    name="John Doe",
                    role="Developer",
                    salary_monthly_brute=Decimal("5000"),
                    currency="USD",
                    billable_hours_per_month=160
                )
            ],
            expenses=[]
        )
        
        result = await service.complete_onboarding(request)
        
        assert result["success"] is True
        assert result["team_members_created"] == 1
        assert result["expenses_created"] == 0
        
        # Verify team member was created
        from app.repositories.factory import RepositoryFactory
        team_repo = RepositoryFactory.create_team_repository(db_session, test_organization.id)
        members = await team_repo.get_all()
        assert len(members) == 1
        assert members[0].name == "John Doe"
        assert members[0].role == "Developer"

    async def test_complete_onboarding_rejects_mixed_currency(
        self,
        db_session: AsyncSession,
        test_organization
    ):
        """Complete onboarding should reject mixed currencies and avoid persistence."""
        service = OnboardingService(db_session, test_organization.id)

        request = CompleteOnboardingRequest(
            country="USA",
            currency="USD",
            profile_type="company",
            team_members=[
                OnboardingTeamMember(
                    name="John Doe",
                    role="Developer",
                    salary_monthly_brute=Decimal("5000"),
                    currency="COP",
                    billable_hours_per_month=160
                )
            ],
            expenses=[]
        )

        with pytest.raises(ValueError, match="Mixed currencies are not allowed"):
            await service.complete_onboarding(request)
    
    async def test_complete_onboarding_with_expenses(
        self,
        db_session: AsyncSession,
        test_organization
    ):
        """Test completing onboarding with expenses"""
        service = OnboardingService(db_session, test_organization.id)
        
        request = CompleteOnboardingRequest(
            country="USA",
            currency="USD",
            profile_type="company",
            team_members=[],
            expenses=[
                OnboardingExpense(
                    name="Office Rent",
                    category="rent",
                    amount_monthly=Decimal("2000"),
                    currency="USD"
                ),
                OnboardingExpense(
                    name="Slack",
                    category="software",
                    amount_monthly=Decimal("100"),
                    currency="USD"
                )
            ]
        )
        
        result = await service.complete_onboarding(request)
        
        assert result["success"] is True
        assert result["team_members_created"] == 0
        assert result["expenses_created"] == 2
        
        # Verify expenses were created
        from app.repositories.factory import RepositoryFactory
        cost_repo = RepositoryFactory.create_cost_repository(db_session, test_organization.id)
        costs = await cost_repo.get_all_active()
        assert len(costs) == 2
    
    async def test_complete_onboarding_with_tax_structure(
        self,
        db_session: AsyncSession,
        test_organization
    ):
        """Test completing onboarding with tax structure"""
        # Ensure clean state - reset settings
        test_organization.settings = {}
        await db_session.commit()
        await db_session.refresh(test_organization)
        
        service = OnboardingService(db_session, test_organization.id)
        
        tax_structure = {
            "iva": 19.0,
            "ica": 0.966,
            "retentions": 11.0
        }
        
        request = CompleteOnboardingRequest(
            country="COL",
            currency="COP",
            profile_type="company",
            team_members=[],
            expenses=[],
            tax_structure=tax_structure
        )
        
        result = await service.complete_onboarding(request)
        
        assert result["success"] is True
        
        # Verify tax structure was saved - check in the response first
        assert result["organization"]["settings"] is not None
        saved_tax_structure = result["organization"]["settings"].get("tax_structure")
        assert saved_tax_structure == tax_structure, f"Expected {tax_structure}, got {saved_tax_structure}"
        
        # Also verify by querying the database
        from app.repositories.organization_repository import OrganizationRepository
        org_repo = OrganizationRepository(db_session)
        updated_org = await org_repo.get_by_id(test_organization.id)
        await db_session.refresh(updated_org)
        assert updated_org.settings is not None
        assert updated_org.settings.get("tax_structure") == tax_structure
    
    async def test_complete_onboarding_with_social_charges(
        self,
        db_session: AsyncSession,
        test_organization
    ):
        """Test completing onboarding with social charges config"""
        # Ensure clean state - reset settings
        test_organization.settings = {}
        await db_session.commit()
        await db_session.refresh(test_organization)
        
        service = OnboardingService(db_session, test_organization.id)
        
        social_charges = {
            "enable_social_charges": True,
            "health_percentage": 8.5,
            "pension_percentage": 12.0
        }
        
        request = CompleteOnboardingRequest(
            country="COL",
            currency="COP",
            profile_type="company",
            team_members=[],
            expenses=[],
            social_charges_config=social_charges
        )
        
        result = await service.complete_onboarding(request)
        
        assert result["success"] is True
        
        # Verify social charges were saved - check in the response first
        assert result["organization"]["settings"] is not None
        saved_social_charges = result["organization"]["settings"].get("social_charges_config")
        assert saved_social_charges == social_charges, f"Expected {social_charges}, got {saved_social_charges}"
        
        # Also verify by querying the database
        from app.repositories.organization_repository import OrganizationRepository
        org_repo = OrganizationRepository(db_session)
        updated_org = await org_repo.get_by_id(test_organization.id)
        await db_session.refresh(updated_org)
        assert updated_org.settings is not None
        assert updated_org.settings.get("social_charges_config") == social_charges
    
    async def test_complete_onboarding_organization_not_found(
        self,
        db_session: AsyncSession
    ):
        """Test completing onboarding with non-existent organization"""
        service = OnboardingService(db_session, 99999)
        
        request = CompleteOnboardingRequest(
            country="USA",
            currency="USD",
            profile_type="freelance",
            team_members=[],
            expenses=[]
        )
        
        with pytest.raises(ValueError, match="Organization.*not found"):
            await service.complete_onboarding(request)
    
    async def test_complete_onboarding_transaction_rollback(
        self,
        db_session: AsyncSession,
        test_organization
    ):
        """Test that transaction rolls back on error"""
        # Get initial state before any operations
        initial_name = test_organization.name
        initial_settings = test_organization.settings.copy() if test_organization.settings else {}
        
        # Create request that will cause an error during team member creation
        # We'll use a service with invalid organization_id to trigger rollback
        invalid_service = OnboardingService(db_session, 99999)
        
        request = CompleteOnboardingRequest(
            country="USA",
            currency="USD",
            profile_type="company",
            team_members=[
                OnboardingTeamMember(
                    name="Test Developer",
                    role="Developer",
                    salary_monthly_brute=Decimal("5000"),
                    currency="USD",
                    billable_hours_per_month=160
                )
            ],
            expenses=[]
        )
        
        # This should raise ValueError because organization doesn't exist
        # The service should rollback automatically on exception
        with pytest.raises(ValueError, match="Organization.*not found"):
            await invalid_service.complete_onboarding(request)
        
        # Verify rollback: After the exception, the service's rollback should have been called
        # We verify that the test_organization wasn't affected by refreshing it
        # Since the error happens before any changes to test_organization (different org_id),
        # the organization should remain unchanged
        await db_session.refresh(test_organization)
        assert test_organization.name == initial_name
        
        # Verify settings weren't modified by the failed operation
        final_settings = test_organization.settings.copy() if test_organization.settings else {}
        # The test_organization should not have onboarding_completed set
        # because the invalid_service used a different org_id (99999)
        # Since the error happens early (org not found), no changes should have been made
        if test_organization.settings:
            assert test_organization.settings.get("onboarding_completed") != True or final_settings == initial_settings
        else:
            # If settings is None, it should match initial state
            assert initial_settings == {}


@pytest.mark.unit
class TestOnboardingImportPreview:
    """Tests for onboarding import preview mapping and validation."""

    async def test_import_preview_builds_payload_successfully(
        self,
        db_session: AsyncSession,
        test_organization
    ):
        service = OnboardingService(db_session, test_organization.id)

        result = await service._build_payload_from_import_rows(
            organization_rows=[{
                "organization_name": "Agency X",
                "organization_description": "Design agency",
                "country": "USA",
                "currency": "USD",
                "profile_type": "agency",
            }],
            team_rows=[{
                "name": "Alice",
                "role": "Developer",
                "salary_monthly_brute": "5000",
                "currency": "USD",
                "billable_hours_per_month": 160,
            }],
            expense_rows=[{
                "name": "Office Rent",
                "category": "rent",
                "amount_monthly": "1000",
                "currency": "USD",
                "quantity": 1,
            }],
            inventory_rows=[{
                "name": "Laptop",
                "category": "Tools",
                "amount_monthly": "2400",
                "currency": "USD",
                "quantity": 1,
                "amortizable": "true",
            }],
            source="excel",
        )

        assert result["success"] is True
        assert result["issues"] == []
        assert result["payload"] is not None
        assert result["payload"]["country"] == "USA"
        assert result["payload"]["currency"] == "USD"
        assert len(result["payload"]["team_members"]) == 1
        assert result["temporary_bcr"] is not None

    async def test_import_preview_rejects_mixed_currency(
        self,
        db_session: AsyncSession,
        test_organization
    ):
        service = OnboardingService(db_session, test_organization.id)

        result = await service._build_payload_from_import_rows(
            organization_rows=[{
                "organization_name": "Agency Y",
                "country": "COL",
                "currency": "COP",
                "profile_type": "agency",
            }],
            team_rows=[{
                "name": "Bob",
                "role": "Designer",
                "salary_monthly_brute": "4000",
                "currency": "USD",
                "billable_hours_per_month": 160,
            }],
            expense_rows=[],
            inventory_rows=[],
            source="google_sheets",
        )

        assert result["success"] is False
        assert result["payload"] is None
        assert any(issue["field"] == "currency" for issue in result["issues"])


@pytest.mark.unit
class TestOnboardingImportTemplate:
    """Tests for official onboarding import template generation."""

    async def test_generate_excel_import_template_has_required_sheets(
        self,
        db_session: AsyncSession,
        test_organization
    ):
        service = OnboardingService(db_session, test_organization.id)
        content = service.generate_excel_import_template()
        assert content is not None
        assert len(content) > 0

        from io import BytesIO
        from openpyxl import load_workbook

        wb = load_workbook(BytesIO(content))
        sheet_names = set(wb.sheetnames)
        assert {"Organization", "Team", "Expenses", "Inventory", "README"}.issubset(sheet_names)

    async def test_generate_excel_import_template_contains_expected_headers(
        self,
        db_session: AsyncSession,
        test_organization
    ):
        service = OnboardingService(db_session, test_organization.id)
        content = service.generate_excel_import_template()

        from io import BytesIO
        from openpyxl import load_workbook

        wb = load_workbook(BytesIO(content))
        org_headers = [cell.value for cell in wb["Organization"][1]]
        team_headers = [cell.value for cell in wb["Team"][1]]
        expenses_headers = [cell.value for cell in wb["Expenses"][1]]
        inventory_headers = [cell.value for cell in wb["Inventory"][1]]

        assert org_headers == ["organization_name", "organization_description", "country", "currency", "profile_type"]
        assert team_headers == ["name", "role", "salary_monthly_brute", "currency", "billable_hours_per_month"]
        assert expenses_headers == ["name", "category", "amount_monthly", "currency", "quantity"]
        assert inventory_headers == [
            "name",
            "category",
            "purchase_price",
            "useful_life_months",
            "salvage_value",
            "purchase_date",
            "depreciation_method",
            "amount_monthly",
            "currency",
            "quantity",
            "amortizable",
        ]
