"""Real PostgreSQL migration/backup gate; CI supplies two disposable empty databases."""

import os

import pytest
from sqlalchemy import create_engine, inspect, text

from alembic import command
from multilang.services.native_migration import (
    BackupService,
    MigrationService,
    database_fingerprint,
    native_alembic_config,
)


@pytest.mark.timeout(300)
def test_postgresql_native_upgrade_backup_restore_and_downgrade(tmp_path):
    source_url = os.environ.get("MULTILANG_TEST_POSTGRES_SOURCE_URL")
    clone_url = os.environ.get("MULTILANG_TEST_POSTGRES_CLONE_URL")
    if not source_url or not clone_url:
        pytest.skip("requires two disposable PostgreSQL databases (configured in CI)")
    source = create_engine(source_url)
    clone = create_engine(clone_url)
    try:
        assert source.dialect.name == clone.dialect.name == "postgresql"
        assert not inspect(source).get_table_names(), "source must be an empty disposable database"
        assert not inspect(clone).get_table_names(), "clone must be an empty disposable database"
        command.upgrade(native_alembic_config(source), "20260913_21")
        with source.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO generation_jobs "
                    "(id,run_key,language,source_type,source_fingerprint,status,current_stage,resume_state) "
                    "VALUES (:id,:run,'en','frequency','fixture','completed','export','{}')"
                ),
                {"id": "postgres-preserved-job", "run": "postgres-preserved-run"},
            )
        fingerprint = database_fingerprint(source)
        evidence = tmp_path / "operator-evidence.json"
        evidence.write_text('{"fixture": "backup-file"}', encoding="utf-8")
        backup = BackupService(source).snapshot(
            tmp_path / "snapshot", files={"evidence/operator.json": evidence}
        )
        result = MigrationService(source).rehearse(backup, clone_engine=clone)
        assert result["upgrade_passed"]
        assert result["rollback_passed"]
        assert result["legacy_rows_preserved"]
        assert database_fingerprint(source) == fingerprint
        assert database_fingerprint(clone) == fingerprint
        assert "lexical_identities" not in inspect(source).get_table_names()
        with clone.connect() as connection:
            assert (
                connection.scalar(
                    text("SELECT status FROM generation_jobs WHERE id=:id"),
                    {"id": "postgres-preserved-job"},
                )
                == "completed"
            )
    finally:
        source.dispose()
        clone.dispose()
