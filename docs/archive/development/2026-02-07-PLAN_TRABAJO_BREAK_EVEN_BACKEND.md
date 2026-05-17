# Plan de Implementación: Break-Even Point Backend

**Fecha:** 2026-01-25  
**Base:** [2026-02-07-ANALISIS_BREAK_EVEN_BACKEND.md](./2026-02-07-ANALISIS_BREAK_EVEN_BACKEND.md)  
**Arquitectura:** MVC + Repository/Service (`.cursorrules/2026-02-07-nougram_backend_rules.md`)  
**Frontend Requirements:** `UI_REQUIREMENTS_BREAK_EVEN_POINT.md` (si existe)

---

## 🎯 Resumen Ejecutivo

El módulo de **Break-Even Point (Punto de Equilibrio)** NO está implementado en el backend. Este documento detalla la implementación completa siguiendo la **arquitectura MVC + Repository/Service** establecida.

**Arquitectura Requerida:**
```
Endpoint → Controller → Service → Repository → ORM → Database
                    ↓
                  View (transformación de datos)
```

**Endpoints Requeridos:**
1. `GET /api/v1/analytics/break-even` - Análisis actual
2. `POST /api/v1/analytics/break-even/scenarios` - Simulación de escenarios
3. `GET /api/v1/analytics/break-even/projection` - Proyección temporal

---

## 📋 Componentes a Implementar

### 1. ✅ Schemas (`backend/app/schemas/break_even.py`)

**Estado:** ❌ No implementado

**Implementación Requerida:**

```python
"""
Pydantic schemas for Break-Even Point analysis
"""
from typing import Optional, List
from pydantic import BaseModel, Field, field_serializer
from decimal import Decimal
from datetime import date


class BreakEvenAnalysisResponse(BaseModel):
    """Response schema for break-even analysis"""
    period: str = Field(..., description="Period: monthly, quarterly, annual")
    currency: str = Field(..., description="Currency code")
    
    # Costos
    total_fixed_costs: str = Field(..., description="Total fixed costs (Decimal as string)")
    total_costs: str = Field(..., description="Total costs (Decimal as string)")
    
    # Horas
    total_billable_hours_available: float = Field(..., description="Total billable hours available")
    break_even_hours: float = Field(..., description="Hours needed to break even")
    current_allocated_hours: float = Field(..., description="Currently allocated hours")
    hours_to_break_even: float = Field(..., description="Hours still needed to break even")
    safety_margin_hours: float = Field(..., description="Safety margin in hours")
    safety_margin_percentage: float = Field(..., description="Safety margin percentage")
    
    # Ingresos
    break_even_revenue: str = Field(..., description="Revenue needed to break even (Decimal as string)")
    current_projected_revenue: str = Field(..., description="Current projected revenue (Decimal as string)")
    revenue_to_break_even: str = Field(..., description="Revenue still needed (Decimal as string)")
    average_margin: float = Field(..., description="Average margin percentage")
    
    # Métricas
    operating_leverage: float = Field(..., description="Operating leverage")
    current_utilization_rate: float = Field(..., description="Current utilization rate")
    break_even_utilization_rate: float = Field(..., description="Break-even utilization rate")
    
    # Estado
    status: str = Field(..., description="above_break_even, at_break_even, or below_break_even")
    status_message: str = Field(..., description="Human-readable status message")
    
    # Proyección
    months_to_break_even: Optional[int] = Field(None, description="Months until break-even")
    projected_break_even_date: Optional[str] = Field(None, description="Projected break-even date (ISO 8601)")
    
    @field_serializer('total_fixed_costs', 'total_costs', 'break_even_revenue', 
                      'current_projected_revenue', 'revenue_to_break_even')
    def serialize_decimal(self, value: Decimal) -> str:
        """Serialize Decimal as string for API"""
        return str(value)


class ScenarioConfig(BaseModel):
    """Configuration for a break-even scenario"""
    name: str = Field(..., min_length=1, description="Scenario name")
    bcr_multiplier: float = Field(1.0, ge=0.1, le=5.0, description="BCR multiplier (1.0 = no change, 1.1 = +10%)")
    fixed_costs_adjustment: Decimal = Field(Decimal('0'), description="Fixed costs adjustment (positive = increase)")
    average_margin_adjustment: float = Field(0.0, ge=-1.0, le=1.0, description="Average margin adjustment (0 = no change, 0.15 = +15%)")


class BreakEvenScenarioRequest(BaseModel):
    """Request schema for scenario simulation"""
    scenarios: List[ScenarioConfig] = Field(..., min_items=1, description="List of scenarios to simulate")
    currency: Optional[str] = Field(None, description="Currency for calculations")


class ScenarioResult(BaseModel):
    """Result of a scenario simulation"""
    name: str = Field(..., description="Scenario name")
    break_even_hours: float = Field(..., description="Break-even hours for this scenario")
    break_even_revenue: str = Field(..., description="Break-even revenue (Decimal as string)")
    hours_to_break_even: float = Field(..., description="Hours still needed")
    impact: dict = Field(..., description="Impact compared to base scenario")
    
    @field_serializer('break_even_revenue')
    def serialize_decimal(self, value: Decimal) -> str:
        return str(value)


class BreakEvenScenariosResponse(BaseModel):
    """Response schema for scenario simulation"""
    base_scenario: dict = Field(..., description="Base scenario data")
    scenarios: List[ScenarioResult] = Field(..., description="Simulated scenarios")


class MonthProjection(BaseModel):
    """Monthly projection data"""
    month: str = Field(..., description="Month in YYYY-MM format")
    allocated_hours: float = Field(..., description="Projected allocated hours")
    break_even_hours: float = Field(..., description="Break-even hours (constant)")
    hours_to_break_even: float = Field(..., description="Hours still needed")
    status: str = Field(..., description="below_break_even, at_break_even, or above_break_even")
    break_even_date: Optional[str] = Field(None, description="Date when break-even is reached (ISO 8601)")
    profit_hours: Optional[float] = Field(None, description="Hours above break-even (if applicable)")


class BreakEvenProjectionResponse(BaseModel):
    """Response schema for temporal projection"""
    current_status: dict = Field(..., description="Current status")
    projection: List[MonthProjection] = Field(..., description="Monthly projections")
    break_even_date: Optional[str] = Field(None, description="Projected break-even date (ISO 8601)")
    months_to_break_even: Optional[int] = Field(None, description="Months until break-even")
```

