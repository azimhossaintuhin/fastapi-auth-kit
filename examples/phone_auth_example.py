"""
Example: Extending BaseUser for phone number based authentication.

This shows how to:
1. Extend BaseUser with phone_number field
2. Create a custom repository that supports phone lookup
3. Create custom auth service methods
4. Build custom FastAPI routes for phone-based auth
"""
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session
from sqlalchemy import select, or_

from authkit import AuthSettings
from authkit.fastapi.models import BaseUser
from authkit.hashing import hash_password, verify_password
from authkit.tokens import create_access_token, create_refresh_token
from authkit.protocols import SyncUserProtocol, UserProtocol


# ============================================================================
# 1. Extended User Model with Phone Number (using BaseUser)
# ============================================================================
class Base(DeclarativeBase):
    pass


class User(BaseUser, Base):
    """
    User model extending BaseUser.
    All required fields (id, email, username, password_hash, etc.) are inherited.
    We just add phone_number as a custom field.
    """
    __tablename__ = "users"

    # Required fields inherited from BaseUser:
    # id, email, username, password_hash, is_active, is_staff, is_superuser
    
    # Custom field: phone number
    phone_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)


# ============================================================================
# 2. Custom Repository with Phone Support
# ============================================================================
class PhoneAuthRepository(SyncUserProtocol):
    """
    Custom repository that extends the protocol to support phone lookup.
    Still implements the required protocol methods for compatibility.
    """

    def __init__(self, session: Session, user_model: type[User]):
        self.session = session
        self.user_model = user_model

    # Required protocol methods (for compatibility)
    def get_by_id(self, user_id: int) -> UserProtocol | None:
        return self.session.get(self.user_model, user_id)

    def get_by_email_or_username(self, value: str) -> UserProtocol | None:
        stmt = select(self.user_model).where(
            or_(
                self.user_model.email == value,
                self.user_model.username == value,
            )
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def create_user(
        self,
        *,
        email: str,
        username: str,
        password: str,
        is_staff: bool = False,
        is_active: bool = True,
        is_superuser: bool = False,
    ) -> UserProtocol:
        # This won't be used for phone auth, but required by protocol
        raise NotImplementedError("Use create_user_by_phone instead")

    # Custom phone-based methods
    def get_by_phone(self, phone_number: str) -> User | None:
        stmt = select(self.user_model).where(self.user_model.phone_number == phone_number)
        return self.session.execute(stmt).scalar_one_or_none()

    def create_user_by_phone(
        self,
        *,
        phone_number: str,
        password: str,
        email: str | None = None,
        username: str | None = None,
        is_active: bool = True,
        is_staff: bool = False,
        is_superuser: bool = False,
    ) -> User:
        existing = self.get_by_phone(phone_number)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this phone number already exists",
            )
        user = self.user_model(
            phone_number=phone_number,
            email=email or f"{phone_number}@example.com",  # Dummy email
            username=username or phone_number,  # Use phone as username
            password_hash=hash_password(password),
            is_active=is_active,
            is_staff=is_staff,
            is_superuser=is_superuser,
        )
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user


# ============================================================================
# 3. Custom Auth Service for Phone Authentication
# ============================================================================
class PhoneAuthService:
    """
    Custom service for phone-based authentication.
    Uses the standard token utilities from authkit.
    """

    def __init__(self, settings: AuthSettings, repo: PhoneAuthRepository):
        self.settings = settings
        self.repo = repo

    def register_by_phone(self, phone_number: str, password: str) -> User:
        """Register a new user with phone number."""
        return self.repo.create_user_by_phone(
            phone_number=phone_number,
            password=password,
        )

    def authenticate_by_phone(self, phone_number: str, password: str) -> User:
        """Authenticate user by phone number and password."""
        user = self.repo.get_by_phone(phone_number)
        if not user or not verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid phone number or password",
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive",
            )
        return user

    def assign_token(self, user: User) -> tuple[str, str]:
        """Issue JWT tokens (uses authkit's token utilities)."""
        access_token = create_access_token(self.settings, subject=str(user.id))
        refresh_token = create_refresh_token(
            self.settings, subject=str(user.id), jti=__import__("secrets").token_hex(16)
        )
        return access_token, refresh_token


# ============================================================================
# 4. FastAPI App with Phone Auth Routes
# ============================================================================
from pydantic import BaseModel
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./phone_auth.db"
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)

Base.metadata.create_all(engine)

AUTH_SETTINGS = AuthSettings(
    secret_key="your-secret-key-change-in-production",
    algorithm="HS256",
)


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


# Pydantic schemas
class PhoneRegisterSchema(BaseModel):
    phone_number: str
    password: str


class PhoneLoginSchema(BaseModel):
    phone_number: str
    password: str


# FastAPI app
app = FastAPI(title="Phone Auth Example")


@app.post("/auth/register-phone")
def register_phone(
    data: PhoneRegisterSchema,
    session: Session = Depends(get_session),
):
    """Register a new user with phone number."""
    repo = PhoneAuthRepository(session, User)
    service = PhoneAuthService(AUTH_SETTINGS, repo)
    user = service.register_by_phone(data.phone_number, data.password)
    return {
        "id": user.id,
        "phone_number": user.phone_number,
        "is_active": user.is_active,
    }


@app.post("/auth/login-phone")
def login_phone(
    data: PhoneLoginSchema,
    session: Session = Depends(get_session),
):
    """Login with phone number and password."""
    repo = PhoneAuthRepository(session, User)
    service = PhoneAuthService(AUTH_SETTINGS, repo)
    user = service.authenticate_by_phone(data.phone_number, data.password)
    access_token, refresh_token = service.assign_token(user)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": {
            "id": user.id,
            "phone_number": user.phone_number,
        },
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
