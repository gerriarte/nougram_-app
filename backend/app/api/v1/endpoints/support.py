"""
Support endpoints for support roles (support_manager, data_analyst, super_admin).

Support personnel must see anonymized data by default, while super_admin may
see raw values. This module centralizes those read-only helper APIs.
"""

from __future__ import annotations

import csv
import json
from datetime import datetime
from io import StringIO
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy import func, select, text
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.logging import get_logger
from app.core.permission_middleware import require_role_decorator, require_support_role_decorator
from app.core.permissions import get_user_role
from app.core.plan_limits import PLAN_LIMITS
from app.models.ai_usage import AIUsageEvent
from app.models.audit_log import AuditLog
from app.models.project import Project, Quote
from app.models.proposal import ProposalClientLink
from app.models.subscription import Subscription
from app.models.team import TeamMember
from app.models.user import User
from app.repositories.factory import RepositoryFactory
from app.repositories.organization_repository import OrganizationRepository
from app.schemas.organization import OrganizationResponse
from app.services.credit_service import CreditService
from app.services.data_anonymizer import (
    anonymize_organization_data,
    anonymize_project_cost_data,
    anonymize_quote_totals,
    anonymize_team_salaries,
    anonymize_usage_metrics,
)

logger = get_logger(__name__)

router = APIRouter(prefix="/support", tags=["Support"])
require_support_user = require_support_role_decorator(
    ["super_admin", "support_manager", "data_analyst"]
)
require_super_admin = require_role_decorator(["super_admin"])


def _is_super_admin(user: User) -> bool:
    return get_user_role(user) == "super_admin"


async def _count_quotes(db: AsyncSession, organization_id: int) -> int:
    stmt = (
        select(func.count(Quote.id))
        .join(Project, Quote.project_id == Project.id)
        .where(Project.organization_id == organization_id)
    )
    result = await db.execute(stmt)
    return result.scalar() or 0


async def _load_projects(
    db: AsyncSession, organization_ids: list[int] | None = None
) -> list[Project]:
    stmt = select(Project).options(selectinload(Project.quotes))
    if organization_ids:
        stmt = stmt.where(Project.organization_id.in_(organization_ids))
    result = await db.execute(stmt)
    return list(result.scalars().unique().all())


