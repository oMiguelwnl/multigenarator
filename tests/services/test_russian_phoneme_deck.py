"""Tests for the deterministic Russian phoneme deck."""

from __future__ import annotations

from dataclasses import asdict
from hashlib import sha256
import json
import re
import zipfile
from pathlib import Path

import multilang.services.phoneme_deck as neutral_phoneme_deck
import multilang.services.russian_phoneme_deck as russian_phoneme_deck
from multilang.services.russian_phoneme_deck import (
    GREEK_PHONEME_CARDS,
    PHONEME_FIELD_NAMES,
    POLISH_PHONEME_CARDS,
    RUSSIAN_PHONEME_CARDS,
    RussianPhonemeCard,
    RussianPhonemeNote,
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

_EXPECTED_PUBLIC_EXPORTS = (
    "DEFAULT_GREEK_PHONEME_DECK_NAME",
    "DEFAULT_POLISH_PHONEME_DECK_NAME",
    "DEFAULT_RUSSIAN_PHONEME_DECK_NAME",
    "GREEK_PHONEME_CARDS",
    "GREEK_PHONEME_DECK_ID",
    "GREEK_PHONEME_LOCALE",
    "GREEK_PHONEME_MODEL_ID",
    "GREEK_PHONEME_NOTE_TYPE_NAME",
    "GREEK_PHONEME_VOICE_ID",
    "PHONEME_DECK_ID",
    "PHONEME_FIELD_NAMES",
    "PHONEME_MODEL_ID",
    "PHONEME_NOTE_TYPE_NAME",
    "POLISH_PHONEME_CARDS",
    "POLISH_PHONEME_DECK_ID",
    "POLISH_PHONEME_LOCALE",
    "POLISH_PHONEME_MODEL_ID",
    "POLISH_PHONEME_NOTE_TYPE_NAME",
    "POLISH_PHONEME_VOICE_ID",
    "RUSSIAN_PHONEME_CARDS",
    "RUSSIAN_PHONEME_LOCALE",
    "RUSSIAN_PHONEME_VOICE_ID",
    "RussianPhonemeCard",
    "RussianPhonemeDeckExportResult",
    "build_greek_phoneme_model",
    "build_greek_phoneme_note",
    "build_polish_phoneme_model",
    "build_polish_phoneme_note",
    "build_russian_phoneme_model",
    "build_russian_phoneme_note",
    "export_greek_phoneme_deck",
    "export_polish_phoneme_deck",
    "export_russian_phoneme_deck",
)

_EXPECTED_LANGUAGE_CONTRACTS = {
    "russian": {
        "model_id": 1_602_300_601,
        "deck_id": 1_602_300_602,
        "note_type_name": "Multilang::Russian Phoneme",
        "deck_name": "Multilang Russian::Intro Phonemes",
        "voice_id": "ru-RU-DmitryNeural",
        "locale": "ru-RU",
        "inventory_sha256": "1f2d95f883826395650242f1e60b6a292142d9c15d2cbf3db0365b9650baac05",
        "guid_list_sha256": "5f722198b4d3c30b56dc53c5d3e8b3ba0bc3d103a68e833370a68a0d5e785412",
        "first_guid": "b26694cb021c19c5263614fc5cc3cde4",
    },
    "polish": {
        "model_id": 1_602_300_603,
        "deck_id": 1_602_300_604,
        "note_type_name": "Multilang::Polish Phoneme",
        "deck_name": "Multilang Polish::Intro Phonemes",
        "voice_id": "pl-PL-AgnieszkaNeural",
        "locale": "pl-PL",
        "inventory_sha256": "f47f7be267a1c81e8057f6cc09253035773d0c78decec5ade760b87a13ccadba",
        "guid_list_sha256": "7b10cee8ca0299ad0db2296c13c368262833e6da7d9a3171ce30c9b713dd07d1",
        "first_guid": "b9b1513bd440672d6bc303a69cda5908",
    },
    "greek": {
        "model_id": 1_602_300_605,
        "deck_id": 1_602_300_606,
        "note_type_name": "Multilang::Greek Phoneme",
        "deck_name": "Multilang Greek::Intro Phonemes",
        "voice_id": "el-GR-AthinaNeural",
        "locale": "el-GR",
        "inventory_sha256": "44994699c515f5b6e194eb346f7ad7716ba34f59d59f75bbd2d001c2b2f84999",
        "guid_list_sha256": "fd312fa3d6522cbd1051e2e130310182dbfca4702fb7a74e06c1b1fb79da7722",
        "first_guid": "d20e2656a851001d6453c11f70ed127d",
    },
}

_EXPECTED_TEMPLATE_HASHES = {
    "qfmt": "8dcd312a1701efe52e8a849b6560a32e34d704e5f23b8301f9929875ee7ca6a2",
    "afmt": "c80d95d48c63660edf9e3691588c68af0218a6d45497a07c27f53efd6783eb39",
    "css": "788a67fec92ef52853cc4ee88ed06868fe840e80fa7922601cab185f98f13b75",
}


class NoOpAzureSpeechAdapter:
    def __init__(self, *_args, **_kwargs) -> None:
        pass

    def synthesize(self, **_kwargs):
        raise RuntimeError("audio disabled in phoneme deck tests")


def _template_references(template: str) -> set[str]:
    return {match.group(1) or match.group(2) for match in _FIELD_REFERENCE_RE.finditer(template)}


def _json_sha256(value: object) -> str:
    serialized = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(serialized.encode("utf-8")).hexdigest()


def test_russian_phoneme_public_surface_and_legacy_contract_are_frozen() -> None:
    assert tuple(russian_phoneme_deck.__all__) == _EXPECTED_PUBLIC_EXPORTS
    assert all(hasattr(russian_phoneme_deck, name) for name in _EXPECTED_PUBLIC_EXPORTS)
    assert russian_phoneme_deck.RussianPhonemeNote is RussianPhonemeNote

    language_inputs = {
        "russian": (
            RUSSIAN_PHONEME_CARDS,
            build_russian_phoneme_model,
            build_russian_phoneme_note,
            russian_phoneme_deck.PHONEME_DECK_ID,
            russian_phoneme_deck.DEFAULT_RUSSIAN_PHONEME_DECK_NAME,
            russian_phoneme_deck.RUSSIAN_PHONEME_VOICE_ID,
            russian_phoneme_deck.RUSSIAN_PHONEME_LOCALE,
        ),
        "polish": (
            POLISH_PHONEME_CARDS,
            build_polish_phoneme_model,
            build_polish_phoneme_note,
            russian_phoneme_deck.POLISH_PHONEME_DECK_ID,
            russian_phoneme_deck.DEFAULT_POLISH_PHONEME_DECK_NAME,
            russian_phoneme_deck.POLISH_PHONEME_VOICE_ID,
            russian_phoneme_deck.POLISH_PHONEME_LOCALE,
        ),
        "greek": (
            GREEK_PHONEME_CARDS,
            build_greek_phoneme_model,
            build_greek_phoneme_note,
            russian_phoneme_deck.GREEK_PHONEME_DECK_ID,
            russian_phoneme_deck.DEFAULT_GREEK_PHONEME_DECK_NAME,
            russian_phoneme_deck.GREEK_PHONEME_VOICE_ID,
            russian_phoneme_deck.GREEK_PHONEME_LOCALE,
        ),
    }

    for language, values in language_inputs.items():
        cards, model_builder, note_builder, deck_id, deck_name, voice_id, locale = values
        expected = _EXPECTED_LANGUAGE_CONTRACTS[language]
        model = model_builder()
        note = note_builder(cards[0], model=model)

        assert model.model_id == expected["model_id"]
        assert deck_id == expected["deck_id"]
        assert model.name == expected["note_type_name"]
        assert deck_name == expected["deck_name"]
        assert voice_id == expected["voice_id"]
        assert locale == expected["locale"]
        assert tuple(field["name"] for field in model.fields) == PHONEME_FIELD_NAMES
        assert sha256(model.templates[0]["qfmt"].encode("utf-8")).hexdigest() == (
            _EXPECTED_TEMPLATE_HASHES["qfmt"]
        )
        assert sha256(model.templates[0]["afmt"].encode("utf-8")).hexdigest() == (
            _EXPECTED_TEMPLATE_HASHES["afmt"]
        )
        assert sha256(model.css.encode("utf-8")).hexdigest() == _EXPECTED_TEMPLATE_HASHES["css"]
        assert _json_sha256([asdict(card) for card in cards]) == expected["inventory_sha256"]
        assert _json_sha256([card.guid for card in cards]) == expected["guid_list_sha256"]
        assert note.guid == expected["first_guid"]
        assert note.fields == russian_phoneme_deck._phoneme_card_fields(cards[0])


def test_russian_compatibility_types_and_helpers_delegate_to_neutral_mechanics() -> None:
    assert russian_phoneme_deck.PHONEME_FIELD_NAMES is neutral_phoneme_deck.PHONEME_FIELD_NAMES
    assert issubclass(RussianPhonemeCard, neutral_phoneme_deck.PhonemeCard)
    assert RussianPhonemeNote is neutral_phoneme_deck.PhonemeNote
    assert russian_phoneme_deck._load_phoneme_template() == (
        neutral_phoneme_deck._load_phoneme_template()
    )
    assert russian_phoneme_deck._phoneme_card_fields(RUSSIAN_PHONEME_CARDS[0]) == (
        neutral_phoneme_deck.phoneme_card_fields(RUSSIAN_PHONEME_CARDS[0])
    )


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
    assert [match.group(1) or match.group(2) for match in _FIELD_REFERENCE_RE.finditer(front + back)] == [
        "Spellings",
        "Sound",
        "letter_audio",
        "Example Word",
        "word_audio",
        "Word Translation",
        "Example Sentence",
        "sentence_audio",
        "Sentence Translation",
        "FrontSide",
        "Sentence Translation",
    ]
    for signature in (
        "--color-page-background: #0a1220;",
        "--color-card-background: #0f1b2d;",
        "--color-accent: #3b82f6;",
        "--color-box-background: #12213a;",
        "--color-box-border: #24405f;",
        "border-radius: 16px;",
        "border-top: 4px solid var(--color-accent);",
        "box-shadow: 0 8px 30px rgba(0, 0, 0, 0.45);",
        "border-radius: 50%;",
        "overflow-x: hidden;",
    ):
        assert signature in model.css
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
