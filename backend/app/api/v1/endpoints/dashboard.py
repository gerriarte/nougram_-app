"""
Dashboard endpoints for KPIs and statistics
"""

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.permission_middleware import require_view_analytics
from app.core.permissions import get_user_role
from app.core.security import get_current_user
from app.core.tenant import TenantContext, get_tenant_context
from app.models.organization import Organization
from app.models.project import Project, Quote
from app.models.user import User
from app.schemas.operational_cost import OperationalCostPayloadSchema
from app.services.operational_cost_service import get_current_month_operational_costs
from app.services.settings_service import SettingsService

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


async def _won_projects_revenue(db: AsyncSession, filters: list) -> float:
    """
    Facturación de los proyectos ganados: UNA cotización por proyecto.

    Antes esto era `SUM(Quote.total_client_price) JOIN Project`, que produce una fila por
    VERSIÓN: un proyecto Won con v1/v2/v3 sumaba las tres (y averageTicket, que divide por
    cantidad de PROYECTOS, heredaba el inflado). La versión que cuenta es la aceptada
    (`accepted_quote_id`) y, si no hay, la última versión activa — misma semántica que
    app/core/business_health.py::_accepted_quote_ids.
    """
    projects = (
        await db.execute(
            select(Project.id, Project.accepted_quote_id).where(
                and_(*filters, Project.status == "Won")
            )
        )
    ).all()
    if not projects:
        return 0.0

    project_ids = [row[0] for row in projects]
    accepted_by_project = {row[0]: row[1] for row in projects if row[1]}

    quotes = (
        await db.execute(
            select(
                Quote.id,
                Quote.project_id,
                Quote.version,
                Quote.total_client_price,
                Quote.is_active,
            ).where(Quote.project_id.in_(project_ids))
        )
    ).all()

    accepted_price: dict[int, Decimal] = {}
    latest: dict[int, tuple[int, int, Decimal]] = {}
    for quote_id, project_id, version, total_client_price, is_active in quotes:
        price = Decimal(str(total_client_price or 0))
        if accepted_by_project.get(project_id) == quote_id:
            accepted_price[project_id] = price
            continue
        if not is_active:
            # Versión borrada: solo cuenta si es la explícitamente aceptada.
            continue
        candidate = (int(version or 0), int(quote_id), price)
        current = latest.get(project_id)
        if current is None or candidate[:2] > current[:2]:
            latest[project_id] = candidate

    revenue = Decimal("0")
    for project_id in project_ids:
        if project_id in accepted_price:
            revenue += accepted_price[project_id]
        elif project_id in latest:
            revenue += latest[project_id][2]
    return float(revenue)


