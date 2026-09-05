"""Repository for privacy-safe provider-call telemetry."""

from __future__ import annotations

from dataclasses import dataclass
import re
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from multilang.db.models import ProviderCallLogModel
from multilang.security.redaction import redact_sensitive_text


@dataclass(frozen=True, slots=True)
class ProviderCallLogCreate:
    operation: str
    provider: str
    status: str
    attempt: int = 1
    latency_ms: int = 0
    job_id: str | None = None
    item_key: str | None = None
    model: str | None = None
    voice_id: str | None = None
    error_code: str | None = None
    error_summary: str | None = None
    fallback_from: str | None = None
    prompt_hash: str | None = None
    response_hash: str | None = None
    route_policy_sha256: str | None = None
    budget_snapshot_sha256: str | None = None
    cache_key_sha256: str | None = None
    response_schema_sha256: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    estimated_cost: float | None = None


class ProviderCallLogRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def insert(self, record: ProviderCallLogCreate) -> ProviderCallLogModel:
        row = ProviderCallLogModel(
            id=str(uuid4()),
            job_id=record.job_id,
            item_key=record.item_key,
            operation=record.operation,
            provider=record.provider,
            model=record.model,
            voice_id=record.voice_id,
            attempt=record.attempt,
            latency_ms=record.latency_ms,
            status=record.status,
            error_code=record.error_code,
            error_summary=_safe_error_summary(record.error_summary, error_code=record.error_code),
            fallback_from=record.fallback_from,
            prompt_hash=record.prompt_hash,
            response_hash=record.response_hash,
            route_policy_sha256=record.route_policy_sha256,
            budget_snapshot_sha256=record.budget_snapshot_sha256,
            cache_key_sha256=record.cache_key_sha256,
            response_schema_sha256=record.response_schema_sha256,
            input_tokens=record.input_tokens,
            output_tokens=record.output_tokens,
            total_tokens=record.total_tokens,
            estimated_cost=record.estimated_cost,
        )
        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        return row

    def list_for_job(self, job_id: str) -> list[ProviderCallLogModel]:
        return list(
            self.session.scalars(
                select(ProviderCallLogModel)
                .where(ProviderCallLogModel.job_id == job_id)
                .order_by(ProviderCallLogModel.created_at.asc(), ProviderCallLogModel.operation.asc())
            )
        )

    def summarize_for_job(self, job_id: str) -> list[dict[str, object]]:
        return summarize_provider_call_records(self.list_for_job(job_id))


_SAFE_ERROR_LABEL_RE = re.compile(r"[^a-z0-9_.:-]+")
_EVIDENCE_HASH_FIELDS = (
    "route_policy_sha256",
    "budget_snapshot_sha256",
    "cache_key_sha256",
    "response_schema_sha256",
)


def _safe_error_summary(value: str | None, *, error_code: str | None) -> str | None:
    redacted = redact_sensitive_text(value or "").strip()
    if not redacted:
        return None
    label_source = error_code or redacted.split(":", 1)[0] or "provider_error"
    label = _SAFE_ERROR_LABEL_RE.sub("_", label_source.strip().casefold()).strip("_:. -")
    if not label:
        label = "provider_error"
    return f"{label}: redacted provider failure"


def summarize_provider_call_records(records: list[object]) -> list[dict[str, object]]:
    buckets: dict[tuple[str, str, str], dict[str, object]] = {}
    for record in records:
        key = (str(getattr(record, "provider", "unknown")), str(getattr(record, "operation", "unknown")), str(getattr(record, "status", "unknown")))
        bucket = buckets.setdefault(
            key,
            {
                "provider": key[0],
                "operation": key[1],
                "status": key[2],
                "calls": 0,
                "retry_attempts": 0,
                "latency_ms_total": 0,
                "latency_ms_p95": 0,
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0,
                "estimated_cost": 0.0,
                "fallback_count": 0,
                "circuit_open_blocks": 0,
            },
        )
        for field in _EVIDENCE_HASH_FIELDS:
            value = getattr(record, field, None)
            if value:
                values = bucket.setdefault(f"_{field}_values", set())
                assert isinstance(values, set)
                values.add(value)
        bucket["calls"] = int(bucket["calls"]) + 1
        attempt = int(getattr(record, "attempt", 1) or 1)
        bucket["retry_attempts"] = int(bucket["retry_attempts"]) + max(0, attempt - 1)
        latencies = bucket.setdefault("_latencies", [])
        assert isinstance(latencies, list)
        latency = int(getattr(record, "latency_ms", 0) or 0)
        latencies.append(latency)
        bucket["latency_ms_total"] = int(bucket["latency_ms_total"]) + latency
        for field in ("input_tokens", "output_tokens", "total_tokens"):
            bucket[field] = int(bucket[field]) + int(getattr(record, field, 0) or 0)
        bucket["estimated_cost"] = float(bucket["estimated_cost"]) + float(getattr(record, "estimated_cost", 0.0) or 0.0)
        if any(getattr(record, field, None) is not None for field in ("input_tokens", "output_tokens", "total_tokens")):
            bucket["_token_value_count"] = int(bucket.get("_token_value_count", 0)) + 1
        if getattr(record, "estimated_cost", None) is not None:
            bucket["_cost_value_count"] = int(bucket.get("_cost_value_count", 0)) + 1
        if getattr(record, "fallback_from", None):
            bucket["fallback_count"] = int(bucket["fallback_count"]) + 1
        if key[2] in {"circuit_open", "circuit_blocked"} or getattr(record, "error_code", None) == "circuit_open":
            bucket["circuit_open_blocks"] = int(bucket["circuit_open_blocks"]) + 1
    summaries: list[dict[str, object]] = []
    for bucket in buckets.values():
        latencies = sorted(bucket.pop("_latencies", []))
        has_evidence_hashes = False
        for field in _EVIDENCE_HASH_FIELDS:
            values = bucket.pop(f"_{field}_values", set())
            if values:
                has_evidence_hashes = True
                sorted_values = sorted(values)
                bucket[field] = sorted_values[0] if len(sorted_values) == 1 else None
                bucket[f"{field}_value_count"] = len(sorted_values)
        token_value_count = int(bucket.pop("_token_value_count", 0))
        cost_value_count = int(bucket.pop("_cost_value_count", 0))
        if has_evidence_hashes:
            bucket["token_value_count"] = token_value_count
            bucket["cost_value_count"] = cost_value_count
        if latencies:
            index = min(len(latencies) - 1, int(0.95 * (len(latencies) - 1)))
            bucket["latency_ms_p95"] = latencies[index]
            bucket["latency_ms_avg"] = round(int(bucket["latency_ms_total"]) / len(latencies), 2)
        summaries.append(bucket)
    return sorted(summaries, key=lambda item: (str(item["provider"]), str(item["operation"]), str(item["status"])))


__all__ = ["ProviderCallLogCreate", "ProviderCallLogRepository", "summarize_provider_call_records"]
