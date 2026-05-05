"""Tests for the deterministic Russian phoneme deck."""

from __future__ import annotations

import re
import zipfile
from pathlib import Path

from multilang.services.russian_phoneme_deck import (
    PHONEME_FIELD_NAMES,
    RUSSIAN_PHONEME_CARDS,
    build_russian_phoneme_model,
    build_russian_phoneme_note,
    export_russian_phoneme_deck,
)


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
    note = build_russian_phoneme_note(RUSSIAN_PHONEME_CARDS[0], model=model)

    assert [field["name"] for field in model.fields] == [
        "SortIndex",
        "Spellings",
        "IPA",
        "letter_audio",
        "Example Word",
        "word_audio",
        "Word Translation",
        "Definitions",
        "Exemple Sentence",
        "sentence_audio",
        "Translation",
        "image",
    ]
    assert tuple(field["name"] for field in model.fields) == PHONEME_FIELD_NAMES
    assert "The letter(s) is:" in model.templates[0]["qfmt"]
    assert "{{Spellings}}" in model.templates[0]["qfmt"]
    assert "{{letter_audio}}" in model.templates[0]["qfmt"]
    assert "{{Exemple Sentence}}" in model.templates[0]["qfmt"]
    assert "document.getElementById" in model.templates[0]["afmt"]
    assert ".russianCard .ruLetterPanel" in model.css
    assert note.fields[1] == "а"
    assert note.fields[2] == "/a/"
    assert note.fields[7]
    assert note.fields[8] == "Анна нашла карту."
    assert note.fields[10] == "Anna found a map."


def test_export_russian_phoneme_deck_writes_apkg(tmp_path: Path) -> None:
    output_path = tmp_path / "russian-phonemes.apkg"

    result = export_russian_phoneme_deck(output_path=output_path)

    assert result.output_path == output_path
    assert result.card_count == len(RUSSIAN_PHONEME_CARDS)
    with zipfile.ZipFile(output_path) as archive:
        assert "collection.anki2" in archive.namelist()
