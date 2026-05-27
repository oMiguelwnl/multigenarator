from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from multilang.db.base import Base
from multilang.repositories.provider_call_log_repository import ProviderCallLogCreate, ProviderCallLogRepository


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
