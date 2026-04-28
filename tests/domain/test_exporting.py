"""Domain tests for the frozen Phase 5 export contract."""

from __future__ import annotations

import pytest

from multilang.domain.exporting import (
    EXPORT_CARD_FIELD_NAMES,
    ExportArtifactFormat,
    ExportCardIdentity,
    ExportCardRow,
)
from multilang.domain.jobs import SupportedLanguage


def make_identity(*, item_key: str = "line-1") -> ExportCardIdentity:
    return ExportCardIdentity(
        language=SupportedLanguage.EN,
        source_type="word-list",
        job_id="job-123",
        item_key=item_key,
        lemma_key="en:run",
        sort_index=1,
    )


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
