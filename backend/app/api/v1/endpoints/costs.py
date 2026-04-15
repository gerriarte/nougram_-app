"""
Cost management endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.tenant import get_tenant_context, TenantContext
from app.core.calculations import calculate_blended_cost_rate
from app.core.money import Money
from app.core.exceptions import ResourceNotFoundError, BusinessLogicError
from app.core.permissions import can_create, can_edit, can_delete, PermissionError, PERM_VIEW_SENSITIVE_DATA, PERM_MODIFY_COSTS, PERM_DELETE_RESOURCES
from app.core.permission_middleware import require_view_sensitive_data, require_modify_costs, require_delete_resources
from app.models.user import User
from app.models.cost import CostFixed
from app.models.role import DeleteRequest, DeleteRequestStatus
from app.repositories.factory import RepositoryFactory
from app.schemas.cost import (
    CostFixedCreate,
    CostFixedUpdate,
    CostFixedResponse,
    CostFixedListResponse,
)
from app.schemas.quote import BlendedCostRateResponse
from app.models.team import TeamMember
from app.core.currency import normalize_to_primary_currency, EXCHANGE_RATES_TO_USD, CURRENCY_INFO
from collections import defaultdict
from app.core.logging import get_logger
from app.services.settings_service import SettingsService

router = APIRouter()
logger = get_logger(__name__)


@router.get("/costs/fixed", response_model=CostFixedListResponse, summary="List all fixed costs")
async def list_fixed_costs(
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(require_view_sensitive_data),  # Require permission to view sensitive data (costs)
    db: AsyncSession = Depends(get_db),
    include_deleted: bool = False,
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page (max 100)")
):
    """
    List all fixed costs with pagination
    By default, excludes soft-deleted items (deleted_at IS NULL)
    
    **Permissions:**
    - Requires `can_view_sensitive_data` permission (costs are sensitive data)
    - Allowed roles: owner, admin_financiero, super_admin
    - Denied roles: product_manager, collaborator (data leakage prevention)
    """
    from app.core.logging import get_logger
    logger = get_logger(__name__)
    
    cost_repo = RepositoryFactory.create_cost_repository(db, tenant.organization_id)
    
    # Get total count
    total = await cost_repo.count(include_deleted=include_deleted)
    
    # Get paginated results
    offset = (page - 1) * page_size
    costs = await cost_repo.get_all(
        include_deleted=include_deleted,
        order_by=CostFixed.created_at.desc(),
        limit=page_size,
        offset=offset
    )
    
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1
    
    logger.info(
        f"User {current_user.email} listed fixed costs (page {page}, size {page_size})",
        extra={"user_id": current_user.id, "page": page, "page_size": page_size, "total": total}
    )
    
    return CostFixedListResponse(
        items=[CostFixedResponse.model_validate(cost) for cost in costs],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.post("/costs/fixed", response_model=CostFixedResponse, status_code=status.HTTP_201_CREATED, summary="Create a new fixed cost")
async def create_fixed_cost(
    cost_data: CostFixedCreate,
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(require_modify_costs),  # Require permission to modify costs
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new fixed cost
    
    **Permissions:**
    - Requires `can_modify_costs` permission
    - Allowed roles: owner, admin_financiero, super_admin
    - Denied roles: product_manager, collaborator
    """
    try:
        user_id = getattr(current_user, "id", None)
        # Ensure all required fields have values
        cost_dict = cost_data.model_dump()
        
        settings_service = SettingsService(db)
        primary_currency = await settings_service.get_primary_currency(tenant.organization_id)
        incoming_currency = cost_dict.get('currency')
        if incoming_currency and incoming_currency != primary_currency:
            logger.warning(
                "Overriding fixed cost currency with organization primary currency",
                user_id=user_id,
                organization_id=tenant.organization_id,
                incoming_currency=incoming_currency,
                primary_currency=primary_currency,
            )
        cost_dict['currency'] = primary_currency
        logger.info("Creating fixed cost", cost_data=cost_dict, user_id=user_id)
        
        cost_dict['organization_id'] = tenant.organization_id
        
        new_cost = CostFixed(**cost_dict)
        cost_repo = RepositoryFactory.create_cost_repository(db, tenant.organization_id)
        new_cost = await cost_repo.create(new_cost)
        
        # Invalidate blended cost rate cache
        from app.core.cache import get_cache
        cache = get_cache()
        cache.invalidate_pattern("blended_cost_rate:")
        cache.invalidate_pattern("financial_summary:")
        
        logger.info("Fixed cost created successfully", cost_id=new_cost.id, user_id=user_id)
        return CostFixedResponse.model_validate(new_cost)
    except Exception as e:
        await db.rollback()
        logger.error(
            "Error creating fixed cost",
            error=str(e),
            user_id=getattr(current_user, "id", None),
            cost_data=cost_data.model_dump() if hasattr(cost_data, 'model_dump') else str(cost_data),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create fixed cost: {str(e)}"
        )