---

### 2. ✅ Service (`backend/app/services/break_even_service.py`)

**Estado:** ❌ No implementado

**Implementación Requerida:**

```python
"""
Break-Even Service - Business logic for break-even calculations
"""
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from decimal import Decimal
import logging

from app.core.calculations import calculate_blended_cost_rate
from app.core.money import Money, sum_money
from app.repositories.factory import RepositoryFactory
from app.models.project import Project, Quote, QuoteItem
from app.models.team import TeamMember
from app.models.cost import CostFixed
from app.models.service import Service

logger = logging.getLogger(__name__)


class BreakEvenService:
    """Service for break-even point calculations"""
    
    def __init__(self, db: AsyncSession, organization_id: int):
        """
        Initialize BreakEvenService
        
        Args:
            db: Database session
            organization_id: Organization ID for tenant scoping
        """
        self.db = db
        self.organization_id = organization_id
        self.cost_repo = RepositoryFactory.create_cost_repository(db, organization_id)
        self.team_repo = RepositoryFactory.create_team_repository(db, organization_id)
        self.project_repo = RepositoryFactory.create_project_repository(db, organization_id)
        self.service_repo = RepositoryFactory.create_service_repository(db, organization_id)
    
    async def get_current_analysis(
        self,
        currency: str = "USD",
        period: str = "monthly",
        include_projected: bool = True
    ) -> Dict[str, Any]:
        """
        Get current break-even analysis
        
        Args:
            currency: Currency code for calculations
            period: Period type (monthly, quarterly, annual)
            include_projected: Whether to include projected break-even date
        
        Returns:
            Dictionary with break-even analysis data
        """
        # Get total fixed costs
        total_fixed_costs = await self._get_total_fixed_costs(currency)
        
        # Get BCR (Blended Cost Rate)
        bcr = await calculate_blended_cost_rate(
            self.db,
            primary_currency=currency,
            tenant_id=self.organization_id
        )
        
        # Get total billable hours available
        total_billable_hours = await self._get_total_billable_hours()
        
        # Calculate break-even hours
        if bcr > 0:
            break_even_hours = float(total_fixed_costs / bcr)
        else:
            break_even_hours = 0.0
        
        # Get current allocated hours
        current_allocated_hours = await self._get_current_allocated_hours()
        
        # Calculate hours to break even
        hours_to_break_even = max(0.0, break_even_hours - current_allocated_hours)
        
        # Calculate safety margin
        safety_margin_hours = current_allocated_hours - break_even_hours if current_allocated_hours > break_even_hours else 0.0
        safety_margin_percentage = (safety_margin_hours / break_even_hours * 100) if break_even_hours > 0 else 0.0
        
        # Get average billable rate and margin
        average_billable_rate, average_margin = await self._get_average_billable_rate_and_margin(currency)
        
        # Calculate break-even revenue
        if average_billable_rate > 0:
            break_even_revenue = Decimal(str(break_even_hours)) * Decimal(str(average_billable_rate))
        else:
            break_even_revenue = Decimal('0')
        
        # Get current projected revenue
        current_projected_revenue = await self._get_current_projected_revenue(currency)
        
        # Calculate revenue to break even
        revenue_to_break_even = max(Decimal('0'), break_even_revenue - current_projected_revenue)
        
        # Calculate utilization rates
        current_utilization_rate = (current_allocated_hours / total_billable_hours * 100) if total_billable_hours > 0 else 0.0
        break_even_utilization_rate = (break_even_hours / total_billable_hours * 100) if total_billable_hours > 0 else 0.0
        
        # Calculate operating leverage
        operating_leverage = self._calculate_operating_leverage(total_fixed_costs, current_projected_revenue)
        
        # Determine status
        status, status_message = self._determine_status(
            current_allocated_hours,
            break_even_hours,
            hours_to_break_even
        )
        
        # Calculate projection if requested
        months_to_break_even = None
        projected_break_even_date = None
        if include_projected and hours_to_break_even > 0:
            months_to_break_even, projected_break_even_date = await self._calculate_projected_break_even_date(
                current_allocated_hours,
                break_even_hours
            )
        
        return {
            "period": period,
            "currency": currency,
            "total_fixed_costs": total_fixed_costs,
            "total_costs": total_fixed_costs,  # For now, same as fixed costs
            "total_billable_hours_available": total_billable_hours,
            "break_even_hours": break_even_hours,
            "current_allocated_hours": current_allocated_hours,
            "hours_to_break_even": hours_to_break_even,
            "safety_margin_hours": safety_margin_hours,
            "safety_margin_percentage": safety_margin_percentage,
            "break_even_revenue": break_even_revenue,
            "current_projected_revenue": current_projected_revenue,
            "revenue_to_break_even": revenue_to_break_even,
            "average_margin": average_margin,
            "operating_leverage": operating_leverage,
            "current_utilization_rate": current_utilization_rate,
            "break_even_utilization_rate": break_even_utilization_rate,
            "status": status,
            "status_message": status_message,
            "months_to_break_even": months_to_break_even,
            "projected_break_even_date": projected_break_even_date
        }
    
    async def simulate_scenarios(
        self,
        scenarios: List[Dict[str, Any]],
        currency: str = "USD"
    ) -> Dict[str, Any]:
        """
        Simulate break-even scenarios with different parameters
        
        Args:
            scenarios: List of scenario configurations
            currency: Currency for calculations
        
        Returns:
            Dictionary with base scenario and simulated scenarios
        """
        # Get base scenario
        base_analysis = await self.get_current_analysis(currency=currency, include_projected=False)
        
        base_scenario = {
            "break_even_hours": base_analysis["break_even_hours"],
            "break_even_revenue": base_analysis["break_even_revenue"],
            "current_allocated_hours": base_analysis["current_allocated_hours"],
            "hours_to_break_even": base_analysis["hours_to_break_even"]
        }
        
        # Simulate each scenario
        scenario_results = []
        for scenario_config in scenarios:
            result = await self._simulate_single_scenario(
                scenario_config,
                base_analysis,
                currency
            )
            scenario_results.append(result)
        
        return {
            "base_scenario": base_scenario,
            "scenarios": scenario_results
        }
    
    async def get_projection(
        self,
        months_ahead: int = 12,
        growth_rate: float = 0.0,
        currency: str = "USD"
    ) -> Dict[str, Any]:
        """
        Get temporal projection of break-even point
        
        Args:
            months_ahead: Number of months to project
            growth_rate: Monthly growth rate (0.0 = no growth, 0.05 = 5% growth)
            currency: Currency for calculations
        
        Returns:
            Dictionary with projection data
        """
        # Get current analysis
        current_analysis = await self.get_current_analysis(currency=currency, include_projected=False)
        
        current_status = {
            "allocated_hours": current_analysis["current_allocated_hours"],
            "break_even_hours": current_analysis["break_even_hours"],
            "hours_to_break_even": current_analysis["hours_to_break_even"]
        }
        
        # Generate monthly projections
        projection = []
        current_hours = current_analysis["current_allocated_hours"]
        break_even_hours = current_analysis["break_even_hours"]
        break_even_reached = False
        break_even_date = None
        months_to_break_even = None
        
        for i in range(months_ahead):
            # Calculate projected hours for this month
            if growth_rate != 0:
                current_hours = current_hours * (1 + growth_rate)
            
            month_date = date.today() + relativedelta(months=i+1)
            month_str = month_date.strftime("%Y-%m")
            
            hours_to_break_even = max(0.0, break_even_hours - current_hours)
            
            # Determine status
            if current_hours >= break_even_hours:
                status = "above_break_even"
                profit_hours = current_hours - break_even_hours
                if not break_even_reached:
                    break_even_reached = True
                    break_even_date = month_date.isoformat()
                    months_to_break_even = i + 1
            elif abs(current_hours - break_even_hours) < 0.01:  # Within 0.01 hours
                status = "at_break_even"
                profit_hours = 0.0
                if not break_even_reached:
                    break_even_reached = True
                    break_even_date = month_date.isoformat()
                    months_to_break_even = i + 1
            else:
                status = "below_break_even"
                profit_hours = None
            
            projection.append({
                "month": month_str,
                "allocated_hours": round(current_hours, 2),
                "break_even_hours": break_even_hours,
                "hours_to_break_even": round(hours_to_break_even, 2),
                "status": status,
                "break_even_date": break_even_date if status in ["at_break_even", "above_break_even"] else None,
                "profit_hours": round(profit_hours, 2) if profit_hours is not None else None
            })
        
        return {
            "current_status": current_status,
            "projection": projection,
            "break_even_date": break_even_date,
            "months_to_break_even": months_to_break_even
        }
    
    # Private helper methods
    
    async def _get_total_fixed_costs(self, currency: str) -> Decimal:
        """Get total fixed costs in specified currency"""
        costs = await self.cost_repo.get_all_active()
        total = Decimal('0')
        
        for cost in costs:
            # Normalize to target currency (simplified - use existing logic)
            # TODO: Use Money and currency conversion
            total += Decimal(str(cost.amount_monthly))
        
        return total
    
    async def _get_total_billable_hours(self) -> float:
        """Get total billable hours available from team"""
        team_members = await self.team_repo.get_all_active()
        total_hours = 0.0
        
        for member in team_members:
            total_hours += float(member.billable_hours_per_month or 0)
        
        return total_hours
    
    async def _get_current_allocated_hours(self) -> float:
        """Get current allocated hours from active projects"""
        # Get active projects with quotes
        projects = await self.project_repo.get_all_with_quotes()
        total_hours = 0.0
        
        for project in projects:
            if project.status in ["active", "in_progress", "pending"]:
                # Get latest quote
                if project.quotes:
                    latest_quote = max(project.quotes, key=lambda q: q.version)
                    for item in latest_quote.items:
                        if item.estimated_hours:
                            total_hours += float(item.estimated_hours)
        
        return total_hours
    
    async def _get_average_billable_rate_and_margin(self, currency: str) -> tuple[float, float]:
        """Get average billable rate and margin from services"""
        services = await self.service_repo.get_all_active()
        
        if not services:
            return 0.0, 0.0
        
        total_rate = 0.0
        total_margin = 0.0
        count = 0
        
        for service in services:
            # Calculate billable rate from BCR and margin
            # This is simplified - actual calculation may be more complex
            if service.default_margin_target:
                total_margin += float(service.default_margin_target)
                count += 1
        
        average_margin = (total_margin / count * 100) if count > 0 else 0.0
        
        # Get BCR to calculate average rate
        bcr = await calculate_blended_cost_rate(
            self.db,
            primary_currency=currency,
            tenant_id=self.organization_id
        )
        
        # Calculate average billable rate: BCR / (1 - margin)
        if average_margin > 0 and average_margin < 100:
            average_rate = float(bcr) / (1 - (average_margin / 100))
        else:
            average_rate = float(bcr)
        
        return average_rate, average_margin
    
    async def _get_current_projected_revenue(self, currency: str) -> Decimal:
        """Get current projected revenue from active projects"""
        # Simplified - sum up projected revenue from active projects
        # TODO: Implement proper calculation
        return Decimal('0')
    
    def _calculate_operating_leverage(self, fixed_costs: Decimal, revenue: Decimal) -> float:
        """Calculate operating leverage"""
        if revenue > 0:
            return float(fixed_costs / revenue)
        return 0.0
    
    def _determine_status(
        self,
        current_hours: float,
        break_even_hours: float,
        hours_to_break_even: float
    ) -> tuple[str, str]:
        """Determine break-even status"""
        if abs(current_hours - break_even_hours) < 0.01:  # Within 0.01 hours
            return "at_break_even", "En el punto de equilibrio"
        elif current_hours > break_even_hours:
            return "above_break_even", f"Por encima del equilibrio ({current_hours - break_even_hours:.1f}h de margen)"
        else:
            return "below_break_even", f"Por debajo del equilibrio (faltan {hours_to_break_even:.1f}h)"
    
    async def _calculate_projected_break_even_date(
        self,
        current_hours: float,
        break_even_hours: float
    ) -> tuple[Optional[int], Optional[str]]:
        """Calculate projected break-even date based on current rate"""
        if current_hours >= break_even_hours:
            return None, None
        
        # Calculate average monthly growth (simplified)
        # TODO: Use actual historical data
        hours_needed = break_even_hours - current_hours
        avg_monthly_hours = 33.0  # Simplified - should calculate from history
        
        if avg_monthly_hours > 0:
            months = int(hours_needed / avg_monthly_hours) + 1
            projected_date = date.today() + relativedelta(months=months)
            return months, projected_date.isoformat()
        
        return None, None
    
    async def _simulate_single_scenario(
        self,
        scenario_config: Dict[str, Any],
        base_analysis: Dict[str, Any],
        currency: str
    ) -> Dict[str, Any]:
        """Simulate a single scenario"""
        # Apply multipliers and adjustments
        adjusted_bcr = float(base_analysis.get("break_even_hours", 0)) * scenario_config.get("bcr_multiplier", 1.0)
        adjusted_fixed_costs = Decimal(str(base_analysis.get("total_fixed_costs", 0))) + Decimal(str(scenario_config.get("fixed_costs_adjustment", 0)))
        
        # Recalculate break-even hours with adjusted parameters
        if adjusted_bcr > 0:
            new_break_even_hours = float(adjusted_fixed_costs / Decimal(str(adjusted_bcr)))
        else:
            new_break_even_hours = base_analysis["break_even_hours"]
        
        # Calculate impact
        hours_change = new_break_even_hours - base_analysis["break_even_hours"]
        impact_percentage = (hours_change / base_analysis["break_even_hours"] * 100) if base_analysis["break_even_hours"] > 0 else 0.0
        
        # Calculate revenue impact (simplified)
        revenue_change = Decimal(str(hours_change)) * Decimal(str(base_analysis.get("break_even_revenue", 0))) / Decimal(str(base_analysis.get("break_even_hours", 1)))
        
        return {
            "name": scenario_config["name"],
            "break_even_hours": new_break_even_hours,
            "break_even_revenue": base_analysis["break_even_revenue"],  # Simplified
            "hours_to_break_even": max(0.0, new_break_even_hours - base_analysis["current_allocated_hours"]),
            "impact": {
                "hours_change": hours_change,
                "revenue_change": str(revenue_change),
                "impact_percentage": impact_percentage
            }
        }
```

