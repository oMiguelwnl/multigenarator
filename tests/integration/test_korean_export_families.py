"""Exercise real Korean note packaging, independently of live content production."""

import csv
import json
import sqlite3
import zipfile
from pathlib import Path

import pytest

from multilang.domain.exporting import (
    ExportArtifactFormat,
    ExportCardIdentity,
    ExportCardRow,
    export_field_names_for_language_and_source,
)
from multilang.domain.jobs import SupportedLanguage
from multilang.services.export_anki_package import build_multilang_model, export_anki_package
from multilang.services.export_tabular_bundle import write_export_tabular_bundle


def _row(source: str, *, language=SupportedLanguage.KO, rank: int = 1) -> ExportCardRow:
    return ExportCardRow(
        identity=ExportCardIdentity(
            language=language, source_type=source, job_id="export-contract",
            item_key=f"entry-{rank}", lemma_key=f"lemma-{rank}", sort_index=rank,
        ),
        word="은/는", front_of_card="은/는", definitions="Marca o tópico.",
        example_sentence="저는 학생이에요.", translation="Eu sou estudante.",
        word_audio="[sound:word.mp3]", sentence_audio="[sound:sentence.mp3]",
    )


def _media(tmp_path: Path) -> dict[str, Path]:
    result = {}
    for name in ("word", "sentence"):
        path = tmp_path / f"{name}.mp3"
        path.write_bytes(b"ID3" + name.encode())
        result[f"[sound:{name}.mp3]"] = path
    return result


@pytest.mark.parametrize("source", ["korean-grammar", "word-list", "kindle-highlights"])
def test_korean_family_package_has_isolated_identity_fonts_and_stable_fields(tmp_path, source):
    row = _row(source)
    result = export_anki_package(
        rows=[row], media_index=_media(tmp_path), output_path=tmp_path / "deck.apkg",
        deck_name=f"Multilang Korean::{source}",
    )
    with zipfile.ZipFile(result.output_path) as archive:
        collection = tmp_path / "collection.anki2"
        collection.write_bytes(archive.read("collection.anki2"))
        media = json.loads(archive.read("media"))
    with sqlite3.connect(collection) as connection:
        models = json.loads(connection.execute("select models from col").fetchone()[0])
        guid, fields = connection.execute("select guid, flds from notes").fetchone()
    model = next(iter(models.values()))
    expected_fields = export_field_names_for_language_and_source(language=SupportedLanguage.KO, source_type=source)
    assert tuple(field["name"] for field in model["flds"]) == expected_fields
    assert fields.split("\x1f")[-1] == ""
    assert guid == row.note_guid
    assert "Korean" in model["name"]
    assert '"Noto Sans KR"' in model["css"]
    assert "Malgun Gothic" in model["css"]
    assert "sentence.mp3" in media.values()
    if source != "korean-grammar":
        assert model["id"] != build_multilang_model(source_type=source, language=SupportedLanguage.EN).model_id


@pytest.mark.parametrize("format", [ExportArtifactFormat.CSV, ExportArtifactFormat.TSV])
def test_korean_grammar_tabular_preserves_translation_and_blank_image(tmp_path, format):
    row = _row("korean-grammar")
    result = write_export_tabular_bundle(
        rows=[row], export_format=format, output_dir=tmp_path,
        deck_name="Multilang Korean::Particles & Endings",
        note_type_name="Multilang::Korean Particles & Endings",
    )
    lines = result.output_path.read_text().splitlines()
    record = next(csv.reader([line for line in lines if not line.startswith("#")], delimiter="\t" if format is ExportArtifactFormat.TSV else ","))
    fields = export_field_names_for_language_and_source(language=SupportedLanguage.KO, source_type="korean-grammar")
    assert record[fields.index("Translation")] == row.translation
    assert record[fields.index("Image")] == ""


def test_non_korean_grammar_is_rejected():
    with pytest.raises(ValueError, match="Korean|Korean grammar"):
        build_multilang_model(source_type="korean-grammar", language=SupportedLanguage.EN)


@pytest.mark.parametrize("source", ["korean-grammar", "word-list", "kindle-highlights"])
def test_runtime_tabular_note_type_matches_korean_apkg(source):
    from multilang.runtime import _note_type_name_for_rows

    assert _note_type_name_for_rows([_row(source)]) == build_multilang_model(source_type=source, language=SupportedLanguage.KO).name


def test_existing_frequency_uses_three_real_levels_without_changing_guids(tmp_path):
    rows = [_row("frequency", language=SupportedLanguage.PL, rank=rank) for rank in (1, 1001, 2001)]
    result = export_anki_package(
        rows=rows, media_index=_media(tmp_path), output_path=tmp_path / "frequency.apkg",
        deck_name="Multilang Polish::Frequency",
    )
    with zipfile.ZipFile(result.output_path) as archive:
        collection = tmp_path / "collection.anki2"
        collection.write_bytes(archive.read("collection.anki2"))
    with sqlite3.connect(collection) as connection:
        decks = json.loads(connection.execute("select decks from col").fetchone()[0])
        actual = connection.execute("select notes.guid, cards.did from notes join cards on notes.id=cards.nid").fetchall()
    assert {decks[str(deck)]["name"] for _, deck in actual} == {
        f"Multilang Polish::Frequency::Level {level}" for level in (1, 2, 3)
    }
    assert {guid for guid, _ in actual} == {row.note_guid for row in rows}
