"""Tests for the deterministic Russian phoneme deck."""

from __future__ import annotations

import re
import zipfile
from pathlib import Path

from multilang.services.russian_phoneme_deck import (
    PHONEME_FIELD_NAMES,
    RUSSIAN_PHONEME_CARDS,
    RussianPhonemeCard,
    build_russian_phoneme_model,
    build_russian_phoneme_note,
    export_russian_phoneme_deck,
)


_FIELD_REFERENCE_RE = re.compile(r"{{[#/^]?([^}:]+)}}|{{hint:([^}]+)}}")


def _template_references(template: str) -> set[str]:
    return {match.group(1) or match.group(2) for match in _FIELD_REFERENCE_RE.finditer(template)}


def test_russian_phoneme_cards_are_ordered_and_have_unique_sentence_words() -> None:
    assert len(RUSSIAN_PHONEME_CARDS) >= 40
    assert [card.sort_index for card in RUSSIAN_PHONEME_CARDS] == list(
        range(1, len(RUSSIAN_PHONEME_CARDS) + 1)
    )

    for card in RUSSIAN_PHONEME_CARDS:
        words = re.findall(r"[А-Яа-яЁё]+", card.example_sentence.casefold())
        assert len(words) == len(set(words)), card.example_sentence


def test_build_russian_phoneme_model_uses_intro_template() -> None:
    model = build_russian_phoneme_model()
    audio_card = RussianPhonemeCard(
        sort_index=999,
        letters="ж",
        ipa="/ʐ/",
        example_word="жук",
        example_word_translation="beetle",
        example_sentence="Женя жарит жёлтый желудь.",
        example_sentence_translation="Zhenya fries a yellow acorn.",
        letter_audio="[sound:letter.mp3]",
        word_audio="[sound:word.mp3]",
        sentence_audio="[sound:sentence.mp3]",
    )
    note = build_russian_phoneme_note(audio_card, model=model)

    assert [field["name"] for field in model.fields] == [
        "Spellings",
        "Sound",
        "letter_audio",
        "Example Word",
        "word_audio",
        "Word Translation",
        "Example Sentence",
        "sentence_audio",
        "Sentence Translation",
    ]
    assert tuple(field["name"] for field in model.fields) == PHONEME_FIELD_NAMES
    front = model.templates[0]["qfmt"]
    back = model.templates[0]["afmt"]
    forbidden_references = {
        "Notes",
        "is_priming",
        "is_sentence",
        "Definitions",
        "image",
        "IPA",
        "Exemple Sentence",
        "Translation",
    }

    for field_reference in (
        "Spellings",
        "Sound",
        "letter_audio",
        "Example Word",
        "word_audio",
        "Word Translation",
        "Example Sentence",
        "sentence_audio",
    ):
        assert f"{{{{{field_reference}}}}}" in front
    assert "{{hint:Sentence Translation}}" not in front
    assert "{{FrontSide}}" in back
    assert "{{Sentence Translation}}" in back
    assert "sentenceTranslation" in back
    assert _template_references(front).isdisjoint(forbidden_references)
    assert _template_references(back).isdisjoint(forbidden_references)
    assert "--color-multilang-primary" in model.css
    assert note.fields == [
        "ж",
        "/ʐ/",
        "[sound:letter.mp3]",
        "жук",
        "[sound:word.mp3]",
        "beetle",
        "Женя жарит жёлтый желудь.",
        "[sound:sentence.mp3]",
        "Zhenya fries a yellow acorn.",
    ]


def test_export_russian_phoneme_deck_writes_apkg(tmp_path: Path) -> None:
    output_path = tmp_path / "russian-phonemes.apkg"

    result = export_russian_phoneme_deck(output_path=output_path)

    assert result.output_path == output_path
    assert result.card_count == len(RUSSIAN_PHONEME_CARDS)
    with zipfile.ZipFile(output_path) as archive:
        assert "collection.anki2" in archive.namelist()
