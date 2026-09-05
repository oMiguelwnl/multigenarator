"""Phase 33 schema invariants for grammar and personal-source persistence."""

from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
import pytest
from sqlalchemy import MetaData, Table, create_engine, inspect, select
from sqlalchemy.exc import IntegrityError

from multilang.db.base import Base

# Import models so SQLAlchemy metadata contains every mapped table.
from multilang.db import models as _models  # noqa: F401


_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_PHASE32_REVISION = "20260821_18"
_PHASE33_REVISION = "20260828_19"
_SHA_A = "a" * 64
_SHA_B = "b" * 64
_SHA_C = "c" * 64
_SHA_D = "d" * 64
_NOT_SHA_HEX = "g" * 64

_PHASE33_TABLE_COLUMNS = {
    "korean_grammar_bundles": {
        "id",
        "bundle_id",
        "bundle_sha256",
        "source_kind",
        "source_sha256",
        "version",
        "status",
        "sequence_count",
    },
    "korean_grammar_members": {
        "id",
        "bundle_id",
        "construction_id",
        "sequence_index",
        "form",
        "function_label",
        "register",
        "prerequisite_ids",
        "member_sha256",
    },
    "personal_source_rows": {
        "id",
        "job_id",
        "item_key",
        "source_type",
        "input_position",
        "submitted_form",
        "normalized_form",
        "source_row_sha256",
        "parser_version",
    },
    "personal_source_decisions": {
        "id",
        "row_id",
        "decision_revision",
        "resolved_lemma",
        "resolved_pos",
        "resolved_sense_id",
        "decision_state",
        "decision_reason_code",
        "korean_identity_sha256",
        "prerequisite_ids",
    },
    "highlight_private_excerpt_revisions": {
        "id",
        "job_id",
        "excerpt_revision_id",
        "highlight_id",
        "import_content_hash",
        "source_content_hash",
        "source_index",
        "source_path",
        "raw_location",
        "normalized_text",
        "revision_number",
    },
    "private_context_capabilities": {
        "id",
        "capability_id",
        "job_id",
        "run_id",
        "item_id",
        "excerpt_revision_id",
        "excerpt_sha256",
        "target_start",
        "target_end",
        "target_text_sha256",
        "provider_id",
        "provider",
        "model",
        "route_id",
        "provider_route_sha256",
        "purpose",
        "policy_version",
        "policy_sha256",
        "tokenization_rule_id",
        "max_context_tokens",
        "max_provider_attempts",
        "idempotency_support",
        "idempotency_key_sha256",
        "state",
        "version",
    },
    "private_disclosure_attempts": {
        "id",
        "capability_id",
        "state",
        "version",
        "context_sha256",
        "context_token_count",
        "refusal_reason_code",
        "attempted_at",
        "processed_at",
    },
    "private_processing_receipts": {
        "id",
        "receipt_id",
        "capability_id",
        "receipt_sha256",
        "context_sha256",
        "context_token_count",
        "provider",
        "model",
        "route_id",
        "policy_sha256",
    },
    "review_field_revisions": {
        "id",
        "job_id",
        "item_id",
        "field_name",
        "revision_no",
        "value_sha256",
        "generator_id",
        "generator_version",
        "route_id",
        "previous_revision_sha256",
    },
    "review_current_pointers": {
        "id",
        "job_id",
        "item_id",
        "field_name",
        "current_revision_id",
        "pointer_version",
        "review_status",
    },
    "review_decisions": {
        "id",
        "job_id",
        "item_id",
        "field_name",
        "revision_id",
        "decision_revision",
        "review_status",
        "reviewer_id_sha256",
        "decision_sha256",
        "reason_code",
    },
    "review_access_events": {
        "id",
        "actor_id",
        "request_id",
        "action",
        "command_sha256",
        "result_id_sha256",
        "result_hash_count",
        "policy_sha256",
        "snapshot_sha256",
    },
    "item_terminal_status_events": {
        "id",
        "job_id",
        "item_id",
        "stage",
        "terminal_status",
        "reason_code",
        "event_sha256",
    },
    "item_processing_facts": {
        "id",
        "job_id",
        "item_id",
        "stage",
        "attempt_count",
        "attempted_at",
        "processed_at",
        "fact_sha256",
    },
    "generation_run_denominators": {
        "id",
        "job_id",
        "stage",
        "expected_count",
        "accepted_count",
        "review_required_count",
        "failed_count",
        "denominator_sha256",
    },
    "audio_publication_reservations": {
        "id",
        "job_id",
        "item_id",
        "field_name",
        "field_revision_id",
        "request_sha256",
        "final_path",
        "final_path_sha256",
        "authority_sha256",
        "root_prestate_sha256",
        "expected_pointer_version",
        "reservation_version",
        "state",
    },
    "audio_publication_transitions": {
        "id",
        "reservation_id",
        "from_state",
        "to_state",
        "expected_version",
        "next_version",
        "transition_sha256",
    },
    "audio_revision_evidence": {
        "id",
        "reservation_id",
        "field_revision_id",
        "role",
        "root_sha256",
        "final_path_sha256",
        "request_sha256",
        "artifact_sha256",
        "byte_length",
        "spoken_text_sha256",
        "voice_profile_sha256",
        "review_status",
        "reservation_state",
        "evidence_sha256",
    },
}


