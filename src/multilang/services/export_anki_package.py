"""Generate `.apkg` artifacts from frozen export-card rows."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
import sqlite3
from tempfile import TemporaryDirectory
import zipfile

import genanki

from multilang.domain.exporting import (
    ExportCardRow,
    export_field_names_for_language_and_source,
    validate_korean_frequency_export_rows,
)
from multilang.domain.jobs import SupportedLanguage
from multilang.domain.source_profiles import get_source_profile
from multilang.services.anki_id_registry import AnkiIdKind, assert_anki_id_registry_clean, registry_id
from multilang.services.card_template_loader import load_card_template
from multilang.services.japanese_frequency_deck import JAPANESE_NOTE_TYPE_NAME

MODEL_ID = registry_id(family="core", role="frequency_model", kind=AnkiIdKind.MODEL)
DECK_ID = registry_id(family="core", role="export_deck", kind=AnkiIdKind.DECK)
NOTE_TYPE_NAME = "Multilang::Card"
MANUAL_MODEL_ID = registry_id(family="core", role="manual_model", kind=AnkiIdKind.MODEL)
MANUAL_NOTE_TYPE_NAME = "Multilang::Manual Card"
HIGHLIGHT_MODEL_ID = registry_id(family="core", role="highlight_model", kind=AnkiIdKind.MODEL)
HIGHLIGHT_NOTE_TYPE_NAME = "Multilang::Highlight Card"
MANDARIN_MODEL_ID = registry_id(family="mandarin", role="card_model", kind=AnkiIdKind.MODEL)
MANDARIN_NOTE_TYPE_NAME = "Multilang::Mandarin Card"
_JAPANESE_MODEL_ID = registry_id(family="japanese_frequency", role="model", kind=AnkiIdKind.MODEL)
_LATIN_MODEL_ID = registry_id(family="latin", role="mvp_model", kind=AnkiIdKind.MODEL)
KOREAN_FREQUENCY_MODEL_ID = registry_id(family="korean_frequency", role="model", kind=AnkiIdKind.MODEL)
KOREAN_FREQUENCY_PARENT_DECK_ID = registry_id(family="korean_frequency", role="parent_deck", kind=AnkiIdKind.DECK)
KOREAN_FREQUENCY_LEVEL_DECK_IDS = {
    1: registry_id(family="korean_frequency", role="level_1_deck", kind=AnkiIdKind.DECK),
    2: registry_id(family="korean_frequency", role="level_2_deck", kind=AnkiIdKind.DECK),
    3: registry_id(family="korean_frequency", role="level_3_deck", kind=AnkiIdKind.DECK),
}

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
    is_zh = _is_mandarin(language=language, source_type=source_type)
    is_ko_frequency = _is_korean_frequency(language=language, source_type=source_type)
    fields_for_model = export_field_names_for_language_and_source(
        language=language or SupportedLanguage.EN,
        source_type=source_type,
    )
    return genanki.Model(
        MANDARIN_MODEL_ID
        if is_zh
        else _JAPANESE_MODEL_ID
        if is_ja
        else KOREAN_FREQUENCY_MODEL_ID
        if is_ko_frequency
        else _LATIN_MODEL_ID
        if is_la
        else model_id,
        MANDARIN_NOTE_TYPE_NAME
        if is_zh
        else JAPANESE_NOTE_TYPE_NAME
        if is_ja
        else "Multilang::Classical Latin MVP"
        if is_la
        else profile.note_type_name,
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
    field_names = export_field_names_for_language_and_source(
        language=row.identity.language,
        source_type=row.identity.source_type,
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
    cards_per_level: int = 1000,
    expected_items: int | None = None,
) -> ExportAnkiPackageResult:
    assert_anki_id_registry_clean(production_roots=True)
    source_types = {row.identity.source_type for row in rows}
    if len(source_types) > 1:
        raise ExportAnkiPackageError("cannot export mixed source types in one note model")
    source_type = next(iter(source_types), "frequency")
    languages = {row.identity.language for row in rows}
    if len(languages) > 1:
        raise ExportAnkiPackageError("cannot export mixed languages in one note model")
    language = next(iter(languages), None)
    model = build_multilang_model(source_type=source_type, language=language)
    is_korean_frequency = _is_korean_frequency(language=language, source_type=source_type)
    if is_korean_frequency:
        gate_result = validate_korean_frequency_export_rows(
            rows,
            cards_per_level=cards_per_level,
            expected_items=expected_items,
        )
        if not gate_result.passed:
            raise ExportAnkiPackageError(f"Korean frequency export gate failed: {gate_result.message()}")
    media_files = _resolve_media_files(rows=rows, media_index=media_index)

    if is_korean_frequency:
        package_decks, expected_decks = _build_korean_frequency_decks(deck_name)
        child_decks = {level: deck for level, deck in package_decks[1:]}
        for row in sorted(rows, key=lambda item: (item.sort_index or 0, item.identity.item_key)):
            assert row.frequency_level is not None
            child_decks[row.frequency_level].add_note(build_multilang_note(row, model=model))
        package: genanki.Package = genanki.Package([deck for _, deck in package_decks])
    else:
        deck = genanki.Deck(DECK_ID, deck_name)
        for row in rows:
            deck.add_note(build_multilang_note(row, model=model))
        expected_decks = {DECK_ID: deck_name}
        package = genanki.Package(deck)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    package.media_files = [str(path) for path in media_files]
    _write_validated_package(
        package=package,
        output_path=output_path,
        rows=rows,
        media_files=media_files,
        expected_decks=expected_decks,
        expected_model_id=model.model_id,
        expected_model_name=model.name,
    )

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
    if row.frequency_level is not None:
        return row.frequency_level
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
        field_names = export_field_names_for_language_and_source(
            language=row.identity.language,
            source_type=row.identity.source_type,
        )
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


def _is_mandarin(*, language: SupportedLanguage | str | None, source_type: str) -> bool:
    value = language.value if hasattr(language, "value") else language
    return source_type in {"frequency", "word-list"} and value == "zh"


def _is_korean_frequency(*, language: SupportedLanguage | str | None, source_type: str) -> bool:
    value = language.value if hasattr(language, "value") else language
    return source_type == "frequency" and value == "ko"


def _build_korean_frequency_decks(deck_name: str) -> tuple[list[tuple[int, genanki.Deck]], dict[int, str]]:
    parent = genanki.Deck(KOREAN_FREQUENCY_PARENT_DECK_ID, deck_name)
    level_names = {level: f"{deck_name}::Level {level}" for level in (1, 2, 3)}
    children = [
        (level, genanki.Deck(KOREAN_FREQUENCY_LEVEL_DECK_IDS[level], level_names[level]))
        for level in (1, 2, 3)
    ]
    expected_decks = {
        KOREAN_FREQUENCY_PARENT_DECK_ID: deck_name,
        **{KOREAN_FREQUENCY_LEVEL_DECK_IDS[level]: name for level, name in level_names.items()},
    }
    return [(0, parent), *children], expected_decks


def _write_validated_package(
    *,
    package: genanki.Package,
    output_path: Path,
    rows: list[ExportCardRow],
    media_files: list[Path],
    expected_decks: dict[int, str],
    expected_model_id: int,
    expected_model_name: str,
) -> None:
    temp_path = output_path.with_name(f".{output_path.name}.tmp")
    if temp_path.exists():
        temp_path.unlink()
    try:
        package.write_to_file(str(temp_path))
        _inspect_staged_package(
            temp_path,
            rows=rows,
            media_files=media_files,
            expected_decks=expected_decks,
            expected_model_id=expected_model_id,
            expected_model_name=expected_model_name,
        )
        temp_path.replace(output_path)
    except Exception:
        if temp_path.exists():
            temp_path.unlink()
        raise


def _inspect_staged_package(
    package_path: Path,
    *,
    rows: list[ExportCardRow],
    media_files: list[Path],
    expected_decks: dict[int, str],
    expected_model_id: int,
    expected_model_name: str,
) -> None:
    try:
        with zipfile.ZipFile(package_path) as archive:
            media_manifest = json.loads(archive.read("media").decode("utf-8"))
            if sorted(media_manifest.values()) != sorted(path.name for path in media_files):
                raise ExportAnkiPackageError("staged package media manifest drift")
            collection_bytes = archive.read("collection.anki2")
    except (OSError, KeyError, zipfile.BadZipFile, json.JSONDecodeError) as exc:
        raise ExportAnkiPackageError(f"unable to inspect staged package: {exc}") from exc

    with TemporaryDirectory() as directory:
        collection_path = Path(directory) / "collection.anki2"
        collection_path.write_bytes(collection_bytes)
        with sqlite3.connect(collection_path) as connection:
            row = connection.execute("select models, decks from col").fetchone()
            if row is None:
                raise ExportAnkiPackageError("staged package collection is missing metadata")
            models = json.loads(row[0])
            decks = json.loads(row[1])
            note_rows = connection.execute(
                "select cards.did, notes.guid, notes.flds, notes.mid "
                "from cards join notes on notes.id = cards.nid"
            ).fetchall()
    model = models.get(str(expected_model_id))
    if model is None or model.get("name") != expected_model_name:
        raise ExportAnkiPackageError("staged package model identity drift")
    field_names = export_field_names_for_language_and_source(
        language=rows[0].identity.language if rows else SupportedLanguage.EN,
        source_type=rows[0].identity.source_type if rows else "frequency",
    )
    if tuple(field["name"] for field in model.get("flds", [])) != field_names:
        raise ExportAnkiPackageError("staged package model field drift")
    for deck_id, deck_name in expected_decks.items():
        deck = decks.get(str(deck_id))
        if deck is None or deck.get("name") != deck_name:
            raise ExportAnkiPackageError("staged package deck identity drift")
    expected_fields = {
        row.note_guid: "\x1f".join(_row_fields(row, field_names=field_names))
        for row in rows
    }
    expected_deck_by_guid = {
        row.note_guid: (
            KOREAN_FREQUENCY_LEVEL_DECK_IDS[row.frequency_level]
            if _is_korean_frequency(language=row.identity.language, source_type=row.identity.source_type)
            and row.frequency_level is not None
            else next(iter(expected_decks))
        )
        for row in rows
    }
    if len(note_rows) != len(rows):
        raise ExportAnkiPackageError("staged package card count drift")
    for deck_id, guid, fields, model_id in note_rows:
        if model_id != expected_model_id:
            raise ExportAnkiPackageError("staged package note model drift")
        if expected_fields.get(guid) != fields:
            raise ExportAnkiPackageError("staged package note field drift")
        if expected_deck_by_guid.get(guid) != deck_id:
            raise ExportAnkiPackageError("staged package card routing drift")


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
    "MANDARIN_MODEL_ID",
    "MANDARIN_NOTE_TYPE_NAME",
    "NOTE_TYPE_NAME",
    "ExportAnkiPackageError",
    "ExportAnkiPackageResult",
    "build_multilang_model",
    "build_multilang_note",
    "export_anki_package",
]
