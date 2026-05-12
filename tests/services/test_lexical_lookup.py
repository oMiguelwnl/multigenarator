"""Tests for cached lexical lookup."""

from __future__ import annotations

import json
from pathlib import Path

from multilang.services.lexical_lookup import LexicalLookup


def test_has_index_reports_missing_and_present_language_index(tmp_path: Path) -> None:
    lookup = LexicalLookup(data_dir=tmp_path)

    assert lookup.has_index(language_code="pt") is False

    _write_fixture_index(tmp_path, language_code="pt", rows={"lavar": _record("lavar")})

    assert lookup.has_index(language_code="pt") is True


def test_lookup_reads_fixture_index(tmp_path: Path) -> None:
    lookup = LexicalLookup(data_dir=tmp_path)
    index_path = _write_fixture_index(
        tmp_path,
        language_code="pt",
        rows={
            "lavar-se": _record(
                "lavar-se",
                definitions=["to wash oneself"],
                ipa=None,
            )
        },
    )

    record = lookup.lookup(language_code="pt", term="  LAVAR-SE  ")

    assert index_path.exists()
    assert record is not None
    assert record.lemma == "lavar-se"
    assert record.display_form == "lavar-se"
    assert record.definitions == ["to wash oneself"]
    assert record.ipa is None
    assert record.source == "manual"


def _record(term: str, *, definitions: list[str] | None = None, ipa: str | None = "/term/") -> dict[str, object]:
    return {
        "term": term,
        "display_form": term,
        "lemma": term,
        "definitions": definitions or [f"definition for {term}"],
        "ipa": ipa,
        "source": "manual",
    }


def _write_fixture_index(tmp_path: Path, *, language_code: str, rows: dict[str, dict[str, object]]) -> Path:
    index_path = tmp_path / language_code / "lexical-index.json"
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(json.dumps(rows, indent=2, sort_keys=True), encoding="utf-8")
    return index_path
