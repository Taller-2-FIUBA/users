"""Provides functions for interacting with other microservices."""
import logging
import httpx
from environ import to_config
from fastapi import HTTPException, Request
from sqlalchemy.orm import Session

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
    logging.info("Getting user credentials...")
    url = f"http://{CONFIGURATION.auth.host}/auth/credentials"
    logging.info("Getting user credentials in auth service: %s", url)
    auth_header = get_auth_header(request)
    if auth_header is not None:
        logging.info("Using auth header: %s...", auth_header)
        creds = await httpx.AsyncClient().get(url, headers=auth_header)
        if creds.status_code != 200:
            error = creds.json()["Message"]
            logging.error("Error when trying to authenticate: %s", error)
            raise HTTPException(status_code=creds.status_code, detail=error)
        try:
            return {
                "role": creds.json()['data']["role"],
                "id": creds.json()['data']["id"]
            }
        except Exception as json_exception:
            msg = "Token format error"
            logging.exception("Error when trying to authenticate")
            raise HTTPException(status_code=403,
                                detail=msg) from json_exception
    else:
        raise HTTPException(status_code=403, detail="No token")


async def get_token(role, user_id):
    """Return token with role and user_id passed by parameter."""
    logging.info("Getting token for %d with role %s", user_id, role)
    url = f"http://{CONFIGURATION.auth.host}/auth/token?role=" + \
          role + "&id=" + str(user_id)
    token = await httpx.AsyncClient().get(url)
    return token.json()["data"]


async def add_user_firebase(email, password):
    """Add user to firebase and return uid."""
    logging.info("Creating user: %s password: %s in firebase", email, password)
    body = {
        "email": email,
        "password": password
    }
    url = f"http://{CONFIGURATION.auth.host}/auth"
    logging.info("Creating user in auth service: %s", url)
    res = await httpx.AsyncClient().post(url, json=body)
    if res.status_code != 200:
        error = res.json()
        logging.error("Error when trying to authenticate: %s", error)
        raise HTTPException(status_code=res.status_code, detail=error)


async def token_login_firebase(request: Request, role: str,
                               session: Session):
    """Log in with token in request header."""
    req = await request.json()
    url = f"http://{CONFIGURATION.auth.host}/auth/tokenLogin"
    logging.info("Logging user with token in auth service: %s", url)
    auth_header = get_auth_header(request)
    if auth_header is not None:
        logging.info("Using auth header: %s...", auth_header)
        res = await httpx.AsyncClient().post(url, json=req,
                                             headers=auth_header)
        if res.status_code != 200:
            error = res.json()["Message"]
            logging.error("Error when trying to login with token: %s", error)
            raise HTTPException(status_code=res.status_code, detail=error)
        return res.json()
    return await regular_login_firebase(req, role, session)


async def regular_login_firebase(body, role, session: Session):
    """Log in with provided body and return token with proper role."""
    url = f"http://{CONFIGURATION.auth.host}/auth/login"
    logging.info("Logging 'regular' user in auth service: %s", url)

    with session as open_session:
        email = body["email"]
        user = get_user_by_email(open_session, email=email)
        if role == "admin":
            user = get_admin_by_email(open_session, email=email)
        if user is None:
            msg = "No such user"
            logging.exception("Couldn't log in non-existing user.")
            raise HTTPException(status_code=404, detail=msg)
    res = await httpx.AsyncClient().post(url, json=body)
    if res.status_code != 200:
        error = res.json()["Message"]
        logging.error("Error when trying to login user: %s", error)
        raise HTTPException(status_code=res.status_code, detail=error)
    return {"token": await get_token(role, user.id), "id": user.id}
