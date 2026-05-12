"""Generate `.apkg` artifacts from frozen export-card rows."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

import genanki

from multilang.domain.exporting import ExportCardRow, export_field_names_for_source_type
from multilang.domain.source_profiles import get_source_profile
from multilang.services.card_template_loader import load_card_template

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


def build_multilang_model(*, source_type: str = "frequency") -> genanki.Model:
    profile = get_source_profile(source_type)
    try:
        template = load_card_template(source_type=profile.source_type)
    except ValueError as exc:
        raise ExportAnkiPackageError(str(exc)) from exc
    model_id = {
        "frequency": MODEL_ID,
        "word-list": MANUAL_MODEL_ID,
        "kindle-highlights": HIGHLIGHT_MODEL_ID,
    }[profile.source_type]
    return genanki.Model(
        model_id,
        profile.note_type_name,
        fields=[{"name": field_name} for field_name in export_field_names_for_source_type(source_type)],
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
    field_names = export_field_names_for_source_type(row.identity.source_type)
    note = MultilangNote(
        model=model or build_multilang_model(source_type=row.identity.source_type),
        fields=_row_fields(row, field_names=field_names),
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
    model = build_multilang_model(source_type=source_type)
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
