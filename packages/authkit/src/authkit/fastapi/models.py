"""
Base User model that can be extended by users.

Example:
    from authkit.fastapi.models import BaseUser
    from sqlalchemy.orm import DeclarativeBase, Mapped
    from sqlalchemy import String
    
    class Base(DeclarativeBase):
        pass
    
    class User(BaseUser, Base):
        __tablename__ = "users"
        
        # Required fields are inherited from BaseUser
        # Add your custom fields:
        phone_number: Mapped[str] = mapped_column(String(20), nullable=True)
"""
from sqlalchemy import String, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column


class BaseUser:
    """
    Base User model mixin with required authkit fields.
    
    Inherit from this class along with your DeclarativeBase to create your User model:
    
    ```python
    from authkit.fastapi.models import BaseUser
    from sqlalchemy.orm import DeclarativeBase, Mapped
    from sqlalchemy import String
    
    class Base(DeclarativeBase):
        pass
    
    class User(BaseUser, Base):
        __tablename__ = "users"
        
        # Required fields are already defined in BaseUser
        # Add your custom fields here:
        phone_number: Mapped[str] = mapped_column(String(20), nullable=True)
        avatar_url: Mapped[str] = mapped_column(String(255), nullable=True)
    ```
    """
    __abstract__ = True
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    username: Mapped[str] = mapped_column(String(150), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_staff: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
