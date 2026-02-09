from typing import Any, Type
from sqlalchemy.orm import Session
from sqlalchemy import select, or_


class SQLAlchemySyncUserProtocol:
    """
    Adapter repository for SQLAlchemy Session (sync).
    """

    def __init__(self, session: Session, user_model: Type[Any]):
        self.session = session
        self.user_model = user_model

    def get_by_id(self, user_id: int):
        return self.session.get(self.user_model, user_id)

    def get_by_email_or_username(self, value: str):
        stmt = select(self.user_model).where(
            or_(
                self.user_model.email == value,
                self.user_model.username == value,
            )
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def get_by_email(self, email: str):
        stmt = select(self.user_model).where(
            self.user_model.email == email
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def get_by_username(self, username: str):
        stmt = select(self.user_model).where(
            self.user_model.username == username
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def create_user(
        self,
        *,
        email: str,
        username: str,
        password: str,
        is_active: bool = True,
        is_staff: bool = False,
        is_superuser: bool = False,
    ):
        user = self.user_model(
            email=email,
            username=username,
            password_hash=password,
            is_active=is_active,
            is_staff=is_staff,
            is_superuser=is_superuser,
        )
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user