@router.put("/costs/fixed/{cost_id}", response_model=CostFixedResponse)
async def update_fixed_cost(
    cost_id: int,
    cost_data: CostFixedUpdate,
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(require_modify_costs),  # Require permission to modify costs
    db: AsyncSession = Depends(get_db)
):
    """
    Update an existing fixed cost
    Cannot update soft-deleted costs
    
    **Permissions:**
    - Requires `can_modify_costs` permission
    - Allowed roles: owner, admin_financiero, super_admin
    - Denied roles: product_manager, collaborator
    """
    try:
        user_id = getattr(current_user, "id", None)
        cost_repo = RepositoryFactory.create_cost_repository(db, tenant.organization_id)
        cost = await cost_repo.get_by_id(cost_id, include_deleted=False)
        
        if not cost:
            raise ResourceNotFoundError("Fixed cost", cost_id)
        
        update_data = cost_data.model_dump(exclude_unset=True)
        settings_service = SettingsService(db)
        primary_currency = await settings_service.get_primary_currency(tenant.organization_id)
        
        # Enforce organization primary currency for financial consistency
        if 'currency' in update_data:
            incoming_currency = update_data.get('currency')
            if incoming_currency and incoming_currency != primary_currency:
                logger.warning(
                    "Overriding fixed cost currency update with organization primary currency",
                    user_id=user_id,
                    organization_id=tenant.organization_id,
                    cost_id=cost_id,
                    incoming_currency=incoming_currency,
                    primary_currency=primary_currency,
                )
            update_data['currency'] = primary_currency
        logger.info("Updating fixed cost", cost_id=cost_id, update_data=update_data, user_id=user_id)
        
        for field, value in update_data.items():
            setattr(cost, field, value)
        
        cost = await cost_repo.update(cost)
        
        # Invalidate blended cost rate cache
        from app.core.cache import get_cache
        cache = get_cache()
        cache.invalidate_pattern("blended_cost_rate:")
        cache.invalidate_pattern("financial_summary:")
        
        logger.info("Fixed cost updated successfully", cost_id=cost_id, user_id=user_id)
        return CostFixedResponse.model_validate(cost)
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(
            "Error updating fixed cost",
            cost_id=cost_id,
            error=str(e),
            user_id=getattr(current_user, "id", None),
            update_data=cost_data.model_dump(exclude_unset=True) if hasattr(cost_data, 'model_dump') else str(cost_data),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update fixed cost: {str(e)}"
        )


