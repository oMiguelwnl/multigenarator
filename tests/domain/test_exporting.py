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
    LATIN_EXPORT_CARD_FIELD_NAMES,
    MANDARIN_EXPORT_CARD_FIELD_NAMES,
    MANUAL_EXPORT_CARD_FIELD_NAMES,
    evaluate_export_quality_gate,
    export_field_names_for_rows,
    export_field_names_for_language_and_source,
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
        "IPA",
        "Definitions",
        "Example Sentence",
        "Translation",
        "word_audio",
        "sentence_audio",
        "Image",
    )
    assert tuple(row.ordered_field_mapping().keys()) == EXPORT_CARD_FIELD_NAMES
    assert "Front of Card" not in row.ordered_field_mapping()


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
    assert export_field_names_for_source_type("latin-mvp") == LATIN_EXPORT_CARD_FIELD_NAMES
    assert "Translation" in export_field_names_for_source_type("frequency")
    assert "Translation" not in export_field_names_for_source_type("word-list")
    assert "Front of Card" not in export_field_names_for_source_type("frequency")


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


def make_mandarin_identity(
    *,
    source_type: str = "frequency",
    item_key: str = "zh-1",
) -> ExportCardIdentity:
    return ExportCardIdentity(
        language=SupportedLanguage.ZH,
        source_type=source_type,
        job_id="job-zh",
        item_key=item_key,
        lemma_key=f"zh:{item_key}",
        sort_index=1,
    )


def make_mandarin_row(**overrides: object) -> ExportCardRow:
    payload: dict[str, object] = {
        "identity": make_mandarin_identity(),
        "word": "中国",
        "front_of_card": "中国",
        "ipa": None,
        "definitions": "proper noun: China",
        "example_sentence": "我去银行。",
        "translation": "I go to the bank.",
        "word_audio": "[sound:zh-word.mp3]",
        "sentence_audio": "[sound:zh-sentence.mp3]",
        "mandarin_word_pinyin": "zhōng guó",
        "mandarin_word_traditional": "中國",
        "mandarin_sentence_pinyin": "wǒ qù yín háng。",
        "mandarin_sentence_traditional": "我去銀行。",
    }
    payload.update(overrides)
    return ExportCardRow(**payload)


def test_mandarin_field_contract_is_exact_for_frequency_and_word_list() -> None:
    assert MANDARIN_EXPORT_CARD_FIELD_NAMES == (
        "SortIndex",
        "word",
        "Pinyin",
        "Traditional",
        "Definitions",
        "Example Sentence",
        "Sentence Pinyin",
        "Traditional Sentence",
        "Translation",
        "word_audio",
        "sentence_audio",
        "Image",
    )
    for source_type in ("frequency", "word-list"):
        assert (
            export_field_names_for_language_and_source(
                language=SupportedLanguage.ZH,
                source_type=source_type,
            )
            == MANDARIN_EXPORT_CARD_FIELD_NAMES
        )

    mapping = make_mandarin_row().ordered_field_mapping()
    assert tuple(mapping) == MANDARIN_EXPORT_CARD_FIELD_NAMES
    assert mapping["Pinyin"] == "zhōng guó"
    assert mapping["Traditional Sentence"] == "我去銀行。"
    assert mapping["Image"] == ""


@pytest.mark.parametrize(
    "missing_field",
    [
        "mandarin_word_pinyin",
        "mandarin_word_traditional",
        "mandarin_sentence_pinyin",
        "mandarin_sentence_traditional",
        "translation",
    ],
)
def test_mandarin_rows_require_orthography_and_translation(missing_field: str) -> None:
    with pytest.raises(ValueError, match="Mandarin"):
        make_mandarin_row(**{missing_field: ""})


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("mandarin_word_pinyin", "㐂"),
        ("mandarin_sentence_pinyin", "wǒ yòng 㐂。"),
        ("mandarin_sentence_pinyin", "zhōng guó Ж"),
    ],
)
def test_mandarin_rows_reject_non_pinyin_letters(field: str, value: str) -> None:
    with pytest.raises(ValueError, match="pinyin"):
        make_mandarin_row(**{field: value})


def test_mandarin_rows_reject_nonblank_image() -> None:
    with pytest.raises(ValueError, match="Image"):
        make_mandarin_row(image="not-allowed.png")


def test_export_field_names_for_rows_rejects_mixed_languages() -> None:
    with pytest.raises(ValueError, match="mixed languages"):
        export_field_names_for_rows(
            [
                make_mandarin_row(),
                make_row(identity=make_identity(item_key="en-1")),
            ]
        )


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


def make_latin_identity(*, item_key: str = "line-1") -> ExportCardIdentity:
    return ExportCardIdentity(
        language=SupportedLanguage.LA,
        source_type="latin-mvp",
        job_id="job-la",
        item_key=item_key,
        lemma_key="la:vir",
        sort_index=1,
    )


def test_latin_grammar_field_uses_gramatica_not_definition() -> None:
    row = make_row(
        identity=make_latin_identity(),
        definitions="substantivo: homem",
        gramatica="virum: subst masc, 2a declinacao, Accusativus singularis, OD.",
    )

    mapping = row.ordered_field_mapping()

    assert "Grammar" in mapping
    assert mapping["Grammar"] == "virum: subst masc, 2a declinacao, Accusativus singularis, OD."
    assert mapping["Grammar"] != mapping["Definition"]


def test_latin_grammar_field_falls_back_to_definition_when_gramatica_absent() -> None:
    row = make_row(identity=make_latin_identity(), definitions="substantivo: homem")

    mapping = row.ordered_field_mapping()

    # Without a structured grammar the field intentionally mirrors Definition.
    assert mapping["Grammar"] == mapping["Definition"] == "substantivo: homem"


def test_export_gate_blocks_fallback_audio_by_default_and_warns_when_partial_allowed() -> None:
    rows = [
        make_row(
            identity=make_identity(item_key=f"level-{((index - 1) // 1000) + 1}-rank-{index:04d}").model_copy(
                update={"sort_index": index, "lemma_key": f"en:run:{index}"}
            ),
            SortIndex=index,
        )
        for index in range(1, 3001)
    ]

    blocked = evaluate_export_quality_gate(source_type="frequency", rows=rows, fallback_audio_count=1)
    partial = evaluate_export_quality_gate(source_type="frequency", rows=rows, fallback_audio_count=1, allow_partial=True)

    assert blocked.passed is False
    assert [issue.code for issue in blocked.issues] == ["fallback_audio"]
    assert partial.passed is True
    assert partial.partial is True
    assert [warning.code for warning in partial.warnings] == ["fallback_audio"]
