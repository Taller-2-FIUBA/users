"""Handles database connection."""
from sqlalchemy import URL
from sqlalchemy.orm import Session

from users.config import AppConfig


def get_database_url(config: AppConfig) -> URL:
    """Return connection parameters."""
    return URL.create(
        drivername=config.db.driver,
        username=config.db.user,
        password=config.db.password,
        host=config.db.host,
        port=config.db.port,
        database=config.db.database,
    )


def get_db(engine) -> Session:
    """Create a session."""
    return Session(autocommit=False, autoflush=False, bind=engine)
