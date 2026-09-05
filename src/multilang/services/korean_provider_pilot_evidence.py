"""Read-only Korean provider/catalog pilot evidence reconciliation."""

from __future__ import annotations

from hashlib import sha256
import json
from typing import Mapping

from pydantic import BaseModel, ConfigDict, Field, field_validator

from multilang.domain.korean import KOREAN_PROVIDER_LOCALE
from multilang.repositories.provider_call_log_repository import summarize_provider_call_records
from multilang.services.korean_foundation_snapshot import verify_active_korean_foundation_snapshot_provenance


_HEX = frozenset("0123456789abcdef")
_SYNTHESIS_OPERATIONS = frozenset({"word_audio", "sentence_audio", "synthesize_audio", "audio_synthesis"})


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


class _FrozenModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)


class KoreanProviderCatalogPilotAuthority(_FrozenModel):
    job_id: str = Field(min_length=1, max_length=128)
    phase31_pointer_locator_sha256: str = Field(min_length=64, max_length=64)
    phase31_pointer_content_sha256: str = Field(min_length=64, max_length=64)
    phase31_validation_receipt_sha256: str = Field(min_length=64, max_length=64)
    phase31_snapshot_manifest_sha256: str = Field(min_length=64, max_length=64)
    phase31_snapshot_root_sha256: str = Field(min_length=64, max_length=64)
    frequency_bundle_locator_sha256: str = Field(min_length=64, max_length=64)
    frequency_bundle_content_sha256: str = Field(min_length=64, max_length=64)
    source_retrieval_sha256: str = Field(min_length=64, max_length=64)
    source_build_result_sha256: str = Field(min_length=64, max_length=64)
    source_review_aggregate_sha256: str = Field(min_length=64, max_length=64)
    provider_policy_sha256: str = Field(min_length=64, max_length=64)
    pilot_authority_sha256: str = Field(min_length=64, max_length=64)
    binding_receipt_sha256: str = Field(min_length=64, max_length=64)
    catalog_locator_sha256: str = Field(min_length=64, max_length=64)
    catalog_content_sha256: str = Field(min_length=64, max_length=64)
    final_authority_sha256: str = Field(min_length=64, max_length=64)

    @field_validator(
        "phase31_pointer_locator_sha256",
        "phase31_pointer_content_sha256",
        "phase31_validation_receipt_sha256",
        "phase31_snapshot_manifest_sha256",
        "phase31_snapshot_root_sha256",
        "frequency_bundle_locator_sha256",
        "frequency_bundle_content_sha256",
        "source_retrieval_sha256",
        "source_build_result_sha256",
        "source_review_aggregate_sha256",
        "provider_policy_sha256",
        "pilot_authority_sha256",
        "binding_receipt_sha256",
        "catalog_locator_sha256",
        "catalog_content_sha256",
        "final_authority_sha256",
    )
    @classmethod
    def hashes_must_be_sha256(cls, value: str, info: object) -> str:
        return _sha256_identifier(value, field_name=getattr(info, "field_name", "hash"))


class KoreanProviderCatalogPilotEvidence(_FrozenModel):
    job_id: str = Field(min_length=1, max_length=128)
    evidence_sha256: str = Field(min_length=64, max_length=64)
    expected_item_count: int = Field(ge=0)
    text_processed_items: int = Field(ge=0)
    text_accepted_items: int = Field(ge=0)
    text_review_required_items: int = Field(ge=0)
    catalog_voice_count: int = Field(ge=0)
    provider_call_count: int = Field(ge=0)
    provider_attempt_count: int = Field(ge=0)
    retry_attempt_count: int = Field(ge=0)
    cache_hit_count: int = Field(ge=0)
    synthesis_attempt_count: int = Field(ge=0)
    fallback_attempt_count: int = Field(ge=0)
    forbidden_attempt_count: int = Field(ge=0)
    token_denominator_count: int = Field(ge=0)
    missing_token_denominator_count: int = Field(ge=0)
    cost_denominator_count: int = Field(ge=0)
    missing_cost_denominator_count: int = Field(ge=0)
    latency_ms_total: int = Field(ge=0)
    provider_policy_sha256: str = Field(min_length=64, max_length=64)
    pilot_authority_sha256: str = Field(min_length=64, max_length=64)
    catalog_locator_sha256: str = Field(min_length=64, max_length=64)
    catalog_content_sha256: str = Field(min_length=64, max_length=64)
    provider_summaries: tuple[dict[str, object], ...]
    grants_route_authority: bool = False
    grants_voice_profile_authority: bool = False


