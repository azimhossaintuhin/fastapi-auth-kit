from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from authkit.settings import AuthSettings
from authkit.fastapi.routers import build_auth_router_async

from .models import Base, User

DATABASE_URL = "sqlite+aiosqlite:///./examples_async.db"

async_engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
)
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_async_session():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


AUTH_SETTINGS = AuthSettings(
    secret_key="your-secret-key-change-in-production",
    algorithm="HS256",
    access_minutes=15,
    refresh_days=7,
    set_cookie_on_login=True,
    cookie_secure=False,
    cookie_samesite="lax",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await async_engine.dispose()


app = FastAPI(
    title="Authkit Async Example",
    description="Register, login, refresh, logout, and /me using async SQLAlchemy",
    lifespan=lifespan,
)

auth_router = build_auth_router_async(
    settings=AUTH_SETTINGS,
    get_session=get_async_session,
    user_model=User,
)
app.include_router(auth_router, prefix="/auth", tags=["auth"])


@app.get("/")
async def root():
    return {
        "message": "Authkit async example",
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
        "examples.async_app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
