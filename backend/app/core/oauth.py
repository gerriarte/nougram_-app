"""
Google OAuth utilities
"""

import httpx

from app.core.config import settings


async def exchange_google_code_for_tokens(code: str, redirect_uri: str = None) -> dict | None:
    """
    Exchange Google OAuth code for access and refresh tokens

    Args:
        code: Authorization code from Google OAuth

    Returns:
        Dict with access_token, refresh_token, expires_in, and user info
    """
    try:
        token_url = "https://oauth2.googleapis.com/token"

        if redirect_uri is None:
            redirect_uri = "http://localhost:3000/auth/callback"  # Default frontend redirect URI

        data = {
            "code": code,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(token_url, data=data)

            if response.status_code != 200:
                return None

            token_data = response.json()

            # Get user info
            user_info = await get_google_user_info(token_data["access_token"])

            if not user_info:
                return None

            return {
                "access_token": token_data["access_token"],
                "refresh_token": token_data.get("refresh_token"),
                "expires_in": token_data.get("expires_in", 3600),
                "user_info": user_info,
            }

    except Exception as e:
        print(f"Error exchanging Google code: {e}")
        return None


async def get_google_user_info(access_token: str) -> dict | None:
    """
    Get user information from Google using access token

    Args:
        access_token: Google access token

    Returns:
        Dict with user info (email, name, etc.)
    """
    try:
        user_info_url = "https://www.googleapis.com/oauth2/v2/userinfo"

        headers = {"Authorization": f"Bearer {access_token}"}

        async with httpx.AsyncClient() as client:
            response = await client.get(user_info_url, headers=headers)

            if response.status_code != 200:
                return None

            return response.json()

    except Exception as e:
        print(f"Error getting Google user info: {e}")
        return None


async def refresh_google_token(refresh_token: str) -> dict | None:
    """
    Refresh Google access token using refresh token

    Args:
        refresh_token: Google refresh token

    Returns:
        Dict with new access_token and expires_in
    """
    try:
        token_url = "https://oauth2.googleapis.com/token"

        data = {
            "refresh_token": refresh_token,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "grant_type": "refresh_token",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(token_url, data=data)

            if response.status_code != 200:
                return None

            token_data = response.json()

            return {
                "access_token": token_data["access_token"],
                "expires_in": token_data.get("expires_in", 3600),
            }

    except Exception as e:
        print(f"Error refreshing Google token: {e}")
        return None


def get_google_oauth_url(include_calendar: bool = False) -> str:
    """
    Generate Google OAuth authorization URL

    Args:
        include_calendar: If True, includes calendar scope

    Returns:
        Google OAuth URL
    """
    redirect_uri = "http://localhost:3000/auth/callback"
    scope = "openid email profile"

    if include_calendar:
        scope += " https://www.googleapis.com/auth/calendar.readonly"

    url = (
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={settings.GOOGLE_CLIENT_ID}&"
        f"redirect_uri={redirect_uri}&"
        f"response_type=code&"
        f"scope={scope}&"
        f"access_type=offline&"
        f"prompt=consent"
    )

    return url
