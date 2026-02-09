from typing import Protocol, Optional, runtime_checkable

@runtime_checkable
class UserProtocol(Protocol):
    id: int
    email: str
    username: str
    password_hash: str
    is_active: bool
    is_staff: bool
    is_superuser: bool

class AsyncUserProtocol(Protocol):
    async def get_by_id(self, user_id: int) -> Optional[UserProtocol]: ...
    async def get_by_email_or_username(self, value: str) -> Optional[UserProtocol]: ...
    async def create_user(
        self, *, email: str, username: str, password_hash: str,
        is_active: bool = ..., is_staff: bool = ..., is_superuser: bool = ...
    ) -> UserProtocol: ...

class SyncUserProtocol(Protocol):
    def get_by_id(self, user_id: int) -> Optional[UserProtocol]: ...
    def get_by_email_or_username(self, value: str) -> Optional[UserProtocol]: ...
    def create_user(
        self, *, email: str, username: str, password_hash: str,
        is_active: bool = ..., is_staff: bool = ..., is_superuser: bool = ...
    ) -> UserProtocol: ...
