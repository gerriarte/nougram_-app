"""
Business Intelligence and AI endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from datetime import datetime, date
from typing import Optional

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.tenant import get_tenant_context, TenantContext
from app.core.ai_advisor import query_ai_advisor
from app.core.permission_middleware import require_view_analytics
from app.models.user import User
from app.models.project import Project, Quote
from app.models.service import Service
from app.schemas.insight import AIAdvisorRequest, AIAdvisorResponse

router = APIRouter()


@router.get("/dashboard")
async def get_dashboard_data(
    start_date: Optional[str] = Query(None, description="Start date filter (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date filter (YYYY-MM-DD)"),
    currency: Optional[str] = Query(None, description="Filter by currency (USD, COP, ARS, EUR)"),
    status: Optional[str] = Query(None, description="Filter by project status"),
    client_name: Optional[str] = Query(None, description="Filter by client name (partial match)"),
    compare_previous: bool = Query(False, description="Compare with previous period"),
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(require_view_analytics),  # Require permission to view analytics
    db: AsyncSession = Depends(get_db)
):
    """
    Get dashboard KPIs and aggregated data
    
    **Permissions:**
    - Requires `can_view_analytics` permission
    - Allowed roles: owner, admin_financiero, product_manager, super_admin, support_manager, data_analyst
    - Denied roles: collaborator
    
    Returns:
        - Total projects
        - Total revenue
        - Average margin
        - Projects by status
        - Revenue by service
    """
    from app.core.cache import get_cache
    
    try:
        # Check cache first (cache key includes all filters and tenant)
        cache = get_cache()
        cache_key = f"dashboard:{tenant.organization_id}:{start_date or 'all'}:{end_date or 'all'}:{currency or 'all'}:{status or 'all'}:{client_name or 'all'}:{compare_previous}"
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return cached_data
        
        # Parse date filters
        start_date_obj = None
        end_date_obj = None
        if start_date:
            try:
                start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid start_date format. Use YYYY-MM-DD"
                )
        if end_date:
            try:
                end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid end_date format. Use YYYY-MM-DD"
                )
        
        # Build filter conditions (always include tenant filter)
        filters = [Project.organization_id == tenant.organization_id]
        if start_date_obj:
            filters.append(Project.created_at >= datetime.combine(start_date_obj, datetime.min.time()))
        if end_date_obj:
            filters.append(Project.created_at <= datetime.combine(end_date_obj, datetime.max.time()))
        if currency:
            filters.append(Project.currency == currency)
        if status:
            filters.append(Project.status == status)
        if client_name:
            filters.append(Project.client_name.ilike(f"%{client_name}%"))
        
        # Total projects
        project_query = select(func.count(Project.id))
        if filters:
            project_query = project_query.where(and_(*filters))
        total_projects_result = await db.execute(project_query)
        total_projects = total_projects_result.scalar() or 0
        
        # Total revenue (sum of all quote client prices)
        revenue_query = select(func.sum(Quote.total_client_price)).join(Project, Quote.project_id == Project.id)
        if filters:
            revenue_query = revenue_query.where(and_(*filters))
        total_revenue_result = await db.execute(revenue_query)
        total_revenue = total_revenue_result.scalar() or 0.0
        
        # Average margin
        margin_query = select(func.avg(Quote.margin_percentage)).join(Project, Quote.project_id == Project.id)
        if filters:
            margin_query = margin_query.where(and_(*filters))
        avg_margin_result = await db.execute(margin_query)
        avg_margin = avg_margin_result.scalar() or 0.0
        
        # Average revenue per project
        avg_revenue_per_project = (total_revenue / total_projects) if total_projects > 0 else 0.0
        
        # Conversion rate (Sent → Won)
        sent_filters = filters + [Project.status == "Sent"]
        sent_count_query = select(func.count(Project.id)).where(and_(*sent_filters))
        sent_count_result = await db.execute(sent_count_query)
        sent_count = sent_count_result.scalar() or 0
        
        won_filters = filters + [Project.status == "Won"]
        won_count_query = select(func.count(Project.id)).where(and_(*won_filters))
        won_count_result = await db.execute(won_count_query)
        won_count = won_count_result.scalar() or 0
        
        conversion_rate = (won_count / sent_count * 100) if sent_count > 0 else 0.0
        
        # Projects by status
        status_query = select(Project.status, func.count(Project.id)).group_by(Project.status)
        if filters:
            status_query = status_query.where(and_(*filters))
        projects_by_status_result = await db.execute(status_query)
        projects_by_status = {
            row[0]: row[1] for row in projects_by_status_result.all()
        }
        
        # Projects by client
        client_query = select(
            Project.client_name,
            func.count(Project.id).label('count'),
            func.sum(Quote.total_client_price).label('total_revenue')
        ).join(Quote, Quote.project_id == Project.id, isouter=True).group_by(Project.client_name)
        if filters:
            client_query = client_query.where(and_(*filters))
        projects_by_client_result = await db.execute(client_query)
        projects_by_client = [
            {
                "client_name": row[0],
                "project_count": row[1],
                "total_revenue": float(row[2] or 0)
            }
            for row in projects_by_client_result.all()
        ]
        projects_by_client.sort(key=lambda x: x["total_revenue"], reverse=True)
        
        # Revenue by service
        from app.models.project import QuoteItem
        service_filters = [Service.organization_id == tenant.organization_id]
        if filters:
            service_filters.extend(filters)
        revenue_by_service_query = (
            select(Service.name, func.sum(QuoteItem.client_price))
            .join(QuoteItem, QuoteItem.service_id == Service.id)
            .join(Quote, QuoteItem.quote_id == Quote.id)
            .join(Project, Quote.project_id == Project.id)
            .where(and_(*service_filters))
            .group_by(Service.name)
        )
        revenue_by_service_result = await db.execute(revenue_by_service_query)
        revenue_by_service = {
            row[0]: float(row[1] or 0) for row in revenue_by_service_result.all()
        }
        
        # Total internal costs
        costs_query = select(func.sum(Quote.total_internal_cost)).join(Project, Quote.project_id == Project.id)
        if filters:
            costs_query = costs_query.where(and_(*filters))
        total_costs_result = await db.execute(costs_query)
        total_costs = total_costs_result.scalar() or 0.0
        
        # Total profit
        total_profit = total_revenue - total_costs
        
        # Team utilization (billable hours used vs available) - filter by project dates
        from app.models.team import TeamMember
        team_hours_result = await db.execute(
            select(func.sum(TeamMember.billable_hours_per_week * 4.33))
            .where(
                TeamMember.is_active == True,
                TeamMember.organization_id == tenant.organization_id
            )
        )
        total_available_hours = team_hours_result.scalar() or 0.0
        
        used_hours_query = (
            select(func.sum(QuoteItem.estimated_hours))
            .join(Quote, QuoteItem.quote_id == Quote.id)
            .join(Project, Quote.project_id == Project.id)
        )
        if filters:
            used_hours_query = used_hours_query.where(and_(*filters))
        used_hours_result = await db.execute(used_hours_query)
        total_used_hours = used_hours_result.scalar() or 0.0
        
        utilization_rate = (total_used_hours / total_available_hours * 100) if total_available_hours > 0 else 0.0
        
        # Monthly trends (last 12 months)
        from dateutil.relativedelta import relativedelta
        monthly_trends = []
        if end_date_obj:
            end_month = end_date_obj.replace(day=1)
        else:
            end_month = datetime.now().date().replace(day=1)
        
        for i in range(11, -1, -1):  # Last 12 months
            month_start = end_month - relativedelta(months=i)
            month_end = (month_start + relativedelta(months=1)) - relativedelta(days=1)
            
            month_filters = [
                Project.created_at >= datetime.combine(month_start, datetime.min.time()),
                Project.created_at <= datetime.combine(month_end, datetime.max.time())
            ]
            if filters:
                month_filters.extend(filters)
            
            month_revenue_query = select(func.sum(Quote.total_client_price)).join(Project, Quote.project_id == Project.id)
            month_revenue_query = month_revenue_query.where(and_(*month_filters))
            month_revenue_result = await db.execute(month_revenue_query)
            month_revenue = month_revenue_result.scalar() or 0.0
            
            month_projects_query = select(func.count(Project.id))
            month_projects_query = month_projects_query.where(and_(*month_filters))
            month_projects_result = await db.execute(month_projects_query)
            month_projects = month_projects_result.scalar() or 0
            
            monthly_trends.append({
                "month": month_start.strftime("%Y-%m"),
                "revenue": float(month_revenue),
                "projects": month_projects
            })
        
        # Previous period comparison
        previous_period_data = None
        if compare_previous and start_date_obj and end_date_obj:
            period_days = (end_date_obj - start_date_obj).days
            prev_start = start_date_obj - relativedelta(days=period_days + 1)
            prev_end = start_date_obj - relativedelta(days=1)
            
            prev_filters = [
                Project.created_at >= datetime.combine(prev_start, datetime.min.time()),
                Project.created_at <= datetime.combine(prev_end, datetime.max.time())
            ]
            if currency:
                prev_filters.append(Project.currency == currency)
            if status:
                prev_filters.append(Project.status == status)
            if client_name:
                prev_filters.append(Project.client_name.ilike(f"%{client_name}%"))
            
            prev_revenue_query = select(func.sum(Quote.total_client_price)).join(Project, Quote.project_id == Project.id)
            prev_revenue_query = prev_revenue_query.where(and_(*prev_filters))
            prev_revenue_result = await db.execute(prev_revenue_query)
            prev_revenue = prev_revenue_result.scalar() or 0.0
            
            prev_projects_query = select(func.count(Project.id))
            prev_projects_query = prev_projects_query.where(and_(*prev_filters))
            prev_projects_result = await db.execute(prev_projects_query)
            prev_projects = prev_projects_result.scalar() or 0
            
            previous_period_data = {
                "total_projects": prev_projects,
                "total_revenue": float(prev_revenue),
                "period": f"{prev_start} to {prev_end}"
            }
        
        dashboard_data = {
            "total_projects": total_projects,
            "total_revenue": float(total_revenue),
            "total_costs": float(total_costs),
            "total_profit": float(total_profit),
            "average_margin": float(avg_margin),
            "average_revenue_per_project": float(avg_revenue_per_project),
            "conversion_rate": float(conversion_rate),
            "utilization_rate": float(utilization_rate),
            "projects_by_status": projects_by_status,
            "projects_by_client": projects_by_client[:10],  # Top 10 clients
            "revenue_by_service": revenue_by_service,
            "monthly_trends": monthly_trends,
            "previous_period": previous_period_data
        }
        
        # Cache the result (2 minutes TTL)
        cache.set(cache_key, dashboard_data, ttl_seconds=120)
        
        return dashboard_data
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting dashboard data: {str(e)}"
        )


@router.post("/ai-advisor", response_model=AIAdvisorResponse)
async def ask_ai_advisor_endpoint(
    request: AIAdvisorRequest,
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Ask AI advisor a question
    
    Receives a question and analyzes the agency's project data (anonymized)
    to provide CFO-level insights and recommendations.
    
    Example questions:
    - "Analiza mis últimos 5 proyectos"
    - "¿Cuál es mi margen promedio?"
    - "¿Qué servicios son más rentables?"
    """
    try:
        result = await query_ai_advisor(
            question=request.question,
            db=db,
            ai_provider=request.ai_provider
        )
        
        return AIAdvisorResponse(
            success=result.get("success", False),
            answer=result.get("answer", ""),
            provider=result.get("provider")
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error querying AI advisor: {str(e)}"
        )
