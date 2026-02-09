from pydantic import  BaseModel ,EmailStr

class RegisterInSchema(BaseModel):
    email: EmailStr
    username: str
    password: str


class LoginInSchema(BaseModel):
    username_or_email: str
    password: str


