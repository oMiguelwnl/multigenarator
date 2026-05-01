"""Tests for cached Kaikki lookup."""

from __future__ import annotations

import gzip
import json
from pathlib import Path

from multilang.services.kaikki_lookup import KaikkiLookup


def test_has_index_reports_missing_and_present_language_index(tmp_path: Path) -> None:
    lookup = KaikkiLookup(data_dir=tmp_path)

    assert lookup.has_index(language_code="pt") is False

    source_path = _write_fixture_jsonl(
        tmp_path / "pt.jsonl.gz",
        [{"word": "lavar", "lang_code": "pt", "senses": [{"glosses": ["to wash"]}]}],
    )
    lookup.build_index(language_code="pt", source_path=source_path)

    assert lookup.has_index(language_code="pt") is True


def test_lookup_reads_fixture_index(tmp_path: Path) -> None:
    source_path = _write_fixture_jsonl(
        tmp_path / "pt.jsonl.gz",
        [
            {
                "word": "lavar",
                "lang_code": "pt",
                "sounds": [{"ipa": "/lɐˈvaɾ/"}],
                "senses": [{"glosses": ["to wash"]}],
            },
            {
                "word": "lavar-se",
                "lang_code": "pt",
                "forms": [{"form": "lavar-se", "tags": ["canonical"]}],
                "senses": [{"glosses": ["to wash oneself"]}],
            },
        ],
    )

    lookup = KaikkiLookup(data_dir=tmp_path)
    index_path = lookup.build_index(language_code="pt", source_path=source_path)
    record = lookup.lookup(language_code="pt", term="  LAVAR-SE  ")

    assert index_path.exists()
    assert record is not None
    assert record.lemma == "lavar-se"
    assert record.display_form == "lavar-se"
    assert record.definitions == ["to wash oneself"]
    assert record.ipa is None


def test_lookup_can_refresh_existing_index(tmp_path: Path) -> None:
    lookup = KaikkiLookup(data_dir=tmp_path)
    source_path = _write_fixture_jsonl(
        tmp_path / "es.jsonl.gz",
        [{"word": "casa", "lang_code": "es", "senses": [{"glosses": ["house"]}]}],
    )

    first_index = lookup.build_index(language_code="es", source_path=source_path)
    second_source_path = _write_fixture_jsonl(
        tmp_path / "es-refresh.jsonl.gz",
        [{"word": "casa", "lang_code": "es", "senses": [{"glosses": ["home"]}]}],
    )

    second_index = lookup.build_index(language_code="es", source_path=second_source_path, force_refresh=True)
    refreshed = lookup.lookup(language_code="es", term="casa")

    assert first_index == second_index
    assert refreshed is not None
    assert refreshed.definitions == ["home"]



def test_build_index_extracts_definition_metadata(tmp_path: Path) -> None:
    source_path = _write_fixture_jsonl(
        tmp_path / "es.jsonl.gz",
        [
            {
                "word": "lavar",
                "lang_code": "es",
                "pos": "verb",
                "forms": [{"form": "lavar", "tags": ["infinitive"]}],
                "senses": [{"glosses": ["to wash something or clean it with water"]}],
            },
        ],
    )

    lookup = KaikkiLookup(data_dir=tmp_path)
    lookup.build_index(language_code="es", source_path=source_path)
    record = lookup.lookup(language_code="es", term="lavar")

    assert record is not None
    assert record.definitions == ["to wash something or clean it with water"]
    assert record.part_of_speech == "verb"
    assert record.grammar_tags == ["infinitive"]


def test_build_index_prefers_more_explanatory_gloss(tmp_path: Path) -> None:
    source_path = _write_fixture_jsonl(
        tmp_path / "en.jsonl.gz",
        [
            {
                "word": "house",
                "lang_code": "en",
                "pos": "noun",
                "senses": [{"glosses": ["home", "a building where people live"]}],
            },
        ],
    )

    lookup = KaikkiLookup(data_dir=tmp_path)
    lookup.build_index(language_code="en", source_path=source_path)
    record = lookup.lookup(language_code="en", term="house")

    assert record is not None
    assert record.definitions == ["a building where people live"]
    assert record.part_of_speech == "noun"


def test_build_index_reuses_existing_index_until_force_refresh(tmp_path: Path) -> None:
    lookup = KaikkiLookup(data_dir=tmp_path)
    source_path = _write_fixture_jsonl(
        tmp_path / "de.jsonl.gz",
        [{"word": "haus", "lang_code": "de", "senses": [{"glosses": ["house"]}]}],
    )

    first_index = lookup.build_index(language_code="de", source_path=source_path)
    replacement_source = _write_fixture_jsonl(
        tmp_path / "de-refresh.jsonl.gz",
        [{"word": "haus", "lang_code": "de", "senses": [{"glosses": ["home"]}]}],
    )

    second_index = lookup.build_index(language_code="de", source_path=replacement_source)
    record = lookup.lookup(language_code="de", term="haus")

    assert first_index == second_index
    assert record is not None
    assert record.definitions == ["house"]


def _write_fixture_jsonl(path: Path, rows: list[dict[str, object]]) -> Path:
    with gzip.open(path, "wt", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False))
            handle.write("\n")
    return path
