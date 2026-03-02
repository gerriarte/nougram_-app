"""
Onboarding Service - Business logic for onboarding operations
"""
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified
from decimal import Decimal
import logging

from app.repositories.factory import RepositoryFactory
from app.repositories.organization_repository import OrganizationRepository
from app.core.calculations import calculate_blended_cost_rate
from app.schemas.onboarding import (
    CompleteOnboardingRequest,
    OnboardingTeamMember,
    OnboardingExpense,
    TemporaryBCRRequest
)
from app.models.team import TeamMember
from app.models.cost import CostFixed

logger = logging.getLogger(__name__)


class OnboardingService:
    """Service for onboarding operations"""
    
    def __init__(self, db: AsyncSession, organization_id: int):
        """
        Initialize OnboardingService
        
        Args:
            db: Database session
            organization_id: Organization ID for tenant scoping
        """
        self.db = db
        self.organization_id = organization_id
        self.org_repo = OrganizationRepository(db)
        self.team_repo = RepositoryFactory.create_team_repository(db, organization_id)
        self.cost_repo = RepositoryFactory.create_cost_repository(db, organization_id)
    
    async def get_benchmarks(
        self,
        profile_type: str,
        country: str = "US",
        currency: str = "USD"
    ) -> Dict[str, Any]:
        """
        Get benchmark values for a business profile
        
        Args:
            profile_type: Profile type (freelance, company, agency)
            country: Country code
            currency: Currency code
        
        Returns:
            Dictionary with benchmark values
        """
        # Benchmarks hardcoded (en producción podrían venir de base de datos o API externa)
        benchmarks_data = {
            "freelance": {
                "avg_monthly_income": Decimal("5000"),
                "avg_margin": Decimal("25"),
                "avg_hours_per_month": Decimal("160"),
                "avg_team_size": None,
                "avg_salary": None,
                "avg_clients": None,
            },
            "company": {
                "avg_monthly_income": None,
                "avg_margin": Decimal("30"),
                "avg_hours_per_month": None,
                "avg_team_size": 5,
                "avg_salary": Decimal("3000"),
                "avg_clients": None,
            },
            "agency": {
                "avg_monthly_income": None,
                "avg_margin": Decimal("35"),
                "avg_hours_per_month": None,
                "avg_team_size": 10,
                "avg_salary": Decimal("3500"),
                "avg_clients": 5,
            }
        }
        
        # Ajustar según país (ejemplo: Colombia tiene salarios más bajos)
        if country == "COL":
            if benchmarks_data[profile_type].get("avg_salary"):
                benchmarks_data[profile_type]["avg_salary"] *= Decimal("0.4")  # Aproximado
        
        return {
            "profile_type": profile_type,
            "country": country,
            "currency": currency,
            "benchmarks": benchmarks_data.get(profile_type, {}),
            "source": "industry_standard"
        }
    
    async def complete_onboarding(
        self,
        request: CompleteOnboardingRequest
    ) -> Dict[str, Any]:
        """
        Complete onboarding by saving all configuration
        
        Args:
            request: CompleteOnboardingRequest with all onboarding data
        
        Returns:
            Dictionary with results of onboarding completion
        """
        try:
            # 1. Update organization
            org = await self.org_repo.get_by_id(self.organization_id)
            if not org:
                raise ValueError(f"Organization {self.organization_id} not found")
            
            # Update organization name if provided
            if request.organization_name:
                org.name = request.organization_name
            
            # Update primary currency
            if request.currency:
                org.primary_currency = request.currency
            
            # Update settings with onboarding data
            if org.settings is None:
                org.settings = {}
            
            if request.organization_description:
                org.settings["description"] = request.organization_description
            
            org.settings["country"] = request.country
            org.settings["profile_type"] = request.profile_type
            org.settings["onboarding_completed"] = True
            
            if request.tax_structure:
                org.settings["tax_structure"] = request.tax_structure
            if request.social_charges_config:
                org.settings["social_charges_config"] = request.social_charges_config
            if request.inventory_items:
                # Keep inventory detail for future modules (assets, amortization, audits).
                org.settings["onboarding_inventory_items"] = request.inventory_items
            
            # Mark settings as modified so SQLAlchemy detects the change
            flag_modified(org, "settings")
            
            await self.db.commit()
            await self.db.refresh(org)
            
            # 2. Create team members
            team_members_created = 0
            for member_data in request.team_members:
                # Convert monthly hours to weekly (approximate)
                billable_hours_per_week = max(1, member_data.billable_hours_per_month // 4)
                
                # Create TeamMember model instance
                team_member = TeamMember(
                    name=member_data.name,
                    role=member_data.role,
                    salary_monthly_brute=member_data.salary_monthly_brute,
                    currency=member_data.currency,
                    billable_hours_per_week=billable_hours_per_week,
                    is_active=True,
                    organization_id=self.organization_id
                )
                await self.team_repo.create(team_member)
                team_members_created += 1
            
            # 3. Create fixed costs (expenses)
            expenses_created = 0
            for expense_data in request.expenses:
                # Create CostFixed model instance
                cost_fixed = CostFixed(
                    name=expense_data.name,
                    category=expense_data.category,
                    amount_monthly=expense_data.amount_monthly,
                    currency=expense_data.currency,
                    description=f"Operational expense: {expense_data.name}",
                    organization_id=self.organization_id
                )
                await self.cost_repo.create(cost_fixed)
                expenses_created += 1
            
            await self.db.commit()
            
            # 4. Calculate BCR after saving
            bcr = await calculate_blended_cost_rate(
                self.db,
                primary_currency=request.currency,
                tenant_id=self.organization_id
            )
            
            logger.info(
                f"Onboarding completed for organization {self.organization_id}: "
                f"{team_members_created} team members, {expenses_created} expenses"
            )
            
            return {
                "success": True,
                "message": "Onboarding completed successfully",
                "organization_id": self.organization_id,
                "team_members_created": team_members_created,
                "expenses_created": expenses_created,
                "bcr_calculated": str(bcr),
                "organization": {
                    "id": org.id,
                    "name": org.name,
                    "primary_currency": org.primary_currency,
                    "settings": org.settings
                }
            }
        
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error completing onboarding: {e}", exc_info=True)
            raise
    
    async def calculate_temporary_bcr(
        self,
        request: TemporaryBCRRequest
    ) -> Dict[str, Any]:
        """
        Calculate BCR with temporary onboarding data (before saving)
        
        Args:
            request: TemporaryBCRRequest with temporary team and expense data
        
        Returns:
            Dictionary with calculated BCR and breakdown
        """
        # Calculate total salaries
        total_salaries = sum(
            Decimal(str(member.salary_monthly_brute))
            for member in request.team_members
        )
        
        # Calculate total expenses
        total_expenses = sum(
            Decimal(str(expense.amount_monthly))
            for expense in request.expenses
        )
        
        # Calculate total monthly costs
        total_monthly_costs = total_salaries + total_expenses
        
        # Calculate total billable hours per month
        total_hours = sum(
            member.billable_hours_per_month
            for member in request.team_members
        )
        
        # Calculate BCR
        if total_hours > 0:
            bcr = total_monthly_costs / Decimal(str(total_hours))
        else:
            bcr = Decimal("0")
        
        return {
            "blended_cost_rate": str(bcr),
            "total_monthly_costs": str(total_monthly_costs),
            "total_fixed_overhead": str(total_expenses),
            "total_salaries": str(total_salaries),
            "total_monthly_hours": float(total_hours),
            "team_members_count": len(request.team_members),
            "currency": request.currency,
            "note": "Values are calculated with temporary data and may differ after saving"
        }
