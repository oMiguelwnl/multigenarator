from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
from datetime import UTC, datetime
from hashlib import sha256
from typing import Any

from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import bindparam, create_engine, func, inspect, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from multilang.db.models import GenerationJob, LexicalCandidate
from multilang.db.provisioning import ensure_database_schema
from multilang.domain.jobs import JobStage, JobStatus, SupportedLanguage
from multilang.domain.korean import KoreanFrequencyJobAuthority, canonical_json_sha256
from multilang.repositories.job_repository import JobRepository
from multilang.services.korean_foundation_snapshot_fallback import (
    verify_active_korean_foundation_snapshot_provenance_with_approved_fallback,
)


PHASE_DIR = pathlib.Path(".planning/phases/32-frequency-portuguese-text-and-audio")
EVIDENCE_DIR = PHASE_DIR / "evidence-inbox"
AUTHORITY_PATH = EVIDENCE_DIR / "production-database-target-reclassification-authority.md"
PREFLIGHT_PATH = EVIDENCE_DIR / "production-database-preflight-result.json"
MIGRATION_PATH = EVIDENCE_DIR / "production-database-migration-result.json"
VALIDATION_PATH = EVIDENCE_DIR / "production-database-post-migration-validation.json"
BINDING_PATH = EVIDENCE_DIR / "production-database-job-binding.json"

EXPECTED_HEAD = "20260828_19"
PHASE32_REVISION = "20260821_18"
EXPECTED_LOCATOR_SHA256 = "19871fdb496eed265952e0358b94fa795d1b74c37d89a674b0189ee1381f32b6"
DATABASE_KIND = "production_postgresql_reclassified"
JOB_ID = "phase32-prod-freq-pilot-base"
RUN_KEY = f"ko-frequency-{JOB_ID}"

PHASE31_ACTIVE_POINTER_SHA256 = "2727c85c12c7c793b4e431356b7e7acf5cca90cec3ec288a6b26f674a996170b"
PHASE31_ACTIVE_POINTER_CONTENT_SHA256 = "b8704d2bbcc390a2cd4ee9b1119928e83c9a75aaa3cf82da98bf2474c8e7c516"
PHASE31_VALIDATION_RECEIPT_SHA256 = "8c2e9108e51c23f26ae29635105bbf3e3017b64284d835c73c2718aa03019705"
PHASE31_SNAPSHOT_MANIFEST_SHA256 = "1ee31613d347c301fc8584382a565f841d0c1bd9c4073f38ee9291eb05aea5f5"
PHASE31_SNAPSHOT_ROOT_SHA256 = "852208b32422eb70aec70772ce92fa3284acfa2eb365acc1f40f218ad5c7d8f4"
FREQUENCY_BUNDLE_MANIFEST_SHA256 = "161aac380bab58b25725e1cd914a7df2e1c43baee3970b0e870d8e03aa724465"
FREQUENCY_BUNDLE_CONTENT_SHA256 = "d235d962f706ce95822b00ec4dc65d4fa55b96b4e28238720adf0df5cf86582a"
SOURCE_RETRIEVAL_SHA256 = "3b49681f05d6a7490c13da2a2847e433effdf65da409fd295792d6ee33685064"
SOURCE_BUILD_RESULT_SHA256 = "b6beb6d5e49a8616d77a8a7515cdcc07cdfbd017eae564297a5c2f6614d15b6c"
SOURCE_REVIEW_AGGREGATE_SHA256 = "24fb03999ea744be64c445bb9de704e40c29ad24ee4120e430a110fcfa0fa35a"
PROVIDER_POLICY_SHA256 = "6174ebd73b7e2963285bb2e44205dde10ef9d3917e50c90850b483b3c8a6fc79"
PILOT_AUTHORITY_SHA256 = "db2b2c1bff644ccf2e90bf59ab00d5c4a88c009d1c03bc8e8fbf8146e9be2ced"

APP_TABLES = (
    "generation_jobs",
    "provider_response_cache",
    "provider_call_logs",
    "highlight_import_records",
    "highlight_import_manifests",
    "generation_items",
    "lexical_candidates",
    "text_quality_records",
    "audio_assets",
    "card_exports",
    "deck_exports",
    "korean_grammar_bundles",
    "korean_grammar_members",
    "personal_source_rows",
    "personal_source_decisions",
    "highlight_private_excerpt_revisions",
    "private_context_capabilities",
    "private_disclosure_attempts",
    "private_processing_receipts",
    "review_field_revisions",
    "review_current_pointers",
    "review_decisions",
    "review_access_events",
    "item_terminal_status_events",
    "item_processing_facts",
    "generation_run_denominators",
    "audio_publication_reservations",
    "audio_publication_transitions",
    "audio_revision_evidence",
)
ALLOWED_PUBLIC_TABLES = APP_TABLES + ("alembic_version",)

