"""
AI-powered financial analysis endpoints
"""

import time
from asyncio import Lock
from collections import defaultdict, deque
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.error_codes import ErrorCode
from app.core.logging import get_logger
from app.core.rate_limiting import get_rate_limit_for_plan, get_tenant_identifier, limiter
from app.core.security import get_current_user
from app.core.tenant import TenantContext, get_tenant_context
from app.core.translations import translate_error
from app.models.organization import Organization
from app.models.user import User
from app.schemas.ai import (
    DocumentParseRequest,
    DocumentParseResponse,
    ExecutiveSummaryRequest,
    ExecutiveSummaryResponse,
    NaturalLanguageCommandRequest,
    NaturalLanguageCommandResponse,
    OnboardingSuggestionRequest,
    OnboardingSuggestionResponse,
)
from app.services.ai_service import ai_service

logger = get_logger(__name__)
router = APIRouter()

# Coarse safety guard at gateway level; plan-specific limits are enforced below.
AI_RATE_LIMIT = "200/minute"
AI_WINDOW_SECONDS = 60
_ai_requests_by_tenant: dict[int, deque[float]] = defaultdict(deque)
_ai_rate_lock = Lock()


async def _enforce_ai_rate_limit_by_plan(tenant: TenantContext) -> None:
    """Apply per-plan AI rate limits per tenant within a 60-second window."""
    plan = (tenant.subscription_plan or "free").strip().lower()
    limit = get_rate_limit_for_plan(plan, "ai")
    now = time.time()
    cutoff = now - AI_WINDOW_SECONDS
    tenant_id = tenant.organization_id

    async with _ai_rate_lock:
        bucket = _ai_requests_by_tenant[tenant_id]
        while bucket and bucket[0] <= cutoff:
            bucket.popleft()

        if len(bucket) >= limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=(
                    f"AI rate limit exceeded for plan '{plan}'. Limit: {limit} requests/minute."
                ),
            )

        bucket.append(now)


class AIAnalysisRequest(BaseModel):
    """Request for AI analysis"""

    question: str | None = None


class AIAnalysisResponse(BaseModel):
    """Response from AI analysis"""

    success: bool
    analysis: str | None = None
    error: str | None = None
    usage: dict | None = None
    context_summary: dict | None = None


@router.post("/analyze", response_model=AIAnalysisResponse)
async def analyze_financial_data(
    request: AIAnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    tenant: TenantContext = Depends(get_tenant_context),
):
    """
    Analyze financial data with AI

    This is the main endpoint for AI-powered financial analysis.
    """

    await _enforce_ai_rate_limit_by_plan(tenant)

    # Check if AI service is available
    if not ai_service.is_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service not configured. Please set OPENAI_API_KEY in environment variables.",
        )

    try:
        # Build context with financial data
        context = await _build_financial_context_safe(
            db, tenant.organization_id, tenant.organization
        )

        # Get AI analysis
        result = await ai_service.analyze_financial_data(context=context, question=request.question)

        if not result.get("success"):
            return AIAnalysisResponse(success=False, error=result.get("error", "Unknown error"))

        return AIAnalysisResponse(
            success=True,
            analysis=result.get("analysis"),
            usage=result.get("usage"),
            context_summary={
                "projects_analyzed": len(context.get("projects", [])),
                "services_count": len(context.get("services", [])),
                "total_costs": context.get("total_monthly_costs"),
                "team_size": context.get("team_size"),
            },
        )

    except Exception as e:
        import traceback

        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error during analysis: {str(e)}",
        )


@router.get("/status")
async def get_ai_status():
    """Check if AI service is available"""
    provider = (settings.AI_PROVIDER or "openai").strip().lower()
    model = (settings.AI_MODEL or "gpt-4o-mini").strip()
    return {
        "available": ai_service.is_available(),
        "provider": provider,
        "model": model,
        "message": "AI service is ready"
        if ai_service.is_available()
        else "OPENAI_API_KEY not configured",
    }


