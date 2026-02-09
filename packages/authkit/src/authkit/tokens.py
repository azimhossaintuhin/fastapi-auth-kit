from  datetime import  datetime , timedelta , timezone
from  jose import  jwt , JWTError
from fastapi import  HTTPException , status
from .settings import AuthSettings


def _encode(settings:AuthSettings , payload:dict) -> str:
    return  jwt.encode(payload, settings.secret_key , algorithm=settings.algorithm)


def _decode(settings:AuthSettings , token:str) -> dict[str, str]:
    return  jwt.decode(token,settings.secret_key,algorithms=[settings.algorithm])

def create_access_token(settings: AuthSettings, *, subject: str) -> str:
    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=settings.access_minutes)
    payload = {"sub": subject, "type": "access", "iat": int(now.timestamp()), "exp": int(exp.timestamp())}
    return _encode(settings, payload)

def create_refresh_token(settings: AuthSettings, *, subject: str, jti: str) -> str:
    now = datetime.now(timezone.utc)
    exp = now + timedelta(days=settings.refresh_days)
    payload = {"sub": subject, "type": "refresh", "jti": jti, "iat": int(now.timestamp()), "exp": int(exp.timestamp())}
    return _encode(settings, payload)


def decode_access(settings:AuthSettings,token:str)->dict[str, str]:
    try:
        payload = _decode(settings, token)
        if payload["type"] != "access":
            raise HTTPException(status_code=401,detail="Invalid access token")
        return payload
    except JWTError:
        raise HTTPException(status_code=401,detail="Invalid access token",headers={"WWW-Authenticate":"Bearer"})



def decode_refresh(settings:AuthSettings,token:str)-> dict:
    try:
        payload = _decode(settings, token)
        if payload["type"] != "refresh":
            raise HTTPException(status_code=401,detail="Invalid refresh token")
        return payload
    except JWTError:
        raise HTTPException(status_code=401,detail="Invalid refresh token",headers={"WWW-Authenticate":"Bearer"})