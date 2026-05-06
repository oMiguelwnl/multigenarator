"""Integration evidence for highlight APKG/CSV/TSV export artifacts."""

from __future__ import annotations

import csv
import json
import re
import sqlite3
import zipfile
from pathlib import Path

from multilang.domain.exporting import (
    ExportArtifactFormat,
    ExportCardIdentity,
    ExportCardRow,
    HIGHLIGHT_EXPORT_CARD_FIELD_NAMES,
)
from multilang.domain.jobs import SupportedLanguage
from multilang.services.export_anki_package import (
    HIGHLIGHT_MODEL_ID,
    HIGHLIGHT_NOTE_TYPE_NAME,
    build_multilang_model,
    export_anki_package,
)
from multilang.services.export_tabular_bundle import write_export_tabular_bundle


def write_media_file(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"ID3-synthetic-highlight-audio")
    return path


def make_highlight_row() -> ExportCardRow:
    return ExportCardRow(
        identity=ExportCardIdentity(
            language=SupportedLanguage.PT,
            source_type="kindle-highlights",
            job_id="job-highlight-export-evidence",
            item_key="highlight-casa",
            lemma_key="pt:casa",
            sort_index=1,
        ),
        word="casa",
        front_of_card="casa",
        ipa="/ˈka.zɐ/",
        definitions="a place where someone lives",
        example_sentence="A casa fica perto do rio.",
        translation="must not appear in highlight export artifacts",
        word_audio="[sound:casa-word.mp3]",
        sentence_audio="[sound:casa-sentence.mp3]",
    )


def test_highlight_export_artifacts_use_dedicated_model_fields_and_safe_media(
    tmp_path: Path,
) -> None:
    row = make_highlight_row()
    word_media = write_media_file(tmp_path / "audio" / "casa-word.mp3")
    sentence_media = write_media_file(tmp_path / "audio" / "casa-sentence.mp3")
    apkg_path = tmp_path / "highlight.apkg"

    result = export_anki_package(
        rows=[row],
        media_index={row.word_audio: word_media, row.sentence_audio: sentence_media},
        output_path=apkg_path,
        deck_name="Portuguese::Highlights",
    )

    assert result.output_path == apkg_path
    assert result.card_count == 1
    assert result.media_files == [word_media, sentence_media]
    assert apkg_path.exists()
    with zipfile.ZipFile(apkg_path) as archive:
        assert "collection.anki2" in archive.namelist()
        assert "media" in archive.namelist()
        media_manifest = json.loads(archive.read("media").decode("utf-8"))
        assert sorted(media_manifest.values()) == ["casa-sentence.mp3", "casa-word.mp3"]
        collection_path = tmp_path / "collection.anki2"
        collection_path.write_bytes(archive.read("collection.anki2"))

    with sqlite3.connect(collection_path) as connection:
        models = json.loads(connection.execute("select models from col").fetchone()[0])
    highlight_model = models[str(HIGHLIGHT_MODEL_ID)]

    assert highlight_model["name"] == HIGHLIGHT_NOTE_TYPE_NAME
    assert [field["name"] for field in highlight_model["flds"]] == list(
        HIGHLIGHT_EXPORT_CARD_FIELD_NAMES
    )


def test_highlight_model_template_has_no_dangling_references_or_translation() -> None:
    model = build_multilang_model(source_type="kindle-highlights")
    allowed_fields = set(HIGHLIGHT_EXPORT_CARD_FIELD_NAMES) | {"FrontSide"}
    template_markup = model.templates[0]["qfmt"] + model.templates[0]["afmt"]
    references = {reference.lstrip("#/") for reference in re.findall(r"{{([^{}]+)}}", template_markup)}

    assert references <= allowed_fields
    assert "Translation" not in references
    assert "{{Translation}}" not in template_markup
    assert "Translation" not in [field["name"] for field in model.fields]


def test_highlight_csv_and_tsv_headers_match_strict_anki_import_metadata(
    tmp_path: Path,
) -> None:
    row = make_highlight_row()
    csv_result = write_export_tabular_bundle(
        rows=[row],
        export_format=ExportArtifactFormat.CSV,
        output_dir=tmp_path / "csv",
        deck_name="Portuguese::Highlights",
        note_type_name=HIGHLIGHT_NOTE_TYPE_NAME,
    )
    tsv_result = write_export_tabular_bundle(
        rows=[row],
        export_format=ExportArtifactFormat.TSV,
        output_dir=tmp_path / "tsv",
        deck_name="Portuguese::Highlights",
        note_type_name=HIGHLIGHT_NOTE_TYPE_NAME,
    )

    csv_lines = csv_result.output_path.read_text(encoding="utf-8").splitlines()
    tsv_lines = tsv_result.output_path.read_text(encoding="utf-8").splitlines()
    csv_row = list(csv.reader(csv_lines[5:]))[0]
    tsv_row = list(csv.reader(tsv_lines[5:], delimiter="\t"))[0]

    assert csv_lines[:5] == [
        "#separator:Comma",
        "#html:true",
        f"#notetype:{HIGHLIGHT_NOTE_TYPE_NAME}",
        "#deck:Portuguese::Highlights",
        "#columns:" + ",".join(HIGHLIGHT_EXPORT_CARD_FIELD_NAMES),
    ]
    assert tsv_lines[:5] == [
        "#separator:Tab",
        "#html:true",
        f"#notetype:{HIGHLIGHT_NOTE_TYPE_NAME}",
        "#deck:Portuguese::Highlights",
        "#columns:" + "\t".join(HIGHLIGHT_EXPORT_CARD_FIELD_NAMES),
    ]
    assert csv_row == tsv_row == [
        "1",
        "casa",
        "/ˈka.zɐ/",
        "[sound:casa-word.mp3]",
        "A casa fica perto do rio.",
        "[sound:casa-sentence.mp3]",
        "a place where someone lives",
        "",
    ]
    assert "Translation" not in csv_lines[4]
    assert "Translation" not in tsv_lines[4]
