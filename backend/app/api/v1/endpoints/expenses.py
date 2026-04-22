"""
Quote Expenses endpoints (Sprint 15)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import ResourceNotFoundError
from app.core.security import get_current_user
from app.core.tenant import TenantContext, get_tenant_context
from app.models.project import Project, Quote, QuoteExpense
from app.models.user import User
from app.schemas.quote import QuoteExpenseCreate, QuoteExpenseResponse

router = APIRouter()


@router.post(
    "/{project_id}/quotes/{quote_id}/expenses",
    response_model=QuoteExpenseResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_quote_expense(
    project_id: int,
    quote_id: int,
    expense_data: QuoteExpenseCreate,
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Add an expense (third-party cost) to a quote (Sprint 15)

    Calculates client_price automatically: cost * quantity * (1 + markup_percentage)

    **Permissions:**
    - Requires `can_modify_costs` permission (same as editing costs)
    - Allowed roles: owner, admin_financiero, super_admin
    """
    from app.core.permissions import PERM_MODIFY_COSTS, PermissionError, check_permission

    try:
        check_permission(current_user, PERM_MODIFY_COSTS)
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to modify costs",
        )

    # Verify project belongs to tenant
    project_check = await db.execute(
        select(Project).where(
            Project.id == project_id, Project.organization_id == tenant.organization_id
        )
    )
    project = project_check.scalar_one_or_none()
    if not project:
        raise ResourceNotFoundError("Project", project_id)

    # Verify quote belongs to project
    quote_check = await db.execute(
        select(Quote).where(Quote.id == quote_id, Quote.project_id == project_id)
    )
    quote = quote_check.scalar_one_or_none()
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Quote with id {quote_id} not found for project {project_id}",
        )

    # Calculate client_price: cost * quantity * (1 + markup_percentage)
    quantity = expense_data.quantity or 1.0
    client_price = expense_data.cost * quantity * (1 + expense_data.markup_percentage)

    # Create expense
    expense = QuoteExpense(
        quote_id=quote_id,
        name=expense_data.name,
        description=expense_data.description,
        cost=expense_data.cost,
        markup_percentage=expense_data.markup_percentage,
        client_price=client_price,
        category=expense_data.category,
        quantity=quantity,
    )

    db.add(expense)
    await db.commit()
    await db.refresh(expense)

    return QuoteExpenseResponse(
        id=expense.id,
        quote_id=expense.quote_id,
        name=expense.name,
        description=expense.description,
        cost=expense.cost,
        markup_percentage=expense.markup_percentage,
        client_price=expense.client_price,
        category=expense.category,
        quantity=expense.quantity,
        created_at=expense.created_at.isoformat() if expense.created_at else None,
    )


@router.put(
    "/{project_id}/quotes/{quote_id}/expenses/{expense_id}", response_model=QuoteExpenseResponse
)
async def update_quote_expense(
    project_id: int,
    quote_id: int,
    expense_id: int,
    expense_data: QuoteExpenseCreate,
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update an expense in a quote (Sprint 15)

    **Permissions:**
    - Requires `can_modify_costs` permission
    - Allowed roles: owner, admin_financiero, super_admin
    """
    from app.core.permissions import PERM_MODIFY_COSTS, PermissionError, check_permission

    try:
        check_permission(current_user, PERM_MODIFY_COSTS)
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to modify costs",
        )

    # Verify project belongs to tenant
    project_check = await db.execute(
        select(Project).where(
            Project.id == project_id, Project.organization_id == tenant.organization_id
        )
    )
    if not project_check.scalar_one_or_none():
        raise ResourceNotFoundError("Project", project_id)

    # Verify quote and expense
    expense_result = await db.execute(
        select(QuoteExpense)
        .join(Quote)
        .where(
            QuoteExpense.id == expense_id,
            QuoteExpense.quote_id == quote_id,
            Quote.id == quote_id,
            Quote.project_id == project_id,
        )
    )
    expense = expense_result.scalar_one_or_none()
    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Expense with id {expense_id} not found for quote {quote_id}",
        )

    # Update expense
    quantity = expense_data.quantity or 1.0
    client_price = expense_data.cost * quantity * (1 + expense_data.markup_percentage)

    expense.name = expense_data.name
    expense.description = expense_data.description
    expense.cost = expense_data.cost
    expense.markup_percentage = expense_data.markup_percentage
    expense.client_price = client_price
    expense.category = expense_data.category
    expense.quantity = quantity

    await db.commit()
    await db.refresh(expense)

    return QuoteExpenseResponse(
        id=expense.id,
        quote_id=expense.quote_id,
        name=expense.name,
        description=expense.description,
        cost=expense.cost,
        markup_percentage=expense.markup_percentage,
        client_price=expense.client_price,
        category=expense.category,
        quantity=expense.quantity,
        created_at=expense.created_at.isoformat() if expense.created_at else None,
    )


@router.delete(
    "/{project_id}/quotes/{quote_id}/expenses/{expense_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_quote_expense(
    project_id: int,
    quote_id: int,
    expense_id: int,
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete an expense from a quote (Sprint 15)

    **Permissions:**
    - Requires `can_modify_costs` permission
    - Allowed roles: owner, admin_financiero, super_admin
    """
    from app.core.permissions import PERM_MODIFY_COSTS, PermissionError, check_permission

    try:
        check_permission(current_user, PERM_MODIFY_COSTS)
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to modify costs",
        )

    # Verify project belongs to tenant
    project_check = await db.execute(
        select(Project).where(
            Project.id == project_id, Project.organization_id == tenant.organization_id
        )
    )
    if not project_check.scalar_one_or_none():
        raise ResourceNotFoundError("Project", project_id)

    # Verify quote and expense
    expense_result = await db.execute(
        select(QuoteExpense)
        .join(Quote)
        .where(
            QuoteExpense.id == expense_id,
            QuoteExpense.quote_id == quote_id,
            Quote.id == quote_id,
            Quote.project_id == project_id,
        )
    )
    expense = expense_result.scalar_one_or_none()
    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Expense with id {expense_id} not found for quote {quote_id}",
        )

    await db.delete(expense)
    await db.commit()

    return None


@router.get("/{project_id}/quotes/{quote_id}/expenses", response_model=list[QuoteExpenseResponse])
async def list_quote_expenses(
    project_id: int,
    quote_id: int,
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List all expenses for a quote (Sprint 15)
    """
    # Verify project belongs to tenant
    project_check = await db.execute(
        select(Project).where(
            Project.id == project_id, Project.organization_id == tenant.organization_id
        )
    )
    if not project_check.scalar_one_or_none():
        raise ResourceNotFoundError("Project", project_id)

    # Verify quote belongs to project
    quote_check = await db.execute(
        select(Quote).where(Quote.id == quote_id, Quote.project_id == project_id)
    )
    if not quote_check.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Quote with id {quote_id} not found for project {project_id}",
        )

    # Get expenses
    expenses_result = await db.execute(
        select(QuoteExpense).where(QuoteExpense.quote_id == quote_id)
    )
    expenses = expenses_result.scalars().all()

    return [
        QuoteExpenseResponse(
            id=expense.id,
            quote_id=expense.quote_id,
            name=expense.name,
            description=expense.description,
            cost=expense.cost,
            markup_percentage=expense.markup_percentage,
            client_price=expense.client_price,
            category=expense.category,
            quantity=expense.quantity,
            created_at=expense.created_at.isoformat() if expense.created_at else None,
        )
        for expense in expenses
    ]
