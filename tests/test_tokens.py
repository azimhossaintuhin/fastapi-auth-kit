"""Tests for authkit.tokens."""
import pytest
from fastapi import HTTPException

from authkit.tokens import (
    create_access_token,
    create_refresh_token,
    decode_access,
    decode_refresh,
)
from authkit.settings import AuthSettings


@pytest.fixture
def settings() -> AuthSettings:
    return AuthSettings(
        secret_key="test-secret",
        algorithm="HS256",
        access_minutes=15,
        refresh_days=7,
    )


def test_create_access_token_returns_string(settings: AuthSettings):
    token = create_access_token(settings, subject="42")
    assert isinstance(token, str)
    assert len(token) > 0


def test_create_refresh_token_returns_string(settings: AuthSettings):
    token = create_refresh_token(settings, subject="42", jti="abc123")
    assert isinstance(token, str)
    assert len(token) > 0


def test_decode_access_returns_payload_with_sub_and_type(settings: AuthSettings):
    token = create_access_token(settings, subject="user-1")
    payload = decode_access(settings, token)
    assert payload["sub"] == "user-1"
    assert payload["type"] == "access"
    assert "iat" in payload
    assert "exp" in payload


def test_decode_access_raises_on_refresh_token(settings: AuthSettings):
    token = create_refresh_token(settings, subject="user-1", jti="jti")
    with pytest.raises(HTTPException) as exc_info:
        decode_access(settings, token)
    assert exc_info.value.status_code == 401


def test_decode_access_raises_on_invalid_token(settings: AuthSettings):
    with pytest.raises(HTTPException) as exc_info:
        decode_access(settings, "invalid.jwt.token")
    assert exc_info.value.status_code == 401


def test_decode_refresh_returns_payload_with_sub_and_type(settings: AuthSettings):
    token = create_refresh_token(settings, subject="99", jti="jti-xyz")
    payload = decode_refresh(settings, token)
    assert payload["sub"] == "99"
    assert payload["type"] == "refresh"
    assert payload.get("jti") == "jti-xyz"
    assert "iat" in payload
    assert "exp" in payload


def test_decode_refresh_raises_on_access_token(settings: AuthSettings):
    token = create_access_token(settings, subject="user-1")
    with pytest.raises(HTTPException) as exc_info:
        decode_refresh(settings, token)
    assert exc_info.value.status_code == 401


def test_decode_refresh_raises_on_invalid_token(settings: AuthSettings):
    with pytest.raises(HTTPException) as exc_info:
        decode_refresh(settings, "bad-token")
    assert exc_info.value.status_code == 401


def test_decode_raises_on_wrong_secret(settings: AuthSettings):
    token = create_access_token(settings, subject="1")
    other = AuthSettings(secret_key="other-secret", algorithm="HS256")
    with pytest.raises(HTTPException):
        decode_access(other, token)
