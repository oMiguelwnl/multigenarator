"""Tests for genanki-backed `.apkg` export packaging."""

from __future__ import annotations

import zipfile
import json
import sqlite3
from pathlib import Path

import pytest

from multilang.domain.exporting import ExportCardIdentity, ExportCardRow
from multilang.domain.jobs import SupportedLanguage
from multilang.services import card_template_loader
from multilang.services.export_anki_package import (
    DECK_ID,
    HIGHLIGHT_MODEL_ID,
    HIGHLIGHT_NOTE_TYPE_NAME,
    MANUAL_MODEL_ID,
    MANUAL_NOTE_TYPE_NAME,
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
    source_type: str = "frequency",
) -> ExportCardRow:
    return ExportCardRow(
        identity=ExportCardIdentity(
            language=SupportedLanguage.EN,
            source_type=source_type,
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
        "IPA",
        "Definitions",
        "Example Sentence",
        "Translation",
        "word_audio",
        "sentence_audio",
        "Image",
    ]
    assert 'id="translation"' in model.templates[0]["qfmt"]
    assert "{{word}}" in model.templates[0]["qfmt"]
    assert "{{Front of Card}}" not in model.templates[0]["qfmt"] + model.templates[0]["afmt"]
    assert 'style="display:none;"' in model.templates[0]["qfmt"]
    assert "{{Translation}}" in model.templates[0]["qfmt"]
    assert "document.getElementById(\"translation\").style.display = \"block\";" in model.templates[0]["afmt"]
    assert "{{FrontSide}}" in model.templates[0]["afmt"]


def test_build_multilang_model_uses_project_card_template_sections() -> None:
    model = build_multilang_model()

    assert '<div class="customCard cardBack">' in model.templates[0]["qfmt"]
    assert '<div id="translation" class="sentenceTranslation indent" style="display:none;">' in model.templates[0]["qfmt"]
    assert '<div class="header">Definition:</div>' in model.templates[0]["qfmt"]
    assert 'definitionsList' in model.templates[0]["qfmt"]
    assert model.templates[0]["qfmt"].index('definitionsList') < model.templates[0]["qfmt"].index('{{Image}}')
    assert model.templates[0]["qfmt"].index('{{Image}}') < model.templates[0]["qfmt"].index('<div class="header">example:</div>')
    assert 'document.getElementById("translation").style.display = "block";' in model.templates[0]["afmt"]
    assert "--max-width-card: 400px;" in model.css
    assert "--color-nightMode-card-background: #0a1628;" in model.css
    assert ".targetWordContainer" in model.css
    assert "justify-content: space-between;" in model.css
    assert ".wordAudioButtonBack" in model.css
    assert "margin-left: 8px;" in model.css
    assert ".exampleSentenceLine" in model.css
    assert ".exampleSentenceText" in model.css
    assert ".sentenceAudioButton" in model.css
    assert "min-width: 0;" in model.css
    assert ".customCard" in model.css


def test_build_english_frequency_model_localizes_visual_labels_only() -> None:
    model = build_multilang_model(language=SupportedLanguage.EN)
    qfmt = model.templates[0]["qfmt"]
    spanish_model = build_multilang_model(language=SupportedLanguage.ES)

    assert '<div class="header">Definição:</div>' in qfmt
    assert '<div class="header">Exemplo:</div>' in qfmt
    assert "{{Definitions}}" in qfmt
    assert "{{Translation}}" in qfmt
    assert '<div class="header">Definition:</div>' in spanish_model.templates[0]["qfmt"]
    assert '<div class="header">example:</div>' in spanish_model.templates[0]["qfmt"]


def test_normal_deck_css_does_not_update_russian_phoneme_template() -> None:
    phoneme_deck_source = Path("src/multilang/services/russian_phoneme_deck.py").read_text(encoding="utf-8")

    assert "--max-width-card: 400px;" not in phoneme_deck_source


def test_build_manual_word_list_model_uses_highlight_template_contract() -> None:
    model = build_multilang_model(source_type="word-list")

    assert MANUAL_MODEL_ID > 0
    assert model.name == MANUAL_NOTE_TYPE_NAME
    assert [field["name"] for field in model.fields] == [
        "SortIndex",
        "Word",
        "IPA",
        "Example Sentence",
        "sentence_audio",
        "Definition",
        "Image",
    ]
    assert "{{Translation}}" not in model.templates[0]["qfmt"] + model.templates[0]["afmt"]
    assert "{{Image}}" not in model.templates[0]["qfmt"]
    assert "{{Image}}" in model.templates[0]["afmt"]
    assert model.templates[0]["afmt"].index("{{Definition}}") < model.templates[0]["afmt"].index("{{Image}}")
    assert 'class="card"' in model.templates[0]["qfmt"]
    assert 'class="meaning"' in model.templates[0]["afmt"]


def test_build_highlight_model_uses_dedicated_identity_and_fields() -> None:
    model = build_multilang_model(source_type="kindle-highlights")

    assert HIGHLIGHT_MODEL_ID > 0
    assert model.name == HIGHLIGHT_NOTE_TYPE_NAME
    assert [field["name"] for field in model.fields] == [
        "SortIndex",
        "Word",
        "IPA",
        "Example Sentence",
        "sentence_audio",
        "Definition",
        "Image",
    ]
    template_markup = model.templates[0]["qfmt"] + model.templates[0]["afmt"]
    assert "{{Word}}" in model.templates[0]["qfmt"]
    assert "{{Definition}}" in model.templates[0]["afmt"]
    assert "{{FrontSide}}" in model.templates[0]["afmt"]
    assert "{{Translation}}" not in template_markup
    assert "{{Image}}" not in model.templates[0]["qfmt"]
    assert "{{Image}}" in model.templates[0]["afmt"]
    assert model.templates[0]["afmt"].index("{{Definition}}") < model.templates[0]["afmt"].index("{{Image}}")
    assert 'class="card"' in model.templates[0]["qfmt"]
    assert 'class="meaning"' in model.templates[0]["afmt"]
    assert ".audio-controls" in model.css


def test_build_highlight_model_rejects_malformed_template_before_model_return(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    template_dir = tmp_path / "src" / "multilang" / "templates"
    template_dir.mkdir(parents=True)
    (template_dir / "normal_card.md").write_text(
        Path("src/multilang/templates/normal_card.md").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (template_dir / "highlight_card.md").write_text(
        """
# Bad Highlight Template

## Front Template

```html
{{Word}} {{Dangling Field}}
```

## Back Template

```html
{{FrontSide}} {{Definition}}
```

## Styling (CSS)

```css
.highlight-card { color: blue; }
```
""",
        encoding="utf-8",
    )
    monkeypatch.setattr(card_template_loader, "TEMPLATE_ROOT", template_dir)

    with pytest.raises(ExportAnkiPackageError, match="card template references fields"):
        build_multilang_model(source_type="kindle-highlights")


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


def test_export_anki_package_deduplicates_shared_media_before_packaging(tmp_path: Path) -> None:
    word_media = write_media_file(tmp_path / "audio" / "run-word.mp3")
    sentence_media = write_media_file(tmp_path / "audio" / "run-sentence.mp3")
    first = make_row(item_key="run", sort_index=1)
    second = make_row(
        item_key="walk",
        sort_index=2,
        word_audio=first.word_audio,
        sentence_audio=first.sentence_audio,
    )
    output_path = tmp_path / "deck.apkg"

    result = export_anki_package(
        rows=[first, second],
        media_index={
            first.word_audio: word_media,
            first.sentence_audio: sentence_media,
        },
        output_path=output_path,
        deck_name="English::Level 1",
    )

    assert result.card_count == 2
    assert result.media_files == [word_media, sentence_media]
    with zipfile.ZipFile(output_path) as archive:
        media_manifest = json.loads(archive.read("media").decode("utf-8"))
    assert sorted(media_manifest.values()) == ["run-sentence.mp3", "run-word.mp3"]


def test_export_highlight_anki_package_uses_highlight_model_and_bundles_media(
    tmp_path: Path,
) -> None:
    sentence_media = write_media_file(tmp_path / "audio" / "run-sentence.mp3")
    row = make_row(item_key="run", sort_index=1, source_type="kindle-highlights")
    output_path = tmp_path / "highlight.apkg"

    result = export_anki_package(
        rows=[row],
        media_index={row.sentence_audio: sentence_media},
        output_path=output_path,
        deck_name="English::Highlights",
    )

    assert result.output_path == output_path
    assert result.card_count == 1
    assert result.media_files == [sentence_media]
    with zipfile.ZipFile(output_path) as archive:
        names = archive.namelist()
        assert "collection.anki2" in names
        assert "media" in names
        media_manifest = json.loads(archive.read("media").decode("utf-8"))
        assert sorted(media_manifest.values()) == ["run-sentence.mp3"]
        collection_path = tmp_path / "collection.anki2"
        collection_path.write_bytes(archive.read("collection.anki2"))
    with sqlite3.connect(collection_path) as connection:
        models = json.loads(connection.execute("select models from col").fetchone()[0])
    highlight_model = models[str(HIGHLIGHT_MODEL_ID)]
    assert highlight_model["name"] == HIGHLIGHT_NOTE_TYPE_NAME
    assert [field["name"] for field in highlight_model["flds"]] == [
        "SortIndex",
        "Word",
        "IPA",
        "Example Sentence",
        "sentence_audio",
        "Definition",
        "Image",
    ]


def test_export_anki_package_rejects_missing_media_before_writing(tmp_path: Path) -> None:
    row = make_row(item_key="run", sort_index=1)
    missing_media = tmp_path / "missing" / "run-word.mp3"
    output_path = tmp_path / "deck.apkg"

    with pytest.raises(ExportAnkiPackageError, match="missing media file"):
        export_anki_package(
            rows=[row],
            media_index={
                row.word_audio: missing_media,
                row.sentence_audio: write_media_file(tmp_path / "audio" / "run-sentence.mp3"),
            },
            output_path=output_path,
            deck_name="English::Level 1",
        )
    assert not output_path.exists()


@pytest.mark.parametrize(
    ("sentence_audio", "media_paths", "error"),
    [
        (
            "[sound:run-sentence.mp3]",
            {},
            "missing media file",
        ),
        (
            "run-sentence.mp3",
            {"run-sentence.mp3": "run-sentence.mp3"},
            "invalid sound reference",
        ),
        (
            "[sound:run-sentence.mp3]",
            {
                "[sound:run-sentence.mp3]": "different-sentence.mp3",
            },
            "media basename mismatch",
        ),
    ],
)
def test_export_highlight_package_rejects_broken_media_before_writing(
    tmp_path: Path,
    sentence_audio: str,
    media_paths: dict[str, str],
    error: str,
) -> None:
    row = make_row(
        item_key="run",
        sort_index=1,
        source_type="kindle-highlights",
        sentence_audio=sentence_audio,
    )
    media_index = {
        sound_tag: write_media_file(tmp_path / "audio" / basename)
        for sound_tag, basename in media_paths.items()
    }
    output_path = tmp_path / "broken-highlight.apkg"

    with pytest.raises(ExportAnkiPackageError, match=error):
        export_anki_package(
            rows=[row],
            media_index=media_index,
            output_path=output_path,
            deck_name="English::Highlights",
        )
    assert not output_path.exists()


def test_export_anki_package_rejects_mixed_source_types(tmp_path: Path) -> None:
    frequency = make_row(item_key="run", sort_index=1, source_type="frequency")
    manual = make_row(item_key="walk", sort_index=2, source_type="word-list")

    with pytest.raises(ExportAnkiPackageError, match="cannot export mixed source types in one note model"):
        export_anki_package(
            rows=[frequency, manual],
            media_index={},
            output_path=tmp_path / "mixed.apkg",
            deck_name="Mixed",
        )


@pytest.mark.parametrize("other_source", ["frequency", "word-list"])
def test_export_anki_package_rejects_highlight_mixed_with_existing_modes(
    tmp_path: Path, other_source: str
) -> None:
    highlight = make_row(item_key="run", sort_index=1, source_type="kindle-highlights")
    other = make_row(item_key="walk", sort_index=2, source_type=other_source)
    output_path = tmp_path / "mixed-highlight.apkg"

    with pytest.raises(ExportAnkiPackageError, match="cannot export mixed source types in one note model"):
        export_anki_package(
            rows=[highlight, other],
            media_index={},
            output_path=output_path,
            deck_name="Mixed",
        )
    assert not output_path.exists()
