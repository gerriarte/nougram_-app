"""
Audit logging service for tracking critical actions
"""
from typing import Optional, Dict, Any
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession
import json

from app.repositories.audit_log_repository import AuditLogRepository
from app.core.logging import get_logger

logger = get_logger(__name__)


class AuditService:
    """Service for logging audit events"""
    
    @staticmethod
    def _get_client_ip(request: Optional[Request]) -> Optional[str]:
        """Extract client IP address from request"""
        if not request:
            return None
        
        # Check for forwarded IP (when behind proxy/load balancer)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        # Check for real IP header
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to client host
        if request.client:
            return request.client.host
        
        return None
    
    @staticmethod
    def _get_user_agent(request: Optional[Request]) -> Optional[str]:
        """Extract user agent from request"""
        if not request:
            return None
        return request.headers.get("User-Agent")
    
    @staticmethod
    async def log_action(
        db: AsyncSession,
        action: str,
        user_id: Optional[int] = None,
        organization_id: Optional[int] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[int] = None,
        request: Optional[Request] = None,
        details: Optional[Dict[str, Any]] = None,
        status: str = "success",
        error_message: Optional[str] = None
    ):
        """
        Log an audit event
        
        Args:
            db: Database session
            action: Action name (e.g., "user.login", "project.create")
            user_id: User ID who performed the action
            organization_id: Organization ID (if applicable)
            resource_type: Type of resource affected (e.g., "project", "user")
            resource_id: ID of the affected resource
            request: FastAPI request object (for IP and user agent)
            details: Additional details as dictionary
            status: Action status (success, failure, error)
            error_message: Error message if status is failure/error
        """
        try:
            ip_address = AuditService._get_client_ip(request)
            user_agent = AuditService._get_user_agent(request)
            
            details_str = None
            if details:
                try:
                    details_str = json.dumps(details, default=str)
                except (TypeError, ValueError) as e:
                    logger.warning(f"Failed to serialize audit details: {e}")
                    details_str = str(details)
            
            repo = AuditLogRepository(db)
            await repo.create_log(
                action=action,
                user_id=user_id,
                organization_id=organization_id,
                resource_type=resource_type,
                resource_id=resource_id,
                ip_address=ip_address,
                user_agent=user_agent,
                details=details_str,
                status=status,
                error_message=error_message
            )
        except Exception as e:
            # Don't fail the main operation if audit logging fails
            logger.error(f"Failed to create audit log: {e}", exc_info=True)


# Predefined action constants
class AuditAction:
    """Constants for audit actions"""
    # Authentication
    USER_LOGIN = "user.login"
    USER_LOGIN_FAILED = "user.login_failed"
    USER_LOGOUT = "user.logout"
    
    # User management
    USER_CREATE = "user.create"
    USER_UPDATE = "user.update"
    USER_DELETE = "user.delete"
    USER_SWITCH_ORGANIZATION = "user.switch_organization"
    
    # Project management
    PROJECT_CREATE = "project.create"
    PROJECT_UPDATE = "project.update"
    PROJECT_DELETE = "project.delete"
    
    # Service management
    SERVICE_CREATE = "service.create"
    SERVICE_UPDATE = "service.update"
    SERVICE_DELETE = "service.delete"
    
    # Team management
    TEAM_MEMBER_CREATE = "team_member.create"
    TEAM_MEMBER_UPDATE = "team_member.update"
    TEAM_MEMBER_DELETE = "team_member.delete"
    
    # Cost management
    COST_CREATE = "cost.create"
    COST_UPDATE = "cost.update"
    COST_DELETE = "cost.delete"
    
    # Subscription/Billing
    SUBSCRIPTION_CREATE = "subscription.create"
    SUBSCRIPTION_UPDATE = "subscription.update"
    SUBSCRIPTION_CANCEL = "subscription.cancel"
    BILLING_MANUAL_REQUEST_CREATE = "billing.manual_request_create"
    CHECKOUT_SESSION_CREATE = "checkout_session.create"
    
    # Security
    UNAUTHORIZED_ACCESS = "security.unauthorized_access"
    RATE_LIMIT_EXCEEDED = "security.rate_limit_exceeded"
    PERMISSION_DENIED = "security.permission_denied"



