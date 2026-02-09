"""Shared pytest fixtures for authkit tests."""
import pytest

from authkit import AuthSettings


@pytest.fixture
def auth_settings() -> AuthSettings:
    return AuthSettings(
        secret_key="test-secret-key-do-not-use-in-production",
        algorithm="HS256",
        access_minutes=15,
        refresh_days=7,
        cookie_name_access="access_token",
        cookie_name_refresh="refresh_token",
        set_cookie_on_login=True,
        cookie_secure=False,
        cookie_samesite="lax",
        accept_header=True,
        accept_cookie=True,
    )
