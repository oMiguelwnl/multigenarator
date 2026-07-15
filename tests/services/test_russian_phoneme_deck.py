"""Tests for the deterministic Russian phoneme deck."""

from __future__ import annotations

import re
import zipfile
from pathlib import Path

from multilang.services.russian_phoneme_deck import (
    GREEK_PHONEME_CARDS,
    PHONEME_FIELD_NAMES,
    POLISH_PHONEME_CARDS,
    RUSSIAN_PHONEME_CARDS,
    RussianPhonemeCard,
    build_greek_phoneme_model,
    build_greek_phoneme_note,
    build_polish_phoneme_model,
    build_polish_phoneme_note,
    build_russian_phoneme_model,
    build_russian_phoneme_note,
    export_greek_phoneme_deck,
    export_polish_phoneme_deck,
    export_russian_phoneme_deck,
)


_FIELD_REFERENCE_RE = re.compile(r"{{[#/^]?([^}:]+)}}|{{hint:([^}]+)}}")


class NoOpAzureSpeechAdapter:
    def __init__(self, *_args, **_kwargs) -> None:
        pass

    def synthesize(self, **_kwargs):
        raise RuntimeError("audio disabled in phoneme deck tests")


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


def test_russian_phoneme_example_sentences_contain_exact_example_word() -> None:
    for card in RUSSIAN_PHONEME_CARDS:
        words = re.findall(r"[А-Яа-яЁё]+", card.example_sentence.casefold())

        assert card.example_word.casefold() in words, (
            card.example_word,
            card.example_sentence,
        )


def test_polish_phoneme_cards_use_supplied_field_data() -> None:
    assert len(POLISH_PHONEME_CARDS) == 16
    assert [card.sort_index for card in POLISH_PHONEME_CARDS] == list(
        range(1, len(POLISH_PHONEME_CARDS) + 1)
    )
    assert {card.language_code for card in POLISH_PHONEME_CARDS} == {"pl"}
    assert [card.letters for card in POLISH_PHONEME_CARDS] == [
        "ą",
        "ę",
        "ł",
        "ń",
        "ś",
        "ź",
        "ż",
        "ć",
        "ó",
        "cz",
        "sz",
        "rz",
        "ch",
        "dz",
        "dź",
        "dż",
    ]

    first_card = POLISH_PHONEME_CARDS[0]
    assert first_card.ipa == "/ɔ̃/"
    assert first_card.example_word == "mąż"
    assert first_card.example_word_translation == "marido"
    assert first_card.example_sentence == "To jest mój mąż."
    assert first_card.example_sentence_translation == "Este é meu marido."


def test_greek_phoneme_cards_use_supplied_field_data() -> None:
    assert len(GREEK_PHONEME_CARDS) == 28
    assert [card.sort_index for card in GREEK_PHONEME_CARDS] == list(
        range(1, len(GREEK_PHONEME_CARDS) + 1)
    )
    assert {card.language_code for card in GREEK_PHONEME_CARDS} == {"el"}
    assert [card.letters for card in GREEK_PHONEME_CARDS[:5]] == [
        "α",
        "ε, αι",
        "η, ι, υ, ει, οι",
        "ο, ω",
        "ου",
    ]

    first_card = GREEK_PHONEME_CARDS[0]
    assert first_card.ipa == "/a/"
    assert first_card.example_word == "αγάπη"
    assert first_card.example_word_translation == "amor"
    assert first_card.example_sentence == "Η αγάπη είναι δυνατή."
    assert first_card.example_sentence_translation == "O amor é forte."


def test_build_polish_phoneme_model_reuses_intro_template() -> None:
    polish_model = build_polish_phoneme_model()
    russian_model = build_russian_phoneme_model()
    note = build_polish_phoneme_note(POLISH_PHONEME_CARDS[0], model=polish_model)

    assert [field["name"] for field in polish_model.fields] == list(PHONEME_FIELD_NAMES)
    assert polish_model.templates[0] == russian_model.templates[0]
    assert polish_model.css == russian_model.css
    assert note.fields == [
        "ą",
        "/ɔ̃/",
        "",
        "mąż",
        "",
        "marido",
        "To jest mój mąż.",
        "",
        "Este é meu marido.",
    ]


