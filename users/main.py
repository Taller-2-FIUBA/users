import json
import firebase_admin
import pyrebase
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from environ import to_config
from prometheus_client import start_http_server, Counter
from firebase_admin import credentials, auth
from users.config import AppConfig
from users import crud
from users import models
from users import schemas
from users.database import SessionLocal, engine

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

REQUEST_COUNTER = Counter(
    "my_failures", "Description of counter", ["endpoint", "http_verb"]
)
CONFIGURATION = to_config(AppConfig)
models.Base.metadata.create_all(bind=engine)
start_http_server(8002)


# Dependency
def get_db():
    database = SessionLocal()
    try:
        yield database
    finally:
        database.close()


def add_user_database(database: Session, user: schemas.User):
    """Attempts to create new user in the database based on id and user details.
    Raises exception if user is already present"""
    db_user = crud.get_user(database, user_id=user.id)
    if db_user:
        raise HTTPException(status_code=400, detail="User already present")
    return crud.create_user(database=database, user=user)


@app.post("/users/login")
async def login(request: Request):
    """Logs in to Firebase with email, password. Returns token if successful"""
    req_json = await request.json()
    email = req_json['email']
    password = req_json['password']
    try:
        user = pb.auth().sign_in_with_email_and_password(email, password)
        jwt = user['idToken']
        return JSONResponse(content={'token': jwt}, status_code=200)
    except:
        raise HTTPException(detail={'message': 'There was an error logging in'}, status_code=400)


@app.post("/users")
def create_new_user(new_user: schemas.UserCreate, database: Session = Depends(get_db)):
    """Attempts to create new user in Firebase, adds it to the database if successful"""
    if new_user.email is None or new_user.password is None:
        raise HTTPException(detail={'message': 'Error! Missing Email or Password'}, status_code=400)
    try:
        user = auth.create_user(
            email=new_user.email,
            password=new_user.password
        )
        details = {"id": user.uid} | new_user.dict()
        return add_user_database(database, schemas.User(**details))
    except:
        raise HTTPException(detail={'message': 'Error Creating User'}, status_code=400)


@app.get("/users/{id}")
def user_details(id: str, database: Session = Depends(get_db)):
    """Retrieves details for users with specified id"""
    db_user = crud.get_user(database, user_id=id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@app.get("/users")
def get_all_users(database: Session = Depends(get_db)):
    """Retrieves details for all users currently present in the database"""
    return crud.get_all_users(database=database)
