"""
Integration tests for authentication endpoints
"""
import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, get_password_hash
from app.models.user import User


@pytest.mark.integration
class TestAuthEndpoints:
    """Integration tests for authentication endpoints"""
    
    async def test_login_success(self, async_client: AsyncClient, test_user: User):
        """Test successful login"""
        response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "testpassword123"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
        assert data["user"]["email"] == test_user.email
        assert data["user"]["full_name"] == "Test User"
    
    async def test_login_invalid_email(self, async_client: AsyncClient):
        """Test login with invalid email"""
        response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "testpassword123"
            }
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "inválidas" in data["detail"].lower() or "invalid" in data["detail"].lower()
    
    async def test_login_invalid_password(self, async_client: AsyncClient, test_user: User):
        """Test login with invalid password"""
        response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "wrongpassword"
            }
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "inválidas" in data["detail"].lower() or "invalid" in data["detail"].lower()
    
    async def test_get_current_user(self, async_client: AsyncClient, test_user: User):
        """Test getting current user info"""
        # Create access token with organization_id (multi-tenant)
        token_data = {
            "sub": str(test_user.id),
            "email": test_user.email,
        }
        if test_user.organization_id:
            token_data["organization_id"] = test_user.organization_id
        token = create_access_token(token_data)
        
        response = await async_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email
        assert data["full_name"] == test_user.full_name
    
    async def test_get_current_user_no_token(self, async_client: AsyncClient):
        """Test getting current user without token"""
        response = await async_client.get("/api/v1/auth/me")
        
        assert response.status_code == 401
    
    async def test_get_current_user_invalid_token(self, async_client: AsyncClient):
        """Test getting current user with invalid token"""
        response = await async_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        
        assert response.status_code == 401

    async def test_update_current_user_profile_persists_extended_fields(
        self,
        async_client: AsyncClient,
        test_user: User,
        db_session: AsyncSession,
    ):
        token_data = {"sub": str(test_user.id), "email": test_user.email}
        if test_user.organization_id:
            token_data["organization_id"] = test_user.organization_id
        token = create_access_token(token_data)

        payload = {
            "full_name": "Nuevo Nombre",
            "job_title": "Product Manager",
            "specialty": "Ventas B2B",
            "bio": "Perfil actualizado",
            "linkedin_url": "https://linkedin.com/in/nuevo",
            "portfolio_url": "https://portfolio.test",
            "instagram_url": "https://instagram.com/nuevo",
            "behance_url": "https://behance.net/nuevo",
            "timezone": "America/Bogota",
            "language": "es",
        }

        response = await async_client.put(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
            json=payload,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == payload["full_name"]
        assert data["job_title"] == payload["job_title"]
        assert data["instagram_url"] == payload["instagram_url"]
        assert data["timezone"] == payload["timezone"]

        await db_session.refresh(test_user)
        assert test_user.full_name == payload["full_name"]
        assert test_user.job_title == payload["job_title"]
        assert test_user.instagram_url == payload["instagram_url"]
        assert test_user.language == payload["language"]

    async def test_change_password_for_authenticated_user(
        self,
        async_client: AsyncClient,
        test_user: User,
    ):
        token_data = {"sub": str(test_user.id), "email": test_user.email}
        if test_user.organization_id:
            token_data["organization_id"] = test_user.organization_id
        token = create_access_token(token_data)

        response = await async_client.post(
            "/api/v1/auth/me/change-password",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "current_password": "testpassword123",
                "new_password": "newpassword123",
            },
        )
        assert response.status_code == 200

        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={"email": test_user.email, "password": "newpassword123"},
        )
        assert login_response.status_code == 200



