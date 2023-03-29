from fastapi import FastAPI, Path, HTTPException, Depends, Request
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

app = FastAPI()


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/new-signup/", include_in_schema=False)
def signup(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user(db, id=user.id)
    if db_user:
        raise HTTPException(status_code=400, detail="User already present")
    return crud.create_user(db=db, user=user)


@app.get("/user-details/", include_in_schema=False)
def get_user(request: Request, db: Session = Depends(get_db)):
    db_user = crud.get_user(db, id=request.headers.get("id"))
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@app.get("/get-all-users/")
def get_all_users(db: Session = Depends(get_db)):
    return crud.get_all_users(db=db)
