import json
import firebase_admin
import pyrebase
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from environ import to_config
from prometheus_client import start_http_server, Counter
from firebase_admin import credentials, auth

from users.config import AppConfig
from users.database import get_database_url, get_db
from users.crud import create_user, delete_user, get_all_users, get_user
from users.schemas import User, UserCreate
from users.models import Base

cred = credentials.Certificate("users/taller2-fiufit-firebase-adminsdk-zwduu-404e45eb18.json")
firebase = firebase_admin.initialize_app(cred)
pb = pyrebase.initialize_app(json.load(open('firebase_config.json')))

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

# Database
engine = create_engine(get_database_url(CONFIGURATION))
Base.metadata.create_all(bind=engine)


def add_user(session: Session, user: User):
    """Attempts to create new user in the database based on id and user details.
    Raises exception if user is already present"""
    with session as open_session:
        db_user = get_user(open_session, user_id=user.id)
        if db_user:
            raise HTTPException(status_code=400, detail="User already present")
        return create_user(session=open_session, user=user)


@app.post("/users/login")
async def login(request: Request):
    """Logs in to Firebase with email, password. Returns token if successful"""
    req_json = await request.json()
    email = req_json['email']
    password = req_json['password']
    try:
        user = pb.auth().sign_in_with_email_and_password(email, password)
        jwt = user['idToken']
        return JSONResponse(content={'token': jwt, 'id': user["uid"]}, status_code=200)
    except:
        raise HTTPException(detail={'message': 'There was an error logging in'}, status_code=400)


@app.post("/users")
def create(new_user: UserCreate, session: Session = Depends(get_db)):
    """Attempts to create new user in Firebase, adds it to the database if successful"""
    if new_user.email is None or new_user.password is None:
        raise HTTPException(detail={'message': 'Error! Missing Email or Password'}, status_code=400)
    try:
        user = auth.create_user(
            email=new_user.email,
            password=new_user.password
        )
    except:
        raise HTTPException(detail={'message': 'Error Creating User'}, status_code=400)
    details = {"id": user.uid} | new_user.dict()
    with session as open_session:
        return add_user(open_session, User(**details))


@app.get("/users/{id}")
async def get_one(id: str, session: Session = Depends(get_db)):
    """Retrieves details for users with specified id"""
    with session as open_session:
        db_user = get_user(open_session, user_id=id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@app.delete("/users", include_in_schema = False)
async def delete(email: str, session: Session = Depends(get_db)):
    """Deletes users with specified email and password"""
    new_user = auth.get_user_by_email(email)
    with session as open_session:
        db_user = get_user(open_session, new_user.uid)
        if db_user is None:
            return
        auth.delete_user(new_user.uid)
        delete_user(open_session, new_user.uid)


@app.get("/users/")
async def get_all(session: Session = Depends(get_db)):
    """Retrieves details for all users currently present in the database"""
    with session as open_session:
        return get_all_users(open_session)
