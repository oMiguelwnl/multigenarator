"""Tests for read-only Korean provider/catalog pilot evidence reconciliation."""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from multilang.services.korean_provider_pilot_evidence import (
    KoreanProviderCatalogPilotAuthority,
    validate_korean_provider_catalog_pilot_result,
)


HASHES = tuple(f"{index:x}" * 64 for index in range(1, 16))


def _authority() -> KoreanProviderCatalogPilotAuthority:
    return KoreanProviderCatalogPilotAuthority(
        job_id="job-ko",
        phase31_pointer_locator_sha256=HASHES[0],
        phase31_pointer_content_sha256=HASHES[1],
        phase31_validation_receipt_sha256=HASHES[2],
        phase31_snapshot_manifest_sha256=HASHES[3],
        phase31_snapshot_root_sha256=HASHES[4],
        frequency_bundle_locator_sha256=HASHES[5],
        frequency_bundle_content_sha256=HASHES[6],
        source_retrieval_sha256=HASHES[7],
        source_build_result_sha256=HASHES[8],
        source_review_aggregate_sha256=HASHES[9],
        provider_policy_sha256=HASHES[10],
        pilot_authority_sha256=HASHES[11],
        binding_receipt_sha256=HASHES[9],
        catalog_locator_sha256=HASHES[12],
        catalog_content_sha256=HASHES[13],
        final_authority_sha256=HASHES[14],
    )


def _phase31_report() -> SimpleNamespace:
    return SimpleNamespace(
        receipt_sha256=HASHES[2],
        snapshot_manifest_sha256=HASHES[3],
        snapshot_root_sha256=HASHES[4],
    )


def _provider_record(
    *,
    operation: str,
    status: str,
    attempt: int,
    item_key: str = "sample-1",
    input_tokens: int | None = 10,
    output_tokens: int | None = 20,
    total_tokens: int | None = 30,
    estimated_cost: float | None = 0.01,
    fallback_from: str | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        job_id="job-ko",
        item_key=item_key,
        operation=operation,
        provider="openai",
        model="gpt-fixture",
        voice_id=None,
        status=status,
        attempt=attempt,
        latency_ms=120 if attempt else 0,
        error_code=None,
        error_summary=None,
        fallback_from=fallback_from,
        prompt_hash="p" * 64,
        response_hash="r" * 64,
        route_policy_sha256=HASHES[10],
        budget_snapshot_sha256=HASHES[11],
        cache_key_sha256=HASHES[12],
        response_schema_sha256=HASHES[13],
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=total_tokens,
        estimated_cost=estimated_cost,
    )


def _text_result() -> dict[str, object]:
    return {
        "job_id": "job-ko",
        "binding_receipt_sha256": HASHES[9],
        "provider_policy_sha256": HASHES[10],
        "pilot_authority_sha256": HASHES[11],
        "processed_items": 3,
        "accepted_items": 2,
        "review_required_items": 1,
        "example_sentence": "안녕하세요 should not appear in output",
    }


def _catalog_result() -> dict[str, object]:
    return {
        "job_id": "job-ko",
        "catalog_locator_sha256": HASHES[12],
        "catalog_content_sha256": HASHES[13],
        "provider_policy_sha256": HASHES[10],
        "pilot_authority_sha256": HASHES[11],
        "voices": [
            {"voice_id": "ko-KR-SunHiNeural", "locale": "ko-KR"},
            {"voice_id": "ko-KR-InJoonNeural", "locale": "ko-KR"},
        ],
    }


