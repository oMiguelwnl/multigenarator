from __future__ import annotations

import csv
import json
import sqlite3
import zipfile
import pytest
from pathlib import Path

from multilang.domain.exporting import ExportArtifactFormat
from multilang.services.latin_audio import load_latin_audio_manifest
from multilang.services.latin_export import (
    LATIN_DECK_NAME,
    LATIN_EXPORT_FIELD_NAMES,
    LATIN_MODEL_ID,
    LATIN_NOTE_TYPE_NAME,
    LatinExportRow,
    build_latin_anki_model,
    build_latin_export_rows,
    export_latin_mvp_apkg,
    export_latin_mvp_bundle,
    write_latin_tabular_export,
)
from multilang.services.latin_review import load_latin_curated_records


def test_latin_export_field_order_excludes_classe() -> None:
    assert LATIN_EXPORT_FIELD_NAMES == (
        "SortIndex",
        "Latin Word",
        "Latin Sentence",
        "Lemma",
        "Translation",
        "Sentence Translation",
        "Gramatica",
        "Source",
        "word_audio",
        "sentence_audio",
        "Image",
    )
    forbidden = {"Classe", "class", "part_of_speech"}
    assert forbidden.isdisjoint(LATIN_EXPORT_FIELD_NAMES)


def test_latin_export_row_mapping_preserves_blank_image_and_no_classe() -> None:
    row = LatinExportRow(
        sort_index=1,
        item_key="latin-mvp-0001",
        latin_word="puella",
        latin_sentence="Puella legit.",
        lemma="puella",
        translation="menina",
        sentence_translation="A menina lê.",
        gramatica="subst Nominativus sg Suj",
        source="adapted_didactic | Multilang | latin-mvp-0001 | project-authored",
        word_audio="[sound:latin-mvp-0001-word.wav]",
        sentence_audio="[sound:latin-mvp-0001-sentence.wav]",
    )

    mapping = row.ordered_field_mapping()

    assert tuple(mapping) == LATIN_EXPORT_FIELD_NAMES
    assert mapping["Image"] == ""
    assert {"Classe", "class", "part_of_speech"}.isdisjoint(mapping)


def test_latin_export_row_rejects_nonblank_image() -> None:
    with pytest.raises(ValueError, match="Image must remain blank"):
        LatinExportRow(
            sort_index=1,
            item_key="latin-mvp-0001",
            latin_word="puella",
            latin_sentence="Puella legit.",
            lemma="puella",
            translation="menina",
            sentence_translation="A menina lê.",
            gramatica="subst Nominativus sg Suj",
            source="adapted_didactic | Multilang | latin-mvp-0001 | project-authored",
            word_audio="[sound:latin-mvp-0001-word.wav]",
            sentence_audio="[sound:latin-mvp-0001-sentence.wav]",
            image="not-blank",
        )


def test_build_latin_export_rows_from_committed_assets() -> None:
    bundle = build_latin_export_rows(repo_root=Path.cwd())

    assert len(bundle.rows) == 50
    assert [row.item_key for row in bundle.rows] == [f"latin-mvp-{index:04d}" for index in range(1, 51)]
    assert len(bundle.media_index) == 100

    first = bundle.rows[0]
    assert first.sort_index == 1
    assert first.item_key == "latin-mvp-0001"
    assert first.latin_word == "et"
    assert first.translation == "e"
    assert first.sentence_translation == "E o menino lê."
    assert first.word_audio == "[sound:latin-mvp-0001-word.wav]"
    assert first.sentence_audio == "[sound:latin-mvp-0001-sentence.wav]"
    assert bundle.media_index[first.word_audio] == Path("data/latin_mvp/audio/latin-mvp-50-v1/latin-mvp-0001-word.wav")
    assert bundle.media_index[first.sentence_audio] == Path("data/latin_mvp/audio/latin-mvp-50-v1/latin-mvp-0001-sentence.wav")
    assert "reference_example" in first.source
    assert "Multilang Latin MVP reference example set" in first.source
    assert "C:\\" not in first.source
    assert "/home/" not in first.source
    assert "AZURE_" not in first.source
    assert "OPENAI_" not in first.source
    assert "Classe" not in first.ordered_field_mapping()


