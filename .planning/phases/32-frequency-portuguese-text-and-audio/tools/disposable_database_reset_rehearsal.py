from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import re
import sys
from datetime import UTC, datetime
from typing import Any

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import bindparam, create_engine, inspect, text
from sqlalchemy.engine import make_url

from multilang.db.provisioning import ensure_database_schema


PHASE_DIR = pathlib.Path(".planning/phases/32-frequency-portuguese-text-and-audio")
EVIDENCE_DIR = PHASE_DIR / "evidence-inbox"
TOOLS_DIR = PHASE_DIR / "tools"
PLAN_32_47_PREFLIGHT = EVIDENCE_DIR / "disposable-database-preflight.json"
AUTHORIZATION_PATH = EVIDENCE_DIR / "disposable-database-reset-authorization.md"
RESET_PREFLIGHT_PATH = EVIDENCE_DIR / "disposable-database-reset-preflight.json"
RESET_RESULT_PATH = EVIDENCE_DIR / "disposable-database-reset-result.json"
MIGRATION_RESULT_PATH = EVIDENCE_DIR / "disposable-database-after-reset-migration-result.json"
VALIDATION_PATH = EVIDENCE_DIR / "disposable-database-after-reset-validation.json"
SUMMARY_PATH = PHASE_DIR / "32-48-SUMMARY.md"