def validate_korean_provider_catalog_pilot_result(
    *,
    authority: KoreanProviderCatalogPilotAuthority,
    provider_call_records: list[object],
    text_result: Mapping[str, object],
    catalog_result: Mapping[str, object],
    expected_item_count: int,
    protected_hashes: Mapping[str, tuple[str, str]],
    phase31_verifier=verify_active_korean_foundation_snapshot_provenance,
) -> KoreanProviderCatalogPilotEvidence:
    """Recompute pilot evidence without mutating authority or granting live powers."""

    if expected_item_count < 1:
        raise ValueError("Korean provider/catalog pilot expected count must be positive")
    if authority.binding_receipt_sha256 != authority.source_review_aggregate_sha256:
        raise ValueError("Korean provider/catalog pilot binding receipt drift")

    for label, pair in protected_hashes.items():
        before, after = pair
        _sha256_identifier(before, field_name=f"{label}_pre_sha256")
        _sha256_identifier(after, field_name=f"{label}_post_sha256")
        if before != after:
            raise ValueError("Korean provider/catalog pilot protected input drift")

    report = phase31_verifier(expected_receipt_sha256=authority.phase31_validation_receipt_sha256)
    expected_phase31 = {
        "receipt_sha256": authority.phase31_validation_receipt_sha256,
        "snapshot_manifest_sha256": authority.phase31_snapshot_manifest_sha256,
        "snapshot_root_sha256": authority.phase31_snapshot_root_sha256,
    }
    for field, value in expected_phase31.items():
        if getattr(report, field, None) != value:
            raise ValueError("Phase 31 active authority drift")

    _validate_result_binding(
        result=text_result,
        authority=authority,
        expected_item_count=expected_item_count,
        result_name="text result",
    )
    _validate_catalog_result(catalog_result, authority=authority)
    _validate_provider_rows(provider_call_records, authority=authority)

    synthesis_attempt_count = sum(
        1 for record in provider_call_records if str(getattr(record, "operation", "")) in _SYNTHESIS_OPERATIONS
    )
    fallback_attempt_count = sum(1 for record in provider_call_records if getattr(record, "fallback_from", None))
    forbidden_attempt_count = sum(
        1 for record in provider_call_records if str(getattr(record, "provider", "")).casefold() == "fallback"
    )
    if synthesis_attempt_count or fallback_attempt_count or forbidden_attempt_count:
        raise ValueError("Korean provider/catalog pilot requires zero synthesis, fallback, and forbidden attempts")

    provider_attempt_count = sum(
        1
        for record in provider_call_records
        if int(getattr(record, "attempt", 0) or 0) > 0 and str(getattr(record, "status", "")) != "cache_hit"
    )
    retry_attempt_count = sum(max(0, int(getattr(record, "attempt", 1) or 1) - 1) for record in provider_call_records)
    cache_hit_count = sum(1 for record in provider_call_records if str(getattr(record, "status", "")) == "cache_hit")
    missing_token_denominator_count = sum(
        1
        for record in provider_call_records
        if not any(getattr(record, field, None) is not None for field in ("input_tokens", "output_tokens", "total_tokens"))
    )
    missing_cost_denominator_count = sum(1 for record in provider_call_records if getattr(record, "estimated_cost", None) is None)
    latency_ms_total = sum(int(getattr(record, "latency_ms", 0) or 0) for record in provider_call_records)
    provider_summaries = tuple(summarize_provider_call_records(provider_call_records))

    text_processed_items = _int_result_value(text_result, "processed_items")
    text_accepted_items = _int_result_value(text_result, "accepted_items")
    text_review_required_items = _int_result_value(text_result, "review_required_items")
    catalog_voice_count = len(tuple(catalog_result.get("voices", ())))
    payload = {
        "job_id": authority.job_id,
        "expected_item_count": expected_item_count,
        "text_processed_items": text_processed_items,
        "text_accepted_items": text_accepted_items,
        "text_review_required_items": text_review_required_items,
        "catalog_voice_count": catalog_voice_count,
        "provider_call_count": len(provider_call_records),
        "provider_attempt_count": provider_attempt_count,
        "retry_attempt_count": retry_attempt_count,
        "cache_hit_count": cache_hit_count,
        "missing_token_denominator_count": missing_token_denominator_count,
        "missing_cost_denominator_count": missing_cost_denominator_count,
        "latency_ms_total": latency_ms_total,
        "provider_policy_sha256": authority.provider_policy_sha256,
        "pilot_authority_sha256": authority.pilot_authority_sha256,
        "catalog_locator_sha256": authority.catalog_locator_sha256,
        "catalog_content_sha256": authority.catalog_content_sha256,
        "provider_summaries": provider_summaries,
    }
    return KoreanProviderCatalogPilotEvidence(
        **payload,
        evidence_sha256=_canonical_sha256(payload),
        synthesis_attempt_count=synthesis_attempt_count,
        fallback_attempt_count=fallback_attempt_count,
        forbidden_attempt_count=forbidden_attempt_count,
        token_denominator_count=len(provider_call_records) - missing_token_denominator_count,
        cost_denominator_count=len(provider_call_records) - missing_cost_denominator_count,
        grants_route_authority=False,
        grants_voice_profile_authority=False,
    )


