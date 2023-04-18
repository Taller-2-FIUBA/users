# pylint: disable=missing-class-docstring
"""Validates token existence with proper scheme."""
from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials


class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super().__init__(auto_error=auto_error)

    async def __call__(self, request: Request):
        auth: HTTPAuthorizationCredentials = await super().__call__(request)
        msg = "Invalid authentication scheme."
        if auth:
            if not auth.scheme == "Bearer":
                raise HTTPException(status_code=403, detail=msg)
            return auth.credentials
        raise HTTPException(status_code=403, detail=msg)
