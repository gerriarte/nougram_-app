"""
Quote Agent (chat) endpoints.

Gated per-tenant via ``require_quote_agent_enabled`` (super admin enables the
module on the organization). The agent estimates in real time using the
deterministic engine; only ``/confirm`` persists a draft Project+Quote (and
consumes 1 credit), which then enters the existing follow-up pipeline.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.ai import _enforce_ai_rate_limit_by_plan
from app.core.database import get_db
from app.core.logging import get_logger
from app.core.security import get_current_user
from app.core.tenant import TenantContext, get_tenant_context
from app.models.user import User
from app.repositories.factory import RepositoryFactory
from app.schemas.project import ProjectCreateWithQuote, QuoteItemCreate
from app.schemas.quote_agent import (
    ConfirmRequest,
    ConfirmResponse,
    ConversationCreateResponse,
    ConversationDetail,
    ConversationSummary,
    EstimateBreakdown,
    FeedbackDatasetResponse,
    MessageResponse,
    SendMessageRequest,
    SendMessageResponse,
)
from app.services.quote_agent_service import QuoteAgentService

logger = get_logger(__name__)
router = APIRouter()


def require_quote_agent_enabled(
    tenant: TenantContext = Depends(get_tenant_context),
) -> TenantContext:
    """Reject with 403 unless the quote_agent module is enabled for the org."""
    settings_obj = getattr(tenant.organization, "settings", None) or {}
    modules = settings_obj.get("modules", {}) if isinstance(settings_obj, dict) else {}
    if not bool(modules.get("quote_agent")):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Quote agent module is not enabled for this organization",
        )
    return tenant


def _message_to_schema(message) -> MessageResponse:
    return MessageResponse(
        id=message.id,
        role=message.role,
        content=message.content,
        meta=message.meta,
        created_at=message.created_at,
    )


@router.post("/conversations", response_model=ConversationCreateResponse)
async def create_conversation(
    tenant: TenantContext = Depends(require_quote_agent_enabled),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = RepositoryFactory.create_agent_conversation_repository(db, tenant.organization_id)
    conversation = await repo.create_conversation(user_id=current_user.id)
    return ConversationCreateResponse(id=conversation.id, status=conversation.status)


@router.get("/conversations", response_model=list[ConversationSummary])
async def list_conversations(
    tenant: TenantContext = Depends(require_quote_agent_enabled),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = RepositoryFactory.create_agent_conversation_repository(db, tenant.organization_id)
    conversations = await repo.list_by_organization()
    return [
        ConversationSummary(
            id=c.id,
            status=c.status,
            project_id=c.project_id,
            quote_id=c.quote_id,
            created_at=c.created_at,
        )
        for c in conversations
    ]


@router.get("/conversations/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(
    conversation_id: int,
    tenant: TenantContext = Depends(require_quote_agent_enabled),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = RepositoryFactory.create_agent_conversation_repository(db, tenant.organization_id)
    conversation = await repo.get_by_id(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    messages = await repo.list_messages(conversation_id)
    return ConversationDetail(
        id=conversation.id,
        status=conversation.status,
        project_id=conversation.project_id,
        quote_id=conversation.quote_id,
        created_at=conversation.created_at,
        messages=[_message_to_schema(m) for m in messages],
    )


@router.post("/conversations/{conversation_id}/messages", response_model=SendMessageResponse)
async def send_message(
    conversation_id: int,
    payload: SendMessageRequest,
    tenant: TenantContext = Depends(require_quote_agent_enabled),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _enforce_ai_rate_limit_by_plan(tenant)

    repo = RepositoryFactory.create_agent_conversation_repository(db, tenant.organization_id)
    conversation = await repo.get_by_id(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    service = QuoteAgentService(db, tenant.organization_id)
    if not service.is_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service not configured. Please set OPENAI_API_KEY.",
        )

    # Build history BEFORE persisting the new user turn to avoid duplication.
    prior_messages = await repo.list_messages(conversation_id)
    history = [
        {"role": m.role, "content": m.content}
        for m in prior_messages
        if m.role in ("user", "assistant") and m.content
    ]

    await repo.add_message(conversation_id, role="user", content=payload.content)

    result = await service.process_message(history, payload.content)

    estimate_dict = result.get("estimate")
    proposal_items = result.get("proposal_items")
    assistant_meta = None
    if estimate_dict is not None:
        assistant_meta = {
            "estimate": {k: v for k, v in estimate_dict.items() if k != "proposal_items"},
            "items": proposal_items,
        }

    assistant_message = await repo.add_message(
        conversation_id,
        role="assistant",
        content=result.get("content", ""),
        meta=assistant_meta,
    )

    usage = result.get("usage")
    if usage:
        try:
            usage_repo = RepositoryFactory.create_ai_usage_repository(db)
            await usage_repo.create_event(
                organization_id=tenant.organization_id,
                feature="quote_agent_message",
                provider="openai",
                model=service.model,
                prompt_tokens=usage.get("prompt_tokens", 0),
                completion_tokens=usage.get("completion_tokens", 0),
                total_tokens=usage.get("total_tokens", 0),
                estimated_cost=usage.get("estimated_cost"),
                actor_user_id=current_user.id,
            )
        except Exception as exc:  # pragma: no cover - usage tracking is best-effort
            logger.warning(f"Failed to record quote agent AI usage: {exc}")

    estimate_response = None
    if estimate_dict is not None:
        estimate_response = EstimateBreakdown(
            **{k: v for k, v in estimate_dict.items() if k != "proposal_items"}
        )

    return SendMessageResponse(
        assistant_message=_message_to_schema(assistant_message),
        estimate=estimate_response,
    )


@router.post("/conversations/{conversation_id}/confirm", response_model=ConfirmResponse)
async def confirm_conversation(
    conversation_id: int,
    payload: ConfirmRequest,
    tenant: TenantContext = Depends(require_quote_agent_enabled),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.services.project_service import ProjectService

    repo = RepositoryFactory.create_agent_conversation_repository(db, tenant.organization_id)
    conversation = await repo.get_by_id(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    if conversation.quote_id is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This conversation already has a created quote",
        )

    # Find the latest proposal produced by the agent.
    messages = await repo.list_messages(conversation_id)
    proposal_items = None
    proposal_meta = None
    for message in reversed(messages):
        if message.role == "assistant" and isinstance(message.meta, dict):
            items = message.meta.get("items")
            if items:
                proposal_items = items
                proposal_meta = message.meta
                break

    if not proposal_items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No estimate to confirm yet. Ask the agent for a proposal first.",
        )

    quote_items = [
        QuoteItemCreate(
            service_id=item["service_id"],
            estimated_hours=item.get("estimated_hours"),
            quantity=item.get("quantity") if item.get("quantity") is not None else 1.0,
            pricing_type=item.get("pricing_type"),
            fixed_price=item.get("fixed_price"),
            recurring_price=item.get("recurring_price"),
            billing_frequency=item.get("billing_frequency"),
            project_value=item.get("project_value"),
        )
        for item in proposal_items
    ]

    project_name = payload.project_name or f"Cotización {payload.client_name}"
    project_data = ProjectCreateWithQuote(
        name=project_name,
        client_name=payload.client_name,
        client_email=payload.client_email,
        tax_ids=payload.tax_ids or [],
        quote_items=quote_items,
        target_margin_percentage=payload.target_margin_percentage,
        allow_low_margin=payload.allow_low_margin,
    )

    project_service = ProjectService(db, tenant.organization_id)
    try:
        quote_response = await project_service.create_project_with_quote(
            project_data=project_data,
            current_user=current_user,
            subscription_plan=tenant.subscription_plan,
            allow_low_margin=payload.allow_low_margin,
        )
    except HTTPException:
        await db.rollback()
        raise

    # Mark provenance so agent-created deals are identifiable in the pipeline.
    project_repo = RepositoryFactory.create_project_repository(db, tenant.organization_id)
    project = await project_repo.get_by_id(quote_response.project_id)
    if project is not None:
        project.source = "quote_agent"
        await project_repo.update(project)

    await repo.set_result(
        conversation,
        project_id=quote_response.project_id,
        quote_id=quote_response.id,
        proposed_snapshot=proposal_meta,
    )

    return ConfirmResponse(project_id=quote_response.project_id, quote_id=quote_response.id)


@router.get("/feedback", response_model=FeedbackDatasetResponse)
async def get_feedback_dataset(
    tenant: TenantContext = Depends(require_quote_agent_enabled),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = QuoteAgentService(db, tenant.organization_id)
    dataset = await service.get_feedback_dataset()
    return FeedbackDatasetResponse(items=dataset)