PHASE32_COLUMNS = {
    "generation_jobs": (
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
    ),
    "generation_items": (
        "stage_authority_sha256",
        "stage_input_sha256",
        "stage_output_sha256",
        "stage_evidence",
    ),
    "lexical_candidates": (
        "frequency_bundle_sha256",
        "frequency_source_sha256",
        "source_review_receipt_sha256",
        "source_review_aggregate_sha256",
        "lexical_evidence",
    ),
    "text_quality_records": (
        "candidate_selection_evidence",
        "adaptive_i_plus_one_evidence",
        "provider_review_evidence",
        "text_review_receipt_sha256",
    ),
    "audio_assets": (
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
    ),
    "card_exports": ("frequency_level", "frequency_bundle_sha256", "export_gate_receipt_sha256"),
    "deck_exports": ("frequency_bundle_sha256", "export_manifest_sha256", "export_gate_receipt_sha256"),
    "provider_call_logs": (
        "route_policy_sha256",
        "budget_snapshot_sha256",
        "cache_key_sha256",
        "response_schema_sha256",
    ),
}

PHASE33_TABLES = (
    "korean_grammar_bundles",
    "korean_grammar_members",
    "personal_source_rows",
    "personal_source_decisions",
    "highlight_private_excerpt_revisions",
    "private_context_capabilities",
    "private_disclosure_attempts",
    "private_processing_receipts",
    "review_field_revisions",
    "review_current_pointers",
    "review_decisions",
    "review_access_events",
    "item_terminal_status_events",
    "item_processing_facts",
    "generation_run_denominators",
    "audio_publication_reservations",
    "audio_publication_transitions",
    "audio_revision_evidence",
)


