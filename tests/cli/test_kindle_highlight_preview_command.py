from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from multilang.cli import create_app


runner = CliRunner()
FIXTURE_DIR = Path(__file__).parents[1] / "fixtures" / "kindle_highlights"


def test_preview_kindle_highlights_prints_stable_count_lines() -> None:
    app = create_app()

    result = runner.invoke(
        app,
        [
            "preview-kindle-highlights",
            "--language",
            "es",
            "--input-file",
            str(FIXTURE_DIR / "local_export.html"),
        ],
    )

    assert result.exit_code == 0
    lines = result.output.strip().splitlines()
    assert lines[0] == "imported_highlights=3"
    assert lines[1].startswith("extracted_candidates=")
    assert lines[2] == "rejected_highlights=0"
    assert lines[3].startswith("duplicate_candidates=")
    assert lines[4].startswith("planned_cards=")


def test_preview_kindle_highlights_applies_planned_card_limit() -> None:
    app = create_app()

    result = runner.invoke(
        app,
        [
            "preview-kindle-highlights",
            "--language",
            "pt",
            "--input-file",
            str(FIXTURE_DIR / "local_export.txt"),
            "--planned-card-limit",
            "2",
        ],
    )

    assert result.exit_code == 0
    assert "planned_cards=2" in result.output


def test_preview_kindle_highlights_has_privacy_safe_errors(tmp_path: Path) -> None:
    private_path = tmp_path / "Private Book - Secret Author.pdf"
    private_path.write_text("minha frase privada", encoding="utf-8")
    app = create_app()

    result = runner.invoke(
        app,
        [
            "preview-kindle-highlights",
            "--language",
            "pt",
            "--input-file",
            str(private_path),
        ],
    )

    assert result.exit_code == 1
    assert "unsupported_format" in result.output
    assert str(private_path) not in result.output
    assert "minha frase privada" not in result.output


def test_generate_source_kindle_highlights_remains_blocked() -> None:
    app = create_app()

    result = runner.invoke(app, ["generate", "--language", "es", "--source", "kindle-highlights"])

    assert result.exit_code != 0
    assert "--source must be one of: frequency, word-list, highlights" in result.output
