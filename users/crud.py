from sqlalchemy.orm import Session
from users.models import Users
from users.schemas import User


def create_user(session: Session, user: User):
    """Creates a new user in the users table, using the id as primary key"""
    db_user = Users(id=user.id, email=user.email, username=user.username,
                           name=user.name, surname=user.surname,
                           height=user.height, weight=user.weight,
                           birth_date=user.birth_date, location=user.location,
                           registration_date=user.registration_date)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


def get_user(session: Session, user_id: str):
    """Returns details from a user identified by a certain user id"""
    return session.query(Users).filter(Users.id == user_id).first()


def get_all_users(session: Session):
    """Returns all users currently present in the session"""
    return session.query(Users).all()


def delete_user(session: Session, user_id):
    session.query(Users).filter(Users.id == user_id).delete()
    session.commit()
