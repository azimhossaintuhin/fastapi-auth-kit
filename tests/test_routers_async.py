"""Integration tests for authkit FastAPI async auth router."""
import pytest
from fastapi import FastAPI, Depends
from httpx import ASGITransport, AsyncClient
from sqlalchemy import String, Boolean, Integer
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from authkit import AuthSettings
from authkit.fastapi.routers import build_auth_router_async


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    username: Mapped[str] = mapped_column(String(150), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_staff: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


@pytest.fixture
def auth_settings() -> AuthSettings:
    return AuthSettings(
        secret_key="test-secret",
        algorithm="HS256",
        set_cookie_on_login=False,
        cookie_secure=False,
    )


@pytest.fixture
async def async_app(auth_settings: AuthSettings):
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    SessionLocal = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False, autocommit=False, autoflush=False
    )

    async def get_session():
        async with SessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    app = FastAPI()
    router = build_auth_router_async(
        settings=auth_settings,
        get_session=get_session,
        user_model=User,
    )
    app.include_router(router, prefix="/auth", tags=["auth"])
    yield app
    await engine.dispose()


@pytest.fixture
async def client(async_app: FastAPI):
    transport = ASGITransport(app=async_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_register_returns_user(client: AsyncClient):
    r = await client.post(
        "/auth/register",
        json={"email": "a@b.com", "username": "alice", "password": "secret123"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["email"] == "a@b.com"
    assert data["username"] == "alice"
    assert "id" in data
    assert "password" not in data


@pytest.mark.asyncio
async def test_login_returns_tokens(client: AsyncClient):
    await client.post(
        "/auth/register",
        json={"email": "u@x.com", "username": "bob", "password": "mypass"},
    )
    r = await client.post(
        "/auth/login",
        json={"username_or_email": "bob", "password": "mypass"},
    )
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_me_requires_auth(client: AsyncClient):
    r = await client.get("/auth/me")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_me_returns_user_when_authenticated(client: AsyncClient):
    await client.post(
        "/auth/register",
        json={"email": "me@x.com", "username": "me", "password": "pass"},
    )
    login = await client.post(
        "/auth/login",
        json={"username_or_email": "me", "password": "pass"},
    )
    token = login.json()["access_token"]
    r = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["username"] == "me"
    assert r.json()["email"] == "me@x.com"


@pytest.mark.asyncio
async def test_refresh_returns_new_tokens(client: AsyncClient):
    await client.post(
        "/auth/register",
        json={"email": "r@x.com", "username": "ref", "password": "p"},
    )
    login = await client.post(
        "/auth/login",
        json={"username_or_email": "ref", "password": "p"},
    )
    refresh_token = login.json()["refresh_token"]
    r = await client.post(
        "/auth/refresh",
        headers={"Authorization": f"Bearer {refresh_token}"},
    )
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_logout_returns_ok(client: AsyncClient):
    r = await client.post("/auth/logout")
    assert r.status_code == 200
    assert r.json().get("ok") is True
