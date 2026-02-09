"""Tests for authkit.hashing."""
import pytest

from authkit.hashing import hash_password, verify_password


def test_hash_password_returns_non_empty_string():
    result = hash_password("mypassword")
    assert isinstance(result, str)
    assert len(result) > 0
    assert result != "mypassword"


def test_hash_password_different_each_time():
    a = hash_password("same")
    b = hash_password("same")
    assert a != b  # bcrypt uses salt


def test_verify_password_accepts_correct_password():
    hashed = hash_password("secret123")
    assert verify_password("secret123", hashed) is True


def test_verify_password_rejects_wrong_password():
    hashed = hash_password("secret123")
    assert verify_password("wrong", hashed) is False


def test_verify_password_rejects_empty_after_hash():
    hashed = hash_password("x")
    assert verify_password("", hashed) is False
