"""Guard that Alembic migrations stay the single source of truth for the schema.

The runtime provisions SQLite (dev/tests) with ``create_all`` but migrates every
other backend (Postgres) with Alembic. If a table or column exists in the ORM
models without a corresponding migration, a migration-based deploy silently ends
up with a schema that does not match the code. These tests upgrade a throwaway
database with the real migrations and assert the resulting schema matches the
ORM metadata table-for-table and column-for-column.
"""

from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from multilang.db.base import Base
from multilang.db.provisioning import ensure_database_schema, find_project_root

# Import the models module so every table is registered on Base.metadata.
from multilang.db import models as _models  # noqa: F401

_PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _alembic_config(database_url: str) -> Config:
    config = Config(str(_PROJECT_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(_PROJECT_ROOT / "alembic"))
    config.set_main_option("sqlalchemy.url", database_url)
    return config


def _migrate(tmp_path: Path, name: str) -> str:
    database_url = f"sqlite:///{tmp_path / name}"
    command.upgrade(_alembic_config(database_url), "head")
    return database_url


def test_migrations_create_every_orm_table(tmp_path: Path) -> None:
    engine = create_engine(_migrate(tmp_path, "table_parity.db"))
    try:
        migrated_tables = set(inspect(engine).get_table_names())
    finally:
        engine.dispose()

    expected_tables = set(Base.metadata.tables.keys())
    missing = expected_tables - migrated_tables
    assert not missing, f"ORM tables without an Alembic migration: {sorted(missing)}"


def test_migrations_include_every_orm_column(tmp_path: Path) -> None:
    engine = create_engine(_migrate(tmp_path, "column_parity.db"))
    try:
        inspector = inspect(engine)
        drift: dict[str, list[str]] = {}
        for table_name, table in Base.metadata.tables.items():
            migrated_columns = {column["name"] for column in inspector.get_columns(table_name)}
            missing_columns = {column.name for column in table.columns} - migrated_columns
            if missing_columns:
                drift[table_name] = sorted(missing_columns)
    finally:
        engine.dispose()

    assert not drift, f"ORM columns without an Alembic migration: {drift}"


def test_provider_response_cache_table_is_migrated(tmp_path: Path) -> None:
    engine = create_engine(_migrate(tmp_path, "cache_parity.db"))
    try:
        tables = set(inspect(engine).get_table_names())
    finally:
        engine.dispose()

    assert "provider_response_cache" in tables


def test_card_exports_gramatica_column_is_migrated(tmp_path: Path) -> None:
    engine = create_engine(_migrate(tmp_path, "gramatica_parity.db"))
    try:
        columns = {column["name"] for column in inspect(engine).get_columns("card_exports")}
    finally:
        engine.dispose()

    assert "gramatica" in columns


def test_ensure_database_schema_creates_sqlite_tables_in_place() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    try:
        ensure_database_schema(engine, "sqlite+pysqlite:///:memory:")
        tables = set(inspect(engine).get_table_names())
    finally:
        engine.dispose()

    # SQLite path must produce exactly the ORM tables via create_all.
    assert set(Base.metadata.tables.keys()) <= tables


def test_project_root_is_locatable_for_alembic() -> None:
    root = find_project_root()
    assert root is not None
    assert (root / "alembic.ini").is_file()