---

### 3. ✅ View (`backend/app/views/break_even_view.py`)

**Estado:** ❌ No implementado

**Implementación Requerida:**

```python
"""
Break-Even View - Data transformation for break-even responses
"""
from typing import Dict, Any
from decimal import Decimal

from app.views.base import BaseView
from app.schemas.break_even import (
    BreakEvenAnalysisResponse,
    BreakEvenScenariosResponse,
    BreakEvenProjectionResponse,
    ScenarioResult,
    MonthProjection
)


class BreakEvenView(BaseView):
    """View for transforming break-even data to response schemas"""
    
    def to_analysis_response(self, data: Dict[str, Any]) -> BreakEvenAnalysisResponse:
        """
        Transform service data to BreakEvenAnalysisResponse
        
        Args:
            data: Dictionary from BreakEvenService.get_current_analysis()
        
        Returns:
            BreakEvenAnalysisResponse instance
        """
        return BreakEvenAnalysisResponse(
            period=data["period"],
            currency=data["currency"],
            total_fixed_costs=str(data["total_fixed_costs"]),
            total_costs=str(data["total_costs"]),
            total_billable_hours_available=data["total_billable_hours_available"],
            break_even_hours=data["break_even_hours"],
            current_allocated_hours=data["current_allocated_hours"],
            hours_to_break_even=data["hours_to_break_even"],
            safety_margin_hours=data["safety_margin_hours"],
            safety_margin_percentage=data["safety_margin_percentage"],
            break_even_revenue=str(data["break_even_revenue"]),
            current_projected_revenue=str(data["current_projected_revenue"]),
            revenue_to_break_even=str(data["revenue_to_break_even"]),
            average_margin=data["average_margin"],
            operating_leverage=data["operating_leverage"],
            current_utilization_rate=data["current_utilization_rate"],
            break_even_utilization_rate=data["break_even_utilization_rate"],
            status=data["status"],
            status_message=data["status_message"],
            months_to_break_even=data.get("months_to_break_even"),
            projected_break_even_date=data.get("projected_break_even_date")
        )
    
    def to_scenarios_response(self, data: Dict[str, Any]) -> BreakEvenScenariosResponse:
        """
        Transform service data to BreakEvenScenariosResponse
        
        Args:
            data: Dictionary from BreakEvenService.simulate_scenarios()
        
        Returns:
            BreakEvenScenariosResponse instance
        """
        scenarios = [
            ScenarioResult(
                name=scenario["name"],
                break_even_hours=scenario["break_even_hours"],
                break_even_revenue=str(scenario["break_even_revenue"]),
                hours_to_break_even=scenario["hours_to_break_even"],
                impact=scenario["impact"]
            )
            for scenario in data["scenarios"]
        ]
        
        return BreakEvenScenariosResponse(
            base_scenario=data["base_scenario"],
            scenarios=scenarios
        )
    
    def to_projection_response(self, data: Dict[str, Any]) -> BreakEvenProjectionResponse:
        """
        Transform service data to BreakEvenProjectionResponse
        
        Args:
            data: Dictionary from BreakEvenService.get_projection()
        
        Returns:
            BreakEvenProjectionResponse instance
        """
        projections = [
            MonthProjection(
                month=proj["month"],
                allocated_hours=proj["allocated_hours"],
                break_even_hours=proj["break_even_hours"],
                hours_to_break_even=proj["hours_to_break_even"],
                status=proj["status"],
                break_even_date=proj.get("break_even_date"),
                profit_hours=proj.get("profit_hours")
            )
            for proj in data["projection"]
        ]
        
        return BreakEvenProjectionResponse(
            current_status=data["current_status"],
            projection=projections,
            break_even_date=data.get("break_even_date"),
            months_to_break_even=data.get("months_to_break_even")
        )
```

