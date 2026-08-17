"""Contracts for language-neutral phoneme note mechanics."""

from __future__ import annotations

import genanki
import pytest

import multilang.services.phoneme_deck as phoneme_deck
from multilang.services.phoneme_deck import (
    PHONEME_FIELD_NAMES,
    PhonemeCard,
    PhonemeNote,
    build_phoneme_model,
    build_phoneme_note,
    phoneme_card_fields,
)
from multilang.services.russian_phoneme_deck import build_russian_phoneme_model


EXPECTED_PHONEME_FIELD_NAMES = (
    "Spellings",
    "Sound",
    "letter_audio",
    "Example Word",
    "word_audio",
    "Word Translation",
    "Example Sentence",
    "sentence_audio",
    "Sentence Translation",
)

KOREAN_FONT_CSS = """.koFont,
.phonemeCard {
  font-family: "Noto Sans KR", "Apple SD Gothic Neo", "Malgun Gothic",
    "맑은 고딕", "Segoe UI", sans-serif;
}"""


def _phoneme_card() -> PhonemeCard:
    return PhonemeCard(
        sort_index=7,
        letters="ㄱ + ㅁ",
        ipa="/ŋm/",
        example_word="국물",
        example_word_translation="caldo",
        example_sentence="국물이 뜨거워요.",
        example_sentence_translation="O caldo está quente.",
        letter_audio="[sound:letter.wav]",
        word_audio="[sound:word.wav]",
        sentence_audio="[sound:sentence.wav]",
    )


def test_neutral_phoneme_fields_and_mapping_are_exactly_ordered() -> None:
    card = _phoneme_card()

    assert PHONEME_FIELD_NAMES == EXPECTED_PHONEME_FIELD_NAMES
    assert phoneme_card_fields(card) == [
        "ㄱ + ㅁ",
        "/ŋm/",
        "[sound:letter.wav]",
        "국물",
        "[sound:word.wav]",
        "caldo",
        "국물이 뜨거워요.",
        "[sound:sentence.wav]",
        "O caldo está quente.",
    ]


def test_neutral_model_preserves_shared_template_and_appends_font_css() -> None:
    shared = build_russian_phoneme_model()

    model = build_phoneme_model(
        model_id=1_762_801_003,
        note_type_name="Multilang::Korean Pronunciation",
        additional_css=KOREAN_FONT_CSS,
    )

    assert model.model_id == 1_762_801_003
    assert model.name == "Multilang::Korean Pronunciation"
    assert tuple(field["name"] for field in model.fields) == EXPECTED_PHONEME_FIELD_NAMES
    assert model.templates == shared.templates
    assert model.css == f"{shared.css}\n\n{KOREAN_FONT_CSS}"


def test_neutral_model_without_additional_css_preserves_base_css_bytes() -> None:
    shared = build_russian_phoneme_model()

    model = build_phoneme_model(
        model_id=1_762_801_003,
        note_type_name="Multilang::Korean Pronunciation",
    )

    assert model.css == shared.css


def test_neutral_note_maps_all_values_and_injects_supplied_guid() -> None:
    model = build_phoneme_model(
        model_id=1_762_801_003,
        note_type_name="Multilang::Korean Pronunciation",
    )

    note = build_phoneme_note(
        _phoneme_card(),
        model=model,
        guid="0123456789abcdef0123456789abcdef",
    )

    assert isinstance(note, PhonemeNote)
    assert note.guid == "0123456789abcdef0123456789abcdef"
    assert note.fields == [
        "ㄱ + ㅁ",
        "/ŋm/",
        "[sound:letter.wav]",
        "국물",
        "[sound:word.wav]",
        "caldo",
        "국물이 뜨거워요.",
        "[sound:sentence.wav]",
        "O caldo está quente.",
    ]


def test_neutral_note_uses_genanki_field_guid_when_no_guid_is_supplied() -> None:
    card = _phoneme_card()
    model = build_phoneme_model(
        model_id=1_762_801_003,
        note_type_name="Multilang::Korean Pronunciation",
    )

    note = build_phoneme_note(card, model=model)

    assert note.guid == genanki.guid_for(*phoneme_card_fields(card))


def test_neutral_card_has_no_language_specific_identity_or_guid_formula() -> None:
    card = _phoneme_card()

    assert not hasattr(card, "language_code")
    assert not hasattr(card, "guid")


def test_neutral_model_rejects_unknown_shared_template_references(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    shared = build_russian_phoneme_model()
    monkeypatch.setattr(
        phoneme_deck,
        "_load_phoneme_template",
        lambda: {
            "front": f'{shared.templates[0]["qfmt"]}\n{{{{Unknown Field}}}}',
            "back": shared.templates[0]["afmt"],
            "css": shared.css,
        },
    )

    with pytest.raises(ValueError, match="Unknown Field"):
        build_phoneme_model(
            model_id=1_762_801_003,
            note_type_name="Multilang::Korean Pronunciation",
        )


@pytest.mark.parametrize(
    "replacement_css",
    [
        "body { background: white; }",
        ":root { --color-page-background: white; }",
        '@import url("https://example.invalid/font.css");',
    ],
)
def test_neutral_model_rejects_non_font_css_replacement_attempts(
    replacement_css: str,
) -> None:
    with pytest.raises(ValueError, match="additional phoneme CSS"):
        build_phoneme_model(
            model_id=1_762_801_003,
            note_type_name="Multilang::Korean Pronunciation",
            additional_css=replacement_css,
        )
