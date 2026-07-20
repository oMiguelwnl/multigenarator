"""Generate `.apkg` artifacts from frozen export-card rows."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

import genanki

from multilang.domain.exporting import (
    ExportCardRow,
    JAPANESE_EXPORT_CARD_FIELD_NAMES,
    LATIN_EXPORT_CARD_FIELD_NAMES,
    export_field_names_for_source_type,
)
from multilang.domain.jobs import SupportedLanguage
from multilang.domain.source_profiles import get_source_profile
from multilang.services.card_template_loader import load_card_template
from multilang.services.japanese_frequency_deck import JAPANESE_MODEL_ID, JAPANESE_NOTE_TYPE_NAME
from multilang.services.latin_export import LATIN_MODEL_ID

MODEL_ID = 1_602_300_501
DECK_ID = 1_602_300_502
NOTE_TYPE_NAME = "Multilang::Card"
MANUAL_MODEL_ID = 1_602_300_503
MANUAL_NOTE_TYPE_NAME = "Multilang::Manual Card"
HIGHLIGHT_MODEL_ID = 1_602_300_504
HIGHLIGHT_NOTE_TYPE_NAME = "Multilang::Highlight Card"

_SOUND_TAG_RE = re.compile(r"^\[sound:(?P<name>[^\]]+)\]$")


class ExportAnkiPackageError(ValueError):
    """Raised when an `.apkg` cannot be safely written."""


@dataclass(frozen=True)
class ExportAnkiPackageResult:
    output_path: Path
    card_count: int
    media_files: list[Path]


class MultilangNote(genanki.Note):
    @property
    def guid(self) -> str:
        return self._multilang_guid  # type: ignore[attr-defined]


def build_multilang_model(
    *,
    source_type: str = "frequency",
    language: SupportedLanguage | None = None,
) -> genanki.Model:
    profile = get_source_profile(source_type)
    try:
        template = load_card_template(source_type=profile.source_type, language=language)
    except ValueError as exc:
        raise ExportAnkiPackageError(str(exc)) from exc
    model_id = {
        "frequency": MODEL_ID,
        "word-list": MANUAL_MODEL_ID,
        "kindle-highlights": HIGHLIGHT_MODEL_ID,
    }[profile.source_type]
    # For la use Latin fields (Definition + Grammar) even if source_type is not latin-mvp
    # Note: caller passes rows or we decide here; for simplicity if la force
    is_la = language is not None and (language == "la" or getattr(language, "value", None) == "la")
    is_ja = _is_japanese_frequency(language=language, source_type=source_type)
    fields_for_model = (
        JAPANESE_EXPORT_CARD_FIELD_NAMES
        if is_ja
        else LATIN_EXPORT_CARD_FIELD_NAMES
        if is_la
        else export_field_names_for_source_type(source_type)
    )
    return genanki.Model(
        JAPANESE_MODEL_ID if is_ja else LATIN_MODEL_ID if is_la else model_id,
        JAPANESE_NOTE_TYPE_NAME if is_ja else "Multilang::Classical Latin MVP" if is_la else profile.note_type_name,
        fields=[{"name": field_name} for field_name in fields_for_model],
        templates=[
            {
                "name": "Card 1",
                "qfmt": template.front,
                "afmt": template.back,
            }
        ],
        css=template.css,
    )


def build_multilang_note(row: ExportCardRow, *, model: genanki.Model | None = None) -> genanki.Note:
    # For la force latin fields (even dynamic)
    is_la = row.identity.language == "la" or getattr(row.identity.language, "value", None) == "la"
    is_ja = _is_japanese_frequency(language=row.identity.language, source_type=row.identity.source_type)
    field_names = (
        JAPANESE_EXPORT_CARD_FIELD_NAMES
        if is_ja
        else LATIN_EXPORT_CARD_FIELD_NAMES
        if is_la
        else export_field_names_for_source_type(row.identity.source_type)
    )
    note = MultilangNote(
        model=model or build_multilang_model(
            source_type=row.identity.source_type,
            language=row.identity.language,
        ),
        fields=_row_fields(row, field_names=field_names),
        tags=_traceability_tags(row),
    )
    note._multilang_guid = row.note_guid  # type: ignore[attr-defined]
    return note


def export_anki_package(
    *,
    rows: list[ExportCardRow],
    media_index: dict[str, Path],
    output_path: Path,
    deck_name: str,
) -> ExportAnkiPackageResult:
    source_types = {row.identity.source_type for row in rows}
    if len(source_types) > 1:
        raise ExportAnkiPackageError("cannot export mixed source types in one note model")
    source_type = next(iter(source_types), "frequency")
    languages = {row.identity.language for row in rows}
    language = next(iter(languages), None)
    model = build_multilang_model(source_type=source_type, language=language)
    deck = genanki.Deck(DECK_ID, deck_name)
    media_files = _resolve_media_files(rows=rows, media_index=media_index)

    for row in rows:
        deck.add_note(build_multilang_note(row, model=model))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    package = genanki.Package(deck)
    package.media_files = [str(path) for path in media_files]
    package.write_to_file(str(output_path))

    return ExportAnkiPackageResult(
        output_path=output_path,
        card_count=len(rows),
        media_files=media_files,
    )


def _row_fields(row: ExportCardRow, *, field_names: tuple[str, ...]) -> list[str]:
    mapping = row.ordered_field_mapping(field_names=field_names)
    return [str(mapping[field_name]) if mapping[field_name] is not None else "" for field_name in field_names]


def _traceability_tags(row: ExportCardRow) -> list[str]:
    tags = [
        "multilang",
        row.identity.language.value,
        row.identity.source_type.replace("-", "_"),
        f"job_{_tag_slug(row.identity.job_id)}",
        f"item_{_tag_slug(row.identity.item_key)}",
    ]
    level = _frequency_level(row)
    if level is not None:
        tags.append(f"level_{level}")
    if row.identity.source_type == "frequency" and row.sort_index is not None:
        tags.append(f"rank_{row.sort_index:04d}")
    return list(dict.fromkeys(tags))


def _frequency_level(row: ExportCardRow) -> int | None:
    if row.identity.source_type != "frequency":
        return None
    rank = row.sort_index or row.identity.sort_index
    if 1 <= rank <= 3000:
        return ((rank - 1) // 1000) + 1
    return None


def _tag_slug(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9_]+", "_", value.strip())
    return slug.strip("_") or "unknown"


def _resolve_media_files(*, rows: list[ExportCardRow], media_index: dict[str, Path]) -> list[Path]:
    sound_tags: list[str] = []
    for row in rows:
        field_names = export_field_names_for_source_type(row.identity.source_type)
        if "word_audio" in field_names:
            sound_tags.append(row.word_audio)
        if "sentence_audio" in field_names:
            sound_tags.append(row.sentence_audio)

    return [
        _require_media_file(sound_tag, media_index=media_index)
        for sound_tag in dict.fromkeys(sound_tags)
    ]


def _is_japanese_frequency(*, language: SupportedLanguage | str | None, source_type: str) -> bool:
    value = language.value if hasattr(language, "value") else language
    return source_type == "frequency" and value == "ja"


def _require_media_file(sound_tag: str, *, media_index: dict[str, Path]) -> Path:
    match = _SOUND_TAG_RE.match(sound_tag)
    if match is None:
        raise ExportAnkiPackageError(f"invalid sound reference: {sound_tag}")
    media_path = media_index.get(sound_tag)
    if media_path is None or not media_path.exists():
        raise ExportAnkiPackageError(f"missing media file for {match.group('name')}")
    if media_path.name != match.group("name"):
        raise ExportAnkiPackageError(f"media basename mismatch for {match.group('name')}")
    return media_path


__all__ = [
    "DECK_ID",
    "HIGHLIGHT_MODEL_ID",
    "HIGHLIGHT_NOTE_TYPE_NAME",
    "MODEL_ID",
    "MANUAL_MODEL_ID",
    "MANUAL_NOTE_TYPE_NAME",
    "NOTE_TYPE_NAME",
    "ExportAnkiPackageError",
    "ExportAnkiPackageResult",
    "build_multilang_model",
    "build_multilang_note",
    "export_anki_package",
]
