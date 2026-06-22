"""Scanner-readable Phase 28 Latin export evidence over committed assets."""

from __future__ import annotations

import csv
import json
import sqlite3
import zipfile
from pathlib import Path

from multilang.domain.exporting import ExportArtifactFormat
from multilang.services.latin_audio import load_latin_audio_manifest
from multilang.services.latin_export import (
    LATIN_EXPORT_FIELD_NAMES,
    LATIN_MODEL_ID,
    LATIN_NOTE_TYPE_NAME,
    build_latin_export_rows,
    export_latin_mvp_bundle,
)


PHASE_28_EXPORT_REQUIREMENTS = ("EXP-01", "EXP-02", "EXP-03")
REPO_ROOT = Path(__file__).resolve().parents[2]


def _assert_public_text(value: str) -> None:
    assert "C:\\" not in value
    assert "/Users/" not in value
    assert "/home/" not in value
    assert ".." not in value
    assert "AZURE_" not in value
    assert "OPENAI_" not in value
    assert "api_key" not in value.lower()


def test_phase_28_export_requirements_are_scanner_readable() -> None:
    assert PHASE_28_EXPORT_REQUIREMENTS == ("EXP-01", "EXP-02", "EXP-03")


def test_committed_latin_export_bundle_has_50_safe_rows_and_100_media_refs() -> None:
    bundle = build_latin_export_rows(repo_root=REPO_ROOT)
    audio_manifest = load_latin_audio_manifest()

    assert len(bundle.rows) == 50
    assert [row.item_key for row in bundle.rows] == [f"latin-mvp-{index:04d}" for index in range(1, 51)]
    assert len(bundle.media_index) == 100
    assert sum(1 for pair in audio_manifest.artifacts for artifact in (pair.word, pair.sentence) if artifact.provider == "google-translate-tts") == 100
    assert {artifact.voice for pair in audio_manifest.artifacts for artifact in (pair.word, pair.sentence)} == {"la"}
    assert {artifact.provider_version for pair in audio_manifest.artifacts for artifact in (pair.word, pair.sentence)} == {
        "google-translate-tts-la"
    }
    for row in bundle.rows:
        mapping = row.ordered_field_mapping()
        assert tuple(mapping) == LATIN_EXPORT_FIELD_NAMES
        assert mapping["Image"] == ""
        assert {"Classe", "class", "part_of_speech", "Translation", "Lemma", "Source"}.isdisjoint(mapping)
        assert row.word_audio.startswith("[sound:latin-mvp-")
        assert row.sentence_audio.startswith("[sound:latin-mvp-")
        assert not hasattr(row, "translation")
        assert not hasattr(row, "lemma")
        assert not hasattr(row, "source")
    for sound_tag, media_path in bundle.media_index.items():
        assert sound_tag.startswith("[sound:")
        assert not media_path.is_absolute()
        assert (REPO_ROOT / media_path).exists()


def test_latin_exports_write_importable_apkg_csv_and_tsv(tmp_path: Path) -> None:
    apkg = export_latin_mvp_bundle(export_format=ExportArtifactFormat.APKG, output_dir=tmp_path, repo_root=REPO_ROOT)
    csv_export = export_latin_mvp_bundle(export_format=ExportArtifactFormat.CSV, output_dir=tmp_path, repo_root=REPO_ROOT)
    tsv_export = export_latin_mvp_bundle(export_format=ExportArtifactFormat.TSV, output_dir=tmp_path, repo_root=REPO_ROOT)

    assert apkg.card_count == 50
    assert apkg.media_count == 100
    assert csv_export.card_count == 50
    assert tsv_export.card_count == 50

    with zipfile.ZipFile(apkg.output_path) as archive:
        assert "collection.anki2" in archive.namelist()
        assert "media" in archive.namelist()
        media_manifest = json.loads(archive.read("media").decode("utf-8"))
        assert len(media_manifest) == 100
        assert sorted(media_manifest.values())[0] == "latin-mvp-0001-sentence.mp3"
        collection_path = tmp_path / "collection.anki2"
        collection_path.write_bytes(archive.read("collection.anki2"))
    with sqlite3.connect(collection_path) as connection:
        note_count = connection.execute("select count(*) from notes").fetchone()[0]
        models = json.loads(connection.execute("select models from col").fetchone()[0])
    assert note_count == 50
    assert models[str(LATIN_MODEL_ID)]["name"] == LATIN_NOTE_TYPE_NAME

    csv_lines = csv_export.output_path.read_text(encoding="utf-8").splitlines()
    tsv_lines = tsv_export.output_path.read_text(encoding="utf-8").splitlines()
    assert csv_lines[:5] == [
        "#separator:Comma",
        "#html:true",
        f"#notetype:{LATIN_NOTE_TYPE_NAME}",
        "#deck:Multilang::Classical Latin::MVP 50",
        "#columns:" + ",".join(LATIN_EXPORT_FIELD_NAMES),
    ]
    assert tsv_lines[4] == "#columns:" + "\t".join(LATIN_EXPORT_FIELD_NAMES)
    csv_fields = csv_lines[4].removeprefix("#columns:").split(",")
    tsv_fields = tsv_lines[4].removeprefix("#columns:").split("\t")
    assert {"Translation", "Lemma", "Source"}.isdisjoint(csv_fields)
    assert {"Translation", "Lemma", "Source"}.isdisjoint(tsv_fields)
    assert len(list(csv.reader(csv_lines[5:]))) == 50
    assert len(list(csv.reader(tsv_lines[5:], delimiter="\t"))) == 50
