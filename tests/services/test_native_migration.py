from pathlib import Path

import pytest
from sqlalchemy import create_engine, inspect, text

from alembic import command
from multilang.services.native_migration import (
    BackupService,
    MigrationService,
    database_fingerprint,
    native_alembic_config,
)


def database(path: Path):
    engine = create_engine(f"sqlite:///{path}")
    command.upgrade(native_alembic_config(engine), "20260913_21")
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO generation_jobs (id,run_key,language,source_type,source_fingerprint,status,current_stage,resume_state) VALUES ('existing','keep','en','frequency','abc','completed','export','{}')"
            )
        )
    return engine


def test_native_migration_requires_explicit_backup_and_authorization(tmp_path):
    engine = database(tmp_path / "source.db")
    try:
        with pytest.raises(ValueError, match="authorization|preview"):
            command.upgrade(native_alembic_config(engine), "head")
        assert "lexical_identities" not in inspect(engine).get_table_names()
    finally:
        engine.dispose()


def test_snapshot_restore_rehearsal_roundtrip_preserves_legacy_rows(tmp_path):
    engine = database(tmp_path / "source.db")
    try:
        with engine.begin() as connection:
            connection.execute(text(
                "INSERT INTO generation_leases "
                "(scope_key,job_id,token,expires_at,inflight_item_sha256) "
                "VALUES ('job:existing','existing','preserved-token',1,:digest)"
            ), {"digest": "a" * 64})
        before = database_fingerprint(engine)
        backup = BackupService(engine).snapshot(tmp_path / "backup")
        assert BackupService(engine).verify(backup)
        result = MigrationService(engine).rehearse(backup, tmp_path / "clone.db")
        assert result["upgrade_passed"] and result["rollback_passed"]
        assert result["legacy_rows_preserved"]
        assert database_fingerprint(engine) == before
        assert "lexical_identities" not in inspect(engine).get_table_names()
        clone = create_engine(f"sqlite:///{tmp_path / 'clone.db'}")
        try:
            assert "lexical_identities" not in inspect(clone).get_table_names()
            with clone.connect() as connection:
                assert list(connection.scalars(text("SELECT version_num FROM alembic_version"))) == ["20260913_21"]
                assert connection.scalar(text("SELECT inflight_item_sha256 FROM generation_leases")) == "a" * 64
        finally:
            clone.dispose()
    finally:
        engine.dispose()


def test_native_preview_binds_the_lease_and_merge_migrations(tmp_path, monkeypatch):
    import multilang.services.native_migration as migration_module

    engine = create_engine(f"sqlite:///{tmp_path / 'source.db'}")
    try:
        backup = migration_module.BackupManifest(
            backend="sqlite", artifact_path=str(tmp_path / "snapshot.db"),
            artifact_sha256="a" * 64, database_sha256="b" * 64,
            legacy_sha256="c" * 64, source_locator_sha256="d" * 64,
        )
        service = MigrationService(engine)
        original_hash = migration_module.file_sha256
        baseline = service._preview_contract(backup, topology=None, rehearsal=None).target_sha256
        for migration_name in (
            "20260912_20_native_architecture.py",
            "20260913_21_generation_leases.py",
            "20260914_22_merge_native_and_generation_leases.py",
        ):
            monkeypatch.setattr(
                migration_module,
                "file_sha256",
                lambda path, changed=migration_name: (
                    "f" * 64 if Path(path).name == changed else original_hash(path)
                ),
            )
            assert service._preview_contract(backup, topology=None, rehearsal=None).target_sha256 != baseline
    finally:
        engine.dispose()


def test_backup_corruption_and_live_drift_block_apply(tmp_path):
    engine = database(tmp_path / "source.db")
    try:
        backup = BackupService(engine).snapshot(tmp_path / "backup")
        with engine.begin() as connection:
            connection.execute(
                text("UPDATE generation_jobs SET status='pending' WHERE id='existing'")
            )
        with pytest.raises(ValueError, match="drift"):
            MigrationService(engine).preview(backup)
        Path(backup.artifact_path).write_bytes(b"broken")
        with pytest.raises(ValueError, match="backup"):
            BackupService(engine).verify(backup)
    finally:
        engine.dispose()