---

### 4. ✅ Controller (`backend/app/controllers/break_even_controller.py`)

**Estado:** ❌ No implementado

**Implementación Requerida:**

```python
"""
Break-Even Controller - HTTP request handling for break-even analysis
"""
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.controllers.base import BaseController
from app.services.break_even_service import BreakEvenService
from app.views.break_even_view import BreakEvenView
from app.schemas.break_even import (
    BreakEvenAnalysisResponse,
    BreakEvenScenarioRequest,
    BreakEvenScenariosResponse,
    BreakEvenProjectionResponse
)


class BreakEvenController(BaseController):
    """
    Controller for handling break-even HTTP requests
    
    Responsibilities:
    - HTTP request validation
    - Delegation to BreakEvenService
    - Response formatting via BreakEvenView
    - Error handling
    """
    
    def __init__(
        self,
        db: AsyncSession,
        tenant,
        current_user
    ):
        """
        Initialize BreakEvenController
        
        Args:
            db: Database session
            tenant: Tenant context
            current_user: Current authenticated user
        """
        super().__init__(db, tenant, current_user)
        self.break_even_service = BreakEvenService(db, self.organization_id)
        self.break_even_view = BreakEvenView()
    
    async def get_current_analysis(
        self,
        currency: Optional[str] = None,
        period: str = "monthly",
        include_projected: bool = True
    ) -> BreakEvenAnalysisResponse:
        """
        Get current break-even analysis
        
        Args:
            currency: Currency code (defaults to organization currency)
            period: Period type (monthly, quarterly, annual)
            include_projected: Whether to include projected break-even date
        
        Returns:
            BreakEvenAnalysisResponse
        
        Raises:
            HTTPException: If analysis fails
        """
        try:
            # Use organization currency if not specified
            if not currency:
                currency = self.tenant.organization.primary_currency or "USD"
            
            # Validate period
            if period not in ["monthly", "quarterly", "annual"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid period: {period}. Must be 'monthly', 'quarterly', or 'annual'"
                )
            
            # Get analysis from service
            analysis_data = await self.break_even_service.get_current_analysis(
                currency=currency,
                period=period,
                include_projected=include_projected
            )
            
            # Transform to response
            return self.break_even_view.to_analysis_response(analysis_data)
        
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            self.logger.error(f"Error getting break-even analysis: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error calculating break-even analysis"
            )
    
    async def simulate_scenarios(
        self,
        request: BreakEvenScenarioRequest
    ) -> BreakEvenScenariosResponse:
        """
        Simulate break-even scenarios
        
        Args:
            request: BreakEvenScenarioRequest with scenarios to simulate
        
        Returns:
            BreakEvenScenariosResponse
        
        Raises:
            HTTPException: If simulation fails
        """
        try:
            # Use organization currency if not specified
            currency = request.currency or self.tenant.organization.primary_currency or "USD"
            
            # Convert scenarios to dict format
            scenarios_dict = [
                {
                    "name": scenario.name,
                    "bcr_multiplier": scenario.bcr_multiplier,
                    "fixed_costs_adjustment": scenario.fixed_costs_adjustment,
                    "average_margin_adjustment": scenario.average_margin_adjustment
                }
                for scenario in request.scenarios
            ]
            
            # Simulate scenarios
            scenarios_data = await self.break_even_service.simulate_scenarios(
                scenarios=scenarios_dict,
                currency=currency
            )
            
            # Transform to response
            return self.break_even_view.to_scenarios_response(scenarios_data)
        
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            self.logger.error(f"Error simulating scenarios: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error simulating break-even scenarios"
            )
    
    async def get_projection(
        self,
        months_ahead: int = 12,
        growth_rate: float = 0.0,
        currency: Optional[str] = None
    ) -> BreakEvenProjectionResponse:
        """
        Get temporal projection of break-even point
        
        Args:
            months_ahead: Number of months to project (1-36)
            growth_rate: Monthly growth rate (-0.5 to 2.0)
            currency: Currency code (defaults to organization currency)
        
        Returns:
            BreakEvenProjectionResponse
        
        Raises:
            HTTPException: If projection fails
        """
        try:
            # Validate parameters
            if months_ahead < 1 or months_ahead > 36:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="months_ahead must be between 1 and 36"
                )
            
            if growth_rate < -0.5 or growth_rate > 2.0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="growth_rate must be between -0.5 and 2.0"
                )
            
            # Use organization currency if not specified
            if not currency:
                currency = self.tenant.organization.primary_currency or "USD"
            
            # Get projection
            projection_data = await self.break_even_service.get_projection(
                months_ahead=months_ahead,
                growth_rate=growth_rate,
                currency=currency
            )
            
            # Transform to response
            return self.break_even_view.to_projection_response(projection_data)
        
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            self.logger.error(f"Error getting projection: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error calculating break-even projection"
            )
```

