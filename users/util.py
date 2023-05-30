"""Provides functions for interacting with other microservices."""
import httpx
from environ import to_config
from fastapi import HTTPException
from sqlalchemy.orm import Session
from starlette.requests import Request

from users.admin.dao import get_admin_by_email
from users.config import AppConfig
from users.crud import get_user_by_email

CONFIGURATION = to_config(AppConfig)


def get_auth_header(request):
    """Check existence auth header, return it or None if it doesn't exist."""
    auth_header = request.headers.get("Authorization")
    if auth_header is None:
        return None
    return {"Authorization": auth_header}


async def get_credentials(request):
    """Get user details from token in request header."""
    url = f"http://{CONFIGURATION.auth.host}/auth/credentials"
    auth_header = get_auth_header(request)
    if auth_header is not None:
        creds = await httpx.AsyncClient().get(url, headers=auth_header)
        if creds.status_code != 200:
            raise HTTPException(status_code=creds.status_code,
                                detail=creds.json()["Message"])
        try:
            return {
                "role": creds.json()['data']["role"],
                "id": creds.json()['data']["id"]
            }
        except Exception as json_exception:
            msg = "Token format error"
            raise HTTPException(status_code=403,
                                detail=msg) from json_exception
    else:
        raise HTTPException(status_code=403, detail="No token")


async def get_token(role, user_id):
    """Return token with role and user_id passed by parameter."""
    url = f"http://{CONFIGURATION.auth.host}/auth/token?role=" + \
          role + "&id=" + str(user_id)
    token = await httpx.AsyncClient().get(url)
    return token.json()["data"]


async def add_user_firebase(email, password):
    """Add user to firebase and return uid."""
    body = {
        "email": email,
        "password": password
    }
    url = f"http://{CONFIGURATION.auth.host}/auth"
    res = await httpx.AsyncClient().post(url, json=body)
    if res.status_code != 200:
        raise HTTPException(status_code=res.status_code, detail=res.json())


async def token_login_firebase(request: Request, role: str,
                               session: Session):
    """Log in with token in request header."""
    req = await request.json()
    url = f"http://{CONFIGURATION.auth.host}/auth/tokenLogin"
    auth_header = get_auth_header(request)
    if auth_header is not None:
        res = await httpx.AsyncClient().post(url, json=req,
                                             headers=auth_header)
        if res.status_code != 200:
            raise HTTPException(status_code=res.status_code,
                                detail=res.json()["Message"])
        return res.json()
    return await regular_login_firebase(req, role, session)


async def regular_login_firebase(body, role, session: Session):
    """Log in with provided body and return token with proper role."""
    url = f"http://{CONFIGURATION.auth.host}/auth/login"
    with session as open_session:
        email = body["email"]
        user = get_user_by_email(open_session, email=email)
        if role == "admin":
            user = get_admin_by_email(open_session, email=email)
        if user is None:
            msg = "No such user"
            raise HTTPException(status_code=404, detail=msg)
    res = await httpx.AsyncClient().post(url, json=body)
    if res.status_code != 200:
        raise HTTPException(status_code=res.status_code,
                            detail=res.json()["Message"])
    return {"token": await get_token(role, user.id), "id": user.id}
