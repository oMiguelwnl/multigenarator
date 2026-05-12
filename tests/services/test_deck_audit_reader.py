"""Tests for read-only APKG audit extraction."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import sqlite3
import zipfile

import pytest

from multilang.domain.exporting import ExportCardIdentity, ExportCardRow
from multilang.domain.jobs import SupportedLanguage
from multilang.services.deck_audit_reader import read_apkg_cards
from multilang.services.export_anki_package import export_anki_package


def write_media_file(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"ID3-audio")
    return path


def make_row(*, item_key: str = "run", sort_index: int = 1, definitions: str = "verb: to run") -> ExportCardRow:
    return ExportCardRow(
        identity=ExportCardIdentity(
            language=SupportedLanguage.EN,
            source_type="frequency",
            job_id="job-audit",
            item_key=item_key,
            lemma_key=f"en:{item_key}",
            sort_index=sort_index,
        ),
        word=item_key,
        front_of_card=item_key,
        ipa=f"/{item_key}/",
        definitions=definitions,
        example_sentence=f"I {item_key} today.",
        translation=f"Eu {item_key} hoje.",
        word_audio="[sound:word.mp3]",
        sentence_audio="[sound:sentence.mp3]",
    )


def make_apkg(tmp_path: Path, *, definitions: str = "verb: to run") -> Path:
    row = make_row(definitions=definitions)
    word_media = write_media_file(tmp_path / "audio" / "word.mp3")
    sentence_media = write_media_file(tmp_path / "audio" / "sentence.mp3")
    output_path = tmp_path / "deck.apkg"
    export_anki_package(
        rows=[row],
        media_index={row.word_audio: word_media, row.sentence_audio: sentence_media},
        output_path=output_path,
        deck_name="Audit Deck",
    )
    return output_path


def test_reads_synthetic_apkg_notes_into_audit_cards(tmp_path: Path) -> None:
    apkg_path = make_apkg(tmp_path, definitions="noun: genitive/dative/prepositional singular")

    result = read_apkg_cards(apkg_path)

    assert result.source_path_name == "deck.apkg"
    assert result.card_count == 1
    assert result.input_sha256 == sha256(apkg_path.read_bytes()).hexdigest()
    card = result.cards[0]
    assert card.model_name == "Multilang::Card"
    assert card.sort_index == "1"
    assert card.fields["word"] == "run"
    assert card.fields["Definitions"] == "noun: genitive/dative/prepositional singular"
    assert card.card_identifier


def test_reading_apkg_does_not_mutate_source_bytes(tmp_path: Path) -> None:
    apkg_path = make_apkg(tmp_path)
    before = sha256(apkg_path.read_bytes()).hexdigest()

    read_apkg_cards(apkg_path)

    assert sha256(apkg_path.read_bytes()).hexdigest() == before
    assert list(tmp_path.glob("collection.anki2")) == []


def test_rejects_apkg_missing_collection_without_sidecar_writes(tmp_path: Path) -> None:
    apkg_path = tmp_path / "broken.apkg"
    with zipfile.ZipFile(apkg_path, "w") as archive:
        archive.writestr("media", "{}")

    with pytest.raises(ValueError, match="collection.anki2"):
        read_apkg_cards(apkg_path)

    assert list(tmp_path.glob("collection.anki2")) == []


def test_rejects_missing_models_and_note_rows(tmp_path: Path) -> None:
    collection_path = tmp_path / "collection.anki2"
    with sqlite3.connect(collection_path) as connection:
        connection.execute("create table col (models text)")
        connection.execute("insert into col values ('{}')")
        connection.execute("create table notes (id integer, guid text, mid integer, flds text)")
    apkg_path = tmp_path / "missing-model.apkg"
    with zipfile.ZipFile(apkg_path, "w") as archive:
        archive.write(collection_path, "collection.anki2")

    with pytest.raises(ValueError, match="no note rows"):
        read_apkg_cards(apkg_path)


def test_rejects_path_traversal_archive_entry(tmp_path: Path) -> None:
    apkg_path = tmp_path / "traversal.apkg"
    with zipfile.ZipFile(apkg_path, "w") as archive:
        archive.writestr("../collection.anki2", b"bad")

    with pytest.raises(ValueError, match="path traversal"):
        read_apkg_cards(apkg_path)
