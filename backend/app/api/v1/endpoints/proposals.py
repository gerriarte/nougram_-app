"""
Proposal document endpoints (independent from quote pricing).
"""

import secrets
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from app.core.config import settings
from app.core.database import get_db
from app.core.email import (
    NOUGRAM_BRAND_ACCENT,
    NOUGRAM_BRAND_DARK,
    NOUGRAM_BRAND_LOGO_URL,
    NOUGRAM_SITE_URL,
    send_email,
)
from app.core.exceptions import ResourceNotFoundError
from app.core.logging import get_logger
from app.core.permission_middleware import (
    require_modify_costs,
    require_send_quotes,
    require_view_sensitive_data,
)
from app.core.security import get_password_hash
from app.core.tenant import TenantContext, get_tenant_context
from app.models.user import User
from app.repositories.factory import RepositoryFactory
from app.schemas.ai import ExecutiveSummaryRequest, ExecutiveSummaryService
from app.schemas.proposal import (
    ProposalAssetUploadResponse,
    ProposalClientShareRequest,
    ProposalClientShareResponse,
    ProposalCreate,
    ProposalGenerateAIRequest,
    ProposalListResponse,
    ProposalResponse,
    ProposalShareStatsResponse,
    ProposalUpdate,
)
from app.services.ai_service import ai_service
from app.services.proposal_asset_service import ProposalAssetService

router = APIRouter()
logger = get_logger(__name__)
DEFAULT_PROPOSAL_ACCESS_DAYS = 30
OTP_EXPIRATION_MINUTES = 30
PROPOSAL_AI_CONTEXT_HISTORY_KEY = "proposal_ai_context_history"
MAX_PROPOSAL_AI_CONTEXT_ITEMS = 25


def _normalize_context_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _build_ai_context_payload(payload: ProposalGenerateAIRequest) -> dict[str, str]:
    return {
        "services_context": _normalize_context_text(payload.services_context),
        "proposal_objective": _normalize_context_text(payload.proposal_objective),
        "estimated_timeline": _normalize_context_text(payload.estimated_timeline),
        "payment_conditions": _normalize_context_text(payload.payment_conditions),
        "execution_conditions": _normalize_context_text(payload.execution_conditions),
        "tone": _normalize_context_text(payload.tone),
        "audience": _normalize_context_text(payload.audience),
        "differentiators": _normalize_context_text(payload.differentiators),
    }


def _build_section_plan_payload(payload: ProposalGenerateAIRequest) -> list[dict[str, Any]]:
    return [item.model_dump() for item in payload.section_plan if item.id.strip()]


def _section_plan_to_prompt(section_plan: list[dict[str, Any]]) -> str:
    if not section_plan:
        return ""
    lines = []
    for idx, item in enumerate(section_plan, start=1):
        label = _normalize_context_text(item.get("label")) or _normalize_context_text(
            item.get("id")
        )
        state = "incluir" if item.get("enabled", True) else "omitir"
        lines.append(f"{idx}. {label}: {state}")
    return "\n".join(lines)


def _read_context_history_from_settings(settings_value: Any) -> list[dict[str, Any]]:
    if not isinstance(settings_value, dict):
        return []
    history = settings_value.get(PROPOSAL_AI_CONTEXT_HISTORY_KEY)
    if not isinstance(history, list):
        return []
    normalized_history: list[dict[str, Any]] = []
    for item in history:
        if isinstance(item, dict):
            normalized_history.append(item)
    return normalized_history


def _history_to_prompt(history: list[dict[str, Any]]) -> str:
    if not history:
        return ""
    latest = history[-3:]
    blocks: list[str] = []
    for idx, item in enumerate(latest, start=1):
        objective = _normalize_context_text(item.get("proposal_objective"))
        timeline = _normalize_context_text(item.get("estimated_timeline"))
        payments = _normalize_context_text(item.get("payment_conditions"))
        execution = _normalize_context_text(item.get("execution_conditions"))
        services = _normalize_context_text(item.get("services_context"))
        blocks.append(
            f"Contexto histórico {idx}:\n"
            f"- Servicios: {services or 'N/A'}\n"
            f"- Objetivo: {objective or 'N/A'}\n"
            f"- Tiempo estimado: {timeline or 'N/A'}\n"
            f"- Condiciones de pago: {payments or 'N/A'}\n"
            f"- Condiciones de ejecución: {execution or 'N/A'}"
        )
    return "\n\n".join(blocks)


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
    logger.info(
        "Listed proposals", user_id=current_user.id, project_id=project_id, count=len(items)
    )
    return ProposalListResponse(
        items=[ProposalResponse.model_validate(item) for item in items], total=len(items)
    )


