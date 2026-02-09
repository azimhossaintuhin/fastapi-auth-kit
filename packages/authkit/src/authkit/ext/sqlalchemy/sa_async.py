from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

class SQLAlchemyAsyncUserProtocol:
    """
    Adapter repo for SQLAlchemy AsyncSession.
    You pass your User model class in user_model.
    """
    def __init__(self, session: AsyncSession, user_model: type[Any]):
        self.session = session
        self.user_model = user_model

    async def get_by_id(self, user_id: int):
        return await self.session.get(self.user_model, user_id)

    async def get_by_email_or_username(self, value: str):
        user_model = self.user_model
        stmt = select(user_model).where(or_(user_model.email == value, user_model.username == value))
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def create_user(
        self,
        *,
        email: str,
        username: str,
        password: str,
        is_active: bool = True,
        is_staff: bool = False,
        is_superuser: bool = False,
    ):
        user_model = self.user_model
        user = user_model(
            email=email,
            username=username,
            password_hash=password,
            is_active=is_active,
            is_staff=is_staff,
            is_superuser=is_superuser,
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user
