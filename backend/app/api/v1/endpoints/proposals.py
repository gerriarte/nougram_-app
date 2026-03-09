"""
Proposal document endpoints (independent from quote pricing).
"""
from decimal import Decimal
from datetime import datetime, timedelta, timezone
import secrets

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.email import send_email
from app.core.exceptions import ResourceNotFoundError
from app.core.logging import get_logger
from app.core.permission_middleware import require_modify_costs, require_send_quotes, require_view_sensitive_data
from app.core.security import get_password_hash
from app.core.tenant import TenantContext, get_tenant_context
from app.models.user import User
from app.repositories.factory import RepositoryFactory
from app.schemas.ai import ExecutiveSummaryRequest, ExecutiveSummaryService
from app.schemas.proposal import (
    ProposalCreate,
    ProposalClientShareRequest,
    ProposalClientShareResponse,
    ProposalGenerateAIRequest,
    ProposalListResponse,
    ProposalResponse,
    ProposalUpdate,
)
from app.services.ai_service import ai_service

router = APIRouter()
logger = get_logger(__name__)
DEFAULT_PROPOSAL_ACCESS_DAYS = 30
OTP_EXPIRATION_MINUTES = 30


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
        "scope": "",
        "timeline": "",
        "conditions": "",
        "free_text": "",
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


@router.post(
    "/{project_id}/proposals/{proposal_id}/share",
    response_model=ProposalClientShareResponse,
    summary="Share proposal with secure client portal link",
)
async def share_proposal_with_client(
    project_id: int,
    proposal_id: int,
    payload: ProposalClientShareRequest,
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(require_send_quotes),
    db: AsyncSession = Depends(get_db),
):
    project_repo = RepositoryFactory.create_project_repository(db, tenant.organization_id)
    project = await project_repo.get_by_id_with_quotes(project_id, include_deleted=False)
    if not project:
        raise ResourceNotFoundError("Project", project_id)

    proposal_repo = RepositoryFactory.create_proposal_repository(db, tenant.organization_id)
    proposal = await proposal_repo.get_by_id(proposal_id)
    if not proposal or proposal.project_id != project_id:
        raise ResourceNotFoundError("Proposal", proposal_id)

    quote_id = payload.quote_id
    selected_quote = None
    if quote_id is not None:
        selected_quote = next((q for q in (project.quotes or []) if q.id == quote_id), None)
        if not selected_quote:
            raise HTTPException(status_code=404, detail=f"Quote with id {quote_id} not found for project {project_id}")
    elif project.quotes:
        selected_quote = sorted(project.quotes, key=lambda q: q.version, reverse=True)[0]
        quote_id = selected_quote.id

    now = datetime.now(timezone.utc)
    max_expiration = now + timedelta(days=DEFAULT_PROPOSAL_ACCESS_DAYS)
    requested_expiration = payload.access_expires_at
    if requested_expiration is not None:
        if requested_expiration.tzinfo is None:
            requested_expiration = requested_expiration.replace(tzinfo=timezone.utc)
        if requested_expiration <= now:
            raise HTTPException(status_code=400, detail="access_expires_at must be in the future")
        if requested_expiration > max_expiration:
            raise HTTPException(
                status_code=400,
                detail=f"Client access cannot exceed {DEFAULT_PROPOSAL_ACCESS_DAYS} days",
            )
        access_expires_at = requested_expiration
    else:
        access_expires_at = max_expiration

    link_repo = RepositoryFactory.create_proposal_client_link_repository(db, tenant.organization_id)
    existing_link = await link_repo.get_latest_by_proposal(proposal_id)
    if existing_link and existing_link.is_active == 1:
        link = existing_link
        link.access_expires_at = access_expires_at
        link.quote_id = quote_id
        link.updated_by_id = current_user.id
    else:
        from app.models.proposal import ProposalClientLink

        link = ProposalClientLink(
            proposal_id=proposal_id,
            project_id=project_id,
            organization_id=tenant.organization_id,
            quote_id=quote_id,
            public_token=secrets.token_urlsafe(24),
            access_expires_at=access_expires_at,
            status="sent",
            is_active=1,
            created_by_id=current_user.id,
            updated_by_id=current_user.id,
        )
        link = await link_repo.create(link)

    custom_access_code = (payload.access_code or "").strip()
    access_code = custom_access_code or f"{secrets.randbelow(900000) + 100000}"
    link.access_code_hash = get_password_hash(access_code)
    link.access_code_expires_at = now + timedelta(minutes=OTP_EXPIRATION_MINUTES)
    link.last_sent_at = now

    sender_company_name = (tenant.organization.name or "").strip() or "tu empresa"
    public_url = f"{tenant.organization.settings.get('frontend_url', '')}" if isinstance(tenant.organization.settings, dict) else ""
    if not public_url:
        public_url = settings.FRONTEND_URL.rstrip("/")
    public_url = f"{public_url}/client/proposals/{link.public_token}"
    access_expires_at_label = access_expires_at.strftime('%Y-%m-%d %H:%M UTC')

    email_html = f"""
    <div style="font-family: Arial, sans-serif; line-height: 1.6;">
      <h2>Tienes una Propuesta de "{sender_company_name}"</h2>
      <p>Hola, tienes una propuesta comercial disponible para revisar.</p>
      <p><strong>Proyecto:</strong> {project.name}</p>
      <p><strong>Cliente:</strong> {project.client_name}</p>
      <p><strong>Vigencia del acceso:</strong> hasta {access_expires_at_label}</p>
      <p><strong>Clave temporal:</strong> <span style="font-size: 18px;">{access_code}</span> (expira en {OTP_EXPIRATION_MINUTES} minutos)</p>
      <p><a href="{public_url}" style="display:inline-block;padding:10px 14px;background:#111827;color:#fff;text-decoration:none;border-radius:6px;">Ver propuesta</a></p>
      <p>También podrás aceptar, rechazar o solicitar revisión.</p>
      <p>{payload.message or ''}</p>
    </div>
    """
    email_text = (
        f'Tienes una Propuesta de "{sender_company_name}"\n'
        f"Proyecto: {project.name}\n"
        f"Cliente: {project.client_name}\n"
        f"Link: {public_url}\n"
        f"Clave temporal: {access_code}\n"
        f"Clave válida por {OTP_EXPIRATION_MINUTES} minutos\n"
        f"Acceso disponible hasta: {access_expires_at_label}\n"
    )
    proposal_share_template_id = (
        (settings.MAILERSEND_TEMPLATE_PROPOSAL_SHARE_ID or "").strip()
        or (settings.MAILERSEND_TEMPLATE_QUOTE_ID or "").strip()
        or None
    )
    proposal_share_template_data = {
        "sender_company_name": sender_company_name,
        "project_name": project.name,
        "client_name": project.client_name,
        "access_code": access_code,
        "public_url": public_url,
        "access_expires_at": access_expires_at_label,
        "message": payload.message or "",
    }

    success = await send_email(
        to_email=payload.to_email,
        subject=f'Tienes una Propuesta de "{sender_company_name}"',
        body_html=email_html,
        body_text=email_text,
        template_id=proposal_share_template_id,
        template_data=proposal_share_template_data,
    )
    if not success:
        raise HTTPException(status_code=500, detail="Failed to send proposal access email")

    await db.commit()
    await db.refresh(link)

    return ProposalClientShareResponse(
        success=True,
        message=f"Proposal access sent successfully to {payload.to_email}",
        public_url=public_url,
        access_expires_at=link.access_expires_at,
        last_sent_at=link.last_sent_at,
    )
