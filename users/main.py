"""Define all endpoints here."""
import os
from typing import Optional
import httpx

from fastapi import FastAPI, HTTPException, Depends, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from environ import to_config
from prometheus_client import start_http_server, Counter

from users.config import AppConfig
from users.database import get_database_url

from users.crud import (
    create_user,
    get_all_users,
    get_user_by_id,
    get_user_by_username,
    update_user, change_blocked_status, get_details_with_id, get_user_by_email
)
from users.schemas import UserCreate, UserUpdate, UserBase
from users.models import Base
from users.admin.dao import create_admin, get_all as get_all_admins, \
    get_admin_by_email
from users.admin.dto import AdminCreationDTO

app = FastAPI()

allow_all = ['*']
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex="http(s)?://(.*vercel.app|localhost|local)(:3000)?",
    allow_credentials=True,
    allow_methods=allow_all,
    allow_headers=allow_all
)

CONFIGURATION = to_config(AppConfig)

# Metrics
REQUEST_COUNTER = Counter(
    "my_failures", "Description of counter", ["endpoint", "http_verb"]
)
start_http_server(8002)

# Database initialization.
# Maybe move this, so it is only run when required? Now it runs when ever
# the application is started, and we may not need to create the database
# structure.
ENGINE = create_engine(get_database_url(CONFIGURATION))
if "TESTING" not in os.environ:
    Base.metadata.create_all(bind=ENGINE)


# Helper methods, move somewhere else
def get_db() -> Session:
    """Create a session."""
    return Session(autocommit=False, autoflush=False, bind=ENGINE)


def get_auth_header(request):
    """Check existence auth header, return it or None if it doesn't exist."""
    auth_header = request.headers.get("Authorization")
    if auth_header is None:
        return None
    return {"Authorization": auth_header}


# Move to their own module
async def get_credentials(request):
    """Get user details from token in request header."""
    if "TESTING" in os.environ:
        if "TOKEN_ID" not in os.environ or "TOKEN_ROLE" not in os.environ:
            raise HTTPException(status_code=403)
        testing_token = {
            "id": os.environ["TOKEN_ID"],
            "role": os.environ["TOKEN_ROLE"],
        }
        return testing_token
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
                "id": int(creds.json()['data']["id"])
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
    if "TESTING" in os.environ:
        return os.environ["TEST_ID"]
    body = {
        "email": email,
        "password": password
    }
    url = f"http://{CONFIGURATION.auth.host}/auth"
    res = await httpx.AsyncClient().post(url, json=body)
    if res.status_code != 200:
        raise HTTPException(status_code=res.status_code, detail=res.json())
    return res.json()["id"]


async def token_login_firebase(request: Request, role: str,
                               session: Session):
    """Log in with token in request header."""
    req = await request.json()
    if "TESTING" in os.environ:
        if os.environ["TOKEN_ID"] != os.environ["TEST_ID"]:
            raise HTTPException(status_code=400, detail="Error logging in")
        return {
            "token": "test_token",
            "id": os.environ["TOKEN_ID"]
        }
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
    res = await httpx.AsyncClient().post(url, json=body)
    if res.status_code != 200:
        raise HTTPException(status_code=res.status_code,
                            detail=res.json()["Message"])
    try:
        with session as open_session:
            email = body["email"]
        user = get_user_by_email(open_session, email=email)
        if role == "admin":
            user = get_admin_by_email(open_session, email=email)
        return {"token": await get_token(role, user.id), "id": user.id}
    except Exception as json_exception:
        msg = "Login error"
        raise HTTPException(status_code=400, detail=msg) from json_exception


# Endpoint definition
@app.post("/users/login")
async def login(request: Request, session: Session = Depends(get_db)):
    """Log in to Firebase with email, password. Return token if successful."""
    body = await token_login_firebase(request, "user", session)
    return JSONResponse(content=body, status_code=200)


def add_user(session: Session, user: UserBase):
    """Create new user in the database based on id and user details."""
    with session as open_session:
        db_user = get_user_by_email(open_session, email=user.email)
        if db_user:
            msg = "User with that email already present"
            raise HTTPException(status_code=400, detail=msg)
        db_user = get_user_by_username(open_session, username=user.username)
        if db_user:
            msg = "User with that username already present"
            raise HTTPException(status_code=400, detail=msg)
        return create_user(session=open_session, user=user)


@app.post("/users")
async def create(new_user: UserCreate, session: Session = Depends(get_db)):
    """Create new user in Firebase, add it to the database if successful."""
    if new_user.email is None or new_user.password is None:
        msg = {'message': 'Error! Missing Email or Password'}
        raise HTTPException(detail=msg, status_code=400)
    await add_user_firebase(new_user.email, new_user.password)
    with session as open_session:
        return add_user(open_session, new_user)


async def validate_idp_token(request: Request):
    """Validate IDP Token through auth microservice."""
    auth_header = get_auth_header(request)
    if auth_header is None:
        msg = "Missing IDP token"
        raise HTTPException(detail=msg, status_code=404)
    request = await request.json()
    url = f"http://{CONFIGURATION.auth.host}/auth/loginIDP"
    res = await httpx.AsyncClient().post(url, json=request,
                                         headers=auth_header)
    if res.status_code != 200:
        raise HTTPException(status_code=res.status_code,
                            detail=res.json()["Message"])


