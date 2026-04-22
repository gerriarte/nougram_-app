"""
Unit tests for ProjectService
"""

import pytest

from app.services.project_service import ProjectService


@pytest.mark.unit
class TestProjectService:
    """Tests for ProjectService"""

    @pytest.mark.asyncio
    async def test_search_clients_delegates_to_repository(
        self, db_session, test_organization, mocker
    ):
        """Test que el servicio delega correctamente al repository"""
        service = ProjectService(db_session, test_organization.id)

        # Mock del repository
        mock_results = [
            {
                "name": "Cliente Test",
                "email": "test@cliente.com",
                "project_count": 2,
                "last_project_date": None,
            }
        ]

        mocker.patch.object(service.project_repo, "search_clients", return_value=mock_results)

        # Llamar al servicio
        results = await service.search_clients("Cliente", limit=10)

        # Verificar que se llamó al repository
        service.project_repo.search_clients.assert_called_once_with("Cliente", limit=10)
        assert results == mock_results
