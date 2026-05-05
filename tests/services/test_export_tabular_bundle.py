"""Tests for CSV/TSV export fallback bundles."""

from __future__ import annotations

import csv
from pathlib import Path

from multilang.domain.exporting import ExportArtifactFormat, ExportCardIdentity, ExportCardRow
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
    assert content.startswith("#separator:Tab\n#html:true\n#notetype:Multilang::Card\n#deck:English::Level 1\n#columns:SortIndex\tword\tFront of Card\tIPA\tDefinitions\tExample Sentence\tTranslation\tword_audio\tsentence_audio\tImage\n")


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
        "beta front",
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
    assert parsed_rows[0][6] == '日本語, português, "quoted"'
    assert parsed_rows[0][4] == "значение<br>ещё одно"


def test_write_export_tabular_bundle_preserves_translation_for_manual_word_lists(tmp_path: Path) -> None:
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

    assert "\tTranslation\t" in content.splitlines()[4]
    assert parsed_rows[0][6] == "world"
    assert content.splitlines()[2] == "#notetype:Multilang::Manual Card"
