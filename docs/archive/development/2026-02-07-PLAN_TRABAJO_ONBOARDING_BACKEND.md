# Plan de Implementación: Onboarding Backend para Nougram

**Fecha:** 2026-02-08  
**Base:** [2026-02-07-PLAN_TRABAJO_ONBOARDING_APPLE_STYLE.md](./2026-02-07-PLAN_TRABAJO_ONBOARDING_APPLE_STYLE.md) (Frontend)  
**Arquitectura:** MVC + Repository/Service (`.cursorrules/nougram_backend_rules.md`)  
**Ubicación:** `backend/app/`

---

## 🎯 Resumen Ejecutivo

Implementar endpoints del backend para soportar el nuevo proceso de onboarding con estilo Apple, permitiendo:

- **Benchmarks por perfil:** Obtener valores sugeridos basados en industria y región
- **Guardado batch:** Guardar toda la configuración de onboarding (organización, equipo, gastos) en una sola transacción
- **Cálculo temporal de BCR:** Calcular BCR con datos del onboarding antes de guardar
- **Mejoras al endpoint existente:** Extender `/onboarding-config` para soportar el nuevo flujo

**Arquitectura Requerida:**
```
Endpoint → Controller → Service → Repository → ORM → Database
                    ↓
                  View (transformación de datos)
```

**Endpoints Requeridos:**
1. `GET /api/v1/onboarding/benchmarks` - Obtener benchmarks por perfil
2. `POST /api/v1/onboarding/complete` - Guardar configuración completa de onboarding
3. `POST /api/v1/onboarding/calculate-bcr` - Calcular BCR temporal con datos del onboarding
4. `PUT /api/v1/organizations/{id}/onboarding-config` - Mejorar endpoint existente

---

## 📊 Análisis de Estado Actual

### Endpoints Existentes
- ✅ `POST /organizations/{id}/onboarding-config` - Guarda configuración en settings (limitado)
- ✅ `POST /team` - Crear miembro de equipo individual
- ✅ `POST /costs/fixed` - Crear costo fijo individual
- ✅ `PUT /organizations/{id}` - Actualizar organización
- ✅ `GET /calculations/agency-cost-hour` - Calcular BCR (requiere datos guardados)

### Limitaciones Actuales
- ❌ No hay endpoint de benchmarks por perfil
- ❌ No hay endpoint para guardar todo el onboarding en batch
- ❌ No hay endpoint para calcular BCR con datos temporales del onboarding
- ❌ El endpoint `/onboarding-config` solo guarda en settings, no crea team/costs

---

## 📋 Componentes a Implementar

### 1. ✅ Schemas (`backend/app/schemas/onboarding.py`)

**Estado:** ❌ No implementado

**Implementación Requerida:**

