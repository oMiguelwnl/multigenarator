"""Tests for CSV/TSV export fallback bundles."""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

from multilang.domain.exporting import (
    ExportArtifactFormat,
    ExportCardIdentity,
    ExportCardRow,
    HIGHLIGHT_EXPORT_CARD_FIELD_NAMES,
)
from multilang.domain.jobs import SupportedLanguage
from multilang.services.export_tabular_bundle import write_export_tabular_bundle


def make_row(
    *,
    item_key: str,
    sort_index: int,
    translation: str,
    definitions: str,
    source_type: str = "frequency",
) -> ExportCardRow:
    return ExportCardRow(
        identity=ExportCardIdentity(
            language=SupportedLanguage.RU,
            source_type=source_type,
            job_id="job-1",
            item_key=item_key,
            lemma_key=f"ru:{item_key}",
            sort_index=sort_index,
        ),
        word=item_key,
        front_of_card=f"{item_key} front",
        ipa=f"/{item_key}/",
        definitions=definitions,
        example_sentence=f"Пример, {item_key}\nв строке два",
        translation=translation,
        word_audio=f"[sound:{item_key}.mp3]",
        sentence_audio=f"[sound:{item_key}-sentence.mp3]",
    )


def test_write_export_tabular_bundle_writes_tsv_with_anki_headers(tmp_path: Path) -> None:
    output = write_export_tabular_bundle(
        rows=[make_row(item_key="alpha", sort_index=2, translation="Перевод", definitions="sense one<br>sense two")],
        export_format=ExportArtifactFormat.TSV,
        output_dir=tmp_path,
        deck_name="English::Level 1",
        note_type_name="Multilang::Card",
    )

    content = output.output_path.read_text(encoding="utf-8")

    assert output.output_path.suffix == ".tsv"
    assert content.startswith("#separator:Tab\n#html:true\n#notetype:Multilang::Card\n#deck:English::Level 1\n#columns:SortIndex\tword\tIPA\tDefinitions\tExample Sentence\tTranslation\tword_audio\tsentence_audio\tImage\n")


def test_write_export_tabular_bundle_writes_utf8_csv_with_fixed_field_order(tmp_path: Path) -> None:
    output = write_export_tabular_bundle(
        rows=[make_row(item_key="beta", sort_index=1, translation='texto, "traduzido"', definitions="um<br>dois")],
        export_format=ExportArtifactFormat.CSV,
        output_dir=tmp_path,
        deck_name="Deck",
        note_type_name="Multilang::Card",
    )

    lines = output.output_path.read_text(encoding="utf-8").splitlines()
    parsed = list(csv.reader(output.output_path.read_text(encoding="utf-8").splitlines()[5:]))[0]

    assert output.output_path.suffix == ".csv"
    assert lines[0] == "#separator:Comma"
    assert parsed == [
        "1",
        "beta",
        "/beta/",
        "um<br>dois",
        "Пример, beta<br>в строке два",
        'texto, "traduzido"',
        "[sound:beta.mp3]",
        "[sound:beta-sentence.mp3]",
        "",
    ]


def test_write_export_tabular_bundle_round_trips_non_latin_text_and_br_values(tmp_path: Path) -> None:
    output = write_export_tabular_bundle(
        rows=[
            make_row(item_key="ёж", sort_index=1, translation="日本語, português, \"quoted\"", definitions="значение<br>ещё одно"),
            make_row(item_key="zeta", sort_index=2, translation="segunda linha", definitions="line 1<br>line 2"),
        ],
        export_format=ExportArtifactFormat.TSV,
        output_dir=tmp_path,
        deck_name="Mixed",
        note_type_name="Multilang::Card",
    )

    parsed_rows = list(csv.reader(output.output_path.read_text(encoding="utf-8").splitlines()[5:], delimiter="\t"))

    assert parsed_rows[0][1] == "ёж"
    assert parsed_rows[0][5] == '日本語, português, "quoted"'
    assert parsed_rows[0][3] == "значение<br>ещё одно"


def test_write_export_tabular_bundle_uses_highlight_fields_for_manual_word_lists(tmp_path: Path) -> None:
    output = write_export_tabular_bundle(
        rows=[
            make_row(
                item_key="мир",
                sort_index=1,
                translation="world",
                definitions="значение",
                source_type="word-list",
            )
        ],
        export_format=ExportArtifactFormat.TSV,
        output_dir=tmp_path,
        deck_name="Manual Russian",
        note_type_name="Multilang::Manual Card",
    )

    content = output.output_path.read_text(encoding="utf-8")
    parsed_rows = list(csv.reader(content.splitlines()[5:], delimiter="\t"))

    assert content.splitlines()[4] == "#columns:" + "\t".join(HIGHLIGHT_EXPORT_CARD_FIELD_NAMES)
    assert "Translation" not in content.splitlines()[4]
    assert parsed_rows[0] == [
        "1",
        "мир",
        "/мир/",
        "Пример, мир<br>в строке два",
        "[sound:мир-sentence.mp3]",
        "значение",
        "",
    ]
    assert content.splitlines()[2] == "#notetype:Multilang::Manual Card"


