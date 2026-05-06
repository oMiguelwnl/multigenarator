"""Tests for genanki-backed `.apkg` export packaging."""

from __future__ import annotations

import zipfile
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
        "Front of Card",
        "IPA",
        "Definitions",
        "Example Sentence",
        "Translation",
        "word_audio",
        "sentence_audio",
        "Image",
    ]
    assert 'id="translation"' in model.templates[0]["qfmt"]
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
    assert 'document.getElementById("translation").style.display = "block";' in model.templates[0]["afmt"]
    assert "--max-width-card: 400px;" in model.css
    assert "--color-nightMode-card-background: #0a1628;" in model.css
    assert ".targetWordContainer" in model.css
    assert "justify-content: space-between;" in model.css
    assert ".wordAudioButtonBack" in model.css
    assert "margin-left: 8px;" in model.css
    assert ".customCard" in model.css


def test_normal_deck_css_does_not_update_russian_phoneme_template() -> None:
    phoneme_deck_source = Path("src/multilang/services/russian_phoneme_deck.py").read_text(encoding="utf-8")

    assert "--max-width-card: 400px;" not in phoneme_deck_source


def test_build_manual_word_list_model_preserves_fixed_translation_field() -> None:
    model = build_multilang_model(source_type="word-list")

    assert MANUAL_MODEL_ID > 0
    assert model.name == MANUAL_NOTE_TYPE_NAME
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
    assert "{{Translation}}" in model.templates[0]["qfmt"]
    assert "translation" in model.templates[0]["afmt"].casefold()


def test_build_highlight_model_uses_dedicated_identity_and_fields() -> None:
    model = build_multilang_model(source_type="kindle-highlights")

    assert HIGHLIGHT_MODEL_ID > 0
    assert model.name == HIGHLIGHT_NOTE_TYPE_NAME
    assert [field["name"] for field in model.fields] == [
        "SortIndex",
        "Word",
        "IPA",
        "word_audio",
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
    assert "highlight-card" in model.templates[0]["qfmt"]
    assert "highlight-definition-answer" in model.templates[0]["afmt"]
    assert "--multilang-blue" in model.css


def test_build_highlight_model_rejects_malformed_template_before_model_return(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "CARD_TEMPLATE.md").write_text(
        Path("CARD_TEMPLATE.md").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (tmp_path / "HIGHLIGHT_CARD_TEMPLATE.md").write_text(
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
    monkeypatch.setattr(card_template_loader, "PROJECT_ROOT", tmp_path)

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
