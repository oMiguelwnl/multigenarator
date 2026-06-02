"""Offline review-gate contracts for curated Classical Latin MVP records."""

from __future__ import annotations

from collections import Counter
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


LatinReviewStatus = Literal["needs_review", "approved", "rejected"]
LatinReviewGateName = Literal["source", "translation", "grammar", "audio"]

_GATE_FIELDS: tuple[tuple[str, LatinReviewGateName], ...] = (
    ("source_gate", "source"),
    ("translation_gate", "translation"),
    ("grammar_gate", "grammar"),
    ("audio_gate", "audio"),
)


def _not_blank(value: str) -> str:
    stripped = value.strip()
    if not stripped:
        raise ValueError("required text field must not be blank")
    return stripped


def _strip_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    return _not_blank(value)


class LatinReviewGate(BaseModel):
    """One independent review gate for a Latin curated record."""

    status: LatinReviewStatus
    reason: str | None = None
    reviewed_by: str | None = None
    reviewed_at: str | None = None

    _strip_optional_text_fields = field_validator("reason", "reviewed_by", "reviewed_at")(_strip_optional_text)

    @model_validator(mode="after")
    def require_reason_for_blocking_status(self) -> "LatinReviewGate":
        if self.status in {"needs_review", "rejected"} and self.reason is None:
            raise ValueError("needs_review and rejected gates require a reason")
        return self


class LatinCuratedRecord(BaseModel):
    """Reviewable Latin MVP record with copied source/frequency provenance."""

    item_key: str = Field(min_length=1)
    sequence: int = Field(ge=1)
    lemma: str = Field(min_length=1)
    target_form: str = Field(min_length=1)
    latin_sentence: str = Field(min_length=1)
    source_pack_version: Literal["latin-mvp-50-v1"]
    frequency_rank: int = Field(ge=1)
    frequency_source: str = Field(min_length=1)
    source_type: Literal["original_classical", "adapted_didactic", "reference_example"]
    citation: str = Field(min_length=1)
    work_reference: str = Field(min_length=1)
    source_url_or_id: str = Field(min_length=1)
    license_note: str = Field(min_length=1)
    replacement_reason: str | None = None
    uncertainty_reason: str | None = None
    source_gate: LatinReviewGate
    translation_gate: LatinReviewGate
    grammar_gate: LatinReviewGate
    audio_gate: LatinReviewGate

    _strip_text = field_validator(
        "item_key",
        "lemma",
        "target_form",
        "latin_sentence",
        "frequency_source",
        "citation",
        "work_reference",
        "source_url_or_id",
        "license_note",
    )(_not_blank)
    _strip_optional_text_fields = field_validator("replacement_reason", "uncertainty_reason")(_strip_optional_text)


class LatinReviewSummary(BaseModel):
    """Aggregate review-readiness counts for Latin curated records."""

    total_records: int
    learner_ready_records: int
    blocked_records: int
    gate_counts: dict[str, dict[str, int]]
    blocking_gates_by_item_key: dict[str, list[str]]


def _blocking_gate_names(record: LatinCuratedRecord) -> list[str]:
    return [gate_name for field_name, gate_name in _GATE_FIELDS if getattr(record, field_name).status != "approved"]


def summarize_latin_review_records(records: list[LatinCuratedRecord]) -> LatinReviewSummary:
    """Summarize learner-ready and per-gate status counts for curated records."""

    gate_counts: dict[str, dict[str, int]] = {}
    for field_name, gate_name in _GATE_FIELDS:
        counter = Counter(getattr(record, field_name).status for record in records)
        gate_counts[gate_name] = {status: counter.get(status, 0) for status in LatinReviewStatus.__args__}

    blocking_gates_by_item_key = {
        record.item_key: blockers for record in records if (blockers := _blocking_gate_names(record))
    }
    learner_ready_records = len(records) - len(blocking_gates_by_item_key)
    return LatinReviewSummary(
        total_records=len(records),
        learner_ready_records=learner_ready_records,
        blocked_records=len(blocking_gates_by_item_key),
        gate_counts=gate_counts,
        blocking_gates_by_item_key=blocking_gates_by_item_key,
    )


def assert_latin_records_export_ready(records: list[LatinCuratedRecord]) -> None:
    """Fail closed unless every required Latin review gate is approved."""

    summary = summarize_latin_review_records(records)
    if not summary.blocking_gates_by_item_key:
        return

    blockers = [
        f"latin_export_blocked item_key={item_key} gates={','.join(gates)}"
        for item_key, gates in summary.blocking_gates_by_item_key.items()
    ]
    raise ValueError("; ".join(blockers))


__all__ = [
    "LatinReviewStatus",
    "LatinReviewGateName",
    "LatinReviewGate",
    "LatinCuratedRecord",
    "LatinReviewSummary",
    "summarize_latin_review_records",
    "assert_latin_records_export_ready",
]
