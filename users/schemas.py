# pylint: disable=no-name-in-module
"""Defines models for data exchange in API and between modules."""
from typing import Optional
from pydantic import BaseModel


class UserBase(BaseModel):
    """User details."""

    email: str
    username: str
    name: str
    surname: str
    height: float
    weight: int
    birth_date: str
    location: str
    registration_date: str
    is_athlete: bool


class UserUpdate(BaseModel):
    """User details to be updated."""

    username: Optional[str]
    name: Optional[str]
    surname: Optional[str]
    height: Optional[float]
    weight: Optional[int]
    birth_date: Optional[str]
    location: Optional[str]


class UserCreate(UserBase):
    """Required for creating a new user, password + details."""

    password: str


class User(UserBase):
    """User after being created, id + details."""

    id: str

    class Config:
        """Required to enable orm."""

        orm_mode = True