def test_fingerprint_detects_constraints_even_when_rows_and_columns_match():
    engine = create_engine("sqlite://")
    try:
        with engine.begin() as connection:
            connection.execute(text("CREATE TABLE sample (id INTEGER PRIMARY KEY, value TEXT)"))
            connection.execute(text("INSERT INTO sample VALUES (1, 'keep')"))
        before = database_fingerprint(engine)
        with engine.begin() as connection:
            connection.execute(text("CREATE UNIQUE INDEX sample_unique ON sample(value)"))
        assert database_fingerprint(engine) != before
    finally:
        engine.dispose()


_POSTGRES_DUMP_RESTORE_CHECK_PAIRS = (
    (
        "state::text = ANY (ARRAY['reserved'::character varying, 'staged'::character varying, 'published'::character varying, 'finalized'::character varying, 'failed_unknown'::character varying, 'blocked_mismatch'::character varying]::text[])",
        "state::text = ANY (ARRAY['reserved'::character varying::text, 'staged'::character varying::text, 'published'::character varying::text, 'finalized'::character varying::text, 'failed_unknown'::character varying::text, 'blocked_mismatch'::character varying::text])",
    ),
    (
        "terminal_status::text = ANY (ARRAY['accepted'::character varying, 'review_required'::character varying, 'failed'::character varying]::text[])",
        "terminal_status::text = ANY (ARRAY['accepted'::character varying::text, 'review_required'::character varying::text, 'failed'::character varying::text])",
    ),
    (
        "status::text = ANY (ARRAY['draft'::character varying, 'active'::character varying, 'retired'::character varying]::text[])",
        "status::text = ANY (ARRAY['draft'::character varying::text, 'active'::character varying::text, 'retired'::character varying::text])",
    ),
    (
        "decision_state::text = ANY (ARRAY['accepted'::character varying, 'duplicate'::character varying, 'bridge'::character varying, 'defer'::character varying, 'needs_review'::character varying, 'rejected'::character varying]::text[])",
        "decision_state::text = ANY (ARRAY['accepted'::character varying::text, 'duplicate'::character varying::text, 'bridge'::character varying::text, 'defer'::character varying::text, 'needs_review'::character varying::text, 'rejected'::character varying::text])",
    ),
    (
        "idempotency_support::text = ANY (ARRAY['supported'::character varying, 'unsupported'::character varying]::text[])",
        "idempotency_support::text = ANY (ARRAY['supported'::character varying::text, 'unsupported'::character varying::text])",
    ),
    (
        "state::text = ANY (ARRAY['pending'::character varying, 'disclosing'::character varying, 'disclosed'::character varying, 'failed_unknown'::character varying]::text[])",
        "state::text = ANY (ARRAY['pending'::character varying::text, 'disclosing'::character varying::text, 'disclosed'::character varying::text, 'failed_unknown'::character varying::text])",
    ),
    (
        "state::text = ANY (ARRAY['pending'::character varying, 'disclosing'::character varying, 'disclosed'::character varying, 'failed_unknown'::character varying]::text[])",
        "state::text = ANY (ARRAY['pending'::character varying::text, 'disclosing'::character varying::text, 'disclosed'::character varying::text, 'failed_unknown'::character varying::text])",
    ),
    (
        "action::text = ANY (ARRAY['list'::character varying, 'inspect'::character varying, 'private_display'::character varying, 'approve'::character varying, 'reject'::character varying, 'edit'::character varying, 'regenerate'::character varying]::text[])",
        "action::text = ANY (ARRAY['list'::character varying::text, 'inspect'::character varying::text, 'private_display'::character varying::text, 'approve'::character varying::text, 'reject'::character varying::text, 'edit'::character varying::text, 'regenerate'::character varying::text])",
    ),
    (
        "review_status::text = ANY (ARRAY['needs_review'::character varying, 'approved'::character varying, 'rejected'::character varying]::text[])",
        "review_status::text = ANY (ARRAY['needs_review'::character varying::text, 'approved'::character varying::text, 'rejected'::character varying::text])",
    ),
    (
        "review_status::text = ANY (ARRAY['needs_review'::character varying, 'approved'::character varying, 'rejected'::character varying]::text[])",
        "review_status::text = ANY (ARRAY['needs_review'::character varying::text, 'approved'::character varying::text, 'rejected'::character varying::text])",
    ),
)

_POSTGRES_DUMP_RESTORE_CHECK_IDS = (
    "audio_publication_reservations.state",
    "item_terminal_status_events.status",
    "korean_grammar_bundles.status",
    "personal_source_decisions.state",
    "private_context_capabilities.idempotency_support",
    "private_context_capabilities.state",
    "private_disclosure_attempts.state",
    "review_access_events.action",
    "review_current_pointers.status",
    "review_decisions.status",
)


