"""
Integration tests for soft delete functionality
"""

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.cost import CostFixed
from app.models.service import Service
from app.models.user import User


@pytest.mark.integration
class TestSoftDelete:
    """Integration tests for soft delete functionality"""

    async def test_soft_delete_service(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        test_admin_user: User,
        test_service: Service,
    ):
        """Test soft delete of a service"""
        token = create_access_token(
            {"sub": str(test_admin_user.id), "email": test_admin_user.email}
        )

        # Delete service
        response = await async_client.delete(
            f"/api/v1/services/{test_service.id}", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200

        # Verify it's soft deleted (not in normal query)
        result = await db_session.execute(
            select(Service).where(Service.id == test_service.id, Service.deleted_at.is_(None))
        )
        deleted_service = result.scalar_one_or_none()
        assert deleted_service is None

        # Verify it's still in database with deleted_at set
        result = await db_session.execute(select(Service).where(Service.id == test_service.id))
        service_with_deleted = result.scalar_one_or_none()
        assert service_with_deleted is not None
        assert service_with_deleted.deleted_at is not None

    async def test_list_services_excludes_deleted(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
        test_service: Service,
    ):
        """Test that listing services excludes soft-deleted ones"""
        token = create_access_token({"sub": str(test_user.id), "email": test_user.email})

        # Soft delete the service
        from datetime import datetime

        test_service.deleted_at = datetime.utcnow()
        await db_session.commit()

        # List services
        response = await async_client.get(
            "/api/v1/services/", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        # The deleted service should not appear in the list
        service_ids = [s["id"] for s in data.get("items", [])]
        assert test_service.id not in service_ids

    async def test_soft_delete_cost(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        test_admin_user: User,
        test_cost: CostFixed,
    ):
        """Test soft delete of a cost"""
        token = create_access_token(
            {"sub": str(test_admin_user.id), "email": test_admin_user.email}
        )

        # Delete cost
        response = await async_client.delete(
            f"/api/v1/costs/fixed/{test_cost.id}", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200

        # Verify it's soft deleted
        result = await db_session.execute(
            select(CostFixed).where(CostFixed.id == test_cost.id, CostFixed.deleted_at.is_(None))
        )
        deleted_cost = result.scalar_one_or_none()
        assert deleted_cost is None

        # Verify it's still in database
        result = await db_session.execute(select(CostFixed).where(CostFixed.id == test_cost.id))
        cost_with_deleted = result.scalar_one_or_none()
        assert cost_with_deleted is not None
        assert cost_with_deleted.deleted_at is not None
