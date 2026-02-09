from fastapi import Request
from  .settings import AuthSettings

def extract_access_token(request: Request, settings: AuthSettings) -> str | None:
    if settings.accept_header:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            return auth_header[7:]

    if settings.accept_cookie:
        cookie_name = settings.cookie_name_access
        return request.cookies.get(cookie_name)

    return None

def  extract_refresh_token(request: Request, settings: AuthSettings) -> str | None:
    if settings.accept_header:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            return auth_header[7:]

    if settings.accept_cookie:
        cookie_name = settings.cookie_name_refresh
        return request.cookies.get(cookie_name)

    return None


