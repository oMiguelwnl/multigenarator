"""Typer CLI for Multilang job orchestration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any

import typer

from multilang.domain.jobs import GenerationRequest, JobProgressSnapshot, SupportedLanguage
from multilang.progress import ProgressRenderer
from multilang.runtime import build_runtime_service
from multilang.services.execution_report import JobExecutionReport
from multilang.services.generate_job import GenerateJobResult, GenerateJobService
from multilang.settings import Settings

app = typer.Typer(help="Multilang operator CLI.")

ConflictChecker = Callable[[GenerationRequest], bool]
GenerateExecutor = Callable[[GenerationRequest], Any]
RequestedItemKeysLoader = Callable[[GenerationRequest], list[str]]
ItemProcessor = Callable[[str], None]
ProgressSink = Callable[[str], None]


def default_conflict_checker(_: GenerationRequest) -> bool:
    """Return whether the request would overwrite completed items."""

    return False


def default_item_processor(_: str) -> None:
    """Default stub processor until downstream phases add real work."""

    return None


def default_progress_sink(line: str) -> None:
    """Write progress lines to the terminal."""

    typer.echo(line)


def build_generate_executor(
    service: GenerateJobService,
    *,
    settings: Settings | None = None,
    item_processor: ItemProcessor = default_item_processor,
    progress_renderer: ProgressRenderer | None = None,
    progress_sink: ProgressSink = default_progress_sink,
) -> GenerateExecutor:
    """Create a CLI executor backed by the orchestration service."""

    runtime_settings = settings or Settings()
    renderer = progress_renderer or ProgressRenderer()

    def execute(request: GenerationRequest) -> JobExecutionReport:
        orchestration = service.orchestrate(
            request,
            requested_item_keys=load_requested_item_keys(request),
        )
        progress_updates, retried_item_keys, failed_item_keys = _execute_with_progress(
            service,
            orchestration,
            max_attempts=runtime_settings.default_retry_attempts,
            item_processor=item_processor,
            progress_renderer=renderer,
            progress_sink=progress_sink,
        )
        return JobExecutionReport(
            orchestration=orchestration,
            progress_updates=progress_updates,
            retried_item_keys=retried_item_keys,
            failed_item_keys=failed_item_keys,
        )

    return execute


def _build_snapshot(
    *,
    stage: Any,
    completed_items: int,
    failed_items: int,
    retrying_items: int,
    skipped_duplicates: int,
) -> JobProgressSnapshot:
    return JobProgressSnapshot(
        stage=stage,
        completed_items=completed_items,
        failed_items=failed_items,
        retrying_items=retrying_items,
        skipped_duplicates=skipped_duplicates,
    )


def _emit_progress(
    snapshot: JobProgressSnapshot,
    *,
    total_items: int,
    progress_renderer: ProgressRenderer,
    progress_sink: ProgressSink,
    progress_updates: list[str],
) -> None:
    line = progress_renderer.render_snapshot(snapshot, total_items=total_items)
    progress_sink(line)
    progress_updates.append(line)


def _execute_with_progress(
    service: GenerateJobService,
    orchestration: GenerateJobResult,
    *,
    max_attempts: int,
    item_processor: ItemProcessor,
    progress_renderer: ProgressRenderer,
    progress_sink: ProgressSink,
) -> tuple[list[str], list[str], list[str]]:
    total_items = len(orchestration.pending_item_keys) + len(orchestration.skipped_item_keys)
    completed_items = 0
    failed_items = 0
    skipped_duplicates = len(orchestration.skipped_item_keys)
    progress_updates: list[str] = []
    retried_item_keys: list[str] = []
    failed_item_keys: list[str] = []

    _emit_progress(
        _build_snapshot(
            stage=orchestration.resume_from_stage,
            completed_items=completed_items,
            failed_items=failed_items,
            retrying_items=0,
            skipped_duplicates=skipped_duplicates,
        ),
        total_items=total_items,
        progress_renderer=progress_renderer,
        progress_sink=progress_sink,
        progress_updates=progress_updates,
    )

    for item_key in orchestration.pending_item_keys:
        for attempt in range(1, max_attempts + 1):
            try:
                item_processor(item_key)
            except Exception as exc:
                if attempt < max_attempts:
                    if item_key not in retried_item_keys:
                        retried_item_keys.append(item_key)
                    _emit_progress(
                        _build_snapshot(
                            stage=orchestration.resume_from_stage,
                            completed_items=completed_items,
                            failed_items=failed_items,
                            retrying_items=1,
                            skipped_duplicates=skipped_duplicates,
                        ),
                        total_items=total_items,
                        progress_renderer=progress_renderer,
                        progress_sink=progress_sink,
                        progress_updates=progress_updates,
                    )
                    continue

                failed_items += 1
                failed_item_keys.append(item_key)
                service.repository.record_item_failure(
                    orchestration.job_id,
                    item_key=item_key,
                    failed_stage=orchestration.resume_from_stage,
                    error=str(exc),
                    retry_count=attempt,
                )
                _emit_progress(
                    _build_snapshot(
                        stage=orchestration.resume_from_stage,
                        completed_items=completed_items,
                        failed_items=failed_items,
                        retrying_items=0,
                        skipped_duplicates=skipped_duplicates,
                    ),
                    total_items=total_items,
                    progress_renderer=progress_renderer,
                    progress_sink=progress_sink,
                    progress_updates=progress_updates,
                )
                break

            completed_items += 1
            service.repository.record_item_success(
                orchestration.job_id,
                item_key=item_key,
                completed_stage=orchestration.resume_from_stage,
            )
            _emit_progress(
                _build_snapshot(
                    stage=orchestration.resume_from_stage,
                    completed_items=completed_items,
                    failed_items=failed_items,
                    retrying_items=0,
                    skipped_duplicates=skipped_duplicates,
                ),
                total_items=total_items,
                progress_renderer=progress_renderer,
                progress_sink=progress_sink,
                progress_updates=progress_updates,
            )
            break

    return progress_updates, retried_item_keys, failed_item_keys


def load_requested_item_keys(request: GenerationRequest) -> list[str]:
    """Resolve deterministic item keys for the current orchestration phase."""

    if request.source_type == "frequency":
        if request.level is None:
            raise ValueError("frequency requests require a level")
        return [f"level-{request.level}-rank-{index:04d}" for index in range(1, 1001)]

    if request.input_file is None:
        raise ValueError("word-list requests require an input file")

    return [
        line.strip()
        for line in request.input_file.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


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
    generate_executor: GenerateExecutor | None = None,
    service: GenerateJobService | None = None,
) -> typer.Typer:
    """Build the CLI application with injectable collaborators for tests."""

    cli = typer.Typer(help="Multilang operator CLI.")

    def resolve_executor() -> GenerateExecutor:
        if service is not None:
            return build_generate_executor(service)
        if generate_executor is not None:
            return generate_executor
        return build_generate_executor(build_runtime_service())

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
        resolve_executor()(request)

    return cli


app = create_app()


if __name__ == "__main__":
    app()
