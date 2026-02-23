"""
Repository Factory for creating repositories with tenant context
"""
from typing import Type, TypeVar, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.base import BaseRepository
from app.repositories.cost_repository import CostRepository
from app.repositories.service_repository import ServiceRepository
from app.repositories.client_repository import ClientRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.team_repository import TeamRepository
from app.repositories.user_repository import UserRepository
from app.repositories.tax_repository import TaxRepository
from app.repositories.settings_repository import SettingsRepository
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.subscription_repository import SubscriptionRepository
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.credit_account_repository import CreditAccountRepository
from app.repositories.credit_transaction_repository import CreditTransactionRepository
from app.repositories.invitation_repository import InvitationRepository
from app.core.tenant import TenantContext

T = TypeVar('T', bound=BaseRepository)


class RepositoryFactory:
    """
    Factory for creating repositories with tenant context
    
    Usage:
        tenant = TenantContext(...)
        repo = RepositoryFactory.create(ServiceRepository, db, tenant.organization_id)
    """
    
    # Map of repository types
    _repositories = {
        'cost': CostRepository,
        'service': ServiceRepository,
        'project': ProjectRepository,
        'team': TeamRepository,
        'user': UserRepository,
        'tax': TaxRepository,
        'settings': SettingsRepository,
    }
    
    @staticmethod
    def create(
        repo_type: Type[T],
        db: AsyncSession,
        tenant_id: int
    ) -> T:
        """
        Create a repository instance with tenant context
        
        Args:
            repo_type: Repository class type
            db: Database session
            tenant_id: Organization ID for tenant scoping
            
        Returns:
            Repository instance with tenant scoping enabled
        """
        return repo_type(db, tenant_id=tenant_id)
    
    @staticmethod
    def create_cost_repository(db: AsyncSession, tenant_id: int) -> CostRepository:
        """Create CostRepository with tenant context"""
        return CostRepository(db, tenant_id=tenant_id)
    
    @staticmethod
    def create_service_repository(db: AsyncSession, tenant_id: int) -> ServiceRepository:
        """Create ServiceRepository with tenant context"""
        return ServiceRepository(db, tenant_id=tenant_id)
    
    @staticmethod
    def create_client_repository(db: AsyncSession, tenant_id: int) -> ClientRepository:
        """Create ClientRepository with tenant context"""
        return ClientRepository(db, tenant_id=tenant_id)

    @staticmethod
    def create_project_repository(db: AsyncSession, tenant_id: int) -> ProjectRepository:
        """Create ProjectRepository with tenant context"""
        return ProjectRepository(db, tenant_id=tenant_id)
    
    @staticmethod
    def create_team_repository(db: AsyncSession, tenant_id: int) -> TeamRepository:
        """Create TeamRepository with tenant context"""
        return TeamRepository(db, tenant_id=tenant_id)
    
    @staticmethod
    def create_tax_repository(db: AsyncSession, tenant_id: int) -> TaxRepository:
        """Create TaxRepository with tenant context"""
        return TaxRepository(db, tenant_id=tenant_id)
    
    @staticmethod
    def create_user_repository(db: AsyncSession, tenant_id: int) -> UserRepository:
        """Create UserRepository with tenant context"""
        return UserRepository(db, tenant_id=tenant_id)
    
    @staticmethod
    def create_settings_repository(db: AsyncSession) -> SettingsRepository:
        """Create SettingsRepository (no tenant scoping)"""
        return SettingsRepository(db, tenant_id=None)
    
    @staticmethod
    def create_organization_repository(db: AsyncSession) -> OrganizationRepository:
        """Create OrganizationRepository (no tenant scoping)"""
        return OrganizationRepository(db, tenant_id=None)
    
    @staticmethod
    def create_subscription_repository(db: AsyncSession, tenant_id: Optional[int] = None) -> SubscriptionRepository:
        """Create SubscriptionRepository with optional tenant context"""
        return SubscriptionRepository(db, tenant_id=tenant_id)
    
    @staticmethod
    def create_audit_log_repository(db: AsyncSession) -> AuditLogRepository:
        """Create AuditLogRepository (no tenant scoping)"""
        return AuditLogRepository(db)
    
    @staticmethod
    def create_invitation_repository(db: AsyncSession, tenant_id: Optional[int] = None) -> InvitationRepository:
        """Create InvitationRepository with optional tenant context"""
        return InvitationRepository(db, tenant_id=tenant_id)


