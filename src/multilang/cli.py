"""Typer CLI for Multilang job orchestration."""

from __future__ import annotations

from collections.abc import Callable
import gzip
import json
from pathlib import Path
from typing import Annotated, Any

import typer

from multilang.domain.jobs import GenerationRequest, JobProgressSnapshot, SupportedLanguage
from multilang.domain.exporting import ExportArtifactFormat
from multilang.progress import ProgressRenderer
from multilang.repositories.text_repository import TextRepository
from multilang.runtime import build_runtime_service
from multilang.services.execution_report import JobExecutionReport
from multilang.services.generate_job import GenerateJobResult, GenerateJobService
from multilang.services.highlight_import_preview import build_highlight_import_preview
from multilang.services.ingest_lexical_items import IngestLexicalItemsService
from multilang.services.kaikki_lookup import KaikkiLookup
from multilang.services.job_summary import JobLifecycleSummary, JobSummaryBuilder
from multilang.services.russian_phoneme_deck import (
    DEFAULT_RUSSIAN_PHONEME_DECK_NAME,
    export_russian_phoneme_deck,
)
from multilang.services.text_review import ReviewReport, TextReviewService
from multilang.settings import Settings

app = typer.Typer(help="Multilang operator CLI.")

TEST_MODE_CARDS_PER_LEVEL = 3
DEFAULT_KAIKKI_SOURCE_DIR = Path(".multilang/sources/kaikki")
LOCAL_SMOKE_LANGUAGE = SupportedLanguage.EN
LOCAL_SMOKE_FIXTURE_DIR = Path(".multilang/live-smoke-azure")
LOCAL_SMOKE_WORDS = ("harbor", "lantern", "meadow")

