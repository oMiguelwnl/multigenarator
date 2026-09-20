"""Generation command registration.

Dependencies are explicit and resolved by the application compatibility boundary.
Registering commands does not construct providers or open databases.
"""

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any

import typer

from multilang.cli_commands.common import TEST_MODE_CARDS_PER_LEVEL
from multilang.domain.deck_audit import audit_deck_package
from multilang.domain.exporting import ExportArtifactFormat
from multilang.domain.highlights import HighlightInputMode
from multilang.domain.jobs import GenerationRequest, SupportedLanguage
from multilang.domain.webdav import WebDAVError
from multilang.services.deck_audit_reader import read_apkg_cards
from multilang.services.deck_audit_reports import write_deck_audit_reports
from multilang.services.execution_report import JobExecutionReport
from multilang.services.ingest_lexical_items import IngestLexicalItemsService
from multilang.services.job_summary import JobSummaryBuilder
from multilang.services.rate_limit import SimpleRateLimiter
from multilang.settings import Settings


@dataclass(frozen=True, slots=True)
class Dependencies:
    """Only the collaborators used by this command family."""

    settings_factory: Callable[..., Settings]

    _build_review_report: Callable[..., Any]
    _confirm_overwrite: Callable[..., Any]
    _prepare_lexical_data: Callable[..., Any]
    _print_generate_text_progress: Callable[..., Any]
    _print_resume_diagnostic: Callable[..., Any]
    _print_review_report: Callable[..., Any]
    _print_summary: Callable[..., Any]
    _print_webdav_error: Callable[..., Any]
    _require_clean_anki_id_registry_for_export: Callable[..., Any]
    _validate_regeneration_flags: Callable[..., Any]
    _validate_request: Callable[..., Any]
    _write_local_smoke_assets: Callable[..., Any]
    assert_anki_id_registry_clean: Callable[..., Any]
    conflict_checker: Callable[..., Any]
    resolve_executor: Callable[..., Any]
    resolve_service: Callable[..., Any]
    resolve_webdav_service: Callable[..., Any]
    review_report_builder: Callable[..., Any] | None
    service: object | None