---

### 5. ✅ Endpoints (`backend/app/api/v1/endpoints/break_even.py`)

**Estado:** ❌ No implementado

**Implementación Requerida:**

```python
"""
Break-Even Point endpoints
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.tenant import get_tenant_context, TenantContext
from app.core.permission_middleware import require_view_analytics
from app.models.user import User
from app.controllers.break_even_controller import BreakEvenController
from app.schemas.break_even import (
    BreakEvenAnalysisResponse,
    BreakEvenScenarioRequest,
    BreakEvenScenariosResponse,
    BreakEvenProjectionResponse
)

router = APIRouter()


@router.get(
    "",
    response_model=BreakEvenAnalysisResponse,
    summary="Get break-even analysis"
)
async def get_break_even_analysis(
    currency: Optional[str] = Query(None, description="Currency code (USD, COP, EUR, ARS)"),
    period: str = Query("monthly", description="Period: monthly, quarterly, or annual"),
    include_projected: bool = Query(True, description="Include projected break-even date"),
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(require_view_analytics),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current break-even analysis
    
    Calculates:
    - Total fixed costs
    - Break-even hours and revenue
    - Current allocated hours
    - Utilization rates
    - Status (above/at/below break-even)
    - Projected break-even date (optional)
    
    **Permissions:**
    - Requires `can_view_analytics` permission
    """
    controller = BreakEvenController(db, tenant, current_user)
    return await controller.get_current_analysis(
        currency=currency,
        period=period,
        include_projected=include_projected
    )


@router.post(
    "/scenarios",
    response_model=BreakEvenScenariosResponse,
    summary="Simulate break-even scenarios"
)
async def simulate_break_even_scenarios(
    request: BreakEvenScenarioRequest,
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(require_view_analytics),
    db: AsyncSession = Depends(get_db)
):
    """
    Simulate break-even scenarios with different parameters
    
    Allows testing impact of:
    - BCR changes (multiplier)
    - Fixed costs adjustments
    - Average margin adjustments
    
    **Permissions:**
    - Requires `can_view_analytics` permission
    """
    controller = BreakEvenController(db, tenant, current_user)
    return await controller.simulate_scenarios(request)


@router.get(
    "/projection",
    response_model=BreakEvenProjectionResponse,
    summary="Get break-even temporal projection"
)
async def get_break_even_projection(
    months_ahead: int = Query(12, ge=1, le=36, description="Number of months to project"),
    growth_rate: float = Query(0.0, ge=-0.5, le=2.0, description="Monthly growth rate (-0.5 to 2.0)"),
    currency: Optional[str] = Query(None, description="Currency code"),
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(require_view_analytics),
    db: AsyncSession = Depends(get_db)
):
    """
    Get temporal projection of break-even point
    
    Projects when break-even will be reached based on:
    - Current allocated hours
    - Monthly growth rate (optional)
    - Break-even hours requirement
    
    **Permissions:**
    - Requires `can_view_analytics` permission
    """
    controller = BreakEvenController(db, tenant, current_user)
    return await controller.get_projection(
        months_ahead=months_ahead,
        growth_rate=growth_rate,
        currency=currency
    )
```

