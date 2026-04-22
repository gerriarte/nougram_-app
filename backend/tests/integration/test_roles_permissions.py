"""
Integration tests for roles and permissions system
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import (
    PERM_ACCESS_ALL_TENANTS,
    PERM_CREATE_QUOTES,
    PERM_MODIFY_COSTS,
    PERM_SEND_QUOTES,
    PERM_VIEW_SENSITIVE_DATA,
    PermissionError,
    can_create,
    can_edit,
    can_user_access_tenant,
    check_permission,
    get_user_role_type,
    has_permission,
)
from app.core.roles import (
    get_role_type,
    is_support_role,
    is_tenant_role,
    validate_role_type_and_organization,
)
from app.core.security import get_password_hash
from app.models.organization import Organization
from app.models.user import User


@pytest.fixture
async def org_a(db_session: AsyncSession) -> Organization:
    """Create Organization A for testing"""
    import uuid

    unique_id = str(uuid.uuid4())[:8]
    org = Organization(
        name="Test Organization A",
        slug=f"test-org-a-{unique_id}",
        subscription_plan="free",
        subscription_status="active",
    )
    db_session.add(org)
    await db_session.commit()
    await db_session.refresh(org)
    return org


@pytest.fixture
async def org_b(db_session: AsyncSession) -> Organization:
    """Create Organization B for testing"""
    import uuid

    unique_id = str(uuid.uuid4())[:8]
    org = Organization(
        name="Test Organization B",
        slug=f"test-org-b-{unique_id}",
        subscription_plan="starter",
        subscription_status="active",
    )
    db_session.add(org)
    await db_session.commit()
    await db_session.refresh(org)
    return org


@pytest.fixture
async def super_admin_user(db_session: AsyncSession) -> User:
    """Create super_admin user (support role)"""
    import uuid

    unique_id = str(uuid.uuid4())[:8]
    user = User(
        email=f"superadmin-{unique_id}@test.com",
        full_name="Super Admin",
        hashed_password=get_password_hash("password123"),
        role="super_admin",
        role_type="support",
        organization_id=None,  # Support users can have NULL org_id
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def owner_user(db_session: AsyncSession, org_a: Organization) -> User:
    """Create owner user (tenant role)"""
    import uuid

    unique_id = str(uuid.uuid4())[:8]
    user = User(
        email=f"owner-{unique_id}@test.com",
        full_name="Owner",
        hashed_password=get_password_hash("password123"),
        role="owner",
        role_type="tenant",
        organization_id=org_a.id,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def product_manager_user(db_session: AsyncSession, org_a: Organization) -> User:
    """Create product_manager user (tenant role)"""
    import uuid

    unique_id = str(uuid.uuid4())[:8]
    user = User(
        email=f"pm-{unique_id}@test.com",
        full_name="Product Manager",
        hashed_password=get_password_hash("password123"),
        role="product_manager",
        role_type="tenant",
        organization_id=org_a.id,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def collaborator_user(db_session: AsyncSession, org_a: Organization) -> User:
    """Create collaborator user (tenant role)"""
    import uuid

    unique_id = str(uuid.uuid4())[:8]
    user = User(
        email=f"collab-{unique_id}@test.com",
        full_name="Collaborator",
        hashed_password=get_password_hash("password123"),
        role="collaborator",
        role_type="tenant",
        organization_id=org_a.id,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.mark.integration
class TestRoleTypes:
    """Tests for role type system"""

    async def test_support_role_identification(self, super_admin_user: User):
        """Test that support roles are correctly identified"""
        assert is_support_role(super_admin_user.role)
        assert not is_tenant_role(super_admin_user.role)
        assert get_role_type(super_admin_user.role) == "support"
        assert get_user_role_type(super_admin_user) == "support"

    async def test_tenant_role_identification(self, owner_user: User):
        """Test that tenant roles are correctly identified"""
        assert is_tenant_role(owner_user.role)
        assert not is_support_role(owner_user.role)
        assert get_role_type(owner_user.role) == "tenant"
        assert get_user_role_type(owner_user) == "tenant"

    async def test_role_type_inference_from_role(
        self, db_session: AsyncSession, org_a: Organization
    ):
        """Test that role_type is inferred from role if not set"""
        import uuid

        unique_id = str(uuid.uuid4())[:8]
        user = User(
            email=f"infer-{unique_id}@test.com",
            full_name="Infer Test",
            hashed_password=get_password_hash("password123"),
            role="owner",
            role_type=None,  # Not set, should be inferred
            organization_id=org_a.id,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Should infer "tenant" from role
        assert get_user_role_type(user) == "tenant"

    async def test_backward_compatibility_null_role_type(
        self, db_session: AsyncSession, org_a: Organization
    ):
        """Test backward compatibility with NULL role_type"""
        import uuid

        unique_id = str(uuid.uuid4())[:8]
        user = User(
            email=f"backward-{unique_id}@test.com",
            full_name="Backward Compat",
            hashed_password=get_password_hash("password123"),
            role=None,
            role_type=None,  # Old users might have both NULL
            organization_id=org_a.id,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Should default to "tenant"
        assert get_user_role_type(user) == "tenant"

    async def test_validate_role_type_and_organization_support(self):
        """Test validation for support roles"""
        is_valid, error = validate_role_type_and_organization(
            role_type="support", role="super_admin", organization_id=None
        )
        assert is_valid
        assert error is None

    async def test_validate_role_type_and_organization_tenant_with_org(self, org_a: Organization):
        """Test validation for tenant roles with organization"""
        is_valid, error = validate_role_type_and_organization(
            role_type="tenant", role="owner", organization_id=org_a.id
        )
        assert is_valid
        assert error is None

    async def test_validate_role_type_and_organization_tenant_without_org(self):
        """Test validation fails for tenant roles without organization"""
        is_valid, error = validate_role_type_and_organization(
            role_type="tenant", role="owner", organization_id=None
        )
        assert not is_valid
        assert "organization_id" in error.lower()


@pytest.mark.integration
class TestPermissions:
    """Tests for permission system"""

    async def test_super_admin_permissions(self, super_admin_user: User):
        """Test that super_admin has all permissions"""
        assert has_permission(super_admin_user, PERM_ACCESS_ALL_TENANTS)
        assert has_permission(super_admin_user, PERM_VIEW_SENSITIVE_DATA)
        assert has_permission(super_admin_user, PERM_CREATE_QUOTES)
        assert has_permission(super_admin_user, PERM_SEND_QUOTES)
        assert has_permission(super_admin_user, PERM_MODIFY_COSTS)

    async def test_owner_permissions(self, owner_user: User):
        """Test that owner has tenant-level permissions"""
        assert has_permission(owner_user, PERM_VIEW_SENSITIVE_DATA)
        assert has_permission(owner_user, PERM_CREATE_QUOTES)
        assert has_permission(owner_user, PERM_SEND_QUOTES)
        assert has_permission(owner_user, PERM_MODIFY_COSTS)
        # Owner cannot access all tenants
        assert not has_permission(owner_user, PERM_ACCESS_ALL_TENANTS)

    async def test_product_manager_permissions(self, product_manager_user: User):
        """Test that product_manager has limited permissions"""
        assert has_permission(product_manager_user, PERM_CREATE_QUOTES)
        assert has_permission(product_manager_user, PERM_SEND_QUOTES)
        # Cannot view costs or modify costs
        assert not has_permission(product_manager_user, PERM_VIEW_SENSITIVE_DATA)
        assert not has_permission(product_manager_user, PERM_MODIFY_COSTS)

    async def test_collaborator_permissions(self, collaborator_user: User):
        """Test that collaborator has minimal permissions"""
        assert has_permission(collaborator_user, PERM_CREATE_QUOTES)
        # Cannot send quotes or view costs
        assert not has_permission(collaborator_user, PERM_SEND_QUOTES)
        assert not has_permission(collaborator_user, PERM_VIEW_SENSITIVE_DATA)

    async def test_check_permission_raises_exception(self, collaborator_user: User):
        """Test that check_permission raises exception when permission denied"""
        with pytest.raises(PermissionError):
            check_permission(collaborator_user, PERM_SEND_QUOTES)

        # Should not raise for allowed permission
        try:
            check_permission(collaborator_user, PERM_CREATE_QUOTES)
        except PermissionError:
            pytest.fail("check_permission raised PermissionError for allowed permission")


@pytest.mark.integration
class TestTenantAccess:
    """Tests for tenant access control"""

    async def test_support_user_can_access_all_tenants(
        self, super_admin_user: User, org_a: Organization, org_b: Organization
    ):
        """Test that support users can access all tenants"""
        assert can_user_access_tenant(super_admin_user, org_a.id)
        assert can_user_access_tenant(super_admin_user, org_b.id)
        assert can_user_access_tenant(super_admin_user, 999)  # Even non-existent org

    async def test_tenant_user_can_only_access_own_org(
        self, owner_user: User, org_a: Organization, org_b: Organization
    ):
        """Test that tenant users can only access their own organization"""
        assert can_user_access_tenant(owner_user, org_a.id)
        assert not can_user_access_tenant(owner_user, org_b.id)
        assert not can_user_access_tenant(owner_user, 999)

    async def test_can_create_resources(self, owner_user: User, product_manager_user: User):
        """Test can_create for different roles"""
        # Owner can create projects and services
        assert can_create(owner_user, "project")
        assert can_create(owner_user, "service")
        assert can_create(owner_user, "quote")

        # Product manager can create projects and quotes, but not services
        assert can_create(product_manager_user, "project")
        assert can_create(product_manager_user, "quote")
        assert not can_create(product_manager_user, "service")

    async def test_can_edit_resources(self, owner_user: User, product_manager_user: User):
        """Test can_edit for different roles"""
        # Owner can edit costs
        assert can_edit(owner_user, "cost")

        # Product manager cannot edit costs
        assert not can_edit(product_manager_user, "cost")


@pytest.mark.integration
class TestBackwardCompatibility:
    """Tests for backward compatibility"""

    async def test_user_without_role_type_defaults_to_tenant(
        self, db_session: AsyncSession, org_a: Organization
    ):
        """Test that users without role_type default to tenant"""
        import uuid

        unique_id = str(uuid.uuid4())[:8]
        user = User(
            email=f"nortype-{unique_id}@test.com",
            full_name="No Role Type",
            hashed_password=get_password_hash("password123"),
            role="product_manager",
            role_type=None,
            organization_id=org_a.id,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        assert get_user_role_type(user) == "tenant"
        assert is_tenant_role(user.role)
