"""
Project Service - Business logic for project and quote management
"""
from typing import Dict, List, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, insert
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
import logging

from app.core.calculations import calculate_blended_cost_rate, calculate_quote_totals_enhanced
from app.core.plan_limits import validate_project_limit
from app.core.permissions import get_user_role
from app.core.exceptions import BusinessLogicError
from app.repositories.factory import RepositoryFactory
from app.models.project import Project, Quote, QuoteItem, QuoteItemAllocation, QuoteExpense, project_taxes
from app.models.service import Service
from app.models.tax import Tax
from app.models.user import User
from app.schemas.project import (
    ProjectCreateWithQuote,
    QuoteCreateNewVersion,
    QuoteResponseWithItems,
    QuoteItemResponse,
    QuoteItemAllocationResponse,
)
from app.schemas.quote import QuoteEmailRequest, QuoteEmailResponse
from app.services.credit_service import CreditService

logger = logging.getLogger(__name__)


class ProjectService:
    """Service for managing projects and quotes"""
    
    def __init__(self, db: AsyncSession, organization_id: int):
        """
        Initialize ProjectService
        
        Args:
            db: Database session
            organization_id: Organization ID for tenant scoping
        """
        self.db = db
        self.organization_id = organization_id
        self.project_repo = RepositoryFactory.create_project_repository(db, organization_id)
        self.service_repo = RepositoryFactory.create_service_repository(db, organization_id)
    
    async def create_project_with_quote(
        self,
        project_data: ProjectCreateWithQuote,
        current_user: User,
        subscription_plan: str,
        allow_low_margin: bool = False
    ) -> QuoteResponseWithItems:
        """
        Create a new project with initial quote
        
        Args:
            project_data: Project and quote data
            current_user: Current user creating the project
            subscription_plan: Subscription plan for limit validation
            
        Returns:
            QuoteResponseWithItems with created quote and items
        """
        # Validate project limit for plan
        await validate_project_limit(self.organization_id, subscription_plan, self.db)
        
        logger.info(f"Creating project with data: name={project_data.name}, client={project_data.client_name}")
        
        # Validate all services exist, are active, and not deleted
        service_ids = [item.service_id for item in project_data.quote_items]
        logger.info(f"Service IDs to validate: {service_ids}")
        
        if not service_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one quote item is required"
            )
        
        all_services = await self.service_repo.get_all(
            where=Service.id.in_(service_ids),
            include_deleted=False
        )
        # Filter to only active services
        services = {service.id: service for service in all_services if service.is_active}
        logger.info(f"Found {len(services)} valid services out of {len(service_ids)} requested")
        
        if len(services) != len(service_ids):
            missing = set(service_ids) - set(services.keys())
            logger.warning(f"Missing services: {list(missing)}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Services with ids {list(missing)} not found, inactive, or deleted"
            )
        
        # Calculate blended cost rate
        from app.models.organization import Organization
        org_result = await self.db.execute(select(Organization).where(Organization.id == self.organization_id))
        org = org_result.scalar_one_or_none()
        primary_currency = org.settings.get('primary_currency', 'USD') if org and org.settings else 'USD'
        social_config = org.settings.get('social_charges_config') if org and org.settings else None
        
        logger.info("Calculating blended cost rate...")
        blended_rate = await calculate_blended_cost_rate(
            self.db, 
            primary_currency=primary_currency,
            tenant_id=self.organization_id,
            social_charges_config=social_config
        )
        logger.info(f"Blended cost rate: {blended_rate}")
        
        # Calculate quote totals using enhanced function
        items_dict = []
        for item in project_data.quote_items:
            item_dict = {
                "service_id": item.service_id,
                "estimated_hours": getattr(item, 'estimated_hours', None),
                "pricing_type": getattr(item, 'pricing_type', None),
                "fixed_price": getattr(item, 'fixed_price', None),
                "quantity": getattr(item, 'quantity', 1.0),
                "recurring_price": getattr(item, 'recurring_price', None),
                "billing_frequency": getattr(item, 'billing_frequency', None),
                "project_value": getattr(item, 'project_value', None),
            }
            items_dict.append(item_dict)
        
        tax_ids = project_data.tax_ids or []
        revisions_included = project_data.revisions_included if hasattr(project_data, 'revisions_included') and project_data.revisions_included is not None else 2
        revision_cost_per_additional = getattr(project_data, 'revision_cost_per_additional', None)
        target_margin_percentage = getattr(project_data, 'target_margin_percentage', None)
        # Convert Decimal to float for target_margin_percentage (function expects float)
        from decimal import Decimal
        target_margin_float = float(target_margin_percentage) if target_margin_percentage is not None and isinstance(target_margin_percentage, Decimal) else target_margin_percentage
        logger.info(f"Calculating quote totals (enhanced) with {len(tax_ids)} taxes, revisions_included={revisions_included}, target_margin={target_margin_float}...")
        totals = await calculate_quote_totals_enhanced(
            self.db, 
            items_dict, 
            blended_rate, 
            tax_ids,
            expenses=None,  # Expenses are added separately via expenses endpoints
            target_margin_percentage=target_margin_float,  # Pass target margin as float
            revisions_included=revisions_included,
            revision_cost_per_additional=revision_cost_per_additional,
            revisions_count=None  # Only used when calculating additional revision costs
        )
        logger.info(f"Quote totals calculated: {totals}")
        
        # Validate profitability before creating quote
        allow_low_margin_flag = getattr(project_data, 'allow_low_margin', False) or allow_low_margin
        await self._validate_quote_profitability(totals, current_user, allow_low_margin=allow_low_margin_flag)
        
        # Create project
        logger.info("Creating project...")
        project = Project(
            name=project_data.name,
            client_name=project_data.client_name,
            client_email=project_data.client_email,
            currency=project_data.currency,
            status="Draft",
            organization_id=self.organization_id
        )
        self.db.add(project)
        await self.db.flush()  # Get project ID
        logger.info(f"Project created with ID: {project.id}")
        
        # Associate taxes if provided
        if tax_ids:
            await self._associate_taxes(project.id, tax_ids)
        
        # Create quote
        logger.info("Creating quote...")
        quote = Quote(
            project_id=project.id,
            version=1,
            total_internal_cost=totals["total_internal_cost"],
            total_client_price=totals["total_client_price"],
            margin_percentage=totals["margin_percentage"],
            target_margin_percentage=target_margin_percentage,  # Save target margin
            revisions_included=revisions_included,
            revision_cost_per_additional=revision_cost_per_additional
        )
        self.db.add(quote)
        await self.db.flush()  # Get quote ID
        logger.info(f"Quote created with ID: {quote.id}")
        
        # Create quote items
        logger.info(f"Creating {len(project_data.quote_items)} quote items...")
        quote_items, quote_allocations = self._create_quote_items(
            quote.id,
            project_data.quote_items,
            services,
            totals.get("items", [])
        )
        self.db.add_all(quote_items)
        if quote_allocations:
            self.db.add_all(quote_allocations)
        
        # Consume credits based on user role (if applicable)
        user_role = get_user_role(current_user)
        if user_role == "product_manager":
            try:
                await CreditService.validate_and_consume_credits(
                    organization_id=self.organization_id,
                    amount=1,
                    user_id=current_user.id,
                    reason=f"Created project '{project.name}' with quote",
                    db=self.db,
                    reference_id=quote.id
                )
                logger.info(f"Consumed 1 credit for project creation by product_manager user {current_user.id}")
            except HTTPException as e:
                # Re-raise HTTPException (e.g., insufficient credits)
                raise e
            except Exception as e:
                logger.error(f"Error consuming credits: {str(e)}")
                # Don't fail project creation if credit consumption fails
                # This allows graceful degradation
        
        await self.db.commit()
        await self.db.refresh(quote)
        
        # Build response
        response = await self._build_quote_response(quote)
        
        # Log audit event
        from app.core.audit import AuditService, AuditAction
        await AuditService.log_action(
            db=self.db,
            action=AuditAction.PROJECT_CREATE,
            user_id=current_user.id,
            organization_id=self.organization_id,
            resource_type="project",
            resource_id=response.project_id,
            request=None,
            details={"project_name": project_data.name, "client_name": project_data.client_name},
            status="success"
        )
        
        return response
    
    async def create_new_quote_version(
        self,
        project_id: int,
        quote_id: int,
        quote_data: QuoteCreateNewVersion,
        current_user: User,
        allow_low_margin: bool = False
    ) -> QuoteResponseWithItems:
        """
        Create a new version of an existing quote
        
        Args:
            project_id: Project ID
            quote_id: Existing quote ID
            quote_data: Data for new quote version
            current_user: Current user creating the version
            
        Returns:
            QuoteResponseWithItems with new quote version
        """
        # Verify project exists and belongs to tenant
        project = await self.project_repo.get_by_id_with_quotes(project_id, include_deleted=False)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with id {project_id} not found"
            )
        
        # Get existing quote
        existing_quote = await self.project_repo.get_quote_by_id(quote_id)
        if not existing_quote or existing_quote.project_id != project_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Quote with id {quote_id} not found"
            )
        
        # Get max version for this project
        max_version_result = await self.db.execute(
            select(func.max(Quote.version)).where(Quote.project_id == project_id)
        )
        max_version = max_version_result.scalar() or 0
        new_version = max_version + 1
        
        # Validate services
        service_ids = [item.service_id for item in quote_data.items]
        all_services = await self.service_repo.get_all(
            where=Service.id.in_(service_ids),
            include_deleted=False
        )
        services = {service.id: service for service in all_services if service.is_active}
        
        if len(services) != len(service_ids):
            missing = set(service_ids) - set(services.keys())
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Services with ids {list(missing)} not found or inactive"
            )
        
        # Calculate blended cost rate
        from app.models.organization import Organization
        org_result = await self.db.execute(select(Organization).where(Organization.id == self.organization_id))
        org = org_result.scalar_one_or_none()
        social_config = org.settings.get('social_charges_config') if org and org.settings else None
        
        blended_rate = await calculate_blended_cost_rate(
            self.db, 
            project.currency, 
            tenant_id=self.organization_id,
            social_charges_config=social_config
        )
        
        # Get project taxes
        tax_ids = [tax.id for tax in project.taxes] if project.taxes else []
        
        # Calculate totals
        items_dict = []
        for item in quote_data.items:
            item_dict = {
                "service_id": item.service_id,
                "estimated_hours": getattr(item, 'estimated_hours', None),
                "pricing_type": getattr(item, 'pricing_type', None),
                "fixed_price": getattr(item, 'fixed_price', None),
                "quantity": getattr(item, 'quantity', 1.0),
                "recurring_price": getattr(item, 'recurring_price', None),
                "billing_frequency": getattr(item, 'billing_frequency', None),
                "project_value": getattr(item, 'project_value', None),
            }
            items_dict.append(item_dict)
        
        revisions_included = quote_data.revisions_included if quote_data.revisions_included is not None else (existing_quote.revisions_included if existing_quote.revisions_included else 2)
        revision_cost_per_additional = quote_data.revision_cost_per_additional if hasattr(quote_data, 'revision_cost_per_additional') and quote_data.revision_cost_per_additional is not None else existing_quote.revision_cost_per_additional
        target_margin_percentage = getattr(quote_data, 'target_margin_percentage', None)
        
        totals = await calculate_quote_totals_enhanced(
            self.db, 
            items_dict, 
            blended_rate, 
            tax_ids,
            expenses=None,
            target_margin_percentage=target_margin_percentage,  # Pass target margin
            revisions_included=revisions_included,
            revision_cost_per_additional=revision_cost_per_additional,
            revisions_count=None
        )
        
        # Validate profitability before creating new quote version
        allow_low_margin_flag = getattr(quote_data, 'allow_low_margin', False) or allow_low_margin
        await self._validate_quote_profitability(totals, current_user, allow_low_margin=allow_low_margin_flag)
        
        # Create new quote version
        new_quote = Quote(
            project_id=project_id,
            version=new_version,
            total_internal_cost=totals["total_internal_cost"],
            total_client_price=totals["total_client_price"],
            margin_percentage=totals["margin_percentage"],
            target_margin_percentage=target_margin_percentage,  # Save target margin
            notes=quote_data.notes,
            revisions_included=revisions_included,
            revision_cost_per_additional=revision_cost_per_additional
        )
        self.db.add(new_quote)
        await self.db.flush()
        
        # Create quote items
        quote_items, quote_allocations = self._create_quote_items(
            new_quote.id,
            quote_data.items,
            services,
            totals.get("items", [])
        )
        self.db.add_all(quote_items)
        if quote_allocations:
            self.db.add_all(quote_allocations)
        
        await self.db.commit()
        await self.db.refresh(new_quote)
        
        # Build response
        return await self._build_quote_response(new_quote)
    
    async def send_quote_email(
        self,
        project_id: int,
        quote_id: int,
        email_data: QuoteEmailRequest,
        current_user: User
    ) -> QuoteEmailResponse:
        """
        Send quote by email
        
        Args:
            project_id: Project ID
            quote_id: Quote ID
            email_data: Email data
            current_user: Current user sending the email
            
        Returns:
            QuoteEmailResponse with success status
        """
        from app.core.email import send_email, generate_quote_email_html, generate_quote_email_text
        from app.core.logging import get_logger
        
        logger_instance = get_logger(__name__)
        
        # Verify project belongs to tenant
        project_check = await self.db.execute(
            select(Project).where(
                Project.id == project_id,
                Project.organization_id == self.organization_id
            )
        )
        if not project_check.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with id {project_id} not found"
            )
        
        # Get quote with all relationships
        result = await self.db.execute(
            select(Quote)
            .where(Quote.id == quote_id, Quote.project_id == project_id)
            .options(
                selectinload(Quote.items).selectinload(QuoteItem.service),
                selectinload(Quote.expenses),
                selectinload(Quote.project).selectinload(Project.taxes)
            )
        )
        quote = result.scalar_one_or_none()
        
        if not quote:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Quote with id {quote_id} for project {project_id} not found"
            )
        
        project = quote.project
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with id {project_id} not found"
            )
        
        # Calculate totals
        total_client_price = quote.total_client_price or 0
        taxes = []
        total_taxes = 0
        if hasattr(project, 'taxes') and project.taxes:
            for tax in project.taxes:
                tax_amount = (total_client_price * tax.percentage / 100) if tax.percentage else 0
                taxes.append(tax_amount)
                total_taxes += tax_amount
        
        total_with_taxes = total_client_price + total_taxes
        
        # Generate email
        subject = email_data.subject or f"Quote for {project.name} - Version {quote.version}"
        html_body = generate_quote_email_html(
            project_name=project.name,
            client_name=project.client_name,
            quote_version=quote.version,
            total_with_taxes=total_with_taxes,
            currency=project.currency,
            notes=quote.notes or email_data.message
        )
        text_body = generate_quote_email_text(
            project_name=project.name,
            client_name=project.client_name,
            quote_version=quote.version,
            total_with_taxes=total_with_taxes,
            currency=project.currency,
            notes=quote.notes or email_data.message
        )
        
        # Prepare attachments
        attachments = []
        
        if email_data.include_pdf:
            from app.core.pdf_generator import generate_quote_pdf
            pdf_buffer = generate_quote_pdf(project, quote)
            safe_project_name = "".join(c for c in project.name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            pdf_filename = f"cotizacion_{safe_project_name}_v{quote.version}.pdf"
            attachments.append({
                'filename': pdf_filename,
                'content': pdf_buffer
            })
        
        if email_data.include_docx:
            from app.core.docx_generator import generate_quote_docx
            docx_buffer = generate_quote_docx(project, quote)
            safe_project_name = "".join(c for c in project.name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            docx_filename = f"cotizacion_{safe_project_name}_v{quote.version}.docx"
            attachments.append({
                'filename': docx_filename,
                'content': docx_buffer
            })
        
        # Send email
        success = await send_email(
            to_email=email_data.to_email,
            subject=subject,
            body_html=html_body,
            body_text=text_body,
            attachments=attachments if attachments else None,
            cc=email_data.cc if email_data.cc else None,
            bcc=email_data.bcc if email_data.bcc else None
        )
        
        if success:
            logger_instance.info(
                f"Quote {quote_id} sent by email to {email_data.to_email}",
                user_id=current_user.id,
                project_id=project_id
            )
            return QuoteEmailResponse(
                success=True,
                message=f"Quote sent successfully to {email_data.to_email}"
            )
        else:
            logger_instance.error(
                f"Failed to send quote {quote_id} by email",
                user_id=current_user.id,
                project_id=project_id,
                to_email=email_data.to_email
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send email. Please check SMTP configuration."
            )
    
    # Helper methods
    
    async def _get_minimum_margin_threshold(self) -> float:
        """
        Get minimum margin threshold from organization settings.
        Defaults to 0.15 (15%) if not configured.
        """
        from app.models.organization import Organization
        result = await self.db.execute(
            select(Organization).where(Organization.id == self.organization_id)
        )
        org = result.scalar_one_or_none()
        
        if org and org.settings:
            # Get minimum margin threshold from settings (0-1 range, e.g., 0.15 = 15%)
            min_margin = org.settings.get('minimum_margin_threshold')
            if min_margin is not None:
                # Ensure it's between 0 and 1
                return max(0.0, min(1.0, float(min_margin)))
        
        # Default to 15% if not configured
        return 0.15
    
    async def _validate_quote_profitability(self, totals: Dict, current_user: User, allow_low_margin: bool = False):
        """
        Validate that the quote meets minimum profitability requirements.
        Raises BusinessLogicError if margin is too low (unless allow_low_margin=True).
        """
        margin_percentage = totals.get("margin_percentage", 0.0)
        total_client_price = totals.get("total_client_price", 0.0)
        total_internal_cost = totals.get("total_internal_cost", 0.0)
        
        # Skip validation if quote has zero or negative price
        if total_client_price <= 0:
            logger.warning(f"Quote has zero or negative client price, skipping profitability validation")
            return
        
        # Get minimum margin threshold from organization settings
        min_margin_threshold = await self._get_minimum_margin_threshold()
        
        # Check if margin is below threshold
        if margin_percentage < min_margin_threshold:
            margin_pct_display = margin_percentage * 100
            min_margin_display = min_margin_threshold * 100
            
            # Calculate how much more revenue is needed to meet threshold
            if margin_percentage < 0:
                # Negative margin - calculate break-even point
                required_price = total_internal_cost / (1 - min_margin_threshold)
                additional_needed = required_price - total_client_price
                error_msg = (
                    f"La propuesta tiene un margen negativo ({margin_pct_display:.1f}%). "
                    f"El margen mínimo configurado es {min_margin_display:.1f}%. "
                    f"Se necesita aumentar el precio en al menos {additional_needed:.2f} para alcanzar el margen mínimo."
                )
            else:
                # Low but positive margin
                required_price = total_internal_cost / (1 - min_margin_threshold)
                additional_needed = required_price - total_client_price
                error_msg = (
                    f"La propuesta tiene un margen muy bajo ({margin_pct_display:.1f}%). "
                    f"El margen mínimo configurado es {min_margin_display:.1f}%. "
                    f"Se necesita aumentar el precio en al menos {additional_needed:.2f} para alcanzar el margen mínimo. "
                    f"Considera ajustar los precios, las horas estimadas o revisar los costos del servicio."
                )
            
            if not allow_low_margin:
                logger.warning(
                    f"Quote profitability validation failed: margin={margin_pct_display:.1f}%, "
                    f"threshold={min_margin_display:.1f}%, user_id={current_user.id}"
                )
                raise BusinessLogicError(error_msg)
            else:
                # Log a warning if allowed but low margin
                logger.warning(
                    f"Quote created with low margin (allowed): margin={margin_pct_display:.1f}%, "
                    f"threshold={min_margin_display:.1f}%, user_id={current_user.id}"
                )
        
        logger.info(
            f"Quote profitability validation passed: margin={margin_percentage*100:.1f}%, "
            f"threshold={min_margin_threshold*100:.1f}%"
        )
    
    async def _associate_taxes(self, project_id: int, tax_ids: List[int]):
        """Associate taxes with a project"""
        logger.info(f"Associating {len(tax_ids)} taxes...")
        result = await self.db.execute(
            select(Tax).where(
                Tax.id.in_(tax_ids),
                Tax.is_active == True,
                Tax.deleted_at.is_(None)
            )
        )
        taxes = result.scalars().all()
        if len(taxes) != len(tax_ids):
            missing = set(tax_ids) - {tax.id for tax in taxes}
            logger.warning(f"Missing taxes: {list(missing)}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Taxes with ids {list(missing)} not found, inactive, or deleted"
            )
        if taxes:
            await self.db.execute(
                insert(project_taxes).values([
                    {"project_id": project_id, "tax_id": tax.id}
                    for tax in taxes
                ])
            )
        logger.info(f"Associated {len(taxes)} taxes to project")
    
    def _create_quote_items(
        self,
        quote_id: int,
        items_data: List,
        services: Dict[int, Service],
        items_breakdown: List[Dict]
    ) -> tuple[List[QuoteItem], List[QuoteItemAllocation]]:
        """Create quote items from items data and breakdown"""
        quote_items = []
        quote_allocations = []
        breakdown_map = {item["service_id"]: item for item in items_breakdown}
        
        for item_data in items_data:
            service = services[item_data.service_id]
            breakdown = breakdown_map.get(item_data.service_id, {})
            
            # Get calculated values from enhanced breakdown
            internal_cost = breakdown.get("internal_cost", 0.0)
            client_price = breakdown.get("client_price", 0.0)
            margin_pct = breakdown.get("margin", 0.0) / 100.0 if breakdown.get("margin") else 0.0
            
            # Determine effective pricing type
            effective_pricing_type = (
                getattr(item_data, 'pricing_type', None) or 
                service.pricing_type or 
                "hourly"
            )
            
            quote_item = QuoteItem(
                quote_id=quote_id,
                service_id=item_data.service_id,
                estimated_hours=getattr(item_data, 'estimated_hours', None),
                internal_cost=internal_cost,
                client_price=client_price,
                margin_percentage=margin_pct,
                pricing_type=effective_pricing_type,
                fixed_price=getattr(item_data, 'fixed_price', None) or (service.fixed_price if effective_pricing_type == "fixed" else None),
                quantity=getattr(item_data, 'quantity', 1.0),
                recurring_price=getattr(item_data, 'recurring_price', None),
                billing_frequency=getattr(item_data, 'billing_frequency', None),
                project_value=getattr(item_data, 'project_value', None),
            )
            quote_items.append(quote_item)

            allocations = getattr(item_data, 'allocations', []) or []
            for alloc in allocations:
                quote_allocations.append(
                    QuoteItemAllocation(
                        quote_item=quote_item,
                        team_member_id=alloc.team_member_id,
                        hours=alloc.hours,
                        role=getattr(alloc, 'role', None),
                        start_date=getattr(alloc, 'start_date', None),
                        end_date=getattr(alloc, 'end_date', None),
                    )
                )
        
        return quote_items, quote_allocations
    
    async def _build_quote_response(self, quote: Quote) -> QuoteResponseWithItems:
        """Build QuoteResponseWithItems from Quote model"""
        # Reload quote with relationships
        quote_result = await self.db.execute(
            select(Quote)
            .where(Quote.id == quote.id)
            .options(
                selectinload(Quote.items).selectinload(QuoteItem.service),
                selectinload(Quote.items).selectinload(QuoteItem.allocations),
            )
        )
        final_quote = quote_result.scalar_one()
        
        items_response = []
        for item in final_quote.items:
            items_response.append(QuoteItemResponse(
                id=item.id,
                service_id=item.service_id,
                service_name=item.service.name if item.service else None,
                estimated_hours=item.estimated_hours,
                pricing_type=getattr(item, 'pricing_type', None),
                fixed_price=getattr(item, 'fixed_price', None),
                quantity=getattr(item, 'quantity', None),
                recurring_price=getattr(item, 'recurring_price', None),
                billing_frequency=getattr(item, 'billing_frequency', None),
                project_value=getattr(item, 'project_value', None),
                internal_cost=item.internal_cost,
                client_price=item.client_price,
                margin_percentage=item.margin_percentage,
                allocations=[
                    QuoteItemAllocationResponse(
                        id=alloc.id,
                        team_member_id=alloc.team_member_id,
                        hours=alloc.hours,
                        role=alloc.role,
                        start_date=alloc.start_date,
                        end_date=alloc.end_date,
                    )
                    for alloc in (item.allocations or [])
                ],
            ))
        
        return QuoteResponseWithItems(
            id=final_quote.id,
            project_id=final_quote.project_id,
            version=final_quote.version,
            total_internal_cost=final_quote.total_internal_cost,
            total_client_price=final_quote.total_client_price,
            margin_percentage=final_quote.margin_percentage,
            notes=final_quote.notes,
            revisions_included=final_quote.revisions_included if hasattr(final_quote, 'revisions_included') else 2,
            revision_cost_per_additional=final_quote.revision_cost_per_additional if hasattr(final_quote, 'revision_cost_per_additional') else None,
            created_at=final_quote.created_at,
            updated_at=final_quote.updated_at,
            items=items_response
        )
    
    async def list_projects(
        self,
        status_filter: Optional[str] = None,
        include_deleted: bool = False,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[Project], int]:
        """
        List projects with pagination
        
        Args:
            status_filter: Optional status filter
            include_deleted: Whether to include soft-deleted projects
            page: Page number (1-indexed)
            page_size: Items per page
            
        Returns:
            Tuple of (list of projects, total count)
        """
        offset = (page - 1) * page_size
        
        projects = await self.project_repo.get_all_paginated(
            include_deleted=include_deleted,
            status_filter=status_filter,
            limit=page_size,
            offset=offset
        )
        
        # Get total count
        where_clause = None
        if status_filter:
            where_clause = Project.status == status_filter
        
        total = await self.project_repo.count(where=where_clause, include_deleted=include_deleted)
        
        return projects, total
    
    async def get_project_by_id(
        self,
        project_id: int,
        include_deleted: bool = False
    ) -> Optional[Project]:
        """
        Get project by ID
        
        Args:
            project_id: Project ID
            include_deleted: Whether to include soft-deleted projects
            
        Returns:
            Project instance or None
        """
        return await self.project_repo.get_by_id_with_quotes(project_id, include_deleted=include_deleted)
    
    async def update_project(
        self,
        project_id: int,
        project_data: 'ProjectUpdate',
        current_user: User
    ) -> Project:
        """
        Update an existing project
        
        Args:
            project_id: Project ID
            project_data: Update data
            current_user: Current user performing the update
            
        Returns:
            Updated project instance
            
        Raises:
            HTTPException: If project not found
        """
        project = await self.project_repo.get_by_id_with_quotes(project_id, include_deleted=False)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with id {project_id} not found"
            )
        
        update_data = project_data.model_dump(exclude_unset=True)
        
        # Handle tax_ids separately
        tax_ids = update_data.pop("tax_ids", None)
        
        # Update project fields
        for field, value in update_data.items():
            setattr(project, field, value)
        
        # Update taxes if provided
        if tax_ids is not None:
            # Remove existing tax associations
            from app.models.project import project_taxes
            from sqlalchemy import delete as sql_delete
            await self.db.execute(
                sql_delete(project_taxes).where(project_taxes.c.project_id == project_id)
            )
            await self.db.flush()
            
            # Associate new taxes
            if tax_ids:
                await self._associate_taxes(project_id, tax_ids)
        
        await self.db.commit()
        await self.db.refresh(project)
        
        # Reload with relationships
        return await self.project_repo.get_by_id_with_quotes(project_id, include_deleted=False)
    
    async def delete_project(
        self,
        project_id: int,
        current_user: User
    ) -> None:
        """
        Soft delete a project
        
        Args:
            project_id: Project ID
            current_user: Current user performing the deletion
            
        Raises:
            HTTPException: If project not found
        """
        project = await self.project_repo.get_by_id(project_id, include_deleted=False)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with id {project_id} not found"
            )
        
        await self.project_repo.delete(project, soft=True, deleted_by_id=current_user.id)
    
    async def restore_project(
        self,
        project_id: int
    ) -> Project:
        """
        Restore a soft-deleted project
        
        Args:
            project_id: Project ID
            
        Returns:
            Restored project instance
            
        Raises:
            HTTPException: If project not found or not deleted
        """
        project = await self.project_repo.get_by_id_with_quotes(project_id, include_deleted=True)
        if not project or project.deleted_at is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with id {project_id} not found or not deleted"
            )
        
        # Restore by clearing deleted_at
        project.deleted_at = None
        project.deleted_by_id = None
        await self.db.commit()
        await self.db.refresh(project)
        
        return await self.project_repo.get_by_id_with_quotes(project_id, include_deleted=False)
    
    async def search_clients(
        self,
        search_query: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Buscar clientes existentes por nombre o email
        
        Args:
            search_query: Query de búsqueda
            limit: Límite de resultados
        
        Returns:
            Lista de diccionarios con información de clientes
        """
        return await self.project_repo.search_clients(
            search_query=search_query,
            limit=limit
        )

