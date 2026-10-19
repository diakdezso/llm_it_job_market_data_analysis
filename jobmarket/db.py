"""Database engine, session factory and declarative base."""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql+psycopg://jobmarket:jobmarket@localhost:5432/jobmarket")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


def get_session():
    """FastAPI dependency: one session per request."""
    with SessionLocal() as session:
        yield session
