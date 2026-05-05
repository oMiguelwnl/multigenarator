from __future__ import annotations

from pathlib import Path

import pytest

from multilang.domain.highlights import (
    HighlightProvenance,
    KindleParseResult,
    NormalizedHighlight,
    RejectedHighlight,
)
from multilang.services.kindle_highlight_parser import parse_kindle_highlight_export


FIXTURE_DIR = Path(__file__).parents[1] / "fixtures" / "kindle_highlights"


def test_highlight_contracts_require_stable_ids_and_hashes() -> None:
    provenance = HighlightProvenance(
        source_path="local_export.html",
        source_format="html",
        source_index=1,
        raw_location="Location 12",
        content_hash="a" * 64,
    )
    highlight = NormalizedHighlight(
        highlight_id="html-1-" + "a" * 12,
        text="¡Buenos días! El niño abre la puerta—rápido.",
        provenance=provenance,
    )

    result = KindleParseResult(highlights=[highlight], rejected=[])

    assert result.highlights[0].highlight_id
    assert result.highlights[0].provenance.source_format == "html"
    assert len(result.highlights[0].provenance.content_hash) == 64


def test_rejected_contract_uses_explicit_reason_codes() -> None:
    rejected = RejectedHighlight(source_index=2, reason_code="empty", detail="empty highlight record")

    assert rejected.reason_code == "empty"
    assert "private" not in rejected.detail.lower()


def test_synthetic_fixtures_are_learner_safe_and_unicode_rich() -> None:
    html_text = (FIXTURE_DIR / "local_export.html").read_text(encoding="utf-8")
    text_text = (FIXTURE_DIR / "local_export.txt").read_text(encoding="utf-8")

    combined = html_text + text_text
    assert "Kindle Formatter" not in combined
    assert "¡Buenos días!" in combined
    assert "Привет" in combined
    assert "Synthetic Learner Reader" in combined


@pytest.mark.parametrize(
    ("fixture_name", "source_format"),
    [("local_export.html", "html"), ("local_export.txt", "text")],
)
def test_parse_local_kindle_exports_preserves_order_and_characters(fixture_name: str, source_format: str) -> None:
    result = parse_kindle_highlight_export(FIXTURE_DIR / fixture_name)

    assert [highlight.provenance.source_index for highlight in result.highlights] == [0, 1, 2]
    assert [highlight.provenance.source_format for highlight in result.highlights] == [source_format] * 3
    assert "¡Buenos días!" in result.highlights[0].text
    assert "puerta—rápido" in result.highlights[0].text
    assert "Привет, мир — это" in result.highlights[2].text
    assert all(len(highlight.provenance.content_hash) == 64 for highlight in result.highlights)
    assert all(highlight.highlight_id for highlight in result.highlights)


def test_parse_rejects_empty_malformed_unsafe_and_unsupported_inputs(tmp_path: Path) -> None:
    empty = tmp_path / "empty.txt"
    empty.write_text("", encoding="utf-8")
    malformed = tmp_path / "malformed.html"
    malformed.write_text("<html><body><div class='noteHeading'>Location 1</div></body></html>", encoding="utf-8")
    unsafe = tmp_path / "unsafe.txt"
    unsafe.write_text("==========\nBook\n- Your Highlight at location 1\n\n<script>alert('x')</script>\n", encoding="utf-8")
    unsupported = tmp_path / "local_export.pdf"
    unsupported.write_text("private words", encoding="utf-8")

    assert parse_kindle_highlight_export(empty).rejected[0].reason_code == "empty"
    assert parse_kindle_highlight_export(malformed).rejected[0].reason_code == "malformed"
    assert parse_kindle_highlight_export(unsafe).rejected[0].reason_code == "unsafe"

    unsupported_result = parse_kindle_highlight_export(unsupported)
    assert unsupported_result.rejected[0].reason_code == "unsupported_format"
    assert "private words" not in unsupported_result.rejected[0].detail
    assert str(unsupported) not in unsupported_result.rejected[0].detail