def test_build_latin_export_rows_calls_fail_closed_validators() -> None:
    calls: list[str] = []

    def records_ready(records: object) -> None:
        calls.append("records")
        raise ValueError("latin_export_blocked item_key=latin-mvp-0001 gates=translation")

    with pytest.raises(ValueError, match="latin_export_blocked item_key=latin-mvp-0001"):
        build_latin_export_rows(records_ready_validator=records_ready)

    assert calls == ["records"]

    def audio_ready(manifest: object, *, repo_root: Path | None = None) -> None:
        calls.append(f"audio:{repo_root == Path.cwd()}")
        raise ValueError("latin_audio_export_blocked item_key=latin-mvp-0001 audio_kind=word")

    with pytest.raises(ValueError, match="latin_audio_export_blocked item_key=latin-mvp-0001"):
        build_latin_export_rows(
            repo_root=Path.cwd(),
            records_ready_validator=lambda records: calls.append("records-ok"),
            audio_ready_validator=audio_ready,
        )

    assert calls[-2:] == ["records-ok", "audio:True"]


def test_build_latin_export_rows_blocks_unapproved_translation_pack_status() -> None:
    from multilang.services.latin_translation_quality import load_latin_portuguese_translation_pack

    translation_pack = load_latin_portuguese_translation_pack()
    blocked_pack = translation_pack.model_copy(
        update={"entries": [translation_pack.entries[0].model_copy(update={"review_status": "needs_review"}), *translation_pack.entries[1:]]}
    )

    with pytest.raises(ValueError, match="unapproved_translation_entries=latin-mvp-0001"):
        build_latin_export_rows(
            repo_root=Path.cwd(),
            translation_pack_loader=lambda: blocked_pack,
        )


def test_build_latin_export_rows_detects_item_key_order_mismatch() -> None:
    curated_records = load_latin_curated_records()
    reversed_records = list(reversed(curated_records))

    with pytest.raises(ValueError, match="curation item_key order mismatch"):
        build_latin_export_rows(
            repo_root=Path.cwd(),
            curated_records_loader=lambda: reversed_records,
        )

    audio_manifest = load_latin_audio_manifest()
    reversed_manifest = audio_manifest.model_copy(update={"artifacts": list(reversed(audio_manifest.artifacts))})
    with pytest.raises(ValueError, match="audio item_key order mismatch"):
        build_latin_export_rows(
            repo_root=Path.cwd(),
            audio_manifest_loader=lambda: reversed_manifest,
            audio_ready_validator=lambda manifest, *, repo_root=None: None,
        )


def test_latin_apkg_export_writes_dedicated_model_notes_and_media(tmp_path: Path) -> None:
    bundle = build_latin_export_rows(repo_root=Path.cwd())
    result = export_latin_mvp_apkg(bundle=bundle, output_path=tmp_path / "latin.apkg", repo_root=Path.cwd())

    assert result.output_path.exists()
    assert result.card_count == 50
    assert result.media_count == 100
    assert result.note_type_name == LATIN_NOTE_TYPE_NAME

    with zipfile.ZipFile(result.output_path) as archive:
        names = archive.namelist()
        assert "collection.anki2" in names
        assert "media" in names
        media_manifest = json.loads(archive.read("media").decode("utf-8"))
        assert len(media_manifest) == 100
        assert "latin-mvp-0001-word.wav" in set(media_manifest.values())
        collection_path = tmp_path / "collection.anki2"
        collection_path.write_bytes(archive.read("collection.anki2"))

    with sqlite3.connect(collection_path) as connection:
        note_count = connection.execute("select count(*) from notes").fetchone()[0]
        models = json.loads(connection.execute("select models from col").fetchone()[0])
        fields = connection.execute("select flds from notes order by id limit 1").fetchone()[0].split("\x1f")

    assert note_count == 50
    latin_model = models[str(LATIN_MODEL_ID)]
    assert latin_model["name"] == LATIN_NOTE_TYPE_NAME
    assert [field["name"] for field in latin_model["flds"]] == list(LATIN_EXPORT_FIELD_NAMES)
    assert fields[1] == "et"
    assert fields[4] == "e"
    assert fields[8] == "[sound:latin-mvp-0001-word.wav]"
    assert fields[10] == ""
    assert "Classe" not in latin_model["tmpls"][0]["qfmt"] + latin_model["tmpls"][0]["afmt"]


