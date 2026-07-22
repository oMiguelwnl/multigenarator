"""Typed export contracts for the frozen Phase 5 card boundary."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from enum import Enum
from hashlib import sha256
import re
import unicodedata

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
JAPANESE_EXPORT_CARD_FIELD_NAMES = (
    "SortIndex",
    "Target Word",
    "Word Reading",
    "Definition",
    "Sentence",
    "Sentence Furigana",
    "Sentence Translation",
    "word_audio",
    "sentence_audio",
    "Image",
)
MANDARIN_EXPORT_CARD_FIELD_NAMES = (
    "SortIndex",
    "word",
    "Pinyin",
    "Traditional",
    "Definitions",
    "Example Sentence",
    "Sentence Pinyin",
    "Traditional Sentence",
    "Translation",
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
    word_reading: str | None = Field(default=None, alias="Word Reading")
    sentence_furigana: str | None = Field(default=None, alias="Sentence Furigana")
    mandarin_word_pinyin: str | None = Field(default=None, alias="Pinyin")
    mandarin_word_traditional: str | None = Field(default=None, alias="Traditional")
    mandarin_sentence_pinyin: str | None = Field(default=None, alias="Sentence Pinyin")
    mandarin_sentence_traditional: str | None = Field(default=None, alias="Traditional Sentence")
    # Grammatical analysis for the dynamic Latin card path. When present it feeds
    # the exported "Grammar" field; absent, that field falls back to Definition.
    gramatica: str | None = Field(default=None, alias="gramatica")

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
        if _uses_mandarin_fields(language=self.identity.language, source_type=self.identity.source_type):
            required_values = {
                "Pinyin": self.mandarin_word_pinyin,
                "Traditional": self.mandarin_word_traditional,
                "Sentence Pinyin": self.mandarin_sentence_pinyin,
                "Traditional Sentence": self.mandarin_sentence_traditional,
                "Translation": self.translation,
            }
            missing = [name for name, value in required_values.items() if not str(value or "").strip()]
            if missing:
                raise ValueError(f"Mandarin export rows require non-empty fields: {', '.join(missing)}")
            invalid_pinyin = [
                name
                for name, value in {
                    "Pinyin": self.mandarin_word_pinyin,
                    "Sentence Pinyin": self.mandarin_sentence_pinyin,
                }.items()
                if _contains_non_pinyin_letter(str(value or ""))
            ]
            if invalid_pinyin:
                raise ValueError(
                    "Mandarin export rows require pinyin fields to contain only pinyin text: "
                    f"{', '.join(invalid_pinyin)}"
                )
        return self

    @classmethod
    def field_names(
        cls,
        *,
        source_type: str = "frequency",
        language: SupportedLanguage | str | None = None,
    ) -> tuple[str, ...]:
        if language is None:
            return export_field_names_for_source_type(source_type)
        return export_field_names_for_language_and_source(language=language, source_type=source_type)

    def ordered_field_mapping(self, *, field_names: tuple[str, ...] | None = None) -> dict[str, object]:
        resolved_field_names = field_names or export_field_names_for_language_and_source(
            language=self.identity.language,
            source_type=self.identity.source_type,
        )
        data = self.model_dump(exclude={"identity", "note_guid"})
        sort_index = data.get("sort_index") if data.get("sort_index") is not None else self.identity.sort_index
        values: dict[str, object] = {
            "SortIndex": sort_index,
            "word": data.get("word") or "",
            "Word": data.get("word") or "",
            "IPA": data.get("ipa") or "",
            "Definitions": data.get("definitions") or "",
            "Definition": data.get("definitions") or "",
            "Example Sentence": data.get("example_sentence") or "",
            "Sentence": data.get("example_sentence") or "",
            "Translation": data.get("translation") or "",
            "Sentence Translation": data.get("translation") or "",
            "Target Word": data.get("front_of_card") or data.get("word") or "",
            "Word Reading": data.get("word_reading") or data.get("front_of_card") or data.get("word") or "",
            "Sentence Furigana": data.get("example_sentence") or "",
            "Pinyin": data.get("mandarin_word_pinyin") or "",
            "Traditional": data.get("mandarin_word_traditional") or "",
            "Sentence Pinyin": data.get("mandarin_sentence_pinyin") or "",
            "Traditional Sentence": data.get("mandarin_sentence_traditional") or "",
            "word_audio": data.get("word_audio") or "",
            "sentence_audio": data.get("sentence_audio") or "",
            "Image": data.get("image") or "",
        }
        if data.get("sentence_furigana"):
            values["Sentence Furigana"] = data["sentence_furigana"]
        if "Grammar" in resolved_field_names:
            values["Grammar"] = data.get("gramatica") or values["Definition"]
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


def export_field_names_for_language_and_source(
    *,
    language: SupportedLanguage | str,
    source_type: str,
) -> tuple[str, ...]:
    """Resolve one export schema from both dimensions that determine card shape."""

    language_value = language.value if isinstance(language, SupportedLanguage) else str(language)
    normalized_source_type = get_source_profile(source_type).source_type
    if language_value == SupportedLanguage.LA.value:
        return LATIN_EXPORT_CARD_FIELD_NAMES
    if language_value == SupportedLanguage.ZH.value and normalized_source_type in {"frequency", "word-list"}:
        return MANDARIN_EXPORT_CARD_FIELD_NAMES
    if language_value == SupportedLanguage.JA.value and normalized_source_type == "frequency":
        return JAPANESE_EXPORT_CARD_FIELD_NAMES
    return export_field_names_for_source_type(normalized_source_type)


def export_field_names_for_rows(rows: list[ExportCardRow]) -> tuple[str, ...]:
    source_types = {row.identity.source_type for row in rows}
    if len(source_types) > 1:
        raise ValueError("cannot resolve export field names for mixed source types")
    languages = {getattr(row.identity, "language", None) for row in rows}
    if len(languages) > 1:
        raise ValueError("cannot resolve export field names for mixed languages")
    source_type = next(iter(source_types), "frequency")
    language = next(iter(languages), SupportedLanguage.EN)
    return export_field_names_for_language_and_source(language=language, source_type=source_type)


def _uses_mandarin_fields(*, language: SupportedLanguage | str, source_type: str) -> bool:
    return (
        export_field_names_for_language_and_source(language=language, source_type=source_type)
        == MANDARIN_EXPORT_CARD_FIELD_NAMES
    )


def _contains_non_pinyin_letter(value: str) -> bool:
    return any(
        _is_han(character)
        or _is_kana(character)
        or (unicodedata.category(character).startswith("L") and not _is_latin(character))
        for character in value
    )


def _is_han(character: str) -> bool:
    name = unicodedata.name(character, "")
    return character == "〇" or "CJK UNIFIED IDEOGRAPH" in name or "CJK COMPATIBILITY IDEOGRAPH" in name


def _is_kana(character: str) -> bool:
    name = unicodedata.name(character, "")
    return "HIRAGANA" in name or "KATAKANA" in name


def _is_latin(character: str) -> bool:
    return "LATIN" in unicodedata.name(character, "") and unicodedata.category(character).startswith("L")


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
    "JAPANESE_EXPORT_CARD_FIELD_NAMES",
    "LATIN_EXPORT_CARD_FIELD_NAMES",
    "MANDARIN_EXPORT_CARD_FIELD_NAMES",
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
    "export_field_names_for_language_and_source",
    "export_field_names_for_source_type",
]
