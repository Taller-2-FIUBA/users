import models
import schemas
from sqlalchemy.orm import Session


def create_user(user_id: str, database: Session, user: schemas.UserBase):
    """Creates a new user in the users table, using the id as primary key"""
    db_user = models.Users(id=user_id, email=user.email, name=user.name, surname=user.surname)
    database.add(db_user)
    database.commit()
    database.refresh(db_user)
    return db_user


def get_user(database: Session, user_id: str):
    """Returns details from a user identified by a certain user id"""
    return database.query(models.Users).filter(models.Users.id == user_id).first()


def get_all_users(database: Session):
    """Returns all users currently present in the database"""
    return database.query(models.Users).all()
