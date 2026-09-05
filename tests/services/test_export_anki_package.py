"""Tests for genanki-backed `.apkg` export packaging."""

from __future__ import annotations

import csv
import json
import sqlite3
import subprocess
import sys
import textwrap
import zipfile
from pathlib import Path

import pytest

from multilang.domain.exporting import (
    FREQUENCY_EXPORT_CARD_FIELD_NAMES,
    JAPANESE_EXPORT_CARD_FIELD_NAMES,
    MANDARIN_EXPORT_CARD_FIELD_NAMES,
    ExportArtifactFormat,
    ExportCardIdentity,
    ExportCardRow,
)
from multilang.domain.jobs import SupportedLanguage
from multilang.services import card_template_loader
from multilang.services.anki_id_registry import AnkiIdKind, registry_id
from multilang.services.export_anki_package import (
    DECK_ID,
    HIGHLIGHT_MODEL_ID,
    HIGHLIGHT_NOTE_TYPE_NAME,
    MANUAL_MODEL_ID,
    MANUAL_NOTE_TYPE_NAME,
    MANDARIN_MODEL_ID,
    MANDARIN_NOTE_TYPE_NAME,
    MODEL_ID,
    ExportAnkiPackageError,
    build_multilang_model,
    build_multilang_note,
    export_anki_package,
)
from multilang.services.japanese_frequency_deck import JAPANESE_MODEL_ID, JAPANESE_NOTE_TYPE_NAME
from multilang.services.export_tabular_bundle import write_export_tabular_bundle


