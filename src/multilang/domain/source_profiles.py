"""Explicit source-mode profiles for generation and export boundaries."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

SourceType = Literal["frequency", "word-list", "kindle-highlights", "latin-mvp"]


@dataclass(frozen=True, slots=True)
class SourceProfile:
    source_type: SourceType
    requires_translation_validation: bool
    exports_translation_field: bool
    min_sentence_tokens: int
    max_sentence_tokens: int
    note_type_name: str
    template_name: str


SOURCE_PROFILES: dict[SourceType, SourceProfile] = {
    "frequency": SourceProfile(
        source_type="frequency",
        requires_translation_validation=True,
        exports_translation_field=True,
        min_sentence_tokens=4,
        max_sentence_tokens=12,
        note_type_name="Multilang::Card",
        template_name="normal_card",
    ),
    "word-list": SourceProfile(
        source_type="word-list",
        requires_translation_validation=True,
        exports_translation_field=False,
        min_sentence_tokens=4,
        max_sentence_tokens=12,
        note_type_name="Multilang::Manual Card",
        template_name="highlight_card",
    ),
    "kindle-highlights": SourceProfile(
        source_type="kindle-highlights",
        requires_translation_validation=False,
        exports_translation_field=False,
        min_sentence_tokens=6,
        max_sentence_tokens=16,
        note_type_name="Multilang::Highlight Card",
        template_name="highlight_card",
    ),
    "latin-mvp": SourceProfile(
        source_type="latin-mvp",
        requires_translation_validation=False,
        exports_translation_field=False,
        min_sentence_tokens=3,
        max_sentence_tokens=20,
        note_type_name="Multilang::Latin MVP Card",
        template_name="latin_mvp_card",
    ),  # LEGACY: frozen data path. For new Latin decks without frozen assets, use --language la --source word-list (dynamic generation with Definition field)
}

SUPPORTED_SOURCE_TYPES: tuple[SourceType, ...] = tuple(SOURCE_PROFILES.keys())


def get_source_profile(source_type: str) -> SourceProfile:
    try:
        return SOURCE_PROFILES[source_type]  # type: ignore[index]
    except KeyError as exc:
        raise ValueError(
            "unsupported source_type; expected one of: "
            + ", ".join(SUPPORTED_SOURCE_TYPES)
        ) from exc


__all__ = [
    "SOURCE_PROFILES",
    "SUPPORTED_SOURCE_TYPES",
    "SourceProfile",
    "SourceType",
    "get_source_profile",
]