@router.delete("/costs/fixed/{cost_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_fixed_cost(
    cost_id: int,
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(get_current_user),  # Permission check inside due to complex logic
    db: AsyncSession = Depends(get_db)
):
    """
    Soft delete a fixed cost (move to trash)
    Fixed costs are used in calculations, so deletion will affect the blended cost rate.
    
    **Permissions:**
    - Requires `can_delete_resources` permission
    - Allowed roles: owner, super_admin (can delete immediately)
    - Admin Financiero: Not allowed (only owner can delete)
    - Denied roles: product_manager, collaborator
    """
    # Check permissions - use require_delete_resources dependency logic
    from app.core.permissions import check_permission, PERM_DELETE_RESOURCES
    try:
        check_permission(current_user, PERM_DELETE_RESOURCES)
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete costs"
        )
    
    # Check if deletion requires approval (currently only owner and super_admin can delete)
    # For now, all users with PERM_DELETE_RESOURCES can delete immediately
    requires_approval = False
    
    # Verify if the cost exists and is not already deleted
    cost_repo = RepositoryFactory.create_cost_repository(db, tenant.organization_id)
    cost = await cost_repo.get_by_id(cost_id, include_deleted=False)
    
    if not cost:
        raise ResourceNotFoundError("Fixed cost", cost_id)
    
    if requires_approval:
        # Create delete request instead of deleting immediately
        delete_request = DeleteRequest(
            resource_type="cost",
            resource_id=cost_id,
            requested_by_id=current_user.id,
            status="pending"  # Use string instead of enum
        )
        db.add(delete_request)
        await db.commit()
        await db.refresh(delete_request)
        
        raise HTTPException(
            status_code=status.HTTP_202_ACCEPTED,
            detail={
                "message": "Delete request created and pending approval",
                "request_id": delete_request.id
            }
        )
    
    # Super Admin can delete immediately
    cost.deleted_at = datetime.utcnow()
    cost.deleted_by_id = current_user.id
    await cost_repo.update(cost)
    
    # Invalidate blended cost rate cache
    from app.core.cache import get_cache
    cache = get_cache()
    cache.invalidate_pattern("blended_cost_rate:")
    cache.invalidate_pattern("financial_summary:")
    
    return None