```python
"""
Pydantic schemas for Onboarding
"""
from typing import Optional, List, Dict, Any, Literal
from decimal import Decimal
from pydantic import BaseModel, Field, field_serializer

from app.schemas.team import TeamMemberCreate
from app.schemas.cost import CostFixedCreate
from app.core.pydantic_config import DECIMAL_CONFIG


# Benchmarks
class ProfileBenchmark(BaseModel):
    """Benchmark values for a business profile"""
    profile_type: Literal["freelance", "company", "agency"]
    avg_monthly_income: Optional[Decimal] = Field(None, description="Average monthly income")
    avg_margin: Optional[Decimal] = Field(None, description="Average margin percentage")
    avg_hours_per_month: Optional[Decimal] = Field(None, description="Average billable hours per month")
    avg_team_size: Optional[int] = Field(None, description="Average team size")
    avg_salary: Optional[Decimal] = Field(None, description="Average salary")
    avg_clients: Optional[int] = Field(None, description="Average number of clients")
    
    @field_serializer('avg_monthly_income', 'avg_margin', 'avg_hours_per_month', 'avg_salary')
    def serialize_decimal(self, value: Optional[Decimal]) -> Optional[str]:
        """Serialize Decimal as string"""
        return str(value) if value is not None else None
    
    model_config = DECIMAL_CONFIG


class BenchmarksResponse(BaseModel):
    """Response with benchmarks for a profile type"""
    profile_type: Literal["freelance", "company", "agency"]
    country: str
    currency: str
    benchmarks: ProfileBenchmark
    source: str = Field("industry_standard", description="Source of benchmarks")


# Complete Onboarding
class OnboardingTeamMember(BaseModel):
    """Team member data for onboarding"""
    name: str = Field(..., min_length=1)
    role: str = Field(..., min_length=1)
    salary_monthly_brute: Decimal = Field(..., gt=0)
    currency: str = Field("USD")
    billable_hours_per_month: int = Field(40, ge=1, le=200)  # Converted from weekly
    
    @field_serializer('salary_monthly_brute')
    def serialize_decimal(self, value: Decimal) -> str:
        return str(value)
    
    model_config = DECIMAL_CONFIG


class OnboardingExpense(BaseModel):
    """Operational expense for onboarding"""
    name: str = Field(..., min_length=1)
    category: Literal["rent", "software", "services"] = Field(...)
    amount_monthly: Decimal = Field(..., gt=0)
    currency: str = Field("USD")
    
    @field_serializer('amount_monthly')
    def serialize_decimal(self, value: Decimal) -> str:
        return str(value)
    
    model_config = DECIMAL_CONFIG


class CompleteOnboardingRequest(BaseModel):
    """Request to save complete onboarding configuration"""
    # Organization data
    organization_name: Optional[str] = Field(None, min_length=1)
    organization_description: Optional[str] = None
    country: str = Field(..., min_length=2, max_length=3)
    currency: str = Field(..., min_length=3, max_length=3)
    profile_type: Literal["freelance", "company", "agency"] = Field(...)
    
    # Team members (optional, can be empty for freelance)
    team_members: List[OnboardingTeamMember] = Field(default_factory=list)
    
    # Operational expenses
    expenses: List[OnboardingExpense] = Field(default_factory=list)
    
    # Tax structure (optional)
    tax_structure: Optional[Dict[str, Any]] = None
    
    # Social charges config (optional, mainly for Colombia)
    social_charges_config: Optional[Dict[str, Any]] = None


class CompleteOnboardingResponse(BaseModel):
    """Response after completing onboarding"""
    success: bool
    message: str
    organization_id: int
    team_members_created: int
    expenses_created: int
    bcr_calculated: Optional[str] = Field(None, description="Calculated BCR after onboarding")
    organization: Dict[str, Any] = Field(..., description="Updated organization data")


# Temporary BCR Calculation
class TemporaryBCRRequest(BaseModel):
    """Request to calculate BCR with temporary onboarding data"""
    team_members: List[OnboardingTeamMember] = Field(..., min_items=1)
    expenses: List[OnboardingExpense] = Field(default_factory=list)
    currency: str = Field("USD")


class TemporaryBCRResponse(BaseModel):
    """Response with temporary BCR calculation"""
    blended_cost_rate: str = Field(..., description="Calculated BCR (Decimal as string)")
    total_monthly_costs: str = Field(..., description="Total monthly costs")
    total_fixed_overhead: str = Field(..., description="Total fixed overhead")
    total_salaries: str = Field(..., description="Total salaries")
    total_monthly_hours: float = Field(..., description="Total billable hours per month")
    team_members_count: int = Field(..., description="Number of team members")
    currency: str = Field(..., description="Currency code")
    note: str = Field("Values are calculated with temporary data and may differ after saving", 
                     description="Disclaimer about temporary calculation")
```

---

### 2. ✅ Service (`backend/app/services/onboarding_service.py`)

**Estado:** ❌ No implementado

**Implementación Requerida:**

