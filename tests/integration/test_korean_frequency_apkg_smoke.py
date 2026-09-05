"""Fast representative Korean frequency APKG smoke gates.

These tests are intentionally synthetic and do not prove exact production scale.
"""

from __future__ import annotations

import json
import sqlite3
import zipfile
from pathlib import Path

import pytest

from multilang.domain.exporting import FREQUENCY_EXPORT_CARD_FIELD_NAMES, ExportCardIdentity, ExportCardRow
from multilang.domain.jobs import SupportedLanguage
from multilang.runtime import build_korean_frequency_synthetic_export_contract
from multilang.services.anki_id_registry import AnkiIdKind, registry_id
from multilang.services.export_anki_package import ExportAnkiPackageError, export_anki_package


_BUNDLE_SHA256 = "a" * 64
_EXPORT_GATE_SHA256 = "b" * 64
_TEXT_REVIEW_SHA256 = "c" * 64
_WORD_AUDIO_SHA256 = "d" * 64
_SENTENCE_AUDIO_SHA256 = "e" * 64


def _write_media(path: Path, payload: bytes) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return path


def _make_smoke_row(*, level: int, ordinal: int) -> ExportCardRow:
    rank = (level - 1) * 1000 + ordinal
    item_key = f"synthetic-ko-l{level}-{ordinal}"
    return ExportCardRow(
        identity=ExportCardIdentity(
            language=SupportedLanguage.KO,
            source_type="frequency",
            job_id="job-ko-smoke",
            item_key=item_key,
            lemma_key=f"ko:synthetic:{level}:{ordinal}",
            sort_index=rank,
        ),
        sort_index=rank,
        frequency_level=level,
        frequency_bundle_sha256=_BUNDLE_SHA256,
        export_gate_receipt_sha256=_EXPORT_GATE_SHA256,
        text_review_receipt_sha256=_TEXT_REVIEW_SHA256,
        word_audio_artifact_sha256=_WORD_AUDIO_SHA256,
        sentence_audio_artifact_sha256=_SENTENCE_AUDIO_SHA256,
        word=f"합성어{level}{ordinal}",
        front_of_card=f"합성어{level}{ordinal}",
        ipa=f"/synthetic-{level}-{ordinal}/",
        definitions="substantivo: fixture sintetica",
        example_sentence=f"합성어{level}{ordinal}을 봐요.",
        translation="Eu vejo o item sintetico.",
        word_audio=f"[sound:{item_key}-word.mp3]",
        sentence_audio=f"[sound:{item_key}-sentence.mp3]",
    )


def _media_index(tmp_path: Path, rows: list[ExportCardRow]) -> dict[str, Path]:
    media: dict[str, Path] = {}
    for row in rows:
        key = row.identity.item_key
        media[row.word_audio] = _write_media(tmp_path / "media" / f"{key}-word.mp3", b"ID3-word")
        media[row.sentence_audio] = _write_media(
            tmp_path / "media" / f"{key}-sentence.mp3",
            b"ID3-sentence",
        )
    return media


def test_fast_three_level_apkg_smoke_does_not_claim_exact_counts(tmp_path: Path) -> None:
    contract = build_korean_frequency_synthetic_export_contract(cards_per_level=2, exact_scale=False)
    rows = [_make_smoke_row(level=level, ordinal=ordinal) for level in (1, 2, 3) for ordinal in (1, 2)]
    output_path = tmp_path / "korean-frequency-smoke.apkg"

    result = export_anki_package(
        rows=rows,
        media_index=_media_index(tmp_path, rows),
        output_path=output_path,
        deck_name="Multilang Korean::Synthetic Smoke",
        cards_per_level=contract.cards_per_level,
        expected_items=contract.expected_items,
    )

    assert contract.claim_limit == "fast-representative-only"
    assert contract.level_counts == {1: 2, 2: 2, 3: 2}
    assert contract.expected_items == 6
    assert contract.expected_word_assets == 6
    assert contract.expected_sentence_assets == 6
    assert contract.expected_media_files == 12
    assert not contract.production_count_evidence
    assert result.card_count == 6

    level_deck_ids = {
        level: registry_id(family="korean_frequency", role=f"level_{level}_deck", kind=AnkiIdKind.DECK)
        for level in (1, 2, 3)
    }
    parent_deck_id = registry_id(family="korean_frequency", role="parent_deck", kind=AnkiIdKind.DECK)
    model_id = registry_id(family="korean_frequency", role="model", kind=AnkiIdKind.MODEL)

    with zipfile.ZipFile(output_path) as archive:
        media_manifest = json.loads(archive.read("media").decode("utf-8"))
        assert sorted(media_manifest.values()) == sorted(
            f"{row.identity.item_key}-{kind}.mp3" for row in rows for kind in ("word", "sentence")
        )
        collection_path = tmp_path / "smoke-collection.anki2"
        collection_path.write_bytes(archive.read("collection.anki2"))

    with sqlite3.connect(collection_path) as connection:
        models = json.loads(connection.execute("select models from col").fetchone()[0])
        decks = json.loads(connection.execute("select decks from col").fetchone()[0])
        card_rows = connection.execute(
            "select cards.did, notes.guid, notes.flds, notes.tags "
            "from cards join notes on notes.id = cards.nid"
        ).fetchall()

    assert decks[str(parent_deck_id)]["name"] == "Multilang Korean::Synthetic Smoke"
    assert decks[str(level_deck_ids[1])]["name"] == "Multilang Korean::Synthetic Smoke::Level 1"
    assert decks[str(level_deck_ids[2])]["name"] == "Multilang Korean::Synthetic Smoke::Level 2"
    assert decks[str(level_deck_ids[3])]["name"] == "Multilang Korean::Synthetic Smoke::Level 3"
    assert models[str(model_id)]["name"] == "Multilang::Card"
    assert tuple(field["name"] for field in models[str(model_id)]["flds"]) == FREQUENCY_EXPORT_CARD_FIELD_NAMES

    rows_by_guid = {row.note_guid: row for row in rows}
    assert set(rows_by_guid) == {guid for _deck_id, guid, _fields, _tags in card_rows}
    for deck_id, guid, fields, tags in card_rows:
        row = rows_by_guid[guid]
        assert deck_id == level_deck_ids[row.frequency_level]
        assert fields.split("\x1f")[-1] == ""
        assert _BUNDLE_SHA256 not in fields
        assert f" level_{row.frequency_level} " in tags
        assert f" rank_{row.sort_index:04d} " in tags

    sentinel_path = tmp_path / "korean-frequency-smoke-sentinel.apkg"
    sentinel_path.write_bytes(b"sentinel")
    bad_rows = [rows[0].model_copy(update={"text_review_receipt_sha256": None}), *rows[1:]]
    with pytest.raises(ExportAnkiPackageError, match="text_review_receipt_sha256"):
        export_anki_package(
            rows=bad_rows,
            media_index=_media_index(tmp_path, bad_rows),
            output_path=sentinel_path,
            deck_name="Multilang Korean::Synthetic Smoke",
            cards_per_level=contract.cards_per_level,
            expected_items=contract.expected_items,
        )
    assert sentinel_path.read_bytes() == b"sentinel"
