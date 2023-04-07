"""Defines table structure for each table in the database."""

from sqlalchemy import Column, String, Integer, Float
from users.database import Base


class Users(Base):
    """Table structure for user."""

    __tablename__ = "users"
    id = Column(String, primary_key=True, index=True)
    email = Column(String)
    username = Column(String)
    name = Column(String)
    surname = Column(String)
    height = Column(Float)
    weight = Column(Integer)
    birth_date = Column(String)
    location = Column(String)
    registration_date = Column(String)
