"""Tests for authkit.service.AuthService (sync)."""
import pytest
from fastapi import HTTPException

from authkit import AuthSettings
from authkit.service import AuthService
from authkit.hashing import hash_password


class MockUser:
    def __init__(self, id: int, email: str, username: str, password_hash: str, is_active: bool = True, is_staff: bool = False, is_superuser: bool = False):
        self.id = id
        self.email = email
        self.username = username
        self.password_hash = password_hash
        self.is_active = is_active
        self.is_staff = is_staff
        self.is_superuser = is_superuser


class MockSyncRepo:
    def __init__(self):
        self.users: list[MockUser] = []
        self._id = 1

    def get_by_id(self, user_id: int) -> MockUser | None:
        for u in self.users:
            if u.id == user_id:
                return u
        return None

    def get_by_email_or_username(self, value: str) -> MockUser | None:
        for u in self.users:
            if u.email == value or u.username == value:
                return u
        return None

    def create_user(
        self,
        *,
        email: str,
        username: str,
        password: str,
        is_active: bool = True,
        is_staff: bool = False,
        is_superuser: bool = False,
    ) -> MockUser:
        u = MockUser(
            id=self._id,
            email=email,
            username=username,
            password_hash=password,
            is_active=is_active,
            is_staff=is_staff,
            is_superuser=is_superuser,
        )
        self._id += 1
        self.users.append(u)
        return u


@pytest.fixture
def settings() -> AuthSettings:
    return AuthSettings(secret_key="test-secret", algorithm="HS256")


@pytest.fixture
def repo() -> MockSyncRepo:
    return MockSyncRepo()


@pytest.fixture
def service(settings: AuthSettings, repo: MockSyncRepo) -> AuthService:
    return AuthService(settings, repo)


def test_create_user_returns_user(service: AuthService):
    user = service.create_user("a@b.com", "alice", "pass123")
    assert user.email == "a@b.com"
    assert user.username == "alice"
    assert user.password_hash  # hashed
    assert user.id >= 1


def test_create_user_duplicate_email_raises(service: AuthService, repo: MockSyncRepo):
    service.create_user("same@x.com", "user1", "pass")
    with pytest.raises(HTTPException) as exc_info:
        service.create_user("same@x.com", "user2", "pass")
    assert exc_info.value.status_code == 400


def test_create_user_duplicate_username_raises(service: AuthService):
    service.create_user("a@x.com", "alice", "pass")
    with pytest.raises(HTTPException) as exc_info:
        service.create_user("b@x.com", "alice", "pass")
    assert exc_info.value.status_code == 400


def test_authenticate_success(service: AuthService):
    service.create_user("u@x.com", "bob", "secret")
    user = service.authenticate("bob", "secret")
    assert user.username == "bob"
    assert user.email == "u@x.com"


def test_authenticate_by_email(service: AuthService):
    service.create_user("u@x.com", "bob", "secret")
    user = service.authenticate("u@x.com", "secret")
    assert user.email == "u@x.com"


def test_authenticate_wrong_password_raises(service: AuthService):
    service.create_user("u@x.com", "bob", "secret")
    with pytest.raises(HTTPException) as exc_info:
        service.authenticate("bob", "wrong")
    assert exc_info.value.status_code == 401


def test_authenticate_unknown_user_raises(service: AuthService):
    with pytest.raises(HTTPException) as exc_info:
        service.authenticate("nobody", "pass")
    assert exc_info.value.status_code == 401


def test_assign_token_returns_two_tokens(service: AuthService):
    user = service.create_user("u@x.com", "bob", "pass")
    access, refresh = service.assign_token(user)
    assert isinstance(access, str)
    assert isinstance(refresh, str)
    assert access != refresh


def test_refresh_pair_returns_new_tokens(service: AuthService):
    user = service.create_user("u@x.com", "bob", "pass")
    _, refresh = service.assign_token(user)
    access2, refresh2 = service.refresh_pair(refresh)
    assert isinstance(access2, str)
    assert isinstance(refresh2, str)
    assert access2
    assert refresh2
