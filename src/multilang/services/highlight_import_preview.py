"""Count-only local Kindle import preview service."""

from __future__ import annotations

from pathlib import Path

from multilang.domain.highlights import HighlightImportPreview
from multilang.domain.jobs import SupportedLanguage
from multilang.services.highlight_candidate_extraction import extract_highlight_candidates
from multilang.services.kindle_highlight_parser import parse_kindle_highlight_export


def build_highlight_import_preview(
    path: str | Path,
    *,
    language: SupportedLanguage,
    planned_card_limit: int | None = None,
) -> HighlightImportPreview:
    """Return count-only import/extraction metrics for a local Kindle export."""

    if planned_card_limit is not None and planned_card_limit < 0:
        raise ValueError("planned_card_limit must be non-negative")

    parse_result = parse_kindle_highlight_export(path)
    if not parse_result.highlights and parse_result.rejected:
        reason_codes = ",".join(rejected.reason_code for rejected in parse_result.rejected)
        raise ValueError(f"kindle highlight preview failed: {reason_codes}")

    extraction_result = extract_highlight_candidates(parse_result.highlights, language=language)
    extracted_count = len(extraction_result.candidates)
    planned_cards = extracted_count if planned_card_limit is None else min(planned_card_limit, extracted_count)

    return HighlightImportPreview(
        imported_highlights=len(parse_result.highlights),
        extracted_candidates=extracted_count,
        rejected_highlights=len(parse_result.rejected),
        duplicate_candidates=extraction_result.duplicate_count,
        planned_cards=planned_cards,
    )


__all__ = ["build_highlight_import_preview"]