```python
"""
Onboarding Service - Business logic for onboarding operations
"""
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal
import logging

from app.repositories.factory import RepositoryFactory
from app.repositories.organization_repository import OrganizationRepository
from app.core.calculations import calculate_blended_cost_rate
from app.core.money import Money
from app.schemas.onboarding import (
    CompleteOnboardingRequest,
    OnboardingTeamMember,
    OnboardingExpense,
    TemporaryBCRRequest
)
from app.schemas.team import TeamMemberCreate
from app.schemas.cost import CostFixedCreate

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
            
            update_data = {}
            if request.organization_name:
                update_data["name"] = request.organization_name
            if request.organization_description:
                if org.settings is None:
                    org.settings = {}
                org.settings["description"] = request.organization_description
            
            # Update primary currency
            if request.currency:
                org.primary_currency = request.currency
            
            # Update settings with onboarding data
            if org.settings is None:
                org.settings = {}
            
            org.settings["country"] = request.country
            org.settings["profile_type"] = request.profile_type
            org.settings["onboarding_completed"] = True
            
            if request.tax_structure:
                org.settings["tax_structure"] = request.tax_structure
            if request.social_charges_config:
                org.settings["social_charges_config"] = request.social_charges_config
            
            if update_data:
                await self.org_repo.update(self.organization_id, update_data)
            
            await self.db.commit()
            await self.db.refresh(org)
            
            # 2. Create team members
            team_members_created = 0
            for member_data in request.team_members:
                team_member_create = TeamMemberCreate(
                    name=member_data.name,
                    role=member_data.role,
                    salary_monthly_brute=member_data.salary_monthly_brute,
                    currency=member_data.currency,
                    billable_hours_per_week=member_data.billable_hours_per_month // 4,  # Convert monthly to weekly
                    is_active=True
                )
                await self.team_repo.create(team_member_create)
                team_members_created += 1
            
            # 3. Create fixed costs (expenses)
            expenses_created = 0
            for expense_data in request.expenses:
                cost_create = CostFixedCreate(
                    name=expense_data.name,
                    category=expense_data.category,
                    amount_monthly=expense_data.amount_monthly,
                    currency=expense_data.currency,
                    is_active=True
                )
                await self.cost_repo.create(cost_create)
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
```

---

### 3. ✅ View (`backend/app/views/onboarding_view.py`)

**Estado:** ❌ No implementado

**Implementación Requerida:**

```python
"""
Onboarding View - Data transformation for onboarding responses
"""
from typing import Dict, Any

from app.views.base import BaseView
from app.schemas.onboarding import (
    BenchmarksResponse,
    ProfileBenchmark,
    CompleteOnboardingResponse,
    TemporaryBCRResponse
)


class OnboardingView(BaseView):
    """View for transforming onboarding data to response schemas"""
    
    def to_benchmarks_response(self, data: Dict[str, Any]) -> BenchmarksResponse:
        """
        Transform service data to BenchmarksResponse
        
        Args:
            data: Dictionary from OnboardingService.get_benchmarks()
        
        Returns:
            BenchmarksResponse instance
        """
        benchmarks = ProfileBenchmark(
            profile_type=data["profile_type"],
            avg_monthly_income=data["benchmarks"].get("avg_monthly_income"),
            avg_margin=data["benchmarks"].get("avg_margin"),
            avg_hours_per_month=data["benchmarks"].get("avg_hours_per_month"),
            avg_team_size=data["benchmarks"].get("avg_team_size"),
            avg_salary=data["benchmarks"].get("avg_salary"),
            avg_clients=data["benchmarks"].get("avg_clients"),
        )
        
        return BenchmarksResponse(
            profile_type=data["profile_type"],
            country=data["country"],
            currency=data["currency"],
            benchmarks=benchmarks,
            source=data["source"]
        )
    
    def to_complete_response(self, data: Dict[str, Any]) -> CompleteOnboardingResponse:
        """
        Transform service data to CompleteOnboardingResponse
        
        Args:
            data: Dictionary from OnboardingService.complete_onboarding()
        
        Returns:
            CompleteOnboardingResponse instance
        """
        return CompleteOnboardingResponse(
            success=data["success"],
            message=data["message"],
            organization_id=data["organization_id"],
            team_members_created=data["team_members_created"],
            expenses_created=data["expenses_created"],
            bcr_calculated=data.get("bcr_calculated"),
            organization=data["organization"]
        )
    
    def to_temporary_bcr_response(self, data: Dict[str, Any]) -> TemporaryBCRResponse:
        """
        Transform service data to TemporaryBCRResponse
        
        Args:
            data: Dictionary from OnboardingService.calculate_temporary_bcr()
        
        Returns:
            TemporaryBCRResponse instance
        """
        return TemporaryBCRResponse(
            blended_cost_rate=data["blended_cost_rate"],
            total_monthly_costs=data["total_monthly_costs"],
            total_fixed_overhead=data["total_fixed_overhead"],
            total_salaries=data["total_salaries"],
            total_monthly_hours=data["total_monthly_hours"],
            team_members_count=data["team_members_count"],
            currency=data["currency"],
            note=data["note"]
        )
```