def test_latin_tabular_exports_use_anki_headers_and_stable_fields(tmp_path: Path) -> None:
    bundle = build_latin_export_rows(repo_root=Path.cwd())
    csv_result = write_latin_tabular_export(bundle=bundle, export_format=ExportArtifactFormat.CSV, output_dir=tmp_path)
    tsv_result = write_latin_tabular_export(bundle=bundle, export_format=ExportArtifactFormat.TSV, output_dir=tmp_path)

    csv_lines = csv_result.output_path.read_text(encoding="utf-8").splitlines()
    tsv_lines = tsv_result.output_path.read_text(encoding="utf-8").splitlines()

    assert csv_lines[:5] == [
        "#separator:Comma",
        "#html:true",
        f"#notetype:{LATIN_NOTE_TYPE_NAME}",
        f"#deck:{LATIN_DECK_NAME}",
        "#columns:" + ",".join(LATIN_EXPORT_FIELD_NAMES),
    ]
    assert tsv_lines[:5] == [
        "#separator:Tab",
        "#html:true",
        f"#notetype:{LATIN_NOTE_TYPE_NAME}",
        f"#deck:{LATIN_DECK_NAME}",
        "#columns:" + "\t".join(LATIN_EXPORT_FIELD_NAMES),
    ]
    parsed_csv = list(csv.reader(csv_lines[5:]))[0]
    parsed_tsv = list(csv.reader(tsv_lines[5:], delimiter="\t"))[0]
    assert parsed_csv[1:6] == ["et", "Et puer legit.", "et", "e", "E o menino lê."]
    assert parsed_tsv[8:11] == ["[sound:latin-mvp-0001-word.wav]", "[sound:latin-mvp-0001-sentence.wav]", ""]
    assert csv_result.card_count == 50
    assert tsv_result.card_count == 50


def test_export_latin_mvp_bundle_routes_all_formats(tmp_path: Path) -> None:
    apkg = export_latin_mvp_bundle(export_format=ExportArtifactFormat.APKG, output_dir=tmp_path, repo_root=Path.cwd())
    csv_export = export_latin_mvp_bundle(export_format=ExportArtifactFormat.CSV, output_dir=tmp_path, repo_root=Path.cwd())
    tsv_export = export_latin_mvp_bundle(export_format=ExportArtifactFormat.TSV, output_dir=tmp_path, repo_root=Path.cwd())

    assert apkg.output_path.name == "latin-mvp-50.apkg"
    assert csv_export.output_path.name == "latin-mvp-50.csv"
    assert tsv_export.output_path.name == "latin-mvp-50.tsv"
    assert apkg.media_count == 100
    assert csv_export.media_count == 0


def test_build_latin_anki_model_is_dedicated_to_latin_fields() -> None:
    model = build_latin_anki_model()

    assert model.name == LATIN_NOTE_TYPE_NAME
    assert [field["name"] for field in model.fields] == list(LATIN_EXPORT_FIELD_NAMES)
    assert "Latin Word" in model.templates[0]["qfmt"]
    assert "Classe" not in model.templates[0]["qfmt"] + model.templates[0]["afmt"]
