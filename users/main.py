"""Define all endpoints here."""
import logging
import os
import time
from typing import Optional
import sentry_sdk
import httpx


from fastapi import FastAPI, HTTPException, Depends, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.applications import get_swagger_ui_html
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from environ import to_config
from prometheus_client import start_http_server

import users.metrics as m
from users.config import AppConfig
from users.database import get_database_url
from users.crud import (
    create_user,
    get_all_users,
    get_user_by_id,
    get_user_by_username,
    update_user,
    change_blocked_status,
    get_user_by_email,
    get_users_followed_by,
    unfollow_user,
    follow_new_user
)
from users.schemas import UserCreate, UserUpdate, UserBase
from users.models import Base
from users.admin.dao import create_admin, get_all as get_all_admins
from users.admin.dto import AdminCreationDTO
from users.util import get_auth_header, \
    get_credentials, get_token, add_user_firebase, token_login_firebase
from users.healthcheck import HealthCheckDto

BASE_URI = "/users"
CONFIGURATION = to_config(AppConfig)
DOCUMENTATION_URI = BASE_URI + "/documentation/"
START = time.time()

if CONFIGURATION.sentry.enabled:
    sentry_sdk.init(dsn=CONFIGURATION.sentry.dsn, traces_sample_rate=0.5)

logging.basicConfig(encoding="utf-8", level=CONFIGURATION.log_level.upper())
app = FastAPI(
    debug=CONFIGURATION.log_level.upper() == "DEBUG",
    openapi_url=DOCUMENTATION_URI + "openapi.json",
)

METHODS = [
    "GET",
    "get",
    "POST",
    "post",
    "PUT",
    "put",
    "PATCH",
    "patch",
    "OPTIONS",
    "options",
    "DELETE",
    "delete",
    "HEAD",
    "head",
]
ORIGIN_REGEX = "(http)?(s)?(://)?(.*vercel.app|localhost|local)(:3000)?.*"
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=METHODS,
    allow_headers=['*']
)

# Metrics
start_http_server(CONFIGURATION.prometheus_port)

# Database initialization.
# Maybe move this, so it is only run when required? Now it runs when ever
# the application is started, and we may not need to create the database
# structure.
ENGINE = create_engine(get_database_url(CONFIGURATION))
if "TESTING" not in os.environ:
    logging.info("Building database...")
    Base.metadata.create_all(bind=ENGINE)


# Helper methods, move somewhere else
def get_db() -> Session:
    """Create a session."""
    return Session(autocommit=False, autoflush=False, bind=ENGINE)


# Endpoint definition
@app.post("/users/login")
async def login(request: Request, session: Session = Depends(get_db)):
    """Log in to Firebase with email, password. Return token if successful."""
    m.REQUEST_COUNTER.labels("/users/login", "post").inc()
    logging.info("Log-in user %s...")
    body = await token_login_firebase(request, "user", session)
    return JSONResponse(content=body, status_code=200)


def validate_user(session: Session, user: UserBase):
    """Create new user in the database based on id and user details."""
    logging.info("Validating user...")
    with session as open_session:
        db_user = get_user_by_email(open_session, email=user.email)
        if db_user:
            msg = "User with that email already present"
            logging.warning("Error creating user: %s", msg)
            raise HTTPException(status_code=400, detail=msg)
        db_user = get_user_by_username(open_session, username=user.username)
        if db_user:
            msg = "User with that username already present"
            logging.warning("Error creating user: %s", msg)
            raise HTTPException(status_code=400, detail=msg)


@app.post("/users")
async def create(new_user: UserCreate, session: Session = Depends(get_db)):
    """Create new user in Firebase, add it to the database if successful."""
    logging.info("Creating user %s...", new_user)
    m.REQUEST_COUNTER.labels("/users", "post").inc()
    if new_user.email is None or new_user.password is None:
        msg = {'message': 'Error! Missing Email or Password'}
        logging.warning(
            "Error creating user: %s password: %s",
            new_user.email, new_user.password
        )
        raise HTTPException(detail=msg, status_code=400)
    validate_user(session, new_user)
    await add_user_firebase(new_user.email, new_user.password)
    logging.debug("Creating user in DB...")
    return create_user(session=session, user=new_user)


