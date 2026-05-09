"""Domain tests for the frozen Phase 5 export contract."""

from __future__ import annotations

import pytest

from multilang.domain.exporting import (
    EXPORT_CARD_FIELD_NAMES,
    ExportArtifactFormat,
    ExportCardIdentity,
    ExportCardRow,
    FREQUENCY_EXPORT_CARD_FIELD_NAMES,
    HIGHLIGHT_EXPORT_CARD_FIELD_NAMES,
    MANUAL_EXPORT_CARD_FIELD_NAMES,
    export_field_names_for_rows,
    export_field_names_for_source_type,
)
from multilang.domain.jobs import SupportedLanguage


def make_identity(*, item_key: str = "line-1") -> ExportCardIdentity:
    return ExportCardIdentity(
        language=SupportedLanguage.EN,
        source_type="frequency",
        job_id="job-123",
        item_key=item_key,
        lemma_key="en:run",
        sort_index=1,
    )


def make_identity_for_source(source_type: str, *, item_key: str = "line-1") -> ExportCardIdentity:
    return make_identity(item_key=item_key).model_copy(update={"source_type": source_type})


def make_row(**overrides: object) -> ExportCardRow:
    payload: dict[str, object] = {
        "identity": make_identity(),
        "word": "run",
        "front_of_card": "run",
        "ipa": "/rʌn/",
        "definitions": "to move quickly<br>to operate",
        "example_sentence": "I run every morning.",
        "translation": "Eu corro todas as manhãs.",
        "word_audio": "[sound:run.mp3]",
        "sentence_audio": "[sound:run-sentence.mp3]",
    }
    payload.update(overrides)
    return ExportCardRow(**payload)


def test_export_contract_uses_exact_field_order() -> None:
    row = make_row()

    assert EXPORT_CARD_FIELD_NAMES == (
        "SortIndex",
        "word",
        "Front of Card",
        "IPA",
        "Definitions",
        "Example Sentence",
        "Translation",
        "word_audio",
        "sentence_audio",
        "Image",
    )
    assert tuple(row.model_dump(by_alias=True, exclude={"identity", "note_guid"}).keys()) == EXPORT_CARD_FIELD_NAMES


def test_manual_word_list_export_uses_highlight_field_contract() -> None:
    row = make_row(identity=make_identity(), translation="Eu corro.")
    manual_identity = row.identity.model_copy(update={"source_type": "word-list"})
    manual_row = row.model_copy(update={"identity": manual_identity})

    assert MANUAL_EXPORT_CARD_FIELD_NAMES == HIGHLIGHT_EXPORT_CARD_FIELD_NAMES
    mapping = manual_row.ordered_field_mapping()
    assert tuple(mapping) == HIGHLIGHT_EXPORT_CARD_FIELD_NAMES
    assert mapping["Word"] == "run"
    assert mapping["Definition"] == "to move quickly<br>to operate"
    assert "Translation" not in mapping


def test_export_field_names_are_source_profile_aware_for_existing_modes() -> None:
    assert export_field_names_for_source_type("frequency") == FREQUENCY_EXPORT_CARD_FIELD_NAMES
    assert export_field_names_for_source_type("word-list") == MANUAL_EXPORT_CARD_FIELD_NAMES
    assert "Translation" in export_field_names_for_source_type("frequency")
    assert "Translation" not in export_field_names_for_source_type("word-list")


def test_highlight_export_field_names_omit_translation_and_use_highlight_aliases() -> None:
    assert export_field_names_for_source_type("kindle-highlights") == HIGHLIGHT_EXPORT_CARD_FIELD_NAMES
    assert HIGHLIGHT_EXPORT_CARD_FIELD_NAMES == (
        "SortIndex",
        "Word",
        "IPA",
        "Example Sentence",
        "sentence_audio",
        "Definition",
        "Image",
    )
    assert "Translation" not in HIGHLIGHT_EXPORT_CARD_FIELD_NAMES
    assert "word" not in HIGHLIGHT_EXPORT_CARD_FIELD_NAMES
    assert "Definitions" not in HIGHLIGHT_EXPORT_CARD_FIELD_NAMES


def test_highlight_ordered_mapping_synthesizes_aliases_without_translation() -> None:
    row = make_row(identity=make_identity_for_source("kindle-highlights"))

    mapping = row.ordered_field_mapping()

    assert tuple(mapping.keys()) == HIGHLIGHT_EXPORT_CARD_FIELD_NAMES
    assert mapping["Word"] == "run"
    assert mapping["Definition"] == "to move quickly<br>to operate"
    assert "Translation" not in mapping


def test_export_field_names_for_rows_rejects_mixed_sources() -> None:
    rows = [
        make_row(identity=make_identity_for_source("frequency", item_key="one")),
        make_row(identity=make_identity_for_source("word-list", item_key="two")),
    ]

    with pytest.raises(ValueError, match="mixed source types"):
        export_field_names_for_rows(rows)


def test_note_guid_ignores_mutable_card_content() -> None:
    base = make_row()
    changed = make_row(
        definitions="updated definition",
        example_sentence="I run later now.",
        translation="Agora eu corro mais tarde.",
        word_audio="[sound:run-v2.mp3]",
        sentence_audio="[sound:run-sentence-v2.mp3]",
    )

    assert base.note_guid == changed.note_guid
    assert base.note_guid


def test_image_defaults_blank_and_definitions_stay_single_html_field() -> None:
    row = make_row()

    assert row.image == ""
    dumped = row.model_dump(by_alias=True, exclude={"identity", "note_guid"})
    assert dumped["Definitions"] == "to move quickly<br>to operate"
    assert isinstance(dumped["Definitions"], str)


def test_export_artifact_formats_cover_apkg_csv_and_tsv() -> None:
    assert {member.value for member in ExportArtifactFormat} == {"apkg", "csv", "tsv"}


def test_visible_sort_index_must_match_stable_identity() -> None:
    with pytest.raises(ValueError, match="SortIndex"):
        make_row(SortIndex=2)
