"""Typed export contracts for the frozen Phase 5 card boundary."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from enum import Enum
from hashlib import sha256
import re

from pydantic import BaseModel, ConfigDict, Field, model_validator

from multilang.domain.jobs import SupportedLanguage
from multilang.domain.source_profiles import get_source_profile

FREQUENCY_EXPORT_CARD_FIELD_NAMES = (
    "SortIndex",
    "word",
    "IPA",
    "Definitions",
    "Example Sentence",
    "Translation",
    "word_audio",
    "sentence_audio",
    "Image",
)
LATIN_EXPORT_CARD_FIELD_NAMES = (
    "SortIndex",
    "Word",
    "Definition",
    "Sentence",
    "Sentence Translation",
    "Grammar",
    "word_audio",
    "sentence_audio",
    "Image",
)
HIGHLIGHT_EXPORT_CARD_FIELD_NAMES = (
    "SortIndex",
    "Word",
    "IPA",
    "Example Sentence",
    "sentence_audio",
    "Definition",
    "Image",
)
MANUAL_EXPORT_CARD_FIELD_NAMES = HIGHLIGHT_EXPORT_CARD_FIELD_NAMES
EXPORT_CARD_FIELD_NAMES = FREQUENCY_EXPORT_CARD_FIELD_NAMES


class ExportArtifactFormat(str, Enum):
    APKG = "apkg"
    CSV = "csv"
    TSV = "tsv"


class ExportArtifactStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    COMPLETED_WITH_WARNINGS = "completed_with_warnings"
    PARTIAL = "partial"
    BLOCKED = "blocked"
    FAILED = "failed"


class ExportCardIdentity(BaseModel):
    language: SupportedLanguage
    source_type: str = Field(min_length=1)
    job_id: str = Field(min_length=1)
    item_key: str = Field(min_length=1)
    lemma_key: str = Field(min_length=1)
    sort_index: int = Field(ge=0)

    def stable_guid_input(self) -> str:
        return "|".join(
            (
                self.language.value,
                self.source_type,
                self.job_id,
                self.item_key,
                self.lemma_key,
                str(self.sort_index),
            )
        )


def build_export_note_guid(identity: ExportCardIdentity) -> str:
    return sha256(identity.stable_guid_input().encode("utf-8")).hexdigest()[:32]


class ExportCardRow(BaseModel):
    model_config = ConfigDict(populate_by_name=True, frozen=True)

    identity: ExportCardIdentity
    note_guid: str | None = None
    sort_index: int | None = Field(default=None, alias="SortIndex")
    word: str = Field(min_length=1, alias="word")
    front_of_card: str = Field(min_length=1, alias="Front of Card")
    ipa: str | None = Field(default=None, alias="IPA")
    definitions: str = Field(min_length=1, alias="Definitions")
    example_sentence: str = Field(min_length=1, alias="Example Sentence")
    translation: str = Field(default="", alias="Translation")
    word_audio: str = Field(default="", alias="word_audio")
    sentence_audio: str = Field(default="", alias="sentence_audio")
    image: str = Field(default="", alias="Image")

    @model_validator(mode="after")
    def populate_stable_fields(self) -> "ExportCardRow":
        if self.sort_index is None:
            object.__setattr__(self, "sort_index", self.identity.sort_index)
        elif self.sort_index != self.identity.sort_index:
            raise ValueError("SortIndex must match identity.sort_index")
        if self.note_guid is None:
            object.__setattr__(self, "note_guid", build_export_note_guid(self.identity))
        if self.image != "":
            raise ValueError("Image must default to an empty string for export rows")
        return self

    @classmethod
    def field_names(cls, *, source_type: str = "frequency") -> tuple[str, ...]:
        return export_field_names_for_source_type(source_type)

    def ordered_field_mapping(self, *, field_names: tuple[str, ...] | None = None) -> dict[str, object]:
        resolved_field_names = field_names or export_field_names_for_source_type(self.identity.source_type)
        # Use non-alias for python attrs, then map to export names
        data = self.model_dump(exclude={"identity", "note_guid"})
        values: dict[str, object] = {}
        values["Word"] = data.get("word") or data.get("Word") or ""
        values["Definition"] = data.get("definitions") or data.get("Definitions") or data.get("definition") or ""
        # For Latin dynamic (la), provide Grammar (fallback to Definition if no gramatica)
        if "Grammar" in resolved_field_names:
            values["Grammar"] = data.get("gramatica") or data.get("Grammar") or data.get("definitions") or data.get("Definitions") or ""
        # Map sentence from normal attrs (example_sentence -> Sentence)
        if "Sentence" in resolved_field_names:
            values["Sentence"] = data.get("example_sentence") or data.get("Sentence") or ""
        if "Sentence Translation" in resolved_field_names:
            values["Sentence Translation"] = data.get("translation") or data.get("Translation") or data.get("sentence_translation") or ""
        # Also carry audio/image if present in data
        for k in ("word_audio", "sentence_audio", "Image", "SortIndex"):
            if k in data:
                values[k] = data[k]
        return {field_name: values.get(field_name, "") for field_name in resolved_field_names}


def export_field_names_for_source_type(source_type: str) -> tuple[str, ...]:
    profile = get_source_profile(source_type)
    if profile.source_type == "latin-mvp":
        return LATIN_EXPORT_CARD_FIELD_NAMES
    if not profile.exports_translation_field:
        return HIGHLIGHT_EXPORT_CARD_FIELD_NAMES
    if profile.source_type == "word-list":
        return MANUAL_EXPORT_CARD_FIELD_NAMES
    return FREQUENCY_EXPORT_CARD_FIELD_NAMES


def export_field_names_for_rows(rows: list[ExportCardRow]) -> tuple[str, ...]:
    source_types = {row.identity.source_type for row in rows}
    if len(source_types) > 1:
        raise ValueError("cannot resolve export field names for mixed source types")
    source_type = next(iter(source_types), "frequency")
    # Dynamic Latin (any source_type with la) uses the Latin field set (includes Definition + Grammar)
    # to support the dedicated template. This allows dropping frozen data while keeping Latin style.
    languages = {getattr(row.identity, "language", None) for row in rows}
    has_la = any(
        (lang.value if hasattr(lang, "value") else lang) == "la" for lang in languages if lang is not None
    )
    if has_la:
        return LATIN_EXPORT_CARD_FIELD_NAMES
    return export_field_names_for_source_type(source_type)


class ExportDeckArtifact(BaseModel):
    job_id: str = Field(min_length=1)
    export_format: ExportArtifactFormat
    deck_name: str = Field(min_length=1)
    output_path: str = Field(min_length=1)
    card_count: int = Field(ge=0)
    status: ExportArtifactStatus


FREQUENCY_LEVELS = (1, 2, 3)
FREQUENCY_CARDS_PER_LEVEL = 1000
FREQUENCY_TOTAL_CARDS = FREQUENCY_CARDS_PER_LEVEL * len(FREQUENCY_LEVELS)
_LEVEL_ITEM_KEY_RE = re.compile(r"level-(?P<level>[1-3])-rank-\d{4}")


@dataclass(frozen=True)
class ExportQualityIssue:
    code: str
    message: str
    blocking: bool = True


@dataclass(frozen=True)
class ExportQualityGateResult:
    passed: bool
    partial: bool
    card_count: int
    level_counts: dict[int, int]
    issues: list[ExportQualityIssue] = field(default_factory=list)
    warnings: list[ExportQualityIssue] = field(default_factory=list)

    def message(self) -> str:
        parts = [issue.message for issue in [*self.issues, *self.warnings]]
        return "; ".join(parts)


def evaluate_export_quality_gate(
    *,
    source_type: str,
    rows: list[ExportCardRow],
    review_required_count: int = 0,
    invalid_translation_count: int = 0,
    missing_audio_count: int = 0,
    non_synthesized_audio_count: int = 0,
    fallback_audio_count: int = 0,
    allow_partial: bool = False,
) -> ExportQualityGateResult:
    """Fail-closed export gate for final frequency decks."""

    level_counts = _frequency_level_counts(rows)
    issues: list[ExportQualityIssue] = []
    warnings: list[ExportQualityIssue] = []

    if source_type == "frequency":
        total_missing = max(0, FREQUENCY_TOTAL_CARDS - len(rows))
        count_messages: list[str] = []
        if len(rows) != FREQUENCY_TOTAL_CARDS:
            count_messages.append(f"frequency deck has {len(rows)}/{FREQUENCY_TOTAL_CARDS} cards")
            if total_missing:
                count_messages.append(f"total missing {total_missing} cards")
        for level in FREQUENCY_LEVELS:
            count = level_counts.get(level, 0)
            if count != FREQUENCY_CARDS_PER_LEVEL:
                missing = max(0, FREQUENCY_CARDS_PER_LEVEL - count)
                if missing:
                    count_messages.append(f"level_{level} missing {missing} cards")
                else:
                    count_messages.append(f"level_{level} has {count}/{FREQUENCY_CARDS_PER_LEVEL} cards")
        if count_messages:
            issue = ExportQualityIssue(code="incomplete_frequency_deck", message=", ".join(count_messages))
            (warnings if allow_partial else issues).append(issue)

    if review_required_count:
        issue = ExportQualityIssue(
            code="review_required_text",
            message=f"review_required text records: {review_required_count}",
        )
        (warnings if allow_partial else issues).append(issue)

    if invalid_translation_count:
        issues.append(
            ExportQualityIssue(
                code="invalid_translations",
                message=f"invalid translations: {invalid_translation_count}",
            )
        )
    if missing_audio_count:
        issues.append(ExportQualityIssue(code="missing_audio", message=f"missing audio references: {missing_audio_count}"))
    if non_synthesized_audio_count:
        issues.append(
            ExportQualityIssue(
                code="non_synthesized_audio",
                message=f"non-synthesized audio assets: {non_synthesized_audio_count}",
            )
        )
    if fallback_audio_count and source_type == "frequency" and len(rows) == FREQUENCY_TOTAL_CARDS:
        issue = ExportQualityIssue(
            code="fallback_audio",
            message=f"audio assets generated with fallback voices/providers: {fallback_audio_count}",
        )
        (warnings if allow_partial else issues).append(issue)

    return ExportQualityGateResult(
        passed=not issues,
        partial=bool(warnings),
        card_count=len(rows),
        level_counts=level_counts,
        issues=issues,
        warnings=warnings,
    )


def _frequency_level_counts(rows: list[ExportCardRow]) -> dict[int, int]:
    counts: Counter[int] = Counter()
    for row in rows:
        level = _level_for_row(row)
        if level is not None:
            counts[level] += 1
    return {level: counts.get(level, 0) for level in FREQUENCY_LEVELS}


def _level_for_row(row: ExportCardRow) -> int | None:
    match = _LEVEL_ITEM_KEY_RE.search(row.identity.item_key)
    if match is not None:
        return int(match.group("level"))
    sort_index = row.sort_index or row.identity.sort_index
    if 1 <= sort_index <= FREQUENCY_TOTAL_CARDS:
        return ((sort_index - 1) // FREQUENCY_CARDS_PER_LEVEL) + 1
    return None


__all__ = [
    "EXPORT_CARD_FIELD_NAMES",
    "FREQUENCY_EXPORT_CARD_FIELD_NAMES",
    "HIGHLIGHT_EXPORT_CARD_FIELD_NAMES",
    "LATIN_EXPORT_CARD_FIELD_NAMES",
    "MANUAL_EXPORT_CARD_FIELD_NAMES",
    "ExportArtifactFormat",
    "ExportArtifactStatus",
    "ExportQualityGateResult",
    "ExportQualityIssue",
    "ExportCardIdentity",
    "ExportCardRow",
    "ExportDeckArtifact",
    "build_export_note_guid",
    "evaluate_export_quality_gate",
    "export_field_names_for_rows",
    "export_field_names_for_source_type",
]
