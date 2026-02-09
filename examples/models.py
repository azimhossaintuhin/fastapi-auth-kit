"""
Shared SQLAlchemy User model for authkit examples.
Shows how to extend BaseUser with custom fields.

Example of extending BaseUser:
    from authkit.fastapi.models import BaseUser
    from sqlalchemy.orm import DeclarativeBase, Mapped
    from sqlalchemy import String
    
    class Base(DeclarativeBase):
        pass
    
    class User(BaseUser, Base):
        __tablename__ = "users"
        # Add custom fields:
        phone_number: Mapped[str] = mapped_column(String(20), nullable=True)
"""
from sqlalchemy.orm import DeclarativeBase

from authkit.fastapi.models import BaseUser


class Base(DeclarativeBase):
    pass


class User(BaseUser, Base):
   
    __tablename__ = "users"
    
    # Required fields are inherited from BaseUser:
    # - id, email, username, password_hash
    # - is_active, is_staff, is_superuser
    
    # Add your custom fields here if needed:
    # phone_number: Mapped[str] = mapped_column(String(20), nullable=True)