def test_provider_catalog_result_validator_reconciles_phase31_and_denominators_without_authority_grants() -> None:
    records = [
        _provider_record(operation="definition", status="success", attempt=1, item_key="sample-1"),
        _provider_record(
            operation="sentence_generation",
            status="failure",
            attempt=2,
            item_key="sample-2",
            input_tokens=None,
            output_tokens=None,
            total_tokens=None,
            estimated_cost=None,
        ),
        _provider_record(operation="translation", status="cache_hit", attempt=0, item_key="sample-3"),
        _provider_record(operation="catalog", status="success", attempt=1, item_key="catalog"),
    ]

    evidence = validate_korean_provider_catalog_pilot_result(
        authority=_authority(),
        provider_call_records=records,
        text_result=_text_result(),
        catalog_result=_catalog_result(),
        expected_item_count=3,
        protected_hashes={"bundle_manifest": (HASHES[5], HASHES[5])},
        phase31_verifier=lambda **_: _phase31_report(),
    )

    assert evidence.job_id == "job-ko"
    assert evidence.expected_item_count == 3
    assert evidence.text_processed_items == 3
    assert evidence.catalog_voice_count == 2
    assert evidence.provider_call_count == 4
    assert evidence.provider_attempt_count == 3
    assert evidence.retry_attempt_count == 1
    assert evidence.cache_hit_count == 1
    assert evidence.synthesis_attempt_count == 0
    assert evidence.fallback_attempt_count == 0
    assert evidence.token_denominator_count == 3
    assert evidence.missing_token_denominator_count == 1
    assert evidence.cost_denominator_count == 3
    assert evidence.missing_cost_denominator_count == 1
    assert evidence.latency_ms_total == 360
    assert not evidence.grants_route_authority
    assert not evidence.grants_voice_profile_authority
    serialized = evidence.model_dump_json()
    assert "sample-1" not in serialized
    assert "안녕하세요" not in serialized
    assert len(evidence.evidence_sha256) == 64


def test_provider_catalog_result_validator_rejects_zero_synthesis_violation() -> None:
    records = [_provider_record(operation="word_audio", status="success", attempt=1)]

    with pytest.raises(ValueError, match="synthesis"):
        validate_korean_provider_catalog_pilot_result(
            authority=_authority(),
            provider_call_records=records,
            text_result=_text_result(),
            catalog_result=_catalog_result(),
            expected_item_count=3,
            protected_hashes={},
            phase31_verifier=lambda **_: _phase31_report(),
        )


def test_provider_catalog_result_validator_detects_phase31_drift() -> None:
    bad_report = SimpleNamespace(
        receipt_sha256=HASHES[2],
        snapshot_manifest_sha256=HASHES[3],
        snapshot_root_sha256=HASHES[6],
    )

    with pytest.raises(ValueError, match="Phase 31"):
        validate_korean_provider_catalog_pilot_result(
            authority=_authority(),
            provider_call_records=[_provider_record(operation="catalog", status="success", attempt=1)],
            text_result=_text_result(),
            catalog_result=_catalog_result(),
            expected_item_count=3,
            protected_hashes={},
            phase31_verifier=lambda **_: bad_report,
        )


def test_provider_catalog_result_validator_detects_authority_invariance_mutation() -> None:
    with pytest.raises(ValueError, match="input drift"):
        validate_korean_provider_catalog_pilot_result(
            authority=_authority(),
            provider_call_records=[_provider_record(operation="catalog", status="success", attempt=1)],
            text_result=_text_result(),
            catalog_result=_catalog_result(),
            expected_item_count=3,
            protected_hashes={"provider_policy": (HASHES[10], HASHES[11])},
            phase31_verifier=lambda **_: _phase31_report(),
        )


def test_provider_catalog_result_validator_output_is_canonical_and_hash_only() -> None:
    evidence = validate_korean_provider_catalog_pilot_result(
        authority=_authority(),
        provider_call_records=[_provider_record(operation="catalog", status="success", attempt=1)],
        text_result=_text_result(),
        catalog_result=_catalog_result(),
        expected_item_count=3,
        protected_hashes={},
        phase31_verifier=lambda **_: _phase31_report(),
    )

    payload = json.loads(evidence.model_dump_json())
    assert payload["provider_summaries"][0]["operation"] == "catalog"
    assert "model" not in payload["provider_summaries"][0]
    assert "item_key" not in json.dumps(payload)