@router.post(
    "/suggest-config",
    response_model=OnboardingSuggestionResponse,
    summary="Get AI-powered onboarding suggestions",
)
@limiter.limit(
    AI_RATE_LIMIT, key_func=get_tenant_identifier
)  # Rate limit: 10 requests per minute per tenant
async def suggest_onboarding_config(
    request: Request,
    payload: OnboardingSuggestionRequest,
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get AI-powered suggestions for onboarding configuration based on industry, region, and currency.

    This endpoint uses OpenAI's Structured Outputs to generate:
    - Suggested team roles with realistic salaries for the region
    - Suggested services typical for the industry
    - Suggested fixed costs (software, tools, etc.)

    **Permissions:**
    - All authenticated users can request suggestions for their organization

    **Request Body:**
    - `industry`: Industry type (e.g., 'Marketing Digital', 'Desarrollo Web')
    - `region`: Region code (e.g., 'US', 'CO', 'MX') - defaults to 'US'
    - `currency`: Primary currency - defaults to 'USD'
    - `custom_context`: Optional additional context about the business

    **Returns:**
    - `200 OK`: Suggestions generated successfully
    - `503 Service Unavailable`: AI service not configured
    - `500 Internal Server Error`: Error processing request

    **Response includes:**
    - `suggested_roles`: List of suggested team members with salaries
    - `suggested_services`: List of suggested services with pricing models
    - `suggested_fixed_costs`: List of suggested fixed costs
    - `confidence_scores`: Confidence scores for each category
    - `reasoning`: AI reasoning for the suggestions
    """
    await _enforce_ai_rate_limit_by_plan(tenant)

    if not ai_service.is_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=translate_error(ErrorCode.AI_SERVICE_UNAVAILABLE),
        )

    try:
        # Call AI service
        result = await ai_service.suggest_onboarding_data(
            industry=request.industry,
            region=request.region,
            currency=request.currency,
            custom_context=request.custom_context,
        )

        if not result.get("success"):
            error_msg = result.get("error", "Unknown error")
            logger.error(f"AI service error: {error_msg}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=translate_error(ErrorCode.AI_PROCESSING_ERROR, detail=error_msg),
            )

        # Extract data from result
        data = result.get("data", {})

        # Validate and convert to Pydantic schema
        try:
            suggestion_response = OnboardingSuggestionResponse(
                suggested_roles=data.get("suggested_roles", []),
                suggested_services=data.get("suggested_services", []),
                suggested_fixed_costs=data.get("suggested_fixed_costs", []),
                confidence_scores=data.get("confidence_scores", {}),
                reasoning=data.get("reasoning"),
            )

            logger.info(
                f"AI suggestions generated for industry={payload.industry}, region={payload.region}",
                extra={
                    "organization_id": tenant.organization_id,
                    "user_id": current_user.id,
                    "roles_count": len(suggestion_response.suggested_roles),
                    "services_count": len(suggestion_response.suggested_services),
                    "costs_count": len(suggestion_response.suggested_fixed_costs),
                    "usage": result.get("usage", {}),
                },
            )

            return suggestion_response

        except Exception as validation_error:
            logger.error(f"Error validating AI response: {validation_error}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=translate_error(
                    ErrorCode.AI_PROCESSING_ERROR, detail="Invalid response format from AI service"
                ),
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in suggest_onboarding_config: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=translate_error(ErrorCode.UNKNOWN_ERROR),
        )


@router.post(
    "/parse-document",
    response_model=DocumentParseResponse,
    summary="Parse unstructured document data",
)
@limiter.limit(
    AI_RATE_LIMIT, key_func=get_tenant_identifier
)  # Rate limit: 10 requests per minute per tenant
async def parse_document(
    request: Request,
    payload: DocumentParseRequest,
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Parse unstructured document data (payroll, expenses, etc.) into structured format.

    This endpoint uses OpenAI to extract structured data from unstructured text documents
    (PDFs, CSVs, etc.) and classify them into:
    - Team members (with salaries)
    - Fixed costs
    - Subscriptions

    **Permissions:**
    - All authenticated users can parse documents for their organization

    **Request Body:**
    - `text`: Text content from document (PDF, CSV, etc.) - can be copied/pasted
    - `document_type`: Optional type hint ('payroll', 'expenses', 'mixed') - helps AI classify better

    **Returns:**
    - `200 OK`: Document parsed successfully
    - `503 Service Unavailable`: AI service not configured
    - `500 Internal Server Error`: Error processing request

    **Response includes:**
    - `team_members`: List of extracted team members with salaries
    - `fixed_costs`: List of extracted fixed costs
    - `subscriptions`: List of extracted subscriptions
    - `confidence_scores`: Confidence scores for each category (0-1)
    - `warnings`: List of warnings about ambiguous or incomplete data

    **Important:**
    - All extracted data requires human review before saving
    - Confidence scores help identify which data is most reliable
    - Warnings indicate potential issues with the extraction
    """
    await _enforce_ai_rate_limit_by_plan(tenant)

    if not ai_service.is_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=translate_error(ErrorCode.AI_SERVICE_UNAVAILABLE),
        )

    # Validate text is not empty
    if not payload.text or not payload.text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Text content is required and cannot be empty",
        )

    # Limit text length to prevent excessive API costs
    MAX_TEXT_LENGTH = 10000  # characters
    if len(payload.text) > MAX_TEXT_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Text content is too long. Maximum {MAX_TEXT_LENGTH} characters allowed.",
        )

    try:
        # Call AI service
        result = await ai_service.parse_unstructured_data(
            text=payload.text, document_type=payload.document_type
        )

        if not result.get("success"):
            error_msg = result.get("error", "Unknown error")
            logger.error(f"AI service error: {error_msg}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=translate_error(ErrorCode.AI_PROCESSING_ERROR, detail=error_msg),
            )

        # Extract data from result
        data = result.get("data", {})

        # Convert AI response to Pydantic schemas
        # AI returns floats, but schemas expect Decimal for monetary values
        from decimal import Decimal

        # Convert team members
        team_members_data = []
        for member in data.get("team_members", []):
            member_dict = dict(member)
            # Convert salary to Decimal
            if "salary_monthly_brute" in member_dict:
                member_dict["salary_monthly_brute"] = Decimal(
                    str(member_dict["salary_monthly_brute"])
                )
            # Ensure required fields have defaults
            if "currency" not in member_dict:
                member_dict["currency"] = "USD"
            if "billable_hours_per_week" not in member_dict:
                member_dict["billable_hours_per_week"] = 32
            if "is_active" not in member_dict:
                member_dict["is_active"] = True
            team_members_data.append(member_dict)

        # Convert fixed costs
        fixed_costs_data = []
        for cost in data.get("fixed_costs", []):
            cost_dict = dict(cost)
            # Convert amount to Decimal
            if "amount_monthly" in cost_dict:
                cost_dict["amount_monthly"] = Decimal(str(cost_dict["amount_monthly"]))
            # Ensure required fields have defaults
            if "currency" not in cost_dict:
                cost_dict["currency"] = "USD"
            fixed_costs_data.append(cost_dict)

        # Validate and convert to Pydantic schema
        try:
            parse_response = DocumentParseResponse(
                team_members=team_members_data,
                fixed_costs=fixed_costs_data,
                subscriptions=data.get("subscriptions", []),
                confidence_scores=data.get("confidence_scores", {}),
                warnings=data.get("warnings", []),
            )

            logger.info(
                "Document parsed successfully",
                extra={
                    "organization_id": tenant.organization_id,
                    "user_id": current_user.id,
                    "document_type": payload.document_type,
                    "team_members_count": len(parse_response.team_members),
                    "fixed_costs_count": len(parse_response.fixed_costs),
                    "subscriptions_count": len(parse_response.subscriptions),
                    "text_length": len(payload.text),
                    "usage": result.get("usage", {}),
                },
            )

            return parse_response

        except Exception as validation_error:
            logger.error(f"Error validating AI response: {validation_error}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=translate_error(
                    ErrorCode.AI_PROCESSING_ERROR, detail="Invalid response format from AI service"
                ),
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in parse_document: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=translate_error(ErrorCode.UNKNOWN_ERROR),
        )