@router.get("/kpis")
async def get_dashboard_kpis(
    period: str | None = Query("month", description="Period: 'month', 'quarter', 'year'"),
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(require_view_analytics),
    db: AsyncSession = Depends(get_db),
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
    valid_periods = ["month", "quarter", "year"]
    if period not in valid_periods:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid period. Must be one of: {', '.join(valid_periods)}",
        )

    # Check cache
    cache = get_cache()
    cache_key = f"dashboard_kpis:{tenant.organization_id}:{period}"
    cached_data = cache.get(cache_key)
    if cached_data is not None:
        return cached_data

    # Calculate date range for current period
    # La fecha se toma en UTC, no en la hora local del servidor: `Project.created_at` se
    # persiste en UTC, así que comparar contra un `date.today()` local desalinea los bordes
    # del período. Con el servidor en UTC-5, todo proyecto creado después de las 19:00 hora
    # local ya es "mañana" en UTC y quedaba FUERA de los KPIs del mes en curso.
    today = datetime.now(UTC).date()
    if period == "month":
        period_start = today.replace(day=1)
        period_end = today
        prev_period_start = (period_start - timedelta(days=1)).replace(day=1)
        prev_period_end = period_start - timedelta(days=1)
    elif period == "quarter":
        quarter = (today.month - 1) // 3
        period_start = date(today.year, quarter * 3 + 1, 1)
        period_end = today
        prev_period_start = (
            date(period_start.year, period_start.month - 3, 1)
            if period_start.month > 3
            else date(period_start.year - 1, 10, 1)
        )
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
        Project.created_at <= datetime.combine(period_end, datetime.max.time()),
    ]

    # Build filters for previous period
    prev_filters = [
        Project.organization_id == tenant.organization_id,
        Project.deleted_at.is_(None),
        Project.created_at >= datetime.combine(prev_period_start, datetime.min.time()),
        Project.created_at <= datetime.combine(prev_period_end, datetime.max.time()),
    ]

    # 1. Total Revenue (from Won projects) - una sola cotización por proyecto
    current_revenue = await _won_projects_revenue(db, current_filters)
    prev_revenue = await _won_projects_revenue(db, prev_filters)

    total_revenue_change = (
        ((current_revenue - prev_revenue) / prev_revenue * 100) if prev_revenue > 0 else 0.0
    )

    # 2. Active Quotes Count (not draft, not Won, not Lost)
    current_active_query = (
        select(func.count(Quote.id))
        .join(Project, Quote.project_id == Project.id)
        .where(
            and_(
                *current_filters,
                Project.status.in_(["Sent"]),  # Active quotes are those sent but not closed
            )
        )
    )
    current_active_result = await db.execute(current_active_query)
    current_active_count = current_active_result.scalar() or 0

    prev_active_query = (
        select(func.count(Quote.id))
        .join(Project, Quote.project_id == Project.id)
        .where(and_(*prev_filters, Project.status.in_(["Sent"])))
    )
    prev_active_result = await db.execute(prev_active_query)
    prev_active_count = prev_active_result.scalar() or 0

    active_quotes_change = (
        ((current_active_count - prev_active_count) / prev_active_count * 100)
        if prev_active_count > 0
        else 0.0
    )

    # 3. Close Rate (Win rate: Won / (Won + Lost))
    won_query = select(func.count(Project.id)).where(
        and_(*current_filters, Project.status == "Won")
    )
    won_result = await db.execute(won_query)
    won_count = won_result.scalar() or 0

    lost_query = select(func.count(Project.id)).where(
        and_(*current_filters, Project.status == "Lost")
    )
    lost_result = await db.execute(lost_query)
    lost_count = lost_result.scalar() or 0

    total_closed = won_count + lost_count
    close_rate = (won_count / total_closed * 100) if total_closed > 0 else 0.0

    # Previous period close rate
    prev_won_query = select(func.count(Project.id)).where(
        and_(*prev_filters, Project.status == "Won")
    )
    prev_won_result = await db.execute(prev_won_query)
    prev_won_count = prev_won_result.scalar() or 0

    prev_lost_query = select(func.count(Project.id)).where(
        and_(*prev_filters, Project.status == "Lost")
    )
    prev_lost_result = await db.execute(prev_lost_query)
    prev_lost_count = prev_lost_result.scalar() or 0

    prev_total_closed = prev_won_count + prev_lost_count
    prev_close_rate = (prev_won_count / prev_total_closed * 100) if prev_total_closed > 0 else 0.0

    close_rate_change = close_rate - prev_close_rate

    # 4. Average Ticket (Average revenue per Won project)
    won_projects_query = select(func.count(Project.id)).where(
        and_(*current_filters, Project.status == "Won")
    )
    won_projects_result = await db.execute(won_projects_query)
    won_projects_count = won_projects_result.scalar() or 0

    average_ticket = (current_revenue / won_projects_count) if won_projects_count > 0 else 0.0

    # Previous period average ticket
    prev_won_projects_query = select(func.count(Project.id)).where(
        and_(*prev_filters, Project.status == "Won")
    )
    prev_won_projects_result = await db.execute(prev_won_projects_query)
    prev_won_projects_count = prev_won_projects_result.scalar() or 0

    prev_average_ticket = (
        (prev_revenue / prev_won_projects_count) if prev_won_projects_count > 0 else 0.0
    )

    average_ticket_change = (
        ((average_ticket - prev_average_ticket) / prev_average_ticket * 100)
        if prev_average_ticket > 0
        else 0.0
    )

    response = {
        "totalRevenue": current_revenue,
        "totalRevenueChange": round(total_revenue_change, 1),
        "activeQuotesCount": current_active_count,
        "activeQuotesChange": round(active_quotes_change, 1),
        "closeRate": round(close_rate, 1),
        "closeRateChange": round(close_rate_change, 1),
        "averageTicket": average_ticket,
        "averageTicketChange": round(average_ticket_change, 1),
    }

    # Cache for 2 minutes
    cache.set(cache_key, response, ttl_seconds=120)

    return response


@router.get("/operational-costs", response_model=OperationalCostPayloadSchema)
async def get_operational_costs(
    period: str | None = Query(
        "current_month",
        description="Period: 'current_month' (only supported value for now)",
    ),
    organization_id: int | None = Query(
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

    org_result = await db.execute(select(Organization).where(Organization.id == resolved_org_id))
    org = org_result.scalar_one_or_none()
    if org is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found.",
        )

    settings_service = SettingsService(db)
    primary_currency = await settings_service.get_primary_currency(resolved_org_id)
    payload = await get_current_month_operational_costs(
        db=db,
        organization_id=resolved_org_id,
        primary_currency=primary_currency,
    )
    return payload
