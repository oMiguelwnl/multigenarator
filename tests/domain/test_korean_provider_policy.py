from __future__ import annotations

import pytest

from multilang.domain.korean import raw_bytes_sha256
from multilang.settings import Settings


def _hash(seed: str) -> str:
    return raw_bytes_sha256(seed.encode("utf-8"))


def _budget(**overrides: object):
    from multilang.domain.korean_provider import KoreanProviderBudget

    payload: dict[str, object] = {
        "max_attempts": 2,
        "max_input_tokens": 512,
        "max_output_tokens": 192,
        "max_total_tokens": 704,
        "max_estimated_cost_usd": 0.05,
        "max_latency_ms": 30_000,
        "timeout_seconds": 15.0,
        "max_batch_items": 4,
        "max_concurrency": 1,
    }
    payload.update(overrides)
    return KoreanProviderBudget(**payload)


def _route(task: object, **overrides: object):
    from multilang.domain.korean_provider import KoreanProviderRoute

    provider = "disabled" if overrides.get("disabled") else "litellm"
    model = None if provider == "disabled" else "openai/gpt-4o-mini"
    payload: dict[str, object] = {
        "task": task,
        "provider": provider,
        "model": model,
        "budget": _budget(),
        "cache_namespace": "korean-frequency-text",
        "response_schema_sha256": _hash(f"schema-{task}"),
    }
    payload.update({key: value for key, value in overrides.items() if key != "disabled"})
    return KoreanProviderRoute(**payload)


def _routes() -> tuple[object, ...]:
    from multilang.domain.korean_provider import KoreanProviderTask

    return tuple(
        _route(task, disabled=(task is KoreanProviderTask.JUDGE))
        for task in KoreanProviderTask
    )


def test_route_policy_requires_all_tasks_no_fallback_and_hashable_budget() -> None:
    from multilang.domain.korean_provider import (
        KOREAN_PROVIDER_REQUIRED_TASKS,
        KoreanProviderPolicy,
        KoreanProviderRoute,
        KoreanProviderTask,
    )

    policy = KoreanProviderPolicy(routes=_routes())

    assert {route.task for route in policy.routes} == set(KOREAN_PROVIDER_REQUIRED_TASKS)
    assert len(policy.policy_sha256) == 64
    assert policy.fallback_policy == "none"
    route = policy.route_for(KoreanProviderTask.SENTENCE_GENERATION)
    assert route.fallback_policy == "none"
    assert len(route.route_policy_sha256) == 64
    assert len(route.budget_snapshot_sha256) == 64
    assert route.cache_key_sha256(item_sha256=_hash("item"), input_sha256=_hash("input")) == route.cache_key_sha256(
        item_sha256=_hash("item"), input_sha256=_hash("input")
    )

    with pytest.raises(ValueError, match="exactly one route"):
        KoreanProviderPolicy(routes=_routes()[:-1])
    with pytest.raises(ValueError):
        KoreanProviderRoute(
            task=KoreanProviderTask.DEFINITION,
            provider="litellm",
            model="openai/gpt-4o-mini",
            budget=_budget(),
            cache_namespace="korean-frequency-text",
            response_schema_sha256=_hash("schema"),
            fallback_policy="google",
        )
    with pytest.raises(ValueError, match="enabled route requires model"):
        KoreanProviderRoute(
            task=KoreanProviderTask.DEFINITION,
            provider="litellm",
            model=None,
            budget=_budget(),
            cache_namespace="korean-frequency-text",
            response_schema_sha256=_hash("schema"),
        )


def test_budget_denominator_privacy_and_same_route_retry_are_enforced_before_work() -> None:
    from multilang.domain.korean_provider import KoreanProviderResultSummary, KoreanProviderRoute, KoreanProviderTask

    route = _route(KoreanProviderTask.SENTENCE_GENERATION)
    route.assert_within_budget(
        input_tokens=100,
        output_tokens=50,
        estimated_cost_usd=0.01,
        latency_ms=1000,
        batch_items=1,
        concurrency=1,
        timeout_seconds=5.0,
    )
    assert route.retry_allowed(attempt=2, route_policy_sha256=route.route_policy_sha256) is True

    with pytest.raises(ValueError, match="token budget exceeded"):
        route.assert_within_budget(
            input_tokens=600,
            output_tokens=200,
            estimated_cost_usd=0.01,
            latency_ms=1000,
            batch_items=1,
            concurrency=1,
            timeout_seconds=5.0,
        )
    with pytest.raises(ValueError, match="same route"):
        route.retry_allowed(attempt=2, route_policy_sha256=_hash("other-route"))
    with pytest.raises(ValueError, match="attempt budget exceeded"):
        route.retry_allowed(attempt=3, route_policy_sha256=route.route_policy_sha256)

    summary = KoreanProviderResultSummary(
        task=KoreanProviderTask.SENTENCE_GENERATION,
        provider=route.provider,
        status="cache_hit",
        availability_denominator="cache_hit",
        attempt=0,
        latency_ms=0,
        route_policy_sha256=route.route_policy_sha256,
        budget_snapshot_sha256=route.budget_snapshot_sha256,
        cache_key_sha256=route.cache_key_sha256(item_sha256=_hash("item"), input_sha256=_hash("input")),
        response_schema_sha256=route.response_schema_sha256,
    )
    assert summary.availability_denominator == "cache_hit"
    assert summary.input_tokens is None
    assert summary.estimated_cost_usd is None

    with pytest.raises(ValueError):
        KoreanProviderResultSummary(
            task=KoreanProviderTask.SENTENCE_GENERATION,
            provider=route.provider,
            status="success",
            availability_denominator="attempted",
            attempt=1,
            latency_ms=100,
            route_policy_sha256=route.route_policy_sha256,
            budget_snapshot_sha256=route.budget_snapshot_sha256,
            cache_key_sha256=route.cache_key_sha256(item_sha256=_hash("item"), input_sha256=_hash("input")),
            response_schema_sha256=route.response_schema_sha256,
            prompt="raw prompt with /home/reader/private.txt",
        )
    with pytest.raises(ValueError):
        KoreanProviderRoute(
            task=KoreanProviderTask.TRANSLATION,
            provider="deepl_api_key=secret",
            model="deepl-v2",
            budget=_budget(),
            cache_namespace="korean-frequency-text",
            response_schema_sha256=_hash("schema"),
        )


def test_settings_policy_values_are_proposals_not_live_authority() -> None:
    from multilang.domain.korean_provider import KoreanProviderPolicyProposal, propose_korean_provider_policy_from_settings

    settings = Settings(
        _env_file=None,
        korean_provider_policy_version="korean-provider-policy-v1",
        korean_provider_max_attempts=2,
        text_generation_provider="litellm",
        text_generation_model="openai/gpt-4o-mini",
        translation_provider="deepl",
    )

    proposal = propose_korean_provider_policy_from_settings(settings)

    assert proposal.approval_status == "proposal_only"
    assert proposal.can_authorize_live_calls is False
    assert proposal.text_generation_provider == "litellm"
    assert proposal.translation_provider == "deepl"

    with pytest.raises(ValueError):
        KoreanProviderPolicyProposal(
            policy_version="korean-provider-policy-v1",
            settings_fingerprint_sha256=_hash("settings"),
            text_generation_provider="litellm",
            text_generation_model="openai/gpt-4o-mini",
            translation_provider="deepl",
            max_attempts=2,
            approval_status="approved",
        )
