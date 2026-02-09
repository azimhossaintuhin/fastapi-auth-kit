from __future__ import annotations
from typing import Any, Callable, Awaitable
from fastapi import  APIRouter, Depends, HTTPException , Request , Response,status

from ..ext.sqlalchemy import SQLAlchemyAsyncUserProtocol, SQLAlchemySyncUserProtocol
from ..extractors import extract_refresh_token
from ..settings import AuthSettings
from ..service import  AuthService, AsyncAuthService
from  ..authenticator import AsyncAuthenticator , SyncAuthenticator

from .schema import RegisterInSchema, LoginInSchema


def _set_access_cookie(response:Response , settings:AuthSettings, token:str):
    response.set_cookie(
        key=settings.cookie_name_access,
        value=token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        max_age=settings.cookie_max_age_access,
    )


def _set_refresh_cookie(response:Response,settings:AuthSettings, token:str):
    response.set_cookie(
        key=settings.cookie_name_refresh,
        value=token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        max_age=settings.cookie_max_age_refresh,
    )

def _clear_cookie(response:Response,settings:AuthSettings):
        response.delete_cookie(
            key=settings.cookie_name_access,
        )
        response.delete_cookie(
            key=settings.cookie_name_refresh,
        )

def build_auth_router_async(
        *,
        settings:AuthSettings,
        get_session:Callable[...,Any],
        user_model:type[Any]
)-> APIRouter:
    """
       Async FastAPI router.
       get_session must provide an AsyncSession (dependency).
    """

    router = APIRouter()

    def _svc(session=Depends(get_session))->AsyncAuthService:
        repo = SQLAlchemyAsyncUserProtocol(session ,user_model=user_model)
        return AsyncAuthService(settings, repo)

    def _auth(session=Depends(get_session))->AsyncAuthenticator:
        repo= SQLAlchemyAsyncUserProtocol(session ,user_model=user_model)
        return AsyncAuthenticator(settings , repo)


    @router.post("/register")
    async def register(data:RegisterInSchema,svc:AsyncAuthService=Depends(_svc)):
        user = await svc.create_user(data.email , data.username , data.password)
        return {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "is_staff": user.is_staff,
            "is_active": user.is_active,
        }


    @router.post("/login")
    async def login(data:LoginInSchema, response:Response, svc:AsyncAuthService=Depends(_svc)):
        user =  await svc.authenticate(data.username_or_email , data.password)
        access, refresh = await svc.assign_token(user)

        if  settings.set_cookie_on_login:
            _set_access_cookie(response , settings , access)
            _set_refresh_cookie(response , settings , refresh)
        return {
                "access_token": access,
                "refresh_token": refresh,
            }

    @router.post("/refresh")
    async def refresh(request:Request, response:Response, svc:AsyncAuthService=Depends(_svc)):
        rt = extract_refresh_token(request,settings)
        if not rt:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED , detail="Refresh token not found")
        access,refresh = await svc.refresh_pair(rt)

        if settings.set_cookie_on_login:
            _set_access_cookie(response , settings , access)
            _set_refresh_cookie(response , settings , refresh)

        return {
            "access_token": access,
            "refresh_token": refresh,
        }


    @router.post("/logout")
    async def logout(response:Response):
        _clear_cookie(response , settings)
        return {"logout": "success" , "ok":True}


    @router.get("/me")
    async def me(request:Request,auth:AsyncAuthenticator=Depends(_auth)):
        user = await auth.current_user(request)
        return {"id": user.id, "email": user.email, "username": user.username, "is_staff": user.is_staff, "is_superuser": user.is_superuser}

    return router


# ======= Sync Router =======#
def build_auth_router_sync(
        *,
        settings:AuthSettings,
        get_session:Callable[...,Any],
        user_models:type[Any]
)-> APIRouter:
    """
       Sync FastAPI router.
       get_session must provide a Session (dependency).
    """

    router = APIRouter()

    def _svc(session=Depends(get_session))->AuthService:
        repo = SQLAlchemySyncUserProtocol(session ,user_model=user_models)
        return  AuthService(settings, repo)


    def _auth(session=Depends(get_session))->SyncAuthenticator:
         repo =  SQLAlchemySyncUserProtocol(session ,user_model=user_models)
         return SyncAuthenticator(settings , repo)


    @router.post("/register")
    def register(data:RegisterInSchema,svc:AuthService=Depends(_svc)):
        user = svc.create_user(data.email , data.username , data.password)
        return {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "is_staff": user.is_staff,
            "is_active": user.is_active,
        }

    @router.post("/login")
    def login(data:LoginInSchema, response:Response, svc:AuthService=Depends(_svc)):
        user =  svc.authenticate(data.username_or_email , data.password)
        access, refresh = svc.assign_token(user)

        if  settings.set_cookie_on_login:
            _set_access_cookie(response , settings , access)
            _set_refresh_cookie(response , settings , refresh)
        return {
                "access_token": access,
                "refresh_token": refresh,
            }

    @router.post("/refresh")
    def refresh(request:Request, response:Response, svc:AuthService=Depends(_svc)):
        rt = extract_refresh_token(request,settings)
        if not rt:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED , detail="Refresh token not found")
        access,refresh = svc.refresh_pair(rt)

        if settings.set_cookie_on_login:
            _set_access_cookie(response , settings , access)
            _set_refresh_cookie(response , settings , refresh)

        return {
            "access_token": access,
            "refresh_token": refresh,
        }


    @router.post("/logout")
    def logout(response:Response):
        _clear_cookie(response , settings)
        return {"logout": "success" , "ok":True}


    @router.get("/me")
    def me(request:Request,auth:SyncAuthenticator=Depends(_auth)):
        user = auth.current_user(request)
        return {"id": user.id, "email": user.email, "username": user.username, "is_staff": user.is_staff, "is_superuser": user.is_superuser}

    return router







