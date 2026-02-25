"""
Quote calculation endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.calculations import (
    calculate_blended_cost_rate, 
    calculate_quote_totals, 
    calculate_quote_totals_enhanced,
    calculate_rentability_analysis
)
from app.core.permission_middleware import require_create_quotes
from app.models.user import User
from app.models.service import Service
from app.models.project import Quote
from app.schemas.quote import QuoteCalculateRequest, QuoteCalculateResponse, RentabilitySummaryResponse

router = APIRouter()


@router.post("/calculate", response_model=QuoteCalculateResponse, summary="Calculate quote totals")
async def calculate_quote(
    request: QuoteCalculateRequest,
    current_user: User = Depends(require_create_quotes),  # Require permission to create quotes (calculation is part of quote creation)
    db: AsyncSession = Depends(get_db)
):
    """
    Calculate quote totals (internal cost, client price, margin)
    This is the core endpoint for Module 3 (Sprint 14: Enhanced with multiple pricing types)
    
    Supports multiple pricing types:
    - hourly: Hours × BCR (requires estimated_hours)
    - fixed: fixed_price × quantity (requires fixed_price)
    - recurring: recurring_price (requires recurring_price and billing_frequency)
    - project_value: Custom project value (requires project_value)
    
    Receives: list of items with service_id and pricing information
    Returns: {total_internal_cost, total_client_price, margin_percentage, items breakdown}
    
    **Permissions:**
    - Requires `can_create_quotes` permission
    - Allowed roles: owner, admin_financiero, product_manager, collaborator, super_admin
    """
    # Validate services exist and determine pricing type
    for item in request.items:
        result = await db.execute(
            select(Service).where(Service.id == item.service_id, Service.is_active == True)
        )
        service = result.scalar_one_or_none()
        if not service:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Service with id {item.service_id} not found or inactive"
            )
        
        # Determine effective pricing type
        effective_pricing_type = item.pricing_type or service.pricing_type or "hourly"
        
        # Validate required fields based on pricing type
        if effective_pricing_type == "hourly":
            if not item.estimated_hours or item.estimated_hours <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Service {service.name} requires estimated_hours for hourly pricing"
                )
        elif effective_pricing_type == "fixed":
            fixed_price = item.fixed_price or service.fixed_price
            if not fixed_price or fixed_price <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Service {service.name} requires fixed_price for fixed pricing"
                )
        elif effective_pricing_type == "recurring":
            recurring_price = item.recurring_price or service.recurring_price
            billing_frequency = item.billing_frequency or service.billing_frequency
            if not recurring_price or recurring_price <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Service {service.name} requires recurring_price for recurring pricing"
                )
            if not billing_frequency:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Service {service.name} requires billing_frequency for recurring pricing"
                )
        elif effective_pricing_type == "project_value":
            project_value = item.project_value or item.fixed_price
            if not project_value or project_value <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Service {service.name} requires project_value for project_value pricing"
                )
    
    # Get organization primary currency (Sprint 18/19)
    from app.models.organization import Organization
    primary_currency = "USD"
    social_config = None
    if current_user.organization_id:
        result = await db.execute(select(Organization).where(Organization.id == current_user.organization_id))
        org = result.scalar_one_or_none()
        if org and org.settings:
            primary_currency = org.settings.get('primary_currency', 'USD')
            social_config = org.settings.get('social_charges_config')

    # Calculate blended cost rate (needed for hourly calculations and internal cost estimates)
    blended_rate = await calculate_blended_cost_rate(
        db, 
        primary_currency=primary_currency, 
        tenant_id=current_user.organization_id,
        social_charges_config=social_config
    )
    
    # Convert request items to dict format for enhanced calculation
    items_dict = []
    for item in request.items:
        item_dict = {
            "service_id": item.service_id,
            "estimated_hours": item.estimated_hours,
            "pricing_type": item.pricing_type,
            "fixed_price": item.fixed_price,
            "quantity": item.quantity or 1.0,
            "recurring_price": item.recurring_price,
            "billing_frequency": item.billing_frequency,
            "project_value": item.project_value,
        }
        items_dict.append(item_dict)
    
    # Convert request expenses to dict format (Sprint 15)
    expenses_dict = []
    if request.expenses:
        for expense in request.expenses:
            expense_dict = {
                "name": expense.name,
                "description": expense.description,
                "cost": expense.cost,
                "markup_percentage": expense.markup_percentage,
                "category": expense.category,
                "quantity": expense.quantity or 1.0,
            }
            expenses_dict.append(expense_dict)
    
    # Calculate quote totals using enhanced function (with taxes, expenses, and revisions if provided)
    tax_ids = request.tax_ids or []
    totals = await calculate_quote_totals_enhanced(
        db, 
        items_dict, 
        blended_rate, 
        tax_ids, 
        expenses_dict,
        target_margin_percentage=request.target_margin_percentage,
        revisions_included=request.revisions_included or 2,
        revision_cost_per_additional=request.revision_cost_per_additional,
        revisions_count=request.revisions_count,
        currency=primary_currency  # ESTÁNDAR NOUGRAM: Pasar moneda para precisión
    )
    
    # ESTÁNDAR NOUGRAM: Convertir valores float a Decimal para el schema
    from decimal import Decimal
    
    return QuoteCalculateResponse(
        total_internal_cost=Decimal(str(totals["total_internal_cost"])),
        total_client_price=Decimal(str(totals["total_client_price"])),
        total_expenses_cost=Decimal(str(totals.get("total_expenses_cost", 0.0))),
        total_expenses_client_price=Decimal(str(totals.get("total_expenses_client_price", 0.0))),
        total_taxes=Decimal(str(totals["total_taxes"])),
        total_with_taxes=Decimal(str(totals["total_with_taxes"])),
        margin_percentage=Decimal(str(totals["margin_percentage"])),
        target_margin_percentage=Decimal(str(totals.get("target_margin_percentage"))) if totals.get("target_margin_percentage") is not None else None,  # Include target margin
        items=totals.get("items", []),  # Enhanced breakdown from calculate_quote_totals_enhanced
        expenses=totals.get("expenses", []),  # Expenses breakdown (Sprint 15)
        taxes=totals.get("taxes", []),
        revisions_cost=Decimal(str(totals.get("revisions_cost", 0.0))),  # Revisions breakdown (Sprint 16)
        revisions_included=totals.get("revisions_included", 2),
        revisions_count=totals.get("revisions_count")
    )


@router.get("/{quote_id}/rentability", response_model=RentabilitySummaryResponse)
async def get_quote_rentability(
    quote_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get financial rentability breakdown for a specific quote (Sprint 19).
    
    This endpoint provides a detailed breakdown of costs (Talent, Overhead, SaaS, Variable)
    and net profit calculation including tax burden.
    
    **Permissions:**
    - Authenticated users can view rentability for quotes in their organization.
    """
    # 1. Fetch quote to verify existence and ownership
    result = await db.execute(
        select(Quote).filter(Quote.id == quote_id)
    )
    quote = result.scalar_one_or_none()
    
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quote not found"
        )
    
    # 2. Check organization permission
    from app.models.project import Project
    result = await db.execute(
        select(Project).where(Project.id == quote.project_id)
    )
    project = result.scalar_one_or_none()
    
    if not project or project.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view this quote's rentability analysis"
        )
    
    # 3. Calculate Rentability Analysis
    analysis = await calculate_rentability_analysis(db, quote_id, current_user.organization_id)
    
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not calculate rentability analysis"
        )
    
    return analysis
