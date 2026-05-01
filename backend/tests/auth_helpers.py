"""JWT helpers for integration tests."""

from app.core.security import create_access_token
from app.models.user import User


def get_auth_headers(user: User) -> dict:
    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "name": user.full_name,
        "organization_id": user.organization_id,
        "role": user.role,
        "role_type": user.role_type or ("support" if user.role == "super_admin" else "tenant"),
    }
    token = create_access_token(token_data)
    return {"Authorization": f"Bearer {token}"}