def test_write_highlight_tsv_uses_strict_anki_headers(tmp_path: Path) -> None:
    output = write_export_tabular_bundle(
        rows=[
            make_row(
                item_key="luz",
                sort_index=3,
                translation="must not export",
                definitions="visible meaning",
                source_type="kindle-highlights",
            )
        ],
        export_format=ExportArtifactFormat.TSV,
        output_dir=tmp_path,
        deck_name="Portuguese::Highlights",
        note_type_name="Multilang::Highlight Card",
    )

    lines = output.output_path.read_text(encoding="utf-8").splitlines()

    assert lines[:5] == [
        "#separator:Tab",
        "#html:true",
        "#notetype:Multilang::Highlight Card",
        "#deck:Portuguese::Highlights",
        "#columns:" + "\t".join(HIGHLIGHT_EXPORT_CARD_FIELD_NAMES),
    ]
    assert lines[4] == (
        "#columns:SortIndex\tWord\tIPA\tExample Sentence\t"
        "sentence_audio\tDefinition\tImage"
    )


def test_write_highlight_csv_omits_translation_and_legacy_field_names(tmp_path: Path) -> None:
    output = write_export_tabular_bundle(
        rows=[
            make_row(
                item_key="casa",
                sort_index=1,
                translation="must not export",
                definitions="home definition",
                source_type="kindle-highlights",
            )
        ],
        export_format=ExportArtifactFormat.CSV,
        output_dir=tmp_path,
        deck_name="Portuguese::Highlights",
        note_type_name="Multilang::Highlight Card",
    )

    lines = output.output_path.read_text(encoding="utf-8").splitlines()

    assert lines[0] == "#separator:Comma"
    assert lines[4] == "#columns:" + ",".join(HIGHLIGHT_EXPORT_CARD_FIELD_NAMES)
    assert "Translation" not in lines[4]
    assert "word," not in lines[4]
    assert "Definitions" not in lines[4]


def test_write_highlight_rows_serialize_safe_fields_and_blank_image(tmp_path: Path) -> None:
    output = write_export_tabular_bundle(
        rows=[
            make_row(
                item_key="ponte",
                sort_index=2,
                translation="must not export",
                definitions="bridge definition",
                source_type="kindle-highlights",
            )
        ],
        export_format=ExportArtifactFormat.TSV,
        output_dir=tmp_path,
        deck_name="Portuguese::Highlights",
        note_type_name="Multilang::Highlight Card",
    )

    parsed_rows = list(
        csv.reader(output.output_path.read_text(encoding="utf-8").splitlines()[5:], delimiter="\t")
    )

    assert parsed_rows == [
        [
            "2",
            "ponte",
            "/ponte/",
            "Пример, ponte<br>в строке два",
            "[sound:ponte-sentence.mp3]",
            "bridge definition",
            "",
        ]
    ]


@pytest.mark.parametrize("other_source", ["frequency", "word-list"])
def test_write_highlight_tabular_bundle_rejects_mixed_source_rows(
    tmp_path: Path, other_source: str
) -> None:
    highlight = make_row(
        item_key="luz",
        sort_index=1,
        translation="must not export",
        definitions="visible meaning",
        source_type="kindle-highlights",
    )
    other = make_row(
        item_key="run",
        sort_index=2,
        translation="translation remains source-specific",
        definitions="move fast",
        source_type=other_source,
    )

    with pytest.raises(ValueError, match="mixed source types"):
        write_export_tabular_bundle(
            rows=[highlight, other],
            export_format=ExportArtifactFormat.CSV,
            output_dir=tmp_path,
            deck_name="Mixed",
            note_type_name="Multilang::Highlight Card",
        )


def test_write_export_tabular_bundle_preserves_translation_for_frequency_decks(tmp_path: Path) -> None:
    output = write_export_tabular_bundle(
        rows=[
            make_row(
                item_key="run",
                sort_index=1,
                translation="run translation",
                definitions="move fast",
            )
        ],
        export_format=ExportArtifactFormat.CSV,
        output_dir=tmp_path,
        deck_name="Frequency English",
        note_type_name="Multilang::Card",
    )

    lines = output.output_path.read_text(encoding="utf-8").splitlines()
    parsed_rows = list(csv.reader(lines[5:]))

    assert ",Translation," in lines[4]
    assert parsed_rows[0][6] == "run translation"