class _CheckInspector:
    def __init__(self, sqltext: str, dialect: str = "postgresql") -> None:
        from types import SimpleNamespace

        self.dialect = SimpleNamespace(name=dialect)
        self._sqltext = sqltext

    def get_table_names(self):
        return ["probe"]

    def get_columns(self, name):
        return [{"name": "state", "type": "VARCHAR(32)", "nullable": True, "default": None}]

    def get_pk_constraint(self, name):
        return {"constrained_columns": []}

    def get_indexes(self, name):
        return []

    def get_unique_constraints(self, name):
        return []

    def get_foreign_keys(self, name):
        return []

    def get_check_constraints(self, name):
        return [{"name": "ck_probe", "sqltext": self._sqltext}]


def _fingerprint_check(monkeypatch, sqltext: str, *, dialect: str = "postgresql") -> str:
    import multilang.services.native_migration as native_migration

    inspector = _CheckInspector(sqltext, dialect)
    monkeypatch.setattr(native_migration, "inspect", lambda _: inspector)
    return native_migration._schema_fingerprint(object())


@pytest.mark.parametrize(
    "source, restored",
    _POSTGRES_DUMP_RESTORE_CHECK_PAIRS,
    ids=_POSTGRES_DUMP_RESTORE_CHECK_IDS,
)
def test_postgres_check_fingerprint_normalizes_observed_dump_restore_pairs(
    monkeypatch, source, restored
):
    assert _fingerprint_check(monkeypatch, source) == _fingerprint_check(monkeypatch, restored)


def test_postgres_check_normalization_respects_quoted_commas_brackets_and_quotes(monkeypatch):
    source = (
        "state::text = ANY (ARRAY['a,b'::character varying, "
        "'it''s ] still one literal'::character varying]::text[])"
    )
    restored = (
        "state::text = ANY (ARRAY['a,b'::character varying::text, "
        "'it''s ] still one literal'::character varying::text])"
    )
    assert _fingerprint_check(monkeypatch, source) == _fingerprint_check(monkeypatch, restored)


@pytest.mark.parametrize(
    "source, different",
    (
        (
            "state::text = ANY (ARRAY['reserved'::character varying]::varchar[])",
            "state::text = ANY (ARRAY['reserved'::character varying::text])",
        ),
        (
            "state::text = ANY (ARRAY[lower('reserved'::character varying)]::text[])",
            "state::text = ANY (ARRAY[lower('reserved'::character varying)::text])",
        ),
        (
            "ARRAY['reserved'::character varying]::text[] = expected",
            "ARRAY['reserved'::character varying::text] = expected",
        ),
        (
            "state::text = ANY (ARRAY['reserved'::text]::text[])",
            "state::text = ANY (ARRAY['reserved'::text])",
        ),
        (
            "state::text = ANY (ARRAY['reserved'::character varying, now()]::text[])",
            "state::text = ANY (ARRAY['reserved'::character varying::text, now()])",
        ),
        (
            "state::text = ANY (ARRAY['reserved'::character varying]::text[])",
            "state::text = ANY (ARRAY['staged'::character varying::text])",
        ),
        (
            "payload = $$ANY (ARRAY['reserved'::character varying]::text[])$$",
            "payload = $$ANY (ARRAY['reserved'::character varying::text])$$",
        ),
        (
            "\"ANY (ARRAY['reserved'::character varying]::text[])\" IS NOT NULL",
            "\"ANY (ARRAY['reserved'::character varying::text])\" IS NOT NULL",
        ),
    ),
)
def test_postgres_check_normalization_preserves_other_expressions_and_types(
    monkeypatch, source, different
):
    assert _fingerprint_check(monkeypatch, source) != _fingerprint_check(monkeypatch, different)


def test_sqlite_check_fingerprint_does_not_apply_postgres_normalization(monkeypatch):
    source, restored = _POSTGRES_DUMP_RESTORE_CHECK_PAIRS[0]
    assert _fingerprint_check(monkeypatch, source, dialect="sqlite") != _fingerprint_check(
        monkeypatch, restored, dialect="sqlite"
    )