EXPECTED_HEAD = "20260828_19"
PHASE32_REVISION = "20260821_18"
TARGET_ALIAS = "env-multilang-database-url-disposable-test"

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


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha256_json(value: Any) -> str:
    body = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def write_json(path: pathlib.Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_raw_url() -> str:
    raw_url = os.environ.get("MULTILANG_DATABASE_URL")
    if not raw_url:
        raise ControlledBlock("missing_database_url")
    if make_url(raw_url).get_backend_name() != "postgresql":
        raise ControlledBlock("target_not_postgresql")
    return raw_url


def alembic_heads() -> list[str]:
    return ScriptDirectory.from_config(Config("alembic.ini")).get_heads()


def alembic_config(raw_url: str) -> Config:
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", raw_url)
    return config


def schema_rows(conn) -> list[dict[str, Any]]:
    stmt = text(
        "select table_schema,table_name,column_name,data_type,is_nullable "
        "from information_schema.columns "
        "where table_schema <> :pg and table_schema <> :info "
        "order by table_schema,table_name,ordinal_position"
    )
    return [dict(row) for row in conn.execute(stmt, {"pg": "pg_catalog", "info": "information_schema"}).mappings().all()]


def current_revision(conn) -> str | None:
    inspector = inspect(conn)
    if not inspector.has_table("alembic_version"):
        return None
    rows = [row[0] for row in conn.execute(text("select version_num from alembic_version order by version_num")).all()]
    if len(rows) > 1:
        raise ControlledBlock("multiple_current_revisions")
    return rows[0] if rows else None


def app_table_locations(conn) -> list[dict[str, str]]:
    stmt = text(
        "select table_schema, table_name "
        "from information_schema.tables "
        "where table_type = 'BASE TABLE' and table_name in :names "
        "order by table_schema, table_name"
    ).bindparams(bindparam("names", expanding=True))
    return [dict(row) for row in conn.execute(stmt, {"names": list(APP_TABLES)}).mappings().all()]


def public_table_inventory(conn) -> list[dict[str, Any]]:
    stmt = text(
        "select table_name, table_type "
        "from information_schema.tables "
        "where table_schema = 'public' "
        "order by table_type, table_name"
    )
    return [dict(row) for row in conn.execute(stmt).mappings().all()]


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
    safe = re.compile(r"^[a-z_][a-z0-9_]*$")
    for table_name in APP_TABLES:
        if table_name not in public_tables:
            counts[table_name] = None
            continue
        if not safe.fullmatch(table_name):
            raise ControlledBlock("unsafe_table_name")
        counts[table_name] = int(conn.execute(text(f'select count(*) from public."{table_name}"')).scalar_one())
    return counts


def count_allowed_public_rows(conn, public_tables: set[str]) -> dict[str, int | None]:
    counts: dict[str, int | None] = {}
    safe = re.compile(r"^[a-z_][a-z0-9_]*$")
    for table_name in ALLOWED_PUBLIC_TABLES:
        if table_name not in public_tables:
            counts[table_name] = None
            continue
        if not safe.fullmatch(table_name):
            raise ControlledBlock("unsafe_table_name")
        counts[table_name] = int(conn.execute(text(f'select count(*) from public."{table_name}"')).scalar_one())
    return counts


def public_exists(conn) -> bool:
    return bool(
        conn.execute(text("select exists(select 1 from information_schema.schemata where schema_name = 'public')")).scalar_one()
    )


def safe_public_exists(raw_url: str) -> bool | None:
    engine = create_engine(raw_url)
    try:
        with engine.connect() as conn:
            return public_exists(conn)
    except Exception:
        return None
    finally:
        engine.dispose()


def target_hashes(raw_url: str, conn) -> tuple[str, str]:
    url = make_url(raw_url)
    locator = "|".join(str(x or "") for x in (url.get_backend_name(), url.host, url.port, url.database))
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


def total_existing_rows(counts: dict[str, int | None]) -> int:
    return sum(value for value in counts.values() if value is not None)


def failure_envelope(raw_url: str, stage: str, reason: str) -> dict[str, Any]:
    return {
        "failure_stage": stage,
        "blocked_reason": reason,
        "public_schema_exists_after_failure": safe_public_exists(raw_url),
        "provider_call_count_delta": 0,
        "generated_content_row_delta": 0,
        "audio_synthesis_count_delta": 0,
        "export_count_delta": 0,
        "production_authority": False,
        "raw_secret_persisted": False,
        "created_at_utc": utc_now(),
    }


def not_run_result(raw_url: str, status: str, stage: str, reason: str) -> dict[str, Any]:
    return {
        "status": status,
        "target_alias": TARGET_ALIAS,
        "expected_head": EXPECTED_HEAD,
        "manual_sql_used": False,
        **failure_envelope(raw_url, stage, reason),
    }


def leak_check(raw_url: str, paths: list[pathlib.Path]) -> None:
    url = make_url(raw_url)
    rendered = url.render_as_string(hide_password=False)
    components: set[str] = {str(pathlib.Path.home())}
    components.update(str(v) for v in (url.username, url.password, url.host, url.database) if v)
    for values in url.query.values():
        iterable = values if isinstance(values, (tuple, list)) else (values,)
        components.update(str(v) for v in iterable if v)
    generic = {"test", "postgres", "postgresql", "localhost", "default", "public", "admin", "user", "root", "db", "data"}
    components = {v for v in components if len(v) >= 8 and v.casefold() not in generic}
    bodies = "\n".join(path.read_text(encoding="utf-8") for path in paths if path.exists())
    if raw_url in bodies or rendered in bodies or re.search(r"postgres(?:ql)?(?:\+[a-z0-9_]+)?://", bodies, re.I):
        raise ControlledBlock("raw_locator_leak")
    for value in components:
        pattern = r"(?<![A-Za-z0-9_.-])" + re.escape(value) + r"(?![A-Za-z0-9_.-])"
        if re.search(pattern, bodies):
            raise ControlledBlock("target_component_leak")


class ControlledBlock(RuntimeError):
    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(reason)


def load_plan_32_47_preflight() -> dict[str, Any]:
    if not PLAN_32_47_PREFLIGHT.exists():
        raise ControlledBlock("missing_plan_32_47_preflight")
    data = json.loads(PLAN_32_47_PREFLIGHT.read_text(encoding="utf-8"))
    if data.get("target_alias") != TARGET_ALIAS:
        raise ControlledBlock("unexpected_plan_32_47_target_alias")
    if data.get("disposable_test_target") is not True:
        raise ControlledBlock("plan_32_47_target_not_disposable")
    return data


def collect_reset_preflight(raw_url: str) -> dict[str, Any]:
    previous = load_plan_32_47_preflight()
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
            target_matches = (
                locator_hash == previous.get("database_locator_sha256")
                and identity_hash == previous.get("database_identity_sha256")
            )
            recovery = bool(conn.execute(text("select pg_is_in_recovery()")).scalar_one())
            read_only = str(conn.execute(text("show transaction_read_only")).scalar_one()).casefold() == "on"
            revision = current_revision(conn)
            locations = app_table_locations(conn)
            inventory = public_table_inventory(conn)
            non_public_count = sum(1 for row in locations if row["table_schema"] != "public")
            unexpected_public_tables = [row for row in inventory if row["table_name"] not in ALLOWED_PUBLIC_TABLES]
            unexpected_public_base_tables = [
                row for row in unexpected_public_tables if row["table_type"] == "BASE TABLE"
            ]
            public_tables = {row["table_name"] for row in locations if row["table_schema"] == "public"}
            allowed_public_base_tables = {
                row["table_name"]
                for row in inventory
                if row["table_name"] in ALLOWED_PUBLIC_TABLES and row["table_type"] == "BASE TABLE"
            }
            counts = count_public_rows(conn, public_tables)
            allowed_counts = count_allowed_public_rows(conn, allowed_public_base_tables)
            schema_pre_reset = schema_rows(conn)
            public_schema_exists = public_exists(conn)
            lock_available = bool(conn.execute(text("select pg_try_advisory_lock(320048)")).scalar_one())
            if lock_available:
                conn.execute(text("select pg_advisory_unlock(320048)"))
    finally:
        engine.dispose()

    if blocked_reason is None and not target_matches:
        blocked_reason = "target_hash_mismatch"
    if blocked_reason is None and (recovery or read_only):
        blocked_reason = "target_not_writable_primary"
    if blocked_reason is None and non_public_count:
        blocked_reason = "non_public_application_tables_present"
    if blocked_reason is None and unexpected_public_tables:
        blocked_reason = "unexpected_public_tables_present"
    if blocked_reason is None and revision is not None:
        blocked_reason = "unexpected_existing_alembic_revision"

    status = "ready_for_public_schema_reset" if blocked_reason is None else f"blocked_{blocked_reason}"
    return {
        "status": status,
        "blocked_reason": blocked_reason,
        "target_alias": TARGET_ALIAS,
        "target_matches_plan_32_47": target_matches,
        "database_locator_sha256": locator_hash,
        "database_identity_sha256": identity_hash,
        "previous_database_locator_sha256": previous.get("database_locator_sha256"),
        "previous_database_identity_sha256": previous.get("database_identity_sha256"),
        "dialect": "postgresql",
        "disposable_test_target": True,
        "destructive_reset_authorized": True,
        "destructive_authorization_source": "current_session_user_choice_wipe_current_db",
        "expected_head": EXPECTED_HEAD,
        "sole_head": heads[0] if len(heads) == 1 else None,
        "heads": heads,
        "current_revision": revision,
        "phase32_revision": PHASE32_REVISION,
        "phase33_head_acknowledged": True,
        "replica": recovery,
        "transaction_read_only": read_only,
        "advisory_lock_available": lock_available,
        "public_schema_exists": public_schema_exists,
        "public_application_table_count": len(public_tables),
        "non_public_application_table_count": non_public_count,
        "unexpected_public_table_count": len(unexpected_public_tables),
        "unexpected_public_base_table_count": len(unexpected_public_base_tables),
        "public_table_inventory_sha256": public_table_inventory_hash(inventory),
        "pre_reset_row_counts": counts,
        "pre_reset_row_counts_sha256": sha256_json(counts),
        "pre_reset_allowed_public_row_counts": allowed_counts,
        "pre_reset_allowed_public_row_counts_sha256": sha256_json(allowed_counts),
        "pre_reset_row_count_total": total_existing_rows(allowed_counts),
        "pre_reset_all_public_base_row_count_total": total_existing_rows(allowed_counts),
        "schema_pre_reset_sha256": sha256_json(schema_pre_reset),
        "schema_pre_reset_column_count": len(schema_pre_reset),
        "fixed_public_schema_reset": True,
        "database_drop_allowed": False,
        "role_drop_allowed": False,
        "non_public_schema_drop_allowed": False,
        "raw_secret_persisted": False,
        "created_at_utc": utc_now(),
    }


def write_authorization(raw_url: str, preflight: dict[str, Any]) -> None:
    body = "\n".join(
        [
            "# Disposable Database Reset Authorization",
            "",
            "target_alias=env-multilang-database-url-disposable-test",
            "classification=disposable/test",
            "user_choice=Wipe Current DB",
            "destructive_reset_authorized=true",
            "destructive_scope=public_schema_only",
            "production_authority=false",
            "database_drop_allowed=false",
            "role_drop_allowed=false",
            "non_public_schema_drop_allowed=false",
            "backup_restore_required_for_this_rehearsal=false",
            "plan_32_47_target_match=" + str(preflight["target_matches_plan_32_47"]).lower(),
            "scope=Reset the public schema of the exact disposable/test target, then run Alembic current-head rehearsal only.",
            "secret_policy=The raw MULTILANG_DATABASE_URL and target locator components are used only in-process and are not persisted.",
            "production_boundary=A real production or important database still requires a separate plan with backup, restore, and rollback evidence.",
            "recorded_at_utc=" + preflight["created_at_utc"],
            "",
        ]
    )
    AUTHORIZATION_PATH.write_text(body, encoding="utf-8")
    leak_check(raw_url, [AUTHORIZATION_PATH])


def preflight_only() -> int:
    raw_url = load_raw_url()
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    preflight = collect_reset_preflight(raw_url)
    write_authorization(raw_url, preflight)
    write_json(RESET_PREFLIGHT_PATH, preflight)
    leak_check(raw_url, [AUTHORIZATION_PATH, RESET_PREFLIGHT_PATH])
    if preflight["status"] != "ready_for_public_schema_reset":
        print("blocked: " + str(preflight["blocked_reason"]), file=sys.stderr)
        return 2
    return 0


def reset_public_schema(raw_url: str, preflight: dict[str, Any]) -> dict[str, Any]:
    engine = create_engine(raw_url)
    try:
        with engine.begin() as conn:
            conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
            conn.execute(text("CREATE SCHEMA public"))
        with engine.connect() as conn:
            after_schema = schema_rows(conn)
            after_locations = app_table_locations(conn)
            after_revision = current_revision(conn)
            public_after = public_exists(conn)
    finally:
        engine.dispose()

    return {
        "status": "public_schema_reset_completed",
        "target_alias": TARGET_ALIAS,
        "fixed_public_schema_reset": True,
        "statement_ids": ["drop_public_schema_cascade", "create_public_schema"],
        "manual_sql_used": False,
        "database_dropped": False,
        "roles_dropped": False,
        "non_public_schemas_dropped": False,
        "before_revision": preflight["current_revision"],
        "after_revision": after_revision,
        "pre_reset_row_counts": preflight["pre_reset_row_counts"],
        "pre_reset_allowed_public_row_counts": preflight["pre_reset_allowed_public_row_counts"],
        "pre_reset_allowed_public_row_counts_sha256": preflight[
            "pre_reset_allowed_public_row_counts_sha256"
        ],
        "destroyed_row_count_total": preflight["pre_reset_row_count_total"],
        "destroyed_public_base_row_count_total": preflight["pre_reset_all_public_base_row_count_total"],
        "schema_pre_reset_sha256": preflight["schema_pre_reset_sha256"],
        "schema_after_reset_sha256": sha256_json(after_schema),
        "schema_after_reset_column_count": len(after_schema),
        "post_reset_application_table_count": len(after_locations),
        "public_schema_exists_after_reset": public_after,
        "provider_call_count_delta": 0,
        "generated_content_row_delta": 0,
        "audio_synthesis_count_delta": 0,
        "export_count_delta": 0,
        "production_authority": False,
        "raw_secret_persisted": False,
        "created_at_utc": utc_now(),
    }


def run_alembic_upgrade(raw_url: str, reset_result: dict[str, Any]) -> dict[str, Any]:
    engine = create_engine(raw_url)
    try:
        with engine.connect() as conn:
            before_revision = current_revision(conn)
            before_schema_hash = sha256_json(schema_rows(conn))
    finally:
        engine.dispose()

    command.upgrade(alembic_config(raw_url), "head")

    engine = create_engine(raw_url)
    try:
        with engine.connect() as conn:
            after_revision = current_revision(conn)
            after_schema = schema_rows(conn)
    finally:
        engine.dispose()

    return {
        "status": "migrated",
        "target_alias": TARGET_ALIAS,
        "expected_head": EXPECTED_HEAD,
        "sole_head": EXPECTED_HEAD,
        "before_revision": before_revision,
        "after_revision": after_revision,
        "schema_after_reset_sha256": reset_result["schema_after_reset_sha256"],
        "schema_before_migration_sha256": before_schema_hash,
        "schema_after_migration_sha256": sha256_json(after_schema),
        "alembic_upgrade_head_ran": True,
        "manual_sql_used": False,
        "provider_call_count_delta": 0,
        "generated_content_row_delta": 0,
        "audio_synthesis_count_delta": 0,
        "export_count_delta": 0,
        "production_authority": False,
        "raw_secret_persisted": False,
        "created_at_utc": utc_now(),
    }


def phase32_columns_present(conn) -> tuple[bool, dict[str, list[str]]]:
    missing: dict[str, list[str]] = {}
    inspector = inspect(conn)
    for table_name, expected_columns in PHASE32_COLUMNS.items():
        present = {column["name"] for column in inspector.get_columns(table_name)} if inspector.has_table(table_name) else set()
        table_missing = [column for column in expected_columns if column not in present]
        if table_missing:
            missing[table_name] = table_missing
    return not missing, missing


def validate_after_migration(raw_url: str, preflight: dict[str, Any]) -> dict[str, Any]:
    engine = create_engine(raw_url)
    try:
        with engine.connect() as conn:
            before_provision_revision = current_revision(conn)
            before_counts = count_public_rows(conn, {row["table_name"] for row in app_table_locations(conn) if row["table_schema"] == "public"})
            before_total = total_existing_rows(before_counts)
        ensure_database_schema(engine, raw_url)
        with engine.connect() as conn:
            after_provision_revision = current_revision(conn)
            locations = app_table_locations(conn)
            public_tables = {row["table_name"] for row in locations if row["table_schema"] == "public"}
            counts = count_public_rows(conn, public_tables)
            after_total = total_existing_rows(counts)
            schema_poststate = schema_rows(conn)
            current = current_revision(conn)
            phase32_ok, missing_phase32 = phase32_columns_present(conn)
            phase33_present = all(table_name in public_tables for table_name in PHASE33_TABLES)
    finally:
        engine.dispose()

    return {
        "status": "passed"
        if current == EXPECTED_HEAD and phase32_ok and phase33_present and after_total == 0
        else "failed",
        "target_alias": TARGET_ALIAS,
        "target_matches_plan_32_47": True,
        "current_revision": current,
        "expected_head": EXPECTED_HEAD,
        "sole_head": EXPECTED_HEAD,
        "phase32_revision": PHASE32_REVISION,
        "phase32_columns_present": phase32_ok,
        "phase32_missing_columns": missing_phase32,
        "phase33_tables_present": phase33_present,
        "phase33_head_acknowledged": True,
        "runtime_provisioning_revision_before": before_provision_revision,
        "runtime_provisioning_revision_after": after_provision_revision,
        "runtime_provisioning_row_count_delta": after_total - before_total,
        "application_row_counts": counts,
        "application_row_counts_sha256": sha256_json(counts),
        "all_application_row_counts_zero": after_total == 0,
        "unexpected_row_mutation_count": after_total,
        "schema_poststate_sha256": sha256_json(schema_poststate),
        "schema_poststate_column_count": len(schema_poststate),
        "provider_call_count_delta": 0,
        "generated_content_row_delta": 0,
        "audio_synthesis_count_delta": 0,
        "export_count_delta": 0,
        "production_ready": False,
        "production_authority": False,
        "raw_secret_persisted": False,
        "created_at_utc": utc_now(),
        "preflight_row_count_total_destroyed": preflight["pre_reset_row_count_total"],
    }


def write_summary(validation: dict[str, Any], reset_result: dict[str, Any], migration_result: dict[str, Any]) -> None:
    body = "\n".join(
        [
            "# Phase 32 Plan 48 Summary: Disposable DB Reset And Migration Rehearsal",
            "",
            "## Status",
            "- Result: completed for disposable/test rehearsal only." if validation["status"] == "passed" else "- Result: failed or blocked before completion.",
            "- Public schema reset: completed." if reset_result["status"] == "public_schema_reset_completed" else "- Public schema reset: not completed.",
            "- Alembic migration: current head `20260828_19`." if migration_result.get("after_revision") == EXPECTED_HEAD else "- Alembic migration: not at expected head.",
            "- Production authority: false.",
            "- Phase 32 status: remains in progress.",
            "",
            "## What Changed",
            "- Added an audited phase-local reset helper for the disposable/test rehearsal.",
            "- Recorded sanitized destructive authorization from the user's `Wipe Current DB` choice.",
            "- Revalidated the exact Plan 32-47 target hashes before destructive DDL.",
            "- Reset only the disposable target's `public` schema and did not drop the database, roles, or non-public schemas.",
            "- Ran Alembic `upgrade head` and validated runtime provisioning as a no-op at head.",
            "",
            "## Evidence",
            "- `disposable-database-reset-authorization.md`: destructive authorization and production boundary.",
            "- `disposable-database-reset-preflight.json`: target-match and reset-readiness evidence.",
            "- `disposable-database-reset-result.json`: fixed public-schema reset result and destroyed row counts only.",
            "- `disposable-database-after-reset-migration-result.json`: Alembic after-reset migration result.",
            "- `disposable-database-after-reset-validation.json`: current-head, zero-row, runtime no-op, and non-production validation.",
            "",
            "## Key Results",
            "- Destroyed disposable row count: " + str(reset_result["destroyed_row_count_total"]) + ".",
            "- Current Alembic revision after migration: `" + str(validation["current_revision"]) + "`.",
            "- Phase 32 evidence columns present: " + str(validation["phase32_columns_present"]).lower() + ".",
            "- Phase 33 DDL acknowledged as current-head rehearsal only: " + str(validation["phase33_head_acknowledged"]).lower() + ".",
            "- All application row counts zero after migration: " + str(validation["all_application_row_counts_zero"]).lower() + ".",
            "",
            "## Boundary",
            "- This proves only disposable/test reset and migration rehearsal against the current Alembic head.",
            "- This does not prove production database readiness.",
            "- This does not authorize provider calls, text generation, audio synthesis, review application, export, release, publication, delivery, commit, PR, or Phase 32 closure.",
            "",
        ]
    )
    SUMMARY_PATH.write_text(body, encoding="utf-8")


def execute_reset_and_migrate() -> int:
    raw_url = load_raw_url()
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    preflight = collect_reset_preflight(raw_url)
    write_authorization(raw_url, preflight)
    write_json(RESET_PREFLIGHT_PATH, preflight)
    leak_check(raw_url, [AUTHORIZATION_PATH, RESET_PREFLIGHT_PATH])
    if preflight["status"] != "ready_for_public_schema_reset":
        print("blocked: " + str(preflight["blocked_reason"]), file=sys.stderr)
        return 2

    try:
        reset_result = reset_public_schema(raw_url, preflight)
    except Exception:
        reset_result = {
            "status": "reset_failed",
            "target_alias": TARGET_ALIAS,
            "fixed_public_schema_reset": True,
            "statement_ids": ["drop_public_schema_cascade", "create_public_schema"],
            "manual_sql_used": False,
            "database_dropped": False,
            "roles_dropped": False,
            "non_public_schemas_dropped": False,
            "before_revision": preflight["current_revision"],
            "pre_reset_row_counts": preflight["pre_reset_row_counts"],
            "pre_reset_allowed_public_row_counts": preflight["pre_reset_allowed_public_row_counts"],
            "pre_reset_allowed_public_row_counts_sha256": preflight[
                "pre_reset_allowed_public_row_counts_sha256"
            ],
            "destroyed_row_count_total": preflight["pre_reset_row_count_total"],
            "destroyed_public_base_row_count_total": preflight["pre_reset_all_public_base_row_count_total"],
            "schema_pre_reset_sha256": preflight["schema_pre_reset_sha256"],
            **failure_envelope(raw_url, "public_schema_reset", "reset_failed"),
        }
        write_json(RESET_RESULT_PATH, reset_result)
        migration_result = not_run_result(raw_url, "not_run_reset_failed", "public_schema_reset", "reset_failed")
        validation = not_run_result(raw_url, "not_run_reset_failed", "public_schema_reset", "reset_failed")
        write_json(MIGRATION_RESULT_PATH, migration_result)
        write_json(VALIDATION_PATH, validation)
        leak_check(raw_url, [AUTHORIZATION_PATH, RESET_PREFLIGHT_PATH, RESET_RESULT_PATH, MIGRATION_RESULT_PATH, VALIDATION_PATH])
        print("blocked: reset_failed", file=sys.stderr)
        return 2
    write_json(RESET_RESULT_PATH, reset_result)
    if (
        reset_result["after_revision"] is not None
        or reset_result["post_reset_application_table_count"] != 0
        or reset_result["public_schema_exists_after_reset"] is not True
    ):
        reset_result.update(
            {
                "status": "reset_poststate_invalid",
                **failure_envelope(raw_url, "public_schema_reset_poststate", "reset_poststate_invalid"),
            }
        )
        write_json(RESET_RESULT_PATH, reset_result)
        migration_result = not_run_result(
            raw_url,
            "not_run_reset_poststate_invalid",
            "public_schema_reset_poststate",
            "reset_poststate_invalid",
        )
        validation = not_run_result(
            raw_url,
            "not_run_reset_poststate_invalid",
            "public_schema_reset_poststate",
            "reset_poststate_invalid",
        )
        write_json(MIGRATION_RESULT_PATH, migration_result)
        write_json(VALIDATION_PATH, validation)
        leak_check(raw_url, [RESET_RESULT_PATH, MIGRATION_RESULT_PATH, VALIDATION_PATH])
        print("blocked: reset_poststate_invalid", file=sys.stderr)
        return 2

    try:
        migration_result = run_alembic_upgrade(raw_url, reset_result)
    except Exception:
        migration_result = {
            "status": "migration_failed",
            "target_alias": TARGET_ALIAS,
            "expected_head": EXPECTED_HEAD,
            "alembic_upgrade_head_ran": True,
            "manual_sql_used": False,
            **failure_envelope(raw_url, "alembic_upgrade_head", "migration_failed"),
        }
        write_json(MIGRATION_RESULT_PATH, migration_result)
        validation = not_run_result(raw_url, "not_run_migration_failed", "alembic_upgrade_head", "migration_failed")
        write_json(VALIDATION_PATH, validation)
        leak_check(raw_url, [RESET_RESULT_PATH, MIGRATION_RESULT_PATH, VALIDATION_PATH])
        print("blocked: migration_failed", file=sys.stderr)
        return 2
    write_json(MIGRATION_RESULT_PATH, migration_result)
    if migration_result["after_revision"] != EXPECTED_HEAD:
        migration_result.update(
            {
                "status": "migration_incomplete",
                **failure_envelope(raw_url, "alembic_upgrade_head", "unexpected_after_revision"),
            }
        )
        write_json(MIGRATION_RESULT_PATH, migration_result)
        validation = not_run_result(
            raw_url,
            "not_run_migration_incomplete",
            "alembic_upgrade_head",
            "unexpected_after_revision",
        )
        write_json(VALIDATION_PATH, validation)
        leak_check(raw_url, [RESET_RESULT_PATH, MIGRATION_RESULT_PATH, VALIDATION_PATH])
        print("blocked: migration_incomplete", file=sys.stderr)
        return 2

    try:
        validation = validate_after_migration(raw_url, preflight)
    except Exception:
        validation = {
            "status": "validation_failed",
            "target_alias": TARGET_ALIAS,
            "target_matches_plan_32_47": True,
            "current_revision": None,
            "expected_head": EXPECTED_HEAD,
            "sole_head": EXPECTED_HEAD,
            "phase32_revision": PHASE32_REVISION,
            "phase32_columns_present": False,
            "phase32_missing_columns": {},
            "phase33_tables_present": False,
            "phase33_head_acknowledged": True,
            "runtime_provisioning_revision_before": None,
            "runtime_provisioning_revision_after": None,
            "runtime_provisioning_row_count_delta": 0,
            "application_row_counts": {},
            "application_row_counts_sha256": sha256_json({}),
            "all_application_row_counts_zero": False,
            "unexpected_row_mutation_count": 0,
            "schema_poststate_sha256": None,
            "schema_poststate_column_count": 0,
            "production_ready": False,
            "preflight_row_count_total_destroyed": preflight["pre_reset_row_count_total"],
            **failure_envelope(raw_url, "post_migration_validation", "validation_exception"),
        }
        write_json(VALIDATION_PATH, validation)
        write_summary(validation, reset_result, migration_result)
        leak_check(raw_url, [RESET_RESULT_PATH, MIGRATION_RESULT_PATH, VALIDATION_PATH, SUMMARY_PATH])
        print("blocked: validation_exception", file=sys.stderr)
        return 2
    if validation["status"] != "passed":
        validation.update(failure_envelope(raw_url, "post_migration_validation", "validation_failed"))
    write_json(VALIDATION_PATH, validation)
    write_summary(validation, reset_result, migration_result)
    leak_check(
        raw_url,
        [
            AUTHORIZATION_PATH,
            RESET_PREFLIGHT_PATH,
            RESET_RESULT_PATH,
            MIGRATION_RESULT_PATH,
            VALIDATION_PATH,
            SUMMARY_PATH,
            PHASE_DIR / "32-48-PLAN.md",
            TOOLS_DIR / "disposable_database_reset_rehearsal.py",
        ],
    )
    if validation["status"] != "passed":
        print("blocked: validation_failed", file=sys.stderr)
        return 2
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Disposable/test DB reset and migration rehearsal helper")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--preflight-only", action="store_true")
    group.add_argument("--execute-reset-and-migrate", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.preflight_only:
        return preflight_only()
    if args.execute_reset_and_migrate:
        return execute_reset_and_migrate()
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
        print("blocked: sanitized reset rehearsal failure", file=sys.stderr)
        raise SystemExit(2)
