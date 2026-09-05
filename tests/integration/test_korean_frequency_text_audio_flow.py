"""Synthetic Korean frequency text/audio/APKG scale gates.

The exact-scale gate is synthetic evidence only; it does not prove production content,
provider execution, or human/auditory acceptance.
"""

from __future__ import annotations

import json
import sqlite3
import warnings
import zipfile
from pathlib import Path

import pytest

from multilang.domain.exporting import FREQUENCY_EXPORT_CARD_FIELD_NAMES, ExportCardIdentity, ExportCardRow
from multilang.domain.jobs import SupportedLanguage
from multilang.runtime import build_korean_frequency_synthetic_manifest_shape
from multilang.services.anki_id_registry import AnkiIdKind, registry_id
from multilang.services.export_anki_package import export_anki_package


with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=pytest.PytestUnknownMarkWarning)
    _SLOW = pytest.mark.slow


_BUNDLE_SHA256 = "a" * 64
_EXPORT_GATE_SHA256 = "b" * 64
_TEXT_REVIEW_SHA256 = "c" * 64
_WORD_AUDIO_SHA256 = "d" * 64
_SENTENCE_AUDIO_SHA256 = "e" * 64


def _make_scale_row(*, level: int, ordinal: int) -> ExportCardRow:
    rank = (level - 1) * 1000 + ordinal
    item_key = f"synthetic-ko-exact-{rank:04d}"
    return ExportCardRow(
        identity=ExportCardIdentity(
            language=SupportedLanguage.KO,
            source_type="frequency",
            job_id="job-ko-exact-scale",
            item_key=item_key,
            lemma_key=f"ko:synthetic:exact:{rank:04d}",
            sort_index=rank,
        ),
        sort_index=rank,
        frequency_level=level,
        frequency_bundle_sha256=_BUNDLE_SHA256,
        export_gate_receipt_sha256=_EXPORT_GATE_SHA256,
        text_review_receipt_sha256=_TEXT_REVIEW_SHA256,
        word_audio_artifact_sha256=_WORD_AUDIO_SHA256,
        sentence_audio_artifact_sha256=_SENTENCE_AUDIO_SHA256,
        word=f"합성어{rank:04d}",
        front_of_card=f"합성어{rank:04d}",
        ipa=f"/synthetic-{rank:04d}/",
        definitions="substantivo: fixture sintetica",
        example_sentence=f"합성어{rank:04d}을 봐요.",
        translation="Eu vejo o item sintetico.",
        word_audio=f"[sound:{item_key}-word.mp3]",
        sentence_audio=f"[sound:{item_key}-sentence.mp3]",
    )


def _write_exact_media(tmp_path: Path, rows: list[ExportCardRow]) -> dict[str, Path]:
    media: dict[str, Path] = {}
    media_root = tmp_path / "media"
    for row in rows:
        key = row.identity.item_key
        word_path = media_root / f"{key}-word.mp3"
        sentence_path = media_root / f"{key}-sentence.mp3"
        word_path.parent.mkdir(parents=True, exist_ok=True)
        word_path.write_bytes(b"ID3-word")
        sentence_path.write_bytes(b"ID3-sentence")
        media[row.word_audio] = word_path
        media[row.sentence_audio] = sentence_path
    return media


def test_exact_scale_contract_builds_expected_manifest_shape_without_export() -> None:
    shape = build_korean_frequency_synthetic_manifest_shape(cards_per_level=1000)

    assert shape.contract.exact_scale_evidence
    assert shape.contract.claim_limit == "synthetic-exact-scale-only"
    assert shape.contract.expected_items == 3000
    assert shape.contract.expected_media_files == 6000
    assert not shape.contract.production_count_evidence
    assert shape.level_counts == {1: 1000, 2: 1000, 3: 1000}
    assert [shape.items[index].rank for index in (0, 999, 1000, 1999, 2000, 2999)] == [
        1,
        1000,
        1001,
        2000,
        2001,
        3000,
    ]
    assert [shape.items[index].level for index in (0, 999, 1000, 1999, 2000, 2999)] == [1, 1, 2, 2, 3, 3]
    assert len({item.item_key for item in shape.items}) == 3000
    assert len({item.lemma_key for item in shape.items}) == 3000
    media_names = {name for item in shape.items for name in (item.word_audio_name, item.sentence_audio_name)}
    assert len(media_names) == 6000
    assert "frequency_level" in shape.blocked_mutation_fields
    assert "word_audio_artifact_sha256" in shape.blocked_mutation_fields
    assert "sentence_audio_artifact_sha256" in shape.blocked_mutation_fields


@_SLOW
def test_slow_exact_3000_cards_6000_assets_parent_three_children(tmp_path: Path) -> None:
    rows = [_make_scale_row(level=level, ordinal=ordinal) for level in (1, 2, 3) for ordinal in range(1, 1001)]
    output_path = tmp_path / "korean-frequency-exact-scale.apkg"

    result = export_anki_package(
        rows=rows,
        media_index=_write_exact_media(tmp_path, rows),
        output_path=output_path,
        deck_name="Multilang Korean::Synthetic Exact Scale",
        cards_per_level=1000,
        expected_items=3000,
    )

    assert result.card_count == 3000
    with zipfile.ZipFile(output_path) as archive:
        media_manifest = json.loads(archive.read("media").decode("utf-8"))
        assert len(media_manifest) == 6000
        assert set(media_manifest.values()) == {
            f"{row.identity.item_key}-{kind}.mp3" for row in rows for kind in ("word", "sentence")
        }
        collection_path = tmp_path / "exact-scale-collection.anki2"
        collection_path.write_bytes(archive.read("collection.anki2"))

    level_deck_ids = {
        level: registry_id(family="korean_frequency", role=f"level_{level}_deck", kind=AnkiIdKind.DECK)
        for level in (1, 2, 3)
    }
    model_id = registry_id(family="korean_frequency", role="model", kind=AnkiIdKind.MODEL)
    expected_guids = {row.note_guid for row in rows}
    with sqlite3.connect(collection_path) as connection:
        models = json.loads(connection.execute("select models from col").fetchone()[0])
        note_count = connection.execute("select count(*) from notes").fetchone()[0]
        card_count = connection.execute("select count(*) from cards").fetchone()[0]
        deck_counts = dict(connection.execute("select did, count(*) from cards group by did").fetchall())
        guids = {row[0] for row in connection.execute("select guid from notes").fetchall()}

    assert note_count == 3000
    assert card_count == 3000
    assert deck_counts == {level_deck_ids[1]: 1000, level_deck_ids[2]: 1000, level_deck_ids[3]: 1000}
    assert guids == expected_guids
    assert tuple(field["name"] for field in models[str(model_id)]["flds"]) == FREQUENCY_EXPORT_CARD_FIELD_NAMES
