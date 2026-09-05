"""Add Phase 33 grammar and personal-source evidence schema."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260828_19"
down_revision = "20260821_18"
branch_labels = None
depends_on = None


_APPEND_ONLY_TABLES = (
    "korean_grammar_bundles",
    "korean_grammar_members",
    "personal_source_rows",
    "personal_source_decisions",
    "highlight_private_excerpt_revisions",
    "private_disclosure_attempts",
    "private_processing_receipts",
    "review_field_revisions",
    "review_decisions",
    "review_access_events",
    "item_terminal_status_events",
    "item_processing_facts",
    "generation_run_denominators",
    "audio_publication_transitions",
    "audio_revision_evidence",
)


def upgrade() -> None:
    op.create_table(
        "korean_grammar_bundles",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("bundle_id", sa.String(length=160), nullable=False),
        sa.Column("bundle_sha256", sa.String(length=64), nullable=False),
        sa.Column("source_kind", sa.String(length=64), nullable=False),
        sa.Column("source_sha256", sa.String(length=64), nullable=False),
        sa.Column("version", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("sequence_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("bundle_id", name="uq_korean_grammar_bundles_bundle_id"),
        sa.CheckConstraint(_sha256_check("bundle_sha256"), name="ck_korean_grammar_bundles_bundle_sha256"),
        sa.CheckConstraint(_sha256_check("source_sha256"), name="ck_korean_grammar_bundles_source_sha256"),
        sa.CheckConstraint("sequence_count >= 0", name="ck_korean_grammar_bundles_sequence_count"),
        sa.CheckConstraint("status IN ('draft','active','retired')", name="ck_korean_grammar_bundles_status"),
    )
    op.create_index("ix_korean_grammar_bundles_status", "korean_grammar_bundles", ["status"], unique=False)

    op.create_table(
        "korean_grammar_members",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("bundle_id", sa.String(length=36), sa.ForeignKey("korean_grammar_bundles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("construction_id", sa.String(length=160), nullable=False),
        sa.Column("sequence_index", sa.Integer(), nullable=False),
        sa.Column("form", sa.String(length=255), nullable=False),
        sa.Column("function_label", sa.String(length=255), nullable=False),
        sa.Column("register", sa.String(length=64), nullable=False),
        sa.Column("prerequisite_ids", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("member_sha256", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("bundle_id", "sequence_index", name="uq_korean_grammar_members_bundle_sequence"),
        sa.UniqueConstraint("bundle_id", "construction_id", name="uq_korean_grammar_members_bundle_construction"),
        sa.CheckConstraint("sequence_index >= 1", name="ck_korean_grammar_members_sequence_index"),
        sa.CheckConstraint(_sha256_check("member_sha256"), name="ck_korean_grammar_members_member_sha256"),
    )
    op.create_index("ix_korean_grammar_members_bundle_id", "korean_grammar_members", ["bundle_id"], unique=False)
    op.create_index("ix_korean_grammar_members_construction_id", "korean_grammar_members", ["construction_id"], unique=False)

    op.create_table(
        "personal_source_rows",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("job_id", sa.String(length=36), sa.ForeignKey("generation_jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("item_key", sa.String(length=255), nullable=False),
        sa.Column("source_type", sa.String(length=32), nullable=False),
        sa.Column("input_position", sa.Integer(), nullable=False),
        sa.Column("submitted_form", sa.String(length=255), nullable=False),
        sa.Column("normalized_form", sa.String(length=255), nullable=False),
        sa.Column("source_row_sha256", sa.String(length=64), nullable=False),
        sa.Column("parser_version", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("job_id", "source_type", "input_position", name="uq_personal_source_rows_position"),
        sa.UniqueConstraint("job_id", "source_type", "source_row_sha256", name="uq_personal_source_rows_source_row_sha256"),
        sa.CheckConstraint("input_position >= 1", name="ck_personal_source_rows_input_position"),
        sa.CheckConstraint(_sha256_check("source_row_sha256"), name="ck_personal_source_rows_source_row_sha256"),
    )
    op.create_index("ix_personal_source_rows_job_id_item_key", "personal_source_rows", ["job_id", "item_key"], unique=False)
    op.create_index("ix_personal_source_rows_source_type", "personal_source_rows", ["source_type"], unique=False)

    op.create_table(
        "personal_source_decisions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("row_id", sa.String(length=36), sa.ForeignKey("personal_source_rows.id", ondelete="CASCADE"), nullable=False),
        sa.Column("decision_revision", sa.Integer(), nullable=False),
        sa.Column("resolved_lemma", sa.String(length=255), nullable=True),
        sa.Column("resolved_pos", sa.String(length=64), nullable=True),
        sa.Column("resolved_sense_id", sa.String(length=255), nullable=True),
        sa.Column("decision_state", sa.String(length=32), nullable=False),
        sa.Column("decision_reason_code", sa.String(length=64), nullable=True),
        sa.Column("korean_identity_sha256", sa.String(length=64), nullable=True),
        sa.Column("prerequisite_ids", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("row_id", "decision_revision", name="uq_personal_source_decisions_row_revision"),
        sa.CheckConstraint("decision_revision >= 1", name="ck_personal_source_decisions_revision"),
        sa.CheckConstraint(
            "decision_state IN ('accepted','duplicate','bridge','defer','needs_review','rejected')",
            name="ck_personal_source_decisions_state",
        ),
        sa.CheckConstraint(_nullable_sha256_check("korean_identity_sha256"), name="ck_personal_source_decisions_identity_sha256"),
    )
    op.create_index("ix_personal_source_decisions_row_id", "personal_source_decisions", ["row_id"], unique=False)
    op.create_index("ix_personal_source_decisions_state", "personal_source_decisions", ["decision_state"], unique=False)

    op.create_table(
        "highlight_private_excerpt_revisions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("job_id", sa.String(length=36), sa.ForeignKey("generation_jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("excerpt_revision_id", sa.String(length=160), nullable=False),
        sa.Column("highlight_id", sa.String(length=255), nullable=False),
        sa.Column("import_content_hash", sa.String(length=64), nullable=False),
        sa.Column("source_content_hash", sa.String(length=64), nullable=False),
        sa.Column("source_index", sa.Integer(), nullable=False),
        sa.Column("source_path", sa.String(length=512), nullable=False),
        sa.Column("raw_location", sa.String(length=256), nullable=True),
        sa.Column("normalized_text", sa.Text(), nullable=False),
        sa.Column("revision_number", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("excerpt_revision_id", name="uq_highlight_private_excerpt_revisions_revision_id"),
        sa.UniqueConstraint("job_id", "highlight_id", "revision_number", name="uq_highlight_private_excerpt_revisions_job_highlight_revision"),
        sa.CheckConstraint("source_index >= 0", name="ck_highlight_private_excerpt_revisions_source_index"),
        sa.CheckConstraint("revision_number >= 1", name="ck_highlight_private_excerpt_revisions_revision_number"),
        sa.CheckConstraint(_sha256_check("import_content_hash"), name="ck_highlight_private_excerpt_revisions_import_hash"),
        sa.CheckConstraint(_sha256_check("source_content_hash"), name="ck_highlight_private_excerpt_revisions_source_hash"),
    )
    op.create_index("ix_highlight_private_excerpt_revisions_job_highlight", "highlight_private_excerpt_revisions", ["job_id", "highlight_id"], unique=False)

    op.create_table(
        "private_context_capabilities",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("capability_id", sa.String(length=160), nullable=False),
        sa.Column("job_id", sa.String(length=36), sa.ForeignKey("generation_jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("run_id", sa.String(length=160), nullable=False),
        sa.Column("item_id", sa.String(length=160), nullable=False),
        sa.Column("excerpt_revision_id", sa.String(length=160), nullable=False),
        sa.Column("excerpt_sha256", sa.String(length=64), nullable=False),
        sa.Column("target_start", sa.Integer(), nullable=False),
        sa.Column("target_end", sa.Integer(), nullable=False),
        sa.Column("target_text_sha256", sa.String(length=64), nullable=False),
        sa.Column("provider_id", sa.String(length=160), nullable=False),
        sa.Column("provider", sa.String(length=160), nullable=False),
        sa.Column("model", sa.String(length=160), nullable=False),
        sa.Column("route_id", sa.String(length=160), nullable=False),
        sa.Column("provider_route_sha256", sa.String(length=64), nullable=False),
        sa.Column("purpose", sa.String(length=160), nullable=False),
        sa.Column("policy_version", sa.String(length=160), nullable=False),
        sa.Column("policy_sha256", sa.String(length=64), nullable=False),
        sa.Column("tokenization_rule_id", sa.String(length=64), nullable=False),
        sa.Column("max_context_tokens", sa.Integer(), nullable=False),
        sa.Column("max_context_code_points", sa.Integer(), nullable=False),
        sa.Column("max_context_utf8_bytes", sa.Integer(), nullable=False),
        sa.Column("max_provider_attempts", sa.Integer(), nullable=False),
        sa.Column("max_estimated_cost_usd", sa.Float(), nullable=False),
        sa.Column("idempotency_support", sa.String(length=16), nullable=False),
        sa.Column("idempotency_key_sha256", sa.String(length=64), nullable=True),
        sa.Column("state", sa.String(length=32), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("issuer_id", sa.String(length=160), nullable=False),
        sa.Column("issuer_intent_sha256", sa.String(length=64), nullable=False),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("capability_id", name="uq_private_context_capabilities_capability_id"),
        sa.UniqueConstraint("idempotency_key_sha256", name="uq_private_context_capabilities_idempotency_key_sha256"),
        sa.CheckConstraint("target_end > target_start", name="ck_private_context_capabilities_target_span"),
        sa.CheckConstraint("max_context_tokens BETWEEN 1 AND 24", name="ck_private_context_capabilities_token_cap"),
        sa.CheckConstraint("max_context_code_points >= 1", name="ck_private_context_capabilities_code_points"),
        sa.CheckConstraint("max_context_utf8_bytes >= max_context_code_points", name="ck_private_context_capabilities_utf8_bytes"),
        sa.CheckConstraint("max_provider_attempts BETWEEN 1 AND 2", name="ck_private_context_capabilities_attempts"),
        sa.CheckConstraint("idempotency_support IN ('supported','unsupported')", name="ck_private_context_capabilities_idempotency_support"),
        sa.CheckConstraint(
            "(idempotency_support = 'supported' AND idempotency_key_sha256 IS NOT NULL) OR "
            "(idempotency_support = 'unsupported' AND idempotency_key_sha256 IS NULL)",
            name="ck_private_context_capabilities_idempotency_key",
        ),
        sa.CheckConstraint("tokenization_rule_id = 'phase33-private-token-v1'", name="ck_private_context_capabilities_token_rule"),
        sa.CheckConstraint("state IN ('pending','disclosing','disclosed','failed_unknown')", name="ck_private_context_capabilities_state"),
        sa.CheckConstraint("version >= 0", name="ck_private_context_capabilities_version"),
        sa.CheckConstraint(_sha256_check("excerpt_sha256"), name="ck_private_context_capabilities_excerpt_sha256"),
        sa.CheckConstraint(_sha256_check("target_text_sha256"), name="ck_private_context_capabilities_target_sha256"),
        sa.CheckConstraint(_sha256_check("provider_route_sha256"), name="ck_private_context_capabilities_route_sha256"),
        sa.CheckConstraint(_sha256_check("policy_sha256"), name="ck_private_context_capabilities_policy_sha256"),
        sa.CheckConstraint(_sha256_check("issuer_intent_sha256"), name="ck_private_context_capabilities_issuer_sha256"),
        sa.CheckConstraint(_nullable_sha256_check("idempotency_key_sha256"), name="ck_private_context_capabilities_idempotency_sha256"),
    )
    op.create_index("ix_private_context_capabilities_job_id", "private_context_capabilities", ["job_id"], unique=False)
    op.create_index("ix_private_context_capabilities_item_state", "private_context_capabilities", ["item_id", "state"], unique=False)
    op.create_index("ix_private_context_capabilities_cas", "private_context_capabilities", ["capability_id", "state", "version"], unique=False)

    op.create_table(
        "private_disclosure_attempts",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("capability_id", sa.String(length=160), nullable=False),
        sa.Column("state", sa.String(length=32), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("context_sha256", sa.String(length=64), nullable=True),
        sa.Column("context_token_count", sa.Integer(), nullable=True),
        sa.Column("refusal_reason_code", sa.String(length=64), nullable=True),
        sa.Column("attempted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("capability_id", "version", name="uq_private_disclosure_attempts_capability_version"),
        sa.CheckConstraint("state IN ('pending','disclosing','disclosed','failed_unknown')", name="ck_private_disclosure_attempts_state"),
        sa.CheckConstraint("version >= 0", name="ck_private_disclosure_attempts_version"),
        sa.CheckConstraint("context_token_count IS NULL OR context_token_count BETWEEN 1 AND 24", name="ck_private_disclosure_attempts_token_count"),
        sa.CheckConstraint(_nullable_sha256_check("context_sha256"), name="ck_private_disclosure_attempts_context_sha256"),
    )
    op.create_index("ix_private_disclosure_attempts_capability_id", "private_disclosure_attempts", ["capability_id"], unique=False)

    op.create_table(
        "private_processing_receipts",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("receipt_id", sa.String(length=160), nullable=False),
        sa.Column("capability_id", sa.String(length=160), nullable=False),
        sa.Column("receipt_sha256", sa.String(length=64), nullable=False),
        sa.Column("context_sha256", sa.String(length=64), nullable=False),
        sa.Column("context_token_count", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(length=160), nullable=False),
        sa.Column("model", sa.String(length=160), nullable=False),
        sa.Column("route_id", sa.String(length=160), nullable=False),
        sa.Column("policy_sha256", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("receipt_id", name="uq_private_processing_receipts_receipt_id"),
        sa.UniqueConstraint("receipt_sha256", name="uq_private_processing_receipts_receipt_sha256"),
        sa.CheckConstraint("context_token_count BETWEEN 1 AND 24", name="ck_private_processing_receipts_context_token_count"),
        sa.CheckConstraint(_sha256_check("receipt_sha256"), name="ck_private_processing_receipts_receipt_sha256"),
        sa.CheckConstraint(_sha256_check("context_sha256"), name="ck_private_processing_receipts_context_sha256"),
        sa.CheckConstraint(_sha256_check("policy_sha256"), name="ck_private_processing_receipts_policy_sha256"),
    )
    op.create_index("ix_private_processing_receipts_capability_id", "private_processing_receipts", ["capability_id"], unique=False)

    op.create_table(
        "review_field_revisions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("job_id", sa.String(length=36), sa.ForeignKey("generation_jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("item_id", sa.String(length=255), nullable=False),
        sa.Column("field_name", sa.String(length=64), nullable=False),
        sa.Column("revision_no", sa.Integer(), nullable=False),
        sa.Column("value_sha256", sa.String(length=64), nullable=False),
        sa.Column("generator_id", sa.String(length=160), nullable=False),
        sa.Column("generator_version", sa.String(length=160), nullable=False),
        sa.Column("route_id", sa.String(length=160), nullable=True),
        sa.Column("previous_revision_sha256", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("job_id", "item_id", "field_name", "revision_no", name="uq_review_field_revisions_item_field_revision"),
        sa.CheckConstraint("revision_no >= 1", name="ck_review_field_revisions_revision_no"),
        sa.CheckConstraint(_sha256_check("value_sha256"), name="ck_review_field_revisions_value_sha256"),
        sa.CheckConstraint(_nullable_sha256_check("previous_revision_sha256"), name="ck_review_field_revisions_previous_sha256"),
    )
    op.create_index("ix_review_field_revisions_item_field", "review_field_revisions", ["job_id", "item_id", "field_name"], unique=False)

    op.create_table(
        "review_current_pointers",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("job_id", sa.String(length=36), sa.ForeignKey("generation_jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("item_id", sa.String(length=255), nullable=False),
        sa.Column("field_name", sa.String(length=64), nullable=False),
        sa.Column("current_revision_id", sa.String(length=36), sa.ForeignKey("review_field_revisions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("pointer_version", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("review_status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("job_id", "item_id", "field_name", name="uq_review_current_pointers_item_field"),
        sa.CheckConstraint("pointer_version >= 0", name="ck_review_current_pointers_version"),
        sa.CheckConstraint("review_status IN ('needs_review','approved','rejected')", name="ck_review_current_pointers_status"),
    )
    op.create_index("ix_review_current_pointers_item_field", "review_current_pointers", ["job_id", "item_id", "field_name"], unique=False)
    op.create_index("ix_review_current_pointers_status", "review_current_pointers", ["review_status"], unique=False)

    op.create_table(
        "review_decisions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("job_id", sa.String(length=36), sa.ForeignKey("generation_jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("item_id", sa.String(length=255), nullable=False),
        sa.Column("field_name", sa.String(length=64), nullable=False),
        sa.Column("revision_id", sa.String(length=36), sa.ForeignKey("review_field_revisions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("decision_revision", sa.Integer(), nullable=False),
        sa.Column("review_status", sa.String(length=32), nullable=False),
        sa.Column("reviewer_id_sha256", sa.String(length=64), nullable=True),
        sa.Column("decision_sha256", sa.String(length=64), nullable=False),
        sa.Column("reason_code", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("revision_id", "decision_revision", name="uq_review_decisions_revision_decision"),
        sa.CheckConstraint("decision_revision >= 1", name="ck_review_decisions_revision"),
        sa.CheckConstraint("review_status IN ('needs_review','approved','rejected')", name="ck_review_decisions_status"),
        sa.CheckConstraint(_nullable_sha256_check("reviewer_id_sha256"), name="ck_review_decisions_reviewer_sha256"),
        sa.CheckConstraint(_sha256_check("decision_sha256"), name="ck_review_decisions_decision_sha256"),
    )
    op.create_index("ix_review_decisions_revision_id", "review_decisions", ["revision_id"], unique=False)
    op.create_index("ix_review_decisions_item_field", "review_decisions", ["job_id", "item_id", "field_name"], unique=False)

    op.create_table(
        "review_access_events",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("actor_id", sa.String(length=160), nullable=False),
        sa.Column("request_id", sa.String(length=160), nullable=False),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("command_sha256", sa.String(length=64), nullable=False),
        sa.Column("result_id_sha256", sa.String(length=64), nullable=False),
        sa.Column("result_hash_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("policy_sha256", sa.String(length=64), nullable=False),
        sa.Column("snapshot_sha256", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("actor_id", "request_id", "action", name="uq_review_access_events_stable_identity"),
        sa.CheckConstraint("action IN ('list','inspect','private_display','approve','reject','edit','regenerate')", name="ck_review_access_events_action"),
        sa.CheckConstraint("result_hash_count >= 0", name="ck_review_access_events_result_count"),
        sa.CheckConstraint(_sha256_check("command_sha256"), name="ck_review_access_events_command_sha256"),
        sa.CheckConstraint(_sha256_check("result_id_sha256"), name="ck_review_access_events_result_id_sha256"),
        sa.CheckConstraint(_sha256_check("policy_sha256"), name="ck_review_access_events_policy_sha256"),
        sa.CheckConstraint(_sha256_check("snapshot_sha256"), name="ck_review_access_events_snapshot_sha256"),
    )
    op.create_index("ix_review_access_events_actor_request", "review_access_events", ["actor_id", "request_id"], unique=False)

    op.create_table(
        "item_terminal_status_events",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("job_id", sa.String(length=36), sa.ForeignKey("generation_jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("item_id", sa.String(length=255), nullable=False),
        sa.Column("stage", sa.String(length=64), nullable=False),
        sa.Column("terminal_status", sa.String(length=32), nullable=False),
        sa.Column("reason_code", sa.String(length=64), nullable=True),
        sa.Column("event_sha256", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("job_id", "item_id", "stage", name="uq_item_terminal_status_events_item_stage"),
        sa.UniqueConstraint("event_sha256", name="uq_item_terminal_status_events_event_sha256"),
        sa.CheckConstraint("terminal_status IN ('accepted','review_required','failed')", name="ck_item_terminal_status_events_status"),
        sa.CheckConstraint(_sha256_check("event_sha256"), name="ck_item_terminal_status_events_event_sha256"),
    )
    op.create_index("ix_item_terminal_status_events_status_job", "item_terminal_status_events", ["terminal_status", "job_id"], unique=False)

    op.create_table(
        "item_processing_facts",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("job_id", sa.String(length=36), sa.ForeignKey("generation_jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("item_id", sa.String(length=255), nullable=False),
        sa.Column("stage", sa.String(length=64), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False),
        sa.Column("attempted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("fact_sha256", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("job_id", "item_id", "stage", "attempt_count", name="uq_item_processing_facts_attempt"),
        sa.UniqueConstraint("fact_sha256", name="uq_item_processing_facts_fact_sha256"),
        sa.CheckConstraint("attempt_count >= 0", name="ck_item_processing_facts_attempt_count"),
        sa.CheckConstraint(_sha256_check("fact_sha256"), name="ck_item_processing_facts_fact_sha256"),
    )
    op.create_index("ix_item_processing_facts_job_item", "item_processing_facts", ["job_id", "item_id"], unique=False)

    op.create_table(
        "generation_run_denominators",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("job_id", sa.String(length=36), sa.ForeignKey("generation_jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("stage", sa.String(length=64), nullable=False),
        sa.Column("expected_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("accepted_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("review_required_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("denominator_sha256", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("job_id", "stage", name="uq_generation_run_denominators_job_stage"),
        sa.CheckConstraint("expected_count >= 0 AND accepted_count >= 0 AND review_required_count >= 0 AND failed_count >= 0", name="ck_generation_run_denominators_counts"),
        sa.CheckConstraint("accepted_count + review_required_count + failed_count <= expected_count", name="ck_generation_run_denominators_count_sum"),
        sa.CheckConstraint(_sha256_check("denominator_sha256"), name="ck_generation_run_denominators_sha256"),
    )
    op.create_index("ix_generation_run_denominators_job_stage", "generation_run_denominators", ["job_id", "stage"], unique=False)

    op.create_table(
        "audio_publication_reservations",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("job_id", sa.String(length=36), sa.ForeignKey("generation_jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("item_id", sa.String(length=255), nullable=False),
        sa.Column("field_name", sa.String(length=64), nullable=False),
        sa.Column("field_revision_id", sa.String(length=36), sa.ForeignKey("review_field_revisions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("request_sha256", sa.String(length=64), nullable=False),
        sa.Column("final_path", sa.String(length=512), nullable=False),
        sa.Column("final_path_sha256", sa.String(length=64), nullable=False),
        sa.Column("authority_sha256", sa.String(length=64), nullable=False),
        sa.Column("root_prestate_sha256", sa.String(length=64), nullable=False),
        sa.Column("expected_pointer_version", sa.Integer(), nullable=False),
        sa.Column("reservation_version", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("state", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("field_revision_id", name="uq_audio_publication_reservations_field_revision"),
        sa.UniqueConstraint("final_path_sha256", name="uq_audio_publication_reservations_final_path_sha256"),
        sa.CheckConstraint("expected_pointer_version >= 0 AND reservation_version >= 0", name="ck_audio_publication_reservations_versions"),
        sa.CheckConstraint("state IN ('reserved','staged','published','finalized','failed_unknown','blocked_mismatch')", name="ck_audio_publication_reservations_state"),
        sa.CheckConstraint(_sha256_check("request_sha256"), name="ck_audio_publication_reservations_request_sha256"),
        sa.CheckConstraint(_sha256_check("final_path_sha256"), name="ck_audio_publication_reservations_final_path_sha256"),
        sa.CheckConstraint(_sha256_check("authority_sha256"), name="ck_audio_publication_reservations_authority_sha256"),
        sa.CheckConstraint(_sha256_check("root_prestate_sha256"), name="ck_audio_publication_reservations_root_sha256"),
    )
    op.create_index("ix_audio_publication_reservations_item_field", "audio_publication_reservations", ["job_id", "item_id", "field_name"], unique=False)
    op.create_index("ix_audio_publication_reservations_state_job", "audio_publication_reservations", ["state", "job_id"], unique=False)

    op.create_table(
        "audio_publication_transitions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("reservation_id", sa.String(length=36), sa.ForeignKey("audio_publication_reservations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("from_state", sa.String(length=32), nullable=False),
        sa.Column("to_state", sa.String(length=32), nullable=False),
        sa.Column("expected_version", sa.Integer(), nullable=False),
        sa.Column("next_version", sa.Integer(), nullable=False),
        sa.Column("transition_sha256", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("reservation_id", "next_version", name="uq_audio_publication_transitions_reservation_version"),
        sa.UniqueConstraint("transition_sha256", name="uq_audio_publication_transitions_transition_sha256"),
        sa.CheckConstraint("next_version = expected_version + 1", name="ck_audio_publication_transitions_version_step"),
        sa.CheckConstraint(_audio_transition_check(), name="ck_audio_publication_transitions_allowed_step"),
        sa.CheckConstraint(_sha256_check("transition_sha256"), name="ck_audio_publication_transitions_transition_sha256"),
    )
    op.create_index("ix_audio_publication_transitions_reservation_id", "audio_publication_transitions", ["reservation_id"], unique=False)

    op.create_table(
        "audio_revision_evidence",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("reservation_id", sa.String(length=36), sa.ForeignKey("audio_publication_reservations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("field_revision_id", sa.String(length=36), sa.ForeignKey("review_field_revisions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("role", sa.String(length=64), nullable=False),
        sa.Column("root_sha256", sa.String(length=64), nullable=False),
        sa.Column("final_path_sha256", sa.String(length=64), nullable=False),
        sa.Column("request_sha256", sa.String(length=64), nullable=False),
        sa.Column("artifact_sha256", sa.String(length=64), nullable=False),
        sa.Column("byte_length", sa.Integer(), nullable=False),
        sa.Column("spoken_text_sha256", sa.String(length=64), nullable=False),
        sa.Column("voice_profile_sha256", sa.String(length=64), nullable=False),
        sa.Column("review_status", sa.String(length=32), nullable=False),
        sa.Column("reservation_state", sa.String(length=32), nullable=False),
        sa.Column("evidence_sha256", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("reservation_id", "role", name="uq_audio_revision_evidence_reservation_role"),
        sa.UniqueConstraint("evidence_sha256", name="uq_audio_revision_evidence_evidence_sha256"),
        sa.CheckConstraint("byte_length > 0", name="ck_audio_revision_evidence_byte_length"),
        sa.CheckConstraint("reservation_state = 'finalized'", name="ck_audio_revision_evidence_reservation_state"),
        sa.CheckConstraint("review_status = 'approved'", name="ck_audio_revision_evidence_review_status"),
        sa.CheckConstraint(_sha256_check("root_sha256"), name="ck_audio_revision_evidence_root_sha256"),
        sa.CheckConstraint(_sha256_check("final_path_sha256"), name="ck_audio_revision_evidence_final_path_sha256"),
        sa.CheckConstraint(_sha256_check("request_sha256"), name="ck_audio_revision_evidence_request_sha256"),
        sa.CheckConstraint(_sha256_check("artifact_sha256"), name="ck_audio_revision_evidence_artifact_sha256"),
        sa.CheckConstraint(_sha256_check("spoken_text_sha256"), name="ck_audio_revision_evidence_spoken_text_sha256"),
        sa.CheckConstraint(_sha256_check("voice_profile_sha256"), name="ck_audio_revision_evidence_voice_profile_sha256"),
        sa.CheckConstraint(_sha256_check("evidence_sha256"), name="ck_audio_revision_evidence_evidence_sha256"),
    )
    op.create_index("ix_audio_revision_evidence_reservation_id", "audio_revision_evidence", ["reservation_id"], unique=False)
    op.create_index("ix_audio_revision_evidence_final_path", "audio_revision_evidence", ["final_path_sha256"], unique=False)
    op.create_index("ix_audio_revision_evidence_artifact_sha256", "audio_revision_evidence", ["artifact_sha256"], unique=False)

    _create_append_only_guards()


def downgrade() -> None:
    _drop_append_only_guards()
    op.drop_table("audio_revision_evidence")
    op.drop_table("audio_publication_transitions")
    op.drop_table("audio_publication_reservations")
    op.drop_table("generation_run_denominators")
    op.drop_table("item_processing_facts")
    op.drop_table("item_terminal_status_events")
    op.drop_table("review_access_events")
    op.drop_table("review_decisions")
    op.drop_table("review_current_pointers")
    op.drop_table("review_field_revisions")
    op.drop_table("private_processing_receipts")
    op.drop_table("private_disclosure_attempts")
    op.drop_table("private_context_capabilities")
    op.drop_table("highlight_private_excerpt_revisions")
    op.drop_table("personal_source_decisions")
    op.drop_table("personal_source_rows")
    op.drop_table("korean_grammar_members")
    op.drop_table("korean_grammar_bundles")


def _sha256_check(column: str) -> str:
    stripped = column
    for char in "0123456789abcdef":
        stripped = f"replace({stripped}, '{char}', '')"
    return f"length({column}) = 64 AND length({stripped}) = 0"


def _nullable_sha256_check(column: str) -> str:
    return f"{column} IS NULL OR ({_sha256_check(column)})"


def _audio_transition_check() -> str:
    return " OR ".join(
        f"(from_state = '{from_state}' AND to_state = '{to_state}')"
        for from_state, to_state in (
            ("reserved", "staged"),
            ("reserved", "failed_unknown"),
            ("reserved", "blocked_mismatch"),
            ("staged", "published"),
            ("staged", "failed_unknown"),
            ("published", "finalized"),
            ("published", "failed_unknown"),
        )
    )


def _create_append_only_guards() -> None:
    dialect = op.get_bind().dialect.name
    if dialect == "postgresql":
        op.execute(
            """
            CREATE OR REPLACE FUNCTION phase33_reject_append_only_mutation()
            RETURNS trigger AS $$
            BEGIN
                RAISE EXCEPTION 'phase33 append-only table cannot be mutated';
            END;
            $$ LANGUAGE plpgsql;
            """
        )
        for table_name in _APPEND_ONLY_TABLES:
            op.execute(
                f"CREATE TRIGGER trg_{table_name}_append_only "
                f"BEFORE UPDATE OR DELETE ON {table_name} "
                "FOR EACH ROW EXECUTE FUNCTION phase33_reject_append_only_mutation()"
            )
        return
    if dialect == "sqlite":
        for table_name in _APPEND_ONLY_TABLES:
            op.execute(
                f"CREATE TRIGGER trg_{table_name}_append_only_update "
                f"BEFORE UPDATE ON {table_name} "
                f"BEGIN SELECT RAISE(ABORT, '{table_name} is append-only'); END"
            )
            op.execute(
                f"CREATE TRIGGER trg_{table_name}_append_only_delete "
                f"BEFORE DELETE ON {table_name} "
                f"BEGIN SELECT RAISE(ABORT, '{table_name} is append-only'); END"
            )


def _drop_append_only_guards() -> None:
    dialect = op.get_bind().dialect.name
    if dialect == "postgresql":
        for table_name in _APPEND_ONLY_TABLES:
            op.execute(f"DROP TRIGGER IF EXISTS trg_{table_name}_append_only ON {table_name}")
        op.execute("DROP FUNCTION IF EXISTS phase33_reject_append_only_mutation()")
        return
    if dialect == "sqlite":
        for table_name in _APPEND_ONLY_TABLES:
            op.execute(f"DROP TRIGGER IF EXISTS trg_{table_name}_append_only_update")
            op.execute(f"DROP TRIGGER IF EXISTS trg_{table_name}_append_only_delete")
