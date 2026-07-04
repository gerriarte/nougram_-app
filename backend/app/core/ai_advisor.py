"""
AI Advisor utilities using OpenAI or Google Gemini
"""

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.project import Project, Quote, QuoteItem


def anonymize_project_data(project: Project) -> dict:
    """
    Anonymize project data before sending to AI

    Args:
        project: Project instance

    Returns:
        Dict with anonymized project data
    """
    return {
        "project_id": f"PROJ-{project.id}",
        "status": project.status,
        "client_name": "[CLIENT]" if project.client_name else None,
        "client_email": "[EMAIL]" if project.client_email else None,
        "currency": project.currency,
        "created_at": project.created_at.isoformat() if project.created_at else None,
        "quotes": [
            {
                "version": quote.version,
                "total_client_price": quote.total_client_price,
                "total_internal_cost": quote.total_internal_cost,
                "margin_percentage": quote.margin_percentage,
                "created_at": quote.created_at.isoformat() if quote.created_at else None,
                "items": [
                    {
                        "service_name": item.service.name if item.service else "Unknown",
                        "estimated_hours": item.estimated_hours,
                        "internal_cost": item.internal_cost,
                        "client_price": item.client_price,
                    }
                    for item in quote.items
                ],
            }
            for quote in project.quotes
        ],
    }


async def get_anonimized_project_context(
    db: AsyncSession, organization_id: int, limit: int = 5
) -> list[dict]:
    """
    Get anonymized project context for AI analysis

    Args:
        db: Database session
        organization_id: Tenant scope — only this organization's projects are read
        limit: Maximum number of projects to include

    Returns:
        List of anonymized project data
    """
    result = await db.execute(
        select(Project)
        .where(
            Project.organization_id == organization_id,
            Project.deleted_at.is_(None),
        )
        .options(
            selectinload(Project.quotes).selectinload(Quote.items).selectinload(QuoteItem.service)
        )
        .order_by(Project.created_at.desc())
        .limit(limit)
    )

    projects = result.scalars().all()

    return [anonymize_project_data(project) for project in projects]


async def query_openai(question: str, context: list[dict]) -> str | None:
    """
    Query OpenAI API with context

    Args:
        question: User question
        context: Anonymized project context

    Returns:
        AI response or None if error
    """
    if not settings.OPENAI_API_KEY:
        return None

    try:
        url = "https://api.openai.com/v1/chat/completions"

        system_prompt = """You are a CFO (Chief Financial Officer) advisor for a digital agency.
Your role is to analyze the agency's financial data and provide strategic insights.
Focus on profitability, margins, pricing strategies, and financial optimization.
Be concise, data-driven, and provide actionable recommendations."""

        context_str = str(context)[:2000]  # Truncate if too long

        user_prompt = f"""Context: Recent projects data (anonymized):
{context_str}

Question: {question}

Please provide a CFO-level analysis and recommendation."""

        headers = {
            "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
            "Content-Type": "application/json",
        }

        data = {
            "model": "gpt-4",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "max_tokens": 500,
            "temperature": 0.7,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=data, headers=headers)

            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                return f"Error: OpenAI API returned {response.status_code}"

    except Exception as e:
        return f"Error querying OpenAI: {str(e)}"


async def query_gemini(question: str, context: list[dict]) -> str | None:
    """
    Query Google Gemini API with context

    Args:
        question: User question
        context: Anonymized project context

    Returns:
        AI response or None if error
    """
    if not settings.GOOGLE_AI_API_KEY:
        return None

    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={settings.GOOGLE_AI_API_KEY}"

        system_instruction = """You are a CFO (Chief Financial Officer) advisor for a digital agency.
Your role is to analyze the agency's financial data and provide strategic insights.
Focus on profitability, margins, pricing strategies, and financial optimization.
Be concise, data-driven, and provide actionable recommendations."""

        context_str = str(context)[:2000]  # Truncate if too long

        prompt = f"""Context: Recent projects data (anonymized):
{context_str}

Question: {question}

Please provide a CFO-level analysis and recommendation."""

        data = {
            "contents": [{"parts": [{"text": f"{system_instruction}\n\n{prompt}"}]}],
            "generationConfig": {"temperature": 0.7, "maxOutputTokens": 500},
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=data)

            if response.status_code == 200:
                result = response.json()
                if "candidates" in result and len(result["candidates"]) > 0:
                    return result["candidates"][0]["content"]["parts"][0]["text"]
                else:
                    return "Error: No response from Gemini"
            else:
                return f"Error: Gemini API returned {response.status_code}"

    except Exception as e:
        return f"Error querying Gemini: {str(e)}"


async def query_ai_advisor(
    question: str, db: AsyncSession, organization_id: int, ai_provider: str = "openai"
) -> dict:
    """
    Query AI advisor with project context

    Args:
        question: User question
        db: Database session
        organization_id: Tenant scope for the project context
        ai_provider: AI provider to use ("openai" or "gemini")

    Returns:
        Dict with AI response
    """
    # Get anonymized context (scoped to the requesting tenant)
    context = await get_anonimized_project_context(db, organization_id, limit=5)

    # Query AI based on provider
    if ai_provider == "gemini" or (ai_provider == "openai" and not settings.OPENAI_API_KEY):
        if settings.GOOGLE_AI_API_KEY:
            answer = await query_gemini(question, context)
            provider_used = "gemini"
        else:
            return {
                "success": False,
                "answer": "No AI provider configured. Please set OPENAI_API_KEY or GOOGLE_AI_API_KEY.",
                "provider": None,
            }
    else:
        answer = await query_openai(question, context)
        provider_used = "openai"

    if answer:
        return {"success": True, "answer": answer, "provider": provider_used}
    else:
        return {
            "success": False,
            "answer": "Failed to get response from AI provider",
            "provider": None,
        }
