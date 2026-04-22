"""
Helpers to anonymize sensitive multi-tenant data for support roles.

Support users (support_manager, data_analyst) should inspect many organizations
without seeing exact figures. These helpers convert values into coarse buckets
so only super_admin retains full visibility.
"""

from __future__ import annotations

from typing import Any

from app.models.project import Project, Quote
from app.models.team import TeamMember

Currency = str


def anonymize_blended_rate(rate: float, currency: Currency = "USD") -> str:
    """Return a range describing the blended hourly rate."""
    if rate < 50:
        return f"{currency}0-50"
    if rate < 100:
        return f"{currency}50-100"
    if rate < 150:
        return f"{currency}100-150"
    if rate < 200:
        return f"{currency}150-200"
    return f"{currency}200+"


def anonymize_amount(amount: float, currency: Currency = "USD") -> str:
    """Convert an absolute amount into thousands-based buckets."""
    value = abs(amount)
    if value < 1_000:
        bucket = "0-1K"
    elif value < 5_000:
        bucket = "1K-5K"
    elif value < 10_000:
        bucket = "5K-10K"
    elif value < 25_000:
        bucket = "10K-25K"
    elif value < 50_000:
        bucket = "25K-50K"
    elif value < 100_000:
        bucket = "50K-100K"
    else:
        bucket = "100K+"
    return f"{currency}{bucket}"


def anonymize_percentage(value: float) -> str:
    """Return coarse buckets for percentage values."""
    pct = value * 100 if value <= 1 else value
    if pct < 10:
        return "0-10%"
    if pct < 20:
        return "10-20%"
    if pct < 30:
        return "20-30%"
    if pct < 40:
        return "30-40%"
    if pct < 50:
        return "40-50%"
    return "50%+"


def anonymize_quote_totals(quote: Quote, currency: Currency = "USD") -> dict[str, Any]:
    """Return anonymized summary for a quote."""
    return {
        "id": quote.id,
        "project_id": quote.project_id,
        "version": quote.version,
        "total_internal_cost": anonymize_amount(float(quote.total_internal_cost), currency),
        "total_client_price": anonymize_amount(float(quote.total_client_price), currency),
        "margin_percentage": anonymize_percentage(quote.margin_percentage),
        "created_at": quote.created_at.isoformat() if getattr(quote, "created_at", None) else None,
        "notes": getattr(quote, "notes", None),
    }


def anonymize_client_name(name: str | None) -> str:
    """Mask client names keeping only the first character."""
    if not name:
        return "***"
    trimmed = name.strip()
    if len(trimmed) <= 3:
        return trimmed[0] + "**"
    return trimmed[0] + "*" * min(len(trimmed) - 1, 5)


def anonymize_project_cost_data(project: Project, currency: Currency = "USD") -> dict[str, Any]:
    """Return project metadata plus anonymized latest quote."""
    latest_quote = None
    quotes = getattr(project, "quotes", None)
    if quotes:
        try:
            latest_quote = max(quotes, key=lambda q: q.version or 0)
        except (TypeError, ValueError):
            latest_quote = None

    payload: dict[str, Any] = {
        "id": project.id,
        "name": project.name,
        "client_name": anonymize_client_name(getattr(project, "client_name", None)),
        "status": project.status,
        "currency": getattr(project, "currency", currency),
        "created_at": project.created_at.isoformat()
        if getattr(project, "created_at", None)
        else None,
    }

    if latest_quote:
        payload["latest_quote"] = anonymize_quote_totals(
            latest_quote, getattr(project, "currency", currency)
        )

    return payload


def anonymize_name(name: str | None) -> str:
    """Mask personal names keeping the initials."""
    if not name:
        return "***"
    parts = name.split()
    if len(parts) == 1:
        return parts[0][0] + "***"
    first = parts[0][0] + "***"
    last = parts[-1][0] + "***"
    return f"{first} {last}"


def anonymize_team_salaries(
    team_members: list[TeamMember], currency: Currency = "USD"
) -> list[dict[str, Any]]:
    """Return anonymized team member cards."""
    payload: list[dict[str, Any]] = []
    for member in team_members:
        payload.append(
            {
                "id": member.id,
                "name": anonymize_name(member.name),
                "role": member.role,
                "salary_monthly_brute": anonymize_amount(
                    float(member.salary_monthly_brute),
                    member.currency or currency,
                )
                if getattr(member, "salary_monthly_brute", None)
                else None,
                "currency": member.currency or currency,
                "billable_hours_per_week": member.billable_hours_per_week,
                "is_active": member.is_active,
                "created_at": member.created_at.isoformat()
                if getattr(member, "created_at", None)
                else None,
            }
        )
    return payload


def anonymize_organization_data(
    organization: Any, include_sensitive: bool = False
) -> dict[str, Any]:
    """Return anonymized organization summary."""
    data = {
        "id": organization.id,
        "name": organization.name,
        "slug": organization.slug,
        "subscription_plan": organization.subscription_plan,
        "subscription_status": organization.subscription_status,
        "created_at": organization.created_at.isoformat()
        if getattr(organization, "created_at", None)
        else None,
    }
    if include_sensitive:
        data["settings"] = getattr(organization, "settings", None)
    return data


def anonymize_usage_metrics(
    user_count: int,
    project_count: int,
    quote_count: int,
    credits_available: int | None = None,
    credits_used_this_month: int | None = None,
) -> dict[str, Any]:
    """Convert usage numbers into rough buckets."""

    def bucket(value: int) -> str:
        if value <= 0:
            return "0"
        if value < 5:
            return "1-5"
        if value < 10:
            return "5-10"
        if value < 25:
            return "10-25"
        if value < 50:
            return "25-50"
        return "50+"

    metrics = {
        "user_count": bucket(user_count),
        "project_count": bucket(project_count),
        "quote_count": bucket(quote_count),
    }
    if credits_available is not None:
        metrics["credits_available"] = bucket(credits_available)
    if credits_used_this_month is not None:
        metrics["credits_used_this_month"] = bucket(credits_used_this_month)
    return metrics
