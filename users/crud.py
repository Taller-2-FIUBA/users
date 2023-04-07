"""Handles CRUD database operations."""
from sqlalchemy.orm import Session
from users import models
from users import schemas


def create_user(database: Session, user: schemas.User):
    """Create a new user in the users table, using the id as primary key."""
    db_user = models.Users(
        id=user.id,
        email=user.email,
        username=user.username,
        name=user.name,
        surname=user.surname,
        height=user.height,
        weight=user.weight,
        birth_date=user.birth_date,
        location=user.location,
        registration_date=user.registration_date,
    )
    database.add(db_user)
    database.commit()
    database.refresh(db_user)
    return db_user


def get_user(database: Session, user_id: str):
    """Return details from a user identified by a certain user id."""
    database_query = database.query(models.Users)
    return database_query.filter(models.Users.id == user_id).first()


def get_all_users(database: Session):
    """Return all users currently present in the database."""
    return database.query(models.Users).all()


def delete_user(database, user_id):
    """Delete user with certain id from database."""
    database.query(models.Users).filter(models.Users.id == user_id).delete()
    database.commit()