async def validate_idp_token(request: Request):
    """Validate IDP Token through auth microservice."""
    logging.debug("Validating IDP token...")
    auth_header = get_auth_header(request)
    if auth_header is None:
        msg = "Missing IDP token"
        raise HTTPException(detail=msg, status_code=400)
    request = await request.json()
    url = f"http://{CONFIGURATION.auth.host}/auth/loginIDP"
    logging.info("Validating IDP token '%s' in '%s'", auth_header, url)
    res = await httpx.AsyncClient().post(url, json=request,
                                         headers=auth_header)
    if res.status_code != 200:
        error = res.json()["Message"]
        logging.error("Error when trying to login with IDP token: %s", error)
        raise HTTPException(status_code=res.status_code, detail=error)


@app.post("/users/usersIDP")
async def create_idp_user(request: Request,
                          user: UserBase, session: Session = Depends(get_db)):
    """Create new user with federated identity in database."""
    logging.info("Creating user with IDP token...")
    m.REQUEST_COUNTER.labels("/users/usersIDP", "post").inc()
    if user.email is None:
        msg = {'message': 'Error! Missing Email'}
        raise HTTPException(detail=msg, status_code=400)
    validate_user(session, user)
    await validate_idp_token(request)
    logging.debug("Creating user in DB...")
    return create_user(session=session, user=user)


@app.post("/users/login/usersIDP")
async def login_idp(request: Request, session: Session = Depends(get_db)):
    """Verify user is logged in through IDP and return token."""
    logging.info("Log-in user with IDP token...")
    m.REQUEST_COUNTER.labels("/users/login/usersIDP", "post").inc()
    await validate_idp_token(request)
    request = await request.json()
    with session as open_session:
        user = get_user_by_email(session=open_session, email=request["email"])
        if user is None:
            msg = {'message': 'No IDP user with such an email'}
            logging.warning("Could not login with IDP token: %s", msg)
            raise HTTPException(detail=msg, status_code=404)
    return {"token": await get_token("user", user.id), "id": user.id}


@app.get("/users/{_id}")
async def get_one(
    request: Request,
    _id: int,
    session: Session = Depends(get_db)
):
    """Retrieve details for users with specified id."""
    logging.info("Retrieving user %d details...", _id)
    m.REQUEST_COUNTER.labels("/users/{_id}", "get").inc()
    token = await get_credentials(request)
    if not token["role"] == "admin" and not token["role"] == "user":
        logging.warning("Invalid role %s", token["role"])
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
    logging.info("Changing user %d status...", _id)
    m.REQUEST_COUNTER.labels("/users/status/{_id}", "patch").inc()
    token = await get_credentials(request)
    if not token["role"] == "admin":
        logging.warning("Invalid role %s", token["role"])
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
    m.REQUEST_COUNTER.labels("/users/{_id}", "patch").inc()
    logging.info("Updating user %d status...", _id)
    token = await get_credentials(request)
    if token["role"] == "user" and token["id"] != _id:
        logging.warning("Invalid role %s", token["role"])
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
    logging.info("Retrieving users...")
    m.REQUEST_COUNTER.labels("/users", "patch").inc()
    with session as open_session:
        if username is None:
            return get_all_users(open_session, limit=limit, offset=offset)
        db_user = get_user_by_username(open_session, username=username)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@app.post("/users/recovery/{username}")
