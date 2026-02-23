"""
Client Service - business logic for client master catalog.
"""
from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import desc
from fastapi import HTTPException, status

from app.models.client import Client
from app.repositories.factory import RepositoryFactory
from app.schemas.client import ClientCreate, ClientUpdate, ClientResponse, ClientSearchItem


class ClientService:
    """Service for managing clients (master catalog)."""

    def __init__(self, db: AsyncSession, organization_id: int):
        self.db = db
        self.organization_id = organization_id
        self.repo = RepositoryFactory.create_client_repository(db, organization_id)

    async def list_clients(
        self,
        status_filter: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Client], int]:
        """List clients with pagination."""
        total = await self.repo.count(
            where=(Client.status == status_filter) if status_filter else None
        )
        offset = (page - 1) * page_size
        items = await self.repo.get_all_paginated(
            status_filter=status_filter,
            order_by=desc(Client.display_name),
            limit=page_size,
            offset=offset,
        )
        return items, total

    async def get_by_id(self, client_id: int) -> Optional[Client]:
        """Get client by ID (tenant-scoped)."""
        return await self.repo.get_by_id(client_id)

    async def create(self, data: ClientCreate) -> Client:
        """Create a new client."""
        client = Client(
            organization_id=self.organization_id,
            display_name=data.display_name,
            requester_name=data.requester_name,
            email=data.email,
            status=data.status or "active",
            notes=data.notes,
        )
        return await self.repo.create(client)

    async def update(self, client_id: int, data: ClientUpdate) -> Client:
        """Update an existing client."""
        client = await self.repo.get_by_id(client_id)
        if not client:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
        payload = data.model_dump(exclude_unset=True)
        for k, v in payload.items():
            setattr(client, k, v)
        return await self.repo.update(client)

    async def search(self, q: str, limit: int = 10) -> List[Client]:
        """Search clients for autocomplete."""
        return await self.repo.search(q=q, limit=limit)
