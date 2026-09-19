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

import pytest
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import JSON, MetaData, Table, create_engine, inspect, select

from alembic import command

# Import the models module so every table is registered on Base.metadata.
from multilang.db import models as _models  # noqa: F401
from multilang.db import native_models as _native_models  # noqa: F401
from multilang.db import task_models as _task_models  # noqa: F401
from multilang.db.base import Base
from multilang.db.provisioning import ensure_database_schema, find_project_root, run_migrations

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_KOREAN_IDENTITY_REVISION = "20260804_17"
_FREQUENCY_TEXT_AUDIO_REVISION = "20260821_18"
_GRAMMAR_PERSONAL_REVISION = "20260828_19"

_FREQUENCY_TEXT_AUDIO_COLUMNS = {
    "generation_jobs": {
        "korean_phase31_pointer_locator_sha256",
        "korean_phase31_pointer_content_sha256",
        "korean_phase31_validation_receipt_sha256",
        "korean_phase31_snapshot_manifest_sha256",
        "korean_phase31_snapshot_root_sha256",
        "korean_frequency_bundle_locator_sha256",
        "korean_frequency_bundle_content_sha256",
        "korean_frequency_authority",
        "korean_provider_policy_sha256",
        "korean_provider_policy",
    },
    "generation_items": {
        "stage_authority_sha256",
        "stage_input_sha256",
        "stage_output_sha256",
        "stage_evidence",
    },
    "lexical_candidates": {
        "frequency_bundle_sha256",
        "frequency_source_sha256",
        "source_review_receipt_sha256",
        "source_review_aggregate_sha256",
        "lexical_evidence",
    },
    "text_quality_records": {
        "candidate_selection_evidence",
        "adaptive_i_plus_one_evidence",
        "provider_review_evidence",
        "text_review_receipt_sha256",
    },
    "audio_assets": {
        "provider_sdk_version",
        "voice_profile_sha256",
        "catalog_receipt_sha256",
        "synthesis_request_sha256",
        "artifact_sha256",
        "audio_review_status",
        "audio_review_receipt_sha256",
        "heard_review_receipt_sha256",
        "fallback_origin",
        "rejection_reason_code",
    },
    "card_exports": {
        "frequency_level",
        "frequency_bundle_sha256",
        "export_gate_receipt_sha256",
    },
    "deck_exports": {
        "frequency_bundle_sha256",
        "export_manifest_sha256",
        "export_gate_receipt_sha256",
    },
    "provider_call_logs": {
        "route_policy_sha256",
        "budget_snapshot_sha256",
        "cache_key_sha256",
        "response_schema_sha256",
    },
}

_HASH_COLUMNS = {
    column
    for columns in _FREQUENCY_TEXT_AUDIO_COLUMNS.values()
    for column in columns
    if column.endswith("_sha256")
}


