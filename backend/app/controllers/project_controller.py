"""
Project Controller - HTTP request handling for projects
"""

from app.views.project_view import ProjectView
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.controllers.base import BaseController
from app.core.tenant import TenantContext
from app.models.user import User
from app.schemas.project import (
    ClientSearchResponse,
    ClientSearchResult,
    ProjectCreateWithQuote,
    ProjectListResponse,
    ProjectResponse,
    ProjectUpdate,
    QuoteResponseWithItems,
)
from app.services.project_service import ProjectService


class ProjectController(BaseController):
    """
    Controller for project operations

    Responsibilities:
    - HTTP request validation
    - Error handling
    - Delegation to ProjectService
    - Response transformation using ProjectView
    """

    def __init__(self, db: AsyncSession, tenant: TenantContext, current_user: User):
        super().__init__(db, tenant, current_user)
        self.project_service = ProjectService(db, tenant.organization_id)
        self.project_view = ProjectView()

    async def list_projects(
        self,
        status_filter: str | None = None,
        include_deleted: bool = False,
        page: int = 1,
        page_size: int = 20,
    ) -> ProjectListResponse:
        """
        List projects with pagination

        Args:
            status_filter: Optional status filter
            include_deleted: Whether to include soft-deleted projects
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            ProjectListResponse with paginated projects
        """
        self._log_info(
            "Listing projects",
            status_filter=status_filter,
            include_deleted=include_deleted,
            page=page,
            page_size=page_size,
        )

        try:
            projects, total = await self.project_service.list_projects(
                status_filter=status_filter,
                include_deleted=include_deleted,
                page=page,
                page_size=page_size,
            )

            return self.project_view.to_paginated_response(projects, total, page, page_size)
        except Exception as e:
            self._log_error(f"Error listing projects: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to list projects: {str(e)}",
            )

    async def get_project(self, project_id: int, include_deleted: bool = False) -> ProjectResponse:
        """
        Get project by ID

        Args:
            project_id: Project ID
            include_deleted: Whether to include soft-deleted projects

        Returns:
            ProjectResponse instance

        Raises:
            HTTPException 404: If project not found
        """
        self._log_info("Getting project", project_id=project_id, include_deleted=include_deleted)

        project = await self.project_service.get_project_by_id(
            project_id, include_deleted=include_deleted
        )

        if not project:
            self._handle_not_found("Project", project_id)

        return self.project_view.to_response(project)

    async def create_project(
        self,
        project_data: ProjectCreateWithQuote,
        subscription_plan: str,
        allow_low_margin: bool = False,
    ) -> QuoteResponseWithItems:
        """
        Create a new project with initial quote

        Args:
            project_data: Project and quote data
            subscription_plan: Subscription plan for limit validation
            allow_low_margin: Whether to allow low margin quotes

        Returns:
            QuoteResponseWithItems with created quote

        Raises:
            HTTPException: If creation fails
        """
        self._log_info(
            "Creating project", project_name=project_data.name, client_name=project_data.client_name
        )

        try:
            result = await self.project_service.create_project_with_quote(
                project_data=project_data,
                current_user=self.current_user,
                subscription_plan=subscription_plan,
                allow_low_margin=allow_low_margin,
            )

            self._log_info("Project created successfully", project_id=result.project_id)
            return result
        except HTTPException:
            raise
        except Exception as e:
            self._log_error(f"Error creating project: {str(e)}", exc_info=True)
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create project: {str(e)}",
            )

    async def update_project(self, project_id: int, project_data: ProjectUpdate) -> ProjectResponse:
        """
        Update an existing project

        Args:
            project_id: Project ID
            project_data: Update data

        Returns:
            Updated ProjectResponse instance

        Raises:
            HTTPException 404: If project not found
        """
        self._log_info("Updating project", project_id=project_id)

        try:
            project = await self.project_service.update_project(
                project_id=project_id, project_data=project_data, current_user=self.current_user
            )

            self._log_info("Project updated successfully", project_id=project_id)
            return self.project_view.to_response(project)
        except HTTPException:
            raise
        except Exception as e:
            self._log_error(f"Error updating project: {str(e)}", exc_info=True)
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update project: {str(e)}",
            )

    async def delete_project(self, project_id: int) -> None:
        """
        Soft delete a project

        Args:
            project_id: Project ID

        Raises:
            HTTPException 404: If project not found
        """
        self._log_info("Deleting project", project_id=project_id)

        try:
            await self.project_service.delete_project(
                project_id=project_id, current_user=self.current_user
            )

            self._log_info("Project deleted successfully", project_id=project_id)
        except HTTPException:
            raise
        except Exception as e:
            self._log_error(f"Error deleting project: {str(e)}", exc_info=True)
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete project: {str(e)}",
            )

    async def restore_project(self, project_id: int) -> ProjectResponse:
        """
        Restore a soft-deleted project

        Args:
            project_id: Project ID

        Returns:
            Restored ProjectResponse instance

        Raises:
            HTTPException 404: If project not found or not deleted
        """
        self._log_info("Restoring project", project_id=project_id)

        try:
            project = await self.project_service.restore_project(project_id)

            self._log_info("Project restored successfully", project_id=project_id)
            return self.project_view.to_response(project)
        except HTTPException:
            raise
        except Exception as e:
            self._log_error(f"Error restoring project: {str(e)}", exc_info=True)
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to restore project: {str(e)}",
            )

    async def search_clients(self, search_query: str, limit: int = 10) -> ClientSearchResponse:
        """
        Buscar clientes existentes

        Args:
            search_query: Query de búsqueda (mínimo 2 caracteres)
            limit: Límite de resultados (default: 10, max: 50)

        Returns:
            ClientSearchResponse con lista de clientes encontrados

        Raises:
            HTTPException: Si search_query es muy corto o hay error en la búsqueda
        """
        # Validar query mínimo
        if len(search_query.strip()) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Search query must be at least 2 characters long",
            )

        # Validar límite
        limit = min(max(limit, 1), 50)

        self._log_info("Searching clients", search_query=search_query, limit=limit)

        try:
            # Llamar al repository
            clients_data = await self.project_service.search_clients(
                search_query=search_query, limit=limit
            )

            # Convertir a schemas de respuesta
            clients = [
                ClientSearchResult(
                    name=client["name"],
                    email=client["email"],
                    project_count=client["project_count"],
                    last_project_date=client["last_project_date"],
                )
                for client in clients_data
            ]

            return ClientSearchResponse(clients=clients, total=len(clients))

        except Exception as e:
            self._log_error(f"Error searching clients: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to search clients: {str(e)}",
            )