---

### 4. ✅ Controller (`backend/app/controllers/onboarding_controller.py`)

**Estado:** ❌ No implementado

**Implementación Requerida:**

```python
"""
Onboarding Controller - HTTP request handling for onboarding
"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.controllers.base import BaseController
from app.services.onboarding_service import OnboardingService
from app.views.onboarding_view import OnboardingView
from app.schemas.onboarding import (
    BenchmarksResponse,
    CompleteOnboardingRequest,
    CompleteOnboardingResponse,
    TemporaryBCRRequest,
    TemporaryBCRResponse
)


class OnboardingController(BaseController):
    """
    Controller for handling onboarding HTTP requests
    
    Responsibilities:
    - HTTP request validation
    - Delegation to OnboardingService
    - Response formatting via OnboardingView
    - Error handling
    """
    
    def __init__(
        self,
        db: AsyncSession,
        tenant,
        current_user
    ):
        """
        Initialize OnboardingController
        
        Args:
            db: Database session
            tenant: Tenant context
            current_user: Current authenticated user
        """
        super().__init__(db, tenant, current_user)
        self.onboarding_service = OnboardingService(db, self.organization_id)
        self.onboarding_view = OnboardingView()
    
    async def get_benchmarks(
        self,
        profile_type: str,
        country: Optional[str] = None,
        currency: Optional[str] = None
    ) -> BenchmarksResponse:
        """
        Get benchmarks for a profile type
        
        Args:
            profile_type: Profile type (freelance, company, agency)
            country: Country code (defaults to organization country)
            currency: Currency code (defaults to organization currency)
        
        Returns:
            BenchmarksResponse
        
        Raises:
            HTTPException: If validation fails
        """
        try:
            # Validate profile_type
            if profile_type not in ["freelance", "company", "agency"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid profile_type: {profile_type}. Must be 'freelance', 'company', or 'agency'"
                )
            
            # Use organization defaults if not provided
            if not country:
                country = self.tenant.organization.settings.get("country", "US") if self.tenant.organization.settings else "US"
            if not currency:
                currency = self.tenant.organization.primary_currency or "USD"
            
            # Get benchmarks from service
            benchmarks_data = await self.onboarding_service.get_benchmarks(
                profile_type=profile_type,
                country=country,
                currency=currency
            )
            
            # Transform to response
            return self.onboarding_view.to_benchmarks_response(benchmarks_data)
        
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            self.logger.error(f"Error getting benchmarks: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error retrieving benchmarks"
            )
    
    async def complete_onboarding(
        self,
        request: CompleteOnboardingRequest
    ) -> CompleteOnboardingResponse:
        """
        Complete onboarding by saving all configuration
        
        Args:
            request: CompleteOnboardingRequest with all onboarding data
        
        Returns:
            CompleteOnboardingResponse
        
        Raises:
            HTTPException: If onboarding fails
        """
        try:
            # Validate request
            if not request.organization_name and not self.tenant.organization.name:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="organization_name is required"
                )
            
            # Complete onboarding
            result = await self.onboarding_service.complete_onboarding(request)
            
            # Transform to response
            return self.onboarding_view.to_complete_response(result)
        
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            self.logger.error(f"Error completing onboarding: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error completing onboarding"
            )
    
    async def calculate_temporary_bcr(
        self,
        request: TemporaryBCRRequest
    ) -> TemporaryBCRResponse:
        """
        Calculate BCR with temporary onboarding data
        
        Args:
            request: TemporaryBCRRequest with temporary data
        
        Returns:
            TemporaryBCRResponse
        
        Raises:
            HTTPException: If calculation fails
        """
        try:
            # Validate request
            if not request.team_members:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="At least one team member is required"
                )
            
            # Calculate temporary BCR
            result = await self.onboarding_service.calculate_temporary_bcr(request)
            
            # Transform to response
            return self.onboarding_view.to_temporary_bcr_response(result)
        
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            self.logger.error(f"Error calculating temporary BCR: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error calculating temporary BCR"
            )
```

---

