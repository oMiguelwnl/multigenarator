"""Tests for the deterministic Japanese frequency deck."""

from __future__ import annotations

from copy import copy
from importlib import import_module
from importlib.util import find_spec
import zipfile
from pathlib import Path

import pytest

from multilang.services.japanese_frequency_deck import (
    JAPANESE_DECK_ID,
    JAPANESE_FIELD_NAMES,
    JAPANESE_FREQUENCY_CARDS,
    JAPANESE_MODEL_ID,
    JAPANESE_NOTE_TYPE_NAME,
    JapaneseCard,
    build_japanese_model,
    build_japanese_note,
    export_japanese_frequency_deck,
)


class NoOpAzureSpeechAdapter:
    def __init__(self, *_args, **_kwargs) -> None:
        pass

    def synthesize(self, **_kwargs):
        raise RuntimeError("audio disabled in Japanese deck tests")


@pytest.mark.parametrize(
    ("source", "forced_output"),
    [
        ("", None),
        ("   ", None),
        ("学校", ""),
        ("学校", "学校"),
        ("㐂", None),
        ("㐂？", None),
    ],
)
def test_japanese_romaji_uses_modified_hepburn_and_rejects_unresolved_output(
    source: str,
    forced_output: str | None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module_name = "multilang.services.japanese_romaji"
    assert find_spec(module_name) is not None, "Japanese romaji service is not implemented"
    romaji_module = import_module(module_name)
    romanize_japanese = romaji_module.romanize_japanese
    error_type = romaji_module.JapaneseRomajiError

    assert romanize_japanese("学校") == "Gakkou"
    assert romanize_japanese("学校に行く。") == "Gakkou ni iku."
    assert romanize_japanese("カツカレーは美味しい") == "Katsu karee wa oishii"
    assert romanize_japanese("何しているの？") == "Nan shite iru no?"

    if forced_output is not None:
        class FakeConverter:
            def romaji(self, _source: str) -> str:
                return forced_output

        monkeypatch.setattr(romaji_module, "_get_converter", lambda: FakeConverter())

    with pytest.raises(error_type):
        romanize_japanese(source)


def test_japanese_cards_are_ordered_and_start_with_donated_examples() -> None:
    assert len(JAPANESE_FREQUENCY_CARDS) >= 10
    assert [card.sort_index for card in JAPANESE_FREQUENCY_CARDS] == list(
        range(1, len(JAPANESE_FREQUENCY_CARDS) + 1)
    )
    assert {card.language_code for card in JAPANESE_FREQUENCY_CARDS} == {"ja"}

    # The two donated note types are preserved as the first cards.
    first = JAPANESE_FREQUENCY_CARDS[0]
    assert first.target_word == "何"
    assert first.definition == "o que"
    assert first.sentence == "何しているの？"

    second = JAPANESE_FREQUENCY_CARDS[1]
    assert second.target_word == "父親"
    assert second.definition == "pai"
    assert second.sentence_translation == "Meu pai faz 50 anos este ano."


def test_japanese_target_word_appears_in_sentence() -> None:
    for card in JAPANESE_FREQUENCY_CARDS:
        stem = card.target_word.rstrip("るくいきう")  # tolerate verb/adjective okurigana
        assert card.target_word in card.sentence or stem in card.sentence, (
            card.target_word,
            card.sentence,
        )


def test_japanese_card_guids_are_stable_and_unique() -> None:
    guids = [card.guid for card in JAPANESE_FREQUENCY_CARDS]
    assert len(guids) == len(set(guids))
    # Deterministic: rebuilding an identical card yields the same guid.
    clone = JapaneseCard(
        sort_index=JAPANESE_FREQUENCY_CARDS[0].sort_index,
        target_word=JAPANESE_FREQUENCY_CARDS[0].target_word,
        word_reading=JAPANESE_FREQUENCY_CARDS[0].word_reading,
        definition=JAPANESE_FREQUENCY_CARDS[0].definition,
        sentence=JAPANESE_FREQUENCY_CARDS[0].sentence,
        sentence_furigana=JAPANESE_FREQUENCY_CARDS[0].sentence_furigana,
        sentence_translation=JAPANESE_FREQUENCY_CARDS[0].sentence_translation,
    )
    assert clone.guid == JAPANESE_FREQUENCY_CARDS[0].guid
    assert clone.word_romaji == JAPANESE_FREQUENCY_CARDS[0].word_romaji
    assert clone.sentence_romaji == JAPANESE_FREQUENCY_CARDS[0].sentence_romaji

    changed_romaji = copy(JAPANESE_FREQUENCY_CARDS[0])
    object.__setattr__(changed_romaji, "word_romaji", "Changed word reading")
    object.__setattr__(changed_romaji, "sentence_romaji", "Changed sentence reading")
    assert changed_romaji.guid == JAPANESE_FREQUENCY_CARDS[0].guid


def test_build_japanese_model_uses_template_and_field_order() -> None:
    model = build_japanese_model()

    assert model.model_id == JAPANESE_MODEL_ID == 1_762_800_701
    assert JAPANESE_DECK_ID == 1_762_800_702
    assert model.name == JAPANESE_NOTE_TYPE_NAME == "Multilang::Japanese Card"
    assert tuple(field["name"] for field in model.fields) == JAPANESE_FIELD_NAMES
    assert JAPANESE_FIELD_NAMES == (
        "SortIndex",
        "Target Word",
        "Word Reading",
        "Word Romaji",
        "Definition",
        "Sentence",
        "Sentence Furigana",
        "Sentence Romaji",
        "Sentence Translation",
        "word_audio",
        "sentence_audio",
        "Image",
    )

    front = model.templates[0]["qfmt"]
    back = model.templates[0]["afmt"]
    # Furigana toggle (JP1K idea) present on the front.
    assert "toggleFurigana" in front
    assert "{{furigana:Word Reading}}" in front
    assert "{{Target Word}}" in front
    assert "{{Word Romaji}}" not in front
    assert "{{Sentence Romaji}}" not in front
    # Portuguese labels (FRPG+ idea) present on the back.
    assert "{{furigana:Sentence Furigana}}" in back
    assert '<div class="wordRomaji">{{Word Romaji}}</div>' in back
    assert '<div class="sentenceRomaji">{{Sentence Romaji}}</div>' in back
    assert back.index("{{furigana:Word Reading}}") < back.index("{{Word Romaji}}")
    assert back.index("{{furigana:Sentence Furigana}}") < back.index("{{Sentence Romaji}}")
    assert back.index("{{Sentence Romaji}}") < back.index("{{Sentence Translation}}")
    assert "Definição:" in back
    assert "Exemplo:" in back
    assert "{{word_audio}}" in back
    assert "{{sentence_audio}}" in back
    assert "{{#Image}}" in back and "{{Image}}" in back and "{{/Image}}" in back
    assert "jisho.org" not in front + back
    assert "weblio.jp" not in front + back
    assert ".customCard" in model.css
    assert ".targetWordContainer" in model.css
    assert ".exampleSentenceLine" in model.css
    assert ".wordRomaji" in model.css
    assert ".sentenceRomaji" in model.css
    assert ".jpLinks" not in model.css


def test_build_japanese_note_maps_fields_in_order() -> None:
    card = JapaneseCard(
        sort_index=99,
        target_word="犬",
        word_reading="犬[いぬ]",
        definition="cachorro",
        sentence="犬が好きです。",
        sentence_furigana="犬[いぬ]が 好[す]きです。",
        sentence_translation="Eu gosto de cachorros.",
        word_audio="[sound:word.mp3]",
        sentence_audio="[sound:sentence.mp3]",
    )
    note = build_japanese_note(card, model=build_japanese_model())

    assert note.fields == [
        "99",
        "犬",
        "犬[いぬ]",
        "Inu",
        "cachorro",
        "犬が好きです。",
        "犬[いぬ]が 好[す]きです。",
        "Inu ga suki desu.",
        "Eu gosto de cachorros.",
        "[sound:word.mp3]",
        "[sound:sentence.mp3]",
        "",
    ]
    assert note.guid == card.guid


def test_export_japanese_frequency_deck_writes_apkg(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        "multilang.services.japanese_frequency_deck.AzureSpeechAdapter",
        NoOpAzureSpeechAdapter,
    )
    output_path = tmp_path / "japanese-frequency.apkg"

    result = export_japanese_frequency_deck(output_path=output_path)

    assert result.output_path == output_path
    assert result.card_count == len(JAPANESE_FREQUENCY_CARDS)
    with zipfile.ZipFile(output_path) as archive:
        assert "collection.anki2" in archive.namelist()


def test_export_japanese_frequency_deck_can_write_subset(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        "multilang.services.japanese_frequency_deck.AzureSpeechAdapter",
        NoOpAzureSpeechAdapter,
    )
    output_path = tmp_path / "japanese-frequency-subset.apkg"
    cards = JAPANESE_FREQUENCY_CARDS[:3]

    result = export_japanese_frequency_deck(output_path=output_path, cards=cards)

    assert result.card_count == 3
    with zipfile.ZipFile(output_path) as archive:
        assert "collection.anki2" in archive.namelist()
