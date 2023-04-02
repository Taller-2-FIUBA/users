from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from environ import to_config
from prometheus_client import start_http_server, Counter
from config import AppConfig
import crud
import models
import schemas
from database import SessionLocal, engine

REQUEST_COUNTER = Counter(
    "my_failures", "Description of counter", ["endpoint", "http_verb"]
)
CONFIGURATION = to_config(AppConfig)
models.Base.metadata.create_all(bind=engine)
start_http_server(8002)

app = FastAPI()


# Dependency
def get_db():
    database = SessionLocal()
    try:
        yield database
    finally:
        database.close()


@app.get("/", include_in_schema=False)
async def root():
    """Greet."""
    REQUEST_COUNTER.labels("/", "get").inc()
    return {"message": "Hello World"}


@app.post("/users", include_in_schema=False)
def signup(user: schemas.UserCreate, database: Session = Depends(get_db)):
    """Attempts to create new user in the database based on id and user details.
    Raises exception if user is already present"""
    db_user = crud.get_user(database, user_id=user.id)
    if db_user:
        raise HTTPException(status_code=400, detail="User already present")
    return crud.create_user(user.id, database=database, user=user)


@app.get("/users/{user_id}", include_in_schema=False)
def get_user(user_id: str, database: Session = Depends(get_db)):
    """Retrieves user details from database based on a user id.
    Raises exception if there is no such id"""
    db_user = crud.get_user(database, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@app.get("/users/")
def get_all_users(database: Session = Depends(get_db)):
    """Retrieves all details for users currently present in the database"""
    return crud.get_all_users(database=database)
