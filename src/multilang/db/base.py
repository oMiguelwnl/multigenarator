"""Shared SQLAlchemy ORM base for Multilang."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all ORM models."""
