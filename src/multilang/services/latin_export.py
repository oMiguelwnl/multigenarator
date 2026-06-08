"""Classical Latin MVP export row contracts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

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


__all__ = [
    "LATIN_DECK_NAME",
    "LATIN_EXPORT_FIELD_NAMES",
    "LATIN_NOTE_TYPE_NAME",
    "LatinExportBundle",
    "LatinExportRow",
    "build_latin_export_rows",
]