def test_core_export_ids_are_registry_backed_without_local_numeric_declarations() -> None:
    source = Path("src/multilang/services/export_anki_package.py").read_text(encoding="utf-8")

    assert MODEL_ID == registry_id(family="core", role="frequency_model", kind=AnkiIdKind.MODEL)
    assert DECK_ID == registry_id(family="core", role="export_deck", kind=AnkiIdKind.DECK)
    assert MANUAL_MODEL_ID == registry_id(family="core", role="manual_model", kind=AnkiIdKind.MODEL)
    assert HIGHLIGHT_MODEL_ID == registry_id(family="core", role="highlight_model", kind=AnkiIdKind.MODEL)
    assert MANDARIN_MODEL_ID == registry_id(family="mandarin", role="card_model", kind=AnkiIdKind.MODEL)
    assert "1_602_300_501" not in source
    assert "1_602_300_502" not in source
    assert "1_602_300_503" not in source
    assert "1_602_300_504" not in source
    assert "1_762_800_901" not in source


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
    language: SupportedLanguage = SupportedLanguage.EN,
    word_reading: str | None = None,
    word_romaji: str | None = None,
    sentence_furigana: str | None = None,
    sentence_romaji: str | None = None,
) -> ExportCardRow:
    return ExportCardRow(
        identity=ExportCardIdentity(
            language=language,
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
        word_reading=word_reading,
        word_romaji=word_romaji,
        sentence_furigana=sentence_furigana,
        sentence_romaji=sentence_romaji,
    )


def make_mandarin_row(*, source_type: str = "frequency") -> ExportCardRow:
    return ExportCardRow(
        identity=ExportCardIdentity(
            language=SupportedLanguage.ZH,
            source_type=source_type,
            job_id="job-zh",
            item_key="中国",
            lemma_key="zh:中国",
            sort_index=1,
        ),
        word="中国",
        front_of_card="中国",
        definitions="proper noun: China",
        example_sentence="我去银行。",
        translation="I go to the bank.",
        word_audio="[sound:zh-word.mp3]",
        sentence_audio="[sound:zh-sentence.mp3]",
        mandarin_word_pinyin="zhōng guó",
        mandarin_word_traditional="中國",
        mandarin_sentence_pinyin="wǒ qù yín háng。",
        mandarin_sentence_traditional="我去銀行。",
    )


def make_korean_row(*, item_key: str, sort_index: int, frequency_level: int | None) -> ExportCardRow:
    return ExportCardRow(
        identity=ExportCardIdentity(
            language=SupportedLanguage.KO,
            source_type="frequency",
            job_id="job-ko",
            item_key=item_key,
            lemma_key=f"ko:{item_key}",
            sort_index=sort_index,
        ),
        sort_index=sort_index,
        frequency_level=frequency_level,
        frequency_bundle_sha256="a" * 64,
        export_gate_receipt_sha256="b" * 64,
        text_review_receipt_sha256="c" * 64,
        word_audio_artifact_sha256="d" * 64,
        sentence_audio_artifact_sha256="e" * 64,
        word=item_key,
        front_of_card=item_key,
        ipa=f"/{item_key}/",
        definitions="substantivo: fixture",
        example_sentence=f"{item_key}을 봐요.",
        translation="Eu vejo o item.",
        word_audio=f"[sound:{item_key}-word.mp3]",
        sentence_audio=f"[sound:{item_key}-sentence.mp3]",
    )


def korean_media_index(tmp_path: Path, rows: list[ExportCardRow]) -> dict[str, Path]:
    media: dict[str, Path] = {}
    for row in rows:
        media[row.word_audio] = write_media_file(tmp_path / "audio" / f"{row.identity.item_key}-word.mp3", b"ID3-word")
        media[row.sentence_audio] = write_media_file(
            tmp_path / "audio" / f"{row.identity.item_key}-sentence.mp3",
            b"ID3-sentence",
        )
    return media


@pytest.mark.parametrize("source_type", ["frequency", "word-list"])
def test_build_mandarin_model_uses_dedicated_identity_fields_and_template(source_type: str) -> None:
    model = build_multilang_model(source_type=source_type, language=SupportedLanguage.ZH)

    assert model.model_id == MANDARIN_MODEL_ID == 1_762_800_901
    assert model.name == MANDARIN_NOTE_TYPE_NAME == "Multilang::Mandarin Card"
    assert tuple(field["name"] for field in model.fields) == MANDARIN_EXPORT_CARD_FIELD_NAMES
    qfmt = model.templates[0]["qfmt"]
    afmt = model.templates[0]["afmt"]
    assert qfmt.index("{{word}}") < qfmt.index("{{Pinyin}}") < qfmt.index("{{Traditional}}")
    assert qfmt.index("{{Example Sentence}}") < qfmt.index("{{Sentence Pinyin}}")
    assert qfmt.index("{{Sentence Pinyin}}") < qfmt.index("{{Traditional Sentence}}")
    assert 'id="translation"' in qfmt and 'style="display:none;"' in qfmt
    assert 'document.getElementById("translation").style.display = "block";' in afmt


@pytest.mark.parametrize("source_type", ["frequency", "word-list"])
def test_export_mandarin_package_bundles_both_audio_files(source_type: str, tmp_path: Path) -> None:
    row = make_mandarin_row(source_type=source_type)
    word_media = write_media_file(tmp_path / "audio" / "zh-word.mp3", b"ID3-word")
    sentence_media = write_media_file(tmp_path / "audio" / "zh-sentence.mp3", b"ID3-sentence")
    output_path = tmp_path / f"mandarin-{source_type}.apkg"

    result = export_anki_package(
        rows=[row],
        media_index={row.word_audio: word_media, row.sentence_audio: sentence_media},
        output_path=output_path,
        deck_name="Multilang Mandarin Chinese",
    )

    assert result.media_files == [word_media, sentence_media]
    with zipfile.ZipFile(output_path) as archive:
        media_manifest = json.loads(archive.read("media").decode("utf-8"))
        assert set(media_manifest.values()) == {"zh-word.mp3", "zh-sentence.mp3"}
        for archived_name in media_manifest:
            assert archive.read(archived_name).startswith(b"ID3")
        collection_path = tmp_path / f"collection-{source_type}.anki2"
        collection_path.write_bytes(archive.read("collection.anki2"))
    with sqlite3.connect(collection_path) as connection:
        models = json.loads(connection.execute("select models from col").fetchone()[0])
        fields = connection.execute("select flds from notes").fetchone()[0].split("\x1f")
    model = models[str(MANDARIN_MODEL_ID)]
    assert model["name"] == MANDARIN_NOTE_TYPE_NAME
    assert tuple(field["name"] for field in model["flds"]) == MANDARIN_EXPORT_CARD_FIELD_NAMES
    assert fields[-1] == ""
    assert "zhōng guó" in fields and "中國" in fields and "我去銀行。" in fields


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
    assert '<div id="translation" class="sentenceTranslation" style="display:none;">' in model.templates[0]["qfmt"]
    assert '<div class="header">Definition:</div>' in model.templates[0]["qfmt"]
    assert 'definitionsList' in model.templates[0]["qfmt"]
    assert model.templates[0]["qfmt"].index('definitionsList') < model.templates[0]["qfmt"].index('{{Image}}')
    assert model.templates[0]["qfmt"].index('{{Image}}') < model.templates[0]["qfmt"].index('<div class="header">example:</div>')
    assert 'document.getElementById("translation").style.display = "block";' in model.templates[0]["afmt"]
    assert "--max-width-card: 680px;" in model.css
    assert "--color-page-background: #121212;" in model.css
    assert "--color-card-background: #1E1E1E;" in model.css
    assert "--color-text-primary: #EAEAEA;" in model.css
    assert "--color-text-muted: #A0A0A0;" in model.css
    assert "--color-divider: #333333;" in model.css
    assert "border-radius: 8px;" in model.css
    assert "border: 1px solid var(--color-divider);" in model.css
    assert "box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);" in model.css
    assert "--font-size-targetWord: 38px;" in model.css
    assert "background: transparent;" in model.css
    assert ".card {\n  display: flex;\n  justify-content: center;\n  align-items: flex-start;" in model.css
    assert "padding: 16px 12px 12px;" in model.css
    assert "#qa {\n  width: 100%;\n  max-width: 680px;\n  min-width: 0;\n}" in model.css
    assert "margin: 0 auto;\n  max-width: 680px;\n  width: 100%;\n  min-height: 0;" in model.css
    assert "padding: 32px 40px;" in model.css
    assert "max-width: 680px;" in model.css
    assert "min-height: 100vh;" in model.css
    assert "min-height: 0;" in model.css
    assert "@media (max-width: 720px)" in model.css
    assert "min-height: calc(100vh - 24px);" not in model.css
    assert "min-height: calc(100vh - 16px);" not in model.css
    assert "width: calc(100vw - 24px);" in model.css
    assert "padding: 24px 20px;" in model.css
    assert "overflow-x: hidden;" in model.css
    assert "overflow-x: auto" not in model.css
    assert "white-space: nowrap" not in model.css
    assert "overflow-wrap: anywhere;" in model.css
    assert "grid-template-columns: minmax(0, 1fr) 32px;" in model.css
    assert "width: 32px;" in model.css


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


def test_build_japanese_frequency_model_uses_japanese_note_type_and_template() -> None:
    model = build_multilang_model(source_type="frequency", language=SupportedLanguage.JA)

    assert model.model_id == JAPANESE_MODEL_ID
    assert model.name == JAPANESE_NOTE_TYPE_NAME
    assert tuple(field["name"] for field in model.fields) == JAPANESE_EXPORT_CARD_FIELD_NAMES
    assert "toggleFurigana" in model.templates[0]["qfmt"]
    assert "customCard cardBack jpFront" in model.templates[0]["qfmt"]
    assert "customCard cardBack jpBack" in model.templates[0]["afmt"]
    assert "{{furigana:Word Reading}}" in model.templates[0]["qfmt"]
    assert "{{furigana:Sentence Furigana}}" in model.templates[0]["afmt"]


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


def test_build_multilang_note_adds_traceability_tags() -> None:
    note = build_multilang_note(make_row(item_key="level-1-rank-0001", sort_index=1))

    assert {"multilang", "en", "frequency", "level_1", "rank_0001", "job_job_1"}.issubset(set(note.tags))


def test_build_multilang_note_maps_japanese_frequency_fields() -> None:
    row = make_row(
        item_key="学校",
        sort_index=1,
        language=SupportedLanguage.JA,
        example_sentence="学校に行く。",
        translation="I go to school.",
        word_audio="[sound:gakkou-word.mp3]",
        sentence_audio="[sound:gakkou-sentence.mp3]",
        word_reading="学校[がっこう]",
        word_romaji="Gakkou",
        sentence_furigana="学校[がっこう]に行[い]く。",
        sentence_romaji="Gakkou ni iku.",
    )

    note = build_multilang_note(row, model=build_multilang_model(source_type="frequency", language=SupportedLanguage.JA))

    assert note.fields == [
        "1",
        "学校",
        "学校[がっこう]",
        "Gakkou",
        "to move fast<br>to operate",
        "学校に行く。",
        "学校[がっこう]に行[い]く。",
        "Gakkou ni iku.",
        "I go to school.",
        "[sound:gakkou-word.mp3]",
        "[sound:gakkou-sentence.mp3]",
        "",
    ]


def test_export_korean_frequency_package_has_registered_parent_and_three_child_decks(
    tmp_path: Path,
) -> None:
    rows = [
        make_korean_row(item_key="어휘1", sort_index=1, frequency_level=1),
        make_korean_row(item_key="어휘2", sort_index=1001, frequency_level=2),
        make_korean_row(item_key="어휘3", sort_index=2001, frequency_level=3),
    ]
    output_path = tmp_path / "korean-frequency.apkg"
    parent_deck_id = registry_id(family="korean_frequency", role="parent_deck", kind=AnkiIdKind.DECK)
    level_deck_ids = {
        1: registry_id(family="korean_frequency", role="level_1_deck", kind=AnkiIdKind.DECK),
        2: registry_id(family="korean_frequency", role="level_2_deck", kind=AnkiIdKind.DECK),
        3: registry_id(family="korean_frequency", role="level_3_deck", kind=AnkiIdKind.DECK),
    }
    model_id = registry_id(family="korean_frequency", role="model", kind=AnkiIdKind.MODEL)

    result = export_anki_package(
        rows=rows,
        media_index=korean_media_index(tmp_path, rows),
        output_path=output_path,
        deck_name="Multilang Korean::Frequency",
        cards_per_level=1,
        expected_items=3,
    )

    assert result.output_path == output_path
    assert result.card_count == 3
    with zipfile.ZipFile(output_path) as archive:
        media_manifest = json.loads(archive.read("media").decode("utf-8"))
        assert sorted(media_manifest.values()) == sorted(
            [
                "어휘1-word.mp3",
                "어휘1-sentence.mp3",
                "어휘2-word.mp3",
                "어휘2-sentence.mp3",
                "어휘3-word.mp3",
                "어휘3-sentence.mp3",
            ]
        )
        collection_path = tmp_path / "korean-collection.anki2"
        collection_path.write_bytes(archive.read("collection.anki2"))
    with sqlite3.connect(collection_path) as connection:
        models = json.loads(connection.execute("select models from col").fetchone()[0])
        decks = json.loads(connection.execute("select decks from col").fetchone()[0])
        routed_cards = connection.execute(
            "select cards.did, notes.guid, notes.flds, notes.tags "
            "from cards join notes on notes.id = cards.nid order by notes.sfld"
        ).fetchall()

    assert decks[str(parent_deck_id)]["name"] == "Multilang Korean::Frequency"
    assert decks[str(level_deck_ids[1])]["name"] == "Multilang Korean::Frequency::Level 1"
    assert decks[str(level_deck_ids[2])]["name"] == "Multilang Korean::Frequency::Level 2"
    assert decks[str(level_deck_ids[3])]["name"] == "Multilang Korean::Frequency::Level 3"
    assert models[str(model_id)]["name"] == "Multilang::Card"
    assert tuple(field["name"] for field in models[str(model_id)]["flds"]) == FREQUENCY_EXPORT_CARD_FIELD_NAMES
    assert [card[0] for card in routed_cards] == [level_deck_ids[1], level_deck_ids[2], level_deck_ids[3]]
    assert {card[1] for card in routed_cards} == {row.note_guid for row in rows}
    assert all("a" * 64 not in card[2] for card in routed_cards)
    assert " level_1 " in routed_cards[0][3]
    assert " rank_0001 " in routed_cards[0][3]
    assert " level_2 " in routed_cards[1][3]
    assert " rank_1001 " in routed_cards[1][3]
    assert " level_3 " in routed_cards[2][3]
    assert " rank_2001 " in routed_cards[2][3]


def test_export_korean_frequency_package_rejects_inferred_levels_before_replacing_existing_file(
    tmp_path: Path,
) -> None:
    row = make_korean_row(item_key="어휘1", sort_index=1, frequency_level=None)
    output_path = tmp_path / "korean-frequency.apkg"
    output_path.write_bytes(b"sentinel")

    with pytest.raises(ExportAnkiPackageError, match="explicit frequency level"):
        export_anki_package(
            rows=[row],
            media_index=korean_media_index(tmp_path, [row]),
            output_path=output_path,
            deck_name="Multilang Korean::Frequency",
            cards_per_level=1,
            expected_items=1,
        )

    assert output_path.read_bytes() == b"sentinel"
    assert not any(path.name.endswith(".tmp") for path in tmp_path.iterdir())


def test_japanese_frequency_template_and_apkg_are_back_only_with_romaji(tmp_path: Path) -> None:
    row = make_row(
        item_key="学校",
        sort_index=1,
        language=SupportedLanguage.JA,
        example_sentence="学校に行く。",
        translation="I go to school.",
        word_audio="[sound:gakkou-word.mp3]",
        sentence_audio="[sound:gakkou-sentence.mp3]",
        word_reading="学校[がっこう]",
        word_romaji="Gakkou",
        sentence_furigana="学校[がっこう]に行[い]く。",
        sentence_romaji="Gakkou ni iku.",
    )
    model = build_multilang_model(source_type="frequency", language=SupportedLanguage.JA)
    front = model.templates[0]["qfmt"]
    back = model.templates[0]["afmt"]

    assert model.model_id == JAPANESE_MODEL_ID == 1_762_800_701
    assert model.name == JAPANESE_NOTE_TYPE_NAME == "Multilang::Japanese Card"
    assert tuple(field["name"] for field in model.fields) == JAPANESE_EXPORT_CARD_FIELD_NAMES
    assert "{{Word Romaji}}" not in front
    assert "{{Sentence Romaji}}" not in front
    assert '<div class="wordRomaji">{{Word Romaji}}</div>' in back
    assert '<div class="sentenceRomaji">{{Sentence Romaji}}</div>' in back
    assert back.index("{{furigana:Word Reading}}") < back.index("{{Word Romaji}}")
    assert back.index("{{furigana:Sentence Furigana}}") < back.index("{{Sentence Romaji}}")
    assert back.index("{{Sentence Romaji}}") < back.index("{{Sentence Translation}}")
    for reference in (
        "{{Target Word}}",
        "{{furigana:Word Reading}}",
        "{{Sentence}}",
        "{{furigana:Sentence Furigana}}",
        "{{word_audio}}",
        "{{sentence_audio}}",
        "{{#Image}}",
        "{{Image}}",
        "{{/Image}}",
    ):
        assert reference in front + back

    word_media = write_media_file(tmp_path / "audio" / "gakkou-word.mp3", b"ID3-word")
    sentence_media = write_media_file(tmp_path / "audio" / "gakkou-sentence.mp3", b"ID3-sentence")
    output_path = tmp_path / "japanese-frequency.apkg"
    export_anki_package(
        rows=[row],
        media_index={row.word_audio: word_media, row.sentence_audio: sentence_media},
        output_path=output_path,
        deck_name="Multilang Japanese::Frequency",
    )

    with zipfile.ZipFile(output_path) as archive:
        assert "collection.anki2" in archive.namelist()
        collection_path = tmp_path / "japanese-collection.anki2"
        collection_path.write_bytes(archive.read("collection.anki2"))
    with sqlite3.connect(collection_path) as connection:
        models = json.loads(connection.execute("select models from col").fetchone()[0])
        note_fields = connection.execute("select flds from notes").fetchone()[0].split("\x1f")

    archived_model = models[str(JAPANESE_MODEL_ID)]
    assert archived_model["name"] == JAPANESE_NOTE_TYPE_NAME
    assert tuple(field["name"] for field in archived_model["flds"]) == JAPANESE_EXPORT_CARD_FIELD_NAMES
    assert note_fields == [
        "1",
        "学校",
        "学校[がっこう]",
        "Gakkou",
        "to move fast<br>to operate",
        "学校に行く。",
        "学校[がっこう]に行[い]く。",
        "Gakkou ni iku.",
        "I go to school.",
        "[sound:gakkou-word.mp3]",
        "[sound:gakkou-sentence.mp3]",
        "",
    ]


def test_frozen_japanese_apkg_export_does_not_invoke_romaji_converter() -> None:
    script = textwrap.dedent(
        """
        from pathlib import Path
        from tempfile import TemporaryDirectory

        import multilang.services.japanese_romaji as romaji_module

        def unavailable(_value: str) -> str:
            raise AssertionError("frozen APKG export invoked the romaji converter")

        romaji_module.romanize_japanese = unavailable

        from multilang.domain.exporting import ExportCardIdentity, ExportCardRow
        from multilang.domain.jobs import SupportedLanguage
        from multilang.services.export_anki_package import export_anki_package

        row = ExportCardRow(
            identity=ExportCardIdentity(
                language=SupportedLanguage.JA,
                source_type="frequency",
                job_id="frozen-ja",
                item_key="学校",
                lemma_key="ja:学校",
                sort_index=1,
            ),
            word="学校",
            front_of_card="学校",
            definitions="noun: school",
            example_sentence="学校に行く。",
            translation="I go to school.",
            word_audio="[sound:gakkou-word.mp3]",
            sentence_audio="[sound:gakkou-sentence.mp3]",
            word_reading="学校[がっこう]",
            word_romaji="Gakkou",
            sentence_furigana="学校[がっこう]に行[い]く。",
            sentence_romaji="Gakkou ni iku.",
        )

        with TemporaryDirectory() as directory:
            root = Path(directory)
            word_audio = root / "gakkou-word.mp3"
            sentence_audio = root / "gakkou-sentence.mp3"
            word_audio.write_bytes(b"ID3-word")
            sentence_audio.write_bytes(b"ID3-sentence")
            output_path = root / "japanese-frequency.apkg"
            result = export_anki_package(
                rows=[row],
                media_index={
                    row.word_audio: word_audio,
                    row.sentence_audio: sentence_audio,
                },
                output_path=output_path,
                deck_name="Multilang Japanese::Frequency",
            )
            assert result.card_count == 1
            assert output_path.is_file()
        """
    )

    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize(
    ("export_format", "delimiter", "suffix"),
    [
        (ExportArtifactFormat.CSV, ",", ".csv"),
        (ExportArtifactFormat.TSV, "\t", ".tsv"),
    ],
)
def test_japanese_tabular_exports_use_romaji_field_order(
    tmp_path: Path,
    export_format: ExportArtifactFormat,
    delimiter: str,
    suffix: str,
) -> None:
    row = make_row(
        item_key="学校",
        sort_index=1,
        language=SupportedLanguage.JA,
        example_sentence="学校に行く。",
        translation="I go to school.",
        word_audio="[sound:gakkou-word.mp3]",
        sentence_audio="[sound:gakkou-sentence.mp3]",
        word_reading="学校[がっこう]",
        word_romaji="Gakkou",
        sentence_furigana="学校[がっこう]に行[い]く。",
        sentence_romaji="Gakkou ni iku.",
    )

    result = write_export_tabular_bundle(
        rows=[row],
        export_format=export_format,
        output_dir=tmp_path / export_format.value,
        deck_name="Multilang Japanese::Frequency",
        note_type_name=JAPANESE_NOTE_TYPE_NAME,
    )

    assert result.output_path.suffix == suffix
    lines = result.output_path.read_text(encoding="utf-8").splitlines()
    assert lines[:5] == [
        f"#separator:{'Tab' if delimiter == chr(9) else 'Comma'}",
        "#html:true",
        f"#notetype:{JAPANESE_NOTE_TYPE_NAME}",
        "#deck:Multilang Japanese::Frequency",
        f"#columns:{delimiter.join(JAPANESE_EXPORT_CARD_FIELD_NAMES)}",
    ]
    assert next(csv.reader([lines[5]], delimiter=delimiter)) == [
        "1",
        "学校",
        "学校[がっこう]",
        "Gakkou",
        "to move fast<br>to operate",
        "学校に行く。",
        "学校[がっこう]に行[い]く。",
        "Gakkou ni iku.",
        "I go to school.",
        "[sound:gakkou-word.mp3]",
        "[sound:gakkou-sentence.mp3]",
        "",
    ]


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
        collection_path = tmp_path / "collection.anki2"
        collection_path.write_bytes(archive.read("collection.anki2"))
    with sqlite3.connect(collection_path) as connection:
        raw_tags = connection.execute("select tags from notes").fetchone()[0]
    assert " multilang " in raw_tags
    assert " rank_0001 " in raw_tags


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
