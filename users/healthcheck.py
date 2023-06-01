# pylint: disable=no-name-in-module
"""Health check endpoint."""
from pydantic import BaseModel


class HealthCheckDto(BaseModel):
    """HeathCheck endpoint response model."""

    uptime: float
