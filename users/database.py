"""Handles database connection."""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

POSTGRES_URL = "postgresql://postgres:postgres@user_db:5432/postgres"
SQLALCHEMY_DATABASE_URL = POSTGRES_URL

engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
