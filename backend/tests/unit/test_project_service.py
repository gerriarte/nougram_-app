"""
Unit tests for ProjectService
"""

from unittest.mock import AsyncMock, patch

import pytest

from app.services.project_service import ProjectService


@pytest.mark.unit
class TestProjectService:
    """Tests for ProjectService"""

    @pytest.mark.asyncio
    async def test_search_clients_delegates_to_repository(self, db_session, test_organization):
        """Test que el servicio delega correctamente al repository"""
        service = ProjectService(db_session, test_organization.id)

        mock_results = [
            {
                "name": "Cliente Test",
                "email": "test@cliente.com",
                "project_count": 2,
                "last_project_date": None,
            }
        ]

        with patch.object(
            service.project_repo,
            "search_clients",
            new=AsyncMock(return_value=mock_results),
        ) as mock_search:
            results = await service.search_clients("Cliente", limit=10)

            mock_search.assert_awaited_once_with(search_query="Cliente", limit=10)
            assert results == mock_results
