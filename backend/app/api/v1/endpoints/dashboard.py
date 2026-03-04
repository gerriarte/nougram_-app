"""
Dashboard endpoints for KPIs and statistics
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, case
from sqlalchemy.orm import selectinload
from datetime import datetime, date, timedelta
from typing import Optional
from decimal import Decimal

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.tenant import get_tenant_context, TenantContext
from app.core.permission_middleware import require_view_analytics
from app.core.permissions import get_user_role
from app.models.user import User
from app.models.organization import Organization
from app.models.project import Project, Quote
from app.models.team import TeamMember
from app.models.cost import CostFixed
from app.core.calculations import calculate_blended_cost_rate
from app.core.currency import normalize_to_primary_currency
from app.core.money import Money
from app.services.operational_cost_service import get_current_month_operational_costs
from app.schemas.operational_cost import OperationalCostPayloadSchema

router = APIRouter()

# Operational dashboard: owner, admin_financiero, or super_admin only (plan: strict permissions)
ALLOWED_OPERATIONAL_ROLES = {"owner", "admin_financiero", "super_admin"}


async def require_operational_dashboard(
    current_user: User = Depends(get_current_user),
) -> User:
    """Require owner, admin_financiero, or super_admin for operational cost dashboard."""
    role = get_user_role(current_user)
    if role not in ALLOWED_OPERATIONAL_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint requires owner, admin_financiero, or super_admin role.",
        )
    return current_user


@router.get("/kpis")
async def get_dashboard_kpis(
    period: Optional[str] = Query("month", description="Period: 'month', 'quarter', 'year'"),
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(require_view_analytics),
    db: AsyncSession = Depends(get_db)
):
    """
    Get dashboard KPIs for widgets
    
    Returns:
    - totalRevenue: Total revenue from accepted quotes (Won projects)
    - totalRevenueChange: % change vs previous period
    - activeQuotesCount: Number of active quotes (not draft, not closed)
    - activeQuotesChange: % change vs previous period
    - closeRate: Win rate percentage
    - closeRateChange: % change vs previous period
    - averageTicket: Average ticket size
    - averageTicketChange: % change vs previous period
    
    **Permissions:**
    - Requires `can_view_analytics` permission
    """
    from app.core.cache import get_cache
    
    # Validate period
    valid_periods = ['month', 'quarter', 'year']
    if period not in valid_periods:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid period. Must be one of: {', '.join(valid_periods)}"
        )
    
    # Check cache
    cache = get_cache()
    cache_key = f"dashboard_kpis:{tenant.organization_id}:{period}"
    cached_data = cache.get(cache_key)
    if cached_data is not None:
        return cached_data
    
    # Calculate date range for current period
    today = date.today()
    if period == 'month':
        period_start = today.replace(day=1)
        period_end = today
        prev_period_start = (period_start - timedelta(days=1)).replace(day=1)
        prev_period_end = period_start - timedelta(days=1)
    elif period == 'quarter':
        quarter = (today.month - 1) // 3
        period_start = date(today.year, quarter * 3 + 1, 1)
        period_end = today
        prev_period_start = date(period_start.year, period_start.month - 3, 1) if period_start.month > 3 else date(period_start.year - 1, 10, 1)
        prev_period_end = period_start - timedelta(days=1)
    else:  # year
        period_start = date(today.year, 1, 1)
        period_end = today
        prev_period_start = date(today.year - 1, 1, 1)
        prev_period_end = date(today.year - 1, 12, 31)
    
    # Build filters for current period
    current_filters = [
        Project.organization_id == tenant.organization_id,
        Project.deleted_at.is_(None),
        Project.created_at >= datetime.combine(period_start, datetime.min.time()),
        Project.created_at <= datetime.combine(period_end, datetime.max.time())
    ]
    
    # Build filters for previous period
    prev_filters = [
        Project.organization_id == tenant.organization_id,
        Project.deleted_at.is_(None),
        Project.created_at >= datetime.combine(prev_period_start, datetime.min.time()),
        Project.created_at <= datetime.combine(prev_period_end, datetime.max.time())
    ]
    
    # 1. Total Revenue (from Won projects)
    current_revenue_query = (
        select(func.sum(Quote.total_client_price))
        .join(Project, Quote.project_id == Project.id)
        .where(and_(*current_filters, Project.status == "Won"))
    )
    current_revenue_result = await db.execute(current_revenue_query)
    current_revenue = float(current_revenue_result.scalar() or 0)
    
    prev_revenue_query = (
        select(func.sum(Quote.total_client_price))
        .join(Project, Quote.project_id == Project.id)
        .where(and_(*prev_filters, Project.status == "Won"))
    )
    prev_revenue_result = await db.execute(prev_revenue_query)
    prev_revenue = float(prev_revenue_result.scalar() or 0)
    
    total_revenue_change = ((current_revenue - prev_revenue) / prev_revenue * 100) if prev_revenue > 0 else 0.0
    
    # 2. Active Quotes Count (not draft, not Won, not Lost)
    current_active_query = (
        select(func.count(Quote.id))
        .join(Project, Quote.project_id == Project.id)
        .where(and_(
            *current_filters,
            Project.status.in_(["Sent"])  # Active quotes are those sent but not closed
        ))
    )
    current_active_result = await db.execute(current_active_query)
    current_active_count = current_active_result.scalar() or 0
    
    prev_active_query = (
        select(func.count(Quote.id))
        .join(Project, Quote.project_id == Project.id)
        .where(and_(
            *prev_filters,
            Project.status.in_(["Sent"])
        ))
    )
    prev_active_result = await db.execute(prev_active_query)
    prev_active_count = prev_active_result.scalar() or 0
    
    active_quotes_change = ((current_active_count - prev_active_count) / prev_active_count * 100) if prev_active_count > 0 else 0.0
    
    # 3. Close Rate (Win rate: Won / (Won + Lost))
    won_query = select(func.count(Project.id)).where(and_(*current_filters, Project.status == "Won"))
    won_result = await db.execute(won_query)
    won_count = won_result.scalar() or 0
    
    lost_query = select(func.count(Project.id)).where(and_(*current_filters, Project.status == "Lost"))
    lost_result = await db.execute(lost_query)
    lost_count = lost_result.scalar() or 0
    
    total_closed = won_count + lost_count
    close_rate = (won_count / total_closed * 100) if total_closed > 0 else 0.0
    
    # Previous period close rate
    prev_won_query = select(func.count(Project.id)).where(and_(*prev_filters, Project.status == "Won"))
    prev_won_result = await db.execute(prev_won_query)
    prev_won_count = prev_won_result.scalar() or 0
    
    prev_lost_query = select(func.count(Project.id)).where(and_(*prev_filters, Project.status == "Lost"))
    prev_lost_result = await db.execute(prev_lost_query)
    prev_lost_count = prev_lost_result.scalar() or 0
    
    prev_total_closed = prev_won_count + prev_lost_count
    prev_close_rate = (prev_won_count / prev_total_closed * 100) if prev_total_closed > 0 else 0.0
    
    close_rate_change = close_rate - prev_close_rate
    
    # 4. Average Ticket (Average revenue per Won project)
    won_projects_query = select(func.count(Project.id)).where(and_(*current_filters, Project.status == "Won"))
    won_projects_result = await db.execute(won_projects_query)
    won_projects_count = won_projects_result.scalar() or 0
    
    average_ticket = (current_revenue / won_projects_count) if won_projects_count > 0 else 0.0
    
    # Previous period average ticket
    prev_won_projects_query = select(func.count(Project.id)).where(and_(*prev_filters, Project.status == "Won"))
    prev_won_projects_result = await db.execute(prev_won_projects_query)
    prev_won_projects_count = prev_won_projects_result.scalar() or 0
    
    prev_average_ticket = (prev_revenue / prev_won_projects_count) if prev_won_projects_count > 0 else 0.0
    
    average_ticket_change = ((average_ticket - prev_average_ticket) / prev_average_ticket * 100) if prev_average_ticket > 0 else 0.0
    
    response = {
        "totalRevenue": current_revenue,
        "totalRevenueChange": round(total_revenue_change, 1),
        "activeQuotesCount": current_active_count,
        "activeQuotesChange": round(active_quotes_change, 1),
        "closeRate": round(close_rate, 1),
        "closeRateChange": round(close_rate_change, 1),
        "averageTicket": average_ticket,
        "averageTicketChange": round(average_ticket_change, 1)
    }
    
    # Cache for 2 minutes
    cache.set(cache_key, response, ttl_seconds=120)
    
    return response


@router.get("/operational-costs", response_model=OperationalCostPayloadSchema)
async def get_operational_costs(
    period: Optional[str] = Query(
        "current_month",
        description="Period: 'current_month' (only supported value for now)",
    ),
    organization_id: Optional[int] = Query(
        None,
        description="Optional organization id for super_admin scope",
    ),
    current_user: User = Depends(require_operational_dashboard),
    db: AsyncSession = Depends(get_db),
) -> OperationalCostPayloadSchema:
    """
    Get aggregated operational cost dashboard for the current month.

    Single source of truth: all metrics come from backend; no client-side financial logic.
    Returns resource costs (payroll + social charges), fixed costs, amortization,
    tax costs, total operational cost, target margin, effective margin, and calculation metadata.

    **Permissions:** owner, admin_financiero, or super_admin.
    **Multitenancy:** Data is scoped to the tenant organization.
    """
    if period != "current_month":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only period=current_month is supported.",
        )
    role = get_user_role(current_user)
    user_org_id = getattr(current_user, "organization_id", None)

    # Strict multitenancy:
    # - owner/admin_financiero can only read their own organization
    # - super_admin can choose organization_id explicitly
    if role == "super_admin":
        resolved_org_id = organization_id or user_org_id
        if resolved_org_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="super_admin must provide organization_id when no organization is assigned.",
            )
    else:
        if user_org_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tenant users must belong to an organization.",
            )
        if organization_id is not None and organization_id != user_org_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only access your own organization data.",
            )
        resolved_org_id = user_org_id

    org_result = await db.execute(
        select(Organization).where(Organization.id == resolved_org_id)
    )
    org = org_result.scalar_one_or_none()
    if org is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found.",
        )

    primary_currency = "USD"
    if org and org.settings and org.settings.get("primary_currency"):
        primary_currency = org.settings.get("primary_currency")
    payload = await get_current_month_operational_costs(
        db=db,
        organization_id=resolved_org_id,
        primary_currency=primary_currency,
    )
    return payload
