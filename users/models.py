from database import Base
from sqlalchemy import Column, String


class Users(Base):
    """Stores users as ID,email,name,surname"""
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    email = Column(String)
    name = Column(String)
    surname = Column(String)
