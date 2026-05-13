"""v1.3 integration evidence for normal template/export contract boundaries."""

from __future__ import annotations

import csv
import json
import re
import sqlite3
import zipfile
from pathlib import Path

from multilang.domain.exporting import ExportArtifactFormat, ExportCardIdentity, ExportCardRow
from multilang.domain.jobs import SupportedLanguage
from multilang.services.export_anki_package import MODEL_ID, NOTE_TYPE_NAME, export_anki_package
from multilang.services.export_tabular_bundle import write_export_tabular_bundle


NORMAL_FIELD_NAMES = (
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


def write_media_file(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"ID3-synthetic-normal-audio")
    return path


def make_normal_row() -> ExportCardRow:
    return ExportCardRow(
        identity=ExportCardIdentity(
            language=SupportedLanguage.EN,
            source_type="frequency",
            job_id="job-v13-normal-contract",
            item_key="run",
            lemma_key="en:run",
            sort_index=1,
        ),
        word="run",
        front_of_card="legacy internal value must not export",
        ipa="/rʌn/",
        definitions="to move quickly<br>to operate",
        example_sentence="I run every morning.",
        translation="Eu corro todas as manhãs.",
        word_audio="[sound:run-word.mp3]",
        sentence_audio="[sound:run-sentence.mp3]",
    )


def _read_model_from_apkg(apkg_path: Path, tmp_path: Path, model_id: int) -> dict[str, object]:
    with zipfile.ZipFile(apkg_path) as archive:
        collection_path = tmp_path / f"collection-{model_id}.anki2"
        collection_path.write_bytes(archive.read("collection.anki2"))
    with sqlite3.connect(collection_path) as connection:
        models = json.loads(connection.execute("select models from col").fetchone()[0])
    return models[str(model_id)]


def test_normal_apkg_omits_front_of_card_and_exports_responsive_sentence_layout(tmp_path: Path) -> None:
    row = make_normal_row()
    word_media = write_media_file(tmp_path / "audio" / "run-word.mp3")
    sentence_media = write_media_file(tmp_path / "audio" / "run-sentence.mp3")
    apkg_path = tmp_path / "normal.apkg"

    result = export_anki_package(
        rows=[row],
        media_index={row.word_audio: word_media, row.sentence_audio: sentence_media},
        output_path=apkg_path,
        deck_name="English::Level 1",
    )

    assert result.card_count == 1
    normal_model = _read_model_from_apkg(apkg_path, tmp_path, MODEL_ID)
    qfmt = normal_model["tmpls"][0]["qfmt"]
    afmt = normal_model["tmpls"][0]["afmt"]
    css = normal_model["css"]

    assert normal_model["name"] == NOTE_TYPE_NAME
    assert [field["name"] for field in normal_model["flds"]] == list(NORMAL_FIELD_NAMES)
    assert "Front of Card" not in [field["name"] for field in normal_model["flds"]]
    assert "{{Front of Card}}" not in qfmt + afmt
    assert "{{word}}" in qfmt
    assert "exampleSentenceLine" in qfmt
    assert "exampleSentenceText" in qfmt
    assert "sentenceAudioButton" in qfmt
    assert "{{Example Sentence}}" in qfmt
    assert "{{sentence_audio}}" in qfmt
    assert ".exampleSentenceLine" in css
    assert ".exampleSentenceText" in css
    assert ".sentenceAudioButton" in css
    assert "min-width: 0;" in css


def test_normal_csv_and_tsv_headers_omit_front_of_card_in_revised_order(tmp_path: Path) -> None:
    row = make_normal_row()
    csv_result = write_export_tabular_bundle(
        rows=[row],
        export_format=ExportArtifactFormat.CSV,
        output_dir=tmp_path / "csv",
        deck_name="English::Level 1",
        note_type_name=NOTE_TYPE_NAME,
    )
    tsv_result = write_export_tabular_bundle(
        rows=[row],
        export_format=ExportArtifactFormat.TSV,
        output_dir=tmp_path / "tsv",
        deck_name="English::Level 1",
        note_type_name=NOTE_TYPE_NAME,
    )

    csv_lines = csv_result.output_path.read_text(encoding="utf-8").splitlines()
    tsv_lines = tsv_result.output_path.read_text(encoding="utf-8").splitlines()
    csv_row = list(csv.reader(csv_lines[5:]))[0]
    tsv_row = list(csv.reader(tsv_lines[5:], delimiter="\t"))[0]

    assert csv_lines[4] == "#columns:" + ",".join(NORMAL_FIELD_NAMES)
    assert tsv_lines[4] == "#columns:" + "\t".join(NORMAL_FIELD_NAMES)
    assert "Front of Card" not in csv_lines[4]
    assert "Front of Card" not in tsv_lines[4]
    assert csv_row == tsv_row == [
        "1",
        "run",
        "/rʌn/",
        "to move quickly<br>to operate",
        "I run every morning.",
        "Eu corro todas as manhãs.",
        "[sound:run-word.mp3]",
        "[sound:run-sentence.mp3]",
        "",
    ]
    assert "legacy internal value must not export" not in ",".join(csv_row)


def test_normal_template_references_are_within_revised_export_fields(tmp_path: Path) -> None:
    row = make_normal_row()
    word_media = write_media_file(tmp_path / "audio" / "run-word.mp3")
    sentence_media = write_media_file(tmp_path / "audio" / "run-sentence.mp3")
    apkg_path = tmp_path / "normal-template.apkg"

    export_anki_package(
        rows=[row],
        media_index={row.word_audio: word_media, row.sentence_audio: sentence_media},
        output_path=apkg_path,
        deck_name="English::Level 1",
    )
    normal_model = _read_model_from_apkg(apkg_path, tmp_path, MODEL_ID)
    template_markup = normal_model["tmpls"][0]["qfmt"] + normal_model["tmpls"][0]["afmt"]
    references = {reference.lstrip("#/") for reference in re.findall(r"{{([^{}]+)}}", template_markup)}

    assert references <= set(NORMAL_FIELD_NAMES) | {"FrontSide"}
    assert "Front of Card" not in references
