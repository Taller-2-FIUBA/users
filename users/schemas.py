from pydantic import BaseModel

class UserBase(BaseModel):
    email: str
    name: str
    surname: str

class UserCreate(UserBase):
    id: str

class User(UserBase):
    pass

    class Config:
        orm_mode = True