def _validate_result_binding(
    *,
    result: Mapping[str, object],
    authority: KoreanProviderCatalogPilotAuthority,
    expected_item_count: int,
    result_name: str,
) -> None:
    expected = {
        "job_id": authority.job_id,
        "binding_receipt_sha256": authority.binding_receipt_sha256,
        "provider_policy_sha256": authority.provider_policy_sha256,
        "pilot_authority_sha256": authority.pilot_authority_sha256,
    }
    for field, value in expected.items():
        if result.get(field) != value:
            raise ValueError(f"Korean provider/catalog pilot {result_name} authority drift")
    if _int_result_value(result, "processed_items") != expected_item_count:
        raise ValueError(f"Korean provider/catalog pilot {result_name} denominator mismatch")


def _validate_catalog_result(result: Mapping[str, object], *, authority: KoreanProviderCatalogPilotAuthority) -> None:
    expected = {
        "job_id": authority.job_id,
        "catalog_locator_sha256": authority.catalog_locator_sha256,
        "catalog_content_sha256": authority.catalog_content_sha256,
        "provider_policy_sha256": authority.provider_policy_sha256,
        "pilot_authority_sha256": authority.pilot_authority_sha256,
    }
    for field, value in expected.items():
        if result.get(field) != value:
            raise ValueError("Korean provider/catalog pilot catalog authority drift")
    voices = tuple(result.get("voices", ()))
    if not voices:
        raise ValueError("Korean provider/catalog pilot catalog is empty")
    if any(not isinstance(voice, Mapping) or voice.get("locale") != KOREAN_PROVIDER_LOCALE for voice in voices):
        raise ValueError("Korean provider/catalog pilot catalog locale drift")


def _validate_provider_rows(records: list[object], *, authority: KoreanProviderCatalogPilotAuthority) -> None:
    if not records:
        raise ValueError("Korean provider/catalog pilot requires provider call rows")
    for record in records:
        if getattr(record, "job_id", None) != authority.job_id:
            raise ValueError("Korean provider/catalog pilot contains wrong job")
        for field_name in (
            "route_policy_sha256",
            "budget_snapshot_sha256",
            "cache_key_sha256",
            "response_schema_sha256",
        ):
            value = getattr(record, field_name, None)
            if value is None:
                raise ValueError(f"Korean provider/catalog pilot missing {field_name}")
            _sha256_identifier(str(value), field_name=field_name)


def _int_result_value(result: Mapping[str, object], field_name: str) -> int:
    value = result.get(field_name)
    if not isinstance(value, int) or value < 0:
        raise ValueError(f"Korean provider/catalog pilot {field_name} is invalid")
    return value


__all__ = [
    "KoreanProviderCatalogPilotAuthority",
    "KoreanProviderCatalogPilotEvidence",
    "validate_korean_provider_catalog_pilot_result",
]