---

### 6. ✅ Router Registration (`backend/app/api/v1/router.py`)

**Estado:** ⚠️ Pendiente de agregar

**Modificación Requerida:**

```python
# Agregar import
from app.api.v1.endpoints import break_even

# Agregar router (después de insights)
api_router.include_router(break_even.router, prefix="/analytics/break-even", tags=["break-even"])
```

---

## 📝 Plan de Implementación por Fases

### Fase 1: Análisis Actual (Prioridad Alta)

**Objetivo:** Implementar endpoint básico de análisis de break-even

**Tareas:**
1. ✅ Crear `schemas/break_even.py` con `BreakEvenAnalysisResponse`
2. ✅ Crear `services/break_even_service.py` con método `get_current_analysis()`
3. ✅ Implementar métodos helper:
   - `_get_total_fixed_costs()`
   - `_get_total_billable_hours()`
   - `_get_current_allocated_hours()`
   - `_get_average_billable_rate_and_margin()`
   - `_determine_status()`
4. ✅ Crear `views/break_even_view.py` con `to_analysis_response()`
5. ✅ Crear `controllers/break_even_controller.py` con `get_current_analysis()`
6. ✅ Crear `endpoints/break_even.py` con endpoint `GET /analytics/break-even`
7. ✅ Registrar router en `router.py`