async def password_recovery(username: str, session: Session = Depends(get_db)):
    """Request auth service to start password recovery for user_id."""
    logging.info("Recovering password for user %s...", username)
    m.REQUEST_COUNTER.labels("/users/recovery/{username}", "post").inc()
    with session as open_session:
        db_user = get_user_by_username(session=open_session, username=username)
        if db_user is None:
            raise HTTPException(status_code=404, detail="User not found")
    url = f"http://{CONFIGURATION.auth.host}/auth/recovery?email=" + \
          db_user["email"] + "&username=" + username
    logging.info("Requesting password recovery to %s...", url)
    res = await httpx.AsyncClient().post(url)
    if res.status_code != 200:
        error = res.json()["Message"]
        logging.error("Error when recovering password: %s", error)
        raise HTTPException(status_code=res.status_code, detail=error)
    return JSONResponse(content={}, status_code=200)


@app.get("/users/{user_id}/followed/")
async def get_followed_users(
    user_id: int,
    session: Session = Depends(get_db)
):
    """Retrieve all users followed by user with specified id."""
    with session as open_session:
        db_user = get_user_by_id(open_session, user_id=user_id)
        if db_user is None:
            raise HTTPException(status_code=404, detail="User not found")
    return get_users_followed_by(session, user_id)


@app.delete("/users/{user_id}/followed/{_id}")
async def stop_following_user(
    request: Request,
    _id: int,
    user_id: int,
    session: Session = Depends(get_db)
):
    """Retrieve all users followed by user with specified id."""
    with session as open_session:
        db_user = get_user_by_id(open_session, user_id=user_id)
        if db_user is None:
            raise HTTPException(status_code=404, detail="User not found")
    token = await get_credentials(request)
    if token["id"] != user_id:
        raise HTTPException(status_code=403, detail="Invalid credentials")
    return unfollow_user(session, user_id, _id)


@app.post("/users/{user_id}/followed/{_id}")
async def follow_user(
    request: Request,
    _id: int,
    user_id: int,
    session: Session = Depends(get_db)
):
    """Retrieve all users followed by user with specified id."""
    with session as open_session:
        db_user = get_user_by_id(open_session, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    token = await get_credentials(request)
    if token["id"] != user_id:
        raise HTTPException(status_code=403, detail="Invalid credentials")
    if _id == user_id:
        msg = "User can't follow himself"
        raise HTTPException(status_code=400, detail=msg)
    return follow_new_user(session, user_id, _id)


# Admin endpoints. Maybe move to their own module.
@app.post("/admins")
async def add_admin(
    new_admin: AdminCreationDTO,
    session: Session = Depends(get_db)
):
    """Create an admin."""
    logging.info("Creating admin...")
    m.REQUEST_COUNTER.labels("/admins", "post").inc()
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
    logging.info("Retrieving admins...")
    m.REQUEST_COUNTER.labels("/admins", "get").inc()
    token = await get_credentials(request)
    if token["role"] != "admin":
        logging.warning("Invalid role %s", token["role"])
        raise HTTPException(status_code=403, detail="Invalid credentials")
    with session as open_session:
        return get_all_admins(open_session)


@app.post("/admins/login")
async def admin_login(request: Request, session: Session = Depends(get_db)):
    """Login as administrator. Return token if successful."""
    logging.info("Login admins...")
    m.REQUEST_COUNTER.labels("/admins/login", "post").inc()
    body = await token_login_firebase(request, "admin", session)
    return JSONResponse(content=body, status_code=200)


@app.get(BASE_URI + "/healthcheck/")
async def health_check() -> HealthCheckDto:
    """Check for how long has the service been running."""
    return HealthCheckDto(uptime=time.time() - START)


@app.get(DOCUMENTATION_URI, include_in_schema=False)
async def custom_swagger_ui_html(req: Request):
    """To show Swagger with API documentation."""
    root_path = req.scope.get("root_path", "").rstrip("/")
    openapi_url = root_path + app.openapi_url
    return get_swagger_ui_html(
        openapi_url=openapi_url,
        title="FIUFIT users",
    )