async def _load_quotes(db: AsyncSession, organization_ids: list[int] | None = None) -> list[Quote]:
    stmt = select(Quote).join(Project, Quote.project_id == Project.id)
    if organization_ids:
        stmt = stmt.where(Project.organization_id.in_(organization_ids))
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def _load_team_members(
    db: AsyncSession, organization_ids: list[int] | None = None
) -> list[TeamMember]:
    stmt = select(TeamMember)
    if organization_ids:
        stmt = stmt.where(TeamMember.organization_id.in_(organization_ids))
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.get("/organizations", summary="List organizations for support roles")
async def list_support_organizations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    include_inactive: bool = Query(False),
    current_user: User = Depends(require_support_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    repo = OrganizationRepository(db)
    organizations, total = await repo.list_all(
        page=page, page_size=page_size, include_inactive=include_inactive
    )

    if _is_super_admin(current_user):
        items = [OrganizationResponse.model_validate(org).model_dump() for org in organizations]
    else:
        items = [anonymize_organization_data(org) for org in organizations]

    return {
        "items": items,
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": (total + page_size - 1) // page_size if total else 0,
    }


@router.get(
    "/organizations/{organization_id}",
    summary="Get organization details (anonymized for support)",
)
async def get_support_organization(
    organization_id: int,
    current_user: User = Depends(require_support_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    repo = OrganizationRepository(db)
    organization = await repo.get_by_id(organization_id)
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Organization {organization_id} not found",
        )

    if _is_super_admin(current_user):
        return OrganizationResponse.model_validate(organization).model_dump()

    return anonymize_organization_data(organization)


@router.get(
    "/organizations/{organization_id}/usage",
    summary="Usage metrics (anonymized) for support roles",
)
async def get_support_organization_usage(
    organization_id: int,
    current_user: User = Depends(require_support_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    repo = OrganizationRepository(db)
    organization = await repo.get_by_id(organization_id)
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Organization {organization_id} not found",
        )

    user_count = await repo.get_user_count(organization_id)
    project_count = await repo.get_project_count(organization_id)
    quote_count = await _count_quotes(db, organization_id)
    balance = await CreditService.get_credit_balance(organization_id, db)
    plan_key = (organization.subscription_plan or "free").lower()
    plan_limits = PLAN_LIMITS.get(plan_key, PLAN_LIMITS["free"])
    max_users = int(plan_limits.get("max_users", 0))
    max_projects = int(plan_limits.get("max_projects", 0))
    credits_per_month = int(plan_limits.get("credits_per_month", 0))
    users_remaining = -1 if max_users == -1 else max(0, max_users - user_count)
    projects_remaining = -1 if max_projects == -1 else max(0, max_projects - project_count)
    credits_available = balance.get("credits_available")
    credits_used_this_month = balance.get("credits_used_this_month")

    if _is_super_admin(current_user):
        return {
            "organization": OrganizationResponse.model_validate(organization).model_dump(),
            "metrics": {
                "user_count": user_count,
                "project_count": project_count,
                "quote_count": quote_count,
                "credits_available": credits_available,
                "credits_used_this_month": credits_used_this_month,
                "plan_limits": {
                    "max_users": max_users,
                    "max_projects": max_projects,
                    "max_services": int(plan_limits.get("max_services", 0)),
                    "max_team_members": int(plan_limits.get("max_team_members", 0)),
                    "credits_per_month": credits_per_month,
                },
                "remaining_capacity": {
                    "users_remaining": users_remaining,
                    "projects_remaining": projects_remaining,
                },
                "quote_policy": {
                    "is_credit_based": True,
                    "scope": "organization",
                    "message": "Las cotizaciones consumen creditos a nivel empresa (tenant), no por usuario.",
                },
            },
        }

    metrics = anonymize_usage_metrics(
        user_count=user_count,
        project_count=project_count,
        quote_count=quote_count,
        credits_available=balance.get("credits_available"),
        credits_used_this_month=balance.get("credits_used_this_month"),
    )
    return {
        "organization": anonymize_organization_data(organization),
        "metrics": metrics,
    }


async def _build_datasets(
    db: AsyncSession, org_ids: list[int] | None, include_sensitive: bool
) -> dict[str, Any]:
    repo = OrganizationRepository(db)
    if org_ids:
        organizations = [await repo.get_by_id(org_id) for org_id in org_ids]
        organizations = [org for org in organizations if org]
    else:
        organizations, _ = await repo.list_all(page=1, page_size=500, include_inactive=True)

    organization_ids = [org.id for org in organizations]
    projects = await _load_projects(db, organization_ids)
    quotes = await _load_quotes(db, organization_ids)
    team_members = await _load_team_members(db, organization_ids)

    organizations_payload = [
        OrganizationResponse.model_validate(org).model_dump()
        if include_sensitive
        else anonymize_organization_data(org)
        for org in organizations
    ]
    projects_payload = [
        {
            "id": project.id,
            "name": project.name,
            "client_name": project.client_name,
            "status": project.status,
            "organization_id": project.organization_id,
            "created_at": project.created_at.isoformat() if project.created_at else None,
        }
        if include_sensitive
        else anonymize_project_cost_data(project, getattr(project, "currency", "USD"))
        for project in projects
    ]
    quotes_payload = [
        {
            "id": quote.id,
            "project_id": quote.project_id,
            "version": quote.version,
            "total_internal_cost": float(quote.total_internal_cost),
            "total_client_price": float(quote.total_client_price),
            "margin_percentage": quote.margin_percentage,
            "notes": quote.notes,
        }
        if include_sensitive
        else anonymize_quote_totals(quote, getattr(quote, "currency", "USD"))
        for quote in quotes
    ]
    team_payload = [
        {
            "id": member.id,
            "name": member.name,
            "role": member.role,
            "salary_monthly_brute": float(member.salary_monthly_brute)
            if member.salary_monthly_brute
            else None,
            "currency": member.currency,
            "organization_id": member.organization_id,
        }
        if include_sensitive
        else anonymize_team_salaries([member], member.currency or "USD")[0]
        for member in team_members
    ]

    return {
        "organizations": organizations_payload,
        "projects": projects_payload,
        "quotes": quotes_payload,
        "team_members": team_payload,
    }


@router.get(
    "/datasets",
    summary="Get anonymized datasets",
    description="Returns anonymized datasets. Super admins receive raw values.",
)
async def get_anonymized_datasets(
    dataset_type: str | None = Query(
        None, description="organizations, projects, quotes or team_members"
    ),
    organization_id: int | None = Query(None, description="Optional organization filter"),
    current_user: User = Depends(require_support_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    org_ids = [organization_id] if organization_id else None
    datasets = await _build_datasets(
        db=db,
        org_ids=org_ids,
        include_sensitive=_is_super_admin(current_user),
    )

    if dataset_type:
        if dataset_type not in datasets:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid dataset_type '{dataset_type}'. "
                f"Valid options: {list(datasets.keys())}",
            )
        return {dataset_type: datasets[dataset_type]}

    return datasets


@router.post("/datasets/export", summary="Export datasets as JSON or CSV")
async def export_anonymized_dataset(
    dataset_type: str = Query(..., description="organizations, projects, quotes or team_members"),
    export_format: str = Query("json", description="json or csv"),
    organization_id: int | None = Query(None, description="Optional organization filter"),
    current_user: User = Depends(require_support_user),
    db: AsyncSession = Depends(get_db),
):
    dataset = await get_anonymized_datasets(
        dataset_type=dataset_type,
        organization_id=organization_id,
        current_user=current_user,
        db=db,
    )
    data = dataset.get(dataset_type, [])

    if export_format.lower() == "json":
        return JSONResponse(content=data)

    if export_format.lower() == "csv":
        if not data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No data available for dataset '{dataset_type}'",
            )
        if not isinstance(data, list) or not isinstance(data[0], dict):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CSV export requires a list of dictionaries",
            )

        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=list(data[0].keys()))
        writer.writeheader()
        writer.writerows(data)
        output.seek(0)

        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f'attachment; filename="{dataset_type}_anonymized.csv"'
            },
        )

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid export_format. Use 'json' or 'csv'.",
    )