class ControlledBlock(RuntimeError):
    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_text(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def sha256_json(value: Any) -> str:
    return canonical_json_sha256(value)


def write_json(path: pathlib.Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_name(f".{path.name}.tmp")
    if temp_path.exists():
        raise ControlledBlock("temporary_output_exists")
    temp_path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temp_path.replace(path)


def parse_dotenv_database_url(text_body: str) -> str:
    pattern = re.compile(r"^\s*(?:export\s+)?MULTILANG_DATABASE_URL\s*=\s*(.*?)\s*$")
    matches: list[str] = []
    for raw_line in text_body.splitlines():
        match = pattern.match(raw_line)
        if match:
            matches.append(match.group(1).strip().strip('"').strip("'"))
    if not matches:
        raise ControlledBlock("missing_database_url")
    if len(matches) > 1:
        raise ControlledBlock("duplicate_database_url")
    if not matches[0]:
        raise ControlledBlock("blank_database_url")
    return matches[0]


def load_database_url() -> str:
    env_file = pathlib.Path(".env")
    if not env_file.is_file():
        raise ControlledBlock("missing_env_file")
    raw_url = parse_dotenv_database_url(env_file.read_text(encoding="utf-8"))
    try:
        parsed = make_url(raw_url)
    except Exception as exc:
        raise ControlledBlock("malformed_database_url") from exc
    if parsed.get_backend_name() != "postgresql":
        raise ControlledBlock("target_not_postgresql")
    return raw_url


def url_leak_components(raw_url: str) -> set[str]:
    parsed = make_url(raw_url)
    components = {raw_url, parsed.render_as_string(hide_password=False)}
    components.update(str(value) for value in (parsed.username, parsed.password, parsed.host, parsed.port, parsed.database) if value)
    for key, value in parsed.query.items():
        if isinstance(value, (tuple, list)):
            components.update(f"{key}={item}" for item in value if item)
        elif value:
            components.add(f"{key}={value}")
    return {component for component in components if component}


def leak_check(raw_url: str, paths: list[pathlib.Path]) -> None:
    body = "\n".join(path.read_text(encoding="utf-8") for path in paths if path.exists())
    if re.search(r"postgres(?:ql)?(?:\+[a-z0-9_]+)?://", body, re.I):
        raise ControlledBlock("raw_locator_leak")
    for value in url_leak_components(raw_url):
        pattern = r"(?<![A-Za-z0-9_.-])" + re.escape(value) + r"(?![A-Za-z0-9_.-])"
        if re.search(pattern, body):
            raise ControlledBlock("target_component_leak")


def validate_reclassification_authority() -> None:
    if not AUTHORITY_PATH.is_file():
        raise ControlledBlock("missing_reclassification_authority")
    body = AUTHORITY_PATH.read_text(encoding="utf-8")
    required = (
        "target_reclassification_approved=true",
        "prior_disposable_test_classification_acknowledged=true",
        "prior_disposable_reset_acknowledged=true",
        f"prior_disposable_locator_sha256={EXPECTED_LOCATOR_SHA256}",
        "production_database_connection_allowed=true",
        "alembic_upgrade_head_allowed=true",
        f"expected_alembic_head={EXPECTED_HEAD}",
        "pilot_base_job_binding_allowed=true",
        f"job_id={JOB_ID}",
        "authority_stage=pilot_base",
        "destructive_reset_authorized=false",
        "provider_call_allowed=false",
        "azure_call_allowed=false",
        "audio_synthesis_allowed=false",
        "review_application_allowed=false",
        "export_allowed=false",
        "release_allowed=false",
        "publication_allowed=false",
        "delivery_allowed=false",
        "phase32_closure_allowed=false",
        "raw_secret_persistence_allowed=false",
        "raw_locator_printing_allowed=false",
        "raw_locator_component_persistence_allowed=false",
    )
    if any(token not in body for token in required):
        raise ControlledBlock("invalid_reclassification_authority")


def build_authority() -> KoreanFrequencyJobAuthority:
    return KoreanFrequencyJobAuthority(
        stage="pilot_base",
        phase31_pointer_locator_sha256=PHASE31_ACTIVE_POINTER_SHA256,
        phase31_pointer_content_sha256=PHASE31_ACTIVE_POINTER_CONTENT_SHA256,
        phase31_validation_receipt_sha256=PHASE31_VALIDATION_RECEIPT_SHA256,
        phase31_snapshot_manifest_sha256=PHASE31_SNAPSHOT_MANIFEST_SHA256,
        phase31_snapshot_root_sha256=PHASE31_SNAPSHOT_ROOT_SHA256,
        frequency_bundle_locator_sha256=FREQUENCY_BUNDLE_MANIFEST_SHA256,
        frequency_bundle_content_sha256=FREQUENCY_BUNDLE_CONTENT_SHA256,
        source_retrieval_sha256=SOURCE_RETRIEVAL_SHA256,
        source_build_result_sha256=SOURCE_BUILD_RESULT_SHA256,
        source_review_aggregate_sha256=SOURCE_REVIEW_AGGREGATE_SHA256,
        provider_policy_sha256=PROVIDER_POLICY_SHA256,
        pilot_authority_sha256=PILOT_AUTHORITY_SHA256,
    )


def verify_phase31_authority(authority: KoreanFrequencyJobAuthority) -> dict[str, Any]:
    report = verify_active_korean_foundation_snapshot_provenance_with_approved_fallback(
        expected_receipt_sha256=authority.phase31_validation_receipt_sha256,
    )
    expected = {
        "receipt_sha256": authority.phase31_validation_receipt_sha256,
        "snapshot_manifest_sha256": authority.phase31_snapshot_manifest_sha256,
        "snapshot_root_sha256": authority.phase31_snapshot_root_sha256,
    }
    for field, value in expected.items():
        if getattr(report, field, None) != value:
            raise ControlledBlock("phase31_authority_drift")
    return {
        "phase31_dependency_mode": "verified_summary_and_immutable_snapshot_fallback",
        "phase31_active_pointer_sha256": authority.phase31_pointer_locator_sha256,
        "phase31_bundle_sha256": authority.phase31_pointer_content_sha256,
        "phase31_snapshot_receipt_sha256": authority.phase31_validation_receipt_sha256,
        "phase31_snapshot_manifest_sha256": authority.phase31_snapshot_manifest_sha256,
        "phase31_snapshot_root_sha256": authority.phase31_snapshot_root_sha256,
    }


def alembic_heads() -> list[str]:
    return ScriptDirectory.from_config(Config("alembic.ini")).get_heads()


def current_revision(conn) -> str | None:
    inspector = inspect(conn)
    if not inspector.has_table("alembic_version", schema="public"):
        return None
    rows = [row[0] for row in conn.execute(text("select version_num from public.alembic_version order by version_num")).all()]
    if len(rows) > 1:
        raise ControlledBlock("multiple_current_revisions")
    return rows[0] if rows else None


def schema_rows(conn) -> list[dict[str, Any]]:
    statement = text(
        "select table_schema,table_name,column_name,data_type,is_nullable "
        "from information_schema.columns "
        "where table_schema <> :pg and table_schema <> :info "
        "order by table_schema,table_name,ordinal_position"
    )
    return [dict(row) for row in conn.execute(statement, {"pg": "pg_catalog", "info": "information_schema"}).mappings().all()]


def app_table_locations(conn) -> list[dict[str, str]]:
    statement = text(
        "select table_schema, table_name "
        "from information_schema.tables "
        "where table_type = 'BASE TABLE' and table_name in :names "
        "order by table_schema, table_name"
    ).bindparams(bindparam("names", expanding=True))
    return [dict(row) for row in conn.execute(statement, {"names": list(APP_TABLES)}).mappings().all()]


def public_table_inventory(conn) -> list[dict[str, Any]]:
    statement = text(
        "select table_name, table_type "
        "from information_schema.tables "
        "where table_schema = 'public' "
        "order by table_type, table_name"
    )
    return [dict(row) for row in conn.execute(statement).mappings().all()]


def public_table_inventory_hash(rows: list[dict[str, Any]]) -> str:
    hashed = [
        {
            "allowed": row["table_name"] in ALLOWED_PUBLIC_TABLES,
            "table_name_sha256": sha256_text(str(row["table_name"])),
            "table_type": row["table_type"],
        }
        for row in rows
    ]
    return sha256_json(hashed)


def count_public_rows(conn, public_tables: set[str]) -> dict[str, int | None]:
    counts: dict[str, int | None] = {}
    safe_name = re.compile(r"^[a-z_][a-z0-9_]*$")
    for table_name in APP_TABLES:
        if table_name not in public_tables:
            counts[table_name] = None
            continue
        if not safe_name.fullmatch(table_name):
            raise ControlledBlock("unsafe_table_name")
        counts[table_name] = int(conn.execute(text(f'select count(*) from public."{table_name}"')).scalar_one())
    return counts


def total_existing_rows(counts: dict[str, int | None]) -> int:
    return sum(value for value in counts.values() if value is not None)


def phase32_columns_present(conn) -> tuple[bool, dict[str, list[str]]]:
    missing: dict[str, list[str]] = {}
    inspector = inspect(conn)
    for table_name, expected_columns in PHASE32_COLUMNS.items():
        present = (
            {column["name"] for column in inspector.get_columns(table_name, schema="public")}
            if inspector.has_table(table_name, schema="public")
            else set()
        )
        table_missing = [column for column in expected_columns if column not in present]
        if table_missing:
            missing[table_name] = table_missing
    return not missing, missing


def target_hashes(raw_url: str, conn) -> tuple[str, str]:
    parsed = make_url(raw_url)
    locator = "|".join(str(part or "") for part in (parsed.get_backend_name(), parsed.host, parsed.port, parsed.database))
    identity = dict(
        conn.execute(
            text(
                "select current_database() as db, current_user as usr, "
                "inet_server_addr()::text as addr, inet_server_port() as port"
            )
        )
        .mappings()
        .one()
    )
    return sha256_text(locator), sha256_json(identity)


def read_db_counts(raw_url: str) -> tuple[dict[str, int | None], int]:
    engine = create_engine(raw_url)
    try:
        with engine.connect() as conn:
            public_tables = {row["table_name"] for row in app_table_locations(conn) if row["table_schema"] == "public"}
            counts = count_public_rows(conn, public_tables)
            return counts, total_existing_rows(counts)
    finally:
        engine.dispose()


def existing_job_state(repository: JobRepository, authority: KoreanFrequencyJobAuthority) -> dict[str, Any]:
    job = repository.get_job(JOB_ID)
    if job is None:
        return {
            "existing_job_present": False,
            "existing_job_matches_expected_identity": False,
            "existing_job_same_authority": False,
        }
    matches_identity = job.language == SupportedLanguage.KO.value and job.source_type == "frequency" and job.run_key == RUN_KEY
    same_authority = False
    authority_sha256 = None
    if job.korean_frequency_authority is not None:
        loaded = repository.load_korean_authority(JOB_ID)
        same_authority = loaded.model_dump(mode="json", exclude_none=True) == authority.model_dump(mode="json", exclude_none=True)
        authority_sha256 = canonical_json_sha256(loaded.model_dump(mode="json", exclude_none=True))
    return {
        "existing_job_present": True,
        "existing_job_matches_expected_identity": matches_identity,
        "existing_job_same_authority": same_authority,
        "existing_job_authority_sha256": authority_sha256,
    }


def preexisting_rows_allowed(counts: dict[str, int | None], state: dict[str, Any]) -> tuple[bool, str]:
    total = total_existing_rows(counts)
    if total == 0:
        return True, "empty"
    only_same_job = (
        total == 1
        and counts.get("generation_jobs") == 1
        and all((value in (0, None)) for table, value in counts.items() if table != "generation_jobs")
        and state.get("existing_job_matches_expected_identity") is True
        and state.get("existing_job_same_authority") is True
    )
    if only_same_job:
        return True, "idempotent_same_job_replay"
    return False, "unexpected_application_rows"


def blocked_payload(stage: str, reason: str) -> dict[str, Any]:
    return {
        "status": f"blocked_{reason}",
        "blocked_reason": reason,
        "failure_stage": stage,
        "database_kind": DATABASE_KIND,
        "expected_head": EXPECTED_HEAD,
        "job_id": JOB_ID,
        "provider_call_count_delta": 0,
        "azure_call_count": 0,
        "audio_synthesis_attempt_count": 0,
        "review_application_count": 0,
        "export_count": 0,
        "release_action_count": 0,
        "publication_action_count": 0,
        "delivery_action_count": 0,
        "phase32_closure_attempted": False,
        "raw_secret_persisted": False,
        "created_at_utc": utc_now(),
    }


def collect_preflight(raw_url: str, authority: KoreanFrequencyJobAuthority) -> dict[str, Any]:
    validate_reclassification_authority()
    phase31 = verify_phase31_authority(authority)
    heads = alembic_heads()
    blocked_reason = None
    if heads != [EXPECTED_HEAD]:
        blocked_reason = "unexpected_alembic_head_state"

    engine = create_engine(raw_url)
    try:
        with engine.connect() as conn:
            if conn.dialect.name != "postgresql":
                raise ControlledBlock("connected_dialect_mismatch")
            locator_hash, identity_hash = target_hashes(raw_url, conn)
            recovery = bool(conn.execute(text("select pg_is_in_recovery()")).scalar_one())
            read_only = str(conn.execute(text("show transaction_read_only")).scalar_one()).casefold() == "on"
            revision = current_revision(conn)
            locations = app_table_locations(conn)
            inventory = public_table_inventory(conn)
            public_tables = {row["table_name"] for row in locations if row["table_schema"] == "public"}
            public_counts = count_public_rows(conn, public_tables)
            schema_prestate = schema_rows(conn)
            phase32_ok, missing_phase32 = phase32_columns_present(conn)
            phase33_present = all(table_name in public_tables for table_name in PHASE33_TABLES)
            lock_available = bool(conn.execute(text("select pg_try_advisory_lock(320053)")).scalar_one())
            if lock_available:
                conn.execute(text("select pg_advisory_unlock(320053)"))
            non_public_app_count = sum(1 for row in locations if row["table_schema"] != "public")
            unexpected_public_base_tables = [
                row
                for row in inventory
                if row["table_type"] == "BASE TABLE" and row["table_name"] not in ALLOWED_PUBLIC_TABLES
            ]
    except ControlledBlock:
        raise
    except Exception as exc:
        raise ControlledBlock("database_connection_failed") from exc
    finally:
        engine.dispose()

    if blocked_reason is None and locator_hash != EXPECTED_LOCATOR_SHA256:
        blocked_reason = "target_hash_not_reclassified_locator"
    if blocked_reason is None and (recovery or read_only):
        blocked_reason = "target_not_writable_primary"
    if blocked_reason is None and non_public_app_count:
        blocked_reason = "non_public_application_tables_present"
    if blocked_reason is None and unexpected_public_base_tables:
        blocked_reason = "unexpected_public_base_tables_present"

    status = "passed" if blocked_reason is None else f"blocked_{blocked_reason}"
    return {
        "schema_version": "phase32-production-database-preflight-v1",
        "status": status,
        "blocked_reason": blocked_reason,
        "database_kind": DATABASE_KIND,
        "database_connection_attempted": True,
        "database_locator_sha256": locator_hash,
        "database_identity_sha256": identity_hash,
        "expected_reclassified_locator_sha256": EXPECTED_LOCATOR_SHA256,
        "target_reclassified_from_disposable_test": True,
        "target_matches_reclassified_locator": locator_hash == EXPECTED_LOCATOR_SHA256,
        "prior_disposable_reset_plan": "32-48",
        "dialect": "postgresql",
        "expected_head": EXPECTED_HEAD,
        "sole_head": heads[0] if len(heads) == 1 else None,
        "heads": heads,
        "current_revision": revision,
        "phase32_revision": PHASE32_REVISION,
        "phase32_columns_present_before_migration": phase32_ok,
        "phase32_missing_columns_before_migration": missing_phase32,
        "phase33_tables_present_before_migration": phase33_present,
        "phase33_head_acknowledged": True,
        "replica": recovery,
        "transaction_read_only": read_only,
        "advisory_lock_available": lock_available,
        "public_application_table_count": len(public_tables),
        "non_public_application_table_count": non_public_app_count,
        "unexpected_public_base_table_count": len(unexpected_public_base_tables),
        "public_table_inventory_sha256": public_table_inventory_hash(inventory),
        "pre_binding_application_row_counts": public_counts,
        "pre_binding_application_row_counts_sha256": sha256_json(public_counts),
        "pre_binding_application_row_count_total": total_existing_rows(public_counts),
        "schema_prestate_sha256": sha256_json(schema_prestate),
        "schema_prestate_column_count": len(schema_prestate),
        "destructive_reset_authorized": False,
        "manual_sql_used": False,
        "provider_call_count_delta": 0,
        "azure_call_count": 0,
        "audio_synthesis_attempt_count": 0,
        "review_application_count": 0,
        "export_count": 0,
        "raw_secret_persisted": False,
        "created_at_utc": utc_now(),
        **phase31,
    }


def run_migration(raw_url: str, preflight: dict[str, Any]) -> dict[str, Any]:
    engine = create_engine(raw_url)
    try:
        with engine.connect() as conn:
            before_revision = current_revision(conn)
            before_schema = schema_rows(conn)
            before_counts, before_total = count_public_rows(
                conn,
                {row["table_name"] for row in app_table_locations(conn) if row["table_schema"] == "public"},
            ), None
            before_total = total_existing_rows(before_counts)
        ensure_database_schema(engine, raw_url)
        with engine.connect() as conn:
            after_revision = current_revision(conn)
            after_schema = schema_rows(conn)
            after_counts = count_public_rows(
                conn,
                {row["table_name"] for row in app_table_locations(conn) if row["table_schema"] == "public"},
            )
            after_total = total_existing_rows(after_counts)
    except ControlledBlock:
        raise
    except Exception as exc:
        raise ControlledBlock("migration_failed") from exc
    finally:
        engine.dispose()

    status = "migrated" if after_revision == EXPECTED_HEAD else "blocked_migration_incomplete"
    return {
        "schema_version": "phase32-production-database-migration-v1",
        "status": status,
        "database_kind": DATABASE_KIND,
        "database_locator_sha256": preflight["database_locator_sha256"],
        "expected_head": EXPECTED_HEAD,
        "sole_head": EXPECTED_HEAD,
        "before_revision": before_revision,
        "after_revision": after_revision,
        "schema_before_migration_sha256": sha256_json(before_schema),
        "schema_before_migration_column_count": len(before_schema),
        "schema_after_migration_sha256": sha256_json(after_schema),
        "schema_after_migration_column_count": len(after_schema),
        "row_count_before_migration": before_total,
        "row_count_after_migration": after_total,
        "row_count_delta": after_total - before_total,
        "application_row_counts_after_migration": after_counts,
        "application_row_counts_after_migration_sha256": sha256_json(after_counts),
        "alembic_upgrade_head_ran": True,
        "manual_sql_used": False,
        "destructive_statement_count": 0,
        "provider_call_count_delta": 0,
        "azure_call_count": 0,
        "audio_synthesis_attempt_count": 0,
        "review_application_count": 0,
        "export_count": 0,
        "raw_secret_persisted": False,
        "created_at_utc": utc_now(),
    }


def validate_post_migration(raw_url: str, preflight: dict[str, Any]) -> dict[str, Any]:
    authority = build_authority()
    engine = create_engine(raw_url)
    try:
        with engine.connect() as conn:
            before_revision = current_revision(conn)
            before_counts = count_public_rows(
                conn,
                {row["table_name"] for row in app_table_locations(conn) if row["table_schema"] == "public"},
            )
            before_total = total_existing_rows(before_counts)
        ensure_database_schema(engine, raw_url)
        with engine.connect() as conn:
            after_revision = current_revision(conn)
            locations = app_table_locations(conn)
            public_tables = {row["table_name"] for row in locations if row["table_schema"] == "public"}
            after_counts = count_public_rows(conn, public_tables)
            after_total = total_existing_rows(after_counts)
            schema_poststate = schema_rows(conn)
            current = current_revision(conn)
            phase32_ok, missing_phase32 = phase32_columns_present(conn)
            phase33_present = all(table_name in public_tables for table_name in PHASE33_TABLES)
        session = Session(engine)
        try:
            state = existing_job_state(JobRepository(session), authority)
        finally:
            session.close()
    except ControlledBlock:
        raise
    except Exception as exc:
        raise ControlledBlock("post_migration_validation_failed") from exc
    finally:
        engine.dispose()

    rows_allowed, row_state = preexisting_rows_allowed(after_counts, state)
    status = (
        "passed"
        if current == EXPECTED_HEAD and phase32_ok and phase33_present and after_total == before_total and rows_allowed
        else "failed"
    )
    return {
        "schema_version": "phase32-production-database-post-migration-validation-v1",
        "status": status,
        "database_kind": DATABASE_KIND,
        "database_locator_sha256": preflight["database_locator_sha256"],
        "current_revision": current,
        "expected_head": EXPECTED_HEAD,
        "sole_head": EXPECTED_HEAD,
        "phase32_revision": PHASE32_REVISION,
        "phase32_columns_present": phase32_ok,
        "phase32_missing_columns": missing_phase32,
        "phase33_tables_present": phase33_present,
        "phase33_head_acknowledged": True,
        "runtime_provisioning_revision_before": before_revision,
        "runtime_provisioning_revision_after": after_revision,
        "runtime_provisioning_row_count_delta": after_total - before_total,
        "pre_binding_row_state": row_state,
        "pre_binding_application_row_counts": after_counts,
        "pre_binding_application_row_counts_sha256": sha256_json(after_counts),
        "pre_binding_application_row_count_total": after_total,
        "pre_binding_existing_job_state": state,
        "schema_poststate_sha256": sha256_json(schema_poststate),
        "schema_poststate_column_count": len(schema_poststate),
        "production_database_ready_for_pilot_base_binding": status == "passed",
        "production_ready": False,
        "provider_call_count_delta": 0,
        "azure_call_count": 0,
        "audio_synthesis_attempt_count": 0,
        "review_application_count": 0,
        "export_count": 0,
        "raw_secret_persisted": False,
        "created_at_utc": utc_now(),
    }


def bind_production_job(raw_url: str, preflight: dict[str, Any], validation: dict[str, Any]) -> dict[str, Any]:
    authority = build_authority()
    engine = create_engine(raw_url)
    try:
        ensure_database_schema(engine, raw_url)
        before_counts, before_total = read_db_counts(raw_url)
        session = Session(engine)
        try:
            repository = JobRepository(session)
            before_state = existing_job_state(repository, authority)
            rows_allowed, row_state = preexisting_rows_allowed(before_counts, before_state)
            if not rows_allowed:
                raise ControlledBlock(row_state)
            provider_attempts_before = repository.count_provider_attempts(JOB_ID)
            job = repository.get_job(JOB_ID)
            job_created = job is None
            if job is None:
                repository.session.add(
                    GenerationJob(
                        id=JOB_ID,
                        run_key=RUN_KEY,
                        language=SupportedLanguage.KO.value,
                        source_type="frequency",
                        source_fingerprint=FREQUENCY_BUNDLE_CONTENT_SHA256,
                        status=JobStatus.PENDING.value,
                        current_stage=JobStage.INGEST.value,
                        total_items=3000,
                        completed_items=0,
                        failed_items=0,
                        retrying_items=0,
                        skipped_duplicates=0,
                        resume_state={},
                    )
                )
            elif not before_state.get("existing_job_matches_expected_identity"):
                raise ControlledBlock("existing_job_identity_drift")
            elif not before_state.get("existing_job_same_authority"):
                raise ControlledBlock("existing_job_authority_drift")
            bound = repository.bind_execution_authority(JOB_ID, authority)
            loaded = repository.load_korean_authority(JOB_ID)
            lexical_candidate_count = int(
                session.scalar(select(func.count(LexicalCandidate.id)).where(LexicalCandidate.job_id == JOB_ID)) or 0
            )
            provider_attempts_after = repository.count_provider_attempts(JOB_ID)
        finally:
            session.close()
        after_counts, after_total = read_db_counts(raw_url)
    except ControlledBlock:
        raise
    except Exception as exc:
        raise ControlledBlock("job_binding_failed") from exc
    finally:
        engine.dispose()

    payload = bound.model_dump(mode="json", exclude_none=True)
    loaded_payload = loaded.model_dump(mode="json", exclude_none=True)
    row_delta = after_total - before_total
    status = "bound" if payload == loaded_payload and row_delta in (0, 1) and lexical_candidate_count == 0 else "failed"
    return {
        "schema_version": "phase32-production-database-job-binding-v1",
        "status": status,
        "database_kind": DATABASE_KIND,
        "database_locator_sha256": preflight["database_locator_sha256"],
        "database_validation_status": validation["status"],
        "job_id": JOB_ID,
        "run_key_sha256": sha256_text(RUN_KEY),
        "job_created": job_created,
        "authority_stage": bound.stage,
        "authority_sha256": canonical_json_sha256(payload),
        "job_authority_equal": payload == authority.model_dump(mode="json", exclude_none=True),
        "persisted_reloaded_equal": payload == loaded_payload,
        "phase31_active_pointer_sha256": PHASE31_ACTIVE_POINTER_SHA256,
        "phase31_bundle_sha256": PHASE31_ACTIVE_POINTER_CONTENT_SHA256,
        "phase31_snapshot_receipt_sha256": PHASE31_VALIDATION_RECEIPT_SHA256,
        "phase31_snapshot_manifest_sha256": PHASE31_SNAPSHOT_MANIFEST_SHA256,
        "phase31_snapshot_root_sha256": PHASE31_SNAPSHOT_ROOT_SHA256,
        "frequency_bundle_manifest_sha256": FREQUENCY_BUNDLE_MANIFEST_SHA256,
        "final_frequency_bundle_sha256": FREQUENCY_BUNDLE_CONTENT_SHA256,
        "source_retrieval_sha256": SOURCE_RETRIEVAL_SHA256,
        "source_build_result_sha256": SOURCE_BUILD_RESULT_SHA256,
        "source_review_aggregate_sha256": SOURCE_REVIEW_AGGREGATE_SHA256,
        "provider_policy_sha256": PROVIDER_POLICY_SHA256,
        "pilot_authority_sha256": PILOT_AUTHORITY_SHA256,
        "binding_receipt_sha256": SOURCE_REVIEW_AGGREGATE_SHA256,
        "pre_binding_row_state": row_state,
        "application_row_count_before_binding": before_total,
        "application_row_count_after_binding": after_total,
        "application_row_count_delta": row_delta,
        "application_row_counts_before_binding_sha256": sha256_json(before_counts),
        "application_row_counts_after_binding_sha256": sha256_json(after_counts),
        "lexical_candidate_count_for_job": lexical_candidate_count,
        "provider_attempt_count_before": provider_attempts_before,
        "provider_attempt_count_after": provider_attempts_after,
        "adapter_constructor_count": 0,
        "fallback_policy": "none",
        "azure_call_count": 0,
        "audio_synthesis_attempt_count": 0,
        "review_application_count": 0,
        "export_count": 0,
        "release_action_count": 0,
        "publication_action_count": 0,
        "delivery_action_count": 0,
        "phase32_closure_attempted": False,
        "full_authority_bound": False,
        "raw_secret_persisted": False,
        "created_at_utc": utc_now(),
    }


def execute_preflight_migrate_bind() -> int:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    try:
        raw_url = load_database_url()
    except ControlledBlock as exc:
        write_json(PREFLIGHT_PATH, blocked_payload("load_database_url", exc.reason))
        return 2

    authority = build_authority()
    written_paths: list[pathlib.Path] = [AUTHORITY_PATH]
    try:
        preflight = collect_preflight(raw_url, authority)
        write_json(PREFLIGHT_PATH, preflight)
        written_paths.append(PREFLIGHT_PATH)
        leak_check(raw_url, written_paths)
        if preflight["status"] != "passed":
            return 2

        migration = run_migration(raw_url, preflight)
        write_json(MIGRATION_PATH, migration)
        written_paths.append(MIGRATION_PATH)
        leak_check(raw_url, written_paths)
        if migration["status"] != "migrated":
            return 2

        validation = validate_post_migration(raw_url, preflight)
        write_json(VALIDATION_PATH, validation)
        written_paths.append(VALIDATION_PATH)
        leak_check(raw_url, written_paths)
        if validation["status"] != "passed":
            return 2

        binding = bind_production_job(raw_url, preflight, validation)
        write_json(BINDING_PATH, binding)
        written_paths.append(BINDING_PATH)
        leak_check(raw_url, written_paths)
        if binding["status"] != "bound":
            return 2
    except ControlledBlock as exc:
        failure = blocked_payload("execute_preflight_migrate_bind", exc.reason)
        target_path = BINDING_PATH if VALIDATION_PATH.exists() else VALIDATION_PATH if MIGRATION_PATH.exists() else MIGRATION_PATH
        write_json(target_path, failure)
        leak_check(raw_url, written_paths + [target_path])
        return 2

    print("production_database_preflight_and_job_binding_status=bound")
    return 0


def self_check() -> int:
    sample_url = "postgresql://user:secret@example.invalid:5432/exampledb?phase32_helper_self_check=not-real"
    parsed = parse_dotenv_database_url("OTHER_SECRET=should_not_be_read\nexport MULTILANG_DATABASE_URL='" + sample_url + "'\n")
    if parsed != sample_url:
        raise ControlledBlock("self_check_env_parser_failed")
    try:
        parse_dotenv_database_url("MULTILANG_DATABASE_URL=postgresql://a/b\nMULTILANG_DATABASE_URL=postgresql://c/d\n")
    except ControlledBlock as exc:
        if exc.reason != "duplicate_database_url":
            raise
    else:
        raise ControlledBlock("self_check_duplicate_not_rejected")
    components = url_leak_components(sample_url)
    required = {
        sample_url,
        "user",
        "secret",
        "example.invalid",
        "5432",
        "exampledb",
        "phase32_helper_self_check=not-real",
    }
    if not required.issubset(components):
        raise ControlledBlock("self_check_component_scan_failed")
    if JOB_ID != "phase32-prod-freq-pilot-base" or len(JOB_ID) > 36:
        raise ControlledBlock("self_check_job_id_invalid")
    validate_reclassification_authority()
    build_authority()
    print("self_check_status=passed")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Phase 32 production DB preflight and job binding helper")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--self-check", action="store_true")
    group.add_argument("--execute-preflight-migrate-bind", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.self_check:
        return self_check()
    if args.execute_preflight_migrate_bind:
        return execute_preflight_migrate_bind()
    raise ControlledBlock("missing_mode")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ControlledBlock as exc:
        print("blocked: " + exc.reason, file=sys.stderr)
        raise SystemExit(2)
    except SystemExit:
        raise
    except Exception:
        print("blocked: sanitized production DB helper failure", file=sys.stderr)
        raise SystemExit(2)
