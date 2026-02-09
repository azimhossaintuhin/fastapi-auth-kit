"""Tests for authkit.extractors."""
import pytest
from fastapi import Request

from authkit.extractors import extract_access_token, extract_refresh_token
from authkit.settings import AuthSettings


def _request_with_headers(headers: dict | None = None) -> Request:
    # ASGI scope header names must be lowercase
    scope = {"type": "http", "headers": [(k.lower().encode(), v.encode()) for k, v in (headers or {}).items()]}
    return Request(scope)


def _request_with_cookies(cookies: dict | None = None) -> Request:
    scope = {"type": "http", "headers": []}
    if cookies:
        scope["headers"] = [(b"cookie", ("; ".join(f"{k}={v}" for k, v in cookies.items())).encode())]
    else:
        scope["headers"] = []
    return Request(scope)


@pytest.fixture
def settings() -> AuthSettings:
    return AuthSettings(
        secret_key="x",
        accept_header=True,
        accept_cookie=True,
        cookie_name_access="access_token",
        cookie_name_refresh="refresh_token",
    )


def test_extract_access_token_from_bearer_header(settings: AuthSettings):
    req = _request_with_headers({"Authorization": "Bearer my.access.token"})
    assert extract_access_token(req, settings) == "my.access.token"


def test_extract_access_token_returns_none_without_bearer(settings: AuthSettings):
    req = _request_with_headers({"Authorization": "Basic xyz"})
    assert extract_access_token(req, settings) is None


def test_extract_access_token_returns_none_without_auth_header(settings: AuthSettings):
    req = _request_with_headers({})
    assert extract_access_token(req, settings) is None


def test_extract_access_token_from_cookie(settings: AuthSettings):
    req = _request_with_cookies({"access_token": "cookie-access"})
    assert extract_access_token(req, settings) == "cookie-access"


def test_extract_refresh_token_from_bearer_header(settings: AuthSettings):
    req = _request_with_headers({"Authorization": "Bearer my.refresh.token"})
    assert extract_refresh_token(req, settings) == "my.refresh.token"


def test_extract_refresh_token_from_cookie(settings: AuthSettings):
    req = _request_with_cookies({"refresh_token": "cookie-refresh"})
    assert extract_refresh_token(req, settings) == "cookie-refresh"


def test_extract_access_token_header_disabled(settings: AuthSettings):
    settings = AuthSettings(secret_key="x", accept_header=False, accept_cookie=True)
    req = _request_with_headers({"Authorization": "Bearer tok"})
    assert extract_access_token(req, settings) is None
