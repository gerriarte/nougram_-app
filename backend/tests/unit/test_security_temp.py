"""
Unit tests for security functions
"""

import pytest

from app.core.security import (
    create_access_token,
    decode_access_token,
    get_password_hash,
    verify_password,
)


@pytest.mark.unit
class TestPasswordHashing:
    """Tests for password hashing and verification"""

    def test_hash_password(self):
        """Test password hashing"""
        password = "testpass123"  # Shorter password to avoid bcrypt 72 byte limit
        hashed = get_password_hash(password)

        assert hashed != password
        assert len(hashed) > 0
        assert isinstance(hashed, str)

    def test_verify_password_correct(self):
        """Test password verification with correct password"""
        password = "testpass123"  # Shorter password
        hashed = get_password_hash(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password"""
        password = "testpass123"  # Shorter password
        wrong_password = "wrongpass"
        hashed = get_password_hash(password)

        assert verify_password(wrong_password, hashed) is False

    def test_hash_different_passwords_different_hashes(self):
        """Test that different passwords produce different hashes"""
        password1 = "pass1"
        password2 = "pass2"

        hash1 = get_password_hash(password1)
        hash2 = get_password_hash(password2)

        assert hash1 != hash2


@pytest.mark.unit
class TestJWT:
    """Tests for JWT token creation and decoding"""

    def test_create_access_token(self):
        """Test creating an access token"""
        data = {"sub": "1", "email": "test@example.com"}
        token = create_access_token(data)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_decode_access_token(self):
        """Test decoding a valid access token"""
        data = {"sub": "1", "email": "test@example.com"}
        token = create_access_token(data)

        decoded = decode_access_token(token)

        assert decoded is not None
        assert decoded["sub"] == "1"
        assert decoded["email"] == "test@example.com"
        assert "exp" in decoded

    def test_decode_invalid_token(self):
        """Test decoding an invalid token"""
        invalid_token = "invalid.token.here"
        decoded = decode_access_token(invalid_token)

        assert decoded is None
