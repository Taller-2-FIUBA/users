"""Handles CRUD database operations."""
from sqlalchemy.orm import Session
from users.models import Users
from users.schemas import User, UserUpdate


def create_user(session: Session, user: User):
    """Create a new user in the users table, using the id as primary key."""
    db_user = Users(id=user.id, email=user.email, username=user.username,
                    name=user.name, surname=user.surname,
                    height=user.height, weight=user.weight,
                    birth_date=user.birth_date, location=user.location,
                    registration_date=user.registration_date,
                    is_athlete=user.is_athlete)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


def get_user_by_id(session: Session, user_id: str):
    """Return details from a user identified by a certain user id."""
    return session.query(Users).filter(Users.id == user_id).first()


def get_user_by_username(session: Session, username: str):
    """Return details from a user identified by a certain username."""
    return session.query(Users).filter(Users.username == username).first()


def get_all_users(session: Session):
    """Return all users currently present in the session."""
    return session.query(Users).all()


def delete_user(session: Session, user_id: str):
    """Delete user with certain id from database."""
    session.query(Users).filter(Users.id == user_id).delete()
    session.commit()


def update_user(session: Session, _id: str, user: UserUpdate):
    """Update an existing user."""
    columns_to_update = {
        col: value for col, value in user.__dict__.items() if value is not None
    }
    session.query(Users)\
        .filter(Users.id == _id)\
        .update(values=columns_to_update)
    session.commit()
