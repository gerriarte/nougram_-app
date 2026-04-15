"""
Service for applying industry templates to organizations
"""
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.template import IndustryTemplate
from app.models.organization import Organization
from app.models.team import TeamMember
from app.models.service import Service
from app.models.cost import CostFixed

logger = logging.getLogger(__name__)

# Region multipliers for salary adjustment (based on USD)
REGION_MULTIPLIERS: Dict[str, float] = {
    "US": 1.0,      # Baseline
    "UK": 0.85,
    "COL": 0.25,    # Colombia
    "ARG": 0.15,    # Argentina
    "MEX": 0.30,    # México
    "ESP": 0.70,    # España
    "BR": 0.20,     # Brasil
    "DEFAULT": 0.5,  # Default for unlisted regions
}


def get_region_multiplier(region: str) -> float:
    """
    Get salary multiplier for a given region
    
    Args:
        region: Region code (US, UK, COL, etc.)
    
    Returns:
        Multiplier value (default 0.5 if region not found)
    """
    return REGION_MULTIPLIERS.get(region.upper(), REGION_MULTIPLIERS["DEFAULT"])


async def apply_industry_template(
    organization_id: int,
    industry_type: str,
    region: str = "US",
    currency: str = "USD",
    db: AsyncSession = None,
    customize: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Apply an industry template to an organization
    
    Creates TeamMembers, Services, and CostFixed based on template suggestions,
    adjusting salaries by region multiplier.
    
    Args:
        organization_id: Organization ID to apply template to
        industry_type: Type of industry template (e.g., "branding", "web_development")
        region: Region code for salary adjustment (default: "US")
        currency: Currency code (default: "USD")
        db: Database session
        customize: Optional customization data to override template defaults
    
    Returns:
        Dictionary with created resources counts and details
    
    Raises:
        ValueError: If template not found or organization not found
    """
    if db is None:
        raise ValueError("Database session is required")
    
    # Get template
    result = await db.execute(
        select(IndustryTemplate).where(
            IndustryTemplate.industry_type == industry_type,
            IndustryTemplate.is_active == True
        )
    )
    template = result.scalar_one_or_none()
    
    if not template:
        raise ValueError(f"Industry template '{industry_type}' not found or inactive")
    
    # Verify organization exists
    result = await db.execute(
        select(Organization).where(Organization.id == organization_id)
    )
    organization = result.scalar_one_or_none()
    
    if not organization:
        raise ValueError(f"Organization {organization_id} not found")
    
    # Get region multiplier
    multiplier = get_region_multiplier(region)
    
    # Initialize result counters
    result_data = {
        "template_applied": industry_type,
        "region": region,
        "multiplier": multiplier,
        "currency": currency,
        "team_members_created": 0,
        "services_created": 0,
        "costs_created": 0,
        "created_items": []
    }
    
    # Apply suggested roles (create TeamMembers)
    if template.suggested_roles and isinstance(template.suggested_roles, list):
        for role_data in template.suggested_roles:
            # Use customization if provided
            if customize and "roles" in customize:
                custom_role = next(
                    (r for r in customize["roles"] if r.get("name") == role_data.get("name")),
                    None
                )
                if custom_role:
                    role_data = {**role_data, **custom_role}
            
            # Adjust salary by region multiplier
            base_monthly_cost = role_data.get("monthly_cost", 0)
            adjusted_monthly_cost = base_monthly_cost * multiplier
            
            # Get role name (use "name" as role since templates store role name in "name" field)
            role_name = role_data.get("name", "Unknown Role")
            
            # Get weekly hours (convert to billable_hours_per_week)
            weekly_hours = role_data.get("weekly_hours", 40)
            billable_hours_per_week = int(role_data.get("billable_hours_per_week", min(int(weekly_hours), 32)))
            
            # Get non_billable_hours_percentage (Sprint 14: for legal/compliance roles)
            non_billable_hours_percentage = float(role_data.get("non_billable_hours_percentage", 0.0))
            
            team_member = TeamMember(
                name=role_data.get("name", "Unknown Role"),
                role=role_name,
                salary_monthly_brute=round(adjusted_monthly_cost, 2),
                currency=currency,
                billable_hours_per_week=billable_hours_per_week,
                non_billable_hours_percentage=non_billable_hours_percentage,
                apply_social_charges=True,
                is_active=True,
                organization_id=organization_id
            )
            db.add(team_member)
            result_data["team_members_created"] += 1
            result_data["created_items"].append({
                "type": "team_member",
                "name": team_member.name,
                "role": team_member.role,
                "salary_monthly_brute": team_member.salary_monthly_brute
            })
    
    # Apply suggested services
    if template.suggested_services and isinstance(template.suggested_services, list):
        for service_data in template.suggested_services:
            # Use customization if provided
            if customize and "services" in customize:
                custom_service = next(
                    (s for s in customize["services"] if s.get("name") == service_data.get("name")),
                    None
                )
                if custom_service:
                    service_data = {**service_data, **custom_service}
            
            # Get default margin target if provided, otherwise use default 40%
            default_margin_target = service_data.get("default_margin_target", 0.40)
            
            # Get pricing type and related fields (Sprint 14)
            pricing_type = service_data.get("pricing_type", "hourly")
            fixed_price = service_data.get("fixed_price")
            is_recurring = service_data.get("is_recurring", False)
            billing_frequency = service_data.get("billing_frequency")
            recurring_price = service_data.get("recurring_price")
            
            service = Service(
                name=service_data.get("name", "Unknown Service"),
                description=service_data.get("description"),
                default_margin_target=default_margin_target,
                pricing_type=pricing_type,
                fixed_price=fixed_price,
                is_recurring=is_recurring,
                billing_frequency=billing_frequency,
                recurring_price=recurring_price,
                is_active=True,
                organization_id=organization_id
            )
            db.add(service)
            result_data["services_created"] += 1
            result_data["created_items"].append({
                "type": "service",
                "name": service.name,
                "description": service.description
            })
    
    # Apply suggested fixed costs
    if template.suggested_fixed_costs and isinstance(template.suggested_fixed_costs, list):
        for cost_data in template.suggested_fixed_costs:
            # Use customization if provided
            if customize and "costs" in customize:
                custom_cost = next(
                    (c for c in customize["costs"] if c.get("name") == cost_data.get("name")),
                    None
                )
                if custom_cost:
                    cost_data = {**cost_data, **custom_cost}
            
            # Adjust amount by region multiplier (if applicable)
            base_amount = cost_data.get("amount", 0)
            # For software subscriptions, we might not adjust by region
            # Only adjust if explicitly marked as regional
            if cost_data.get("adjust_by_region", False):
                adjusted_amount = base_amount * multiplier
            else:
                adjusted_amount = base_amount
            
            cost_fixed = CostFixed(
                name=cost_data.get("name", "Unknown Cost"),
                amount_monthly=round(adjusted_amount, 2),
                currency=currency,
                category=cost_data.get("category", "Software"),
                description=cost_data.get("description"),
                organization_id=organization_id
            )
            db.add(cost_fixed)
            result_data["costs_created"] += 1
            result_data["created_items"].append({
                "type": "cost",
                "name": cost_fixed.name,
                "amount": cost_fixed.amount_monthly,
                "currency": cost_fixed.currency
            })
    
    # Update organization settings with onboarding context
    settings = organization.settings or {}
    
    # Set social charges configuration for Colombia
    if region.upper() == "COL":
        if "social_charges_config" not in settings or customize:
            settings["social_charges_config"] = {
                "enable_social_charges": True,
                "health_percentage": 8.5,
                "pension_percentage": 12.0,
                "arl_percentage": 0.522,
                "parafiscales_percentage": 4.0,
                "prima_services_percentage": 8.33,
                "cesantias_percentage": 8.33,
                "int_cesantias_percentage": 1.0,
                "vacations_percentage": 4.17,
                "total_percentage": 52.852
            }
            # Add customization if provided (Sprint 18 - allow overriding defaults)
            if customize and "taxes" in customize:
                tax_data = customize["taxes"]
                for key in ["health", "pension", "arl", "parafiscales", "prima_services", "cesantias", "int_cesantias", "vacations"]:
                    if key in tax_data:
                        field_name = f"{key}_percentage" if not key.endswith("_percentage") else key
                        settings["social_charges_config"][field_name] = tax_data[key]

    settings.update({
        "onboarding_completed": True,
        "industry_type": industry_type,
        "primary_currency": currency,
        "template_applied_at": datetime.now(timezone.utc).isoformat(),
        "template_applied_region": region,
        "template_applied_currency": currency,
        "template_applied_multiplier": multiplier
    })
    
    # Add customization data if provided
    if customize:
        if "client_types" in customize:
            settings["client_types"] = customize["client_types"]
        if "services_offered" in customize:
            settings["services_offered"] = customize["services_offered"]
        if "team_size_range" in customize:
            settings["team_size_range"] = customize["team_size_range"]
    
    organization.settings = settings
    
    # Commit all changes
    await db.commit()
    
    logger.info(
        f"Applied template {industry_type} to organization {organization_id}. "
        f"Created: {result_data['team_members_created']} team members, "
        f"{result_data['services_created']} services, {result_data['costs_created']} costs"
    )
    
    return result_data