def _alembic_config(database_url: str) -> Config:
    config = Config(str(_PROJECT_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(_PROJECT_ROOT / "alembic"))
    config.set_main_option("sqlalchemy.url", database_url)
    return config


def _migrate(tmp_path: Path, name: str, revision: str = "head") -> str:
    database_url = f"sqlite:///{tmp_path / name}"
    command.upgrade(_alembic_config(database_url), revision)
    return database_url


def _table(engine, name: str) -> Table:
    metadata = MetaData()
    return Table(name, metadata, autoload_with=engine)


def _insert_job(connection) -> None:
    jobs = _table(connection.engine, "generation_jobs")
    connection.execute(
        jobs.insert().values(
            id="job-33",
            run_key="run-33",
            language="ko",
            source_type="kindle-highlights",
            source_fingerprint="fixture-source",
            status="created",
            current_stage="generate_text",
        )
    )


def test_phase33_tables_indexes_constraints_and_private_column_boundary(tmp_path: Path) -> None:
    engine = create_engine(_migrate(tmp_path, "phase33_inventory.db"))
    try:
        inspector = inspect(engine)
        tables = set(inspector.get_table_names())
        assert set(_PHASE33_TABLE_COLUMNS) <= tables

        for table_name, expected_columns in _PHASE33_TABLE_COLUMNS.items():
            columns = {column["name"]: column for column in inspector.get_columns(table_name)}
            missing = expected_columns - set(columns)
            assert not missing, f"{table_name} missing columns: {sorted(missing)}"

        phase33_private_tables = {"highlight_private_excerpt_revisions"}
        private_column_names = {"normalized_text", "source_path", "raw_location", "excerpt_text", "prompt", "payload"}
        leaked = {
            (table_name, column_name)
            for table_name in _PHASE33_TABLE_COLUMNS
            for column_name in {column["name"] for column in inspector.get_columns(table_name)}
            if table_name not in phase33_private_tables and column_name in private_column_names
        }
        assert not leaked

        indexes = {
            table_name: {index["name"] for index in inspector.get_indexes(table_name)}
            for table_name in _PHASE33_TABLE_COLUMNS
        }
        assert "ix_personal_source_rows_job_id_item_key" in indexes["personal_source_rows"]
        assert "ix_private_context_capabilities_item_state" in indexes["private_context_capabilities"]
        assert "ix_review_current_pointers_item_field" in indexes["review_current_pointers"]
        assert "ix_item_terminal_status_events_status_job" in indexes["item_terminal_status_events"]
        assert "ix_audio_publication_reservations_item_field" in indexes["audio_publication_reservations"]
    finally:
        engine.dispose()


def test_phase33_access_stable_unique_and_command_sha256_conflict(tmp_path: Path) -> None:
    engine = create_engine(_migrate(tmp_path, "phase33_access.db"))
    try:
        access = _table(engine, "review_access_events")
        with engine.begin() as connection:
            connection.execute(
                access.insert().values(
                    id="access-1",
                    actor_id="actor-1",
                    request_id="request-1",
                    action="list",
                    command_sha256=_SHA_A,
                    result_id_sha256=_SHA_B,
                    result_hash_count=1,
                    policy_sha256=_SHA_C,
                    snapshot_sha256=_SHA_D,
                )
            )
            with pytest.raises(IntegrityError):
                connection.execute(
                    access.insert().values(
                        id="access-2",
                        actor_id="actor-1",
                        request_id="request-1",
                        action="list",
                        command_sha256=_SHA_B,
                        result_id_sha256=_SHA_B,
                        result_hash_count=1,
                        policy_sha256=_SHA_C,
                        snapshot_sha256=_SHA_D,
                    )
                )
    finally:
        engine.dispose()


def test_phase33_sha256_checks_reject_non_hex_lowercase_values(tmp_path: Path) -> None:
    engine = create_engine(_migrate(tmp_path, "phase33_hash_checks.db"))
    try:
        access = _table(engine, "review_access_events")
        with engine.begin() as connection:
            with pytest.raises(IntegrityError):
                connection.execute(
                    access.insert().values(
                        id="access-bad-hash",
                        actor_id="actor-1",
                        request_id="request-1",
                        action="private_display",
                        command_sha256=_NOT_SHA_HEX,
                        result_id_sha256=_SHA_B,
                        result_hash_count=1,
                        policy_sha256=_SHA_C,
                        snapshot_sha256=_SHA_D,
                    )
                )
    finally:
        engine.dispose()


def test_phase33_audio_publication_reservation_and_artifact_constraints(tmp_path: Path) -> None:
    engine = create_engine(_migrate(tmp_path, "phase33_audio.db"))
    try:
        field_revisions = _table(engine, "review_field_revisions")
        reservations = _table(engine, "audio_publication_reservations")
        evidence = _table(engine, "audio_revision_evidence")
        with engine.begin() as connection:
            _insert_job(connection)
            connection.execute(
                field_revisions.insert(),
                [
                    {
                        "id": "field-rev-1",
                        "job_id": "job-33",
                        "item_id": "item-1",
                        "field_name": "sentence_audio",
                        "revision_no": 1,
                        "value_sha256": _SHA_A,
                        "generator_id": "provider",
                        "generator_version": "v1",
                    },
                    {
                        "id": "field-rev-2",
                        "job_id": "job-33",
                        "item_id": "item-2",
                        "field_name": "sentence_audio",
                        "revision_no": 1,
                        "value_sha256": _SHA_B,
                        "generator_id": "provider",
                        "generator_version": "v1",
                    },
                ],
            )
            connection.execute(
                reservations.insert(),
                [
                    _reservation_values("reservation-1", "item-1", "field-rev-1", _SHA_A),
                    _reservation_values("reservation-2", "item-2", "field-rev-2", _SHA_B),
                ],
            )
            with pytest.raises(IntegrityError):
                connection.execute(
                    reservations.insert().values(
                        _reservation_values("reservation-dup-revision", "item-1", "field-rev-1", _SHA_C)
                    )
                )
            with pytest.raises(IntegrityError):
                connection.execute(
                    reservations.insert().values(
                        _reservation_values("reservation-dup-path", "item-3", "field-rev-3", _SHA_A)
                    )
                )
            connection.execute(
                evidence.insert(),
                [
                    _audio_evidence_values("evidence-1", "reservation-1", "field-rev-1", _SHA_A),
                    _audio_evidence_values("evidence-2", "reservation-2", "field-rev-2", _SHA_B),
                ],
            )
            artifact_hashes = connection.execute(select(evidence.c.artifact_sha256)).all()
        assert [row.artifact_sha256 for row in artifact_hashes] == [_SHA_C, _SHA_C]
    finally:
        engine.dispose()


def test_phase33_reservation_transition_finalize_requires_published_state(tmp_path: Path) -> None:
    engine = create_engine(_migrate(tmp_path, "phase33_transitions.db"))
    try:
        transitions = _table(engine, "audio_publication_transitions")
        evidence = _table(engine, "audio_revision_evidence")
        with engine.begin() as connection:
            _seed_audio_reservation(connection)
            connection.execute(
                transitions.insert().values(
                    id="transition-1",
                    reservation_id="reservation-1",
                    from_state="reserved",
                    to_state="staged",
                    expected_version=0,
                    next_version=1,
                    transition_sha256=_SHA_A,
                )
            )
            with pytest.raises(IntegrityError):
                connection.execute(
                    transitions.insert().values(
                        id="transition-bad",
                        reservation_id="reservation-1",
                        from_state="reserved",
                        to_state="finalized",
                        expected_version=0,
                        next_version=1,
                        transition_sha256=_SHA_B,
                    )
                )
            with pytest.raises(IntegrityError):
                connection.execute(
                    evidence.insert().values(
                        _audio_evidence_values(
                            "evidence-bad",
                            "reservation-1",
                            "field-rev-1",
                            _SHA_A,
                            reservation_state="published",
                        )
                    )
                )
    finally:
        engine.dispose()


def test_phase33_append_only_guards_reject_update_and_delete(tmp_path: Path) -> None:
    engine = create_engine(_migrate(tmp_path, "phase33_append_only.db"))
    try:
        field_revisions = _table(engine, "review_field_revisions")
        attempts = _table(engine, "private_disclosure_attempts")
        capabilities = _table(engine, "private_context_capabilities")
        with engine.begin() as connection:
            _insert_job(connection)
            connection.execute(
                field_revisions.insert().values(
                    id="field-rev-1",
                    job_id="job-33",
                    item_id="item-1",
                    field_name="sentence",
                    revision_no=1,
                    value_sha256=_SHA_A,
                    generator_id="provider",
                    generator_version="v1",
                )
            )
            connection.execute(capabilities.insert().values(_capability_values()))
            connection.execute(
                attempts.insert().values(
                    id="attempt-1",
                    capability_id="cap-1",
                    state="pending",
                    version=0,
                )
            )
            with pytest.raises(IntegrityError):
                connection.execute(
                    field_revisions.update().where(field_revisions.c.id == "field-rev-1").values(value_sha256=_SHA_B)
                )
            with pytest.raises(IntegrityError):
                connection.execute(attempts.delete().where(attempts.c.id == "attempt-1"))
    finally:
        engine.dispose()


def test_phase33_orm_metadata_matches_migration_and_legacy_tables_stay_unchanged(tmp_path: Path) -> None:
    engine = create_engine(_migrate(tmp_path, "phase33_orm.db"))
    try:
        inspector = inspect(engine)
        for table_name, expected_columns in _PHASE33_TABLE_COLUMNS.items():
            assert table_name in Base.metadata.tables
            orm_columns = {column.name for column in Base.metadata.tables[table_name].columns}
            migrated_columns = {column["name"] for column in inspector.get_columns(table_name)}
            assert expected_columns <= orm_columns
            assert orm_columns <= migrated_columns

        legacy_items_columns = {column["name"] for column in inspector.get_columns("generation_items")}
        assert {"stage_authority_sha256", "stage_input_sha256", "stage_output_sha256"} <= legacy_items_columns
    finally:
        engine.dispose()


def test_phase33_schema_upgrades_to_one_head_and_round_trips(tmp_path: Path) -> None:
    migration_path = _PROJECT_ROOT / "alembic" / "versions" / "20260828_19_grammar_personal_sources.py"
    assert migration_path.is_file()

    database_url = f"sqlite:///{tmp_path / 'phase33_round_trip.db'}"
    config = _alembic_config(database_url)
    command.upgrade(config, _PHASE32_REVISION)
    engine = create_engine(database_url)
    try:
        assert "review_field_revisions" not in set(inspect(engine).get_table_names())
    finally:
        engine.dispose()

    command.upgrade(config, _PHASE33_REVISION)
    engine = create_engine(database_url)
    try:
        assert set(_PHASE33_TABLE_COLUMNS) <= set(inspect(engine).get_table_names())
    finally:
        engine.dispose()

    command.downgrade(config, _PHASE32_REVISION)
    engine = create_engine(database_url)
    try:
        assert set(_PHASE33_TABLE_COLUMNS).isdisjoint(set(inspect(engine).get_table_names()))
    finally:
        engine.dispose()

    command.upgrade(config, _PHASE33_REVISION)
    engine = create_engine(database_url)
    try:
        assert set(_PHASE33_TABLE_COLUMNS) <= set(inspect(engine).get_table_names())
    finally:
        engine.dispose()


def test_phase33_revision_is_the_sole_linear_head() -> None:
    heads = ScriptDirectory.from_config(_alembic_config("sqlite://")).get_heads()

    assert heads == [_PHASE33_REVISION]


def _reservation_values(
    reservation_id: str,
    item_id: str,
    field_revision_id: str,
    final_path_sha256: str,
) -> dict[str, object]:
    return {
        "id": reservation_id,
        "job_id": "job-33",
        "item_id": item_id,
        "field_name": "sentence_audio",
        "field_revision_id": field_revision_id,
        "request_sha256": _SHA_A,
        "final_path": f"audio/{final_path_sha256}.mp3",
        "final_path_sha256": final_path_sha256,
        "authority_sha256": _SHA_B,
        "root_prestate_sha256": _SHA_C,
        "expected_pointer_version": 0,
        "reservation_version": 0,
        "state": "reserved",
    }


def _audio_evidence_values(
    evidence_id: str,
    reservation_id: str,
    field_revision_id: str,
    final_path_sha256: str,
    *,
    reservation_state: str = "finalized",
) -> dict[str, object]:
    return {
        "id": evidence_id,
        "reservation_id": reservation_id,
        "field_revision_id": field_revision_id,
        "role": "sentence_audio",
        "root_sha256": _SHA_A,
        "final_path_sha256": final_path_sha256,
        "request_sha256": _SHA_B,
        "artifact_sha256": _SHA_C,
        "byte_length": 123,
        "spoken_text_sha256": _SHA_D,
        "voice_profile_sha256": _SHA_A,
        "review_status": "approved",
        "reservation_state": reservation_state,
        "evidence_sha256": ("e" if evidence_id.endswith("1") else "f") * 64,
    }


def _seed_audio_reservation(connection) -> None:
    field_revisions = _table(connection.engine, "review_field_revisions")
    reservations = _table(connection.engine, "audio_publication_reservations")
    _insert_job(connection)
    connection.execute(
        field_revisions.insert().values(
            id="field-rev-1",
            job_id="job-33",
            item_id="item-1",
            field_name="sentence_audio",
            revision_no=1,
            value_sha256=_SHA_A,
            generator_id="provider",
            generator_version="v1",
        )
    )
    connection.execute(reservations.insert().values(_reservation_values("reservation-1", "item-1", "field-rev-1", _SHA_A)))


def _capability_values() -> dict[str, object]:
    return {
        "id": "cap-row-1",
        "capability_id": "cap-1",
        "job_id": "job-33",
        "run_id": "run-33",
        "item_id": "item-1",
        "excerpt_revision_id": "excerpt-1",
        "excerpt_sha256": _SHA_A,
        "target_start": 0,
        "target_end": 2,
        "target_text_sha256": _SHA_B,
        "provider_id": "provider-route",
        "provider": "provider",
        "model": "model-v1",
        "route_id": "korean-highlight-microexample",
        "provider_route_sha256": _SHA_C,
        "purpose": "highlight_microexample_context",
        "policy_version": "private-processing-policy-v1",
        "policy_sha256": _SHA_D,
        "tokenization_rule_id": "phase33-private-token-v1",
        "max_context_tokens": 24,
        "max_context_code_points": 120,
        "max_context_utf8_bytes": 360,
        "max_provider_attempts": 1,
        "max_estimated_cost_usd": 0.05,
        "idempotency_support": "unsupported",
        "state": "pending",
        "version": 0,
        "issuer_id": "operator",
        "issuer_intent_sha256": _SHA_A,
    }
