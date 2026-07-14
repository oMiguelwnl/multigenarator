"""Integration validation for the committed Latin MVP 50-entry source pack."""

from __future__ import annotations

import json
import re
from pathlib import Path

from multilang.services.latin_source_pack import load_latin_mvp_source_pack


FORBIDDEN_MARKERS = ("TBD", "placeholder", "future", "later", "hardcoded", "C:\\", "/Users/", "\\Users\\")


def test_committed_latin_source_pack_loads_in_manifest_order() -> None:
    pack = load_latin_mvp_source_pack()

    assert pack.source_pack_version == "latin-mvp-50-v1"
    assert pack.card_count == 50
    assert [entry.sequence for entry in pack.entries] == list(range(1, 51))
    assert [entry.item_key for entry in pack.entries] == [f"latin-mvp-{index:04d}" for index in range(1, 51)]


def test_committed_latin_source_pack_has_required_frequency_source_and_license_evidence() -> None:
    pack = load_latin_mvp_source_pack()

    assert "mylittlewordland" in pack.frequency_attribution
    assert "based on DCC" in pack.frequency_attribution
    assert "CC BY-SA" in pack.license_attribution
    for entry in pack.entries:
        assert entry.license_gate == "approved"
        assert entry.frequency_rank >= 1
        assert entry.frequency_source == "As mil palavras mais frequentes do latim (mylittlewordland)"
        assert str(entry.frequency_source_url).startswith("https://mylittlewordland.com/")
        assert entry.inclusion_rationale
        assert entry.didactic_order_rationale
        assert entry.source_type in {"original_classical", "adapted_didactic", "reference_example"}


def test_committed_latin_source_pack_contains_didactic_reorder_evidence() -> None:
    pack = load_latin_mvp_source_pack()

    assert any("reorder" in entry.didactic_order_rationale.casefold() for entry in pack.entries)
    assert any(entry.sequence != entry.frequency_rank for entry in pack.entries)
    assert {entry.inclusion_status for entry in pack.entries} <= {"included", "replacement", "deferred"}


def test_committed_latin_source_pack_has_no_placeholder_or_private_path_markers() -> None:
    payload = json.loads(Path("data/latin_mvp/latin-mvp-50-v1.json").read_text(encoding="utf-8"))
    serialized = json.dumps(payload, ensure_ascii=False)

    for marker in FORBIDDEN_MARKERS:
        assert marker.lower() not in serialized.lower()
    assert not re.search(r"[A-Z]:[\\/]", serialized)
    assert all(value != "" for entry in payload["entries"] for value in entry.values() if isinstance(value, str))


def test_adapted_didactic_rows_are_not_spoofed_as_original_citations() -> None:
    pack = load_latin_mvp_source_pack()

    adapted = [entry for entry in pack.entries if entry.source_type == "adapted_didactic"]
    assert adapted
    for entry in adapted:
        assert not entry.original_citation_claim
        assert "Project-authored didactic text" in entry.license_note
        assert "Project-authored" in entry.citation
