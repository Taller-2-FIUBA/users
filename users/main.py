"""Define all endpoints here."""
import json
import firebase_admin
import pyrebase
import jwt
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

cred = credentials.Certificate("users/fiufit-backend-keys.json")
firebase = firebase_admin.initialize_app(cred)
with open("firebase_config.json", "r", encoding="utf8") as firebase_config:
    pb = pyrebase.initialize_app(json.load(firebase_config))

app = FastAPI()

allow_all = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_all,
    allow_credentials=True,
    allow_methods=allow_all,
    allow_headers=allow_all,
)

REQUEST_COUNTER = Counter(
    "my_failures", "Description of counter", ["endpoint", "http_verb"]
)
CONFIGURATION = to_config(AppConfig)
models.Base.metadata.create_all(bind=engine)
start_http_server(8002)


# Dependency
def get_db():
    """Attempt to get database to operate."""
    database = SessionLocal()
    try:
        yield database
    finally:
        database.close()


def add_user_database(database: Session, user: schemas.User):
    """Create new user in the database based on id and user details."""
    db_user = crud.get_user(database, user_id=user.id)
    if db_user:
        raise HTTPException(status_code=400, detail="User already present")
    return crud.create_user(database=database, user=user)


@app.post("/users/login")
async def login(request: Request):
    """Log in to Firebase with email, password. Return token if successful."""
    req_json = await request.json()
    email = req_json["email"]
    password = req_json["password"]
    try:
        pb.auth().sign_in_with_email_and_password(email, password)
    except Exception as login_exception:
        msg = "Error logging in"
        raise HTTPException(detail=msg, status_code=400) from login_exception
    user_id = auth.get_user_by_email(email).uid
    data = {"id": user_id, "role": "admin"}
    encoded = jwt.encode(data, "secret", algorithm="HS256")
    body = {"token": encoded, "id": user_id}
    return JSONResponse(content=body, status_code=200)


@app.post("/users")
async def create_new_user(new: schemas.UserCreate,
                          database: Session = Depends(get_db)):
    """Create new user in Firebase, add it to the database if successful."""
    if new.email is None or new.password is None:
        raise HTTPException(
            detail={"message": "Missing email or password"}, status_code=400
        )
    try:
        user = auth.create_user(email=new.email, password=new.password)
        details = {"id": user.uid} | new.dict()
        return add_user_database(database, schemas.User(**details))
    except Exception as login_exception:
        msg = "Error creating user"
        raise HTTPException(detail=msg, status_code=400) from login_exception


@app.get("/users/{user_id}")
async def user_details(user_id: str, database: Session = Depends(get_db)):
    """Retrieve details for users with specified id."""
    db_user = crud.get_user(database, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


# Only meant for testing right now
@app.delete("/users", include_in_schema=False)
async def delete_user(email: str, database: Session = Depends(get_db)):
    """Delete users with specified email and password."""
    new_user = auth.get_user_by_email(email)
    db_user = crud.get_user(database, user_id=new_user.uid)
    if db_user is None:
        return
    auth.delete_user(new_user.uid)
    crud.delete_user(database, user_id=new_user.uid)


@app.get("/users/")
async def get_all_users(database: Session = Depends(get_db)):
    """Retrieve details for all users currently present in the database."""
    return crud.get_all_users(database=database)
