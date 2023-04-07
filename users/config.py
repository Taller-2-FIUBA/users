"""Application configuration."""
from environ import config, var


@config(prefix="USERS")
class AppConfig:
    """Application configuration values from environment."""

    log_level = var("WARNING")
    prometheus_port = var(9001, converter=int)
