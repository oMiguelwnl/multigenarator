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
from alembic.script import ScriptDirectory
from sqlalchemy import JSON, MetaData, Table, create_engine, inspect, select

from multilang.db.base import Base
from multilang.db.provisioning import ensure_database_schema, find_project_root

# Import the models module so every table is registered on Base.metadata.
from multilang.db import models as _models  # noqa: F401

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_KOREAN_IDENTITY_REVISION = "20260804_17"


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


def test_card_exports_mandarin_columns_are_migrated(tmp_path: Path) -> None:
    engine = create_engine(_migrate(tmp_path, "mandarin_parity.db"))
    try:
        columns = {column["name"] for column in inspect(engine).get_columns("card_exports")}
    finally:
        engine.dispose()

    assert {
        "mandarin_word_pinyin",
        "mandarin_word_traditional",
        "mandarin_sentence_pinyin",
        "mandarin_sentence_traditional",
    } <= columns


def test_korean_identity_revision_is_the_sole_linear_head() -> None:
    heads = ScriptDirectory.from_config(_alembic_config("sqlite://")).get_heads()

    assert heads == [_KOREAN_IDENTITY_REVISION]


def test_korean_identity_column_upgrade_downgrade_and_reupgrade(tmp_path: Path) -> None:
    migration_path = (
        _PROJECT_ROOT
        / "alembic"
        / "versions"
        / "20260804_17_korean_lexical_identity.py"
    )
    assert migration_path.is_file()
    database_url = f"sqlite:///{tmp_path / 'korean_identity_migration.db'}"
    config = _alembic_config(database_url)
    command.upgrade(config, "20260804_16")

    engine = create_engine(database_url)
    try:
        legacy_metadata = MetaData()
        legacy_candidates = Table(
            "lexical_candidates",
            legacy_metadata,
            autoload_with=engine,
        )
        assert "korean_identity" not in legacy_candidates.c
        with engine.begin() as connection:
            connection.execute(
                legacy_candidates.insert().values(
                    id="fixture-legacy-candidate",
                    job_id="fixture-legacy-job",
                    run_key="fixture-legacy-run",
                    item_key="fixture-legacy-item",
                    source_type="word-list",
                    submitted_form="fixture",
                    normalized_source="fixture",
                    display_form="fixture",
                    lemma="fixture",
                    lemma_key="en:fixture",
                    definition_language="en",
                    translation_target_language="en",
                    grounding_status="grounded",
                    provenance={},
                )
            )
    finally:
        engine.dispose()

    command.upgrade(config, _KOREAN_IDENTITY_REVISION)
    engine = create_engine(database_url)
    try:
        columns = {
            column["name"]: column
            for column in inspect(engine).get_columns("lexical_candidates")
        }
        assert columns["korean_identity"]["nullable"] is True
        assert isinstance(columns["korean_identity"]["type"], JSON)
        upgraded_metadata = MetaData()
        upgraded_candidates = Table(
            "lexical_candidates",
            upgraded_metadata,
            autoload_with=engine,
        )
        with engine.connect() as connection:
            legacy_value = connection.scalar(
                select(upgraded_candidates.c.korean_identity).where(
                    upgraded_candidates.c.id == "fixture-legacy-candidate"
                )
            )
        assert legacy_value is None
    finally:
        engine.dispose()

    command.downgrade(config, "20260804_16")
    engine = create_engine(database_url)
    try:
        downgraded_columns = {
            column["name"]
            for column in inspect(engine).get_columns("lexical_candidates")
        }
        assert "korean_identity" not in downgraded_columns
    finally:
        engine.dispose()

    command.upgrade(config, _KOREAN_IDENTITY_REVISION)
    engine = create_engine(database_url)
    try:
        restored_columns = {
            column["name"]: column
            for column in inspect(engine).get_columns("lexical_candidates")
        }
        assert restored_columns["korean_identity"]["nullable"] is True
        assert isinstance(restored_columns["korean_identity"]["type"], JSON)
    finally:
        engine.dispose()


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
