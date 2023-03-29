import models
import schemas
from sqlalchemy.orm import Session

def create_user(db: Session, user: schemas.UserCreate):
   db_user = models.users(id=user.id, email=user.email, name=user.name, surname=user.surname)
   db.add(db_user)
   db.commit()
   db.refresh(db_user)
   return db_user

def get_user(db: Session, id: str):
   return db.query(models.users).filter(models.users.id == id).first()

def get_all_users(db: Session):
   return db.query(models.users).all()