**Estimación:** 2-3 días

---

### Fase 2: Simulación de Escenarios (Prioridad Media)

**Objetivo:** Implementar simulación de escenarios financieros

**Tareas:**
1. ✅ Agregar schemas: `BreakEvenScenarioRequest`, `BreakEvenScenariosResponse`, `ScenarioConfig`, `ScenarioResult`
2. ✅ Agregar método `simulate_scenarios()` en `BreakEvenService`
3. ✅ Implementar `_simulate_single_scenario()`
4. ✅ Agregar método `simulate_scenarios()` en `BreakEvenController`
5. ✅ Agregar método `to_scenarios_response()` en `BreakEvenView`
6. ✅ Agregar endpoint `POST /analytics/break-even/scenarios`

**Estimación:** 1-2 días

---

### Fase 3: Proyección Temporal (Prioridad Media)

**Objetivo:** Implementar proyección temporal de break-even

**Tareas:**
1. ✅ Agregar schemas: `BreakEvenProjectionResponse`, `MonthProjection`
2. ✅ Agregar método `get_projection()` en `BreakEvenService`
3. ✅ Implementar cálculo de proyección mes a mes
4. ✅ Agregar método `get_projection()` en `BreakEvenController`
5. ✅ Agregar método `to_projection_response()` en `BreakEvenView`
6. ✅ Agregar endpoint `GET /analytics/break-even/projection`

**Estimación:** 1-2 días

---

## ✅ Checklist de Implementación