### 5. ✅ Endpoints (`backend/app/api/v1/endpoints/onboarding.py`)

**Estado:** ❌ No implementado

**Implementación Requerida:**

```python
"""
Onboarding endpoints
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.tenant import get_tenant_context, TenantContext
from app.models.user import User
from app.controllers.onboarding_controller import OnboardingController
from app.schemas.onboarding import (
    BenchmarksResponse,
    CompleteOnboardingRequest,
    CompleteOnboardingResponse,
    TemporaryBCRRequest,
    TemporaryBCRResponse
)

router = APIRouter()


@router.get(
    "/benchmarks",
    response_model=BenchmarksResponse,
    summary="Get benchmarks for a business profile"
)
async def get_benchmarks(
    profile_type: str = Query(..., description="Profile type: freelance, company, or agency"),
    country: Optional[str] = Query(None, description="Country code (defaults to organization country)"),
    currency: Optional[str] = Query(None, description="Currency code (defaults to organization currency)"),
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get benchmark values for a business profile type
    
    Returns industry-standard benchmarks for:
    - Average monthly income (freelance)
    - Average margin percentage
    - Average billable hours per month
    - Average team size (company/agency)
    - Average salary (company/agency)
    - Average number of clients (agency)
    
    **Permissions:**
    - Requires authentication
    - Available to all authenticated users
    
    **Example:**
    ```
    GET /api/v1/onboarding/benchmarks?profile_type=freelance&country=US&currency=USD
    ```
    """
    controller = OnboardingController(db, tenant, current_user)
    return await controller.get_benchmarks(
        profile_type=profile_type,
        country=country,
        currency=currency
    )


@router.post(
    "/complete",
    response_model=CompleteOnboardingResponse,
    status_code=201,
    summary="Complete onboarding by saving all configuration"
)
async def complete_onboarding(
    request: CompleteOnboardingRequest,
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Complete onboarding by saving all configuration in a single transaction
    
    This endpoint:
    1. Updates organization details (name, currency, settings)
    2. Creates all team members
    3. Creates all operational expenses (fixed costs)
    4. Calculates and returns the final BCR
    
    **Permissions:**
    - Requires `can_modify_costs` permission (team and costs affect financial calculations)
    - Allowed roles: owner, admin_financiero
    - Must be owner of the organization
    
    **Request Body:**
    - `organization_name`: Organization name (optional if already set)
    - `country`: Country code (required)
    - `currency`: Currency code (required)
    - `profile_type`: Profile type (required)
    - `team_members`: List of team members (can be empty for freelance)
    - `expenses`: List of operational expenses (optional)
    - `tax_structure`: Tax structure dictionary (optional)
    - `social_charges_config`: Social charges configuration (optional)
    
    **Returns:**
    - `201 Created`: Onboarding completed successfully
    - `400 Bad Request`: Validation error
    - `403 Forbidden`: User doesn't have permission
    """
    # Verify user is owner
    if current_user.role != 'owner' and current_user.organization_id != tenant.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only organization owners can complete onboarding"
        )
    
    controller = OnboardingController(db, tenant, current_user)
    return await controller.complete_onboarding(request)


@router.post(
    "/calculate-bcr",
    response_model=TemporaryBCRResponse,
    summary="Calculate BCR with temporary onboarding data"
)
async def calculate_temporary_bcr(
    request: TemporaryBCRRequest,
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Calculate BCR with temporary onboarding data (before saving)
    
    This endpoint allows calculating the BCR with data that hasn't been saved yet,
    useful for showing a preview in the onboarding flow.
    
    **Permissions:**
    - Requires authentication
    - Available to all authenticated users
    
    **Request Body:**
    - `team_members`: List of team members (at least one required)
    - `expenses`: List of operational expenses (optional)
    - `currency`: Currency code (required)
    
    **Returns:**
    - `200 OK`: BCR calculated successfully
    - `400 Bad Request`: Validation error (e.g., no team members)
    
    **Note:**
    This is a temporary calculation and may differ from the actual BCR after saving,
    especially if there are existing team members or costs in the database.
    """
    controller = OnboardingController(db, tenant, current_user)
    return await controller.calculate_temporary_bcr(request)
```

---

### 6. ✅ Router Registration (`backend/app/api/v1/router.py`)

