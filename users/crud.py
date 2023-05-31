"""Handles CRUD database operations."""
import math

from sqlalchemy.orm import Session
from users.models import Users, FollowedUsers
from users.schemas import UserUpdate, UserBase


def create_user(session: Session, user: UserBase):
    """Create a new user in the users table, using the id as primary key."""
    db_user = Users(email=user.email, username=user.username,
                    name=user.name, surname=user.surname,
                    height=user.height, weight=user.weight,
                    birth_date=user.birth_date, location=user.location,
                    registration_date=user.registration_date,
                    is_athlete=user.is_athlete, is_blocked=False)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


def get_user_by_id(session: Session, user_id: int):
    """Return details from a user identified by a certain user id."""
    return session.query(Users).filter(Users.id == user_id).first()


def get_user_by_username(session: Session, username: str):
    """Return details from a user identified by a certain username."""
    user = session.query(Users).filter(Users.username == username).first()
    if user is None:
        return None
    return {
        "name": user.name,
        "surname": user.surname,
        "email": user.email,
        "location": user.location
    }


def get_user_by_email(session: Session, email: str):
    """Return details from a user identified by a certain username."""
    return session.query(Users).filter(Users.email == email).first()


def get_all_users(session: Session, limit: int, offset: int):
    """Return all users currently present in the session with pagination."""
    total = session.query(Users).count()
    items = session.query(Users).limit(limit).offset(offset).all()
    size = len(items)
    pages = math.ceil(total / limit)
    page = 1 + math.ceil(offset / limit)
    return {"items": items, "total": total,
            "page": page, "size": size, "pages": pages}


def change_blocked_status(session: Session, user_id: int):
    """Inverts blocked status for user with provided id."""
    db_user = session.query(Users).filter(Users.id == user_id).first()
    db_user.is_blocked = not db_user.is_blocked
    session.commit()


def update_user(session: Session, _id: int, user: UserUpdate):
    """Update an existing user."""
    columns_to_update = {
        col: value for col, value in user.__dict__.items() if value is not None
    }
    session.query(Users) \
        .filter(Users.id == _id) \
        .update(values=columns_to_update)
    session.commit()


def get_details_with_id(session: Session, user_id: int):
    """Inverts blocked status for user with provided id."""
    user = session.query(Users).filter(Users.id == user_id).first()
    return user.email, user.username


def get_users_followed_by(session: Session, _id: int):
    """Inverts blocked status for user with provided id."""
    vec = []
    users = session.query(FollowedUsers).filter(FollowedUsers.id == _id).all()
    for pair in users:
        vec.append(get_user_by_id(session, pair.followed_id))
    return vec


def follow_new_user(session: Session, user_id: int, _id: int):
    """Add new followed user to specified user."""
    if session.query(FollowedUsers).filter(FollowedUsers.id == user_id,
                                           FollowedUsers.followed_id == _id)\
            .first() is not None:
        return get_users_followed_by(session, user_id)
    new_follow = FollowedUsers(id=user_id, followed_id=_id)
    session.add(new_follow)
    session.commit()
    session.refresh(new_follow)
    return get_users_followed_by(session, user_id)


def unfollow_user(session: Session, user_id: int, _id: int):
    """Unfollow specified user."""
    session.query(FollowedUsers).filter(FollowedUsers.id == user_id,
                                        FollowedUsers.followed_id == _id)\
        .delete()
    session.commit()
    return get_users_followed_by(session, user_id)
