"""VAL-03 regression evidence for deck-mode isolation after v1.3 changes."""

from __future__ import annotations

import re

from multilang.domain.exporting import (
    FREQUENCY_EXPORT_CARD_FIELD_NAMES,
    HIGHLIGHT_EXPORT_CARD_FIELD_NAMES,
    MANUAL_EXPORT_CARD_FIELD_NAMES,
    ExportCardIdentity,
    ExportCardRow,
    export_field_names_for_source_type,
)
from multilang.domain.jobs import SupportedLanguage
from multilang.services.export_anki_package import (
    HIGHLIGHT_NOTE_TYPE_NAME,
    MANUAL_NOTE_TYPE_NAME,
    NOTE_TYPE_NAME,
    build_multilang_model,
)
from multilang.services.russian_phoneme_deck import PHONEME_FIELD_NAMES, build_russian_phoneme_model


V13_NORMAL_FIELD_NAMES = (
    "SortIndex",
    "word",
    "IPA",
    "Definitions",
    "Example Sentence",
    "Translation",
    "word_audio",
    "sentence_audio",
    "Image",
)


def _template_references(markup: str) -> set[str]:
    return {reference.lstrip("#/") for reference in re.findall(r"{{(?:hint:)?([^{}]+)}}", markup)}


def _sample_row(source_type: str) -> ExportCardRow:
    return ExportCardRow(
        identity=ExportCardIdentity(
            language=SupportedLanguage.EN,
            source_type=source_type,
            job_id=f"job-v13-mode-{source_type}",
            item_key="sample",
            lemma_key="en:sample",
            sort_index=7,
        ),
        word="sample",
        front_of_card="Sample",
        ipa="/ˈsæm.pəl/",
        definitions="a small representative part",
        example_sentence="This sample proves the field contract.",
        translation="Esta amostra comprova o contrato de campos.",
        word_audio="[sound:sample-word.mp3]",
        sentence_audio="[sound:sample-sentence.mp3]",
    )


def test_frequency_mode_keeps_revised_normal_contract_with_word_audio_and_translation() -> None:
    model = build_multilang_model(source_type="frequency")
    row = _sample_row("frequency")

    assert model.name == NOTE_TYPE_NAME
    assert FREQUENCY_EXPORT_CARD_FIELD_NAMES == V13_NORMAL_FIELD_NAMES
    assert export_field_names_for_source_type("frequency") == V13_NORMAL_FIELD_NAMES
    assert [field["name"] for field in model.fields] == list(V13_NORMAL_FIELD_NAMES)
    assert row.ordered_field_mapping() == {
        "SortIndex": 7,
        "word": "sample",
        "IPA": "/ˈsæm.pəl/",
        "Definitions": "a small representative part",
        "Example Sentence": "This sample proves the field contract.",
        "Translation": "Esta amostra comprova o contrato de campos.",
        "word_audio": "[sound:sample-word.mp3]",
        "sentence_audio": "[sound:sample-sentence.mp3]",
        "Image": "",
    }
    assert "Front of Card" not in V13_NORMAL_FIELD_NAMES
    assert "Word" not in V13_NORMAL_FIELD_NAMES
    assert "Translation" in V13_NORMAL_FIELD_NAMES
    assert "word_audio" in V13_NORMAL_FIELD_NAMES


def test_custom_word_list_mode_keeps_manual_highlight_style_contract_without_normal_audio() -> None:
    model = build_multilang_model(source_type="word-list")
    row = _sample_row("word-list")
    markup = model.templates[0]["qfmt"] + model.templates[0]["afmt"]

    assert model.name == MANUAL_NOTE_TYPE_NAME
    assert MANUAL_EXPORT_CARD_FIELD_NAMES == HIGHLIGHT_EXPORT_CARD_FIELD_NAMES
    assert export_field_names_for_source_type("word-list") == MANUAL_EXPORT_CARD_FIELD_NAMES
    assert [field["name"] for field in model.fields] == list(MANUAL_EXPORT_CARD_FIELD_NAMES)
    assert "Translation" not in MANUAL_EXPORT_CARD_FIELD_NAMES
    assert "word_audio" not in MANUAL_EXPORT_CARD_FIELD_NAMES
    assert "word" not in MANUAL_EXPORT_CARD_FIELD_NAMES
    assert "Word" in MANUAL_EXPORT_CARD_FIELD_NAMES
    assert row.ordered_field_mapping(field_names=MANUAL_EXPORT_CARD_FIELD_NAMES) == {
        "SortIndex": 7,
        "Word": "sample",
        "IPA": "/ˈsæm.pəl/",
        "Example Sentence": "This sample proves the field contract.",
        "sentence_audio": "[sound:sample-sentence.mp3]",
        "Definition": "a small representative part",
        "Image": "",
    }
    assert "{{Word}}" in markup
    assert "{{Translation}}" not in markup
    assert "{{word_audio}}" not in markup


def test_highlight_mode_keeps_dedicated_note_type_and_source_profile_fields() -> None:
    model = build_multilang_model(source_type="kindle-highlights")
    row = _sample_row("kindle-highlights")
    markup = model.templates[0]["qfmt"] + model.templates[0]["afmt"]
    references = _template_references(markup)

    assert model.name == HIGHLIGHT_NOTE_TYPE_NAME
    assert HIGHLIGHT_NOTE_TYPE_NAME != MANUAL_NOTE_TYPE_NAME
    assert HIGHLIGHT_NOTE_TYPE_NAME != NOTE_TYPE_NAME
    assert export_field_names_for_source_type("kindle-highlights") == HIGHLIGHT_EXPORT_CARD_FIELD_NAMES
    assert [field["name"] for field in model.fields] == list(HIGHLIGHT_EXPORT_CARD_FIELD_NAMES)
    assert references <= set(HIGHLIGHT_EXPORT_CARD_FIELD_NAMES) | {"FrontSide"}
    assert "Translation" not in references
    assert "word_audio" not in references
    assert "Translation" not in HIGHLIGHT_EXPORT_CARD_FIELD_NAMES
    assert "word_audio" not in HIGHLIGHT_EXPORT_CARD_FIELD_NAMES
    assert row.ordered_field_mapping(field_names=HIGHLIGHT_EXPORT_CARD_FIELD_NAMES)["sentence_audio"] == (
        "[sound:sample-sentence.mp3]"
    )


def test_russian_phonetics_mode_keeps_phoneme_contract_without_normal_or_highlight_leakage() -> None:
    model = build_russian_phoneme_model()
    markup = model.templates[0]["qfmt"] + model.templates[0]["afmt"]
    references = _template_references(markup)
    forbidden_fields = set(FREQUENCY_EXPORT_CARD_FIELD_NAMES) | set(HIGHLIGHT_EXPORT_CARD_FIELD_NAMES)

    assert tuple(field["name"] for field in model.fields) == PHONEME_FIELD_NAMES
    assert references <= set(PHONEME_FIELD_NAMES) | {"FrontSide"}
    assert references.isdisjoint({"word", "Word", "IPA", "Definitions", "Definition", "Translation", "Image"})
    assert set(PHONEME_FIELD_NAMES).isdisjoint(forbidden_fields)
    assert "word_audio" in PHONEME_FIELD_NAMES
    assert "sentence_audio" in PHONEME_FIELD_NAMES