@router.post("/costs/fixed/{cost_id}/restore", response_model=CostFixedResponse)
async def restore_fixed_cost(
    cost_id: int,
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Restore a soft-deleted fixed cost from trash
    """
    cost_repo = RepositoryFactory.create_cost_repository(db, tenant.organization_id)
    cost = await cost_repo.get_by_id(cost_id, include_deleted=True)
    
    if not cost or cost.deleted_at is None:
        raise ResourceNotFoundError("Fixed cost", cost_id)
    
    # Restore: clear deleted fields
    cost.deleted_at = None
    cost.deleted_by_id = None
    cost = await cost_repo.update(cost)
    
    # Invalidate blended cost rate cache
    from app.core.cache import get_cache
    cache = get_cache()
    cache.invalidate_pattern("blended_cost_rate:")
    cache.invalidate_pattern("financial_summary:")
    
    return CostFixedResponse.model_validate(cost)


@router.get("/costs/fixed/trash/list", response_model=CostFixedListResponse)
async def list_deleted_fixed_costs(
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all soft-deleted fixed costs (trash)
    """
    from sqlalchemy.orm import selectinload
    
    query = select(CostFixed).where(
        CostFixed.deleted_at.isnot(None)
    ).options(selectinload(CostFixed.deleted_by)).order_by(CostFixed.deleted_at.desc())
    
    result = await db.execute(query)
    costs = result.scalars().all()
    
    # Build response with user info
    items = []
    for cost in costs:
        cost_dict = {
            "id": cost.id,
            "name": cost.name,
            "amount_monthly": cost.amount_monthly,
            "currency": cost.currency,
            "category": cost.category,
            "description": cost.description,
            "created_at": cost.created_at,
            "updated_at": cost.updated_at,
            "deleted_at": cost.deleted_at,
            "deleted_by_id": cost.deleted_by_id,
            "deleted_by_name": cost.deleted_by.name if cost.deleted_by else None,
            "deleted_by_email": cost.deleted_by.email if cost.deleted_by else None,
        }
        items.append(CostFixedResponse.model_validate(cost_dict))
    
    return CostFixedListResponse(
        items=items,
        total=len(costs)
    )


@router.delete("/costs/fixed/{cost_id}/permanent", status_code=status.HTTP_204_NO_CONTENT)
async def permanently_delete_fixed_cost(
    cost_id: int,
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Permanently delete a soft-deleted fixed cost (hard delete)
    This action cannot be undone. Only soft-deleted costs can be permanently deleted.
    """
    # Verify if the cost exists and is soft-deleted
    result = await db.execute(
        select(CostFixed).where(
            CostFixed.id == cost_id,
            CostFixed.deleted_at.isnot(None)
        )
    )
    cost = result.scalar_one_or_none()
    
    if not cost:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fixed cost with id {cost_id} not found in trash. Only soft-deleted costs can be permanently deleted."
        )
    
    # Hard delete: permanently remove from database
    await db.delete(cost)
    await db.commit()
    
    return None


@router.get("/calculations/agency-cost-hour", response_model=BlendedCostRateResponse)
async def calculate_agency_cost_hour(
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Calculate blended cost rate (agency cost per hour)
    This is the core calculation for Module 1
    All costs are normalized to the primary currency before calculation
    """
    
    try:
        settings_service = SettingsService(db)
        primary_currency = await settings_service.get_primary_currency(tenant.organization_id)
        org_settings = tenant.organization.settings if tenant.organization.settings else {}
        
        # Calculate blended cost rate (normalized to primary currency)
        social_config = org_settings.get('social_charges_config') if org_settings else None
        blended_rate = await calculate_blended_cost_rate(
            db, 
            primary_currency, 
            tenant_id=tenant.organization_id,
            social_charges_config=social_config
        )
        
        # Get additional details for response (normalized to primary currency)
        # Exclude soft-deleted costs from calculations
        # ESTÁNDAR NOUGRAM: Usar Decimal para precisión
        from decimal import Decimal
        
        cost_repo = RepositoryFactory.create_cost_repository(db, tenant.organization_id)
        fixed_costs = await cost_repo.get_all_active(include_deleted=False)
        total_fixed_overhead = Decimal('0')
        total_tools_costs = Decimal('0')
        
        for cost in fixed_costs:
            normalized = normalize_to_primary_currency(
                cost.amount_monthly,
                cost.currency or "USD",
                primary_currency
            )
            # ESTÁNDAR NOUGRAM: normalize_to_primary_currency puede retornar Money o float
            # Convertir a Decimal para cálculos
            if isinstance(normalized, Money):
                normalized_decimal = normalized.amount
            else:
                normalized_decimal = Decimal(str(normalized))
            
            # Categorize: 'Software', 'SaaS', 'Herramientas', 'Tools' go to tools
            # 'Overhead', 'Infrastructure', 'Office', 'Rent', 'General' go to overhead
            category_lower = (cost.category or "").lower()
            tools_keywords = ['software', 'saas', 'herramienta', 'tool', 'licencia', 'license', 'subscription', 'suscripcion']
            overhead_keywords = ['overhead', 'infrastructure', 'office', 'utilities', 'rent', 'alquiler', 'general', 'otro']
            
            is_tool = any(keyword in category_lower for keyword in tools_keywords)
            is_overhead = any(keyword in category_lower for keyword in overhead_keywords)
            
            if is_tool:
                total_tools_costs += normalized_decimal
            elif is_overhead or not is_tool:  # Por defecto es overhead si no coincide con ninguna
                total_fixed_overhead += normalized_decimal
        
        total_fixed_costs = total_fixed_overhead + total_tools_costs
        
        # Get active team members salaries
        team_repo = RepositoryFactory.create_team_repository(db, tenant.organization_id)
        team_members = await team_repo.get_all_active()
        
        # Get organization settings for social charges (Sprint 18)
        social_charges_multiplier = Decimal('1.0')
        if org_settings and org_settings.get('social_charges_config'):
            social_config = org_settings.get('social_charges_config', {})
            if social_config.get('enable_social_charges', False):
                total_percentage = 0
                total_percentage += social_config.get('health_percentage', 0) or 0
                total_percentage += social_config.get('pension_percentage', 0) or 0
                total_percentage += social_config.get('arl_percentage', 0) or 0
                total_percentage += social_config.get('parafiscales_percentage', 0) or 0
                total_percentage += social_config.get('prima_services_percentage', 0) or 0
                total_percentage += social_config.get('cesantias_percentage', 0) or 0
                total_percentage += social_config.get('int_cesantias_percentage', 0) or 0
                total_percentage += social_config.get('vacations_percentage', 0) or 0
                
                social_charges_multiplier = Decimal('1') + (Decimal(str(total_percentage)) / Decimal('100'))
        
        total_salaries = Decimal('0')
        currency_counts = {}
        for currency in ["USD", "COP", "ARS", "EUR"]:
            currency_counts[currency] = {"count": 0, "total_amount": 0.0, "exchange_rate_to_primary": 0.0}
        
        for member in team_members:
            # Normalize first, then apply social charges multiplier (consistent with calculate_blended_cost_rate)
            normalized = normalize_to_primary_currency(
                member.salary_monthly_brute,
                member.currency or "USD",
                primary_currency
            )
            # ESTÁNDAR NOUGRAM: normalize_to_primary_currency puede retornar Money o float
            # Convertir a Decimal para cálculos
            if isinstance(normalized, Money):
                normalized_decimal = normalized.amount
            else:
                normalized_decimal = Decimal(str(normalized))
            
            member_mult = (
                social_charges_multiplier
                if getattr(member, "apply_social_charges", True)
                else Decimal("1")
            )
            real_monthly_cost = normalized_decimal * member_mult
            total_salaries += real_monthly_cost
        
        # Calculate total billable hours per month across all members
        # Consider non_billable_hours_percentage (consistent with calculate_blended_cost_rate)
        total_hours = sum(
            member.billable_hours_per_week * 4.33 * (1 - (member.non_billable_hours_percentage or 0.0))
            for member in team_members
        )
        
        # Collect currency distribution info
        # ESTÁNDAR NOUGRAM: Usar Decimal para total_amount
        for cost in fixed_costs:
            cost_currency = cost.currency or "USD"
            if cost_currency not in currency_counts:
                currency_counts[cost_currency] = {"count": 0, "total_amount": Decimal('0'), "exchange_rate_to_primary": Decimal('0')}
            currency_counts[cost_currency]["count"] += 1
            currency_counts[cost_currency]["total_amount"] += Decimal(str(cost.amount_monthly))
        
        # Count currencies in team member salaries
        for member in team_members:
            member_currency = member.currency or "USD"
            if member_currency not in currency_counts:
                currency_counts[member_currency] = {"count": 0, "total_amount": Decimal('0'), "exchange_rate_to_primary": Decimal('0')}
            currency_counts[member_currency]["count"] += 1
            currency_counts[member_currency]["total_amount"] += Decimal(str(member.salary_monthly_brute))
        
        # Build currency info list
        # ESTÁNDAR NOUGRAM: Usar Decimal para cálculos de tasas de cambio
        currencies_used = []
        primary_rate = Decimal(str(EXCHANGE_RATES_TO_USD.get(primary_currency, 1.0)))
        
        for currency_code, info in currency_counts.items():
            if currency_code in EXCHANGE_RATES_TO_USD:
                currency_rate = Decimal(str(EXCHANGE_RATES_TO_USD[currency_code]))
                
                # Calculate exchange rate to primary currency
                # EXCHANGE_RATES_TO_USD stores: 1 USD = X currency
                # So: 1 currency = 1/currency_rate USD
                # Then: 1 currency = (1/currency_rate) * primary_rate primary_currency
                if currency_code == primary_currency:
                    exchange_rate_to_primary = Decimal('1')
                else:
                    exchange_rate_to_primary = (Decimal('1') / currency_rate) * primary_rate
                
                if info["count"] > 0:
                    currencies_used.append({
                        "code": currency_code,
                        "count": info["count"],
                        "exchange_rate_to_primary": exchange_rate_to_primary,
                        "total_amount": info["total_amount"]
                    })
        
        # ESTÁNDAR NOUGRAM: Construir respuesta con Decimal
        total_monthly_costs_final = total_fixed_costs + total_salaries
        
        return BlendedCostRateResponse(
            blended_cost_rate=blended_rate,
            total_monthly_costs=total_monthly_costs_final,
            total_fixed_overhead=total_fixed_overhead,
            total_tools_costs=total_tools_costs,
            total_salaries=total_salaries,
            total_monthly_hours=round(total_hours, 2),
            active_team_members=len(team_members),
            primary_currency=primary_currency,
            currencies_used=currencies_used,
            exchange_rates_date=datetime.now().isoformat()
        )
    except Exception as e:
        # Log error and return default values
        # ESTÁNDAR NOUGRAM: Usar Decimal para valores por defecto
        from decimal import Decimal
        logger.error("Error calculating blended cost rate", error=str(e), user_id=current_user.id, exc_info=True)
        return BlendedCostRateResponse(
            blended_cost_rate=Decimal('0'),
            total_monthly_costs=Decimal('0'),
            total_monthly_hours=0.0,
            active_team_members=0,
            primary_currency="USD",
            currencies_used=[],
            exchange_rates_date=datetime.now().isoformat()
        )