@router.post(
    "/{project_id}/proposals", response_model=ProposalResponse, status_code=status.HTTP_201_CREATED
)
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
    user_key = _normalize_context_text(payload.user_api_key) if payload.user_api_key else None
    if not user_key and not ai_service.is_available():
        raise HTTPException(status_code=503, detail="AI service unavailable")

    project_repo = RepositoryFactory.create_project_repository(db, tenant.organization_id)
    project = await project_repo.get_by_id_with_quotes(project_id, include_deleted=False)
    if not project:
        raise ResourceNotFoundError("Project", project_id)
    active_quotes = [q for q in (project.quotes or []) if bool(getattr(q, "is_active", 1))]
    if not active_quotes:
        raise HTTPException(status_code=400, detail="Cannot generate proposal without quote")

    latest_quote = sorted(active_quotes, key=lambda q: q.version, reverse=True)[0]
    services_payload = []
    for idx, item in enumerate(latest_quote.items or []):
        service_name = item.custom_service_name or (
            item.service.name if item.service else f"Servicio {idx + 1}"
        )
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

    context_payload = _build_ai_context_payload(payload)
    settings_obj = (
        tenant.organization.settings if isinstance(tenant.organization.settings, dict) else {}
    )
    history = _read_context_history_from_settings(settings_obj)
    history_prompt = _history_to_prompt(history)
    current_prompt_context = (
        f"Servicios cotizados: {context_payload['services_context'] or 'No especificado'}\n"
        f"Objetivo de la propuesta: {context_payload['proposal_objective'] or 'No especificado'}\n"
        f"Tiempo estimado de desarrollo: {context_payload['estimated_timeline'] or 'No especificado'}\n"
        f"Condiciones de pago: {context_payload['payment_conditions'] or 'No especificado'}\n"
        f"Condiciones de ejecución: {context_payload['execution_conditions'] or 'No especificado'}\n"
        f"Tono: {context_payload['tone'] or 'No especificado'}\n"
        f"Audiencia: {context_payload['audience'] or 'No especificado'}\n"
        f"Diferenciadores: {context_payload['differentiators'] or 'No especificado'}"
    )
    section_plan = _build_section_plan_payload(payload)
    section_plan_prompt = _section_plan_to_prompt(section_plan)
    composed_extra_instructions = "\n\n".join(
        block
        for block in [
            _normalize_context_text(payload.extra_instructions),
            "Contexto actual para redactar la propuesta:\n" + current_prompt_context,
            ("Plan de secciones solicitado:\n" + section_plan_prompt)
            if section_plan_prompt
            else "",
            ("Contexto útil de propuestas anteriores:\n" + history_prompt)
            if history_prompt
            else "",
        ]
        if block
    )

    summary_request = ExecutiveSummaryRequest(
        project_name=project.name,
        client_name=project.client_name,
        client_sector=None,
        services=services_payload,
        total_price=Decimal(str(latest_quote.total_client_price or 0)),
        currency=project.currency or "USD",
        language=payload.language,
    )
    if user_key:
        sections_result = await ai_service.generate_proposal_sections_with_user_key(
            user_api_key=user_key,
            ai_provider=_normalize_context_text(payload.ai_provider) or "openai",
            project_name=project.name,
            client_name=project.client_name,
            currency=project.currency or "USD",
            services=[service.service_name for service in services_payload],
            objective=context_payload["proposal_objective"],
            timeline=context_payload["estimated_timeline"],
            payment_conditions=context_payload["payment_conditions"],
            execution_conditions=context_payload["execution_conditions"],
            language=payload.language,
            extra_instructions=composed_extra_instructions,
        )
    else:
        sections_result = await ai_service.generate_proposal_sections(
            project_name=project.name,
            client_name=project.client_name,
            currency=project.currency or "USD",
            services=[service.service_name for service in services_payload],
            objective=context_payload["proposal_objective"],
            timeline=context_payload["estimated_timeline"],
            payment_conditions=context_payload["payment_conditions"],
            execution_conditions=context_payload["execution_conditions"],
            language=payload.language,
            extra_instructions=composed_extra_instructions,
        )
    if not sections_result.get("success"):
        raise HTTPException(
            status_code=500, detail=sections_result.get("error", "Failed to generate proposal")
        )

    generated_sections = sections_result.get("sections") or {}
    executive_summary = _normalize_context_text(generated_sections.get("executive_summary"))
    summary_usage = None
    if not executive_summary:
        summary_result = await ai_service.generate_executive_summary(summary_request)
        if summary_result.get("success"):
            executive_summary = _normalize_context_text(summary_result.get("summary"))
            summary_usage = summary_result.get("usage")

    raw_objectives = generated_sections.get("objectives")
    objectives = []
    if isinstance(raw_objectives, list):
        objectives = [str(item).strip() for item in raw_objectives if str(item).strip()]

    raw_deliverables = generated_sections.get("deliverables")
    deliverables = []
    if isinstance(raw_deliverables, list):
        for item in raw_deliverables:
            if isinstance(item, dict):
                name = _normalize_context_text(item.get("name"))
                if name:
                    deliverables.append(
                        {
                            "name": name,
                            "status": _normalize_context_text(item.get("status")) or "propuesto",
                        }
                    )
            else:
                name = _normalize_context_text(item)
                if name:
                    deliverables.append({"name": name, "status": "propuesto"})

    if not deliverables:
        deliverables = [
            {"name": service.service_name, "status": "propuesto"}
            for service in services_payload[:6]
        ]

    proposal_body = {
        "description": _normalize_context_text(generated_sections.get("description"))
        or f"Proyecto {project.name} para {project.client_name}",
        "objectives": objectives
        or [
            "Resolver la necesidad principal del cliente con un plan ejecutable",
            "Entregar valor medible en tiempos y alcance acordados",
        ],
        "deliverables": deliverables,
        "executive_summary": executive_summary,
        "scope": _normalize_context_text(generated_sections.get("scope")),
        "timeline": _normalize_context_text(generated_sections.get("timeline"))
        or context_payload["estimated_timeline"],
        "conditions": _normalize_context_text(generated_sections.get("conditions"))
        or "\n\n".join(
            [
                f"Condiciones de pago: {context_payload['payment_conditions']}"
                if context_payload["payment_conditions"]
                else "",
                f"Condiciones de ejecución: {context_payload['execution_conditions']}"
                if context_payload["execution_conditions"]
                else "",
            ]
        ).strip(),
        "free_text": _normalize_context_text(generated_sections.get("free_text")),
        "extra_instructions": payload.extra_instructions or "",
        "ai_context": context_payload,
        "ai_brief": {
            **context_payload,
            "extra_instructions": _normalize_context_text(payload.extra_instructions),
        },
        "layout": {
            "sections": [item["id"] for item in section_plan if item.get("enabled", True)],
            "hidden": [item["id"] for item in section_plan if not item.get("enabled", True)],
            "section_plan": section_plan,
        },
    }

    if payload.persist_context:
        context_entry = {
            **context_payload,
            "project_id": project_id,
            "saved_at": datetime.now(UTC).isoformat(),
            "saved_by_user_id": current_user.id,
        }
        history.append(context_entry)
        settings_obj[PROPOSAL_AI_CONTEXT_HISTORY_KEY] = history[-MAX_PROPOSAL_AI_CONTEXT_ITEMS:]
        tenant.organization.settings = settings_obj
        flag_modified(tenant.organization, "settings")
        await db.flush()

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

    # Persist AI usage for proposal generation (sections + optional executive summary)
    ai_usage_repo = RepositoryFactory.create_ai_usage_repository(db)
    sections_usage = sections_result.get("usage")
    if sections_usage:
        await ai_usage_repo.create_event(
            organization_id=tenant.organization_id,
            project_id=project_id,
            proposal_id=created.id,
            feature="proposal_ai_generate",
            provider=sections_result.get("provider") or "openai",
            model=getattr(ai_service, "model", None),
            prompt_tokens=sections_usage.get("prompt_tokens", 0) or 0,
            completion_tokens=sections_usage.get("completion_tokens", 0) or 0,
            total_tokens=sections_usage.get("total_tokens", 0) or 0,
            estimated_cost=sections_usage.get("estimated_cost"),
            actor_user_id=current_user.id,
        )
    if summary_usage:
        await ai_usage_repo.create_event(
            organization_id=tenant.organization_id,
            project_id=project_id,
            proposal_id=created.id,
            feature="proposal_executive_summary",
            provider="openai",
            model=getattr(ai_service, "model", None),
            prompt_tokens=summary_usage.get("prompt_tokens", 0) or 0,
            completion_tokens=summary_usage.get("completion_tokens", 0) or 0,
            total_tokens=summary_usage.get("total_tokens", 0) or 0,
            estimated_cost=summary_usage.get("estimated_cost"),
            actor_user_id=current_user.id,
        )

    return ProposalResponse.model_validate(created)


