"""Integration tests for authkit FastAPI sync auth router."""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, String, Boolean, Integer
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Mapped, mapped_column
from sqlalchemy.pool import StaticPool

from authkit import AuthSettings
from authkit.fastapi.routers import build_auth_router_sync


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
def sync_app(auth_settings: AuthSettings):
    engine = create_engine(
        "sqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def get_session():
        session = SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    app = FastAPI()
    router = build_auth_router_sync(
        settings=auth_settings,
        get_session=get_session,
        user_models=User,
    )
    app.include_router(router, prefix="/auth", tags=["auth"])
    return app


@pytest.fixture
def client(sync_app: FastAPI) -> TestClient:
    return TestClient(sync_app)


def test_register_returns_user(client: TestClient):
    r = client.post(
        "/auth/register",
        json={"email": "a@b.com", "username": "alice", "password": "secret123"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["email"] == "a@b.com"
    assert data["username"] == "alice"
    assert "id" in data


def test_login_returns_tokens(client: TestClient):
    client.post(
        "/auth/register",
        json={"email": "u@x.com", "username": "bob", "password": "mypass"},
    )
    r = client.post(
        "/auth/login",
        json={"username_or_email": "bob", "password": "mypass"},
    )
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    assert "refresh_token" in data


def test_me_requires_auth(client: TestClient):
    r = client.get("/auth/me")
    assert r.status_code == 401


def test_me_returns_user_when_authenticated(client: TestClient):
    client.post(
        "/auth/register",
        json={"email": "me@x.com", "username": "me", "password": "pass"},
    )
    login = client.post(
        "/auth/login",
        json={"username_or_email": "me", "password": "pass"},
    )
    token = login.json()["access_token"]
    r = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["username"] == "me"
    assert r.json()["email"] == "me@x.com"


def test_refresh_returns_new_tokens(client: TestClient):
    client.post(
        "/auth/register",
        json={"email": "r@x.com", "username": "ref", "password": "p"},
    )
    login = client.post(
        "/auth/login",
        json={"username_or_email": "ref", "password": "p"},
    )
    refresh_token = login.json()["refresh_token"]
    r = client.post(
        "/auth/refresh",
        headers={"Authorization": f"Bearer {refresh_token}"},
    )
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    assert "refresh_token" in data


def test_logout_returns_ok(client: TestClient):
    r = client.post("/auth/logout")
    assert r.status_code == 200
    assert r.json().get("ok") is True
