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

def extract_refresh_token(request: Request, settings: AuthSettings, body_data: dict | None = None) -> str | None:
    """
    Extract refresh token from header, cookie, or request body.
    
    Priority order:
    1. Authorization header (Bearer token)
    2. Cookie (refresh_token)
    3. Request body (refresh_token field)
    """
    # Check Authorization header
    if settings.accept_header:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            return auth_header[7:]

    # Check cookie
    if settings.accept_cookie:
        cookie_name = settings.cookie_name_refresh
        token = request.cookies.get(cookie_name)
        if token:
            return token

    # Check request body
    if body_data and isinstance(body_data, dict):
        token = body_data.get("refresh_token")
        if token:
            return token

    return None


