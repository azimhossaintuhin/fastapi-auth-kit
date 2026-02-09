from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session
from sqlalchemy import select, or_

from authkit.settings import AuthSettings
from authkit.fastapi.models import BaseUser
from authkit.hashing import hash_password, verify_password
from authkit.tokens import create_access_token, create_refresh_token
from authkit.protocols import SyncUserProtocol, UserProtocol


class Base(DeclarativeBase):
    pass


class User(BaseUser, Base):
    __tablename__ = "users"
    phone_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)


class PhoneAuthRepository(SyncUserProtocol):
    def __init__(self, session: Session, user_model: type[User]):
        self.session = session
        self.user_model = user_model

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
        raise NotImplementedError("Use create_user_by_phone instead")

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
            email=email or f"{phone_number}@example.com",
            username=username or phone_number,
            password_hash=hash_password(password),
            is_active=is_active,
            is_staff=is_staff,
            is_superuser=is_superuser,
        )
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user


class PhoneAuthService:
    def __init__(self, settings: AuthSettings, repo: PhoneAuthRepository):
        self.settings = settings
        self.repo = repo

    def register_by_phone(self, phone_number: str, password: str) -> User:
        return self.repo.create_user_by_phone(
            phone_number=phone_number,
            password=password,
        )

    def authenticate_by_phone(self, phone_number: str, password: str) -> User:
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
        access_token = create_access_token(self.settings, subject=str(user.id))
        refresh_token = create_refresh_token(
            self.settings, subject=str(user.id), jti=__import__("secrets").token_hex(16)
        )
        return access_token, refresh_token


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


class PhoneRegisterSchema(BaseModel):
    phone_number: str
    password: str


class PhoneLoginSchema(BaseModel):
    phone_number: str
    password: str


app = FastAPI(title="Phone Auth Example")


@app.post("/auth/register-phone")
def register_phone(
    data: PhoneRegisterSchema,
    session: Session = Depends(get_session),
):
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
