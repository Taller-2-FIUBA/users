"""Define all endpoints here."""
import json
import os
from typing import Optional
import firebase_admin
import pyrebase

from fastapi import FastAPI, HTTPException, Depends, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from environ import to_config
from prometheus_client import start_http_server, Counter
from firebase_admin import credentials, auth
from fastapi_pagination import LimitOffsetPage, add_pagination, \
    paginate, Params

from users.auth.auth_bearer import JWTBearer
from users.auth.auth_operations import encode_token, get_token
from users.config import AppConfig
from users.database import get_database_url
from users.crud import (
    create_user,
    delete_user,
    get_all_users,
    get_user_by_id,
    get_user_by_username,
    update_user, change_blocked_status
)
from users.schemas import User, UserCreate, UserUpdate
from users.models import Base
from users.admin.dao import create_admin, get_all as get_all_admins
from users.admin.dto import AdminCreationDTO, AdminDTO

cred = credentials.Certificate("users/fiufit-backend-keys.json")
firebase = firebase_admin.initialize_app(cred)
with open("firebase_config.json", "r", encoding="utf8") as firebase_config:
    pb = pyrebase.initialize_app(json.load(firebase_config))

app = FastAPI()

allow_all = ['*']
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_all,
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
# Maybe move this so it is only run when required? Now it runs when ever
# the application is started, and we may not need to create the database
# structure.
ENGINE = create_engine(get_database_url(CONFIGURATION))
if "TESTING" not in os.environ:
    Base.metadata.create_all(bind=ENGINE)

add_pagination(app)


# Helper methods.
def get_db() -> Session:
    """Create a session."""
    return Session(autocommit=False, autoflush=False, bind=ENGINE)


def add_user(session: Session, user: User):
    """Create new user in the database based on id and user details."""
    with session as open_session:
        db_user = get_user_by_id(open_session, user_id=user.id)
        if db_user:
            raise HTTPException(status_code=400, detail="User already present")
        return create_user(session=open_session, user=user)


# Endpoint definition
@app.post("/users/login")
async def login(request: Request):
    """Log in to Firebase with email, password. Return token if successful."""
    req_json = await request.json()
    email = req_json['email']
    password = req_json['password']
    try:
        pb.auth().sign_in_with_email_and_password(email, password)
    except Exception as login_exception:
        msg = "Error logging in"
        raise HTTPException(detail=msg, status_code=400) from login_exception
    user_id = auth.get_user_by_email(email).uid
    body = {"token": encode_token("user", user_id), "id": user_id}
    return JSONResponse(content=body, status_code=200)


@app.post("/users")
def create(new_user: UserCreate, session: Session = Depends(get_db)):
    """Create new user in Firebase, add it to the database if successful."""
    if new_user.email is None or new_user.password is None:
        msg = {'message': 'Error! Missing Email or Password'}
        raise HTTPException(detail=msg, status_code=400)
    try:
        user = auth.create_user(
            email=new_user.email,
            password=new_user.password
        )
    except Exception as signup_exception:
        msg = {'message': 'Error Creating User'}
        raise HTTPException(detail=msg, status_code=400) from signup_exception
    details = {"id": user.uid, "is_blocked": False} | new_user.dict()
    with session as open_session:
        return add_user(open_session, User(**details))


@app.get("/users/{_id}", dependencies=[Depends(JWTBearer())])
async def get_one(
    request: Request,
    _id: str,
    session: Session = Depends(get_db)
):
    """Retrieve details for users with specified id."""
    token = get_token(request)
    if not token["role"] == "admin" and not token["role"] == "user":
        raise HTTPException(status_code=403, detail="Invalid credentials")
    with session as open_session:
        db_user = get_user_by_id(open_session, user_id=_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@app.post("/validation-test", dependencies=[Depends(JWTBearer())])
async def test(request: Request):
    """Check if token is valid. Only for demonstration."""
    token = get_token(request)
    if not token["role"] == "admin" or not token["id"] == "magicword":
        raise HTTPException(status_code=403, detail="Invalid credentials")


@app.patch("/users/status/{_id}", dependencies=[Depends(JWTBearer())])
async def change_status(request: Request,
                        _id: str,
                        session: Session = Depends(get_db)):
    """Invert blocked status of a user.

    Only admins allowed, can't block other admins
    """
    token = get_token(request)
    if not token["role"] == "admin":
        raise HTTPException(status_code=403, detail="Invalid credentials")
    with session as open_session:
        db_user = get_user_by_id(open_session, user_id=_id)
        change_blocked_status(open_session, _id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")


@app.delete("/users", dependencies=[Depends(JWTBearer())])
async def delete(request: Request,
                 email: str,
                 session: Session = Depends(get_db)):
    """Delete users with specified email and password. Only admins allowed."""
    token = get_token(request)
    if not token["role"] == "admin":
        raise HTTPException(status_code=403, detail="Invalid credentials")
    new_user = auth.get_user_by_email(email)
    with session as open_session:
        db_user = get_user_by_id(open_session, new_user.uid)
        if db_user is None:
            return
        auth.delete_user(new_user.uid)
        delete_user(open_session, user_id=new_user.uid)


@app.patch("/users/{_id}")
async def patch_user(
    _id: str,
    user: UserUpdate,
    session: Session = Depends(get_db)
):
    """Update user data."""
    with session as open_session:
        if get_user_by_id(open_session, user_id=_id) is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )
        update_user(session, _id, user)
    return JSONResponse({}, status_code=status.HTTP_204_NO_CONTENT)


@app.get("/users")
async def get_all(
    username: Optional[str] = None,
    offset: Optional[str] = 0,
    limit: Optional[str] = 10,
    session: Session = Depends(get_db)
) -> LimitOffsetPage[User]:
    """Retrieve details for all users currently present in the database."""
    with session as open_session:
        if username is None:
            return paginate(get_all_users(open_session),
                            params=Params(offset=offset, limit=limit))
        db_user = get_user_by_username(open_session, username=username)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return paginate([db_user], params=Params(offset=0, limit=1))


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
    try:
        firebase_user = auth.create_user(
            email=new_admin.email,
            password=new_admin.password
        )
    except Exception as signup_exception:
        msg = {'message': 'Error Creating User'}
        raise HTTPException(detail=msg, status_code=400) from signup_exception
    fields_and_values = {"id": firebase_user.uid} | new_admin.dict()
    with session as open_session:
        return create_admin(open_session, AdminDTO(**fields_and_values))


@app.get("/admins")
async def get_admins(session: Session = Depends(get_db)):
    """Return all administrators."""
    with session as open_session:
        return get_all_admins(open_session)


@app.post("/admins/login")
async def admin_login(request: Request):
    """Login as administrator. Return token if successful."""
    req_json = await request.json()
    email = req_json['email']
    password = req_json['password']
    try:
        pb.auth().sign_in_with_email_and_password(email, password)
    except Exception as login_exception:
        msg = "Error logging in"
        raise HTTPException(detail=msg, status_code=400) from login_exception
    user_id = auth.get_user_by_email(email).uid
    body = {"token": encode_token("admin", user_id), "id": user_id}
    return JSONResponse(content=body, status_code=200)