# --- Super-admin-only analytics (proposal consumption, AI usage, paid accounts) ---

PAID_PLANS = ("starter", "professional", "enterprise")
PAID_STATUSES = ("active", "trialing", "past_due")


@router.get(
    "/analytics/proposals",
    summary="Proposal consumption by tenant (super_admin only)",
)
async def get_support_analytics_proposals(
    organization_id: int | None = Query(None),
    since: datetime | None = Query(None),
    until: datetime | None = Query(None),
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Aggregate proposal client links by organization: total, sent, viewed, accepted, rejected, revision_requested."""
    base = select(
        ProposalClientLink.organization_id,
        func.count(ProposalClientLink.id).label("total_links"),
        func.count(ProposalClientLink.id)
        .filter(ProposalClientLink.last_sent_at.isnot(None))
        .label("sent_count"),
        func.count(ProposalClientLink.id)
        .filter(ProposalClientLink.view_count > 0)
        .label("viewed_count"),
        func.count(ProposalClientLink.id)
        .filter(ProposalClientLink.status == "accepted")
        .label("accepted_count"),
        func.count(ProposalClientLink.id)
        .filter(ProposalClientLink.status == "rejected")
        .label("rejected_count"),
        func.count(ProposalClientLink.id)
        .filter(ProposalClientLink.status == "revision_requested")
        .label("revision_count"),
    ).group_by(ProposalClientLink.organization_id)
    if organization_id is not None:
        base = base.where(ProposalClientLink.organization_id == organization_id)
    if since is not None:
        base = base.where(ProposalClientLink.created_at >= since)
    if until is not None:
        base = base.where(ProposalClientLink.created_at <= until)
    result = await db.execute(base)
    rows = result.all()
    items = [
        {
            "organization_id": r.organization_id,
            "total_links": r.total_links,
            "sent_count": r.sent_count,
            "viewed_count": r.viewed_count,
            "accepted_count": r.accepted_count,
            "rejected_count": r.rejected_count,
            "revision_count": r.revision_count,
        }
        for r in rows
    ]
    return {"items": items}


@router.get(
    "/analytics/subscription-history",
    summary="Subscription change history by tenant (super_admin only)",
)
async def get_support_analytics_subscription_history(
    organization_id: int | None = Query(None),
    since: datetime | None = Query(None),
    until: datetime | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    base = select(AuditLog).where(AuditLog.action == "subscription.update")
    if organization_id is not None:
        base = base.where(AuditLog.organization_id == organization_id)
    if since is not None:
        base = base.where(AuditLog.created_at >= since)
    if until is not None:
        base = base.where(AuditLog.created_at <= until)
    base = base.order_by(AuditLog.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(base)
    logs = result.scalars().all()

    items: list[dict[str, Any]] = []
    for log in logs:
        details: dict[str, Any] = {}
        if log.details:
            try:
                details = json.loads(log.details)
            except json.JSONDecodeError:
                details = {"raw": log.details}
        items.append(
            {
                "id": log.id,
                "organization_id": log.organization_id,
                "user_id": log.user_id,
                "status": log.status,
                "previous_plan": details.get("previous_plan"),
                "new_plan": details.get("new_plan"),
                "previous_status": details.get("previous_status"),
                "new_status": details.get("new_status"),
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
        )

    return {"items": items}


@router.get(
    "/analytics/ai-usage",
    summary="AI token/cost aggregates by tenant (super_admin only)",
)
async def get_support_analytics_ai_usage(
    organization_id: int | None = Query(None),
    since: datetime | None = Query(None),
    until: datetime | None = Query(None),
    feature: str | None = Query(None, description="e.g. proposal_ai_generate"),
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Aggregate AI usage events by organization (tokens and estimated cost)."""
    base = select(
        AIUsageEvent.organization_id,
        func.count(AIUsageEvent.id).label("event_count"),
        func.coalesce(func.sum(AIUsageEvent.prompt_tokens), 0).label("total_prompt_tokens"),
        func.coalesce(func.sum(AIUsageEvent.completion_tokens), 0).label("total_completion_tokens"),
        func.coalesce(func.sum(AIUsageEvent.total_tokens), 0).label("total_tokens"),
        func.coalesce(func.sum(AIUsageEvent.estimated_cost), 0).label("total_estimated_cost"),
    ).group_by(AIUsageEvent.organization_id)
    if organization_id is not None:
        base = base.where(AIUsageEvent.organization_id == organization_id)
    if since is not None:
        base = base.where(AIUsageEvent.created_at >= since)
    if until is not None:
        base = base.where(AIUsageEvent.created_at <= until)
    if feature is not None:
        base = base.where(AIUsageEvent.feature == feature)
    result = await db.execute(base)
    rows = result.all()
    items = [
        {
            "organization_id": r.organization_id,
            "event_count": r.event_count,
            "total_prompt_tokens": r.total_prompt_tokens,
            "total_completion_tokens": r.total_completion_tokens,
            "total_tokens": r.total_tokens,
            "total_estimated_cost_usd": float(r.total_estimated_cost)
            if r.total_estimated_cost
            else 0.0,
        }
        for r in rows
    ]
    return {"items": items}


@router.get(
    "/analytics/paid-accounts",
    summary="Paid-account summary by tenant (super_admin only)",
)
async def get_support_analytics_paid_accounts(
    organization_id: int | None = Query(None),
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """List organizations with paid plans (starter/professional/enterprise) and status active/trialing/past_due."""
    subscriptions_table_exists = True
    try:
        table_check = await db.execute(
            text(
                "SELECT EXISTS ("
                "SELECT 1 FROM information_schema.tables "
                "WHERE table_schema = 'public' AND table_name = 'subscriptions'"
                ") AS exists"
            )
        )
        subscriptions_table_exists = bool(table_check.scalar())
    except Exception:
        subscriptions_table_exists = False

    if subscriptions_table_exists:
        try:
            base = select(Subscription).where(
                Subscription.plan.in_(PAID_PLANS),
                Subscription.status.in_(PAID_STATUSES),
            )
            if organization_id is not None:
                base = base.where(Subscription.organization_id == organization_id)
            result = await db.execute(base)
            subs = result.scalars().unique().all()
            items = [
                {
                    "organization_id": s.organization_id,
                    "plan": s.plan,
                    "status": s.status,
                    "current_period_start": s.current_period_start.isoformat()
                    if s.current_period_start
                    else None,
                    "current_period_end": s.current_period_end.isoformat()
                    if s.current_period_end
                    else None,
                }
                for s in subs
            ]
            return {"items": items}
        except ProgrammingError:
            # Safety fallback for legacy envs where metadata exists but table does not.
            pass

    # Legacy fallback: use organization-level subscription fields.
    from app.models.organization import Organization

    org_query = select(Organization).where(
        Organization.subscription_plan.in_(PAID_PLANS),
        Organization.subscription_status.in_(PAID_STATUSES),
    )
    if organization_id is not None:
        org_query = org_query.where(Organization.id == organization_id)
    org_result = await db.execute(org_query)
    orgs = org_result.scalars().all()
    return {
        "items": [
            {
                "organization_id": org.id,
                "plan": org.subscription_plan,
                "status": org.subscription_status,
                "current_period_start": None,
                "current_period_end": None,
            }
            for org in orgs
        ]
    }


@router.get(
    "/analytics/financial-ledger",
    summary="Financial event ledger by tenant (super_admin only)",
)
async def get_support_analytics_financial_ledger(
    organization_id: int | None = Query(None),
    since: datetime | None = Query(None),
    until: datetime | None = Query(None),
    provider: str | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """List financial ledger events (manual now, Wompi-ready)."""
    from app.models.financial_ledger import FinancialLedgerEvent

    base = select(FinancialLedgerEvent)
    if organization_id is not None:
        base = base.where(FinancialLedgerEvent.organization_id == organization_id)
    if since is not None:
        base = base.where(FinancialLedgerEvent.created_at >= since)
    if until is not None:
        base = base.where(FinancialLedgerEvent.created_at <= until)
    if provider is not None:
        base = base.where(FinancialLedgerEvent.provider == provider)
    base = base.order_by(FinancialLedgerEvent.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(base)
    events = result.scalars().unique().all()
    items = [
        {
            "id": e.id,
            "organization_id": e.organization_id,
            "event_type": e.event_type,
            "provider": e.provider,
            "amount": float(e.amount),
            "currency": e.currency,
            "status": e.status,
            "external_id": e.external_id,
            "reference": e.reference,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }
        for e in events
    ]
    return {"items": items}


@router.get(
    "/billing-requests",
    summary="Manual billing requests queue (super_admin only)",
)
async def get_support_billing_requests(
    organization_id: int | None = Query(None),
    status_filter: str | None = Query(
        None,
        alias="status",
        description="Filter by status (pending, processed, dismissed)",
    ),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Fallback queue for super admins when email notifications fail.
    """
    billing_request_repo = RepositoryFactory.create_billing_request_repository(db)
    items, total = await billing_request_repo.list_requests(
        organization_id=organization_id,
        status=status_filter,
        limit=limit,
        offset=offset,
    )

    payload = [
        {
            "id": req.id,
            "organization_id": req.organization_id,
            "organization_name": req.organization.name if req.organization else None,
            "requested_by_user_id": req.requested_by_user_id,
            "requested_by_email": req.requested_by_user.email if req.requested_by_user else None,
            "requested_by_name": req.requested_by_user.full_name if req.requested_by_user else None,
            "request_type": req.request_type,
            "target_plan": req.target_plan,
            "target_interval": req.target_interval,
            "notes": req.notes,
            "status": req.status,
            "created_at": req.created_at.isoformat() if req.created_at else None,
        }
        for req in items
    ]
    return {
        "items": payload,
        "total": total,
        "limit": limit,
        "offset": offset,
    }
