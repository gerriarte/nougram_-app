"""
Base repository class for data access operations
"""

from datetime import datetime
from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import Base

T = TypeVar("T", bound=Base)


class BaseRepository(Generic[T]):
    """
    Base repository class providing common CRUD operations with tenant scoping
    """

    def __init__(self, db: AsyncSession, model: type[T], tenant_id: int | None = None):
        """
        Initialize repository with database session and model

        Args:
            db: Async database session
            model: SQLAlchemy model class
            tenant_id: Organization ID for tenant scoping (None to disable scoping)
        """
        self.db = db
        self.model = model
        self.tenant_id = tenant_id

    def _apply_tenant_filter(self, query):
        """
        Apply tenant filter to query if tenant_id is set and model has organization_id

        Args:
            query: SQLAlchemy select query

        Returns:
            Query with tenant filter applied if applicable
        """
        if self.tenant_id is not None and hasattr(self.model, "organization_id"):
            query = query.where(self.model.organization_id == self.tenant_id)
        return query

    async def get_by_id(self, id: int, include_deleted: bool = False) -> T | None:
        """
        Get entity by ID (with tenant scoping)

        Args:
            id: Entity ID
            include_deleted: Whether to include soft-deleted entities

        Returns:
            Entity instance or None if not found or not in tenant scope
        """
        query = select(self.model).where(self.model.id == id)

        # Apply tenant filter
        query = self._apply_tenant_filter(query)

        if not include_deleted and hasattr(self.model, "deleted_at"):
            query = query.where(self.model.deleted_at.is_(None))

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        where=None,
        include_deleted: bool = False,
        order_by=None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[T]:
        """
        Get all entities matching criteria (with tenant scoping)

        Args:
            where: SQLAlchemy where clause
            include_deleted: Whether to include soft-deleted entities
            order_by: SQLAlchemy order_by clause
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of entity instances (filtered by tenant if applicable)
        """
        query = select(self.model)

        # Apply tenant filter first
        query = self._apply_tenant_filter(query)

        if not include_deleted and hasattr(self.model, "deleted_at"):
            query = query.where(self.model.deleted_at.is_(None))

        if where is not None:
            query = query.where(where)

        if order_by is not None:
            query = query.order_by(order_by)

        if limit is not None:
            query = query.limit(limit)

        if offset is not None:
            query = query.offset(offset)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def create(self, entity: T) -> T:
        """
        Create new entity (with tenant validation)

        Args:
            entity: Entity instance to create (must have organization_id if tenant_id is set)

        Returns:
            Created entity with ID populated

        Raises:
            ValueError: If entity organization_id doesn't match tenant_id
        """
        # Validate tenant if tenant_id is set
        if self.tenant_id is not None and hasattr(entity, "organization_id"):
            if entity.organization_id != self.tenant_id:
                raise ValueError(
                    f"Cannot create entity with organization_id={entity.organization_id} "
                    f"in tenant scope {self.tenant_id}"
                )
            # Ensure organization_id is set
            if entity.organization_id is None:
                entity.organization_id = self.tenant_id

        self.db.add(entity)
        await self.db.commit()
        await self.db.refresh(entity)
        return entity

    async def update(self, entity: T) -> T:
        """
        Update existing entity

        Args:
            entity: Entity instance to update

        Returns:
            Updated entity
        """
        await self.db.commit()
        await self.db.refresh(entity)
        return entity

    async def delete(self, entity: T, soft: bool = True, deleted_by_id: int | None = None) -> None:
        """
        Delete entity (soft delete by default)

        Args:
            entity: Entity instance to delete
            soft: Whether to perform soft delete (if supported)
            deleted_by_id: Optional user ID who performed the deletion (for audit)
        """
        if soft and hasattr(entity, "deleted_at"):
            entity.deleted_at = datetime.utcnow()
            if deleted_by_id is not None and hasattr(entity, "deleted_by_id"):
                entity.deleted_by_id = deleted_by_id
            await self.db.commit()
        else:
            await self.db.delete(entity)
            await self.db.commit()

    async def count(self, where=None, include_deleted: bool = False) -> int:
        """
        Count entities matching criteria (with tenant scoping)

        Args:
            where: SQLAlchemy where clause
            include_deleted: Whether to include soft-deleted entities

        Returns:
            Number of matching entities (filtered by tenant if applicable)
        """
        from sqlalchemy import func

        query = select(func.count()).select_from(self.model)

        # Apply tenant filter
        if self.tenant_id is not None and hasattr(self.model, "organization_id"):
            query = query.where(self.model.organization_id == self.tenant_id)

        if not include_deleted and hasattr(self.model, "deleted_at"):
            query = query.where(self.model.deleted_at.is_(None))

        if where is not None:
            query = query.where(where)

        result = await self.db.execute(query)
        return result.scalar() or 0
