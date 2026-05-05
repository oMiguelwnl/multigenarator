from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from multilang.cli import create_app
from multilang.domain.jobs import SupportedLanguage
from multilang.services.highlight_candidate_extraction import extract_highlight_candidates
from multilang.services.highlight_import_preview import build_highlight_import_preview
from multilang.services.kindle_highlight_parser import parse_kindle_highlight_export


FIXTURE_DIR = Path(__file__).parents[1] / "fixtures" / "kindle_highlights"


def test_local_html_fixture_flows_from_parser_to_candidates_to_preview() -> None:
    html_fixture = FIXTURE_DIR / "local_export.html"

    parse_result = parse_kindle_highlight_export(html_fixture)
    extraction_result = extract_highlight_candidates(parse_result.highlights, language=SupportedLanguage.ES)
    preview = build_highlight_import_preview(html_fixture, language=SupportedLanguage.ES)

    assert parse_result.rejected == []
    assert preview.imported_highlights == len(parse_result.highlights) == 3
    assert preview.extracted_candidates == len(extraction_result.candidates)
    assert preview.duplicate_candidates == extraction_result.duplicate_count
    assert [candidate.display_form for candidate in extraction_result.candidates[:3]] == ["Buenos", "días", "niño"]


def test_local_text_fixture_preserves_unicode_through_preview_cli() -> None:
    text_fixture = FIXTURE_DIR / "local_export.txt"
    parse_result = parse_kindle_highlight_export(text_fixture)
    runner = CliRunner()

    result = runner.invoke(
        create_app(),
        ["preview-kindle-highlights", "--language", "pt", "--input-file", str(text_fixture)],
    )

    assert result.exit_code == 0
    assert "puerta—rápido" in parse_result.highlights[0].text
    assert "Привет, мир — это" in parse_result.highlights[2].text
    assert "imported_highlights=3" in result.output
    assert "planned_cards=" in result.output


def test_malformed_local_input_reports_rejections_without_private_text(tmp_path: Path) -> None:
    private_text = "minha anotação privada não deve vazar"
    malformed = tmp_path / "private-export.html"
    malformed.write_text(f"<html><body>{private_text}</body></html>", encoding="utf-8")

    parse_result = parse_kindle_highlight_export(malformed)
    runner = CliRunner()
    preview_result = runner.invoke(
        create_app(),
        ["preview-kindle-highlights", "--language", "pt", "--input-file", str(malformed)],
    )

    assert parse_result.highlights == []
    assert parse_result.rejected[0].reason_code == "malformed"
    assert preview_result.exit_code == 1
    assert private_text not in preview_result.output
    assert str(malformed) not in preview_result.output


def test_highlight_preview_does_not_enable_generation_side_effects() -> None:
    app = create_app(generate_executor=lambda _: (_ for _ in ()).throw(AssertionError("generation called")))
    runner = CliRunner()

    preview_result = runner.invoke(
        app,
        ["preview-kindle-highlights", "--language", "es", "--input-file", str(FIXTURE_DIR / "local_export.html")],
    )
    generate_result = runner.invoke(app, ["generate", "--language", "es", "--source", "kindle-highlights"])

    assert preview_result.exit_code == 0
    assert generate_result.exit_code != 0
    assert "generation called" not in preview_result.output
