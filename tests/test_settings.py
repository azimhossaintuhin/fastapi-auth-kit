"""Tests for authkit.settings."""
import pytest

from authkit import AuthSettings


def test_auth_settings_defaults():
    s = AuthSettings(secret_key="key")
    assert s.secret_key == "key"
    assert s.algorithm == "HS256"
    assert s.access_minutes == 15
    assert s.refresh_days == 7
    assert s.cookie_name_access == "access_token"
    assert s.cookie_name_refresh == "refresh_token"
    assert s.accept_header is True
    assert s.accept_cookie is True
    assert s.set_cookie_on_login is True
    assert s.cookie_samesite == "lax"


def test_auth_settings_frozen():
    s = AuthSettings(secret_key="x")
    with pytest.raises(Exception):
        s.secret_key = "y"