def register_commands(cli: typer.Typer, dependencies: Dependencies) -> None:
    """Attach this family to an existing application without running commands."""

    @cli.command("generation-lease-status")
    def generation_lease_status(job_id: Annotated[str, typer.Option("--job-id")]) -> None:
        """Inspect active or interrupted generation without calling providers."""
        import json

        from sqlalchemy import create_engine

        from multilang.services.generation_leases import GenerationLeaseManager

        engine = create_engine(dependencies.settings_factory().database_url)
        try:
            typer.echo(json.dumps(GenerationLeaseManager(engine).status(job_id), sort_keys=True))
        finally:
            engine.dispose()

    @cli.command("recover-generation-lease")
    def recover_generation_lease(
        job_id: Annotated[str, typer.Option("--job-id")],
        expected_item_sha256: Annotated[str, typer.Option("--expected-item-sha256")],
        acknowledge_unknown_outcome: Annotated[
            bool, typer.Option("--acknowledge-unknown-outcome", help="Acknowledge the interrupted provider outcome; this command does not retry it."),
        ] = False,
    ) -> None:
        """Clear one exact expired reservation after operator reconciliation."""
        import json

        from sqlalchemy import create_engine

        from multilang.services.generation_leases import (
            GenerationLeaseError,
            GenerationLeaseManager,
        )

        if not acknowledge_unknown_outcome:
            raise typer.BadParameter("--acknowledge-unknown-outcome is required")
        engine = create_engine(dependencies.settings_factory().database_url)
        try:
            result = GenerationLeaseManager(engine).recover(
                job_id, expected_item_sha256=expected_item_sha256,
                acknowledge_unknown_outcome=acknowledge_unknown_outcome,
            )
            typer.echo(json.dumps(result, sort_keys=True))
        except GenerationLeaseError as exc:
            typer.echo(str(exc))
            raise typer.Exit(code=1) from exc
        finally:
            engine.dispose()

    @cli.command("check-anki-id-registry")
    def check_anki_id_registry(
        production_roots: Annotated[
            bool,
            typer.Option("--production-roots", help="Scan production roots for non-registry Anki IDs."),
        ] = False,
    ) -> None:
        if not production_roots:
            typer.echo("check_anki_id_registry_error=production_roots_required")
            raise typer.Exit(code=1)
        try:
            result = dependencies.assert_anki_id_registry_clean(production_roots=True)
        except ValueError as exc:
            typer.echo(str(exc))
            raise typer.Exit(code=1) from exc
        typer.echo("anki_id_registry_status=clean")
        typer.echo(f"scanned_files={result.scanned_files}")
        typer.echo(f"issue_count={len(result.issues)}")

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
        ] = dependencies.settings_factory().example_output_dir / "local-smoke",
    ) -> None:
        words_path, index_path = dependencies._write_local_smoke_assets(output_dir)
        typer.echo(f"words={words_path}")
        typer.echo(f"index={index_path}")
        typer.echo(
            "smoke_command="
            f"MULTILANG_DATABASE_URL=sqlite+pysqlite:///{output_dir / 'smoke.db'} "
            f"MULTILANG_LEXICON_DATA_DIR={output_dir / 'lexicon'} "
            f"MULTILANG_AUDIO_STORAGE_DIR={output_dir / 'audio'} "
            "uv run python -m multilang.cli generate --language en --source word-list "
            f"--input-file {words_path}"
        )

    @cli.command("generate")
    def generate(
        language: Annotated[
            SupportedLanguage,
            typer.Option("--language", help="Target language."),
        ],
        source: Annotated[
            str,
            typer.Option("--source", help="Input mode: frequency, word-list, or highlights."),
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
        highlight_input: Annotated[
            HighlightInputMode,
            typer.Option("--highlight-input", help="Kindle input: text extracts words; vocabulary keeps each highlight as one word or expression."),
        ] = HighlightInputMode.TEXT,
        webdav_remote_path: Annotated[
            str | None,
            typer.Option(
                "--webdav-remote-path",
                help="Explicit WebDAV remote Kindle export path for --source highlights.",
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
        missing_only: Annotated[
            bool,
            typer.Option(
                "--missing-only",
                help="Generate text only for items without persisted text.",
            ),
        ] = False,
        max_items: Annotated[
            int | None,
            typer.Option(
                "--max-items",
                min=1,
                help="Maximum eligible text candidates to process in this run.",
            ),
        ] = None,
        rate_limit_per_minute: Annotated[
            int | None,
            typer.Option(
                "--rate-limit-per-minute",
                min=1,
                help="Maximum provider calls per minute during generation.",
            ),
        ] = None,
        concurrency: Annotated[
            int,
            typer.Option(
                "--concurrency",
                min=1,
                max=1,
                help="Text generation workers per job; currently only 1 is supported.",
            ),
        ] = 1,
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
        if source not in {"frequency", "word-list", "highlights"}:
            raise typer.BadParameter("--source must be one of: frequency, word-list, highlights")
        if highlight_input is HighlightInputMode.VOCABULARY:
            if source != "highlights":
                raise typer.BadParameter("--highlight-input vocabulary is only valid when --source highlights")
            if language is SupportedLanguage.KO:
                raise typer.BadParameter("Korean highlights require --highlight-input text")
        if language == SupportedLanguage.LA and source == "frequency":
            raise typer.BadParameter("--source frequency is not supported for Latin (la); use --source word-list with a list of lemmas instead (frozen data path is legacy)")
        if webdav_remote_path is not None and source != "highlights":
            raise typer.BadParameter("--webdav-remote-path is only valid when --source highlights")
        if webdav_remote_path is not None and input_file is not None:
            raise typer.BadParameter("--input-file and --webdav-remote-path are mutually exclusive")

        resolved_cards_per_level = cards_per_level
        if source == "frequency" and test_mode and resolved_cards_per_level is None:
            resolved_cards_per_level = TEST_MODE_CARDS_PER_LEVEL
        internal_source = "kindle-highlights" if source == "highlights" else source
        if webdav_remote_path is not None:
            try:
                fetch_result = dependencies.resolve_webdav_service().fetch_export(webdav_remote_path)
            except WebDAVError as exc:
                dependencies._print_webdav_error(exc)
                raise typer.Exit(code=1) from exc
            input_file = fetch_result.cached_path
            typer.echo(f"webdav_content_hash={fetch_result.content_hash}")
            typer.echo(f"webdav_size_bytes={fetch_result.size_bytes}")

        request = GenerationRequest(
            language=language,
            source_type=internal_source,
            level=level,
            cards_per_level=resolved_cards_per_level,
            input_file=input_file,
            highlight_input=highlight_input,
            resume_job_id=resume,
            overwrite=overwrite,
            yes_overwrite=yes_overwrite,
            missing_only=missing_only,
            max_items=max_items,
            rate_limit_per_minute=rate_limit_per_minute,
            concurrency=concurrency,
        )
        dependencies._validate_request(request, test_mode=test_mode)
        dependencies._validate_regeneration_flags(
            request=request,
            regenerate_item_key=regenerate_item_key,
        )
        dependencies._confirm_overwrite(request, dependencies.conflict_checker)
        resolved_service = dependencies.resolve_service()
        rate_limiter = (
            SimpleRateLimiter(request.rate_limit_per_minute)
            if request.rate_limit_per_minute is not None
            else None
        )

        if isinstance(resolved_service, IngestLexicalItemsService):
            if dependencies.service is None:
                dependencies._prepare_lexical_data(request, settings=resolved_service.settings)
            lexical_result = resolved_service.execute(request, rate_limiter=rate_limiter)
            if lexical_result.report.orchestration.diagnostic is not None:
                dependencies._print_resume_diagnostic(lexical_result.report)
                raise typer.Exit(code=1)

            typer.echo(f"grounded_candidates={lexical_result.grounded_candidates}")
            typer.echo(f"pending_groundings={lexical_result.pending_groundings}")
            typer.echo(f"rejected_rows={lexical_result.rejected_rows}")
            typer.echo(f"level_1_candidates={lexical_result.level_counts.get(1, 0)}")
            typer.echo(f"level_2_candidates={lexical_result.level_counts.get(2, 0)}")
            typer.echo(f"level_3_candidates={lexical_result.level_counts.get(3, 0)}")
            typer.echo(f"backfilled_candidates={lexical_result.backfilled_candidates}")
            if request.source_type == "kindle-highlights":
                typer.echo(f"imported_highlights={lexical_result.imported_highlights}")
                typer.echo(f"rejected_highlights={lexical_result.rejected_highlights}")
                typer.echo(f"extracted_candidates={lexical_result.extracted_candidates}")
                typer.echo(f"duplicate_candidates={lexical_result.duplicate_candidates}")
                typer.echo(f"reused_existing_candidates={lexical_result.reused_existing_items}")
                typer.echo(f"newly_planned_candidates={lexical_result.newly_planned_candidates}")
                typer.echo(f"blocked_candidates={lexical_result.blocked_candidates}")
                typer.echo(f"planned_cards={lexical_result.planned_cards}")
            if hasattr(resolved_service, "generate_text"):
                if regenerate_item_key is not None:
                    text_result = resolved_service.regenerate_text_item(
                        job_id=lexical_result.report.job_id,
                        item_key=regenerate_item_key,
                        deck_language=language,
                    )
                else:
                    try:
                        text_result = resolved_service.generate_text(
                            job_id=lexical_result.report.job_id,
                            deck_language=language,
                            missing_only=request.missing_only,
                            max_items=request.max_items,
                            progress_callback=dependencies._print_generate_text_progress,
                            rate_limiter=rate_limiter,
                            concurrency=request.concurrency,
                        )
                    except TypeError as exc:
                        if "concurrency" not in str(exc):
                            raise
                        text_result = resolved_service.generate_text(
                            job_id=lexical_result.report.job_id,
                            deck_language=language,
                            missing_only=request.missing_only,
                            max_items=request.max_items,
                            progress_callback=dependencies._print_generate_text_progress,
                            rate_limiter=rate_limiter,
                        )
                typer.echo(f"text_processed_items={text_result.processed_items}")
                typer.echo(f"accepted_text_items={text_result.accepted_items}")
                typer.echo(f"review_required_text_items={text_result.review_required_items}")
                typer.echo(f"audio_processed_items={text_result.audio_processed_items}")
                typer.echo(f"audio_reused_items={text_result.audio_reused_items}")
                typer.echo(f"fallback_audio_items={text_result.fallback_audio_items}")
                typer.echo(f"failed_audio_items={text_result.failed_audio_items}")
                dependencies._print_review_report(
                    dependencies._build_review_report(
                        resolved_service,
                        job_id=lexical_result.report.job_id,
                        review_report_file=review_report_file,
                        review_report_builder=dependencies.review_report_builder,
                    )
                )
            dependencies._print_summary(JobSummaryBuilder(resolved_service.repository).build(lexical_result.report))
            return

        result = dependencies.resolve_executor(resolved_service)(request)

        if not isinstance(result, JobExecutionReport):
            return

        if result.orchestration.diagnostic is not None:
            dependencies._print_resume_diagnostic(result)
            raise typer.Exit(code=1)

        if resolved_service is None:
            return

        summary = JobSummaryBuilder(resolved_service.repository).build(result)
        dependencies._print_summary(summary)
        dependencies._print_review_report(
            dependencies._build_review_report(
                resolved_service,
                job_id=result.job_id,
                review_report_file=review_report_file,
                review_report_builder=dependencies.review_report_builder,
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
        refresh_snapshots: Annotated[
            bool,
            typer.Option("--refresh-snapshots", help="Rebuild card_exports before writing the artifact."),
        ] = False,
        allow_partial: Annotated[
            bool,
            typer.Option("--allow-partial", help="Allow incomplete frequency exports with an explicit warning status."),
        ] = False,
    ) -> None:
        resolved_service = dependencies.resolve_service()
        if resolved_service is None or not hasattr(resolved_service, "export_job"):
            raise typer.Exit(code=1)

        settings = getattr(resolved_service, "settings", dependencies.settings_factory())
        target_output_dir = output_dir or settings.export_output_dir

        try:
            dependencies._require_clean_anki_id_registry_for_export()
            result = resolved_service.export_job(
                job_id=job_id,
                export_format=format,
                output_dir=target_output_dir,
                deck_name=deck_name,
                refresh_snapshots=refresh_snapshots,
                allow_partial=allow_partial,
            )
        except ValueError as exc:
            typer.echo(str(exc))
            raise typer.Exit(code=1) from exc

        typer.echo(f"artifact_path={result.output_path}")
        typer.echo(f"card_count={result.card_count}")
        if getattr(result, "partial", False):
            typer.echo("export_status=partial")
        if getattr(result, "report_json_path", None):
            typer.echo(f"generation_report_json={result.report_json_path}")
            typer.echo(f"generation_report_md={result.report_markdown_path}")

    @cli.command("repair-text")
    def repair_text(
        job_id: Annotated[str, typer.Option("--job-id", help="Persisted job id to repair.")],
        max_items: Annotated[int | None, typer.Option("--max-items", min=1, help="Maximum review rows to repair.")] = None,
    ) -> None:
        resolved_service = dependencies.resolve_service()
        if resolved_service is None or not hasattr(resolved_service, "generate_text"):
            raise typer.Exit(code=1)
        job = resolved_service.repository.get_job(job_id)
        if job is None:
            typer.echo(f"unknown job_id: {job_id}")
            raise typer.Exit(code=1)
        result = resolved_service.generate_text(
            job_id=job_id,
            deck_language=SupportedLanguage(job.language),
            max_items=max_items,
            repair_only=True,
            synthesize_audio=False,
            progress_callback=dependencies._print_generate_text_progress,
        )
        typer.echo(f"text_processed_items={result.processed_items}")
        typer.echo(f"accepted_text_items={result.accepted_items}")
        typer.echo(f"review_required_text_items={result.review_required_items}")

    @cli.command("synthesize-audio")
    def synthesize_audio(
        job_id: Annotated[str, typer.Option("--job-id", help="Persisted job id to synthesize audio for.")],
        missing_only: Annotated[bool, typer.Option("--missing-only", help="Generate only missing audio assets.")] = False,
        fallback_only: Annotated[bool, typer.Option("--fallback-only", help="Regenerate only audio assets previously produced via fallback.")] = False,
        max_items: Annotated[int | None, typer.Option("--max-items", min=1, help="Maximum text rows to process.")] = None,
    ) -> None:
        resolved_service = dependencies.resolve_service()
        if resolved_service is None or not hasattr(resolved_service, "synthesize_audio"):
            raise typer.Exit(code=1)
        job = resolved_service.repository.get_job(job_id)
        if job is None:
            typer.echo(f"unknown job_id: {job_id}")
            raise typer.Exit(code=1)
        result = resolved_service.synthesize_audio(
            job_id=job_id,
            deck_language=SupportedLanguage(job.language),
            missing_only=missing_only,
            fallback_only=fallback_only,
            max_items=max_items,
        )
        typer.echo(f"audio_processed_items={result.audio_processed_items}")
        typer.echo(f"audio_reused_items={result.audio_reused_items}")
        typer.echo(f"fallback_audio_items={result.fallback_audio_items}")
        typer.echo(f"failed_audio_items={result.failed_audio_items}")

    @cli.command("audit-deck")
    def audit_deck(
        input_apkg: Annotated[
            Path,
            typer.Option("--input-apkg", exists=False, dir_okay=False, help="Path to the APKG deck to audit."),
        ],
        output_dir: Annotated[
            Path,
            typer.Option(
                "--output-dir",
                file_okay=False,
                dir_okay=True,
                help="Directory where deck-audit.json and deck-audit.md will be written.",
            ),
        ] = dependencies.settings_factory().report_output_dir / "audits",
    ) -> None:
        try:
            read_result = read_apkg_cards(input_apkg)
            issues = audit_deck_package(read_result)
            report_result = write_deck_audit_reports(read_result, issues, output_dir)
        except (ValueError, OSError) as exc:
            typer.echo(str(exc))
            raise typer.Exit(code=1) from exc

        typer.echo(f"json_report={report_result.json_path}")
        typer.echo(f"markdown_report={report_result.markdown_path}")
        typer.echo(f"card_count={read_result.card_count}")
        typer.echo(f"issue_count={report_result.issue_count}")
        typer.echo(f"input_sha256={read_result.input_sha256}")
        if any(issue.severity == "error" for issue in issues):
            raise typer.Exit(code=1)