def _alembic_config(database_url: str) -> Config:
    config = Config(str(_PROJECT_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(_PROJECT_ROOT / "alembic"))
    config.set_main_option("sqlalchemy.url", database_url)
    return config


def _migrate(tmp_path: Path, name: str) -> str:
    database_url = f"sqlite:///{tmp_path / name}"
    config = _alembic_config(database_url)
    config.attributes["explicit_database_url"] = True
    command.upgrade(config, _GRAMMAR_PERSONAL_REVISION)
    from multilang.services.native_migration import BackupService, SchemaAuthorization
    engine = create_engine(database_url)
    try:
        backup = BackupService(engine).snapshot(tmp_path / f"{name}-backup")
        config.attributes["native_authorization"] = SchemaAuthorization(
            backup.source_locator_sha256, backup.snapshot_sha256, "isolated_rehearsal")
        command.upgrade(config, "head")
    finally:
        engine.dispose()
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


def test_generation_lease_branch_has_a_single_native_merge_head() -> None:
    scripts = ScriptDirectory.from_config(_alembic_config("sqlite://"))
    assert scripts.get_heads() == ["20260914_22"]
    assert set(scripts.get_revision("20260914_22").down_revision) == {
        "20260912_20", "20260913_21",
    }
    assert scripts.get_revision("20260913_21").down_revision == _GRAMMAR_PERSONAL_REVISION


def test_frequency_text_audio_schema_has_expected_evidence_columns_without_sensitive_names() -> None:
    forbidden_fragments = ("raw", "private", "path", "prompt", "payload", "credential", "secret", "traceback")

    for table_name, expected_columns in _FREQUENCY_TEXT_AUDIO_COLUMNS.items():
        table = Base.metadata.tables[table_name]
        missing = expected_columns - {column.name for column in table.columns}
        assert not missing, f"{table_name} is missing ORM columns: {sorted(missing)}"
        leaked = {
            column
            for column in expected_columns
            if any(fragment in column for fragment in forbidden_fragments)
        }
        assert not leaked, f"sensitive evidence column names: {sorted(leaked)}"


def test_frequency_text_audio_migration_upgrade_downgrade_and_reupgrade(tmp_path: Path) -> None:
    migration_path = (
        _PROJECT_ROOT
        / "alembic"
        / "versions"
        / "20260821_18_frequency_text_audio_evidence.py"
    )
    assert migration_path.is_file()
    database_url = f"sqlite:///{tmp_path / 'frequency_text_audio_migration.db'}"
    config = _alembic_config(database_url)
    command.upgrade(config, _KOREAN_IDENTITY_REVISION)

    engine = create_engine(database_url)
    try:
        legacy_metadata = MetaData()
        legacy_jobs = Table("generation_jobs", legacy_metadata, autoload_with=engine)
        with engine.begin() as connection:
            connection.execute(
                legacy_jobs.insert().values(
                    id="fixture-legacy-job",
                    run_key="fixture-legacy-run",
                    language="ko",
                    source_type="frequency",
                    source_fingerprint="fixture-source",
                    status="created",
                    current_stage="lexical",
                )
            )
    finally:
        engine.dispose()

    command.upgrade(config, _FREQUENCY_TEXT_AUDIO_REVISION)
    engine = create_engine(database_url)
    try:
        inspector = inspect(engine)
        for table_name, expected_columns in _FREQUENCY_TEXT_AUDIO_COLUMNS.items():
            migrated_columns = {
                column["name"]: column
                for column in inspector.get_columns(table_name)
            }
            missing = expected_columns - set(migrated_columns)
            assert not missing, f"{table_name} migration columns missing: {sorted(missing)}"
            for column_name in expected_columns:
                assert migrated_columns[column_name]["nullable"] is True
                if column_name in _HASH_COLUMNS:
                    assert getattr(migrated_columns[column_name]["type"], "length", None) == 64
        upgraded_metadata = MetaData()
        upgraded_jobs = Table("generation_jobs", upgraded_metadata, autoload_with=engine)
        with engine.connect() as connection:
            row = connection.execute(
                select(
                    upgraded_jobs.c.korean_phase31_pointer_locator_sha256,
                    upgraded_jobs.c.korean_frequency_authority,
                ).where(upgraded_jobs.c.id == "fixture-legacy-job")
            ).one()
        assert row.korean_phase31_pointer_locator_sha256 is None
        assert row.korean_frequency_authority is None
    finally:
        engine.dispose()

    command.downgrade(config, _KOREAN_IDENTITY_REVISION)
    engine = create_engine(database_url)
    try:
        inspector = inspect(engine)
        for table_name, expected_columns in _FREQUENCY_TEXT_AUDIO_COLUMNS.items():
            downgraded_columns = {
                column["name"]
                for column in inspector.get_columns(table_name)
            }
            assert expected_columns.isdisjoint(downgraded_columns)
    finally:
        engine.dispose()

    command.upgrade(config, _FREQUENCY_TEXT_AUDIO_REVISION)
    engine = create_engine(database_url)
    try:
        inspector = inspect(engine)
        for table_name, expected_columns in _FREQUENCY_TEXT_AUDIO_COLUMNS.items():
            restored_columns = {
                column["name"]
                for column in inspector.get_columns(table_name)
            }
            assert expected_columns <= restored_columns
    finally:
        engine.dispose()


def test_frequency_text_audio_domain_evidence_rejects_bad_locator_hashes_and_private_fields() -> None:
    from multilang.domain.korean import KoreanFrequencyTextAudioEvidence

    valid_hash = "a" * 64
    evidence = KoreanFrequencyTextAudioEvidence(
        phase31_pointer_locator_sha256=valid_hash,
        phase31_pointer_content_sha256=valid_hash,
        phase31_validation_receipt_sha256=valid_hash,
        phase31_snapshot_manifest_sha256=valid_hash,
        phase31_snapshot_root_sha256=valid_hash,
        frequency_bundle_locator_sha256=valid_hash,
        frequency_bundle_content_sha256=valid_hash,
        provider_policy_sha256=valid_hash,
    )

    assert evidence.phase31_pointer_locator_sha256 == valid_hash
    with pytest.raises(ValueError):
        KoreanFrequencyTextAudioEvidence(
            phase31_pointer_locator_sha256="A" * 64,
        )
    with pytest.raises(ValueError):
        KoreanFrequencyTextAudioEvidence.model_validate(
            {
                "phase31_pointer_locator_sha256": valid_hash,
                "private_path": "/tmp/secret",
            }
        )


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

    legacy_tables = {table.name for table in Base.metadata.tables.values() if not table.info.get("native")}
    native_tables = {table.name for table in Base.metadata.tables.values() if table.info.get("native")}
    assert legacy_tables <= tables
    assert not native_tables & tables


def test_project_root_is_locatable_for_alembic() -> None:
    root = find_project_root()
    assert root is not None
    assert (root / "alembic.ini").is_file()


def test_unauthorized_merge_downgrade_preserves_both_branches(tmp_path: Path) -> None:
    database_url = _migrate(tmp_path, "merge_downgrade.db")
    engine = create_engine(database_url)
    try:
        from multilang.services.native_migration import database_fingerprint

        before = database_fingerprint(engine)
        config = _alembic_config(database_url)
        config.attributes["explicit_database_url"] = True
        with pytest.raises(ValueError, match="authorization|preview"):
            command.downgrade(config, _GRAMMAR_PERSONAL_REVISION)
        assert database_fingerprint(engine) == before
        assert {"generation_leases", "lexical_identities"} <= set(inspect(engine).get_table_names())
    finally:
        engine.dispose()


def test_legacy_provisioning_migrates_leases_without_authorizing_native_schema(tmp_path: Path) -> None:
    database_url = f"sqlite:///{tmp_path / 'legacy_lease_provisioning.db'}"
    run_migrations(database_url)
    engine = create_engine(database_url)
    try:
        tables = set(inspect(engine).get_table_names())
        assert "generation_leases" in tables
        assert "lexical_identities" not in tables
        metadata = MetaData()
        version = Table("alembic_version", metadata, autoload_with=engine)
        with engine.connect() as connection:
            assert list(connection.scalars(select(version.c.version_num))) == ["20260913_21"]
        config = _alembic_config(database_url)
        config.attributes["explicit_database_url"] = True
        with pytest.raises(ValueError, match="authorization|preview"):
            command.upgrade(config, "head")
        assert "lexical_identities" not in inspect(engine).get_table_names()
    finally:
        engine.dispose()
