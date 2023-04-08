from sqlalchemy import Column, String, Integer, Float
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Users(Base):
    """Stores user details: ID, email, username, name, surname, date of birth,
    weight, username, registration date"""
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
