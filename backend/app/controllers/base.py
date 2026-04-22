"""
Base Controller - Base class for all controllers
"""

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tenant import TenantContext
from app.models.user import User


class BaseController:
    """
    Base controller class providing common functionality
    """

    def __init__(self, db: AsyncSession, tenant: TenantContext, current_user: User):
        """
        Initialize controller with database session, tenant context, and current user

        Args:
            db: Database session
            tenant: Tenant context (organization_id, subscription_plan, etc.)
            current_user: Current authenticated user
        """
        self.db = db
        self.tenant = tenant
        self.current_user = current_user
        self.organization_id = tenant.organization_id

        # Setup logger
        from app.core.logging import get_logger

        self.logger = get_logger(self.__class__.__name__)

    def _raise_not_found(self, resource_name: str, resource_id: str | None = None):
        """
        Raise HTTP 404 Not Found exception

        Args:
            resource_name: Name of the resource (e.g., "Project", "Service")
            resource_id: Optional ID of the resource
        """
        message = f"{resource_name} not found"
        if resource_id:
            message += f" (id: {resource_id})"
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)

    def _raise_forbidden(self, message: str = "Forbidden"):
        """
        Raise HTTP 403 Forbidden exception

        Args:
            message: Error message
        """
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=message)

    def _raise_bad_request(self, message: str):
        """
        Raise HTTP 400 Bad Request exception

        Args:
            message: Error message
        """
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

    def _log_info(self, message: str, **kwargs):
        """Log info message with context"""
        self.logger.info(message, **kwargs)

    def _log_error(self, message: str, exc_info: bool = False, **kwargs):
        """Log error message with context"""
        self.logger.error(message, exc_info=exc_info, **kwargs)

    def _handle_not_found(self, resource_name: str, resource_id: str | None = None):
        """Handle not found error - logs and raises exception"""
        self._log_error(f"{resource_name} not found", resource_id=resource_id)
        self._raise_not_found(resource_name, resource_id)
