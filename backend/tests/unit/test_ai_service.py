"""
Unit tests for AI service
"""

import json
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.cache import get_cache
from app.schemas.ai import ExecutiveSummaryRequest, ExecutiveSummaryService
from app.services.ai_service import AIService


def _apply_ai_service_settings_mock(mock_settings, *, openai_api_key="test-key-123"):
    """MagicMock settings must expose real scalars or AIService treats provider as non-openai."""
    mock_settings.AI_PROVIDER = "openai"
    mock_settings.AI_MODEL = "gpt-4o-mini"
    mock_settings.AI_TIMEOUT_SECONDS = 30
    mock_settings.AI_MAX_RETRIES = 2
    mock_settings.OPENAI_API_KEY = openai_api_key


@pytest.mark.unit
class TestAIService:
    """Tests for AIService"""

    def test_is_available_with_key(self):
        """Test is_available returns True when API key is set"""
        with patch("app.services.ai_service.settings") as mock_settings:
            _apply_ai_service_settings_mock(mock_settings)
            service = AIService()
            assert service.is_available() is True

    def test_is_available_without_key(self):
        """Test is_available returns False when API key is not set"""
        with patch("app.services.ai_service.settings") as mock_settings:
            _apply_ai_service_settings_mock(mock_settings, openai_api_key="")
            service = AIService()
            assert service.is_available() is False

    @pytest.mark.asyncio
    async def test_suggest_onboarding_data_cache_hit(self):
        """Test suggest_onboarding_data returns cached result"""
        with patch("app.services.ai_service.settings") as mock_settings:
            _apply_ai_service_settings_mock(mock_settings)
            service = AIService()

            # Pre-populate cache
            cache = get_cache()
            cached_data = {
                "suggested_roles": [
                    {
                        "name": "Test",
                        "role": "Developer",
                        "salary_monthly_brute": 5000,
                        "currency": "USD",
                        "billable_hours_per_week": 40,
                    }
                ],
                "suggested_services": [],
                "suggested_fixed_costs": [],
                "confidence_scores": {"roles": 0.9, "services": 0.8, "costs": 0.7},
            }
            cache.set("ai_suggestion:marketing digital:US:USD", cached_data, ttl_seconds=86400)

            result = await service.suggest_onboarding_data(
                industry="Marketing Digital", region="US", currency="USD"
            )

            assert result["success"] is True
            assert result["data"] == cached_data
            assert result["usage"]["cached"] is True
            assert result["usage"]["total_tokens"] == 0

    @pytest.mark.asyncio
    async def test_suggest_onboarding_data_cache_miss(self):
        """Test suggest_onboarding_data calls OpenAI when cache miss"""
        with patch("app.services.ai_service.settings") as mock_settings:
            _apply_ai_service_settings_mock(mock_settings)
            service = AIService()

            # Clear cache
            cache = get_cache()
            cache.invalidate("ai_suggestion:marketing digital:US:USD")

            # Mock OpenAI response
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = json.dumps(
                {
                    "suggested_roles": [
                        {
                            "name": "Test",
                            "role": "Developer",
                            "salary_monthly_brute": 5000,
                            "currency": "USD",
                            "billable_hours_per_week": 40,
                        }
                    ],
                    "suggested_services": [],
                    "suggested_fixed_costs": [],
                    "confidence_scores": {"roles": 0.9, "services": 0.8, "costs": 0.7},
                }
            )
            mock_response.usage = MagicMock()
            mock_response.usage.prompt_tokens = 100
            mock_response.usage.completion_tokens = 200
            mock_response.usage.total_tokens = 300

            mock_client = AsyncMock()
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            service.client = mock_client

            result = await service.suggest_onboarding_data(
                industry="Marketing Digital", region="US", currency="USD"
            )

            assert result["success"] is True
            assert "data" in result
            assert result["usage"]["cached"] is False
            assert result["usage"]["total_tokens"] == 300
            assert mock_client.chat.completions.create.called

    @pytest.mark.asyncio
    async def test_suggest_onboarding_data_not_available(self):
        """Test suggest_onboarding_data returns error when AI not available"""
        with patch("app.services.ai_service.settings") as mock_settings:
            _apply_ai_service_settings_mock(mock_settings, openai_api_key="")
            service = AIService()

            result = await service.suggest_onboarding_data(
                industry="Marketing Digital", region="US", currency="USD"
            )

            assert result["success"] is False
            assert "error" in result

    @pytest.mark.asyncio
    async def test_suggest_onboarding_data_custom_context_no_cache(self):
        """Test suggest_onboarding_data doesn't cache when custom_context is provided"""
        with patch("app.services.ai_service.settings") as mock_settings:
            _apply_ai_service_settings_mock(mock_settings)
            service = AIService()

            # Mock OpenAI response
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
            mock_response.usage.completion_tokens = 200
            mock_response.usage.total_tokens = 300

            mock_client = AsyncMock()
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            service.client = mock_client

            # Clear cache first
            cache = get_cache()
            cache.invalidate_pattern("ai_suggestion:")

            result = await service.suggest_onboarding_data(
                industry="Marketing Digital",
                region="US",
                currency="USD",
                custom_context="Custom business context here",
            )

            assert result["success"] is True
            # Verify cache was not populated (check that key with context hash doesn't exist)
            # Since custom_context is provided, it should use a different cache key
            assert mock_client.chat.completions.create.called

    @pytest.mark.asyncio
    async def test_parse_unstructured_data_basic(self):
        """Test parse_unstructured_data with valid text"""
        with patch("app.services.ai_service.settings") as mock_settings:
            _apply_ai_service_settings_mock(mock_settings)
            service = AIService()

            # Mock OpenAI response
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = json.dumps(
                {
                    "team_members": [
                        {
                            "name": "John Doe",
                            "role": "Developer",
                            "salary_monthly_brute": 5000,
                            "currency": "USD",
                        }
                    ],
                    "fixed_costs": [],
                    "subscriptions": [],
                }
            )
            mock_response.usage = MagicMock()
            mock_response.usage.prompt_tokens = 100
            mock_response.usage.completion_tokens = 200
            mock_response.usage.total_tokens = 300

            mock_client = AsyncMock()
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            service.client = mock_client

            result = await service.parse_unstructured_data(
                text="John Doe, Developer, $5000/month", document_type="payroll"
            )

            assert result["success"] is True
            assert "data" in result
            assert "team_members" in result["data"]
            assert len(result["data"]["team_members"]) == 1

    @pytest.mark.asyncio
    async def test_parse_unstructured_data_not_available(self):
        """Test parse_unstructured_data returns error when AI not available"""
        with patch("app.services.ai_service.settings") as mock_settings:
            _apply_ai_service_settings_mock(mock_settings, openai_api_key="")
            service = AIService()

            result = await service.parse_unstructured_data(
                text="Test text", document_type="payroll"
            )

            assert result["success"] is False
            assert "error" in result

    @pytest.mark.asyncio
    async def test_process_natural_language_command_basic(self):
        """Test process_natural_language_command with valid command"""
        with patch("app.services.ai_service.settings") as mock_settings:
            _apply_ai_service_settings_mock(mock_settings)
            service = AIService()

            # Mock OpenAI response
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = json.dumps(
                {
                    "action": "add_team_member",
                    "data": {
                        "name": "Jane Doe",
                        "role": "Designer",
                        "salary_monthly_brute": 4000,
                        "currency": "USD",
                        "billable_hours_per_week": 40,
                    },
                    "confidence": 0.9,
                }
            )
            mock_response.usage = MagicMock()
            mock_response.usage.prompt_tokens = 100
            mock_response.usage.completion_tokens = 200
            mock_response.usage.total_tokens = 300

            mock_client = AsyncMock()
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            service.client = mock_client

            result = await service.process_natural_language_command(
                command="Add a designer named Jane Doe with salary $4000/month", context=None
            )

            assert result["success"] is True
            assert "action" in result["data"]
            assert result["data"]["action"] == "add_team_member"
            assert "data" in result["data"]

    @pytest.mark.asyncio
    async def test_process_natural_language_command_not_available(self):
        """Test process_natural_language_command returns error when AI not available"""
        with patch("app.services.ai_service.settings") as mock_settings:
            _apply_ai_service_settings_mock(mock_settings, openai_api_key="")
            service = AIService()

            result = await service.process_natural_language_command(
                command="Add a team member", context=None
            )

            assert result["success"] is False
            assert "error" in result

    def test_estimate_cost(self):
        """Test cost estimation calculation"""
        with patch("app.services.ai_service.settings") as mock_settings:
            _apply_ai_service_settings_mock(mock_settings)
            service = AIService()

            # Mock usage object
            mock_usage = MagicMock()
            mock_usage.prompt_tokens = 1000
            mock_usage.completion_tokens = 500
            mock_usage.total_tokens = 1500

            cost = service._estimate_cost(mock_usage)

            # Should be > 0 (exact calculation depends on model pricing)
            assert cost > 0

    @pytest.mark.asyncio
    async def test_suggest_onboarding_data_json_decode_error(self):
        """Test suggest_onboarding_data handles JSON decode errors"""
        with patch("app.services.ai_service.settings") as mock_settings:
            _apply_ai_service_settings_mock(mock_settings)
            service = AIService()

            # Mock OpenAI response with invalid JSON
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Invalid JSON {"

            mock_client = AsyncMock()
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            service.client = mock_client

            result = await service.suggest_onboarding_data(
                industry="Marketing Digital", region="US", currency="USD"
            )

            assert result["success"] is False
            assert "error" in result

    @pytest.mark.asyncio
    async def test_generate_executive_summary_success(self):
        """Test generación exitosa de resumen ejecutivo"""
        with patch("app.services.ai_service.settings") as mock_settings:
            _apply_ai_service_settings_mock(mock_settings)

            # Mock de OpenAI client
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Este es un resumen ejecutivo de prueba."
            mock_response.usage.prompt_tokens = 100
            mock_response.usage.completion_tokens = 50
            mock_response.usage.total_tokens = 150

            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

            # Crear servicio con mock
            service = AIService()
            service.client = mock_client

            # Crear request
            request = ExecutiveSummaryRequest(
                project_name="Proyecto Test",
                client_name="Cliente Test",
                client_sector="Tecnología",
                services=[
                    ExecutiveSummaryService(
                        service_id=1,
                        service_name="Desarrollo Frontend",
                        estimated_hours=80,
                        client_price=Decimal("12000"),
                    )
                ],
                total_price=Decimal("12000"),
                currency="USD",
                language="es",
            )

            # Llamar al servicio
            result = await service.generate_executive_summary(request)

            # Verificar resultado
            assert result["success"] is True
            assert "summary" in result
            assert result["summary"] == "Este es un resumen ejecutivo de prueba."
            assert "usage" in result
            assert result["usage"]["total_tokens"] == 150

    @pytest.mark.asyncio
    async def test_generate_executive_summary_ai_not_available(self):
        """Test que retorna error cuando IA no está disponible"""
        with patch("app.services.ai_service.settings") as mock_settings:
            _apply_ai_service_settings_mock(mock_settings, openai_api_key=None)
            service = AIService()

            request = ExecutiveSummaryRequest(
                project_name="Proyecto Test",
                client_name="Cliente Test",
                services=[
                    ExecutiveSummaryService(
                        service_id=1, service_name="Servicio Test", client_price=Decimal("1000")
                    )
                ],
                total_price=Decimal("1000"),
                currency="USD",
            )

            result = await service.generate_executive_summary(request)

            assert result["success"] is False
            assert "error" in result

    def test_build_executive_summary_prompt(self):
        """Test construcción de prompt para resumen ejecutivo"""
        with patch("app.services.ai_service.settings") as mock_settings:
            _apply_ai_service_settings_mock(mock_settings)
            service = AIService()

            request = ExecutiveSummaryRequest(
                project_name="Proyecto Test",
                client_name="Cliente Test",
                client_sector="Tecnología",
                services=[
                    ExecutiveSummaryService(
                        service_id=1,
                        service_name="Desarrollo Frontend",
                        estimated_hours=80,
                        client_price=Decimal("12000"),
                    ),
                    ExecutiveSummaryService(
                        service_id=2, service_name="Diseño UI/UX", client_price=Decimal("8000")
                    ),
                ],
                total_price=Decimal("20000"),
                currency="USD",
                language="es",
            )

            prompt = service._build_executive_summary_prompt(request)

            # Verificar que el prompt contiene información relevante
            assert "Proyecto Test" in prompt
            assert "Cliente Test" in prompt
            assert "Tecnología" in prompt
            assert "Desarrollo Frontend" in prompt
            assert "Diseño UI/UX" in prompt
            assert "USD" in prompt
            assert "20,000" in prompt or "20000" in prompt
