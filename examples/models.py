from sqlalchemy.orm import DeclarativeBase

from authkit.fastapi.models import BaseUser


class Base(DeclarativeBase):
    pass


class User(BaseUser, Base):
    __tablename__ = "users"
