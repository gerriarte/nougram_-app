"""
Onboarding Controller - HTTP request handling for onboarding
"""

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.controllers.base import BaseController
from app.schemas.onboarding import (
    BenchmarksResponse,
    CompleteOnboardingRequest,
    CompleteOnboardingResponse,
    OnboardingDraftRequest,
    OnboardingDraftResponse,
    OnboardingImportPreviewResponse,
    OnboardingImportSheetsRequest,
    TemporaryBCRRequest,
    TemporaryBCRResponse,
)
from app.services.onboarding_service import OnboardingService
from app.views.onboarding_view import OnboardingView


class OnboardingController(BaseController):
    """
    Controller for handling onboarding HTTP requests

    Responsibilities:
    - HTTP request validation
    - Delegation to OnboardingService
    - Response formatting via OnboardingView
    - Error handling
    """

    def __init__(self, db: AsyncSession, tenant, current_user):
        """
        Initialize OnboardingController

        Args:
            db: Database session
            tenant: Tenant context
            current_user: Current authenticated user
        """
        super().__init__(db, tenant, current_user)
        self.onboarding_service = OnboardingService(db, self.organization_id)
        self.onboarding_view = OnboardingView()

    async def get_benchmarks(
        self, profile_type: str, country: str | None = None, currency: str | None = None
    ) -> BenchmarksResponse:
        """
        Get benchmarks for a profile type

        Args:
            profile_type: Profile type (freelance, company, agency)
            country: Country code (defaults to organization country)
            currency: Currency code (defaults to organization currency)

        Returns:
            BenchmarksResponse

        Raises:
            HTTPException: If validation fails
        """
        try:
            # Validate profile_type
            if profile_type not in ["freelance", "company", "agency"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid profile_type: {profile_type}. Must be 'freelance', 'company', or 'agency'",
                )

            # Use organization defaults if not provided
            if not country:
                country = (
                    self.tenant.organization.settings.get("country", "US")
                    if self.tenant.organization.settings
                    else "US"
                )
            if not currency:
                currency = (
                    self.tenant.organization.settings.get("primary_currency", "USD")
                    if self.tenant.organization.settings
                    else "USD"
                )

            # Get benchmarks from service
            benchmarks_data = await self.onboarding_service.get_benchmarks(
                profile_type=profile_type, country=country, currency=currency
            )

            # Transform to response
            return self.onboarding_view.to_benchmarks_response(benchmarks_data)

        except HTTPException:
            raise
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            self.logger.error(f"Error getting benchmarks: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error retrieving benchmarks",
            )

    async def get_templates(self) -> dict:
        """
        Get onboarding inventory templates from backend source.
        """
        try:
            return await self.onboarding_service.get_inventory_templates()
        except Exception as e:
            self.logger.error(f"Error getting onboarding templates: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error retrieving onboarding templates",
            )

    async def complete_onboarding(
        self, request: CompleteOnboardingRequest
    ) -> CompleteOnboardingResponse:
        """
        Complete onboarding by saving all configuration

        Args:
            request: CompleteOnboardingRequest with all onboarding data

        Returns:
            CompleteOnboardingResponse

        Raises:
            HTTPException: If onboarding fails
        """
        try:
            # Validate request
            if not request.organization_name and not self.tenant.organization.name:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="organization_name is required"
                )

            # Complete onboarding
            result = await self.onboarding_service.complete_onboarding(request)

            # Transform to response
            return self.onboarding_view.to_complete_response(result)

        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            self.logger.error(f"Error completing onboarding: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error completing onboarding",
            )

    async def get_onboarding_draft(self) -> OnboardingDraftResponse:
        """Get persisted onboarding draft."""
        try:
            draft = await self.onboarding_service.get_onboarding_draft()
            metadata = await self.onboarding_service.get_onboarding_draft_metadata()
            return OnboardingDraftResponse(
                success=True,
                organization_id=self.organization_id,
                data=draft,
                metadata=metadata,
            )
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            self.logger.error(f"Error getting onboarding draft: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error retrieving onboarding draft",
            )

    async def save_onboarding_draft(
        self, request: OnboardingDraftRequest
    ) -> OnboardingDraftResponse:
        """Save onboarding draft."""
        try:
            saved = await self.onboarding_service.save_onboarding_draft(
                request.data,
                updated_by_user_id=self.current_user.id,
            )
            metadata = await self.onboarding_service.get_onboarding_draft_metadata()
            return OnboardingDraftResponse(
                success=True,
                organization_id=self.organization_id,
                data=saved,
                metadata=metadata,
            )
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            self.logger.error(f"Error saving onboarding draft: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error saving onboarding draft",
            )

    async def calculate_temporary_bcr(self, request: TemporaryBCRRequest) -> TemporaryBCRResponse:
        """
        Calculate BCR with temporary onboarding data

        Args:
            request: TemporaryBCRRequest with temporary data

        Returns:
            TemporaryBCRResponse

        Raises:
            HTTPException: If calculation fails
        """
        try:
            # Validate request
            if not request.team_members:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="At least one team member is required",
                )

            # Calculate temporary BCR
            result = await self.onboarding_service.calculate_temporary_bcr(request)

            # Transform to response
            return self.onboarding_view.to_temporary_bcr_response(result)

        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            self.logger.error(f"Error calculating temporary BCR: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error calculating temporary BCR",
            )

    async def preview_import_from_excel(
        self, file_content: bytes
    ) -> OnboardingImportPreviewResponse:
        """Generate onboarding preview payload from an Excel file."""
        try:
            result = await self.onboarding_service.preview_import_from_excel(file_content)
            return OnboardingImportPreviewResponse(**result)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )
        except Exception as e:
            self.logger.error(f"Error importing onboarding preview from Excel: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error generating onboarding import preview from Excel",
            )

    async def preview_import_from_google_sheets(
        self,
        request: OnboardingImportSheetsRequest,
    ) -> OnboardingImportPreviewResponse:
        """Generate onboarding preview payload from Google Sheets."""
        try:
            result = await self.onboarding_service.preview_import_from_google_sheets(request)
            return OnboardingImportPreviewResponse(**result)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )
        except Exception as e:
            self.logger.error(
                f"Error importing onboarding preview from Google Sheets: {e}", exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error generating onboarding import preview from Google Sheets",
            )

    async def download_excel_import_template(self) -> bytes:
        """Generate the official onboarding Excel import template."""
        try:
            return self.onboarding_service.generate_excel_import_template()
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )
        except Exception as e:
            self.logger.error(f"Error generating onboarding import template: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error generating onboarding import template",
            )
