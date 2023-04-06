from pydantic import BaseModel


class UserBase(BaseModel):

    """Basic user details"""
    email: str
    username: str
    name: str
    surname: str
    height: float
    weight: int
    birth_date: str
    location: str
    registration_date: str


class UserCreate(UserBase):
    """User ID, used for creating new users"""
    password: str


class User(UserBase):
    id: str
    pass
    class Config:
        orm_mode = True
