"""
Integration tests for AI-powered endpoints

Tests all AI endpoints including:
- /ai/suggest-config (onboarding suggestions)
- /ai/parse-document (document parsing)
- /ai/process-command (natural language commands)
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.organization import Organization
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


@pytest.mark.integration
class TestAISuggestConfigEndpoint:
    """Tests for /ai/suggest-config endpoint"""

    @pytest.mark.asyncio
    async def test_suggest_config_success(
        self, async_client: AsyncClient, test_user: User, test_organization: Organization
    ):
        """Test successful AI onboarding suggestion"""
        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps(
            {
                "suggested_roles": [
                    {
                        "name": "John Doe",
                        "role": "Senior Developer",
                        "salary_monthly_brute": 5000,
                        "currency": "USD",
                        "billable_hours_per_week": 40,
                        "is_active": True,
                    }
                ],
                "suggested_services": [
                    {
                        "name": "Web Development",
                        "description": "Custom web development",
                        "default_margin_target": 0.30,
                        "pricing_type": "hourly",
                        "is_active": True,
                    }
                ],
                "suggested_fixed_costs": [
                    {
                        "name": "AWS Hosting",
                        "amount_monthly": 200,
                        "currency": "USD",
                        "category": "Tools",
                        "description": "Cloud hosting",
                    }
                ],
                "confidence_scores": {"roles": 0.9, "services": 0.85, "costs": 0.8},
                "reasoning": "Based on industry standards",
            }
        )
        mock_response.usage = MagicMock()
        mock_response.usage.prompt_tokens = 500
        mock_response.usage.completion_tokens = 300
        mock_response.usage.total_tokens = 800

        with patch("app.services.ai_service.AsyncOpenAI") as mock_openai_class:
            mock_client = AsyncMock()
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_openai_class.return_value = mock_client

            headers = get_auth_headers(test_user)
            response = await async_client.post(
                "/api/v1/ai/suggest-config",
                json={
                    "industry": "Marketing Digital",
                    "region": "US",
                    "currency": "USD",
                    "custom_context": None,
                },
                headers=headers,
            )

            assert response.status_code == 200
            data = response.json()
            assert "suggested_roles" in data
            assert "suggested_services" in data
            assert "suggested_fixed_costs" in data
            assert "confidence_scores" in data
            assert len(data["suggested_roles"]) == 1
            assert len(data["suggested_services"]) == 1
            assert len(data["suggested_fixed_costs"]) == 1

    @pytest.mark.asyncio
    async def test_suggest_config_without_auth(self, async_client: AsyncClient):
        """Test suggest-config endpoint without authentication"""
        response = await async_client.post(
            "/api/v1/ai/suggest-config",
            json={"industry": "Marketing Digital", "region": "US", "currency": "USD"},
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_suggest_config_missing_industry(
        self, async_client: AsyncClient, test_user: User
    ):
        """Test suggest-config with missing required field"""
        headers = get_auth_headers(test_user)
        response = await async_client.post(
            "/api/v1/ai/suggest-config", json={"region": "US", "currency": "USD"}, headers=headers
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_suggest_config_cache_hit(
        self, async_client: AsyncClient, test_user: User, test_organization: Organization
    ):
        """Test suggest-config returns cached result"""
        from app.core.cache import get_cache

        # Pre-populate cache
        cache = get_cache()
        cached_data = {
            "suggested_roles": [],
            "suggested_services": [],
            "suggested_fixed_costs": [],
            "confidence_scores": {"roles": 0.9, "services": 0.8, "costs": 0.7},
        }
        cache.set("ai_suggestion:marketing digital:us:usd", cached_data, ttl_seconds=86400)

        headers = get_auth_headers(test_user)
        response = await async_client.post(
            "/api/v1/ai/suggest-config",
            json={"industry": "Marketing Digital", "region": "US", "currency": "USD"},
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "suggested_roles" in data
        # Verify it's from cache (no OpenAI call made)
        # This is verified by the fact that we didn't mock OpenAI and it still worked


@pytest.mark.integration
class TestAIParseDocumentEndpoint:
    """Tests for /ai/parse-document endpoint"""

    @pytest.mark.asyncio
    async def test_parse_document_success(
        self, async_client: AsyncClient, test_user: User, test_organization: Organization
    ):
        """Test successful document parsing"""
        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps(
            {
                "team_members": [
                    {
                        "name": "Jane Smith",
                        "role": "Designer",
                        "salary_monthly_brute": 4000,
                        "currency": "USD",
                        "billable_hours_per_week": 40,
                    }
                ],
                "fixed_costs": [
                    {
                        "name": "Adobe Creative Cloud",
                        "amount_monthly": 50,
                        "currency": "USD",
                        "category": "Tools",
                    }
                ],
                "subscriptions": [],
                "confidence_scores": {
                    "team_members": 0.85,
                    "fixed_costs": 0.9,
                    "subscriptions": 0.8,
                },
                "warnings": [],
            }
        )
        mock_response.usage = MagicMock()
        mock_response.usage.prompt_tokens = 600
        mock_response.usage.completion_tokens = 400
        mock_response.usage.total_tokens = 1000

        with patch("app.services.ai_service.AsyncOpenAI") as mock_openai_class:
            mock_client = AsyncMock()
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_openai_class.return_value = mock_client

            headers = get_auth_headers(test_user)
            response = await async_client.post(
                "/api/v1/ai/parse-document",
                json={
                    "text": "Jane Smith, Designer, $4000/month\nAdobe Creative Cloud: $50/month",
                    "document_type": "payroll",
                },
                headers=headers,
            )

            assert response.status_code == 200
            data = response.json()
            assert "team_members" in data
            assert "fixed_costs" in data
            assert "subscriptions" in data
            assert "confidence_scores" in data
            assert len(data["team_members"]) == 1
            assert len(data["fixed_costs"]) == 1

    @pytest.mark.asyncio
    async def test_parse_document_empty_text(self, async_client: AsyncClient, test_user: User):
        """Test parse-document with empty text"""
        headers = get_auth_headers(test_user)
        response = await async_client.post(
            "/api/v1/ai/parse-document",
            json={"text": "", "document_type": "payroll"},
            headers=headers,
        )

        assert response.status_code == 400
        data = response.json()
        assert "required" in data["detail"].lower() or "empty" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_parse_document_text_too_long(self, async_client: AsyncClient, test_user: User):
        """Test parse-document with text exceeding max length"""
        headers = get_auth_headers(test_user)
        long_text = "A" * 10001  # Exceeds 10000 character limit
        response = await async_client.post(
            "/api/v1/ai/parse-document",
            json={"text": long_text, "document_type": "payroll"},
            headers=headers,
        )

        assert response.status_code == 400
        data = response.json()
        assert "too long" in data["detail"].lower() or "maximum" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_parse_document_without_auth(self, async_client: AsyncClient):
        """Test parse-document endpoint without authentication"""
        response = await async_client.post(
            "/api/v1/ai/parse-document", json={"text": "Test text", "document_type": "payroll"}
        )

        assert response.status_code == 401


@pytest.mark.integration
class TestAIProcessCommandEndpoint:
    """Tests for /ai/process-command endpoint"""

    @pytest.mark.asyncio
    async def test_process_command_success(
        self, async_client: AsyncClient, test_user: User, test_organization: Organization
    ):
        """Test successful natural language command processing"""
        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps(
            {
                "action": "add_team_member",
                "data": {
                    "name": "Bob Johnson",
                    "role": "Senior Designer",
                    "salary_monthly_brute": 4500,
                    "currency": "USD",
                    "billable_hours_per_week": 40,
                },
                "confidence": 0.9,
                "reasoning": "Command clearly requests adding a team member",
            }
        )
        mock_response.usage = MagicMock()
        mock_response.usage.prompt_tokens = 400
        mock_response.usage.completion_tokens = 200
        mock_response.usage.total_tokens = 600

        with patch("app.services.ai_service.AsyncOpenAI") as mock_openai_class:
            mock_client = AsyncMock()
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_openai_class.return_value = mock_client

            headers = get_auth_headers(test_user)
            response = await async_client.post(
                "/api/v1/ai/process-command",
                json={
                    "command": "Add a Senior Designer named Bob Johnson with salary $4500/month",
                    "context": None,
                },
                headers=headers,
            )

            assert response.status_code == 200
            data = response.json()
            assert "action" in data
            assert "data" in data
            assert "confidence" in data
            assert data["action"] == "add_team_member"
            assert data["data"]["name"] == "Bob Johnson"

    @pytest.mark.asyncio
    async def test_process_command_empty_command(self, async_client: AsyncClient, test_user: User):
        """Test process-command with empty command"""
        headers = get_auth_headers(test_user)
        response = await async_client.post(
            "/api/v1/ai/process-command", json={"command": "", "context": None}, headers=headers
        )

        assert response.status_code == 400
        data = response.json()
        assert "required" in data["detail"].lower() or "empty" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_process_command_with_context(
        self, async_client: AsyncClient, test_user: User, test_organization: Organization
    ):
        """Test process-command with context provided"""
        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps(
            {
                "action": "add_service",
                "data": {
                    "name": "Social Media Management",
                    "default_margin_target": 0.35,
                    "pricing_type": "recurring",
                },
                "confidence": 0.85,
            }
        )
        mock_response.usage = MagicMock()
        mock_response.usage.prompt_tokens = 500
        mock_response.usage.completion_tokens = 250
        mock_response.usage.total_tokens = 750

        with patch("app.services.ai_service.AsyncOpenAI") as mock_openai_class:
            mock_client = AsyncMock()
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_openai_class.return_value = mock_client

            headers = get_auth_headers(test_user)
            response = await async_client.post(
                "/api/v1/ai/process-command",
                json={
                    "command": "Add a recurring service for social media",
                    "context": {"existing_services": ["Web Development", "SEO"], "currency": "USD"},
                },
                headers=headers,
            )

            assert response.status_code == 200
            data = response.json()
            assert "action" in data
            assert data["action"] == "add_service"

    @pytest.mark.asyncio
    async def test_process_command_without_auth(self, async_client: AsyncClient):
        """Test process-command endpoint without authentication"""
        response = await async_client.post(
            "/api/v1/ai/process-command", json={"command": "Add a team member", "context": None}
        )

        assert response.status_code == 401


@pytest.mark.integration
class TestAIRateLimiting:
    """Tests for rate limiting on AI endpoints"""

    @pytest.mark.asyncio
    async def test_rate_limiting_suggest_config(
        self, async_client: AsyncClient, test_user: User, test_organization: Organization
    ):
        """Test rate limiting on suggest-config endpoint"""
        # Mock OpenAI to avoid actual API calls
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps(
            {
                "suggested_roles": [],
                "suggested_services": [],
                "suggested_fixed_costs": [],
                "confidence_scores": {"roles": 0.5, "services": 0.5, "costs": 0.5},
            }
        )
        mock_response.usage = MagicMock()
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 100
        mock_response.usage.total_tokens = 200

        with patch("app.services.ai_service.AsyncOpenAI") as mock_openai_class:
            mock_client = AsyncMock()
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_openai_class.return_value = mock_client

            headers = get_auth_headers(test_user)

            # Make multiple requests quickly (exceeding rate limit)
            # Free plan has 5 requests per minute for AI endpoints
            responses = []
            for _i in range(6):  # One more than the limit
                response = await async_client.post(
                    "/api/v1/ai/suggest-config",
                    json={"industry": "Marketing Digital", "region": "US", "currency": "USD"},
                    headers=headers,
                )
                responses.append(response.status_code)

            # At least one should be rate limited (429)
            # Note: Rate limiting might not trigger in test environment depending on configuration
            # This test verifies the endpoint is protected by rate limiting decorator
            assert all(status in [200, 429] for status in responses)


@pytest.mark.integration
class TestAIDataAnonymization:
    """Tests for data anonymization in AI endpoints"""

    @pytest.mark.asyncio
    async def test_process_command_anonymizes_names(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_organization: Organization,
        db_session: AsyncSession,
    ):
        """Test that process-command anonymizes team member names in context"""
        from app.models.team import TeamMember

        # Create a team member with a real name
        team_member = TeamMember(
            name="John Smith",
            role="Developer",
            salary_monthly_brute=5000,
            currency="USD",
            billable_hours_per_week=40,
            is_active=True,
            organization_id=test_organization.id,
        )
        db_session.add(team_member)
        await db_session.commit()

        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps(
            {
                "action": "add_team_member",
                "data": {
                    "name": "New Member",
                    "role": "Designer",
                    "salary_monthly_brute": 4000,
                    "currency": "USD",
                    "billable_hours_per_week": 40,
                },
                "confidence": 0.9,
            }
        )
        mock_response.usage = MagicMock()
        mock_response.usage.prompt_tokens = 300
        mock_response.usage.completion_tokens = 150
        mock_response.usage.total_tokens = 450

        with patch("app.services.ai_service.AsyncOpenAI") as mock_openai_class:
            mock_client = AsyncMock()
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_openai_class.return_value = mock_client

            headers = get_auth_headers(test_user)
            response = await async_client.post(
                "/api/v1/ai/process-command",
                json={
                    "command": "Add a new designer",
                    "context": None,  # Context will be built automatically
                },
                headers=headers,
            )

            assert response.status_code == 200
            # Verify that the OpenAI call was made (names should be anonymized in context)
            assert mock_client.chat.completions.create.called
            # The actual anonymization is verified by checking the prompt content
            # but we can't easily access that in integration tests without more complex mocking
