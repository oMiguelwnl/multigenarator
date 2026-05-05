from __future__ import annotations

from pathlib import Path

import pytest

from multilang.domain.jobs import SupportedLanguage
from multilang.services.highlight_import_preview import build_highlight_import_preview


FIXTURE_DIR = Path(__file__).parents[1] / "fixtures" / "kindle_highlights"


def test_build_highlight_import_preview_combines_parser_and_candidate_counts() -> None:
    preview = build_highlight_import_preview(
        FIXTURE_DIR / "local_export.html",
        language=SupportedLanguage.ES,
    )

    assert preview.imported_highlights == 3
    assert preview.extracted_candidates > 0
    assert preview.rejected_highlights == 0
    assert preview.duplicate_candidates >= 0
    assert preview.planned_cards == preview.extracted_candidates


def test_build_highlight_import_preview_applies_planned_card_limit() -> None:
    preview = build_highlight_import_preview(
        FIXTURE_DIR / "local_export.txt",
        language=SupportedLanguage.PT,
        planned_card_limit=2,
    )

    assert preview.extracted_candidates > 2
    assert preview.planned_cards == 2


def test_build_highlight_import_preview_omits_private_text_and_paths_from_errors(tmp_path: Path) -> None:
    private_path = tmp_path / "Private Book - Secret Author.pdf"
    private_text = "Minha frase privada nunca deve aparecer"
    private_path.write_text(private_text, encoding="utf-8")

    with pytest.raises(ValueError) as exc_info:
        build_highlight_import_preview(private_path, language=SupportedLanguage.PT)

    message = str(exc_info.value)
    assert private_text not in message
    assert str(private_path) not in message
    assert "unsupported_format" in message