def test_postgres_source_identity_ignores_credentials_and_transport_options():
    from types import SimpleNamespace

    from sqlalchemy.engine import make_url

    from multilang.services.native_migration import _locator

    source = SimpleNamespace(
        dialect=SimpleNamespace(name="postgresql"),
        url=make_url("postgresql://reader:secret@dbhost/app?sslmode=require"),
    )
    target = SimpleNamespace(
        dialect=SimpleNamespace(name="postgresql"),
        url=make_url("postgresql://writer:other@dbhost:5432/app?sslmode=verify-full"),
    )
    assert _locator(source) == _locator(target)


def topology():
    """Synthetic structural evidence only; tests inject an isolated verifier."""
    from multilang.domain.anki_semantics import (
        ANKI_CLIENTS,
        ANKI_SCENARIOS,
        TopologyDecision,
        TopologyEvidence,
    )

    return TopologyDecision(
        selected_model="B",
        topology_version="1",
        signer="test-reviewer",
        decision_receipt_sha256="a" * 64,
        nonconcurrent_mechanism="explicit-prerequisite-sequence",
        evidence=tuple(
            TopologyEvidence(
                model=model,
                client=client,
                client_version="fixture",
                scenario=scenario,
                positive_passed=True,
                negative_passed=True,
                artifact_sha256="b" * 64,
                fixture_sha256="c" * 64,
            )
            for model in ("A", "B")
            for client in ANKI_CLIENTS
            for scenario in ANKI_SCENARIOS
        ),
    )


def prepared_migration(engine, tmp_path):
    service = MigrationService(engine)
    backup = BackupService(engine).snapshot(tmp_path / "backup")
    rehearsal = service.rehearse(backup, tmp_path / "clone.db")
    decision = topology()
    preview = service.preview(backup, topology=decision, rehearsal=rehearsal)
    arguments = {
        "confirmation_sha256": preview.confirmation_sha256,
        "topology": decision,
        "topology_verifier": lambda _: True,
        "rehearsal": rehearsal,
        "actor": "test-reviewer",
    }
    return service, backup, preview, arguments


def test_apply_is_idempotent_with_the_same_verified_journal(tmp_path):
    engine = database(tmp_path / "source.db")
    try:
        service, backup, preview, arguments = prepared_migration(engine, tmp_path)
        first = service.apply(preview, backup, **arguments)
        assert service.apply(preview, backup, **arguments) == first
        assert database_fingerprint(engine, exclude_native=True) == backup.legacy_sha256
        arguments["confirmation_sha256"] = "0" * 64
        with pytest.raises(ValueError):
            service.apply(preview, backup, **arguments)
    finally:
        engine.dispose()


def test_native_downgrade_requires_explicit_authorization(tmp_path):
    engine = database(tmp_path / "source.db")
    try:
        service, backup, preview, arguments = prepared_migration(engine, tmp_path)
        service.apply(preview, backup, **arguments)
        before = database_fingerprint(engine)
        with pytest.raises(ValueError, match="authorization|preview"):
            command.downgrade(native_alembic_config(engine), "20260828_19")
        assert database_fingerprint(engine) == before
        assert "lexical_identities" in inspect(engine).get_table_names()
    finally:
        engine.dispose()


def test_failure_in_postflight_rolls_back_schema_and_keeps_legacy(tmp_path, monkeypatch):
    engine = database(tmp_path / "source.db")
    try:
        service, backup, preview, arguments = prepared_migration(engine, tmp_path)

        def fail_postflight(*args, **kwargs):
            raise ValueError("injected postflight failure")

        monkeypatch.setattr(service, "_postflight", fail_postflight)
        with pytest.raises(ValueError, match="injected"):
            service.apply(preview, backup, **arguments)
        assert "lexical_identities" not in inspect(engine).get_table_names()
        assert database_fingerprint(engine) == backup.database_sha256
    finally:
        engine.dispose()


# Full backup/rehearsal/apply/negative-rollback/rollback cycle under CI load.
@pytest.mark.timeout(300)
def test_hash_confirmed_rollback_restores_backup_and_refuses_new_data(tmp_path):
    engine = database(tmp_path / "source.db")
    try:
        service, backup, preview, arguments = prepared_migration(engine, tmp_path)
        result = service.apply(preview, backup, **arguments)
        rollback = service.rollback_preview(backup, result["migration_id"])
        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO user_state(owner_id,key,revision,payload) VALUES ('alice','new',1,'{}')"
                )
            )
        with pytest.raises(ValueError, match="data|drift"):
            service.rollback(
                rollback,
                backup,
                confirmation_sha256=rollback.confirmation_sha256,
                actor="test-reviewer",
            )
        with engine.begin() as connection:
            connection.execute(text("DELETE FROM user_state WHERE owner_id='alice'"))
        refreshed = service.rollback_preview(backup, result["migration_id"])
        service.rollback(
            refreshed,
            backup,
            confirmation_sha256=refreshed.confirmation_sha256,
            actor="test-reviewer",
        )
        assert "lexical_identities" not in inspect(engine).get_table_names()
        assert database_fingerprint(engine) == backup.database_sha256
    finally:
        engine.dispose()


