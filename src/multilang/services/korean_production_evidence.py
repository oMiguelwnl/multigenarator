"""Read-only Korean production run and final evidence reconciliation."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
from typing import Mapping
import zipfile

from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import select
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session
from sqlalchemy import create_engine

from multilang.db.models import (
    AudioAssetModel,
    CardExportModel,
    DeckExportModel,
    GenerationJob,
    LexicalCandidate,
    ProviderCallLogModel,
    TextQualityRecordModel,
)
from multilang.domain.audio import AudioAssetKind, AudioReviewStatus, AudioSynthesisStatus
from multilang.domain.exporting import FREQUENCY_EXPORT_CARD_FIELD_NAMES, ExportCardIdentity, build_export_note_guid
from multilang.domain.korean import KOREAN_PROVIDER_LOCALE
from multilang.domain.jobs import SupportedLanguage
from multilang.domain.text_quality import ReviewStatus, ValidationStatus
from multilang.repositories.provider_call_log_repository import summarize_provider_call_records
from multilang.services.korean_foundation_snapshot import verify_active_korean_foundation_snapshot_provenance


_HEX = frozenset("0123456789abcdef")
_EXPECTED_LEVELS = (1, 2, 3)
_AUDIO_SYNTHESIS_OPERATIONS = frozenset({"audio_synthesis", "word_audio", "sentence_audio", "synthesize_audio"})
_KOREAN_FREQUENCY_MODEL_ID = 1_762_801_101
_KOREAN_FREQUENCY_PARENT_DECK_ID = 1_762_801_102
_KOREAN_FREQUENCY_LEVEL_DECK_IDS = {1: 1_762_801_103, 2: 1_762_801_104, 3: 1_762_801_105}


def _sha256_identifier(value: str, *, field_name: str) -> str:
    if len(value) != 64 or any(character not in _HEX for character in value):
        raise ValueError(f"{field_name} must be lowercase SHA-256")
    return value


def _canonical_sha256(payload: object) -> str:
    return sha256(
        json.dumps(
            payload,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class _FrozenModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)


class KoreanProductionEvidenceAuthority(_FrozenModel):
    job_id: str = Field(min_length=1, max_length=128)
    phase31_pointer_locator_sha256: str = Field(min_length=64, max_length=64)
    phase31_pointer_content_sha256: str = Field(min_length=64, max_length=64)
    phase31_validation_receipt_sha256: str = Field(min_length=64, max_length=64)
    phase31_snapshot_manifest_sha256: str = Field(min_length=64, max_length=64)
    phase31_snapshot_root_sha256: str = Field(min_length=64, max_length=64)
    frequency_bundle_locator_sha256: str = Field(min_length=64, max_length=64)
    frequency_bundle_content_sha256: str = Field(min_length=64, max_length=64)
    source_access_authority_sha256: str = Field(min_length=64, max_length=64)
    source_retrieval_sha256: str = Field(min_length=64, max_length=64)
    source_transformation_sha256: str = Field(min_length=64, max_length=64)
    source_build_result_sha256: str = Field(min_length=64, max_length=64)
    source_review_aggregate_sha256: str = Field(min_length=64, max_length=64)
    final_bundle_authority_sha256: str = Field(min_length=64, max_length=64)
    provider_policy_sha256: str = Field(min_length=64, max_length=64)
    provider_review_authority_sha256: str = Field(min_length=64, max_length=64)
    budget_authority_sha256: str = Field(min_length=64, max_length=64)
    retry_policy_sha256: str = Field(min_length=64, max_length=64)
    full_run_authority_sha256: str = Field(min_length=64, max_length=64)
    catalog_locator_sha256: str = Field(min_length=64, max_length=64)
    catalog_content_sha256: str = Field(min_length=64, max_length=64)
    profile_sample_authority_sha256: str = Field(min_length=64, max_length=64)
    heard_review_authority_sha256: str = Field(min_length=64, max_length=64)
    full_binding_receipt_sha256: str = Field(min_length=64, max_length=64)

    @field_validator(
        "phase31_pointer_locator_sha256",
        "phase31_pointer_content_sha256",
        "phase31_validation_receipt_sha256",
        "phase31_snapshot_manifest_sha256",
        "phase31_snapshot_root_sha256",
        "frequency_bundle_locator_sha256",
        "frequency_bundle_content_sha256",
        "source_access_authority_sha256",
        "source_retrieval_sha256",
        "source_transformation_sha256",
        "source_build_result_sha256",
        "source_review_aggregate_sha256",
        "final_bundle_authority_sha256",
        "provider_policy_sha256",
        "provider_review_authority_sha256",
        "budget_authority_sha256",
        "retry_policy_sha256",
        "full_run_authority_sha256",
        "catalog_locator_sha256",
        "catalog_content_sha256",
        "profile_sample_authority_sha256",
        "heard_review_authority_sha256",
        "full_binding_receipt_sha256",
    )
    @classmethod
    def hashes_must_be_sha256(cls, value: str, info: object) -> str:
        return _sha256_identifier(value, field_name=getattr(info, "field_name", "hash"))


class KoreanProductionEvidence(_FrozenModel):
    mode: str = Field(pattern="^(run_result|final_result)$")
    job_id: str = Field(min_length=1, max_length=128)
    evidence_sha256: str = Field(min_length=64, max_length=64)
    expected_item_count: int = Field(ge=0)
    lexical_candidate_count: int = Field(ge=0)
    level_counts: dict[int, int]
    text_record_count: int = Field(ge=0)
    text_review_required_count: int = Field(ge=0)
    text_accepted_count: int = Field(ge=0)
    text_histories_with_two_initial_candidates: int = Field(ge=0)
    text_histories_with_single_repair_or_less: int = Field(ge=0)
    hard_gate_passed_count: int = Field(ge=0)
    adaptive_evidence_count: int = Field(ge=0)
    word_pending_audio_review_count: int = Field(ge=0)
    sentence_pending_audio_review_count: int = Field(ge=0)
    word_reviewed_audio_count: int = Field(ge=0)
    sentence_reviewed_audio_count: int = Field(ge=0)
    audio_request_hash_count: int = Field(ge=0)
    audio_artifact_hash_count: int = Field(ge=0)
    provider_call_count: int = Field(ge=0)
    provider_attempt_count: int = Field(ge=0)
    retry_attempt_count: int = Field(ge=0)
    cache_hit_count: int = Field(ge=0)
    synthesis_attempt_count: int = Field(ge=0)
    fallback_attempt_count: int = Field(ge=0)
    missing_token_denominator_count: int = Field(ge=0)
    missing_cost_denominator_count: int = Field(ge=0)
    latency_ms_total: int = Field(ge=0)
    provider_summaries: tuple[dict[str, object], ...]
    authority: dict[str, str]
    card_export_count: int = Field(default=0, ge=0)
    deck_export_count: int = Field(default=0, ge=0)
    apkg_card_count: int = Field(default=0, ge=0)
    apkg_media_count: int = Field(default=0, ge=0)
    apkg_sha256: str | None = Field(default=None, min_length=64, max_length=64)
    generation_report_json_sha256: str | None = Field(default=None, min_length=64, max_length=64)
    generation_report_markdown_sha256: str | None = Field(default=None, min_length=64, max_length=64)
    content_promotion_authority_sha256: str | None = Field(default=None, min_length=64, max_length=64)
    text_review_aggregate_sha256: str | None = Field(default=None, min_length=64, max_length=64)
    text_review_application_sha256: str | None = Field(default=None, min_length=64, max_length=64)
    audio_review_aggregate_sha256: str | None = Field(default=None, min_length=64, max_length=64)
    audio_review_application_sha256: str | None = Field(default=None, min_length=64, max_length=64)
    grants_review_application_authority: bool = False
    grants_content_promotion_authority: bool = False
    grants_release_authority: bool = False


@dataclass(frozen=True, slots=True)
class KoreanProductionEvidenceRows:
    job: object
    lexical_candidates: tuple[object, ...]
    text_records: tuple[object, ...]
    audio_assets: tuple[object, ...]
    provider_call_records: tuple[object, ...]
    card_exports: tuple[object, ...] = ()
    deck_exports: tuple[object, ...] = ()


def load_korean_production_evidence_rows(*, database_url: str, job_id: str) -> KoreanProductionEvidenceRows:
    """Load only the rows required for production evidence validation."""

    url = make_url(database_url)
    if url.drivername.startswith("sqlite") and url.database not in {None, "", ":memory:"}:
        from pathlib import Path

        if not Path(str(url.database)).is_file():
            raise ValueError("Korean production evidence database is unavailable")
    engine = create_engine(database_url)
    session = Session(engine)
    try:
        job = session.scalar(select(GenerationJob).where(GenerationJob.id == job_id))
        if job is None:
            raise ValueError("Korean production evidence job is unavailable")
        lexical_candidates = tuple(
            session.scalars(
                select(LexicalCandidate)
                .where(LexicalCandidate.job_id == job_id)
                .order_by(LexicalCandidate.frequency_rank.asc(), LexicalCandidate.item_key.asc())
            )
        )
        text_records = tuple(
            session.scalars(
                select(TextQualityRecordModel)
                .where(TextQualityRecordModel.job_id == job_id)
                .order_by(TextQualityRecordModel.item_key.asc())
            )
        )
        audio_assets = tuple(
            session.scalars(
                select(AudioAssetModel)
                .where(AudioAssetModel.job_id == job_id)
                .order_by(AudioAssetModel.item_key.asc(), AudioAssetModel.asset_kind.asc())
            )
        )
        provider_call_records = tuple(
            session.scalars(
                select(ProviderCallLogModel)
                .where(ProviderCallLogModel.job_id == job_id)
                .order_by(ProviderCallLogModel.created_at.asc(), ProviderCallLogModel.operation.asc())
            )
        )
        card_exports = tuple(
            session.scalars(
                select(CardExportModel)
                .where(CardExportModel.job_id == job_id)
                .order_by(CardExportModel.sort_index.asc(), CardExportModel.item_key.asc())
            )
        )
        deck_exports = tuple(
            session.scalars(
                select(DeckExportModel)
                .where(DeckExportModel.job_id == job_id)
                .order_by(DeckExportModel.export_format.asc())
            )
        )
        return KoreanProductionEvidenceRows(
            job=job,
            lexical_candidates=lexical_candidates,
            text_records=text_records,
            audio_assets=audio_assets,
            provider_call_records=provider_call_records,
            card_exports=card_exports,
            deck_exports=deck_exports,
        )
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError("Korean production evidence row read failed") from exc
    finally:
        session.close()
        engine.dispose()


def validate_korean_production_run_result(
    *,
    authority: KoreanProductionEvidenceAuthority,
    rows: KoreanProductionEvidenceRows,
    expected_item_count: int,
    protected_hashes: Mapping[str, tuple[str, str]],
    phase31_verifier=verify_active_korean_foundation_snapshot_provenance,
) -> KoreanProductionEvidence:
    """Recompute pre-review production evidence without applying reviews or mutating rows."""

    if expected_item_count != 3000:
        raise ValueError("Korean production evidence expected item count drift")
    _validate_protected_hashes(protected_hashes)
    _verify_phase31(authority, phase31_verifier=phase31_verifier)
    _validate_job(rows.job, authority=authority, expected_item_count=expected_item_count)
    level_counts = _validate_lexical_candidates(
        rows.lexical_candidates,
        authority=authority,
        expected_item_count=expected_item_count,
    )
    text_counts = _validate_run_text_records(
        rows.text_records,
        lexical_candidates=rows.lexical_candidates,
        authority=authority,
        expected_item_count=expected_item_count,
    )
    audio_counts = _validate_run_audio_assets(
        rows.audio_assets,
        authority=authority,
        expected_item_count=expected_item_count,
    )
    provider_counts = _validate_provider_rows(tuple(rows.provider_call_records), authority=authority)
    payload = {
        "mode": "run_result",
        "job_id": authority.job_id,
        "expected_item_count": expected_item_count,
        "lexical_candidate_count": len(rows.lexical_candidates),
        "level_counts": level_counts,
        **text_counts,
        **audio_counts,
        **provider_counts,
        "authority": _authority_hash_payload(authority),
    }
    return KoreanProductionEvidence(
        **payload,
        evidence_sha256=_canonical_sha256(payload),
        grants_review_application_authority=False,
        grants_content_promotion_authority=False,
        grants_release_authority=False,
    )


def validate_korean_production_final_evidence(
    *,
    authority: KoreanProductionEvidenceAuthority,
    rows: KoreanProductionEvidenceRows,
    expected_item_count: int,
    expected_word_assets: int,
    expected_sentence_assets: int,
    cards_per_level: int,
    content_promotion_authority_sha256: str,
    text_review_aggregate_sha256: str,
    text_review_application_sha256: str,
    audio_review_aggregate_sha256: str,
    audio_review_application_sha256: str,
    apkg_file: Path,
    generation_report_json: Path,
    generation_report_markdown: Path,
    protected_hashes: Mapping[str, tuple[str, str]],
    phase31_verifier=verify_active_korean_foundation_snapshot_provenance,
) -> KoreanProductionEvidence:
    """Recompute final production evidence from persisted rows and exact files."""

    if expected_item_count != 3000 or expected_word_assets != 3000 or expected_sentence_assets != 3000 or cards_per_level != 1000:
        raise ValueError("Korean production final evidence expected count drift")
    for field_name, value in {
        "content_promotion_authority_sha256": content_promotion_authority_sha256,
        "text_review_aggregate_sha256": text_review_aggregate_sha256,
        "text_review_application_sha256": text_review_application_sha256,
        "audio_review_aggregate_sha256": audio_review_aggregate_sha256,
        "audio_review_application_sha256": audio_review_application_sha256,
    }.items():
        _sha256_identifier(value, field_name=field_name)
    _validate_distinct_authority_hashes(
        authority,
        content_promotion_authority_sha256=content_promotion_authority_sha256,
        text_review_aggregate_sha256=text_review_aggregate_sha256,
        text_review_application_sha256=text_review_application_sha256,
        audio_review_aggregate_sha256=audio_review_aggregate_sha256,
        audio_review_application_sha256=audio_review_application_sha256,
    )
    _validate_protected_hashes(protected_hashes)
    _verify_phase31(authority, phase31_verifier=phase31_verifier)
    _validate_job(rows.job, authority=authority, expected_item_count=expected_item_count)
    level_counts = _validate_lexical_candidates(
        rows.lexical_candidates,
        authority=authority,
        expected_item_count=expected_item_count,
    )
    text_counts = _validate_final_text_records(
        rows.text_records,
        lexical_candidates=rows.lexical_candidates,
        authority=authority,
        expected_item_count=expected_item_count,
        text_review_application_sha256=text_review_application_sha256,
    )
    audio_counts = _validate_audio_assets(
        rows.audio_assets,
        authority=authority,
        expected_item_count=expected_item_count,
        expected_review_status=AudioReviewStatus.APPROVED.value,
        require_review_receipts=True,
        audio_review_application_sha256=audio_review_application_sha256,
        heard_review_receipt_sha256=authority.heard_review_authority_sha256,
    )
    provider_counts = _validate_provider_rows(tuple(rows.provider_call_records), authority=authority)
    export_counts = _validate_final_export_rows(
        rows.card_exports,
        rows.deck_exports,
        authority=authority,
        expected_item_count=expected_item_count,
        content_promotion_authority_sha256=content_promotion_authority_sha256,
    )
    apkg_counts = _inspect_final_apkg(
        apkg_file,
        card_exports=rows.card_exports,
        expected_item_count=expected_item_count,
        cards_per_level=cards_per_level,
    )
    report_counts = _validate_generation_reports(
        generation_report_json,
        generation_report_markdown,
        authority=authority,
        apkg_sha256=str(apkg_counts["apkg_sha256"]),
        expected_item_count=expected_item_count,
        expected_word_assets=expected_word_assets,
        expected_sentence_assets=expected_sentence_assets,
        cards_per_level=cards_per_level,
    )
    payload = {
        "mode": "final_result",
        "job_id": authority.job_id,
        "expected_item_count": expected_item_count,
        "lexical_candidate_count": len(rows.lexical_candidates),
        "level_counts": level_counts,
        **text_counts,
        **audio_counts,
        **provider_counts,
        **export_counts,
        **apkg_counts,
        **report_counts,
        "content_promotion_authority_sha256": content_promotion_authority_sha256,
        "text_review_aggregate_sha256": text_review_aggregate_sha256,
        "text_review_application_sha256": text_review_application_sha256,
        "audio_review_aggregate_sha256": audio_review_aggregate_sha256,
        "audio_review_application_sha256": audio_review_application_sha256,
        "authority": _authority_hash_payload(authority),
    }
    return KoreanProductionEvidence(
        **payload,
        evidence_sha256=_canonical_sha256(payload),
        grants_review_application_authority=False,
        grants_content_promotion_authority=False,
        grants_release_authority=False,
    )


def build_korean_production_audit_payload(evidence: KoreanProductionEvidence) -> dict[str, object]:
    return {
        "mode": evidence.mode,
        "job_id": evidence.job_id,
        "evidence_sha256": evidence.evidence_sha256,
        "counts": {
            "expected_item_count": evidence.expected_item_count,
            "lexical_candidate_count": evidence.lexical_candidate_count,
            "level_counts": evidence.level_counts,
            "text_record_count": evidence.text_record_count,
            "text_accepted_count": evidence.text_accepted_count,
            "text_review_required_count": evidence.text_review_required_count,
            "word_reviewed_audio_count": evidence.word_reviewed_audio_count,
            "sentence_reviewed_audio_count": evidence.sentence_reviewed_audio_count,
            "provider_call_count": evidence.provider_call_count,
            "fallback_attempt_count": evidence.fallback_attempt_count,
        },
        "final": {
            "card_export_count": evidence.card_export_count,
            "deck_export_count": evidence.deck_export_count,
            "apkg_card_count": evidence.apkg_card_count,
            "apkg_media_count": evidence.apkg_media_count,
            "apkg_sha256": evidence.apkg_sha256,
            "generation_report_json_sha256": evidence.generation_report_json_sha256,
            "generation_report_markdown_sha256": evidence.generation_report_markdown_sha256,
        },
        "authority": evidence.authority,
        "authority_limits": {
            "grants_review_application_authority": evidence.grants_review_application_authority,
            "grants_content_promotion_authority": evidence.grants_content_promotion_authority,
            "grants_release_authority": evidence.grants_release_authority,
        },
        "privacy": {
            "excluded": ["learner_text", "korean_text", "prompts", "provider_payloads", "credentials", "file_paths"],
        },
    }


def render_korean_production_audit_markdown(payload: Mapping[str, object]) -> str:
    final = _mapping(payload.get("final"))
    return (
        "# Korean Production Evidence Audit\n\n"
        f"mode={payload.get('mode')}\n"
        f"job_id={payload.get('job_id')}\n"
        f"evidence_sha256={payload.get('evidence_sha256')}\n"
        f"apkg_sha256={final.get('apkg_sha256')}\n"
        f"apkg_card_count={final.get('apkg_card_count')}\n"
        f"apkg_media_count={final.get('apkg_media_count')}\n"
    )


def _validate_protected_hashes(protected_hashes: Mapping[str, tuple[str, str]]) -> None:
    for label, pair in protected_hashes.items():
        before, after = pair
        _sha256_identifier(before, field_name=f"{label}_pre_sha256")
        _sha256_identifier(after, field_name=f"{label}_post_sha256")
        if before != after:
            raise ValueError("Korean production evidence protected input drift")


def _validate_distinct_authority_hashes(
    authority: KoreanProductionEvidenceAuthority,
    **extra_authorities: str,
) -> None:
    values = {
        **_authority_hash_payload(authority),
        **extra_authorities,
    }
    if len(set(values.values())) != len(values):
        raise ValueError("Korean production evidence authority hashes must be distinct")


def _verify_phase31(authority: KoreanProductionEvidenceAuthority, *, phase31_verifier: object) -> None:
    report = phase31_verifier(expected_receipt_sha256=authority.phase31_validation_receipt_sha256)
    expected = {
        "receipt_sha256": authority.phase31_validation_receipt_sha256,
        "snapshot_manifest_sha256": authority.phase31_snapshot_manifest_sha256,
        "snapshot_root_sha256": authority.phase31_snapshot_root_sha256,
    }
    for field, value in expected.items():
        if getattr(report, field, None) != value:
            raise ValueError("Phase 31 active authority drift")


def _validate_job(job: object, *, authority: KoreanProductionEvidenceAuthority, expected_item_count: int) -> None:
    expected_columns = {
        "id": authority.job_id,
        "language": SupportedLanguage.KO.value,
        "source_type": "frequency",
        "total_items": expected_item_count,
        "korean_phase31_pointer_locator_sha256": authority.phase31_pointer_locator_sha256,
        "korean_phase31_pointer_content_sha256": authority.phase31_pointer_content_sha256,
        "korean_phase31_validation_receipt_sha256": authority.phase31_validation_receipt_sha256,
        "korean_phase31_snapshot_manifest_sha256": authority.phase31_snapshot_manifest_sha256,
        "korean_phase31_snapshot_root_sha256": authority.phase31_snapshot_root_sha256,
        "korean_frequency_bundle_locator_sha256": authority.frequency_bundle_locator_sha256,
        "korean_frequency_bundle_content_sha256": authority.frequency_bundle_content_sha256,
        "korean_provider_policy_sha256": authority.provider_policy_sha256,
    }
    for field, value in expected_columns.items():
        if getattr(job, field, None) != value:
            raise ValueError("Korean production evidence job authority drift")
    stored_authority = getattr(job, "korean_frequency_authority", None)
    if not isinstance(stored_authority, Mapping):
        raise ValueError("Korean production evidence job authority drift")
    for field, value in authority.model_dump(mode="json").items():
        if stored_authority.get(field) != value:
            raise ValueError("Korean production evidence job authority drift")


def _validate_lexical_candidates(
    candidates: tuple[object, ...],
    *,
    authority: KoreanProductionEvidenceAuthority,
    expected_item_count: int,
) -> dict[int, int]:
    if len(candidates) != expected_item_count:
        raise ValueError("Korean production evidence lexical denominator drift")
    expected_ranks = list(range(1, expected_item_count + 1))
    ranks = [int(getattr(candidate, "frequency_rank", 0) or 0) for candidate in candidates]
    if sorted(ranks) != expected_ranks:
        raise ValueError("Korean production evidence rank sequence drift")
    item_keys = [str(getattr(candidate, "item_key", "")) for candidate in candidates]
    lemma_keys = [str(getattr(candidate, "lemma_key", "")) for candidate in candidates]
    if len(set(item_keys)) != expected_item_count or len(set(lemma_keys)) != expected_item_count:
        raise ValueError("Korean production evidence lexical identity drift")
    level_counts = Counter(int(getattr(candidate, "frequency_level", 0) or 0) for candidate in candidates)
    expected_level_count = expected_item_count // len(_EXPECTED_LEVELS)
    if dict(level_counts) != {level: expected_level_count for level in _EXPECTED_LEVELS}:
        raise ValueError("Korean production evidence requires 1000/1000/1000 levels")
    for candidate in candidates:
        evidence = _mapping(getattr(candidate, "lexical_evidence", None))
        expected = {
            "job_id": authority.job_id,
            "source_type": "frequency",
            "grounding_status": "grounded",
            "frequency_bundle_sha256": authority.frequency_bundle_content_sha256,
            "frequency_source_sha256": authority.source_retrieval_sha256,
            "source_review_aggregate_sha256": authority.source_review_aggregate_sha256,
        }
        for field, value in expected.items():
            if getattr(candidate, field, None) != value:
                raise ValueError("Korean production evidence lexical authority drift")
        for field, value in {
            "source_access_authority_sha256": authority.source_access_authority_sha256,
            "source_transformation_sha256": authority.source_transformation_sha256,
            "source_build_result_sha256": authority.source_build_result_sha256,
            "final_bundle_authority_sha256": authority.final_bundle_authority_sha256,
        }.items():
            if evidence.get(field) != value:
                raise ValueError("Korean production evidence lexical authority drift")
    return {level: int(level_counts[level]) for level in _EXPECTED_LEVELS}


def _validate_run_text_records(
    text_records: tuple[object, ...],
    *,
    lexical_candidates: tuple[object, ...],
    authority: KoreanProductionEvidenceAuthority,
    expected_item_count: int,
) -> dict[str, int]:
    if len(text_records) != expected_item_count:
        raise ValueError("Korean production evidence text denominator drift")
    candidate_item_keys = {str(getattr(candidate, "item_key", "")) for candidate in lexical_candidates}
    text_item_keys = {str(getattr(record, "item_key", "")) for record in text_records}
    if text_item_keys != candidate_item_keys:
        raise ValueError("Korean production evidence text identity drift")
    two_initial = 0
    single_repair_or_less = 0
    hard_gate_passed = 0
    adaptive_count = 0
    review_required = 0
    accepted = 0
    for record in text_records:
        if getattr(record, "job_id", None) != authority.job_id:
            raise ValueError("Korean production evidence text job drift")
        if getattr(record, "validation_status", None) != ValidationStatus.PASSED.value:
            raise ValueError("Korean production evidence text validation drift")
        review_status = str(getattr(record, "review_status", ""))
        if review_status == ReviewStatus.REVIEW_REQUIRED.value:
            review_required += 1
        elif review_status == ReviewStatus.ACCEPTED.value:
            accepted += 1
        else:
            raise ValueError("Korean production evidence text review-state drift")
        selection = _mapping(getattr(record, "candidate_selection_evidence", None))
        if selection.get("initial_candidate_count") == 2:
            two_initial += 1
        repair_attempt_count = int(selection.get("repair_attempt_count", -1))
        if repair_attempt_count <= 1 and int(getattr(record, "repair_attempt_count", -1)) <= 1:
            single_repair_or_less += 1
        if selection.get("hard_gate_status") == "passed":
            hard_gate_passed += 1
        adaptive = _mapping(getattr(record, "adaptive_i_plus_one_evidence", None))
        if adaptive:
            adaptive_count += 1
            for field, value in {
                "phase31_pointer_locator_sha256": authority.phase31_pointer_locator_sha256,
                "phase31_pointer_content_sha256": authority.phase31_pointer_content_sha256,
                "phase31_validation_receipt_sha256": authority.phase31_validation_receipt_sha256,
                "phase31_snapshot_manifest_sha256": authority.phase31_snapshot_manifest_sha256,
                "phase31_snapshot_root_sha256": authority.phase31_snapshot_root_sha256,
                "frequency_bundle_locator_sha256": authority.frequency_bundle_locator_sha256,
                "frequency_bundle_content_sha256": authority.frequency_bundle_content_sha256,
            }.items():
                if adaptive.get(field) != value:
                    raise ValueError("Korean production evidence adaptive prefix drift")
    if review_required != expected_item_count:
        raise ValueError("Korean production evidence text must be pending review")
    if two_initial != expected_item_count or single_repair_or_less != expected_item_count:
        raise ValueError("Korean production evidence text history drift")
    if hard_gate_passed != expected_item_count or adaptive_count != expected_item_count:
        raise ValueError("Korean production evidence text hard-gate/adaptive drift")
    return {
        "text_record_count": len(text_records),
        "text_review_required_count": review_required,
        "text_accepted_count": accepted,
        "text_histories_with_two_initial_candidates": two_initial,
        "text_histories_with_single_repair_or_less": single_repair_or_less,
        "hard_gate_passed_count": hard_gate_passed,
        "adaptive_evidence_count": adaptive_count,
    }


def _validate_final_text_records(
    text_records: tuple[object, ...],
    *,
    lexical_candidates: tuple[object, ...],
    authority: KoreanProductionEvidenceAuthority,
    expected_item_count: int,
    text_review_application_sha256: str,
) -> dict[str, int]:
    if len(text_records) != expected_item_count:
        raise ValueError("Korean production evidence reviewed text denominator drift")
    candidate_item_keys = {str(getattr(candidate, "item_key", "")) for candidate in lexical_candidates}
    text_item_keys = {str(getattr(record, "item_key", "")) for record in text_records}
    if text_item_keys != candidate_item_keys:
        raise ValueError("Korean production evidence reviewed text identity drift")
    two_initial = 0
    single_repair_or_less = 0
    hard_gate_passed = 0
    adaptive_count = 0
    for record in text_records:
        if getattr(record, "job_id", None) != authority.job_id:
            raise ValueError("Korean production evidence reviewed text job drift")
        if getattr(record, "validation_status", None) != ValidationStatus.PASSED.value:
            raise ValueError("Korean production evidence reviewed text validation drift")
        if getattr(record, "review_status", None) != ReviewStatus.ACCEPTED.value:
            raise ValueError("Korean production evidence reviewed text state drift")
        if getattr(record, "text_review_receipt_sha256", None) != text_review_application_sha256:
            raise ValueError("Korean production evidence reviewed text receipt drift")
        provider_review = _mapping(getattr(record, "provider_review_evidence", None))
        if (
            provider_review.get("review_receipt_sha256") != authority.provider_review_authority_sha256
            or provider_review.get("decision") != "accepted"
        ):
            raise ValueError("Korean production evidence reviewed text provider-review drift")
        selection = _mapping(getattr(record, "candidate_selection_evidence", None))
        if selection.get("initial_candidate_count") == 2:
            two_initial += 1
        repair_attempt_count = int(selection.get("repair_attempt_count", -1))
        if repair_attempt_count <= 1 and int(getattr(record, "repair_attempt_count", -1)) <= 1:
            single_repair_or_less += 1
        if selection.get("hard_gate_status") == "passed":
            hard_gate_passed += 1
        adaptive = _mapping(getattr(record, "adaptive_i_plus_one_evidence", None))
        if adaptive:
            adaptive_count += 1
            for field, value in {
                "phase31_pointer_locator_sha256": authority.phase31_pointer_locator_sha256,
                "phase31_pointer_content_sha256": authority.phase31_pointer_content_sha256,
                "phase31_validation_receipt_sha256": authority.phase31_validation_receipt_sha256,
                "phase31_snapshot_manifest_sha256": authority.phase31_snapshot_manifest_sha256,
                "phase31_snapshot_root_sha256": authority.phase31_snapshot_root_sha256,
                "frequency_bundle_locator_sha256": authority.frequency_bundle_locator_sha256,
                "frequency_bundle_content_sha256": authority.frequency_bundle_content_sha256,
            }.items():
                if adaptive.get(field) != value:
                    raise ValueError("Korean production evidence reviewed text adaptive prefix drift")
    if two_initial != expected_item_count or single_repair_or_less != expected_item_count:
        raise ValueError("Korean production evidence reviewed text history drift")
    if hard_gate_passed != expected_item_count or adaptive_count != expected_item_count:
        raise ValueError("Korean production evidence reviewed text hard-gate/adaptive drift")
    return {
        "text_record_count": len(text_records),
        "text_review_required_count": 0,
        "text_accepted_count": expected_item_count,
        "text_histories_with_two_initial_candidates": two_initial,
        "text_histories_with_single_repair_or_less": single_repair_or_less,
        "hard_gate_passed_count": hard_gate_passed,
        "adaptive_evidence_count": adaptive_count,
    }


def _validate_run_audio_assets(
    assets: tuple[object, ...],
    *,
    authority: KoreanProductionEvidenceAuthority,
    expected_item_count: int,
) -> dict[str, int]:
    return _validate_audio_assets(
        assets,
        authority=authority,
        expected_item_count=expected_item_count,
        expected_review_status=AudioReviewStatus.SYNTHESIZED_PENDING.value,
        require_review_receipts=False,
    )


def _validate_audio_assets(
    assets: tuple[object, ...],
    *,
    authority: KoreanProductionEvidenceAuthority,
    expected_item_count: int,
    expected_review_status: str,
    require_review_receipts: bool,
    audio_review_application_sha256: str | None = None,
    heard_review_receipt_sha256: str | None = None,
) -> dict[str, int]:
    if len(assets) != expected_item_count * 2:
        raise ValueError("Korean production evidence audio denominator drift")
    kind_counts = Counter(str(getattr(asset, "asset_kind", "")) for asset in assets)
    if kind_counts.get(AudioAssetKind.WORD.value, 0) != expected_item_count or kind_counts.get(AudioAssetKind.SENTENCE.value, 0) != expected_item_count:
        raise ValueError("Korean production evidence audio kind denominator drift")
    request_hash_count = 0
    artifact_hash_count = 0
    pending_word = 0
    pending_sentence = 0
    reviewed_word = 0
    reviewed_sentence = 0
    for asset in assets:
        kind = str(getattr(asset, "asset_kind", ""))
        if getattr(asset, "job_id", None) != authority.job_id:
            raise ValueError("Korean production evidence audio job drift")
        if getattr(asset, "status", None) != AudioSynthesisStatus.SYNTHESIZED.value:
            raise ValueError("Korean production evidence synthesized audio drift")
        if bool(getattr(asset, "fallback_used", False)):
            raise ValueError("Korean production evidence audio fallback drift")
        if getattr(asset, "locale", None) != KOREAN_PROVIDER_LOCALE or getattr(asset, "provider", None) != "azure":
            raise ValueError("Korean production evidence audio provider drift")
        if getattr(asset, "voice_profile_sha256", None) != authority.profile_sample_authority_sha256:
            raise ValueError("Korean production evidence audio profile drift")
        if getattr(asset, "catalog_receipt_sha256", None) != authority.catalog_content_sha256:
            raise ValueError("Korean production evidence audio catalog drift")
        if getattr(asset, "audio_review_status", None) != expected_review_status:
            if require_review_receipts:
                raise ValueError("Korean production evidence reviewed audio drift")
            raise ValueError("Korean production evidence pending-review audio drift")
        _sha256_identifier(str(getattr(asset, "text_hash", "")), field_name="audio_text_hash")
        _sha256_identifier(str(getattr(asset, "ssml_hash", "")), field_name="audio_ssml_hash")
        _sha256_identifier(str(getattr(asset, "synthesis_request_sha256", "")), field_name="synthesis_request_sha256")
        _sha256_identifier(str(getattr(asset, "artifact_sha256", "")), field_name="artifact_sha256")
        request_hash_count += 1
        artifact_hash_count += 1
        if int(getattr(asset, "byte_size", 0) or 0) <= 0:
            raise ValueError("Korean production evidence audio byte drift")
        if require_review_receipts:
            audio_review_receipt = str(getattr(asset, "audio_review_receipt_sha256", ""))
            heard_review_receipt = str(getattr(asset, "heard_review_receipt_sha256", ""))
            _sha256_identifier(audio_review_receipt, field_name="audio_review_receipt_sha256")
            _sha256_identifier(heard_review_receipt, field_name="heard_review_receipt_sha256")
            if audio_review_application_sha256 is not None and audio_review_receipt != audio_review_application_sha256:
                raise ValueError("Korean production evidence reviewed audio receipt drift")
            if heard_review_receipt_sha256 is not None and heard_review_receipt != heard_review_receipt_sha256:
                raise ValueError("Korean production evidence heard audio review drift")
            if kind == AudioAssetKind.WORD.value:
                reviewed_word += 1
            elif kind == AudioAssetKind.SENTENCE.value:
                reviewed_sentence += 1
        elif kind == AudioAssetKind.WORD.value:
            pending_word += 1
        elif kind == AudioAssetKind.SENTENCE.value:
            pending_sentence += 1
    return {
        "word_pending_audio_review_count": pending_word,
        "sentence_pending_audio_review_count": pending_sentence,
        "word_reviewed_audio_count": reviewed_word,
        "sentence_reviewed_audio_count": reviewed_sentence,
        "audio_request_hash_count": request_hash_count,
        "audio_artifact_hash_count": artifact_hash_count,
    }


def _validate_provider_rows(
    records: tuple[object, ...],
    *,
    authority: KoreanProductionEvidenceAuthority,
) -> dict[str, object]:
    if not records:
        raise ValueError("Korean production evidence requires provider call rows")
    provider_attempt_count = 0
    retry_attempt_count = 0
    cache_hit_count = 0
    synthesis_attempt_count = 0
    fallback_attempt_count = 0
    missing_token_denominator_count = 0
    missing_cost_denominator_count = 0
    latency_ms_total = 0
    for record in records:
        if getattr(record, "job_id", None) != authority.job_id:
            raise ValueError("Korean production evidence provider job drift")
        provider = str(getattr(record, "provider", ""))
        operation = str(getattr(record, "operation", ""))
        if provider.casefold() == "fallback" or getattr(record, "fallback_from", None):
            fallback_attempt_count += 1
        if operation in _AUDIO_SYNTHESIS_OPERATIONS:
            synthesis_attempt_count += 1
        for field, expected in {
            "route_policy_sha256": authority.provider_policy_sha256,
            "budget_snapshot_sha256": authority.budget_authority_sha256,
        }.items():
            value = getattr(record, field, None)
            if value != expected:
                raise ValueError("Korean production evidence provider authority drift")
        for field in ("prompt_hash", "response_hash", "cache_key_sha256", "response_schema_sha256"):
            _sha256_identifier(str(getattr(record, field, "")), field_name=field)
        status = str(getattr(record, "status", ""))
        attempt = int(getattr(record, "attempt", 0) or 0)
        if status == "cache_hit":
            cache_hit_count += 1
        elif attempt > 0:
            provider_attempt_count += 1
        retry_attempt_count += max(0, attempt - 1)
        latency_ms_total += int(getattr(record, "latency_ms", 0) or 0)
        if not any(getattr(record, field, None) is not None for field in ("input_tokens", "output_tokens", "total_tokens")):
            missing_token_denominator_count += 1
        if getattr(record, "estimated_cost", None) is None:
            missing_cost_denominator_count += 1
    if fallback_attempt_count:
        raise ValueError("Korean production evidence provider fallback drift")
    if missing_token_denominator_count or missing_cost_denominator_count:
        raise ValueError("Korean production evidence provider denominator drift")
    return {
        "provider_call_count": len(records),
        "provider_attempt_count": provider_attempt_count,
        "retry_attempt_count": retry_attempt_count,
        "cache_hit_count": cache_hit_count,
        "synthesis_attempt_count": synthesis_attempt_count,
        "fallback_attempt_count": fallback_attempt_count,
        "missing_token_denominator_count": missing_token_denominator_count,
        "missing_cost_denominator_count": missing_cost_denominator_count,
        "latency_ms_total": latency_ms_total,
        "provider_summaries": tuple(summarize_provider_call_records(list(records))),
    }


def _validate_final_export_rows(
    card_exports: tuple[object, ...],
    deck_exports: tuple[object, ...],
    *,
    authority: KoreanProductionEvidenceAuthority,
    expected_item_count: int,
    content_promotion_authority_sha256: str,
) -> dict[str, int]:
    if len(card_exports) != expected_item_count:
        raise ValueError("Korean production evidence export row denominator drift")
    ranks = [int(getattr(row, "sort_index", 0) or 0) for row in card_exports]
    if sorted(ranks) != list(range(1, expected_item_count + 1)):
        raise ValueError("Korean production evidence export rank drift")
    level_counts = Counter(int(getattr(row, "frequency_level", 0) or 0) for row in card_exports)
    if dict(level_counts) != {1: 1000, 2: 1000, 3: 1000}:
        raise ValueError("Korean production evidence export level drift")
    for row in card_exports:
        rank = int(getattr(row, "sort_index", 0) or 0)
        identity = ExportCardIdentity(
            language=SupportedLanguage.KO,
            source_type="frequency",
            job_id=authority.job_id,
            item_key=str(getattr(row, "item_key", "")),
            lemma_key=str(getattr(row, "lemma_key", "")),
            sort_index=rank,
        )
        expected = {
            "job_id": authority.job_id,
            "frequency_bundle_sha256": authority.frequency_bundle_content_sha256,
            "export_gate_receipt_sha256": content_promotion_authority_sha256,
            "note_guid": build_export_note_guid(identity),
        }
        for field, value in expected.items():
            if getattr(row, field, None) != value:
                raise ValueError("Korean production evidence export row authority drift")
        if getattr(row, "image", None) not in {"", None}:
            raise ValueError("Korean production evidence export image drift")
        for field in ("word_audio", "sentence_audio"):
            value = str(getattr(row, field, ""))
            if not value.startswith("[sound:") or not value.endswith("]"):
                raise ValueError("Korean production evidence export media reference drift")
    if len(deck_exports) != 1:
        raise ValueError("Korean production evidence deck export denominator drift")
    deck_export = deck_exports[0]
    expected_deck = {
        "job_id": authority.job_id,
        "export_format": "apkg",
        "card_count": expected_item_count,
        "status": "completed",
        "frequency_bundle_sha256": authority.frequency_bundle_content_sha256,
        "export_manifest_sha256": authority.frequency_bundle_locator_sha256,
        "export_gate_receipt_sha256": content_promotion_authority_sha256,
    }
    for field, value in expected_deck.items():
        if getattr(deck_export, field, None) != value:
            raise ValueError("Korean production evidence deck export authority drift")
    return {"card_export_count": len(card_exports), "deck_export_count": len(deck_exports)}


def _inspect_final_apkg(
    apkg_file: Path,
    *,
    card_exports: tuple[object, ...],
    expected_item_count: int,
    cards_per_level: int,
) -> dict[str, object]:
    if not apkg_file.is_file():
        raise ValueError("Korean production APKG file missing")
    apkg_sha256 = _sha256_file(apkg_file)
    try:
        with zipfile.ZipFile(apkg_file) as archive:
            media_manifest = json.loads(archive.read("media").decode("utf-8"))
            if not isinstance(media_manifest, dict):
                raise ValueError("Korean production APKG media manifest drift")
            names = set(archive.namelist())
            if any(str(key) not in names for key in media_manifest):
                raise ValueError("Korean production APKG media payload drift")
            collection_bytes = archive.read("collection.anki2")
    except (OSError, KeyError, zipfile.BadZipFile, json.JSONDecodeError) as exc:
        raise ValueError("Korean production APKG inspection failed") from exc
    expected_media_names = {
        f"{getattr(row, 'item_key')}-{kind}.mp3"
        for row in card_exports
        for kind in ("word", "sentence")
    }
    if len(media_manifest) != expected_item_count * 2 or set(media_manifest.values()) != expected_media_names:
        raise ValueError("Korean production APKG media count drift")

    with TemporaryDirectory() as directory:
        collection_path = Path(directory) / "collection.anki2"
        collection_path.write_bytes(collection_bytes)
        with sqlite3.connect(collection_path) as connection:
            row = connection.execute("select models, decks from col").fetchone()
            if row is None:
                raise ValueError("Korean production APKG metadata drift")
            models = json.loads(row[0])
            decks = json.loads(row[1])
            note_count = int(connection.execute("select count(*) from notes").fetchone()[0])
            card_count = int(connection.execute("select count(*) from cards").fetchone()[0])
            deck_counts = dict(connection.execute("select did, count(*) from cards group by did").fetchall())
            guids = {value[0] for value in connection.execute("select guid from notes").fetchall()}
            field_counts = {len(value[0].split("\x1f")) for value in connection.execute("select flds from notes limit 25").fetchall()}
    model = models.get(str(_KOREAN_FREQUENCY_MODEL_ID))
    if model is None or model.get("name") != "Multilang::Card":
        raise ValueError("Korean production APKG model identity drift")
    if tuple(field["name"] for field in model.get("flds", [])) != FREQUENCY_EXPORT_CARD_FIELD_NAMES:
        raise ValueError("Korean production APKG model field drift")
    if str(_KOREAN_FREQUENCY_PARENT_DECK_ID) not in decks:
        raise ValueError("Korean production APKG parent deck drift")
    level_deck_ids = _KOREAN_FREQUENCY_LEVEL_DECK_IDS
    if any(str(deck_id) not in decks for deck_id in level_deck_ids.values()):
        raise ValueError("Korean production APKG child deck drift")
    expected_deck_counts = {deck_id: cards_per_level for deck_id in level_deck_ids.values()}
    if note_count != expected_item_count or card_count != expected_item_count or deck_counts != expected_deck_counts:
        raise ValueError("Korean production APKG card routing/count drift")
    if guids != {str(getattr(row, "note_guid", "")) for row in card_exports}:
        raise ValueError("Korean production APKG GUID drift")
    if field_counts != {len(FREQUENCY_EXPORT_CARD_FIELD_NAMES)}:
        raise ValueError("Korean production APKG field count drift")
    return {"apkg_card_count": card_count, "apkg_media_count": len(media_manifest), "apkg_sha256": apkg_sha256}


def _validate_generation_reports(
    generation_report_json: Path,
    generation_report_markdown: Path,
    *,
    authority: KoreanProductionEvidenceAuthority,
    apkg_sha256: str,
    expected_item_count: int,
    expected_word_assets: int,
    expected_sentence_assets: int,
    cards_per_level: int,
) -> dict[str, str]:
    try:
        payload = json.loads(generation_report_json.read_text(encoding="utf-8"))
        markdown = generation_report_markdown.read_text(encoding="utf-8")
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("Korean production report inspection failed") from exc
    if not isinstance(payload, Mapping):
        raise ValueError("Korean production report structure drift")
    export = _mapping(payload.get("export"))
    job = _mapping(payload.get("job"))
    bundle = _mapping(payload.get("frequency_bundle"))
    text = _mapping(payload.get("text"))
    audio = _mapping(payload.get("audio"))
    word_audio = _mapping(audio.get("word"))
    sentence_audio = _mapping(audio.get("sentence"))
    if (
        job.get("id") != authority.job_id
        or job.get("language") != SupportedLanguage.KO.value
        or job.get("source_type") != "frequency"
        or bundle.get("content_sha256") != authority.frequency_bundle_content_sha256
        or bundle.get("manifest_sha256") != authority.frequency_bundle_locator_sha256
        or bundle.get("binding_receipt_sha256") != authority.full_binding_receipt_sha256
    ):
        raise ValueError("Korean production report authority drift")
    if (
        export.get("apkg_sha256") != apkg_sha256
        or export.get("card_count") != expected_item_count
        or export.get("expected_items") != expected_item_count
        or export.get("cards_per_level") != cards_per_level
        or payload.get("level_counts") != {"1": cards_per_level, "2": cards_per_level, "3": cards_per_level}
    ):
        raise ValueError("Korean production report export count drift")
    if text.get("accepted") != expected_item_count or text.get("review_required") != 0:
        raise ValueError("Korean production report reviewed text drift")
    if (
        word_audio.get("approved") != expected_word_assets
        or sentence_audio.get("approved") != expected_sentence_assets
        or audio.get("fallback_count") != 0
        or audio.get("artifact_hash_count") != expected_word_assets + expected_sentence_assets
    ):
        raise ValueError("Korean production report reviewed audio drift")
    if f"exact_apkg_sha256={apkg_sha256}" not in markdown:
        raise ValueError("Korean production report markdown drift")
    return {
        "generation_report_json_sha256": _sha256_file(generation_report_json),
        "generation_report_markdown_sha256": _sha256_file(generation_report_markdown),
    }


def _mapping(value: object) -> Mapping[str, object]:
    if isinstance(value, Mapping):
        return value
    return {}


def _authority_hash_payload(authority: KoreanProductionEvidenceAuthority) -> dict[str, str]:
    fields = authority.model_dump(mode="json")
    return {field: value for field, value in sorted(fields.items()) if field != "job_id"}


__all__ = [
    "build_korean_production_audit_payload",
    "KoreanProductionEvidence",
    "KoreanProductionEvidenceAuthority",
    "KoreanProductionEvidenceRows",
    "load_korean_production_evidence_rows",
    "render_korean_production_audit_markdown",
    "validate_korean_production_final_evidence",
    "validate_korean_production_run_result",
]
