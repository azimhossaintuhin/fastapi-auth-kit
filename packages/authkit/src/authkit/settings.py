from  dataclasses import dataclass
from typing import Literal

@dataclass(frozen=True)
class AuthSettings:
    secret_key: str
    algorithm: str = "HS256"

    access_minutes: int = 15
    refresh_days: int = 7

    cookie_name_access: str = "access_token"
    cookie_name_refresh: str = "refresh_token"

    accept_header: bool = True
    accept_cookie: bool = True

    set_cookie_on_login: bool = True
    cookie_secure: bool = True
    cookie_samesite: Literal["lax", "strict", "none"] = "lax"
    cookie_max_age_access: int = 60 * 15
    cookie_max_age_refresh: int = 60 * 60 * 24 * 7

    # SimpleJWT-style extras
    refresh_rotation: bool = True
    blacklist_after_rotation: bool = True 