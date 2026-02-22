"""
Integration tests for quote calculation endpoints
"""
import pytest
from httpx import AsyncClient
from decimal import Decimal
from app.core.security import create_access_token
from app.models.user import User


@pytest.mark.integration
class TestQuoteEndpoints:
    """Integration tests for quote calculation endpoints"""
    
    async def test_calculate_quote_success(
        self, 
        async_client: AsyncClient, 
        test_user: User,
        test_service,
        test_settings,
        test_team_member
    ):
        """Test successful quote calculation"""
        token = create_access_token({"sub": str(test_user.id), "email": test_user.email})
        
        response = await async_client.post(
            "/api/v1/quotes/calculate",
            json={
                "items": [
                    {
                        "service_id": test_service.id,
                        "estimated_hours": 10.0
                    }
                ],
                "tax_ids": []
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "total_internal_cost" in data
        assert "total_client_price" in data
        assert "margin_percentage" in data
        assert "items" in data
        assert len(data["items"]) == 1
        assert data["items"][0]["service_id"] == test_service.id
        # Enhanced quote endpoint does not include estimated_hours in item breakdown.
        assert "internal_cost" in data["items"][0]
        assert "client_price" in data["items"][0]
        assert Decimal(str(data["total_internal_cost"])) > 0
        assert Decimal(str(data["total_client_price"])) > 0
        assert Decimal(str(data["margin_percentage"])) > 0
    
    async def test_calculate_quote_invalid_service(
        self,
        async_client: AsyncClient,
        test_user: User
    ):
        """Test quote calculation with invalid service"""
        token = create_access_token({"sub": str(test_user.id), "email": test_user.email})
        
        response = await async_client.post(
            "/api/v1/quotes/calculate",
            json={
                "items": [
                    {
                        "service_id": 99999,
                        "estimated_hours": 10.0
                    }
                ],
                "tax_ids": []
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower() or "inactive" in data["detail"].lower()
    
    async def test_calculate_quote_no_auth(self, async_client: AsyncClient, test_service):
        """Test quote calculation without authentication"""
        response = await async_client.post(
            "/api/v1/quotes/calculate",
            json={
                "items": [
                    {
                        "service_id": test_service.id,
                        "estimated_hours": 10.0
                    }
                ],
                "tax_ids": []
            }
        )
        
        assert response.status_code == 401















