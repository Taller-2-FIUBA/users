from pydantic import BaseModel


class UserBase(BaseModel):
    """Basic user details"""
    email: str
    name: str
    surname: str


class UserCreate(UserBase):
    """User ID, used for creating new users"""
    id: str


class User(UserBase):
    pass
    class Config:
        orm_mode = True
