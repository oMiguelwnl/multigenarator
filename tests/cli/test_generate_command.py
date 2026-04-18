"""CLI tests for the generate command."""

from __future__ import annotations

from typer.testing import CliRunner

from multilang.cli import create_app

runner = CliRunner()


def test_generate_command_rejects_unsupported_language() -> None:
    app = create_app()

    result = runner.invoke(
        app,
        ["generate", "--language", "it", "--source", "frequency", "--level", "1"],
    )

    assert result.exit_code != 0
    assert "Invalid value for '--language'" in result.output


def test_frequency_source_requires_level() -> None:
    app = create_app()

    result = runner.invoke(app, ["generate", "--language", "en", "--source", "frequency"])

    assert result.exit_code != 0
    assert "--level is required when --source frequency" in result.output


def test_word_list_source_requires_input_file() -> None:
    app = create_app()

    result = runner.invoke(app, ["generate", "--language", "en", "--source", "word-list"])

    assert result.exit_code != 0
    assert "--input-file is required when --source word-list" in result.output


def test_overwrite_requires_explicit_confirmation() -> None:
    app = create_app(conflict_checker=lambda _: True)

    result = runner.invoke(
        app,
        ["generate", "--language", "en", "--source", "frequency", "--level", "1", "--overwrite"],
        input="n\n",
    )

    assert result.exit_code == 1
    assert "Overwrite and reprocess" in result.output


def test_yes_overwrite_allows_non_interactive_confirmation() -> None:
    called = False

    def execute(_: object) -> None:
        nonlocal called
        called = True

    app = create_app(conflict_checker=lambda _: True, generate_executor=execute)

    result = runner.invoke(
        app,
        [
            "generate",
            "--language",
            "en",
            "--source",
            "frequency",
            "--level",
            "1",
            "--overwrite",
            "--yes-overwrite",
        ],
    )

    assert result.exit_code == 0
    assert called is True