**Estado:** ⚠️ Pendiente de agregar

**Modificación Requerida:**

```python
# Agregar import
from app.api.v1.endpoints import onboarding

# Agregar router (después de organizations)
api_router.include_router(onboarding.router, prefix="/onboarding", tags=["onboarding"])
```

---

### 7. ✅ Mejora: Endpoint Existente de Onboarding Config

**Estado:** ⚠️ Mejorar endpoint existente

**Archivo:** `backend/app/api/v1/endpoints/organizations.py`

**Mejora Requerida:**

El endpoint `POST /organizations/{organization_id}/onboarding-config` ya existe pero solo guarda en settings. Podemos mantenerlo para compatibilidad, pero el nuevo endpoint `/onboarding/complete` será el principal.

**Opción:** Agregar documentación indicando que `/onboarding/complete` es el endpoint recomendado.

---

## 📝 Plan de Implementación por Fases

### Fase 1: Schemas y Estructura Base (Prioridad Alta)

**Objetivo:** Crear schemas y estructura base para onboarding

**Tareas:**
1. ✅ Crear `schemas/onboarding.py` con todos los schemas
2. ✅ Validar schemas con Pydantic
3. ✅ Agregar serializadores para Decimal

**Estimación:** 1 día

---

### Fase 2: Service Layer (Prioridad Alta)

**Objetivo:** Implementar lógica de negocio para onboarding

**Tareas:**
1. ✅ Crear `services/onboarding_service.py`
2. ✅ Implementar `get_benchmarks()`
3. ✅ Implementar `complete_onboarding()`
4. ✅ Implementar `calculate_temporary_bcr()`
5. ✅ Manejar transacciones y rollback

**Estimación:** 2 días

---

### Fase 3: View Layer (Prioridad Media)

**Objetivo:** Implementar transformación de datos

**Tareas:**
1. ✅ Crear `views/onboarding_view.py`
2. ✅ Implementar métodos de transformación
3. ✅ Validar respuestas

**Estimación:** 0.5 días

---

### Fase 4: Controller Layer (Prioridad Alta)

**Objetivo:** Implementar manejo de HTTP requests

**Tareas:**
1. ✅ Crear `controllers/onboarding_controller.py`
2. ✅ Implementar validaciones HTTP
3. ✅ Manejo de errores
4. ✅ Logging

**Estimación:** 1 día

---

### Fase 5: Endpoints (Prioridad Alta)

**Objetivo:** Crear endpoints REST

**Tareas:**
1. ✅ Crear `endpoints/onboarding.py`
2. ✅ Implementar `GET /onboarding/benchmarks`
3. ✅ Implementar `POST /onboarding/complete`
4. ✅ Implementar `POST /onboarding/calculate-bcr`
5. ✅ Registrar router en `router.py`

**Estimación:** 1 día

---

### Fase 6: Testing (Prioridad Alta)

**Objetivo:** Testing completo de endpoints

**Tareas:**
1. ✅ Tests unitarios para `OnboardingService`
2. ✅ Tests de integración para endpoints
3. ✅ Tests de validación de schemas
4. ✅ Tests de transacciones

**Estimación:** 2 días

---

## ✅ Checklist de Implementación

### Schemas (Pydantic)
- [ ] `ProfileBenchmark`
- [ ] `BenchmarksResponse`
- [ ] `OnboardingTeamMember`
- [ ] `OnboardingExpense`
- [ ] `CompleteOnboardingRequest`
- [ ] `CompleteOnboardingResponse`
- [ ] `TemporaryBCRRequest`
- [ ] `TemporaryBCRResponse`

### Services (Lógica de Negocio)
- [ ] `OnboardingService.__init__()`
- [ ] `OnboardingService.get_benchmarks()`
- [ ] `OnboardingService.complete_onboarding()`
- [ ] `OnboardingService.calculate_temporary_bcr()`

### Views (Transformación de Datos)
- [ ] `OnboardingView.to_benchmarks_response()`
- [ ] `OnboardingView.to_complete_response()`
- [ ] `OnboardingView.to_temporary_bcr_response()`

