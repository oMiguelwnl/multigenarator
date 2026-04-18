"""Typer CLI for Multilang job orchestration."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Annotated, Any

import typer

from multilang.domain.jobs import GenerationRequest, SupportedLanguage

app = typer.Typer(help="Multilang operator CLI.")

ConflictChecker = Callable[[GenerationRequest], bool]
GenerateExecutor = Callable[[GenerationRequest], Any]


def default_conflict_checker(_: GenerationRequest) -> bool:
    """Return whether the request would overwrite completed items."""

    return False


def default_generate_executor(request: GenerationRequest) -> GenerationRequest:
    """Default command behavior until a service is wired in."""

    return request


def _validate_request(request: GenerationRequest) -> None:
    if request.source_type == "frequency" and request.level is None:
        raise typer.BadParameter("--level is required when --source frequency")
    if request.source_type == "word-list" and request.input_file is None:
        raise typer.BadParameter("--input-file is required when --source word-list")
    if request.source_type != "frequency" and request.level is not None:
        raise typer.BadParameter("--level is only valid when --source frequency")
    if request.source_type != "word-list" and request.input_file is not None:
        raise typer.BadParameter("--input-file is only valid when --source word-list")
    if request.yes_overwrite and not request.overwrite:
        raise typer.BadParameter("--yes-overwrite requires --overwrite")


def _confirm_overwrite(request: GenerationRequest, conflict_checker: ConflictChecker) -> None:
    if not request.overwrite:
        return

    has_conflicts = conflict_checker(request)
    if not has_conflicts:
        return

    if request.yes_overwrite:
        return

    confirmed = typer.confirm(
        "Completed items already exist for this run. Overwrite and reprocess them?",
        default=False,
    )
    if not confirmed:
        raise typer.Exit(code=1)


def create_app(
    *,
    conflict_checker: ConflictChecker = default_conflict_checker,
    generate_executor: GenerateExecutor = default_generate_executor,
) -> typer.Typer:
    """Build the CLI application with injectable collaborators for tests."""

    cli = typer.Typer(help="Multilang operator CLI.")

    @cli.callback()
    def main() -> None:
        """Root command group for Multilang."""

        return None

    @cli.command("generate")
    def generate(
        language: Annotated[
            SupportedLanguage,
            typer.Option("--language", help="Target language."),
        ],
        source: Annotated[
            str,
            typer.Option("--source", help="Input mode: frequency or word-list."),
        ],
        level: Annotated[
            int | None,
            typer.Option("--level", min=1, max=3, help="Frequency level 1-3."),
        ] = None,
        input_file: Annotated[
            Path | None,
            typer.Option("--input-file", exists=False, dir_okay=False, help="Path to a word list."),
        ] = None,
        resume: Annotated[
            str | None,
            typer.Option("--resume", help="Resume an existing job by id."),
        ] = None,
        overwrite: Annotated[
            bool,
            typer.Option("--overwrite", help="Allow reprocessing completed items."),
        ] = False,
        yes_overwrite: Annotated[
            bool,
            typer.Option(
                "--yes-overwrite",
                help="Confirm overwrite in non-interactive mode when conflicts exist.",
            ),
        ] = False,
    ) -> None:
        if source not in {"frequency", "word-list"}:
            raise typer.BadParameter("--source must be one of: frequency, word-list")

        request = GenerationRequest(
            language=language,
            source_type=source,
            level=level,
            input_file=input_file,
            resume_job_id=resume,
            overwrite=overwrite,
            yes_overwrite=yes_overwrite,
        )
        _validate_request(request)
        _confirm_overwrite(request, conflict_checker)
        generate_executor(request)

    return cli


app = create_app()


if __name__ == "__main__":
    app()
