"""
Pytest configuration and shared fixtures
"""

import asyncio
import os
from collections.abc import AsyncGenerator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

# Set test environment variables before importing settings
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing-only")
os.environ.setdefault("GOOGLE_CLIENT_ID", "test-google-client-id")
os.environ.setdefault("GOOGLE_CLIENT_SECRET", "test-google-client-secret")
os.environ.setdefault("GOOGLE_SERVICE_ACCOUNT_PATH", "test-path")
os.environ.setdefault("GOOGLE_SHEETS_ID", "test-sheets-id")

from app.core.database import Base, get_db
from app.core.security import get_password_hash
from app.models.cost import CostFixed
from app.models.organization import Organization
from app.models.service import Service
from app.models.settings import AgencySettings
from app.models.team import TeamMember
from app.models.user import User

# Test database URL (SQLite in-memory for tests)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session"""
    async_session = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def test_organization(db_session: AsyncSession) -> Organization:
    """Create a test organization"""
    from sqlalchemy import select

    # Check if default test org exists
    result = await db_session.execute(select(Organization).where(Organization.slug == "test-org"))
    org = result.scalar_one_or_none()

    if not org:
        org = Organization(
            name="Test Organization",
            slug="test-org",
            subscription_plan="free",
            subscription_status="active",
        )
        db_session.add(org)
        await db_session.commit()
        await db_session.refresh(org)

    return org


@pytest.fixture
async def test_user(db_session: AsyncSession, test_organization: Organization) -> User:
    """Create a test user with organization"""
    import uuid

    unique_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    user = User(
        email=unique_email,
        full_name="Test User",
        role="product_manager",
        hashed_password=get_password_hash("testpassword123"),
        organization_id=test_organization.id,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_admin_user(db_session: AsyncSession, test_organization: Organization) -> User:
    """Create a test admin user with organization"""
    import uuid

    unique_email = f"admin_{uuid.uuid4().hex[:8]}@example.com"
    user = User(
        email=unique_email,
        full_name="Admin User",
        role="super_admin",
        hashed_password=get_password_hash("adminpassword123"),
        organization_id=test_organization.id,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_settings(db_session: AsyncSession) -> AgencySettings:
    """Create test agency settings"""
    settings = AgencySettings(primary_currency="USD", currency_symbol="$")
    db_session.add(settings)
    await db_session.commit()
    await db_session.refresh(settings)
    return settings


@pytest.fixture
async def test_service(db_session: AsyncSession, test_organization: Organization) -> Service:
    """Create a test service with organization"""
    service = Service(
        name="Test Service",
        description="Test service description",
        default_margin_target=0.30,
        is_active=True,
        organization_id=test_organization.id,
    )
    db_session.add(service)
    await db_session.commit()
    await db_session.refresh(service)
    return service


@pytest.fixture
async def test_cost(db_session: AsyncSession, test_organization: Organization) -> CostFixed:
    """Create a test fixed cost with organization"""
    cost = CostFixed(
        name="Test Cost",
        amount_monthly=1000.0,
        currency="USD",
        category="Overhead",
        description="Test cost description",
        organization_id=test_organization.id,
    )
    db_session.add(cost)
    await db_session.commit()
    await db_session.refresh(cost)
    return cost


@pytest.fixture
async def test_team_member(
    db_session: AsyncSession, test_user: User, test_organization: Organization
) -> TeamMember:
    """Create a test team member with organization"""
    member = TeamMember(
        user_id=test_user.id,
        name="Test Member",
        role="Developer",
        salary_monthly_brute=5000.0,
        currency="USD",
        billable_hours_per_week=40,
        is_active=True,
        organization_id=test_organization.id,
    )
    db_session.add(member)
    await db_session.commit()
    await db_session.refresh(member)
    return member


@pytest.fixture
async def async_client(db_session: AsyncSession) -> AsyncGenerator:
    """Create an async test client for FastAPI with test database override"""

    from httpx import ASGITransport, AsyncClient

    from main import app

    # Override get_db dependency to use test database session
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client

    # Clean up overrides
    app.dependency_overrides.clear()