### Controllers (Manejo HTTP)
- [ ] `OnboardingController.__init__()`
- [ ] `OnboardingController.get_benchmarks()`
- [ ] `OnboardingController.complete_onboarding()`
- [ ] `OnboardingController.calculate_temporary_bcr()`

### Endpoints (API REST)
- [ ] `GET /api/v1/onboarding/benchmarks`
- [ ] `POST /api/v1/onboarding/complete`
- [ ] `POST /api/v1/onboarding/calculate-bcr`

### Router
- [ ] Importar `onboarding` en `router.py`
- [ ] Registrar router con prefix `/onboarding`

### Tests
- [ ] Tests unitarios para `OnboardingService`
- [ ] Tests de integración para endpoints
- [ ] Tests de validación de schemas
- [ ] Tests de transacciones y rollback

---

## 🔗 Dependencias y Reutilización

### Código Existente Reutilizable:

1. **`RepositoryFactory`**
   - ✅ Ya existe
   - ✅ Métodos `create_team_repository()` y `create_cost_repository()` disponibles

2. **`OrganizationRepository`**
   - ✅ Ya existe
   - ✅ Métodos `get_by_id()` y `update()` disponibles

3. **`calculate_blended_cost_rate()`**
   - ✅ Ya existe en `app.core.calculations`
   - ✅ Soporta tenant scoping
   - ✅ Usa datos guardados en base de datos

4. **`TeamMemberCreate` y `CostFixedCreate`**
   - ✅ Ya existen en schemas
   - ✅ Validación completa

---

## 🎯 Consideraciones de Implementación

### Precisión Financiera:
- ✅ Usar `Decimal` para todos los cálculos financieros
- ✅ Serializar `Decimal` como string en respuestas API
- ✅ Validar montos positivos

### Tenant Scoping:
- ✅ Todos los repositorios ya tienen tenant scoping
- ✅ Usar `organization_id` del tenant context
- ✅ Validar que usuario pertenezca a la organización

### Permisos:
- ✅ `get_benchmarks`: Autenticación básica
- ✅ `complete_onboarding`: Requiere ser owner
- ✅ `calculate_temporary_bcr`: Autenticación básica

### Transacciones:
- ✅ Usar transacciones para `complete_onboarding`
- ✅ Rollback en caso de error
- ✅ Commit solo si todo es exitoso

### Validaciones:
- ✅ Validar profile_type en schemas
- ✅ Validar que haya al menos un team member para calcular BCR
- ✅ Validar montos positivos
- ✅ Validar horas facturables razonables

---

## 📚 Referencias

### Documentos Relacionados:
- [2026-02-07-PLAN_TRABAJO_ONBOARDING_APPLE_STYLE.md](./2026-02-07-PLAN_TRABAJO_ONBOARDING_APPLE_STYLE.md) - Plan de frontend
- [2026-02-07-PLAN_TRABAJO_BREAK_EVEN_BACKEND.md](./2026-02-07-PLAN_TRABAJO_BREAK_EVEN_BACKEND.md) - Ejemplo de estructura de plan
- `.cursorrules/nougram_backend_rules.md` - Reglas de arquitectura

### Código de Referencia:
- `backend/app/services/template_service.py` - Ejemplo de service con transacciones
- `backend/app/controllers/team_controller.py` - Ejemplo de controller
- `backend/app/views/team_view.py` - Ejemplo de view
- `backend/app/core/calculations.py` - Funciones de cálculo existentes

---

## 🚀 Próximos Pasos

1. **Revisar este plan** con el equipo
2. **Crear branch:** `feature/onboarding-backend`
3. **Implementar Fase 1** (Schemas)
4. **Implementar Fase 2** (Service)
5. **Implementar Fase 3** (View)
6. **Implementar Fase 4** (Controller)
7. **Implementar Fase 5** (Endpoints)
8. **Implementar Fase 6** (Testing)
9. **Code review**
10. **Merge a main**

---

## 📊 Estimación Total

- **Fase 1:** 1 día
- **Fase 2:** 2 días
- **Fase 3:** 0.5 días
- **Fase 4:** 1 día
- **Fase 5:** 1 día
- **Fase 6:** 2 días

**Total estimado:** 7.5 días de desarrollo

---

**Última actualización:** 2026-02-08  
**Versión:** 1.0  
**Estado:** Pendiente de Implementación
