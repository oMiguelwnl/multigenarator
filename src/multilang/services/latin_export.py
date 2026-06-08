"""Classical Latin MVP export row contracts."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import csv
from hashlib import sha256
from io import StringIO
import re
from typing import Callable

import genanki

from multilang.domain.exporting import ExportArtifactFormat
from multilang.services.latin_audio import (
    LatinAudioManifest,
    assert_latin_audio_manifest_export_ready,
    load_latin_audio_manifest,
)
from multilang.services.latin_review import (
    LatinCuratedRecord,
    assert_latin_records_export_ready,
    load_latin_curated_records,
)
from multilang.services.latin_source_pack import LatinMvpSourcePack, load_latin_mvp_source_pack
from multilang.services.latin_translation_quality import (
    LatinPortugueseTranslationPack,
    load_latin_portuguese_translation_pack,
)


LATIN_EXPORT_FIELD_NAMES: tuple[str, ...] = (
    "SortIndex",
    "Latin Word",
    "Latin Sentence",
    "Lemma",
    "Translation",
    "Sentence Translation",
    "Gramatica",
    "Source",
    "word_audio",
    "sentence_audio",
    "Image",
)
LATIN_NOTE_TYPE_NAME = "Multilang::Classical Latin MVP"
LATIN_DECK_NAME = "Multilang::Classical Latin::MVP 50"
LATIN_MODEL_ID = 1_602_300_701
LATIN_DECK_ID = 1_602_300_702
_SOUND_TAG_RE = re.compile(r"^\[sound:(?P<name>[^\]]+)\]$")


@dataclass(frozen=True)
class LatinExportRow:
    """One learner-facing Classical Latin MVP row in stable Anki field order."""

    sort_index: int
    item_key: str
    latin_word: str
    latin_sentence: str
    lemma: str
    translation: str
    sentence_translation: str
    gramatica: str
    source: str
    word_audio: str
    sentence_audio: str
    image: str = ""

    def __post_init__(self) -> None:
        if self.image != "":
            raise ValueError("Image must remain blank for Latin MVP export rows")
        if self.sort_index < 1:
            raise ValueError("sort_index must be positive")
        for field_name in (
            "item_key",
            "latin_word",
            "latin_sentence",
            "lemma",
            "translation",
            "sentence_translation",
            "gramatica",
            "source",
            "word_audio",
            "sentence_audio",
        ):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must not be blank")

    def ordered_field_mapping(self) -> dict[str, object]:
        """Return the Anki-ready mapping in the stable Latin field order."""

        return {
            "SortIndex": self.sort_index,
            "Latin Word": self.latin_word,
            "Latin Sentence": self.latin_sentence,
            "Lemma": self.lemma,
            "Translation": self.translation,
            "Sentence Translation": self.sentence_translation,
            "Gramatica": self.gramatica,
            "Source": self.source,
            "word_audio": self.word_audio,
            "sentence_audio": self.sentence_audio,
            "Image": self.image,
        }


@dataclass(frozen=True)
class LatinExportBundle:
    """Latin export rows plus media references keyed by sound tags."""

    rows: list[LatinExportRow]
    media_index: dict[str, Path]


@dataclass(frozen=True)
class LatinExportArtifactResult:
    """Result for one written Latin MVP export artifact."""

    output_path: Path
    card_count: int
    media_count: int
    note_type_name: str = LATIN_NOTE_TYPE_NAME
    deck_name: str = LATIN_DECK_NAME
    export_status: str = "completed"


def _sound_tag(storage_path: str) -> str:
    basename = Path(storage_path).name
    if not basename or basename in {".", ".."}:
        raise ValueError("Latin audio storage_path must include a public basename")
    return f"[sound:{basename}]"


def _public_source_text(record: LatinCuratedRecord) -> str:
    parts = (
        record.source_type,
        record.citation,
        record.work_reference,
        record.source_url_or_id,
        record.license_note,
    )
    source_text = " | ".join(parts)
    forbidden_fragments = ("..", "C:\\", "c:\\", "/Users/", "/home/", "AZURE_", "OPENAI_", "api_key")
    if any(fragment in source_text for fragment in forbidden_fragments):
        raise ValueError(f"Latin source text contains non-public provenance item_key={record.item_key}")
    return source_text


def _require_exact_item_key_order(
    *,
    expected: list[str],
    actual: list[str],
    label: str,
) -> None:
    if actual != expected:
        raise ValueError(f"Latin export {label} item_key order mismatch")


def build_latin_export_rows(
    *,
    repo_root: Path | None = None,
    source_pack_loader: Callable[[], LatinMvpSourcePack] = load_latin_mvp_source_pack,
    curated_records_loader: Callable[[], list[LatinCuratedRecord]] = load_latin_curated_records,
    translation_pack_loader: Callable[[], LatinPortugueseTranslationPack] = load_latin_portuguese_translation_pack,
    audio_manifest_loader: Callable[[], LatinAudioManifest] = load_latin_audio_manifest,
    records_ready_validator: Callable[[list[LatinCuratedRecord]], None] = assert_latin_records_export_ready,
    audio_ready_validator: Callable[..., None] = assert_latin_audio_manifest_export_ready,
) -> LatinExportBundle:
    """Join approved committed Latin assets into learner-facing export rows."""

    source_pack = source_pack_loader()
    records = curated_records_loader()
    translations = translation_pack_loader()
    audio_manifest = audio_manifest_loader()

    records_ready_validator(records)
    audio_ready_validator(audio_manifest, repo_root=repo_root)

    expected_keys = [entry.item_key for entry in source_pack.entries]
    _require_exact_item_key_order(expected=expected_keys, actual=[record.item_key for record in records], label="curation")
    _require_exact_item_key_order(expected=expected_keys, actual=[entry.item_key for entry in translations.entries], label="translation")
    _require_exact_item_key_order(expected=expected_keys, actual=[pair.item_key for pair in audio_manifest.artifacts], label="audio")

    if translations.source_pack_version != source_pack.source_pack_version:
        raise ValueError("Latin export translation source_pack_version mismatch")
    unapproved_translation_keys = [entry.item_key for entry in translations.entries if entry.review_status != "approved"]
    if unapproved_translation_keys:
        raise ValueError(
            "latin_export_blocked unapproved_translation_entries=" + ",".join(unapproved_translation_keys)
        )

    records_by_key = {record.item_key: record for record in records}
    translations_by_key = {entry.item_key: entry for entry in translations.entries}
    audio_by_key = {pair.item_key: pair for pair in audio_manifest.artifacts}
    rows: list[LatinExportRow] = []
    media_index: dict[str, Path] = {}

    for source_entry in source_pack.entries:
        record = records_by_key[source_entry.item_key]
        translation = translations_by_key[source_entry.item_key]
        audio_pair = audio_by_key[source_entry.item_key]
        if audio_pair.word is None or audio_pair.sentence is None:
            raise ValueError(f"latin_audio_export_blocked item_key={source_entry.item_key} missing audio pair")

        word_audio = _sound_tag(audio_pair.word.storage_path)
        sentence_audio = _sound_tag(audio_pair.sentence.storage_path)
        media_index[word_audio] = Path(audio_pair.word.storage_path)
        media_index[sentence_audio] = Path(audio_pair.sentence.storage_path)
        rows.append(
            LatinExportRow(
                sort_index=source_entry.sequence,
                item_key=source_entry.item_key,
                latin_word=source_entry.target_form,
                latin_sentence=source_entry.latin_sentence,
                lemma=source_entry.lemma,
                translation=translation.short_translation_pt,
                sentence_translation=translation.sentence_translation_pt,
                gramatica=source_entry.gramatica,
                source=_public_source_text(record),
                word_audio=word_audio,
                sentence_audio=sentence_audio,
            )
        )

    return LatinExportBundle(rows=rows, media_index=media_index)


class LatinNote(genanki.Note):
    @property
    def guid(self) -> str:
        return self._latin_guid  # type: ignore[attr-defined]


def build_latin_anki_model() -> genanki.Model:
    """Build the dedicated Classical Latin MVP Anki note model."""

    return genanki.Model(
        LATIN_MODEL_ID,
        LATIN_NOTE_TYPE_NAME,
        fields=[{"name": field_name} for field_name in LATIN_EXPORT_FIELD_NAMES],
        templates=[
            {
                "name": "Latin MVP Card",
                "qfmt": (
                    '<div class="latin-card">'
                    '<div class="latin-word">{{Latin Word}} {{word_audio}}</div>'
                    '<div class="latin-sentence">{{Latin Sentence}} {{sentence_audio}}</div>'
                    '<div class="latin-translation" style="display:none;">{{Sentence Translation}}</div>'
                    "</div>"
                ),
                "afmt": (
                    "{{FrontSide}}"
                    '<hr id="answer">'
                    '<div class="translation">{{Translation}}</div>'
                    '<div class="sentence-translation">{{Sentence Translation}}</div>'
                    '<div class="lemma">Lemma: {{Lemma}}</div>'
                    '<div class="gramatica">Gramatica: {{Gramatica}}</div>'
                    '<div class="source">Source: {{Source}}</div>'
                    "{{Image}}"
                ),
            }
        ],
        css=".latin-card{font-family:serif}.latin-word{font-size:2rem}.source{font-size:.8rem;color:#666}",
    )


def _latin_note_guid(row: LatinExportRow) -> str:
    return sha256(f"la|latin-mvp|{row.item_key}|{row.sort_index}".encode("utf-8")).hexdigest()[:32]


def build_latin_anki_note(row: LatinExportRow, *, model: genanki.Model | None = None) -> genanki.Note:
    note = LatinNote(
        model=model or build_latin_anki_model(),
        fields=[str(row.ordered_field_mapping()[field_name]) for field_name in LATIN_EXPORT_FIELD_NAMES],
        tags=["multilang", "la", "latin_mvp", f"item_{row.item_key.replace('-', '_')}", f"rank_{row.sort_index:04d}"],
    )
    note._latin_guid = _latin_note_guid(row)  # type: ignore[attr-defined]
    return note


def _require_latin_media_file(sound_tag: str, *, media_index: dict[str, Path], repo_root: Path) -> Path:
    match = _SOUND_TAG_RE.match(sound_tag)
    if match is None:
        raise ValueError(f"invalid Latin sound reference: {sound_tag}")
    media_path = media_index.get(sound_tag)
    if media_path is None:
        raise ValueError(f"missing Latin media file for {match.group('name')}")
    resolved = media_path if media_path.is_absolute() else repo_root / media_path
    if not resolved.exists():
        raise ValueError(f"missing Latin media file for {match.group('name')}")
    if resolved.name != match.group("name"):
        raise ValueError(f"Latin media basename mismatch for {match.group('name')}")
    return resolved


def _latin_media_files(bundle: LatinExportBundle, *, repo_root: Path) -> list[Path]:
    sound_tags: list[str] = []
    for row in bundle.rows:
        sound_tags.extend([row.word_audio, row.sentence_audio])
    return [
        _require_latin_media_file(sound_tag, media_index=bundle.media_index, repo_root=repo_root)
        for sound_tag in dict.fromkeys(sound_tags)
    ]


def export_latin_mvp_apkg(
    *,
    bundle: LatinExportBundle,
    output_path: Path,
    deck_name: str = LATIN_DECK_NAME,
    repo_root: Path | None = None,
) -> LatinExportArtifactResult:
    """Write the approved Classical Latin MVP as an APKG with WAV media."""

    root = repo_root or Path.cwd()
    model = build_latin_anki_model()
    deck = genanki.Deck(LATIN_DECK_ID, deck_name)
    media_files = _latin_media_files(bundle, repo_root=root)
    for row in sorted(bundle.rows, key=lambda row: (row.sort_index, row.item_key)):
        deck.add_note(build_latin_anki_note(row, model=model))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    package = genanki.Package(deck)
    package.media_files = [str(path) for path in media_files]
    package.write_to_file(str(output_path))
    return LatinExportArtifactResult(output_path=output_path, card_count=len(bundle.rows), media_count=len(media_files), deck_name=deck_name)


def _serialize_latin_field(value: object) -> str:
    return str(value).replace("\r\n", "<br>").replace("\n", "<br>").replace("\r", "<br>")


def write_latin_tabular_export(
    *,
    bundle: LatinExportBundle,
    export_format: ExportArtifactFormat,
    output_dir: Path,
    deck_name: str = LATIN_DECK_NAME,
) -> LatinExportArtifactResult:
    """Write CSV or TSV Anki import files using the Latin field order."""

    if export_format not in {ExportArtifactFormat.CSV, ExportArtifactFormat.TSV}:
        raise ValueError(f"unsupported Latin tabular export format: {export_format.value}")
    delimiter = "\t" if export_format is ExportArtifactFormat.TSV else ","
    separator_name = "Tab" if export_format is ExportArtifactFormat.TSV else "Comma"
    suffix = ".tsv" if export_format is ExportArtifactFormat.TSV else ".csv"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"latin-mvp-50{suffix}"
    buffer = StringIO()
    writer = csv.writer(buffer, delimiter=delimiter, lineterminator="\n", quoting=csv.QUOTE_MINIMAL)
    buffer.write(f"#separator:{separator_name}\n")
    buffer.write("#html:true\n")
    buffer.write(f"#notetype:{LATIN_NOTE_TYPE_NAME}\n")
    buffer.write(f"#deck:{deck_name}\n")
    buffer.write(f"#columns:{delimiter.join(LATIN_EXPORT_FIELD_NAMES)}\n")
    for row in sorted(bundle.rows, key=lambda row: (row.sort_index, row.item_key)):
        mapping = row.ordered_field_mapping()
        writer.writerow([_serialize_latin_field(mapping[field_name]) for field_name in LATIN_EXPORT_FIELD_NAMES])
    output_path.write_text(buffer.getvalue(), encoding="utf-8")
    return LatinExportArtifactResult(output_path=output_path, card_count=len(bundle.rows), media_count=0, deck_name=deck_name)


def export_latin_mvp_bundle(
    *,
    export_format: ExportArtifactFormat,
    output_dir: Path,
    deck_name: str = LATIN_DECK_NAME,
    repo_root: Path | None = None,
) -> LatinExportArtifactResult:
    """Build approved rows and write one Latin MVP export artifact."""

    root = repo_root or Path.cwd()
    bundle = build_latin_export_rows(repo_root=root)
    if export_format is ExportArtifactFormat.APKG:
        return export_latin_mvp_apkg(
            bundle=bundle,
            output_path=output_dir / "latin-mvp-50.apkg",
            deck_name=deck_name,
            repo_root=root,
        )
    return write_latin_tabular_export(bundle=bundle, export_format=export_format, output_dir=output_dir, deck_name=deck_name)


__all__ = [
    "LATIN_DECK_NAME",
    "LATIN_DECK_ID",
    "LATIN_EXPORT_FIELD_NAMES",
    "LATIN_MODEL_ID",
    "LATIN_NOTE_TYPE_NAME",
    "LatinExportArtifactResult",
    "LatinExportBundle",
    "LatinExportRow",
    "build_latin_anki_model",
    "build_latin_anki_note",
    "build_latin_export_rows",
    "export_latin_mvp_apkg",
    "export_latin_mvp_bundle",
    "write_latin_tabular_export",
]
