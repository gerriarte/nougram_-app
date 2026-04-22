"""
Integration tests for quote creation endpoints
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, get_password_hash
from app.models.organization import Organization
from app.models.project import Project
from app.models.user import User


def get_auth_headers(user: User) -> dict:
    """Generate authorization headers for a user"""
    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "name": user.full_name,
        "organization_id": user.organization_id,
    }
    token = create_access_token(token_data)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def test_org_with_user(db_session: AsyncSession) -> tuple[Organization, User]:
    """Create test organization with user"""
    unique_id = str(uuid.uuid4())[:8]

    org = Organization(
        name="Test Quote Org",
        slug=f"test-quote-org-{unique_id}",
        subscription_plan="free",
        subscription_status="active",
        primary_currency="USD",
    )
    db_session.add(org)
    await db_session.commit()
    await db_session.refresh(org)

    user = User(
        email=f"user{unique_id}@test.com",
        full_name="Test User",
        hashed_password=get_password_hash("password123"),
        organization_id=org.id,
        role="owner",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    return org, user


@pytest.fixture
async def other_organization(db_session: AsyncSession) -> Organization:
    """Create another organization for tenant isolation tests"""
    unique_id = str(uuid.uuid4())[:8]

    org = Organization(
        name="Other Organization",
        slug=f"other-org-{unique_id}",
        subscription_plan="free",
        subscription_status="active",
        primary_currency="USD",
    )
    db_session.add(org)
    await db_session.commit()
    await db_session.refresh(org)

    return org


@pytest.mark.integration
class TestSearchClientsEndpoint:
    """Tests for GET /api/v1/projects/clients/search"""

    async def test_search_clients_endpoint_success(
        self,
        async_client: AsyncClient,
        test_org_with_user: tuple[Organization, User],
        db_session: AsyncSession,
    ):
        """Test endpoint de búsqueda de clientes - éxito"""
        org, user = test_org_with_user

        # Crear proyectos de prueba
        project1 = Project(
            name="Proyecto 1",
            client_name="TechStore Inc",
            client_email="contacto@techstore.com",
            organization_id=org.id,
            currency="USD",
        )
        project2 = Project(
            name="Proyecto 2",
            client_name="TechStore Inc",
            client_email="contacto@techstore.com",
            organization_id=org.id,
            currency="USD",
        )
        project3 = Project(
            name="Proyecto 3",
            client_name="Retail Corp",
            client_email="info@retail.com",
            organization_id=org.id,
            currency="USD",
        )

        db_session.add_all([project1, project2, project3])
        await db_session.commit()

        # Llamar al endpoint
        response = await async_client.get(
            "/api/v1/projects/clients/search?q=Tech&limit=10", headers=get_auth_headers(user)
        )

        assert response.status_code == 200
        data = response.json()
        assert "clients" in data
        assert "total" in data
        assert len(data["clients"]) > 0
        assert data["clients"][0]["name"] == "TechStore Inc"
        assert data["clients"][0]["project_count"] == 2

    async def test_search_clients_endpoint_query_too_short(
        self, async_client: AsyncClient, test_org_with_user: tuple[Organization, User]
    ):
        """Test endpoint de búsqueda - query muy corto"""
        org, user = test_org_with_user

        response = await async_client.get(
            "/api/v1/projects/clients/search?q=T&limit=10", headers=get_auth_headers(user)
        )

        assert response.status_code == 400

    async def test_search_clients_respects_tenant(
        self,
        async_client: AsyncClient,
        test_org_with_user: tuple[Organization, User],
        other_organization: Organization,
        db_session: AsyncSession,
    ):
        """Test que la búsqueda respeta tenant scoping"""
        org, user = test_org_with_user

        # Crear proyectos en diferentes organizaciones
        project1 = Project(
            name="Proyecto Org 1",
            client_name="Cliente Org 1",
            organization_id=org.id,
            currency="USD",
        )
        project2 = Project(
            name="Proyecto Org 2",
            client_name="Cliente Org 2",
            organization_id=other_organization.id,
            currency="USD",
        )

        db_session.add_all([project1, project2])
        await db_session.commit()

        # Buscar "Cliente"
        response = await async_client.get(
            "/api/v1/projects/clients/search?q=Cliente&limit=10", headers=get_auth_headers(user)
        )

        assert response.status_code == 200
        data = response.json()
        # Solo debe encontrar clientes de la organización del usuario
        assert len(data["clients"]) == 1
        assert data["clients"][0]["name"] == "Cliente Org 1"

    async def test_search_clients_excludes_deleted(
        self,
        async_client: AsyncClient,
        test_org_with_user: tuple[Organization, User],
        db_session: AsyncSession,
    ):
        """Test que la búsqueda excluye proyectos eliminados"""
        org, user = test_org_with_user
        from datetime import datetime

        # Crear proyecto activo y eliminado
        project1 = Project(
            name="Proyecto Activo",
            client_name="Cliente Activo",
            organization_id=org.id,
            currency="USD",
        )
        project2 = Project(
            name="Proyecto Eliminado",
            client_name="Cliente Eliminado",
            organization_id=org.id,
            currency="USD",
            deleted_at=datetime.utcnow(),
        )

        db_session.add_all([project1, project2])
        await db_session.commit()

        # Buscar "Cliente"
        response = await async_client.get(
            "/api/v1/projects/clients/search?q=Cliente&limit=10", headers=get_auth_headers(user)
        )

        assert response.status_code == 200
        data = response.json()
        # Solo debe encontrar cliente activo
        assert len(data["clients"]) == 1
        assert data["clients"][0]["name"] == "Cliente Activo"


@pytest.mark.integration
class TestGenerateExecutiveSummaryEndpoint:
    """Tests for POST /api/v1/ai/generate-executive-summary"""

    async def test_generate_executive_summary_endpoint_success(
        self, async_client: AsyncClient, test_org_with_user: tuple[Organization, User], mocker
    ):
        """Test endpoint de generación de resumen ejecutivo - éxito"""
        org, user = test_org_with_user

        # Mock de OpenAI
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[
            0
        ].message.content = "Este es un resumen ejecutivo de prueba generado por IA."
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 50
        mock_response.usage.total_tokens = 150

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        # Mock del servicio de IA
        with patch("app.api.v1.endpoints.ai.ai_service") as mock_ai_service:
            mock_ai_service.is_available.return_value = True
            mock_ai_service.generate_executive_summary = AsyncMock(
                return_value={
                    "success": True,
                    "summary": "Este es un resumen ejecutivo de prueba generado por IA.",
                    "usage": {
                        "prompt_tokens": 100,
                        "completion_tokens": 50,
                        "total_tokens": 150,
                        "estimated_cost": 0.01,
                    },
                }
            )

            payload = {
                "project_name": "Proyecto Test",
                "client_name": "Cliente Test",
                "client_sector": "Tecnología",
                "services": [
                    {
                        "service_id": 1,
                        "service_name": "Desarrollo Frontend",
                        "estimated_hours": 80,
                        "client_price": "12000",
                    }
                ],
                "total_price": "12000",
                "currency": "USD",
                "language": "es",
            }

            response = await async_client.post(
                "/api/v1/ai/generate-executive-summary",
                json=payload,
                headers=get_auth_headers(user),
            )

            assert response.status_code == 200
            data = response.json()
            assert "summary" in data
            assert "provider" in data
            assert data["provider"] == "openai"
            assert len(data["summary"]) > 0

    async def test_generate_executive_summary_endpoint_ai_not_available(
        self, async_client: AsyncClient, test_org_with_user: tuple[Organization, User]
    ):
        """Test endpoint de generación - IA no disponible"""
        org, user = test_org_with_user

        # Mock del servicio de IA para simular que no está disponible
        with patch("app.api.v1.endpoints.ai.ai_service") as mock_ai_service:
            mock_ai_service.is_available.return_value = False

            payload = {
                "project_name": "Proyecto Test",
                "client_name": "Cliente Test",
                "services": [
                    {"service_id": 1, "service_name": "Servicio Test", "client_price": "1000"}
                ],
                "total_price": "1000",
                "currency": "USD",
            }

            response = await async_client.post(
                "/api/v1/ai/generate-executive-summary",
                json=payload,
                headers=get_auth_headers(user),
            )

            assert response.status_code == 503

    async def test_generate_executive_summary_endpoint_no_services(
        self, async_client: AsyncClient, test_org_with_user: tuple[Organization, User]
    ):
        """Test endpoint de generación - sin servicios"""
        org, user = test_org_with_user

        with patch("app.api.v1.endpoints.ai.ai_service") as mock_ai_service:
            mock_ai_service.is_available.return_value = True

            payload = {
                "project_name": "Proyecto Test",
                "client_name": "Cliente Test",
                "services": [],
                "total_price": "1000",
                "currency": "USD",
            }

            response = await async_client.post(
                "/api/v1/ai/generate-executive-summary",
                json=payload,
                headers=get_auth_headers(user),
            )

            assert response.status_code == 400