@app.post("/usersIDP")
async def create_idp_user(request: Request,
                          user: UserBase, session: Session = Depends(get_db)):
    """Create new user with federated identity in database."""
    if user.email is None:
        msg = {'message': 'Error! Missing Email'}
        raise HTTPException(detail=msg, status_code=400)
    await validate_idp_token(request)
    with session as open_session:
        return add_user(open_session, user)


@app.post("/login/usersIDP")
async def login_idp(request: Request, session: Session = Depends(get_db)):
    """Verify user is logged in through IDP and return token."""
    await validate_idp_token(request)
    request = await request.json()
    with session as open_session:
        user = get_user_by_email(session=open_session, email=request["email"])
        if user is None:
            msg = {'message': 'No user with such an email'}
            raise HTTPException(detail=msg, status_code=404)
    return {"token": await get_token("user", user.id), "id": user.id}


@app.get("/users/{_id}")
async def get_one(
    request: Request,
    _id: int,
    session: Session = Depends(get_db)
):
    """Retrieve details for users with specified id."""
    token = await get_credentials(request)
    if not token["role"] == "admin" and not token["role"] == "user":
        raise HTTPException(status_code=403, detail="Invalid credentials")
    with session as open_session:
        db_user = get_user_by_id(open_session, user_id=_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@app.patch("/users/status/{_id}")
async def change_status(request: Request,
                        _id: int,
                        session: Session = Depends(get_db)):
    """Invert blocked status of a user.

    Only admins allowed, can't block other admins
    """
    token = await get_credentials(request)
    if not token["role"] == "admin":
        raise HTTPException(status_code=403, detail="Invalid credentials")
    with session as open_session:
        db_user = get_user_by_id(open_session, user_id=_id)
        change_blocked_status(open_session, _id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")


@app.patch("/users/{_id}")
async def patch_user(
    request: Request,
    _id: int,
    user: UserUpdate,
    session: Session = Depends(get_db)
):
    """Update user data."""
    token = await get_credentials(request)
    if token["role"] == "user" and token["id"] != _id:
        raise HTTPException(status_code=403, detail="Invalid credentials")
    with session as open_session:
        if get_user_by_id(open_session, user_id=_id) is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )
        update_user(session, _id, user)
    return JSONResponse(content={}, status_code=200)


@app.get("/users")
async def get_all(
    username: Optional[str] = None,
    offset: Optional[int] = 0,
    limit: Optional[int] = 10,
    session: Session = Depends(get_db)
):
    """Retrieve details for all users currently present in the database."""
    with session as open_session:
        if username is None:
            return get_all_users(open_session, limit=limit, offset=offset)
        db_user = get_user_by_username(open_session, username=username)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@app.post("/users/recovery/{user_id}")
async def password_recovery(request: Request,
                            user_id: int, session: Session = Depends(get_db)):
    """Request auth service to start password recovery for user_id."""
    auth_header = get_auth_header(request)
    if auth_header is None:
        raise HTTPException(status_code=403, detail="No token")
    token = await get_credentials(request)
    if token["id"] != user_id:
        raise HTTPException(status_code=403, detail="Invalid credentials")
    with session as open_session:
        db_user = get_user_by_id(open_session, user_id=user_id)
        if db_user is None:
            raise HTTPException(status_code=404, detail="User not found")
        email, username = get_details_with_id(open_session, user_id)
    url = f"http://{CONFIGURATION.auth.host}/auth/recovery?email=" + email \
          + "&username=" + username
    res = await httpx.AsyncClient().post(url, headers=auth_header)
    if res.status_code != 200:
        raise HTTPException(status_code=res.status_code,
                            detail=res.json()["Message"])
    return JSONResponse(content={}, status_code=200)


# Admin endpoints. Maybe move to their own module.
@app.post("/admins")
async def add_admin(
    new_admin: AdminCreationDTO,
    session: Session = Depends(get_db)
):
    """Create an admin."""
    if new_admin.email is None:
        msg = {'message': 'Error! Missing Email.'}
        raise HTTPException(detail=msg, status_code=400)
    if new_admin.password is None:
        msg = {'message': 'Error! Missing Password.'}
        raise HTTPException(detail=msg, status_code=400)
    await add_user_firebase(new_admin.email, new_admin.password)
    with session as open_session:
        return create_admin(open_session, new_admin)


@app.get("/admins")
async def get_admins(request: Request, session: Session = Depends(get_db)):
    """Return all administrators."""
    token = await get_credentials(request)
    if token["role"] != "admin":
        raise HTTPException(status_code=403, detail="Invalid credentials")
    with session as open_session:
        return get_all_admins(open_session)


@app.post("/admins/login")
async def admin_login(request: Request, session: Session = Depends(get_db)):
    """Login as administrator. Return token if successful."""
    body = await token_login_firebase(request, "admin", session)
    return JSONResponse(content=body, status_code=200)