@router.post(
    "/process-command",
    response_model=NaturalLanguageCommandResponse,
    summary="Process natural language configuration commands",
)
@limiter.limit(
    AI_RATE_LIMIT, key_func=get_tenant_identifier
)  # Rate limit: 10 requests per minute per tenant
async def process_command(
    request: Request,
    payload: NaturalLanguageCommandRequest,
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Process natural language configuration commands and convert them to structured actions.

    This endpoint uses OpenAI to interpret commands in natural language (Spanish or English)
    and convert them into structured actions like:
    - Adding team members
    - Adding services
    - Adding fixed costs
    - Updating team members
    - Deleting team members

    **Permissions:**
    - All authenticated users can process commands for their organization
    - Actual execution of actions requires appropriate permissions (e.g., `can_modify_costs`)

    **Request Body:**
    - `command`: Natural language command (e.g., "Añade un Senior Designer que gana 45k anuales")
    - `context`: Optional current configuration context (helps AI understand current state)

    **Returns:**
    - `200 OK`: Command processed successfully
    - `503 Service Unavailable`: AI service not configured
    - `500 Internal Server Error`: Error processing request

    **Response includes:**
    - `action_type`: Type of action to execute
    - `action_data`: Structured data for the action
    - `confidence`: Confidence score (0-1) for the parsed command
    - `requires_confirmation`: Whether user confirmation is required before executing
    - `reasoning`: AI explanation of how the command was interpreted

    **Important:**
    - All actions require user confirmation before execution
    - Low confidence scores indicate ambiguous commands
    - The endpoint only parses the command; actual execution must be done separately
    """
    await _enforce_ai_rate_limit_by_plan(tenant)

    if not ai_service.is_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=translate_error(ErrorCode.AI_SERVICE_UNAVAILABLE),
        )

    # Validate command is not empty
    if not payload.command or not payload.command.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Command is required and cannot be empty",
        )

    try:
        # Build context from current organization state (optional, helps AI)
        context = None
        if payload.context:
            context = payload.context
        else:
            # Optionally build context from current organization data
            # This helps AI understand what already exists
            try:
                from app.models.service import Service
                from app.models.team import TeamMember

                # Get current team members (names and roles only, no sensitive data)
                # Anonymize names before sending to OpenAI
                from app.services.data_anonymizer import anonymize_name

                team_result = await db.execute(
                    select(TeamMember.name, TeamMember.role)
                    .where(
                        TeamMember.organization_id == tenant.organization_id,
                        TeamMember.is_active,
                    )
                    .limit(10)
                )
                team_members = [
                    {"name": anonymize_name(r.name), "role": r.role} for r in team_result.all()
                ]

                # Get current services (names only)
                services_result = await db.execute(
                    select(Service.name)
                    .where(
                        Service.organization_id == tenant.organization_id,
                        Service.is_active,
                        Service.deleted_at.is_(None),
                    )
                    .limit(10)
                )
                services = [{"name": r.name} for r in services_result.all()]

                context = {
                    "existing_team_members": team_members,
                    "existing_services": services,
                }
            except Exception as e:
                logger.warning(f"Could not build context for command: {e}")
                context = None

        # Call AI service
        result = await ai_service.process_natural_language_command(
            command=payload.command, context=context
        )

        if not result.get("success"):
            error_msg = result.get("error", "Unknown error")
            logger.error(f"AI service error: {error_msg}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=translate_error(ErrorCode.AI_PROCESSING_ERROR, detail=error_msg),
            )

        # Extract data from result
        data = result.get("data", {})

        # Validate and convert to Pydantic schema
        try:
            command_response = NaturalLanguageCommandResponse(
                action_type=data.get("action_type", "unknown"),
                action_data=data.get("action_data", {}),
                confidence=data.get("confidence", 0.0),
                requires_confirmation=data.get("requires_confirmation", True),
                reasoning=data.get("reasoning"),
            )

            logger.info(
                "Command processed successfully",
                extra={
                    "organization_id": tenant.organization_id,
                    "user_id": current_user.id,
                    "command": payload.command[:100],  # Log first 100 chars
                    "action_type": command_response.action_type,
                    "confidence": command_response.confidence,
                    "usage": result.get("usage", {}),
                },
            )

            return command_response

        except Exception as validation_error:
            logger.error(f"Error validating AI response: {validation_error}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=translate_error(
                    ErrorCode.AI_PROCESSING_ERROR, detail="Invalid response format from AI service"
                ),
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in process_command: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=translate_error(ErrorCode.UNKNOWN_ERROR),
        )


@router.post(
    "/generate-executive-summary",
    response_model=ExecutiveSummaryResponse,
    summary="Generate executive summary for quote",
)
@limiter.limit(
    AI_RATE_LIMIT, key_func=get_tenant_identifier
)  # Rate limit: 10 requests per minute per tenant
async def generate_executive_summary(
    request: Request,
    payload: ExecutiveSummaryRequest,
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(get_current_user),
):
    """
    Generate an executive summary for a quote using AI

    This endpoint uses OpenAI to generate a professional executive summary
    for a quote, suitable for presenting to executives and decision-makers.

    **Permissions:**
    - All authenticated users can generate summaries for their organization

    **Rate Limiting:**
    - Limited to 10 requests per minute per tenant (to control API costs)

    **Request Body:**
    - `project_name`: Name of the project
    - `client_name`: Name of the client
    - `client_sector`: Optional client sector (e.g., 'Technology', 'Retail')
    - `services`: List of services included in the quote (min 1)
      - `service_id`: Service ID
      - `service_name`: Service name
      - `estimated_hours`: Optional estimated hours
      - `client_price`: Price for this service
    - `total_price`: Total quote price
    - `currency`: Currency code (default: "USD")
    - `language`: Language for summary: "es" or "en" (default: "es")

    **Returns:**
    - `200 OK`: Executive summary generated successfully
    - `400 Bad Request`: Invalid request data
    - `503 Service Unavailable`: AI service not configured
    - `500 Internal Server Error`: Error generating summary

    **Response includes:**
    - `summary`: Generated executive summary (150-250 words)
    - `provider`: AI provider used ("openai")
    - `usage`: API usage information (tokens, estimated cost)

    **Example Request:**
    ```json
    {
      "project_name": "Rediseño de E-commerce",
      "client_name": "TechStore Inc",
      "client_sector": "Retail",
      "services": [
        {
          "service_id": 1,
          "service_name": "Diseño UI/UX",
          "estimated_hours": 80,
          "client_price": "12000"
        },
        {
          "service_id": 2,
          "service_name": "Desarrollo Frontend",
          "estimated_hours": 120,
          "client_price": "18000"
        }
      ],
      "total_price": "30000",
      "currency": "USD",
      "language": "es"
    }
    ```
    """
    await _enforce_ai_rate_limit_by_plan(tenant)

    if not ai_service.is_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=translate_error(ErrorCode.AI_SERVICE_UNAVAILABLE),
        )

    try:
        # Validar request
        if not payload.services or len(payload.services) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="At least one service is required"
            )

        # Llamar al servicio de IA
        result = await ai_service.generate_executive_summary(payload)

        if not result.get("success"):
            error_msg = result.get("error", "Unknown error")
            logger.error(f"AI service error: {error_msg}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=translate_error(ErrorCode.AI_PROCESSING_ERROR, detail=error_msg),
            )

        # Construir respuesta
        response = ExecutiveSummaryResponse(
            summary=result.get("summary", ""),
            provider=result.get("provider", "openai"),
            usage=result.get("usage"),
        )

        logger.info(
            f"Executive summary generated for project={payload.project_name}",
            extra={
                "organization_id": tenant.organization_id,
                "user_id": current_user.id,
                "project_name": payload.project_name,
                "services_count": len(payload.services),
                "language": payload.language,
                "usage": result.get("usage", {}),
            },
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in generate_executive_summary: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=translate_error(ErrorCode.UNKNOWN_ERROR),
        )


async def _build_financial_context_safe(
    db: AsyncSession, organization_id: int, organization: Organization | None = None
) -> dict:
    """
    Build financial context safely, with fallbacks for missing data
    Filter by organization_id for multi-tenancy.
    """
    from app.models.cost import CostFixed
    from app.models.project import Project, Quote
    from app.models.service import Service
    from app.models.settings import AgencySettings
    from app.models.team import TeamMember

    context = {}

    try:
        # 1. Get costs (safe)
        costs_result = await db.execute(
            select(CostFixed).where(
                CostFixed.deleted_at.is_(None), CostFixed.organization_id == organization_id
            )
        )
        costs = costs_result.scalars().all()

        if costs:
            total_costs = sum(getattr(cost, "amount_monthly", 0) for cost in costs)
            context["total_monthly_costs"] = total_costs
            context["costs_count"] = len(costs)
        else:
            context["total_monthly_costs"] = 0
            context["costs_count"] = 0
    except Exception as e:
        print(f"Error loading costs: {e}")
        context["total_monthly_costs"] = 0
        context["costs_count"] = 0

    try:
        # 2. Get team (safe)
        team_result = await db.execute(
            select(TeamMember).where(
                TeamMember.is_active, TeamMember.organization_id == organization_id
            )
        )
        team_members = team_result.scalars().all()

        if team_members:
            # Calculate hours (billable_hours_per_week * 4.33)
            total_hours = sum(
                getattr(member, "billable_hours_per_week", 0) * 4.33 for member in team_members
            )
            context["team_size"] = len(team_members)
            context["total_monthly_hours"] = round(total_hours, 2)

            # Blended rate
            if total_hours > 0 and context["total_monthly_costs"] > 0:
                context["blended_cost_rate"] = round(
                    context["total_monthly_costs"] / total_hours, 2
                )
            else:
                context["blended_cost_rate"] = 0
        else:
            context["team_size"] = 0
            context["total_monthly_hours"] = 0
            context["blended_cost_rate"] = 0
    except Exception as e:
        print(f"Error loading team: {e}")
        context["team_size"] = 0
        context["total_monthly_hours"] = 0
        context["blended_cost_rate"] = 0

    try:
        # 3. Get services (safe)
        services_result = await db.execute(
            select(Service).where(
                Service.is_active,
                Service.deleted_at.is_(None),
                Service.organization_id == organization_id,
            )
        )
        services = services_result.scalars().all()

        context["services"] = [
            {
                "name": getattr(service, "name", "Unknown"),
                "default_margin_target": getattr(service, "default_margin_target", 0),
                "is_active": getattr(service, "is_active", True),
            }
            for service in services
        ]
    except Exception as e:
        print(f"Error loading services: {e}")
        context["services"] = []

    try:
        # 4. Get projects (safe)
        cutoff_date = datetime.utcnow() - timedelta(days=90)
        projects_result = await db.execute(
            select(Project)
            .where(
                Project.created_at >= cutoff_date,
                Project.deleted_at.is_(None),
                Project.organization_id == organization_id,
            )
            .order_by(Project.created_at.desc())
            .limit(10)
        )
        projects = projects_result.scalars().all()

        context["projects"] = []
        for project in projects:
            try:
                # Try to get latest quote
                quote_result = await db.execute(
                    select(Quote)
                    .where(Quote.project_id == project.id)
                    .order_by(Quote.version.desc())
                    .limit(1)
                )
                latest_quote = quote_result.scalar_one_or_none()

                if latest_quote:
                    total_price = getattr(latest_quote, "total_client_price", 0) or 0
                    total_cost = getattr(latest_quote, "total_internal_cost", 0) or 0
                    margin = getattr(latest_quote, "margin_percentage", 0) or 0

                    context["projects"].append(
                        {
                            "name": getattr(project, "name", "Unknown"),
                            "client": getattr(project, "client_name", "Unknown"),
                            "status": getattr(project, "status", "unknown"),
                            "total_price": float(total_price),
                            "total_cost": float(total_cost),
                            "margin_percentage": float(margin),
                            "created_at": project.created_at.isoformat()
                            if project.created_at
                            else None,
                        }
                    )
            except Exception as e:
                print(f"Error processing project {project.id}: {e}")
                continue
    except Exception as e:
        print(f"Error loading projects: {e}")
        context["projects"] = []

        # 5. Get settings
        primary_currency = "USD"
        if organization and organization.settings:
            primary_currency = organization.settings.get("primary_currency", "USD")
        else:
            # Fallback to general settings
            settings_result = await db.execute(select(AgencySettings))
            settings_obj = settings_result.scalar_one_or_none()
            primary_currency = (
                getattr(settings_obj, "primary_currency", "USD") if settings_obj else "USD"
            )

        context["primary_currency"] = primary_currency

    return context
