"""
Proposal document endpoints (independent from quote pricing).
"""
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import ResourceNotFoundError
from app.core.logging import get_logger
from app.core.permission_middleware import require_modify_costs, require_send_quotes, require_view_sensitive_data
from app.core.tenant import TenantContext, get_tenant_context
from app.models.user import User
from app.repositories.factory import RepositoryFactory
from app.schemas.ai import ExecutiveSummaryRequest, ExecutiveSummaryService
from app.schemas.proposal import (
    ProposalCreate,
    ProposalGenerateAIRequest,
    ProposalListResponse,
    ProposalResponse,
    ProposalUpdate,
)
from app.services.ai_service import ai_service

router = APIRouter()
logger = get_logger(__name__)


@router.get("/{project_id}/proposals", response_model=ProposalListResponse)
async def list_project_proposals(
    project_id: int,
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(require_view_sensitive_data),
    db: AsyncSession = Depends(get_db),
):
    project_repo = RepositoryFactory.create_project_repository(db, tenant.organization_id)
    project = await project_repo.get_by_id(project_id, include_deleted=False)
    if not project:
        raise ResourceNotFoundError("Project", project_id)

    proposal_repo = RepositoryFactory.create_proposal_repository(db, tenant.organization_id)
    items = await proposal_repo.get_by_project(project_id)
    logger.info("Listed proposals", user_id=current_user.id, project_id=project_id, count=len(items))
    return ProposalListResponse(items=[ProposalResponse.model_validate(item) for item in items], total=len(items))


@router.post("/{project_id}/proposals", response_model=ProposalResponse, status_code=status.HTTP_201_CREATED)
async def create_project_proposal(
    project_id: int,
    payload: ProposalCreate,
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(require_modify_costs),
    db: AsyncSession = Depends(get_db),
):
    project_repo = RepositoryFactory.create_project_repository(db, tenant.organization_id)
    project = await project_repo.get_by_id(project_id, include_deleted=False)
    if not project:
        raise ResourceNotFoundError("Project", project_id)

    proposal_repo = RepositoryFactory.create_proposal_repository(db, tenant.organization_id)
    latest = await proposal_repo.get_latest_by_project(project_id)
    next_version = (latest.version + 1) if latest else 1

    from app.models.proposal import ProposalDocument
    entity = ProposalDocument(
        project_id=project_id,
        organization_id=tenant.organization_id,
        version=next_version,
        title=payload.title,
        body_json=payload.body_json,
        status=payload.status,
        created_by_id=current_user.id,
        updated_by_id=current_user.id,
        is_locked=0,
    )
    created = await proposal_repo.create(entity)
    return ProposalResponse.model_validate(created)


@router.put("/{project_id}/proposals/{proposal_id}", response_model=ProposalResponse)
async def update_project_proposal(
    project_id: int,
    proposal_id: int,
    payload: ProposalUpdate,
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(require_modify_costs),
    db: AsyncSession = Depends(get_db),
):
    project_repo = RepositoryFactory.create_project_repository(db, tenant.organization_id)
    project = await project_repo.get_by_id(project_id, include_deleted=False)
    if not project:
        raise ResourceNotFoundError("Project", project_id)

    proposal_repo = RepositoryFactory.create_proposal_repository(db, tenant.organization_id)
    proposal = await proposal_repo.get_by_id(proposal_id)
    if not proposal or proposal.project_id != project_id:
        raise ResourceNotFoundError("Proposal", proposal_id)
    if proposal.is_locked:
        raise HTTPException(status_code=409, detail="Proposal is locked and cannot be edited")

    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        if field == "is_locked":
            setattr(proposal, field, 1 if value else 0)
        else:
            setattr(proposal, field, value)
    proposal.updated_by_id = current_user.id
    updated = await proposal_repo.update(proposal)
    return ProposalResponse.model_validate(updated)


@router.post("/{project_id}/proposals/ai-generate", response_model=ProposalResponse)
async def generate_proposal_with_ai(
    project_id: int,
    payload: ProposalGenerateAIRequest,
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(require_send_quotes),
    db: AsyncSession = Depends(get_db),
):
    if not ai_service.is_available():
        raise HTTPException(status_code=503, detail="AI service unavailable")

    project_repo = RepositoryFactory.create_project_repository(db, tenant.organization_id)
    project = await project_repo.get_by_id_with_quotes(project_id, include_deleted=False)
    if not project:
        raise ResourceNotFoundError("Project", project_id)
    if not project.quotes:
        raise HTTPException(status_code=400, detail="Cannot generate proposal without quote")

    latest_quote = sorted(project.quotes, key=lambda q: q.version, reverse=True)[0]
    services_payload = []
    for idx, item in enumerate(latest_quote.items or []):
        service_name = item.service.name if item.service else f"Servicio {idx + 1}"
        services_payload.append(
            ExecutiveSummaryService(
                service_id=item.service_id,
                service_name=service_name,
                estimated_hours=float(item.estimated_hours or 0),
                client_price=Decimal(str(item.client_price or 0)),
            )
        )
    if not services_payload:
        raise HTTPException(status_code=400, detail="Cannot generate proposal without quote items")

    summary_request = ExecutiveSummaryRequest(
        project_name=project.name,
        client_name=project.client_name,
        client_sector=None,
        services=services_payload,
        total_price=Decimal(str(latest_quote.total_client_price or 0)),
        currency=project.currency or "USD",
        language=payload.language,
    )
    result = await ai_service.generate_executive_summary(summary_request)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Failed to generate proposal"))

    proposal_body = {
        "description": f"Proyecto {project.name} para {project.client_name}",
        "objectives": [
            "Resolver la necesidad principal del cliente con un plan ejecutable",
            "Entregar valor medible en tiempos y alcance acordados",
        ],
        "deliverables": [
            {"name": "Documento de alcance", "status": "propuesto"},
            {"name": "Plan de trabajo", "status": "propuesto"},
        ],
        "executive_summary": result.get("summary", ""),
        "extra_instructions": payload.extra_instructions or "",
    }

    proposal_repo = RepositoryFactory.create_proposal_repository(db, tenant.organization_id)
    latest = await proposal_repo.get_latest_by_project(project_id)
    next_version = (latest.version + 1) if latest else 1

    from app.models.proposal import ProposalDocument
    entity = ProposalDocument(
        project_id=project_id,
        organization_id=tenant.organization_id,
        version=next_version,
        title=payload.title or f"Propuesta comercial V{next_version}",
        body_json=proposal_body,
        status="draft",
        created_by_id=current_user.id,
        updated_by_id=current_user.id,
        is_locked=0,
    )
    created = await proposal_repo.create(entity)
    return ProposalResponse.model_validate(created)