### Schemas (Pydantic)
- [ ] `BreakEvenAnalysisResponse`
- [ ] `BreakEvenScenarioRequest`
- [ ] `BreakEvenScenariosResponse`
- [ ] `BreakEvenProjectionResponse`
- [ ] `ScenarioConfig`
- [ ] `ScenarioResult`
- [ ] `MonthProjection`

### Services (Lógica de Negocio)
- [ ] `BreakEvenService.__init__()`
- [ ] `BreakEvenService.get_current_analysis()`
- [ ] `BreakEvenService._get_total_fixed_costs()`
- [ ] `BreakEvenService._get_total_billable_hours()`
- [ ] `BreakEvenService._get_current_allocated_hours()`
- [ ] `BreakEvenService._get_average_billable_rate_and_margin()`
- [ ] `BreakEvenService._get_current_projected_revenue()`
- [ ] `BreakEvenService._calculate_operating_leverage()`
- [ ] `BreakEvenService._determine_status()`
- [ ] `BreakEvenService._calculate_projected_break_even_date()`
- [ ] `BreakEvenService.simulate_scenarios()`
- [ ] `BreakEvenService._simulate_single_scenario()`
- [ ] `BreakEvenService.get_projection()`

### Views (Transformación de Datos)
- [ ] `BreakEvenView.to_analysis_response()`
- [ ] `BreakEvenView.to_scenarios_response()`
- [ ] `BreakEvenView.to_projection_response()`

### Controllers (Manejo HTTP)
- [ ] `BreakEvenController.__init__()`
- [ ] `BreakEvenController.get_current_analysis()`
- [ ] `BreakEvenController.simulate_scenarios()`
- [ ] `BreakEvenController.get_projection()`

### Endpoints (API REST)
- [ ] `GET /api/v1/analytics/break-even`
- [ ] `POST /api/v1/analytics/break-even/scenarios`
- [ ] `GET /api/v1/analytics/break-even/projection`

### Router
- [ ] Importar `break_even` en `router.py`
- [ ] Registrar router con prefix `/analytics/break-even`

### Tests
- [ ] Tests unitarios para `BreakEvenService`
- [ ] Tests de integración para endpoints
- [ ] Tests de validación de schemas

---

## 🔗 Dependencias y Reutilización

### Código Existente Reutilizable:

1. **`app.core.calculations.calculate_blended_cost_rate()`**
   - ✅ Ya existe
   - ✅ Calcula BCR correctamente
   - ✅ Soporta tenant scoping

2. **`CostRepository`**
   - ✅ Ya existe
   - ✅ Método `get_all_active()` disponible

3. **`TeamRepository`**
   - ✅ Ya existe
   - ✅ Método `get_all_active()` disponible

4. **`ProjectRepository`**
   - ✅ Ya existe
   - ✅ Método `get_all_with_quotes()` disponible

5. **`ServiceRepository`**
   - ✅ Ya existe
   - ✅ Método `get_all_active()` disponible

6. **`app.core.money.Money`**
   - ✅ Ya existe
   - ✅ Para cálculos precisos con moneda

---

## 🎯 Consideraciones de Implementación

### Precisión Financiera:
- ✅ Usar `Decimal` para todos los cálculos financieros
- ✅ Usar `Money` para operaciones con moneda
- ✅ Serializar `Decimal` como string en respuestas API

### Tenant Scoping:
- ✅ Todos los repositorios ya tienen tenant scoping
- ✅ Usar `organization_id` del tenant context

### Permisos:
- ✅ Usar `require_view_analytics` para todos los endpoints
- ✅ Verificar permisos en controller si es necesario

### Caching:
- ⚠️ Considerar cachear análisis de break-even (TTL: 5 minutos)
- ⚠️ Invalidar cache al cambiar costos fijos o equipo

### Validaciones:
- ✅ Validar parámetros en controller
- ✅ Validar schemas con Pydantic
- ✅ Validar rangos de valores (months_ahead, growth_rate)

---

## 📚 Referencias

### Documentos Relacionados:
- [2026-02-07-ANALISIS_BREAK_EVEN_BACKEND.md](./2026-02-07-ANALISIS_BREAK_EVEN_BACKEND.md) - Análisis de estado actual
- `UI_REQUIREMENTS_BREAK_EVEN_POINT.md` - Requerimientos de frontend (si existe)
- `EQUIPMENT_AMORTIZATION_PLAN_MVC.md` - Ejemplo de implementación MVC

### Código de Referencia:
- `backend/app/services/insight_service.py` - Ejemplo de service
- `backend/app/controllers/insight_controller.py` - Ejemplo de controller
- `backend/app/views/insight_view.py` - Ejemplo de view
- `backend/app/core/calculations.py` - Funciones de cálculo existentes

---

## 🚀 Próximos Pasos

1. **Revisar este plan** con el equipo
2. **Crear branch:** `feature/break-even-backend`
3. **Implementar Fase 1** (Análisis Actual)
4. **Testing** de Fase 1
5. **Implementar Fase 2** (Simulación)
6. **Implementar Fase 3** (Proyección)
7. **Testing completo**
8. **Code review**
9. **Merge a main**

---

**Última actualización:** 2026-01-25  
**Versión:** 1.0  
**Estado:** Pendiente de Implementación
