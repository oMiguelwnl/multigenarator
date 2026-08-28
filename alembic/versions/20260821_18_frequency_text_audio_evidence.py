"""Add Phase 32 frequency text audio evidence fields."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260821_18"
down_revision = "20260804_17"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("generation_jobs", sa.Column("korean_phase31_pointer_locator_sha256", sa.String(length=64), nullable=True))
    op.add_column("generation_jobs", sa.Column("korean_phase31_pointer_content_sha256", sa.String(length=64), nullable=True))
    op.add_column("generation_jobs", sa.Column("korean_phase31_validation_receipt_sha256", sa.String(length=64), nullable=True))
    op.add_column("generation_jobs", sa.Column("korean_phase31_snapshot_manifest_sha256", sa.String(length=64), nullable=True))
    op.add_column("generation_jobs", sa.Column("korean_phase31_snapshot_root_sha256", sa.String(length=64), nullable=True))
    op.add_column("generation_jobs", sa.Column("korean_frequency_bundle_locator_sha256", sa.String(length=64), nullable=True))
    op.add_column("generation_jobs", sa.Column("korean_frequency_bundle_content_sha256", sa.String(length=64), nullable=True))
    op.add_column("generation_jobs", sa.Column("korean_frequency_authority", sa.JSON(), nullable=True))
    op.add_column("generation_jobs", sa.Column("korean_provider_policy_sha256", sa.String(length=64), nullable=True))
    op.add_column("generation_jobs", sa.Column("korean_provider_policy", sa.JSON(), nullable=True))

    op.add_column("generation_items", sa.Column("stage_authority_sha256", sa.String(length=64), nullable=True))
    op.add_column("generation_items", sa.Column("stage_input_sha256", sa.String(length=64), nullable=True))
    op.add_column("generation_items", sa.Column("stage_output_sha256", sa.String(length=64), nullable=True))
    op.add_column("generation_items", sa.Column("stage_evidence", sa.JSON(), nullable=True))

    op.add_column("lexical_candidates", sa.Column("frequency_bundle_sha256", sa.String(length=64), nullable=True))
    op.add_column("lexical_candidates", sa.Column("frequency_source_sha256", sa.String(length=64), nullable=True))
    op.add_column("lexical_candidates", sa.Column("source_review_receipt_sha256", sa.String(length=64), nullable=True))
    op.add_column("lexical_candidates", sa.Column("source_review_aggregate_sha256", sa.String(length=64), nullable=True))
    op.add_column("lexical_candidates", sa.Column("lexical_evidence", sa.JSON(), nullable=True))

    op.add_column("text_quality_records", sa.Column("candidate_selection_evidence", sa.JSON(), nullable=True))
    op.add_column("text_quality_records", sa.Column("adaptive_i_plus_one_evidence", sa.JSON(), nullable=True))
    op.add_column("text_quality_records", sa.Column("provider_review_evidence", sa.JSON(), nullable=True))
    op.add_column("text_quality_records", sa.Column("text_review_receipt_sha256", sa.String(length=64), nullable=True))

    op.add_column("audio_assets", sa.Column("provider_sdk_version", sa.String(length=64), nullable=True))
    op.add_column("audio_assets", sa.Column("voice_profile_sha256", sa.String(length=64), nullable=True))
    op.add_column("audio_assets", sa.Column("catalog_receipt_sha256", sa.String(length=64), nullable=True))
    op.add_column("audio_assets", sa.Column("synthesis_request_sha256", sa.String(length=64), nullable=True))
    op.add_column("audio_assets", sa.Column("artifact_sha256", sa.String(length=64), nullable=True))
    op.add_column("audio_assets", sa.Column("audio_review_status", sa.String(length=32), nullable=True))
    op.add_column("audio_assets", sa.Column("audio_review_receipt_sha256", sa.String(length=64), nullable=True))
    op.add_column("audio_assets", sa.Column("heard_review_receipt_sha256", sa.String(length=64), nullable=True))
    op.add_column("audio_assets", sa.Column("fallback_origin", sa.String(length=128), nullable=True))
    op.add_column("audio_assets", sa.Column("rejection_reason_code", sa.String(length=64), nullable=True))

    op.add_column("card_exports", sa.Column("frequency_level", sa.Integer(), nullable=True))
    op.add_column("card_exports", sa.Column("frequency_bundle_sha256", sa.String(length=64), nullable=True))
    op.add_column("card_exports", sa.Column("export_gate_receipt_sha256", sa.String(length=64), nullable=True))

    op.add_column("deck_exports", sa.Column("frequency_bundle_sha256", sa.String(length=64), nullable=True))
    op.add_column("deck_exports", sa.Column("export_manifest_sha256", sa.String(length=64), nullable=True))
    op.add_column("deck_exports", sa.Column("export_gate_receipt_sha256", sa.String(length=64), nullable=True))

    op.add_column("provider_call_logs", sa.Column("route_policy_sha256", sa.String(length=64), nullable=True))
    op.add_column("provider_call_logs", sa.Column("budget_snapshot_sha256", sa.String(length=64), nullable=True))
    op.add_column("provider_call_logs", sa.Column("cache_key_sha256", sa.String(length=64), nullable=True))
    op.add_column("provider_call_logs", sa.Column("response_schema_sha256", sa.String(length=64), nullable=True))


def downgrade() -> None:
    op.drop_column("provider_call_logs", "response_schema_sha256")
    op.drop_column("provider_call_logs", "cache_key_sha256")
    op.drop_column("provider_call_logs", "budget_snapshot_sha256")
    op.drop_column("provider_call_logs", "route_policy_sha256")

    op.drop_column("deck_exports", "export_gate_receipt_sha256")
    op.drop_column("deck_exports", "export_manifest_sha256")
    op.drop_column("deck_exports", "frequency_bundle_sha256")

    op.drop_column("card_exports", "export_gate_receipt_sha256")
    op.drop_column("card_exports", "frequency_bundle_sha256")
    op.drop_column("card_exports", "frequency_level")

    op.drop_column("audio_assets", "rejection_reason_code")
    op.drop_column("audio_assets", "fallback_origin")
    op.drop_column("audio_assets", "heard_review_receipt_sha256")
    op.drop_column("audio_assets", "audio_review_receipt_sha256")
    op.drop_column("audio_assets", "audio_review_status")
    op.drop_column("audio_assets", "artifact_sha256")
    op.drop_column("audio_assets", "synthesis_request_sha256")
    op.drop_column("audio_assets", "catalog_receipt_sha256")
    op.drop_column("audio_assets", "voice_profile_sha256")
    op.drop_column("audio_assets", "provider_sdk_version")

    op.drop_column("text_quality_records", "text_review_receipt_sha256")
    op.drop_column("text_quality_records", "provider_review_evidence")
    op.drop_column("text_quality_records", "adaptive_i_plus_one_evidence")
    op.drop_column("text_quality_records", "candidate_selection_evidence")

    op.drop_column("lexical_candidates", "lexical_evidence")
    op.drop_column("lexical_candidates", "source_review_aggregate_sha256")
    op.drop_column("lexical_candidates", "source_review_receipt_sha256")
    op.drop_column("lexical_candidates", "frequency_source_sha256")
    op.drop_column("lexical_candidates", "frequency_bundle_sha256")

    op.drop_column("generation_items", "stage_evidence")
    op.drop_column("generation_items", "stage_output_sha256")
    op.drop_column("generation_items", "stage_input_sha256")
    op.drop_column("generation_items", "stage_authority_sha256")

    op.drop_column("generation_jobs", "korean_provider_policy")
    op.drop_column("generation_jobs", "korean_provider_policy_sha256")
    op.drop_column("generation_jobs", "korean_frequency_authority")
    op.drop_column("generation_jobs", "korean_frequency_bundle_content_sha256")
    op.drop_column("generation_jobs", "korean_frequency_bundle_locator_sha256")
    op.drop_column("generation_jobs", "korean_phase31_snapshot_root_sha256")
    op.drop_column("generation_jobs", "korean_phase31_snapshot_manifest_sha256")
    op.drop_column("generation_jobs", "korean_phase31_validation_receipt_sha256")
    op.drop_column("generation_jobs", "korean_phase31_pointer_content_sha256")
    op.drop_column("generation_jobs", "korean_phase31_pointer_locator_sha256")
