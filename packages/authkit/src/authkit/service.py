from  __future__ import annotations

import secrets
from fastapi import HTTPException , status

from .hashing import  hash_password , verify_password
from .settings import AuthSettings

from .tokens  import (
create_access_token,
create_refresh_token,
decode_refresh
)
from .protocols import  AsyncUserProtocol , SyncUserProtocol , UserProtocol


class AsyncAuthService:
    def __init__(self,settings:AuthSettings,repo:AsyncUserProtocol):
        self.settings = settings
        self.repo = repo

    async def create_user(self, email:str, username:str, password:str) -> UserProtocol:
        existing_user = await self.repo.get_by_email_or_username(email) or await self.repo.get_by_email_or_username(username)
        if existing_user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User with this email or username already exists")
        return await self.repo.create_user(
            email=email,
            username=username,
            password=hash_password(password),
            is_active=True,
            is_staff=False,
            is_superuser=False,
        )

    async def create_superuser(self, email:str, username:str, password:str) -> UserProtocol:
        existing_user = await self.repo.get_by_email_or_username(email) or await self.repo.get_by_email_or_username(username)
        if existing_user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User with this email or username already exists")
        return await self.repo.create_user(
            email=email,
            username=username,
            password=hash_password(password),
            is_active=True,
            is_staff=True,
            is_superuser=True,
        )


    async def authenticate(self , user_name_or_email:str, password:str) -> UserProtocol:
        user = await self.repo.get_by_email_or_username(user_name_or_email)
        if not user or not verify_password(password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        return user


    async  def assign_token(self , user:UserProtocol) -> tuple[str, str]:
        access_token = create_access_token(self.settings , subject=str(user.id))
        refresh_token = create_refresh_token(self.settings , subject=str(user.id), jti=secrets.token_hex(16))
        return access_token, refresh_token


    async def refresh_pair(self , refresh_token:str) ->tuple[str, str|None]:
        payload = decode_refresh(self.settings , refresh_token)
        sub = payload.get("sub")
        new_access_token = create_access_token(self.settings , subject=str(sub))
        if self.settings.refresh_rotation:
            new_refresh_token = create_refresh_token(self.settings , subject=str(sub) , jti=secrets.token_hex(16))
            return new_access_token, new_refresh_token
        return new_access_token, None


class AuthService:
    def __init__(self, settings: AuthSettings, repo: SyncUserProtocol):
        self.settings = settings
        self.repo = repo

    def create_user(self, email: str, username: str, password: str) -> UserProtocol:
        existing_user = (
            self.repo.get_by_email_or_username(email)
            or self.repo.get_by_email_or_username(username)
        )
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email or username already exists",
            )

        return self.repo.create_user(
            email=email,
            username=username,
            password=hash_password(password),
            is_active=True,
            is_staff=False,
            is_superuser=False,
        )

    def create_superuser(self, email: str, username: str, password: str) -> UserProtocol:
        existing_user = (
            self.repo.get_by_email_or_username(email)
            or self.repo.get_by_email_or_username(username)
        )
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email or username already exists",
            )

        return self.repo.create_user(
            email=email,
            username=username,
            password=hash_password(password),
            is_active=True,
            is_staff=True,
            is_superuser=True,
        )

    def authenticate(self, user_name_or_email: str, password: str) -> UserProtocol:
        user = self.repo.get_by_email_or_username(user_name_or_email)
        if not user or not verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )
        return user

    def assign_token(self, user: UserProtocol) -> tuple[str, str]:
        access_token = create_access_token(self.settings, subject=str(user.id))
        refresh_token = create_refresh_token(self.settings, subject=str(user.id), jti=secrets.token_hex(16))
        return access_token, refresh_token

    def refresh_pair(self, refresh_token: str) -> tuple[str, str | None]:
        payload = decode_refresh(self.settings, refresh_token)
        sub = payload.get("sub")

        new_access_token = create_access_token(self.settings, subject=str(sub))

        if self.settings.refresh_rotation:
            new_refresh_token = create_refresh_token(
                self.settings,
                subject=str(sub),
                jti=secrets.token_hex(16),
            )
            return new_access_token, new_refresh_token

        return new_access_token, None