@router.get(
    "/{project_id}/proposals/{proposal_id}/share-stats",
    response_model=ProposalShareStatsResponse,
    summary="Get latest client portal share statistics for a proposal",
)
async def get_proposal_share_stats(
    project_id: int,
    proposal_id: int,
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(require_view_sensitive_data),
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

    link_repo = RepositoryFactory.create_proposal_client_link_repository(db, tenant.organization_id)
    link = await link_repo.get_latest_by_proposal(proposal_id)
    logger.info(
        "Fetched proposal share stats",
        user_id=current_user.id,
        project_id=project_id,
        proposal_id=proposal_id,
        link_id=link.id if link else None,
    )
    if not link:
        return ProposalShareStatsResponse(proposal_id=proposal_id)

    return ProposalShareStatsResponse(
        proposal_id=proposal_id,
        link_id=link.id,
        status=link.status,
        view_count=int(link.view_count or 0),
        viewed_at=link.viewed_at,
        last_sent_at=link.last_sent_at,
        decided_at=link.decided_at,
        decision_comment=link.decision_comment,
        access_expires_at=link.access_expires_at,
    )


@router.post(
    "/{project_id}/proposals/{proposal_id}/assets",
    response_model=ProposalAssetUploadResponse,
    summary="Upload logo or cover asset for a proposal",
)
async def upload_proposal_asset(
    project_id: int,
    proposal_id: int,
    asset_type: str = Form(..., pattern="^(logo|cover)$"),
    file: UploadFile = File(...),
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

    content = await file.read()
    uploaded = ProposalAssetService().upload(
        organization_id=tenant.organization_id,
        project_id=project_id,
        proposal_id=proposal_id,
        asset_type=asset_type,
        filename=file.filename or "",
        content_type=file.content_type or "",
        content=content,
    )

    body_json = proposal.body_json if isinstance(proposal.body_json, dict) else {}
    branding = body_json.get("branding") if isinstance(body_json.get("branding"), dict) else {}
    next_branding = {
        **branding,
        "logoUrl" if asset_type == "logo" else "coverImageUrl": uploaded.url,
    }
    proposal.body_json = {
        **body_json,
        "branding": next_branding,
    }
    proposal.updated_by_id = current_user.id
    updated = await proposal_repo.update(proposal)

    logger.info(
        "Uploaded proposal asset",
        user_id=current_user.id,
        project_id=project_id,
        proposal_id=proposal_id,
        asset_type=asset_type,
    )
    return ProposalAssetUploadResponse(
        success=True,
        asset_type=asset_type,
        asset_url=uploaded.url,
        asset_key=uploaded.key,
        body_json=updated.body_json if isinstance(updated.body_json, dict) else {},
    )


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
    active_quotes = [q for q in (project.quotes or []) if bool(getattr(q, "is_active", 1))]
    if quote_id is not None:
        selected_quote = next((q for q in active_quotes if q.id == quote_id), None)
        if not selected_quote:
            raise HTTPException(
                status_code=404,
                detail=f"Quote with id {quote_id} not found for project {project_id}",
            )
    elif active_quotes:
        selected_quote = sorted(active_quotes, key=lambda q: q.version, reverse=True)[0]
        quote_id = selected_quote.id

    now = datetime.now(UTC)
    max_expiration = now + timedelta(days=DEFAULT_PROPOSAL_ACCESS_DAYS)
    requested_expiration = payload.access_expires_at
    if requested_expiration is not None:
        if requested_expiration.tzinfo is None:
            requested_expiration = requested_expiration.replace(tzinfo=UTC)
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

    if payload.send_email and not (payload.to_email or "").strip():
        raise HTTPException(status_code=400, detail="to_email is required when send_email is true")

    custom_access_code = (payload.access_code or "").strip()
    access_code = custom_access_code or f"{secrets.randbelow(900000) + 100000}"
    link.access_code_hash = get_password_hash(access_code)
    # For manual share mode (without sending email), keep the code valid for the full access window.
    link.access_code_expires_at = (
        now + timedelta(minutes=OTP_EXPIRATION_MINUTES) if payload.send_email else access_expires_at
    )
    if payload.send_email:
        link.last_sent_at = now

    sender_company_name = (tenant.organization.name or "").strip() or "tu empresa"
    public_url = (
        f"{tenant.organization.settings.get('frontend_url', '')}"
        if isinstance(tenant.organization.settings, dict)
        else ""
    )
    if not public_url:
        public_url = settings.FRONTEND_URL.rstrip("/")
    public_url = f"{public_url}/client/proposals/{link.public_token}"
    access_expires_at_label = access_expires_at.strftime("%Y-%m-%d %H:%M UTC")

    if payload.send_email:
        d, a, logo, site = NOUGRAM_BRAND_DARK, NOUGRAM_BRAND_ACCENT, NOUGRAM_BRAND_LOGO_URL, NOUGRAM_SITE_URL
        email_html = f"""
        <!DOCTYPE html><html><head><meta charset="utf-8"></head>
        <body style="margin:0;padding:0;background:#ebebf0;font-family:Arial,sans-serif;">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#ebebf0;padding:24px 16px;"><tr><td align="center">
        <table role="presentation" width="100%" style="max-width:600px;background:#fff;border-radius:12px;border:1px solid #d4d4dc;overflow:hidden;"><tr>
        <td style="padding:20px 24px;text-align:center;background:{d};">
        <a href="{site}" target="_blank" rel="noopener noreferrer" style="text-decoration:none;display:inline-block;">
        <img src="{logo}" alt="Nougram" width="140" style="display:block;margin:0 auto;border:0;max-width:140px;width:140px;height:auto;" /></a></td></tr><tr>
        <td style="padding:24px;color:{d};">
          <h2 style="margin:0 0 16px;font-size:20px;font-weight:600;">Tienes una propuesta de «{sender_company_name}»</h2>
          <p style="margin:0 0 16px;line-height:1.6;">Hola, tienes una propuesta comercial disponible para revisar.</p>
          <p style="margin:0 0 8px;"><strong>Proyecto:</strong> {project.name}</p>
          <p style="margin:0 0 8px;"><strong>Cliente:</strong> {project.client_name}</p>
          <p style="margin:0 0 8px;"><strong>Vigencia del acceso:</strong> hasta {access_expires_at_label}</p>
          <p style="margin:0 0 20px;"><strong>Clave temporal:</strong> <span style="font-size:18px;font-weight:700;color:{a};">{access_code}</span> (expira en {OTP_EXPIRATION_MINUTES} minutos)</p>
          <table role="presentation" cellspacing="0" cellpadding="0"><tr>
          <td style="border-radius:8px;background:{a};">
          <a href="{public_url}" style="display:inline-block;padding:12px 20px;color:#fff !important;text-decoration:none;font-weight:600;">Ver propuesta</a>
          </td></tr></table>
          <p style="margin:20px 0 8px;line-height:1.6;">También podrás aceptar, rechazar o solicitar revisión.</p>
          <p>{payload.message or ""}</p>
        </td></tr></table></td></tr></table>
        </body></html>
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
            to_email=payload.to_email or "",
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

    if payload.send_email:
        message = f"Proposal access sent successfully to {payload.to_email}"
    else:
        message = "Proposal access generated successfully without sending email"

    return ProposalClientShareResponse(
        success=True,
        message=message,
        public_url=public_url,
        access_expires_at=link.access_expires_at,
        last_sent_at=link.last_sent_at,
        access_code=access_code,
        sent_email=payload.send_email,
    )
