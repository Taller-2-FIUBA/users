from database import Base
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String

class users(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    email = Column(String)
    name = Column(String)
    surname = Column(String)