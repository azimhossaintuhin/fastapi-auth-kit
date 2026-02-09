"""Tests for authkit.service.AsyncAuthService."""
import pytest
from fastapi import HTTPException

from authkit import AuthSettings
from authkit.service import AsyncAuthService
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


class MockAsyncRepo:
    def __init__(self):
        self.users: list[MockUser] = []
        self._id = 1

    async def get_by_id(self, user_id: int) -> MockUser | None:
        for u in self.users:
            if u.id == user_id:
                return u
        return None

    async def get_by_email_or_username(self, value: str) -> MockUser | None:
        for u in self.users:
            if u.email == value or u.username == value:
                return u
        return None

    async def create_user(
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
def repo() -> MockAsyncRepo:
    return MockAsyncRepo()


@pytest.fixture
def service(settings: AuthSettings, repo: MockAsyncRepo) -> AsyncAuthService:
    return AsyncAuthService(settings, repo)


@pytest.mark.asyncio
async def test_create_user_returns_user(service: AsyncAuthService):
    user = await service.create_user("a@b.com", "alice", "pass123")
    assert user.email == "a@b.com"
    assert user.username == "alice"
    assert user.password_hash
    assert user.id >= 1


@pytest.mark.asyncio
async def test_create_user_duplicate_email_raises(service: AsyncAuthService):
    await service.create_user("same@x.com", "user1", "pass")
    with pytest.raises(HTTPException) as exc_info:
        await service.create_user("same@x.com", "user2", "pass")
    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_authenticate_success(service: AsyncAuthService):
    await service.create_user("u@x.com", "bob", "secret")
    user = await service.authenticate("bob", "secret")
    assert user.username == "bob"


@pytest.mark.asyncio
async def test_authenticate_wrong_password_raises(service: AsyncAuthService):
    await service.create_user("u@x.com", "bob", "secret")
    with pytest.raises(HTTPException) as exc_info:
        await service.authenticate("bob", "wrong")
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_assign_token_returns_two_tokens(service: AsyncAuthService):
    user = await service.create_user("u@x.com", "bob", "pass")
    access, refresh = await service.assign_token(user)
    assert isinstance(access, str)
    assert isinstance(refresh, str)


@pytest.mark.asyncio
async def test_refresh_pair_returns_new_tokens(service: AsyncAuthService):
    user = await service.create_user("u@x.com", "bob", "pass")
    _, refresh = await service.assign_token(user)
    access2, refresh2 = await service.refresh_pair(refresh)
    assert isinstance(access2, str)
    assert isinstance(refresh2, str)
