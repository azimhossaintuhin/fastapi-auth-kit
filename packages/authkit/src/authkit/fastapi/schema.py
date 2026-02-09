from pydantic import  BaseModel ,EmailStr
from typing import Optional

class RegisterInSchema(BaseModel):
    email: EmailStr
    username: str
    password: str


class LoginInSchema(BaseModel):
    username_or_email: str
    password: str


class RefreshTokenSchema(BaseModel):
    refresh_token: Optional[str] = None


