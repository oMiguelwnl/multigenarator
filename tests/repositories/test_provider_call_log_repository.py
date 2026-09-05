from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from multilang.db.base import Base
from multilang.domain.korean import raw_bytes_sha256
from multilang.repositories.provider_call_log_repository import ProviderCallLogCreate, ProviderCallLogRepository


def _hash(seed: str) -> str:
    return raw_bytes_sha256(seed.encode("utf-8"))


def test_provider_call_log_repository_inserts_redacted_records() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    repo = ProviderCallLogRepository(Session(engine))

    row = repo.insert(
        ProviderCallLogCreate(
            job_id="job-1",
            item_key="item-1",
            operation="sentence",
            provider="litellm",
            model="openai/gpt-4o-mini",
            attempt=2,
            latency_ms=42,
            status="failure",
            error_code="RateLimitError",
            error_summary="429 api_key=secret raw private sentence",
            prompt_hash="a" * 64,
            response_hash="b" * 64,
            input_tokens=10,
            output_tokens=5,
            total_tokens=15,
        )
    )

    assert row.provider == "litellm"
    assert row.attempt == 2
    assert "secret" not in (row.error_summary or "")


def test_provider_call_log_repository_summarizes_calls() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    repo = ProviderCallLogRepository(Session(engine))
    repo.insert(ProviderCallLogCreate(job_id="job-1", operation="sentence", provider="litellm", status="success", latency_ms=10, total_tokens=3))
    repo.insert(ProviderCallLogCreate(job_id="job-1", operation="sentence", provider="litellm", status="success", latency_ms=30, attempt=2, total_tokens=7))

    summary = repo.summarize_for_job("job-1")

    assert summary == [
        {
            "provider": "litellm",
            "operation": "sentence",
            "status": "success",
            "calls": 2,
            "retry_attempts": 1,
            "latency_ms_total": 40,
            "latency_ms_p95": 10,
            "latency_ms_avg": 20.0,
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 10,
            "estimated_cost": 0.0,
            "fallback_count": 0,
            "circuit_open_blocks": 0,
        }
    ]


def test_provider_call_log_summary_keeps_route_cache_token_cost_latency_denominators_without_content() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    repo = ProviderCallLogRepository(Session(engine))
    repo.insert(
        ProviderCallLogCreate(
            job_id="job-1",
            item_key="rank-0001",
            operation="sentence_generation",
            provider="litellm",
            model="openai/gpt-4o-mini",
            status="success",
            latency_ms=20,
            route_policy_sha256=_hash("route"),
            budget_snapshot_sha256=_hash("budget"),
            cache_key_sha256=_hash("cache"),
            response_schema_sha256=_hash("schema"),
            input_tokens=50,
            output_tokens=20,
            total_tokens=70,
            estimated_cost=0.002,
        )
    )
    repo.insert(
        ProviderCallLogCreate(
            job_id="job-1",
            item_key="rank-0002",
            operation="sentence_generation",
            provider="litellm",
            model="openai/gpt-4o-mini",
            status="success",
            latency_ms=40,
            route_policy_sha256=_hash("route"),
            budget_snapshot_sha256=_hash("budget"),
            cache_key_sha256=_hash("cache"),
            response_schema_sha256=_hash("schema"),
        )
    )
    failure = repo.insert(
        ProviderCallLogCreate(
            job_id="job-1",
            item_key="rank-0003",
            operation="sentence_generation",
            provider="litellm",
            status="failure",
            error_code="RateLimitError",
            error_summary="raw exception api_key=secret /home/reader/private.txt provider payload",
            route_policy_sha256=_hash("route"),
            budget_snapshot_sha256=_hash("budget"),
            cache_key_sha256=_hash("cache-failure"),
            response_schema_sha256=_hash("schema"),
        )
    )

    summary = repo.summarize_for_job("job-1")

    success_summary = next(item for item in summary if item["status"] == "success")
    assert success_summary["route_policy_sha256"] == _hash("route")
    assert success_summary["route_policy_sha256_value_count"] == 1
    assert success_summary["budget_snapshot_sha256"] == _hash("budget")
    assert success_summary["cache_key_sha256"] == _hash("cache")
    assert success_summary["response_schema_sha256"] == _hash("schema")
    assert success_summary["token_value_count"] == 1
    assert success_summary["cost_value_count"] == 1
    assert success_summary["input_tokens"] == 50
    assert success_summary["output_tokens"] == 20
    assert success_summary["estimated_cost"] == 0.002
    assert "secret" not in (failure.error_summary or "")
    assert "/home/reader" not in (failure.error_summary or "")
    assert not hasattr(failure, "prompt")
    assert not hasattr(failure, "output")
