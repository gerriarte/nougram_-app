"""
Endpoints for industry templates
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.organization import Organization
from app.models.template import IndustryTemplate
from app.models.user import User
from app.schemas.template import (
    ApplyTemplateRequest,
    ApplyTemplateResponse,
    IndustryTemplateListResponse,
    IndustryTemplateResponse,
)
from app.services.template_service import apply_industry_template

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/templates", tags=["templates"])


@router.get("/industries", response_model=IndustryTemplateListResponse)
async def list_industry_templates(active_only: bool = True, db: AsyncSession = Depends(get_db)):
    """
    List all available industry templates

    Returns list of templates with their suggested roles, services, and costs.
    Can filter to show only active templates.

    **Query Parameters:**
    - `active_only` (bool): If true, only return active templates (default: true)

    **Returns:**
    - List of industry templates with full details

    **Example:**
    ```json
    {
      "items": [
        {
          "id": 1,
          "industry_type": "branding",
          "name": "Agencia de Branding",
          "description": "Plantilla para agencias de branding...",
          "suggested_roles": [...],
          "suggested_services": [...],
          "suggested_fixed_costs": [...]
        }
      ],
      "total": 5
    }
    ```
    """
    query = select(IndustryTemplate)

    if active_only:
        query = query.where(IndustryTemplate.is_active)

    result = await db.execute(query.order_by(IndustryTemplate.name))
    templates = result.scalars().all()

    items = [IndustryTemplateResponse.model_validate(template) for template in templates]

    return IndustryTemplateListResponse(items=items, total=len(items))


@router.get("/industries/{industry_type}", response_model=IndustryTemplateResponse)
async def get_industry_template(industry_type: str, db: AsyncSession = Depends(get_db)):
    """
    Get detailed information about a specific industry template

    Returns full details of a template including all suggested roles, services, and costs.

    **Path Parameters:**
    - `industry_type` (str): Type identifier of the template (e.g., "branding", "web_development")

    **Returns:**
    - Full template details

    **Raises:**
    - 404: If template not found

    **Example:**
    ```json
    {
      "id": 1,
      "industry_type": "branding",
      "name": "Agencia de Branding",
      "description": "Plantilla para agencias de branding...",
      "suggested_roles": [
        {
          "name": "Diseñador Gráfico Junior",
          "monthly_cost": 2000,
          "weekly_hours": 40,
          "seniority": "junior"
        }
      ],
      "suggested_services": [...],
      "suggested_fixed_costs": [...]
    }
    ```
    """
    result = await db.execute(
        select(IndustryTemplate).where(
            IndustryTemplate.industry_type == industry_type, IndustryTemplate.is_active
        )
    )
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Industry template '{industry_type}' not found or inactive",
        )

    return IndustryTemplateResponse.model_validate(template)


@router.post(
    "/organizations/{organization_id}/apply-template",
    response_model=ApplyTemplateResponse,
    summary="Apply template to organization",
)
async def apply_template_to_organization(
    organization_id: int,
    template_data: ApplyTemplateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Apply an industry template to an organization

    Creates TeamMembers, Services, and CostFixed based on template suggestions,
    adjusting salaries by region multiplier.

    **Permissions:**
    - Organization admin of the target organization
    - Super admin

    **Path Parameters:**
    - `organization_id` (int): ID of the organization to apply template to

    **Request Body:**
    - `industry_type` (str): Type of industry template to apply
    - `region` (str): Region code for salary adjustment (default: "US")
    - `currency` (str): Currency code (default: "USD")
    - `customize` (dict, optional): Customization data to override template defaults

    **Returns:**
    - Result of template application with counts of created resources

    **Raises:**
    - 403: If user doesn't have permission
    - 404: If organization or template not found
    - 400: If template application fails

    **Example Request:**
    ```json
    {
      "industry_type": "branding",
      "region": "COL",
      "currency": "COP",
      "customize": {
        "roles": [
          {
            "name": "Diseñador Gráfico Junior",
            "monthly_cost": 2500
          }
        ]
      }
    }
    ```

    **Example Response:**
    ```json
    {
      "success": true,
      "message": "Template applied successfully",
      "template_applied": "branding",
      "region": "COL",
      "multiplier": 0.25,
      "currency": "COP",
      "team_members_created": 5,
      "services_created": 3,
      "costs_created": 2,
      "created_items": [...]
    }
    ```
    """
    # Check permissions
    is_super_admin = getattr(current_user, "role", None) == "super_admin"
    is_org_admin = current_user.organization_id == organization_id and getattr(
        current_user, "role", None
    ) in ["org_admin", "admin_financiero", "owner"]

    if not (is_super_admin or is_org_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to apply templates to this organization",
        )

    # Verify organization exists
    result = await db.execute(select(Organization).where(Organization.id == organization_id))
    organization = result.scalar_one_or_none()

    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Organization {organization_id} not found",
        )

    try:
        # Apply template
        result_data = await apply_industry_template(
            organization_id=organization_id,
            industry_type=template_data.industry_type,
            region=template_data.region,
            currency=template_data.currency,
            db=db,
            customize=template_data.customize,
        )

        logger.info(
            f"Template {template_data.industry_type} applied to organization {organization_id} "
            f"by user {current_user.id}"
        )

        return ApplyTemplateResponse(
            success=True, message="Template applied successfully", **result_data
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error applying template: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error applying template: {str(e)}",
        )
