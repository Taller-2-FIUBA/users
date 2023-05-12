# pylint: disable=no-name-in-module
"""Admin DTO."""
from pydantic import BaseModel


class AdminDTO(BaseModel):
    """Admin details."""

    id: int
    username: str
    email: str

    class Config:
        """Required to enable orm."""

        orm_mode = True


class AdminCreationDTO(BaseModel):
    """Data necessary to create an admin."""

    username: str
    password: str
    email: str
