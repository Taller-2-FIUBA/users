# pylint: disable=no-name-in-module
"""Payment DTO."""
from pydantic import BaseModel


class BalanceBonus(BaseModel):
    """Data necessary to transfer money from contract to user."""

    amount: float
