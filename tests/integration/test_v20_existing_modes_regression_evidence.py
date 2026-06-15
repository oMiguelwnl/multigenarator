"""Focused EVID-03 regression evidence for existing modes after Latin export."""

from __future__ import annotations

from multilang.domain.exporting import (
    FREQUENCY_EXPORT_CARD_FIELD_NAMES,
    HIGHLIGHT_EXPORT_CARD_FIELD_NAMES,
    MANUAL_EXPORT_CARD_FIELD_NAMES,
    export_field_names_for_source_type,
)
from multilang.services.export_anki_package import (
    HIGHLIGHT_MODEL_ID,
    HIGHLIGHT_NOTE_TYPE_NAME,
    MANUAL_MODEL_ID,
    MANUAL_NOTE_TYPE_NAME,
    MODEL_ID,
    NOTE_TYPE_NAME,
    build_multilang_model,
)
from multilang.services.latin_export import LATIN_EXPORT_FIELD_NAMES, LATIN_MODEL_ID, LATIN_NOTE_TYPE_NAME, build_latin_anki_model
from multilang.services.russian_phoneme_deck import PHONEME_FIELD_NAMES, PHONEME_MODEL_ID, PHONEME_NOTE_TYPE_NAME, build_russian_phoneme_model


EVID_03_EXISTING_MODE_EXPORT_REQUIREMENTS = ("EVID-03",)


def test_frequency_export_contract_remains_unchanged() -> None:
    model = build_multilang_model(source_type="frequency")

    assert model.name == NOTE_TYPE_NAME
    assert model.model_id == MODEL_ID
    assert export_field_names_for_source_type("frequency") == FREQUENCY_EXPORT_CARD_FIELD_NAMES
    assert [field["name"] for field in model.fields] == list(FREQUENCY_EXPORT_CARD_FIELD_NAMES)
    assert "Grammar" not in FREQUENCY_EXPORT_CARD_FIELD_NAMES
    assert "Gramatica" not in FREQUENCY_EXPORT_CARD_FIELD_NAMES


def test_manual_and_highlight_export_contracts_do_not_gain_latin_fields() -> None:
    manual_model = build_multilang_model(source_type="word-list")
    highlight_model = build_multilang_model(source_type="kindle-highlights")

    assert manual_model.name == MANUAL_NOTE_TYPE_NAME
    assert manual_model.model_id == MANUAL_MODEL_ID
    assert highlight_model.name == HIGHLIGHT_NOTE_TYPE_NAME
    assert highlight_model.model_id == HIGHLIGHT_MODEL_ID
    assert MANUAL_EXPORT_CARD_FIELD_NAMES == HIGHLIGHT_EXPORT_CARD_FIELD_NAMES
    assert set(MANUAL_EXPORT_CARD_FIELD_NAMES).isdisjoint({"Sentence", "Grammar", "Gramatica"})
    assert set(HIGHLIGHT_EXPORT_CARD_FIELD_NAMES).isdisjoint({"Sentence", "Grammar", "Gramatica"})


def test_russian_phonetics_model_remains_isolated_from_latin_and_normal_fields() -> None:
    model = build_russian_phoneme_model()

    assert model.name == PHONEME_NOTE_TYPE_NAME
    assert model.model_id == PHONEME_MODEL_ID
    assert [field["name"] for field in model.fields] == list(PHONEME_FIELD_NAMES)
    assert set(PHONEME_FIELD_NAMES).isdisjoint({"Sentence", "Grammar", "Gramatica", "Definitions", "Translation"})


def test_latin_note_type_and_model_are_distinct_from_existing_modes() -> None:
    latin_model = build_latin_anki_model()

    assert EVID_03_EXISTING_MODE_EXPORT_REQUIREMENTS == ("EVID-03",)
    assert latin_model.name == LATIN_NOTE_TYPE_NAME
    assert latin_model.model_id == LATIN_MODEL_ID
    assert [field["name"] for field in latin_model.fields] == list(LATIN_EXPORT_FIELD_NAMES)
    assert LATIN_NOTE_TYPE_NAME not in {NOTE_TYPE_NAME, MANUAL_NOTE_TYPE_NAME, HIGHLIGHT_NOTE_TYPE_NAME, PHONEME_NOTE_TYPE_NAME}
    assert LATIN_MODEL_ID not in {MODEL_ID, MANUAL_MODEL_ID, HIGHLIGHT_MODEL_ID, PHONEME_MODEL_ID}
    assert {"Translation", "Lemma", "Source", "Latin Word", "Latin Sentence", "Gramatica"}.isdisjoint(LATIN_EXPORT_FIELD_NAMES)
    assert set(LATIN_EXPORT_FIELD_NAMES) != set(FREQUENCY_EXPORT_CARD_FIELD_NAMES)
    assert set(LATIN_EXPORT_FIELD_NAMES) != set(HIGHLIGHT_EXPORT_CARD_FIELD_NAMES)
    assert set(LATIN_EXPORT_FIELD_NAMES) != set(PHONEME_FIELD_NAMES)
