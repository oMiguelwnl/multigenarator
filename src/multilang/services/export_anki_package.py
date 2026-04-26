"""Generate `.apkg` artifacts from frozen export-card rows."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

import genanki

from multilang.domain.exporting import EXPORT_CARD_FIELD_NAMES, ExportCardRow

MODEL_ID = 1_602_300_501
DECK_ID = 1_602_300_502
NOTE_TYPE_NAME = "Multilang::Card"

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


def build_multilang_model() -> genanki.Model:
    return genanki.Model(
        MODEL_ID,
        NOTE_TYPE_NAME,
        fields=[{"name": field_name} for field_name in EXPORT_CARD_FIELD_NAMES],
        templates=[
            {
                "name": "Card 1",
                "qfmt": "{{Front of Card}}<br>{{IPA}}<br>{{word_audio}}",
                "afmt": "{{FrontSide}}<hr id=\"answer\">{{Definitions}}<br>{{Example Sentence}}<br>{{Translation}}<br>{{sentence_audio}}",
            }
        ],
        css=".card { font-family: arial; font-size: 20px; }",
    )


def build_multilang_note(row: ExportCardRow, *, model: genanki.Model | None = None) -> genanki.Note:
    note = MultilangNote(model=model or build_multilang_model(), fields=_row_fields(row))
    note._multilang_guid = row.note_guid  # type: ignore[attr-defined]
    return note


def export_anki_package(
    *,
    rows: list[ExportCardRow],
    media_index: dict[str, Path],
    output_path: Path,
    deck_name: str,
) -> ExportAnkiPackageResult:
    model = build_multilang_model()
    deck = genanki.Deck(DECK_ID, deck_name)
    media_files: list[Path] = []

    for row in rows:
        deck.add_note(build_multilang_note(row, model=model))
        media_files.extend(_resolve_media_files(row=row, media_index=media_index))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    package = genanki.Package(deck)
    deduped_media = list(dict.fromkeys(media_files))
    package.media_files = [str(path) for path in deduped_media]
    package.write_to_file(str(output_path))

    return ExportAnkiPackageResult(
        output_path=output_path,
        card_count=len(rows),
        media_files=deduped_media,
    )


def _row_fields(row: ExportCardRow) -> list[str]:
    mapping = row.ordered_field_mapping()
    return [str(mapping[field_name]) if mapping[field_name] is not None else "" for field_name in EXPORT_CARD_FIELD_NAMES]


def _resolve_media_files(*, row: ExportCardRow, media_index: dict[str, Path]) -> list[Path]:
    return [
        _require_media_file(row.word_audio, media_index=media_index),
        _require_media_file(row.sentence_audio, media_index=media_index),
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
    "MODEL_ID",
    "NOTE_TYPE_NAME",
    "ExportAnkiPackageError",
    "ExportAnkiPackageResult",
    "build_multilang_model",
    "build_multilang_note",
    "export_anki_package",
]
