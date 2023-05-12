"""Defines table structure for each table in the database."""

from sqlalchemy import Column, String, Integer, Float, Boolean
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


class Admin(Base):
    """Table structure for admin."""

    __tablename__ = "admin"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String)
    username = Column(String)
