"""Defines table structure for each table in the database."""

from sqlalchemy import Column, String, Integer, \
    Float, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Users(Base):
    """Table structure for user."""

    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String)
    username = Column(String)
    name = Column(String)
    surname = Column(String)
    height = Column(Float)
    weight = Column(Integer)
    birth_date = Column(String)
    location = Column(String)
    registration_date = Column(String)
    is_athlete = Column(Boolean)
    is_blocked = Column(Boolean)


class FollowedUsers(Base):
    """Table structure for user."""

    __tablename__ = "usersFollowed"
    id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    followed_id = Column(Integer, ForeignKey("users.id"), primary_key=True)


class UsersWallets(Base):
    """Table structure for user."""

    __tablename__ = "usersWallets"
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    address = Column(String)
    private_key = Column(String)


class Transactions(Base):
    """Table structure for user."""

    __tablename__ = "transactions"
    sender = Column(String, primary_key=True)
    receiver = Column(String, primary_key=True)
    amount = Column(Float, primary_key=True)
    date = Column(DateTime, primary_key=True)


class Admin(Base):
    """Table structure for admin."""

    __tablename__ = "admin"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String)
    username = Column(String)
