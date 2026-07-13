"""Guard that Alembic migrations create every table declared by the ORM models.

The runtime bootstraps the schema with ``Base.metadata.create_all`` (see
``build_runtime_service``), which masks any table that exists in the ORM models
but has no corresponding migration. Deployments that provision via
``alembic upgrade head`` would then be missing that table and fail at runtime.
This test upgrades a throwaway database with the real migrations and asserts the
resulting schema matches the ORM metadata table-for-table.
"""

from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from multilang.db.base import Base

# Import the models module so every table is registered on Base.metadata.
from multilang.db import models as _models  # noqa: F401

_PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _alembic_config(database_url: str) -> Config:
    config = Config(str(_PROJECT_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(_PROJECT_ROOT / "alembic"))
    config.set_main_option("sqlalchemy.url", database_url)
    return config


def test_migrations_create_every_orm_table(tmp_path: Path) -> None:
    database_path = tmp_path / "migration_parity.db"
    database_url = f"sqlite:///{database_path}"

    command.upgrade(_alembic_config(database_url), "head")

    engine = create_engine(database_url)
    try:
        migrated_tables = set(inspect(engine).get_table_names())
    finally:
        engine.dispose()

    expected_tables = set(Base.metadata.tables.keys())
    missing = expected_tables - migrated_tables
    assert not missing, f"ORM tables without an Alembic migration: {sorted(missing)}"


def test_provider_response_cache_table_is_migrated(tmp_path: Path) -> None:
    database_path = tmp_path / "cache_parity.db"
    database_url = f"sqlite:///{database_path}"

    command.upgrade(_alembic_config(database_url), "head")

    engine = create_engine(database_url)
    try:
        tables = set(inspect(engine).get_table_names())
    finally:
        engine.dispose()

    assert "provider_response_cache" in tables
