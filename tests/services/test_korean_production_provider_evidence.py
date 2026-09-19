"""Production evidence must reconcile real route telemetry without inventing TTS usage."""

from hashlib import sha256
from types import SimpleNamespace

import pytest

from multilang.domain.korean_provider import (
    KoreanProviderBudget,
    KoreanProviderPolicy,
    KoreanProviderRoute,
    KoreanProviderTask,
)
from multilang.services.korean_production_evidence import (
    KoreanProductionEvidenceAuthority,
    _validate_provider_rows,
)


def _hash(value):
    return sha256(value.encode()).hexdigest()


def provider_policy():
    budget = KoreanProviderBudget(
        max_attempts=2, max_input_tokens=4096, max_output_tokens=4096,
        max_total_tokens=8192, max_estimated_cost_usd=1, max_latency_ms=60000,
        timeout_seconds=60, max_batch_items=3000, max_concurrency=1,
    )
    return KoreanProviderPolicy(routes=tuple(
        KoreanProviderRoute(
            task=task, provider="azure-speech" if task.value.endswith("audio") else "openai",
            model="ko-KR-SunHiNeural" if task.value.endswith("audio") else "fixture-model",
            budget=budget, cache_namespace=f"fixture-{task.value}",
            response_schema_sha256=_hash(f"schema-{task.value}"),
        ) for task in KoreanProviderTask
    ))


def _case(task=KoreanProviderTask.WORD_AUDIO, **overrides):
    policy = provider_policy()
    route = policy.route_for(task)
    authority = KoreanProductionEvidenceAuthority(**{
        **{field: _hash(field) for field in KoreanProductionEvidenceAuthority.model_fields
           if field != "job_id"},
        "job_id": "fixture-production", "provider_policy_sha256": policy.policy_sha256,
    })
    row = SimpleNamespace(
        job_id=authority.job_id, provider=route.provider, model=route.model,
        operation=task.value, voice_id=route.model if task.value.endswith("audio") else None,
        route_policy_sha256=route.route_policy_sha256,
        budget_snapshot_sha256=route.budget_snapshot_sha256,
        response_schema_sha256=route.response_schema_sha256,
        prompt_hash=_hash("request"), response_hash=_hash("response"), cache_key_sha256=_hash("cache"),
        status="success", attempt=1, latency_ms=100,
        input_tokens=None, output_tokens=None, total_tokens=None, estimated_cost=None,
    )
    row.__dict__.update(overrides)
    return policy, authority, row


def test_real_azure_route_usage_remains_unknown_in_evidence():
    policy, authority, row = _case()
    assert row.route_policy_sha256 != authority.provider_policy_sha256
    counts = _validate_provider_rows((row,), authority=authority, provider_policy=policy)
    assert counts["synthesis_attempt_count"] == 1
    assert counts["missing_token_denominator_count"] == 1
    assert counts["missing_cost_denominator_count"] == 1
    summary = counts["provider_summaries"][0]
    assert summary["total_tokens"] is None
    assert summary["estimated_cost"] is None
    assert summary["token_usage_status"] == "unknown"
    assert summary["cost_usage_status"] == "unknown"


@pytest.mark.parametrize("field", [
    "provider", "model", "operation", "route_policy_sha256", "budget_snapshot_sha256",
    "response_schema_sha256", "voice_id",
])
def test_provider_evidence_rejects_route_identity_drift(field):
    policy, authority, row = _case(**{field: _hash("drift")})
    with pytest.raises(ValueError, match="provider.*drift"):
        _validate_provider_rows((row,), authority=authority, provider_policy=policy)


def test_provider_evidence_rejects_different_bound_policy():
    policy, authority, row = _case()
    authority = authority.model_copy(update={"provider_policy_sha256": _hash("different")})
    with pytest.raises(ValueError, match="provider policy.*drift"):
        _validate_provider_rows((row,), authority=authority, provider_policy=policy)


@pytest.mark.parametrize("usage", [
    {}, {"input_tokens": 1, "output_tokens": 2, "total_tokens": 3},
    {"estimated_cost": 0.01},
])
def test_successful_llm_usage_is_still_required(usage):
    policy, authority, row = _case(KoreanProviderTask.DEFINITION, **usage)
    with pytest.raises(ValueError, match="provider denominator drift"):
        _validate_provider_rows((row,), authority=authority, provider_policy=policy)


def test_failed_azure_attempt_counts_unknown_outcome_without_response_hash():
    policy, authority, row = _case(status="failure", response_hash=None, error_code="timeout")
    counts = _validate_provider_rows((row,), authority=authority, provider_policy=policy)
    assert counts["provider_attempt_count"] == 1
    assert counts["provider_failure_count"] == 1
    assert counts["provider_unknown_outcome_count"] == 1
    assert counts["provider_summaries"][0]["estimated_cost"] is None


@pytest.mark.parametrize("overrides", [
    {"estimated_cost": -1}, {"estimated_cost": float("nan")}, {"estimated_cost": 2},
    {"input_tokens": -1}, {"input_tokens": 4097}, {"total_tokens": 8193},
    {"attempt": 3}, {"attempt": 0}, {"status": "made-up"},
])
def test_provider_evidence_rejects_invalid_or_over_budget_usage(overrides):
    policy, authority, row = _case(**overrides)
    with pytest.raises(ValueError, match="provider.*(budget|usage|status|attempt).*(drift|exceeded)"):
        _validate_provider_rows((row,), authority=authority, provider_policy=policy)
