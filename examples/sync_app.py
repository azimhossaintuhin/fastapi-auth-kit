"""
Sync FastAPI example using authkit with SQLAlchemy sync Session.

Run:
  uv run python -m examples.sync_app
  # or: uvicorn examples.sync_app:app --reload --port 8001
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from authkit import AuthSettings
from authkit.fastapi.routers import build_auth_router_sync

from .models import Base, User

# ---------------------------------------------------------------------------
# Database (sync)
# ---------------------------------------------------------------------------
DATABASE_URL = "sqlite:///./examples_sync.db"

engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_sync_session():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Auth settings
# ---------------------------------------------------------------------------
AUTH_SETTINGS = AuthSettings(
    secret_key="your-secret-key-change-in-production",
    algorithm="HS256",
    access_minutes=15,
    refresh_days=7,
    set_cookie_on_login=True,
    cookie_secure=False,  # True in production with HTTPS
    cookie_samesite="lax",
)


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield
    engine.dispose()


app = FastAPI(
    title="Authkit Sync Example",
    description="Register, login, refresh, logout, and /me using sync SQLAlchemy",
    lifespan=lifespan,
)

auth_router = build_auth_router_sync(
    settings=AUTH_SETTINGS,
    get_session=get_sync_session,
    user_model=User
)
app.include_router(auth_router, prefix="/auth", tags=["auth"])


@app.get("/")
def root():
    return {
        "message": "Authkit sync example",
        "docs": "/docs",
        "auth": {
            "register": "POST /auth/register",
            "login": "POST /auth/login",
            "refresh": "POST /auth/refresh",
            "logout": "POST /auth/logout",
            "me": "GET /auth/me",
        },
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "examples.sync_app:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
    )