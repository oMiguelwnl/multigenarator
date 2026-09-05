"""Exact private-processing authority contracts for Phase 33 highlights."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from importlib import import_module, util

import pytest
from pydantic import ValidationError


SHA_A = "a" * 64
SHA_B = "b" * 64
SHA_C = "c" * 64
SHA_D = "d" * 64
SHA_E = "e" * 64
ISSUED_AT = datetime(2026, 8, 30, 12, 0, tzinfo=UTC)


def _api():
    assert util.find_spec("multilang.domain.private_processing") is not None, (
        "the private-processing domain contract module must exist"
    )
    return import_module("multilang.domain.private_processing")


def _policy(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "policy_version": "private-processing-policy-v1",
        "policy_sha256": SHA_D,
        "tokenization_rule_id": "phase33-private-token-v1",
        "max_context_tokens": 12,
        "max_context_code_points": 160,
        "max_context_utf8_bytes": 512,
        "max_provider_attempts": 1,
        "max_estimated_cost_usd": 0.05,
        "redaction_policy_version": "phase33-private-redaction-v1",
    }
    payload.update(overrides)
    return payload


def _capability(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "capability_id": "cap-" + "1" * 40,
        "job_id": "job-33",
        "run_id": "run-20260830",
        "item_id": "highlight-item-0001",
        "excerpt_revision_id": "excerpt-revision-0001",
        "excerpt_sha256": SHA_A,
        "target_start": 3,
        "target_end": 5,
        "target_text_sha256": SHA_B,
        "provider_id": "route-openai-sentence",
        "provider": "openai",
        "model": "gpt-5.5",
        "route_id": "korean-highlight-microexample",
        "provider_route_sha256": SHA_C,
        "purpose": "highlight_microexample_context",
        "policy_version": "private-processing-policy-v1",
        "policy_sha256": SHA_D,
        "tokenization_rule_id": "phase33-private-token-v1",
        "max_context_tokens": 12,
        "max_context_code_points": 160,
        "max_context_utf8_bytes": 512,
        "max_provider_attempts": 1,
        "max_estimated_cost_usd": 0.05,
        "idempotency": {"support": "unsupported", "key": None},
        "issued_at": ISSUED_AT,
        "expires_at": ISSUED_AT + timedelta(minutes=10),
        "issuer_id": "local-operator",
        "issuer_intent_sha256": SHA_E,
        "state": "pending",
        "version": 0,
    }
    payload.update(overrides)
    return payload


def _validation_request(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "job_id": "job-33",
        "run_id": "run-20260830",
        "item_id": "highlight-item-0001",
        "excerpt_revision_id": "excerpt-revision-0001",
        "excerpt_sha256": SHA_A,
        "target_start": 3,
        "target_end": 5,
        "target_text_sha256": SHA_B,
        "provider": "openai",
        "model": "gpt-5.5",
        "route_id": "korean-highlight-microexample",
        "provider_route_sha256": SHA_C,
        "purpose": "highlight_microexample_context",
        "policy_sha256": SHA_D,
        "now": ISSUED_AT + timedelta(minutes=1),
    }
    payload.update(overrides)
    return payload


def test_exact_capability_validates_only_for_exact_provider_purpose_and_hash_bindings() -> None:
    api = _api()

    capability = api.PrivateProcessingCapability(**_capability())

    assert capability.state == api.PrivateDisclosureState.PENDING
    assert capability.tokenization_rule_id == api.PRIVATE_TOKENIZATION_RULE_ID
    assert capability.max_context_tokens == 12
    with pytest.raises(ValidationError):
        capability.model_copy(update={"provider": "anthropic"}, deep=True).provider = "openai"

    assert api.validate_private_processing_capability(
        capability,
        **_validation_request(),
    ) is None

    refusal = api.validate_private_processing_capability(
        capability,
        **_validation_request(model="gpt-provider-any"),
    )
    assert refusal is not None
    assert refusal.reason_code == api.PrivateProcessingRefusalReason.BINDING_MISMATCH
    assert refusal.adapter_call_status == "not_called"
    assert "highlight-item-0001" not in refusal.model_dump_json()


def test_wildcard_provider_model_route_and_boolean_allow_private_are_rejected() -> None:
    api = _api()

    wildcard_cases = (
        {"provider": "*"},
        {"model": "model-any"},
        {"route_id": "all"},
        {"purpose": "source-wide"},
    )
    for mutation in wildcard_cases:
        with pytest.raises(ValidationError):
            api.PrivateProcessingCapability(**_capability(**mutation))

    with pytest.raises(ValidationError) as excinfo:
        api.PrivateProcessingCapability(
            **_capability(
                allow_private=True,
                hidden_input="민감한 하이라이트와 /home/private/book.txt",
            )
        )
    rendered = str(excinfo.value)
    assert "민감한" not in rendered
    assert "/home/private" not in rendered


def test_provider_idempotency_support_key_and_attempt_budget_are_exact() -> None:
    api = _api()

    supported = api.PrivateProcessingCapability(
        **_capability(
            idempotency={"support": "supported", "key": "idem-key-0001"},
            max_provider_attempts=2,
        )
    )
    assert supported.idempotency.support == "supported"
    assert supported.idempotency.key == "idem-key-0001"
    single_attempt_supported = api.PrivateProcessingCapability(
        **_capability(idempotency={"support": "supported", "key": "idem-key-0001"})
    )
    assert single_attempt_supported.max_provider_attempts == 1

    invalid_cases = (
        _capability(idempotency={"support": "supported", "key": None}, max_provider_attempts=2),
        _capability(idempotency={"support": "unsupported", "key": "idem-key-0001"}),
        _capability(idempotency={"support": "unsupported", "key": None}, max_provider_attempts=2),
    )
    for payload in invalid_cases:
        with pytest.raises(ValidationError):
            api.PrivateProcessingCapability(**payload)


def test_budget_policy_token_cap_24_and_unknown_token_rule_fail_closed() -> None:
    api = _api()

    assert api.PrivateProcessingPolicy(**_policy(max_context_tokens=24)).max_context_tokens == 24
    for mutation in (
        {"max_context_tokens": 0},
        {"max_context_tokens": 25},
        {"tokenization_rule_id": "wordpiece-any"},
        {"max_context_code_points": api.MAX_PRIVATE_CONTEXT_CODE_POINTS + 1},
        {"max_context_utf8_bytes": api.MAX_PRIVATE_CONTEXT_UTF8_BYTES + 1},
    ):
        with pytest.raises(ValidationError):
            api.PrivateProcessingPolicy(**_policy(**mutation))


def test_token_v1_unicode_count_normalizes_nfc_and_counts_punctuation_symbols() -> None:
    api = _api()

    text = "가나다 cafe\u0301 3.14?! 👋\n\t끝"
    tokens = api.tokenize_private_context_v1(text)

    assert [token.text for token in tokens] == ["가나다", "café", "3", ".", "14", "?", "!", "👋", "끝"]
    assert api.count_private_context_tokens_v1(text) == 9
    assert tokens[1].text == "café"


def test_consumed_state_transitions_require_versions_and_never_reset_closed_states() -> None:
    api = _api()

    transition = api.PrivateDisclosureStateTransition(
        capability_id="cap-" + "1" * 40,
        from_state="pending",
        to_state="disclosing",
        expected_version=0,
        next_version=1,
    )

    assert transition.to_state == api.PrivateDisclosureState.DISCLOSING
    for mutation in (
        {"from_state": "pending", "to_state": "disclosed", "expected_version": 0, "next_version": 1},
        {"from_state": "disclosed", "to_state": "pending", "expected_version": 1, "next_version": 2},
        {"from_state": "failed_unknown", "to_state": "pending", "expected_version": 1, "next_version": 2},
        {"from_state": "pending", "to_state": "disclosing", "expected_version": 2, "next_version": 2},
    ):
        with pytest.raises(ValidationError):
            api.PrivateDisclosureStateTransition(capability_id="cap-" + "1" * 40, **mutation)


def test_private_content_free_receipts_and_refusals_forbid_context_prompt_payload_fields() -> None:
    api = _api()

    receipt = api.PrivateProcessingReceipt(
        receipt_id="receipt-0001",
        capability_id_sha256=SHA_A,
        job_id_sha256=SHA_B,
        item_id_sha256=SHA_C,
        excerpt_revision_id_sha256=SHA_D,
        excerpt_sha256=SHA_A,
        context_sha256=SHA_B,
        context_token_count=4,
        context_code_point_count=12,
        context_utf8_byte_count=36,
        provider_id="route-openai-sentence",
        provider="openai",
        model="gpt-5.5",
        route_id="korean-highlight-microexample",
        provider_route_sha256=SHA_C,
        purpose="highlight_microexample_context",
        policy_version="private-processing-policy-v1",
        policy_sha256=SHA_D,
        tokenization_rule_id="phase33-private-token-v1",
        idempotency_key_sha256=None,
        state="disclosed",
        receipt_sha256=SHA_E,
    )
    refusal = api.PrivateProcessingRefusal(
        reason_code="missing_capability",
        capability_id_sha256=None,
        policy_sha256=SHA_D,
    )

    for serialized in (receipt.model_dump_json(), refusal.model_dump_json()):
        assert "민감한" not in serialized
        assert "context_text" not in serialized
        assert "excerpt_text" not in serialized
        assert "prompt" not in serialized
        assert "payload" not in serialized

    with pytest.raises(ValidationError):
        api.PrivateProcessingReceipt(**(receipt.model_dump(mode="json") | {"context_text": "민감한 원문"}))
