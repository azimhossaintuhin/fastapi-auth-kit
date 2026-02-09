from fastapi import HTTPException,status, Request
from .settings import  AuthSettings
from  .extractors import  extract_access_token
from .tokens import  decode_access
from .protocols import  AsyncUserProtocol , SyncUserProtocol , UserProtocol


class AsyncAuthenticator:
    def __init__(self,settings:AuthSettings, repo:AsyncUserProtocol ):
        self.settings = settings
        self.repo = repo


    async def current_user(self,request:Request) -> UserProtocol:
        token = extract_access_token(request,self.settings)
        if not token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Not authenticated")
        payload = decode_access(self.settings,token)
        sub = payload.get("sub")
        if not sub:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Invalid token payload")

        user = await self.repo.get_by_id(int(sub))
        if  not user:
            raise  HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="User not found")
        return user


class SyncAuthenticator:
    def __init__(self,settings:AuthSettings,repo:SyncUserProtocol):
        self.settings = settings
        self.repo = repo

    def  current_user(self,request:Request) -> UserProtocol:
        token = extract_access_token(request,self.settings)
        if not token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Not authenticated")
        payload = decode_access(self.settings,token)
        sub = payload.get("sub")
        if not sub:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Invalid token payload")

        user = self.repo.get_by_id(int(sub))
        if  not user:
            raise  HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="User not found")

        return user
