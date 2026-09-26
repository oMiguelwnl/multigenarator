import pytest

from multilang.domain.exporting import ExportCardIdentity, ExportCardRow
from multilang.domain.jobs import SupportedLanguage
from multilang.services.card_template_loader import load_card_template, validate_template_references
from multilang.services.exporting.package import build_multilang_model as build_model


def test_japanese_highlights_have_readings_and_their_own_model_without_translation():
    names = ExportCardRow.field_names(language="ja", source_type="kindle-highlights")
    assert names == ("SortIndex", "Target Word", "Word Reading", "Word Romaji", "Definition",
                     "Sentence", "Sentence Furigana", "Sentence Romaji", "word_audio", "sentence_audio", "Image")
    template = load_card_template("kindle-highlights", language=SupportedLanguage.JA)
    validate_template_references(template, names)
    assert "{{furigana:Sentence Furigana}}" in template.back
    assert "{{Sentence Romaji}}" in template.back
    assert "{{Sentence Romaji}}" not in template.front
    japanese = build_model(source_type="kindle-highlights", language=SupportedLanguage.JA)
    generic = build_model(source_type="kindle-highlights", language=SupportedLanguage.EN)
    frequency = build_model(source_type="frequency", language=SupportedLanguage.JA)
    assert len({japanese.model_id, generic.model_id, frequency.model_id}) == 3
    assert [field["name"] for field in japanese.fields] == list(names)


def test_japanese_highlights_reject_missing_readings_and_keep_guid_stable():
    identity = ExportCardIdentity(language="ja", source_type="kindle-highlights", job_id="pilot",
                                  item_key="school", lemma_key="school", sort_index=1)
    payload = dict(identity=identity, word="学校", front_of_card="学校", definitions="school",
                   example_sentence="学校に行く。")
    with pytest.raises(ValueError, match="Japanese.*require"):
        ExportCardRow(**payload)
    payload.update(word_reading="学校[がっこう]", word_romaji="Gakkou",
                   sentence_furigana="学校[がっこう]に行[い]く。", sentence_romaji="Gakkou ni iku.")
    first = ExportCardRow(**payload)
    second = ExportCardRow(**{**payload, "definitions": "a place for learning"})
    assert first.note_guid == second.note_guid
    assert "Sentence Translation" not in first.ordered_field_mapping()


def test_non_japanese_highlight_fields_are_unchanged():
    assert ExportCardRow.field_names(language="en", source_type="kindle-highlights") == (
        "SortIndex", "Word", "IPA", "Example Sentence", "sentence_audio", "Definition", "Image")


def test_japanese_highlight_apkg_and_tsv_have_identical_fields(tmp_path):
    import csv
    import json
    import sqlite3
    import zipfile

    from support.audio import SILENT_MP3

    from multilang.domain.exporting import ExportArtifactFormat
    from multilang.services.export_anki_package import export_anki_package
    from multilang.services.export_tabular_bundle import write_export_tabular_bundle
    row = ExportCardRow(identity=ExportCardIdentity(language="ja", source_type="kindle-highlights",
        job_id="synthetic", item_key="school", lemma_key="school", sort_index=1),
        word="学校", front_of_card="学校", definitions="school", example_sentence="学校に行く。",
        word_reading="学校[がっこう]", word_romaji="Gakkou", sentence_furigana="学校[がっこう]に行[い]く。",
        sentence_romaji="Gakkou ni iku.", word_audio="[sound:word.mp3]", sentence_audio="[sound:sentence.mp3]")
    media = {}
    for name in ("word.mp3", "sentence.mp3"):
        path = tmp_path / name
        path.write_bytes(SILENT_MP3)
        media[f"[sound:{name}]"] = path
    output = tmp_path / "deck.apkg"
    export_anki_package(rows=[row], media_index=media, output_path=output, deck_name="Synthetic Japanese highlights")
    with zipfile.ZipFile(output) as package:
        database = tmp_path / "collection.anki2"
        database.write_bytes(package.read("collection.anki2"))
        assert set(json.loads(package.read("media")).values()) == {path.name for path in media.values()}
    with sqlite3.connect(database) as connection:
        guid, fields = connection.execute("select guid, flds from notes").fetchone()
        models = json.loads(connection.execute("select models from col").fetchone()[0])
    assert guid == row.note_guid
    model = next(iter(models.values()))
    assert len(model["flds"]) == 11
    tabular = write_export_tabular_bundle(rows=[row], export_format=ExportArtifactFormat.TSV,
        output_dir=tmp_path / "tsv", deck_name="Synthetic Japanese highlights", note_type_name=model["name"])
    with tabular.output_path.open() as handle:
        data = list(csv.reader((line for line in handle if not line.startswith("#")), delimiter="\t"))
    assert data == [fields.split("\x1f")]
