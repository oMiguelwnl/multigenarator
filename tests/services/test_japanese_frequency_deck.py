"""Tests for the deterministic Japanese frequency deck."""

from __future__ import annotations

import zipfile
from pathlib import Path

from multilang.services.japanese_frequency_deck import (
    JAPANESE_FIELD_NAMES,
    JAPANESE_FREQUENCY_CARDS,
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


def test_build_japanese_model_uses_template_and_field_order() -> None:
    model = build_japanese_model()

    assert model.name == JAPANESE_NOTE_TYPE_NAME
    assert tuple(field["name"] for field in model.fields) == JAPANESE_FIELD_NAMES

    front = model.templates[0]["qfmt"]
    back = model.templates[0]["afmt"]
    # Furigana toggle (JP1K idea) present on the front.
    assert "toggleFurigana" in front
    assert "{{furigana:Word Reading}}" in front
    assert "{{Target Word}}" in front
    # Portuguese labels (FRPG+ idea) present on the back.
    assert "{{furigana:Sentence Furigana}}" in back
    assert "Definição:" in back
    assert "Exemplo:" in back
    assert "jisho.org" not in front + back
    assert "weblio.jp" not in front + back
    assert ".customCard" in model.css
    assert ".targetWordContainer" in model.css
    assert ".exampleSentenceLine" in model.css
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
        "cachorro",
        "犬が好きです。",
        "犬[いぬ]が 好[す]きです。",
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