def test_snapshot_assets_are_bounded_checked_and_restored_privately(tmp_path):
    engine = database(tmp_path / "source.db")
    clone = create_engine(f"sqlite:///{tmp_path / 'restored.db'}")
    try:
        settings_file = tmp_path / "settings.toml"
        settings_file.write_text("private_fixture = true", encoding="utf-8")
        backup = BackupService(engine).snapshot(
            tmp_path / "backup", files={"config/settings.toml": settings_file}
        )
        restored = tmp_path / "restored-files"
        BackupService(engine).restore_to(backup, clone, files_destination=restored)
        copied = restored / "config/settings.toml"
        assert copied.read_bytes() == settings_file.read_bytes()
        assert copied.stat().st_mode & 0o777 == 0o600
        with pytest.raises(ValueError):
            BackupService(engine).snapshot(tmp_path / "bad", files={"../escape": settings_file})
        with pytest.raises(ValueError, match="limit"):
            BackupService(engine).snapshot(
                tmp_path / "limited", files={"config": settings_file}, max_file_bytes=1
            )
    finally:
        clone.dispose()
        engine.dispose()


def test_existing_create_all_schema_requires_exact_parity_and_confirmed_adoption(
    tmp_path,
):
    from multilang.db.base import Base

    engine = create_engine(f"sqlite:///{tmp_path / 'unversioned.db'}")
    try:
        Base.metadata.create_all(
            engine,
            tables=[
                table for table in Base.metadata.tables.values() if not table.info.get("native")
            ],
        )
        service = MigrationService(engine)
        backup = BackupService(engine).snapshot(tmp_path / "backup")
        preview = service.adoption_preview(backup)
        with pytest.raises(ValueError, match="confirmation"):
            service.adopt_legacy_schema(preview, backup, confirmation_sha256="0" * 64)
        service.adopt_legacy_schema(
            preview, backup, confirmation_sha256=preview.confirmation_sha256
        )
        with engine.connect() as connection:
            assert (
                connection.scalar(text("SELECT version_num FROM alembic_version")) == "20260913_21"
            )
        assert "lexical_identities" not in inspect(engine).get_table_names()
    finally:
        engine.dispose()


def test_asset_snapshot_changes_the_migration_confirmation(tmp_path):
    engine = database(tmp_path / "source.db")
    try:
        asset = tmp_path / "settings.toml"
        asset.write_text("version = 1")
        first = BackupService(engine).snapshot(tmp_path / "first", files={"settings.toml": asset})
        asset.write_text("version = 2")
        second = BackupService(engine).snapshot(tmp_path / "second", files={"settings.toml": asset})
        assert first.database_sha256 == second.database_sha256
        assert (
            MigrationService(engine).preview(first).confirmation_sha256
            != MigrationService(engine).preview(second).confirmation_sha256
        )
    finally:
        engine.dispose()


def test_postgresql_backup_uses_explicit_engine_connection_and_no_password_argv(
    monkeypatch,
):
    import subprocess

    captured = []
    monkeypatch.setenv("PGHOST", "wrong-host")
    monkeypatch.setenv("PGSERVICE", "wrong-service")
    monkeypatch.setattr(subprocess, "run", lambda args, **kwargs: captured.append((args, kwargs)))
    engine = create_engine(
        "postgresql+psycopg://fixture:fixture-password@db.example:5433/fixture?sslmode=require"
    )
    try:
        BackupService(engine)._pg_tool("pg_dump", ["--format=custom", "--file=/tmp/fixture.dump"])
        args, kwargs = captured[0]
        assert "fixture-password" not in repr(args)
        assert "--host=db.example" in args and "--port=5433" in args and "--dbname=fixture" in args
        assert "PGHOST" not in kwargs["env"] and "PGSERVICE" not in kwargs["env"]
        assert kwargs["env"]["PGPASSWORD"] == "fixture-password"
        assert kwargs["env"]["PGSSLMODE"] == "require"
    finally:
        engine.dispose()
