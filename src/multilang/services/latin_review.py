"""Offline review-gate contracts for curated Classical Latin MVP records."""

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from multilang.services.latin_source_pack import load_latin_mvp_source_pack


LatinReviewStatus = Literal["needs_review", "approved", "rejected"]
LatinReviewGateName = Literal["source", "translation", "grammar", "audio"]

_GATE_FIELDS: tuple[tuple[str, LatinReviewGateName], ...] = (
    ("source_gate", "source"),
    ("translation_gate", "translation"),
    ("grammar_gate", "grammar"),
    ("audio_gate", "audio"),
)
DEFAULT_LATIN_MVP_CURATION_PATH = Path("data") / "latin_mvp" / "latin-mvp-50-v1-curation.json"
_SOURCE_PROVENANCE_FIELDS: tuple[str, ...] = (
    "item_key",
    "sequence",
    "lemma",
    "target_form",
    "latin_sentence",
    "source_pack_version",
    "frequency_rank",
    "frequency_source",
    "source_type",
    "citation",
    "work_reference",
    "source_url_or_id",
    "license_note",
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


def _validate_against_source_pack(records: list[LatinCuratedRecord], source_pack_path: Path | None) -> None:
    source_pack = load_latin_mvp_source_pack(source_pack_path)
    if len(records) != len(source_pack.entries):
        raise ValueError(
            f"Latin curation asset count mismatch: curated={len(records)} source_pack={len(source_pack.entries)}"
        )

    for index, (record, source_entry) in enumerate(zip(records, source_pack.entries, strict=True), start=1):
        for field_name in _SOURCE_PROVENANCE_FIELDS:
            curated_value = getattr(record, field_name)
            source_value = getattr(source_entry, field_name)
            if curated_value != source_value:
                raise ValueError(
                    "Latin curation asset provenance mismatch "
                    f"index={index} item_key={record.item_key} field={field_name} "
                    f"curated={curated_value!r} source_pack={source_value!r}"
                )


def load_latin_curated_records(
    path: Path | None = None,
    source_pack_path: Path | None = None,
) -> list[LatinCuratedRecord]:
    """Load curated Latin review records and verify source-pack provenance has not drifted."""

    curation_path = path or DEFAULT_LATIN_MVP_CURATION_PATH
    try:
        payload = json.loads(curation_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError("Latin MVP curation asset is missing for latin-mvp-50-v1") from exc
    except json.JSONDecodeError as exc:
        raise ValueError("Latin MVP curation JSON is malformed for latin-mvp-50-v1") from exc

    if not isinstance(payload, list):
        raise ValueError("Latin MVP curation asset must be a JSON array")
    try:
        records = [LatinCuratedRecord.model_validate(item) for item in payload]
    except Exception as exc:
        if exc.__class__.__module__.startswith("pydantic"):
            raise ValueError(f"Latin MVP curation asset failed validation for latin-mvp-50-v1: {exc}") from exc
        raise

    _validate_against_source_pack(records, source_pack_path)
    return records


__all__ = [
    "LatinReviewStatus",
    "LatinReviewGateName",
    "DEFAULT_LATIN_MVP_CURATION_PATH",
    "LatinReviewGate",
    "LatinCuratedRecord",
    "LatinReviewSummary",
    "load_latin_curated_records",
    "summarize_latin_review_records",
    "assert_latin_records_export_ready",
]
