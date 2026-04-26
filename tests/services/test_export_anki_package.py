"""Tests for genanki-backed `.apkg` export packaging."""

from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from multilang.domain.exporting import ExportCardIdentity, ExportCardRow
from multilang.domain.jobs import SupportedLanguage
from multilang.services.export_anki_package import (
    DECK_ID,
    MODEL_ID,
    ExportAnkiPackageError,
    build_multilang_model,
    build_multilang_note,
    export_anki_package,
)


def write_media_file(path: Path, payload: bytes = b"ID3-audio") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return path


def make_row(
    *,
    item_key: str,
    sort_index: int,
    translation: str = "Eu corro.",
    example_sentence: str = "I run every day.",
    word_audio: str = "[sound:run-word.mp3]",
    sentence_audio: str = "[sound:run-sentence.mp3]",
) -> ExportCardRow:
    return ExportCardRow(
        identity=ExportCardIdentity(
            language=SupportedLanguage.EN,
            source_type="word-list",
            job_id="job-1",
            item_key=item_key,
            lemma_key=f"en:{item_key}",
            sort_index=sort_index,
        ),
        word=item_key,
        front_of_card=item_key,
        ipa=f"/{item_key}/",
        definitions="to move fast<br>to operate",
        example_sentence=example_sentence,
        translation=translation,
        word_audio=word_audio,
        sentence_audio=sentence_audio,
    )


def test_build_multilang_model_uses_exact_fields_and_hides_translation_on_front() -> None:
    model = build_multilang_model()

    assert MODEL_ID > 0
    assert DECK_ID > 0
    assert [field["name"] for field in model.fields] == [
        "SortIndex",
        "word",
        "Front of Card",
        "IPA",
        "Definitions",
        "Example Sentence",
        "Translation",
        "word_audio",
        "sentence_audio",
        "Image",
    ]
    assert "Translation" not in model.templates[0]["qfmt"]
    assert "{{Translation}}" in model.templates[0]["afmt"]
    assert "{{FrontSide}}" in model.templates[0]["afmt"]


def test_build_multilang_note_reuses_deterministic_guid_across_mutable_content_changes() -> None:
    original = build_multilang_note(make_row(item_key="run", sort_index=1))
    changed = build_multilang_note(
        make_row(
            item_key="run",
            sort_index=1,
            translation="Agora eu corro depois.",
            example_sentence="I run later now.",
            word_audio="[sound:run-word-v2.mp3]",
            sentence_audio="[sound:run-sentence-v2.mp3]",
        )
    )

    assert original.guid == changed.guid
    assert original.fields[6] != changed.fields[6]


def test_export_anki_package_bundles_referenced_media_and_sound_basenames(tmp_path: Path) -> None:
    word_media = write_media_file(tmp_path / "audio" / "run-word.mp3")
    sentence_media = write_media_file(tmp_path / "audio" / "run-sentence.mp3")
    row = make_row(item_key="run", sort_index=1)
    output_path = tmp_path / "deck.apkg"

    result = export_anki_package(
        rows=[row],
        media_index={
            row.word_audio: word_media,
            row.sentence_audio: sentence_media,
        },
        output_path=output_path,
        deck_name="English::Level 1",
    )

    assert result.output_path == output_path
    assert result.card_count == 1
    assert result.media_files == [word_media, sentence_media]
    assert output_path.exists()
    with zipfile.ZipFile(output_path) as archive:
        assert "collection.anki2" in archive.namelist()
        assert any(name.isdigit() for name in archive.namelist())


def test_export_anki_package_rejects_missing_media_before_writing(tmp_path: Path) -> None:
    row = make_row(item_key="run", sort_index=1)
    missing_media = tmp_path / "missing" / "run-word.mp3"

    with pytest.raises(ExportAnkiPackageError, match="missing media file"):
        export_anki_package(
            rows=[row],
            media_index={
                row.word_audio: missing_media,
                row.sentence_audio: write_media_file(tmp_path / "audio" / "run-sentence.mp3"),
            },
            output_path=tmp_path / "deck.apkg",
            deck_name="English::Level 1",
        )