def test_build_greek_phoneme_model_reuses_intro_template() -> None:
    greek_model = build_greek_phoneme_model()
    russian_model = build_russian_phoneme_model()
    note = build_greek_phoneme_note(GREEK_PHONEME_CARDS[0], model=greek_model)

    assert [field["name"] for field in greek_model.fields] == list(PHONEME_FIELD_NAMES)
    assert greek_model.templates[0] == russian_model.templates[0]
    assert greek_model.css == russian_model.css
    assert note.fields == [
        "α",
        "/a/",
        "",
        "αγάπη",
        "",
        "amor",
        "Η αγάπη είναι δυνατή.",
        "",
        "O amor é forte.",
    ]


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
    assert "{{Sentence Translation}}" in front
    assert 'id="sentenceTranslation"' in front
    assert 'style="display:none;"' in front
    assert 'id="sentenceTranslation" class="sentenceTranslation"' in front
    assert "{{FrontSide}}" in back
    assert "{{Sentence Translation}}" in back
    assert 'document.getElementById("sentenceTranslation").style.display = "block"' in back
    assert _template_references(front).isdisjoint(forbidden_references)
    assert _template_references(back).isdisjoint(forbidden_references)
    assert "--color-audio-button: #8b6cff" in model.css
    assert ".replay-button::before" not in model.css
    assert ".replay-button svg { display: none; }" not in model.css
    assert ".replay-button svg path" in model.css
    assert "pronunciationHighlight" not in front
    assert ".pronunciationHighlight" not in model.css
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


def test_export_russian_phoneme_deck_writes_apkg(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("multilang.services.russian_phoneme_deck.AzureSpeechAdapter", NoOpAzureSpeechAdapter)
    output_path = tmp_path / "russian-phonemes.apkg"

    result = export_russian_phoneme_deck(output_path=output_path)

    assert result.output_path == output_path
    assert result.card_count == len(RUSSIAN_PHONEME_CARDS)
    with zipfile.ZipFile(output_path) as archive:
        assert "collection.anki2" in archive.namelist()


def test_export_polish_phoneme_deck_writes_apkg(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("multilang.services.russian_phoneme_deck.AzureSpeechAdapter", NoOpAzureSpeechAdapter)
    output_path = tmp_path / "polish-phonemes.apkg"

    result = export_polish_phoneme_deck(output_path=output_path)

    assert result.output_path == output_path
    assert result.card_count == len(POLISH_PHONEME_CARDS)
    with zipfile.ZipFile(output_path) as archive:
        assert "collection.anki2" in archive.namelist()


def test_export_greek_phoneme_deck_writes_apkg(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("multilang.services.russian_phoneme_deck.AzureSpeechAdapter", NoOpAzureSpeechAdapter)
    output_path = tmp_path / "greek-phonemes.apkg"

    result = export_greek_phoneme_deck(output_path=output_path)

    assert result.output_path == output_path
    assert result.card_count == len(GREEK_PHONEME_CARDS)
    with zipfile.ZipFile(output_path) as archive:
        assert "collection.anki2" in archive.namelist()


def test_export_russian_phoneme_deck_can_write_visual_check_subset(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("multilang.services.russian_phoneme_deck.AzureSpeechAdapter", NoOpAzureSpeechAdapter)
    output_path = tmp_path / "russian-phonemes-visual-check.apkg"
    cards = RUSSIAN_PHONEME_CARDS[:4]

    result = export_russian_phoneme_deck(output_path=output_path, cards=cards)

    assert result.output_path == output_path
    assert result.card_count == 4
    assert all("ь" not in card.letters and "ъ" not in card.letters for card in cards)
    assert all(card.ipa.startswith("/") and card.ipa.endswith("/") for card in cards)
    with zipfile.ZipFile(output_path) as archive:
        assert "collection.anki2" in archive.namelist()