ConflictChecker = Callable[[GenerationRequest], bool]
GenerateExecutor = Callable[[GenerationRequest], Any]
RequestedItemKeysLoader = Callable[[GenerationRequest], list[str]]
ItemProcessor = Callable[[str], None]
ProgressSink = Callable[[str], None]
ReviewReportBuilder = Callable[..., ReviewReport]


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
        levels = [request.level] if request.level is not None else [1, 2, 3]
        cards_per_level = request.resolved_cards_per_level()
        return [
            f"level-{level}-rank-{index:04d}"
            for level in levels
            for index in range(1, cards_per_level + 1)
        ]

    if request.input_file is None:
        raise ValueError("word-list requests require an input file")

    return [
        line.strip()
        for line in request.input_file.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _validate_request(request: GenerationRequest, *, test_mode: bool = False) -> None:
    if request.source_type == "frequency" and request.level is None:
        # Allow None level for frequency - indicates full 3-level deck build
        pass
    if request.source_type == "word-list" and request.input_file is None:
        raise typer.BadParameter("--input-file is required when --source word-list")
    if request.source_type != "frequency" and request.level is not None:
        raise typer.BadParameter("--level is only valid when --source frequency")
    if request.source_type != "frequency" and test_mode:
        raise typer.BadParameter("--test-mode is only valid when --source frequency")
    if request.source_type != "frequency" and request.cards_per_level is not None:
        raise typer.BadParameter("--cards-per-level is only valid when --source frequency")
    if request.source_type != "word-list" and request.input_file is not None:
        raise typer.BadParameter("--input-file is only valid when --source word-list")
    if request.yes_overwrite and not request.overwrite:
        raise typer.BadParameter("--yes-overwrite requires --overwrite")


def _validate_regeneration_flags(
    *,
    request: GenerationRequest,
    regenerate_item_key: str | None,
) -> None:
    if regenerate_item_key is None:
        return
    if request.resume_job_id is None:
        raise typer.BadParameter("--regenerate-item-key requires --resume")


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


def _print_summary(summary: JobLifecycleSummary) -> None:
    typer.echo(f"completed_items={summary.completed_items}")
    typer.echo(f"retried_items={summary.retried_items}")
    typer.echo(f"failed_items={len(summary.failed_items)}")
    typer.echo(f"skipped_duplicates={summary.skipped_duplicates}")
    typer.echo(f"resumed_from_job={summary.resumed_from_job}")
    typer.echo(f"overwritten_items={summary.overwritten_items}")

    for failed_item in summary.failed_items:
        typer.echo(
            f"failed_item={failed_item.item_key} retry_count={failed_item.retry_count} error={failed_item.error}"
        )


def _print_resume_diagnostic(report: JobExecutionReport) -> None:
    diagnostic = report.orchestration.diagnostic
    if diagnostic is None:
        return

    typer.echo(diagnostic.reason)
    typer.echo(f"resume_diagnostic_details={diagnostic.details}")


def _default_review_report_path(job_id: str) -> Path:
    return Path(".multilang") / "review-reports" / f"{job_id}.json"


def _build_review_report(
    service: GenerateJobService | IngestLexicalItemsService,
    *,
    job_id: str,
    review_report_file: Path | None,
    review_report_builder: ReviewReportBuilder | None,
) -> ReviewReport:
    if review_report_builder is not None:
        return review_report_builder(job_id=job_id, output_path=review_report_file)

    if hasattr(service, "build_review_report"):
        return service.build_review_report(
            job_id=job_id,
            output_path=review_report_file or _default_review_report_path(job_id),
        )

    text_repository = TextRepository(service.repository.session)
    return TextReviewService(text_repository=text_repository).build_review_report(
        job_id=job_id,
        output_path=review_report_file or _default_review_report_path(job_id),
    )


def _print_review_report(report: ReviewReport) -> None:
    typer.echo(f"flagged_cards={report.item_count}")
    if report.item_count > 0 and report.report_path is not None:
        typer.echo(f"review_report={report.report_path}")


def _default_kaikki_source_file(language_code: str) -> Path:
    return DEFAULT_KAIKKI_SOURCE_DIR / f"kaikki-{language_code}.jsonl.gz"


def _resolve_lexicon_source_file(request: GenerationRequest) -> Path | None:
    if request.lexicon_source_file is not None:
        return request.lexicon_source_file

    source_path = _default_kaikki_source_file(request.language.value)
    if source_path.exists():
        return source_path

    return None


def _prepare_lexical_data(request: GenerationRequest, *, settings: Settings) -> None:
    lookup = KaikkiLookup(data_dir=settings.lexicon_data_dir)
    index_path = lookup.ensure_index(
        language_code=request.language.value,
        source_path=_resolve_lexicon_source_file(request),
    )
    if index_path is not None:
        return

    default_source = _default_kaikki_source_file(request.language.value)
    typer.echo(
        "lexical data is missing for language "
        f"'{request.language.value}'. Place the archive at {default_source} "
        "or re-run with --lexicon-source-file <path-to-local-kaikki.jsonl.gz> "
        "to bootstrap the local cache."
    )
    raise typer.Exit(code=1)


def _local_smoke_archive_rows() -> list[dict[str, object]]:
    return [
        {
            "word": "harbor",
            "lang_code": LOCAL_SMOKE_LANGUAGE.value,
            "senses": [{"glosses": ["a sheltered place where boats can anchor safely"]}],
            "sounds": [{"ipa": "/ˈhɑrbər/"}],
        },
        {
            "word": "lantern",
            "lang_code": LOCAL_SMOKE_LANGUAGE.value,
            "senses": [{"glosses": ["a portable light protected by a transparent case"]}],
            "sounds": [{"ipa": "/ˈlæntərn/"}],
        },
        {
            "word": "meadow",
            "lang_code": LOCAL_SMOKE_LANGUAGE.value,
            "senses": [{"glosses": ["a field of grass and wildflowers"]}],
            "sounds": [{"ipa": "/ˈmɛdoʊ/"}],
        },
    ]


def _write_local_smoke_assets(output_dir: Path) -> tuple[Path, Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)

    archive_path = output_dir / f"kaikki-{LOCAL_SMOKE_LANGUAGE.value}.jsonl.gz"
    with gzip.open(archive_path, "wt", encoding="utf-8") as handle:
        for row in _local_smoke_archive_rows():
            handle.write(json.dumps(row, ensure_ascii=False))
            handle.write("\n")

    words_path = output_dir / "words.txt"
    words_path.write_text("\n".join(LOCAL_SMOKE_WORDS), encoding="utf-8")

    lookup = KaikkiLookup(data_dir=output_dir / "lexicon")
    index_path = lookup.build_index(
        language_code=LOCAL_SMOKE_LANGUAGE.value,
        source_path=archive_path,
        force_refresh=True,
    )
    return archive_path, words_path, index_path


def create_app(
    *,
    conflict_checker: ConflictChecker = default_conflict_checker,
    generate_executor: GenerateExecutor | None = None,
    service: GenerateJobService | IngestLexicalItemsService | None = None,
    review_report_builder: ReviewReportBuilder | None = None,
) -> typer.Typer:
    """Build the CLI application with injectable collaborators for tests."""

    cli = typer.Typer(help="Multilang operator CLI.")

    def resolve_service() -> GenerateJobService | IngestLexicalItemsService | None:
        if service is not None:
            return service
        if generate_executor is not None:
            return None
        return build_runtime_service()

    def resolve_executor(resolved_service: GenerateJobService | None) -> GenerateExecutor:
        if resolved_service is not None:
            return build_generate_executor(resolved_service)
        if generate_executor is not None:
            return generate_executor
        raise RuntimeError("unable to resolve generate executor")

    @cli.callback()
    def main() -> None:
        """Root command group for Multilang."""

        return None

    @cli.command("prepare-local-smoke")
    def prepare_local_smoke(
        output_dir: Annotated[
            Path,
            typer.Option(
                "--output-dir",
                file_okay=False,
                dir_okay=True,
                writable=True,
                help="Directory where the local English smoke assets will be written.",
            ),
        ] = LOCAL_SMOKE_FIXTURE_DIR,
    ) -> None:
        archive_path, words_path, index_path = _write_local_smoke_assets(output_dir)
        typer.echo(f"archive={archive_path}")
        typer.echo(f"words={words_path}")
        typer.echo(f"index={index_path}")
        typer.echo(
            "smoke_command="
            f"MULTILANG_DATABASE_URL=sqlite+pysqlite:///{output_dir / 'smoke.db'} "
            f"MULTILANG_LEXICON_DATA_DIR={output_dir / 'lexicon'} "
            f"MULTILANG_AUDIO_STORAGE_DIR={output_dir / 'audio'} "
            "uv run python -m multilang.cli generate --language en --source word-list "
            f"--input-file {words_path} --lexicon-source-file {archive_path}"
        )

    @cli.command("preview-kindle-highlights")
    def preview_kindle_highlights(
        language: Annotated[
            SupportedLanguage,
            typer.Option("--language", help="Target language for candidate filtering."),
        ],
        input_file: Annotated[
            Path,
            typer.Option("--input-file", exists=False, dir_okay=False, help="Path to a local Kindle export."),
        ],
        planned_card_limit: Annotated[
            int | None,
            typer.Option("--planned-card-limit", min=0, help="Optional cap for planned preview cards."),
        ] = None,
    ) -> None:
        try:
            preview = build_highlight_import_preview(
                input_file,
                language=language,
                planned_card_limit=planned_card_limit,
            )
        except ValueError as exc:
            typer.echo(str(exc))
            raise typer.Exit(code=1) from exc

        typer.echo(f"imported_highlights={preview.imported_highlights}")
        typer.echo(f"extracted_candidates={preview.extracted_candidates}")
        typer.echo(f"rejected_highlights={preview.rejected_highlights}")
        typer.echo(f"duplicate_candidates={preview.duplicate_candidates}")
        typer.echo(f"planned_cards={preview.planned_cards}")

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
        cards_per_level: Annotated[
            int | None,
            typer.Option("--cards-per-level", min=1, help="Cards to generate per frequency level."),
        ] = None,
        test_mode: Annotated[
            bool,
            typer.Option(
                "--test-mode",
                help=f"Shortcut for a small frequency run ({TEST_MODE_CARDS_PER_LEVEL} cards per level).",
            ),
        ] = False,
        input_file: Annotated[
            Path | None,
            typer.Option("--input-file", exists=False, dir_okay=False, help="Path to a word list."),
        ] = None,
        lexicon_source_file: Annotated[
            Path | None,
            typer.Option(
                "--lexicon-source-file",
                exists=True,
                dir_okay=False,
                help="Local Kaikki .jsonl.gz archive used to bootstrap lexical cache data.",
            ),
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
        review_report_file: Annotated[
            Path | None,
            typer.Option(
                "--review-report-file",
                dir_okay=False,
                exists=False,
                help="Optional output path for the flagged text review report.",
            ),
        ] = None,
        regenerate_item_key: Annotated[
            str | None,
            typer.Option(
                "--regenerate-item-key",
                help="Regenerate one persisted text item for the resumed job.",
            ),
        ] = None,
    ) -> None:
        if source not in {"frequency", "word-list"}:
            raise typer.BadParameter("--source must be one of: frequency, word-list")

        resolved_cards_per_level = cards_per_level
        if source == "frequency" and test_mode and resolved_cards_per_level is None:
            resolved_cards_per_level = TEST_MODE_CARDS_PER_LEVEL

        request = GenerationRequest(
            language=language,
            source_type=source,
            level=level,
            cards_per_level=resolved_cards_per_level,
            input_file=input_file,
            lexicon_source_file=lexicon_source_file,
            resume_job_id=resume,
            overwrite=overwrite,
            yes_overwrite=yes_overwrite,
        )
        _validate_request(request, test_mode=test_mode)
        _validate_regeneration_flags(
            request=request,
            regenerate_item_key=regenerate_item_key,
        )
        _confirm_overwrite(request, conflict_checker)
        resolved_service = resolve_service()

        if isinstance(resolved_service, IngestLexicalItemsService):
            if service is None:
                _prepare_lexical_data(request, settings=resolved_service.settings)
            lexical_result = resolved_service.execute(request)
            if lexical_result.report.orchestration.diagnostic is not None:
                _print_resume_diagnostic(lexical_result.report)
                raise typer.Exit(code=1)

            typer.echo(f"grounded_candidates={lexical_result.grounded_candidates}")
            typer.echo(f"pending_groundings={lexical_result.pending_groundings}")
            typer.echo(f"rejected_rows={lexical_result.rejected_rows}")
            typer.echo(f"level_1_candidates={lexical_result.level_counts.get(1, 0)}")
            typer.echo(f"level_2_candidates={lexical_result.level_counts.get(2, 0)}")
            typer.echo(f"level_3_candidates={lexical_result.level_counts.get(3, 0)}")
            typer.echo(f"backfilled_candidates={lexical_result.backfilled_candidates}")
            if hasattr(resolved_service, "generate_text"):
                if regenerate_item_key is not None:
                    text_result = resolved_service.regenerate_text_item(
                        job_id=lexical_result.report.job_id,
                        item_key=regenerate_item_key,
                        deck_language=language,
                    )
                else:
                    text_result = resolved_service.generate_text(
                        job_id=lexical_result.report.job_id,
                        deck_language=language,
                    )
                typer.echo(f"text_processed_items={text_result.processed_items}")
                typer.echo(f"accepted_text_items={text_result.accepted_items}")
                typer.echo(f"review_required_text_items={text_result.review_required_items}")
                typer.echo(f"audio_processed_items={text_result.audio_processed_items}")
                typer.echo(f"audio_reused_items={text_result.audio_reused_items}")
                typer.echo(f"fallback_audio_items={text_result.fallback_audio_items}")
                typer.echo(f"failed_audio_items={text_result.failed_audio_items}")
                _print_review_report(
                    _build_review_report(
                        resolved_service,
                        job_id=lexical_result.report.job_id,
                        review_report_file=review_report_file,
                        review_report_builder=review_report_builder,
                    )
                )
            _print_summary(JobSummaryBuilder(resolved_service.repository).build(lexical_result.report))
            return

        result = resolve_executor(resolved_service)(request)

        if not isinstance(result, JobExecutionReport):
            return

        if result.orchestration.diagnostic is not None:
            _print_resume_diagnostic(result)
            raise typer.Exit(code=1)

        if resolved_service is None:
            return

        summary = JobSummaryBuilder(resolved_service.repository).build(result)
        _print_summary(summary)
        _print_review_report(
            _build_review_report(
                resolved_service,
                job_id=result.job_id,
                review_report_file=review_report_file,
                review_report_builder=review_report_builder,
            )
        )

    @cli.command("export")
    def export(
        job_id: Annotated[str, typer.Option("--job-id", help="Persisted job id to export.")],
        format: Annotated[
            ExportArtifactFormat,
            typer.Option("--format", help="Export format: apkg, csv, or tsv."),
        ],
        output_dir: Annotated[
            Path | None,
            typer.Option(
                "--output-dir",
                file_okay=False,
                dir_okay=True,
                writable=True,
                help="Directory where the export artifact will be written.",
            ),
        ] = None,
        deck_name: Annotated[
            str | None,
            typer.Option("--deck-name", help="Optional deck name override for exported artifacts."),
        ] = None,
    ) -> None:
        resolved_service = resolve_service()
        if resolved_service is None or not hasattr(resolved_service, "export_job"):
            raise typer.Exit(code=1)

        settings = getattr(resolved_service, "settings", Settings())
        target_output_dir = output_dir or settings.export_output_dir

        try:
            result = resolved_service.export_job(
                job_id=job_id,
                export_format=format,
                output_dir=target_output_dir,
                deck_name=deck_name,
            )
        except ValueError as exc:
            typer.echo(str(exc))
            raise typer.Exit(code=1) from exc

        typer.echo(f"artifact_path={result.output_path}")
        typer.echo(f"card_count={result.card_count}")

    @cli.command("export-russian-phonemes")
    def export_russian_phonemes(
        output_path: Annotated[
            Path,
            typer.Option(
                "--output-path",
                dir_okay=False,
                writable=True,
                help="Path for the Russian introductory phoneme .apkg deck.",
            ),
        ] = Settings().export_output_dir / "russian-phonemes.apkg",
        deck_name: Annotated[
            str,
            typer.Option("--deck-name", help="Deck name for the Russian phoneme package."),
        ] = DEFAULT_RUSSIAN_PHONEME_DECK_NAME,
    ) -> None:
        result = export_russian_phoneme_deck(output_path=output_path, deck_name=deck_name)
        typer.echo(f"artifact_path={result.output_path}")
        typer.echo(f"card_count={result.card_count}")

    return cli


app = create_app()


if __name__ == "__main__":
    app()
