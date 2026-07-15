"""Schema provisioning that keeps Alembic as the single source of truth.

The runtime historically bootstrapped the schema with ``Base.metadata.create_all``
regardless of backend, which meant the Alembic migrations were never exercised
on the real (Postgres) path. That let the ORM models and the migrations drift
apart silently — a table could exist in the models but have no migration and
nobody would notice until a migration-based deploy failed at runtime.

This module centralises provisioning:

- **SQLite** (local dev and tests): use ``create_all`` for zero-setup speed.
- **Everything else** (Postgres in production): run ``alembic upgrade head`` so
  the migrations are the authoritative schema definition. A schema-parity test
  guards that every ORM table/column has a corresponding migration.
"""

from __future__ import annotations

from pathlib import Path

from sqlalchemy.engine import Engine

from multilang.db.base import Base

# Import the models module so every table is registered on ``Base.metadata``.
from multilang.db import models as _models  # noqa: F401


class SchemaProvisioningError(RuntimeError):
    """Raised when the schema cannot be provisioned for a non-SQLite backend."""


def find_project_root() -> Path | None:
    """Locate the directory holding ``alembic.ini`` and the ``alembic`` package."""

    for parent in Path(__file__).resolve().parents:
        if (parent / "alembic.ini").is_file() and (parent / "alembic").is_dir():
            return parent
    return None


def _alembic_config(database_url: str, project_root: Path):
    from alembic.config import Config

    config = Config(str(project_root / "alembic.ini"))
    config.set_main_option("script_location", str(project_root / "alembic"))
    config.set_main_option("sqlalchemy.url", database_url)
    return config


def run_migrations(database_url: str) -> None:
    """Upgrade *database_url* to the latest Alembic revision."""

    project_root = find_project_root()
    if project_root is None:
        raise SchemaProvisioningError(
            "Alembic migrations directory not found; run 'alembic upgrade head' "
            "against the target database before starting the service."
        )
    from alembic import command

    command.upgrade(_alembic_config(database_url, project_root), "head")


def ensure_database_schema(engine: Engine, database_url: str) -> None:
    """Provision the schema for *engine* using the correct mechanism per backend.

    SQLite uses ``create_all`` (fast, no external setup). Any other backend is
    migrated with Alembic so the migrations stay the single source of truth.
    """

    if engine.dialect.name == "sqlite":
        Base.metadata.create_all(engine)
        return
    run_migrations(database_url)


__all__ = [
    "SchemaProvisioningError",
    "ensure_database_schema",
    "find_project_root",
    "run_migrations",
]
