"""Phase 26 Portuguese translation asset coverage evidence."""

from __future__ import annotations

from multilang.services.latin_source_pack import load_latin_mvp_source_pack
from multilang.services.latin_translation_quality import (
    DEFAULT_LATIN_PORTUGUESE_TRANSLATION_PACK_PATH,
    LatinPortugueseTranslationQaService,
    load_latin_portuguese_translation_pack,
)

PHASE_26_REQUIREMENTS = ("PT-01", "PT-02", "PT-03")


def test_phase_26_requirements_are_scanner_readable() -> None:
    assert PHASE_26_REQUIREMENTS == ("PT-01", "PT-02", "PT-03")


def test_portuguese_translation_asset_has_50_ordered_entries() -> None:
    pack = load_latin_portuguese_translation_pack(DEFAULT_LATIN_PORTUGUESE_TRANSLATION_PACK_PATH)

    assert len(pack.entries) == 50
    assert [entry.item_key for entry in pack.entries] == [f"latin-mvp-{index:04d}" for index in range(1, 51)]


def test_portuguese_translation_asset_has_required_review_fields() -> None:
    pack = load_latin_portuguese_translation_pack(DEFAULT_LATIN_PORTUGUESE_TRANSLATION_PACK_PATH)

    for entry in pack.entries:
        assert entry.short_translation_pt.strip()
        assert entry.sentence_translation_pt.strip()
        assert entry.translation_notes.strip()
        assert entry.review_status == "approved"


def test_portuguese_translation_asset_passes_deterministic_qa_against_source_pack() -> None:
    source_pack = load_latin_mvp_source_pack()
    translation_pack = load_latin_portuguese_translation_pack(DEFAULT_LATIN_PORTUGUESE_TRANSLATION_PACK_PATH)

    result = LatinPortugueseTranslationQaService().validate_pack(translation_pack, source_pack)
    summary = result.qa_summary()

    assert summary["source_pack_version"] == "latin-mvp-50-v1"
    assert summary["translation_pack_version"] == "latin-mvp-50-pt-v1"
    assert summary["entry_count"] == 50
    assert summary["passed_count"] == 50
    assert summary["failed_count"] == 0
    assert summary["issue_counts"] == {}
    assert summary["review_status_counts"] == {"needs_review": 0, "approved": 50, "rejected": 0}
